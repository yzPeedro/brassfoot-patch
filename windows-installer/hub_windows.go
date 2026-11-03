//go:build windows

package main

import (
	_ "embed"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"syscall"
	"time"
	"unsafe"

	webview2 "github.com/jchv/go-webview2"
	"github.com/jchv/go-webview2/webviewloader"
	"golang.org/x/sys/windows/registry"
)

//go:embed ui/hub.html
var hubPage string

//go:embed ui/mark.svg
var hubMark string

//go:embed ui/pitch.jpg
var hubPitch []byte

//go:embed ui/live-pitch.js
var hubLivePitch string

const (
	hubWidth          = 1240
	hubHeight         = 820
	gwlStyle          = -16
	gwlWndProc        = -4
	wsPopup           = 0x80000000
	wsClipChildren    = 0x02000000
	wsThickFrame      = 0x00040000
	swpNoZOrder       = 0x0004
	swpNoActivate     = 0x0010
	swpFrameChanged   = 0x0020
	swMinimize        = 6
	wmNcCalcSize      = 0x0083
	wmNcLButtonDown   = 0x00A1
	htCaption         = 2
	dwmCornerAttr     = 33
	dwmCornerRound    = 2
	dwmBorderColor    = 34
	cfUnicodeText     = 13
	gmemMoveable      = 0x0002
	siteURL           = "https://yzpeedro.github.io/brassfoot-patch/"
	repositoryURL     = "https://github.com/yzPeedro/brassfoot-patch"
	webviewRuntimeURL = "https://developer.microsoft.com/microsoft-edge/webview2/"
)

var (
	dwm                = syscall.NewLazyDLL("dwmapi.dll")
	setWindowLong      = u32.NewProc("SetWindowLongPtrW")
	getWindowLong      = u32.NewProc("GetWindowLongPtrW")
	callWindowProc     = u32.NewProc("CallWindowProcW")
	setWindowPos       = u32.NewProc("SetWindowPos")
	releaseCapture     = u32.NewProc("ReleaseCapture")
	openClipboard      = u32.NewProc("OpenClipboard")
	emptyClipboard     = u32.NewProc("EmptyClipboard")
	setClipboardData   = u32.NewProc("SetClipboardData")
	closeClipboard     = u32.NewProc("CloseClipboard")
	globalAlloc        = k32.NewProc("GlobalAlloc")
	globalLock         = k32.NewProc("GlobalLock")
	globalUnlock       = k32.NewProc("GlobalUnlock")
	dwmSetAttribute    = dwm.NewProc("DwmSetWindowAttribute")
	dwmExtendFrame     = dwm.NewProc("DwmExtendFrameIntoClientArea")
	setDpiAwarenessCtx = u32.NewProc("SetProcessDpiAwarenessContext")
	hubView            webview2.WebView
	hubWindow          uintptr
	hubOriginalProc    uintptr
	hubMutex           sync.Mutex
	hubGame            string
	hubBusy            string
	hubState           = map[string]any{}
	hubStagingRoot     string
)

type margins struct{ Left, Right, Top, Bottom int32 }

func hubEmit(event map[string]any) {
	body, err := json.Marshal(event)
	if err != nil || hubView == nil {
		return
	}
	hubView.Dispatch(func() {
		hubView.Eval("window.hubEvent && window.hubEvent(" + string(body) + ")")
	})
}

func hubSetBusy(operation string) bool {
	hubMutex.Lock()
	defer hubMutex.Unlock()
	if operation != "" && hubBusy != "" {
		return false
	}
	hubBusy = operation
	return true
}

func hubIsBusy() bool {
	hubMutex.Lock()
	defer hubMutex.Unlock()
	return hubBusy != ""
}

func hubCurrentGame() string {
	hubMutex.Lock()
	defer hubMutex.Unlock()
	return hubGame
}

func hubFail(operation string, err error) {
	d := diagnose(err)
	recordDiagnostic(d)
	hubEmit(map[string]any{"type": "error", "operation": operation, "code": d.Code, "title": d.Title, "reason": d.Reason, "action": d.Action})
}

func hubRefresh() {
	game := hubCurrentGame()
	go func() {
		state := map[string]any{"game": game, "valid": false}
		manifest := bundledManifestFromFS()
		if game != "" && len(manifest.Files) == 0 {
			if resolved, _, err := validGame(game); err != nil {
				d := diagnose(err)
				state["error"] = map[string]string{"title": d.Title, "reason": d.Reason, "action": d.Action}
			} else {
				state["valid"] = true
				state["game"] = resolved
				state["patch"], state["live"] = "unknown", "unknown"
			}
		} else if game != "" {
			current, err := detectState(manifest, game)
			if err != nil {
				d := diagnose(err)
				state["error"] = map[string]string{"title": d.Title, "reason": d.Reason, "action": d.Action}
			} else {
				state["valid"] = true
				state["game"] = current.Game
				state["patch"], state["live"] = componentStatus(manifest, current)
				if supportsTargets(manifest) {
					harvestOriginals(manifest, current.Game)
				}
				state["components"] = componentReport(manifest, current.Game)
				state["recommendation"] = recommendFor(current.Game)
				state["version"] = manifest.Version
				state["executableKnown"] = current.ExecutableKnown || current.ExecutableMissing
				state["teamsInstalled"] = current.TeamsInstalled
				state["teamsTotal"] = current.TeamsTotal
			}
		}
		if process, err := runningBrasfoot(); err == nil && process != "" {
			state["running"] = process
		}
		hubMutex.Lock()
		hubState = state
		hubMutex.Unlock()
		hubEmit(map[string]any{"type": "state", "state": state})
	}()
}

func hubInfo() map[string]any {
	m := bundledManifestFromFS()
	return map[string]any{
		"product": productName, "hubVersion": hubVersion, "year": patchYearText,
		"bundleVersion": m.Version, "files": len(m.Files), "components": m.Components != nil,
		"installed": runningFromInstallDir(), "preview": feedIsLocal(),
		"pixPayload": pixPayload, "pixSvg": pixSVG(),
	}
}

func hubFeedInfo(loading bool) map[string]any {
	status := feedStatus()
	feed := status.Feed
	info := map[string]any{
		"loading": loading, "online": status.Online, "cached": status.Cached, "loaded": status.Loaded,
		"problem": status.Problem, "preview": feedIsLocal(), "hubVersion": hubVersion,
	}
	if feed.PatchVersion != "" {
		info["patchVersion"] = feed.PatchVersion
		info["publishedAt"] = feed.PublishedAt
		info["notes"] = feed.Notes
		info["hubRemote"] = feed.Hub.Version
		info["hubNotes"] = feed.Hub.Notes
		info["hubUpdate"] = hubUpdateAvailable(feed)
		info["requiresHub"] = feed.RequiresHub
	}
	return info
}

func hubCheckUpdates() error {
	if !hubSetBusy("feed") {
		return errors.New("Aguarde a operação em andamento terminar.")
	}
	go func() {
		defer func() {
			hubSetBusy("")
			hubRefresh()
		}()
		hubEmit(map[string]any{"type": "feed", "feed": hubFeedInfo(true)})
		last := int64(-1)
		refreshFeed(func(done, total int64) {
			if total <= 0 {
				return
			}
			percent := done * 100 / total
			if percent == last {
				return
			}
			last = percent
			hubEmit(map[string]any{"type": "feed-progress", "percent": percent})
		})
		if status := feedStatus(); status.Online {
			rememberSeenVersions(status.Feed)
		}
		hubEmit(map[string]any{"type": "feed", "feed": hubFeedInfo(false)})
	}()
	return nil
}

func hubGetSettings() HubSettings {
	return loadSettings()
}

func hubSetSetting(key string, value any) (HubSettings, error) {
	settings := loadSettings()
	switch key {
	case "theme":
		theme, _ := value.(string)
		if theme != "light" && theme != "dark" {
			theme = "system"
		}
		settings.Theme = theme
	case "notify":
		enabled, _ := value.(bool)
		if err := setNotifications(enabled); err != nil {
			return settings, errors.New("O Windows não permitiu ativar os avisos de versão nova.")
		}
		settings.Notify = enabled
		if enabled {
			if status := feedStatus(); status.Feed.PatchVersion != "" {
				settings.LastSeenPatch = status.Feed.PatchVersion
				settings.LastSeenHub = status.Feed.Hub.Version
			}
		}
	case "autoInstall":
		enabled, _ := value.(bool)
		settings.AutoInstall = enabled
	default:
		return settings, errors.New("configuração desconhecida")
	}
	return settings, saveSettings(settings)
}

func hubSetFrameTheme(dark bool) {
	if hubWindow == 0 || dwm.Load() != nil {
		return
	}
	border := uint32(0x00f3e7e1)
	if dark {
		border = 0x0020120b
	}
	hubView.Dispatch(func() {
		dwmSetAttribute.Call(hubWindow, dwmBorderColor, uintptr(unsafe.Pointer(&border)), 4)
	})
}

func hubUninstallHub() error {
	if hubIsBusy() {
		return errors.New("Aguarde a operação em andamento terminar.")
	}
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	if err = startHub(exe, []string{"--uninstall-hub"}); err != nil {
		return err
	}
	postMessage.Call(hubWindow, wmClose, 0, 0)
	return nil
}

func hubUpdateHub() error {
	feed := feedStatus().Feed
	if !hubUpdateAvailable(feed) {
		return errors.New("Você já está com o instalador mais recente.")
	}
	if !hubSetBusy("hub-update") {
		return errors.New("Aguarde a operação em andamento terminar.")
	}
	go func() {
		progress := hubProgress("hub-update", 0, 95, func(done, total int) string { return "Baixando o instalador " + feed.Hub.Version })
		err := applyHubUpdate(feed, func(done, total int64) {
			if total > 0 {
				progress(int(done*1000/total), 1000)
			}
		})
		if err != nil {
			hubSetBusy("")
			hubFail("hub-update", err)
			return
		}
		hubEmit(map[string]any{"type": "progress", "operation": "hub-update", "percent": 100, "label": "Reabrindo o instalador"})
		hubSetBusy("")
		postMessage.Call(hubWindow, wmClose, 0, 0)
	}()
	return nil
}

func hubOpenExternal(url string) {
	allowed := []string{repositoryURL + "/", siteURL}
	for _, prefix := range allowed {
		if strings.HasPrefix(url, prefix) {
			shellExecute.Call(hubWindow, uintptr(unsafe.Pointer(strPtr("open"))), uintptr(unsafe.Pointer(strPtr(url))), 0, 0, swShow)
			return
		}
	}
}

func pixSVG() string {
	data, err := base64.StdEncoding.DecodeString(pixQRBitsBase64)
	if err != nil || len(data) != (pixQRSize*pixQRSize+7)/8 {
		return ""
	}
	var path strings.Builder
	for y := 0; y < pixQRSize; y++ {
		for x := 0; x < pixQRSize; x++ {
			offset := y*pixQRSize + x
			if data[offset/8]&(1<<uint(7-offset%8)) != 0 {
				fmt.Fprintf(&path, "M%d %dh1v1h-1z", x, y)
			}
		}
	}
	return fmt.Sprintf(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" shape-rendering="crispEdges"><rect width="100%%" height="100%%" fill="#fff"/><path d="%s" fill="#0b1633"/></svg>`, pixQRSize, pixQRSize, path.String())
}

func hubChooseGame() {
	if hubIsBusy() {
		return
	}
	hubView.Dispatch(func() {
		if path := chooseFolder("Selecione a pasta principal do Brasfoot"); path != "" {
			hubMutex.Lock()
			hubGame = normalizeGameSelection(path)
			hubMutex.Unlock()
			hubRefresh()
		}
	})
}

func hubProgress(operation string, base, span int, label func(done, total int) string) func(done, total int) {
	last := -1
	return func(done, total int) {
		if total <= 0 {
			return
		}
		percent := base + span*done/total
		if percent == last && done != total {
			return
		}
		last = percent
		hubEmit(map[string]any{"type": "progress", "operation": operation, "percent": percent, "label": label(done, total)})
	}
}

func hubInstall(selection Selection) error {
	game := hubCurrentGame()
	if game == "" {
		return errors.New("Escolha a pasta do Brasfoot antes de instalar.")
	}
	if !selection.Patch && !selection.Live {
		return errors.New("Marque ao menos uma opção para instalar.")
	}
	if !hubSetBusy("install") {
		return errors.New("Aguarde a operação em andamento terminar.")
	}
	go func() {
		defer func() {
			hubSetBusy("")
			hubRefresh()
		}()
		hubEmit(map[string]any{"type": "progress", "operation": "install", "percent": 3, "label": "Conferindo o jogo e o pacote"})
		if process, err := runningBrasfoot(); err == nil && process != "" {
			hubEmit(map[string]any{"type": "error", "operation": "install", "code": "BF-112", "title": "Feche o Brasfoot", "reason": "O jogo está aberto (" + process + ").", "action": "Salve sua carreira, feche o jogo e tente de novo."})
			return
		}
		plan, err := stageComponents(hubStagingRoot, game, selection)
		if err != nil {
			hubFail("install", err)
			return
		}
		if plan.AlreadyInstalled {
			hubEmit(map[string]any{"type": "done", "operation": "install", "already": true, "version": plan.Manifest.Version})
			return
		}
		backupProgress := hubProgress("install", 10, 40, func(done, total int) string { return fmt.Sprintf("Guardando backup · %d de %d", done, total) })
		installProgress := hubProgress("install", 50, 49, func(done, total int) string { return fmt.Sprintf("Instalando · %d de %d", done, total) })
		result, err := install(plan, InstallOptions{Progress: func(stage string, done, total int) {
			switch stage {
			case "backup":
				backupProgress(done, total)
			case "install":
				installProgress(done, total)
			}
		}})
		if err != nil {
			hubFail("install", err)
			return
		}
		hubEmit(map[string]any{"type": "done", "operation": "install", "version": result.Version, "files": result.Files, "backup": filepath.Base(result.BackupPath)})
	}()
	return nil
}

func hubApply(target TargetState, operation string) error {
	game := hubCurrentGame()
	if game == "" {
		return errors.New("Escolha a pasta do Brasfoot antes de continuar.")
	}
	if !hubSetBusy("install") {
		return errors.New("Aguarde a operação em andamento terminar.")
	}
	go func() {
		defer func() {
			hubSetBusy("")
			hubRefresh()
		}()
		hubEmit(map[string]any{"type": "progress", "operation": "install", "percent": 3, "label": "Conferindo o jogo e o pacote"})
		if process, err := runningBrasfoot(); err == nil && process != "" {
			hubEmit(map[string]any{"type": "error", "operation": "install", "code": "BF-112", "title": "Feche o Brasfoot", "reason": "O jogo está aberto (" + process + ").", "action": "Salve sua carreira, feche o jogo e tente de novo."})
			return
		}
		plan, err := stageTarget(hubStagingRoot, game, target)
		if err != nil {
			hubFail("install", err)
			return
		}
		if plan.Empty || (plan.Plan.AlreadyInstalled && len(plan.Deletes) == 0) {
			hubEmit(map[string]any{"type": "done", "operation": "install", "mode": operation, "already": true, "version": plan.Plan.Manifest.Version})
			return
		}
		backupProgress := hubProgress("install", 10, 40, func(done, total int) string { return fmt.Sprintf("Guardando backup · %d de %d", done, total) })
		installProgress := hubProgress("install", 50, 49, func(done, total int) string { return fmt.Sprintf("Aplicando · %d de %d", done, total) })
		result, err := applyTarget(plan, InstallOptions{Progress: func(stage string, done, total int) {
			switch stage {
			case "backup":
				backupProgress(done, total)
			case "install":
				installProgress(done, total)
			}
		}})
		if err != nil {
			hubFail("install", err)
			return
		}
		hubEmit(map[string]any{"type": "done", "operation": "install", "mode": operation, "version": result.Version, "files": result.Files, "backup": filepath.Base(result.BackupPath)})
	}()
	return nil
}

func hubImportOriginals() {
	if hubIsBusy() {
		return
	}
	hubView.Dispatch(func() {
		path := chooseFolder("Selecione uma instalação original do Brasfoot (sem patch)")
		if path == "" {
			return
		}
		go func() {
			folder := normalizeGameSelection(path)
			imported, err := importOriginalsFrom(bundledManifestFromFS(), folder)
			if err != nil {
				hubFail("originals", err)
				return
			}
			settings := loadSettings()
			settings.OriginalFolder = folder
			_ = saveSettings(settings)
			hubEmit(map[string]any{"type": "settings", "settings": settings})
			hubEmit(map[string]any{"type": "toast", "message": fmt.Sprintf("%d arquivos originais guardados para a remoção.", imported)})
			hubRefresh()
		}()
	})
}

func hubListBackups() []BackupEntry {
	entries, _ := listBackups()
	game := hubCurrentGame()
	if game == "" {
		return entries
	}
	filtered := []BackupEntry{}
	for _, entry := range entries {
		if entry.Game == "" || sameFolder(entry.Game, game) {
			filtered = append(filtered, entry)
		}
	}
	return filtered
}

func hubCreateBackup() error {
	game := hubCurrentGame()
	if game == "" {
		return errors.New("Escolha a pasta do Brasfoot primeiro.")
	}
	if !hubSetBusy("backup") {
		return errors.New("Aguarde a operação em andamento terminar.")
	}
	go func() {
		defer hubSetBusy("")
		entry, err := createGameSnapshot(game, "Backup completo", bundledManifestFromFS().Version, hubProgress("backup", 0, 100, func(done, total int) string {
			return fmt.Sprintf("Copiando · %d de %d arquivos", done, total)
		}))
		if err != nil {
			hubFail("backup", err)
			return
		}
		hubEmit(map[string]any{"type": "done", "operation": "backup", "backup": entry})
	}()
	return nil
}

func hubRestoreBackup(id string) error {
	game := hubCurrentGame()
	if game == "" {
		return errors.New("Escolha a pasta do Brasfoot primeiro.")
	}
	entry, err := findBackup(id)
	if err != nil {
		return err
	}
	if !hubSetBusy("restore") {
		return errors.New("Aguarde a operação em andamento terminar.")
	}
	go func() {
		defer func() {
			hubSetBusy("")
			hubRefresh()
		}()
		if process, err := runningBrasfoot(); err == nil && process != "" {
			hubEmit(map[string]any{"type": "error", "operation": "restore", "code": "BF-112", "title": "Feche o Brasfoot", "reason": "O jogo está aberto (" + process + ").", "action": "Salve sua carreira, feche o jogo e tente de novo."})
			return
		}
		safety, err := createGameSnapshot(game, "Automático, antes de restaurar", bundledManifestFromFS().Version, hubProgress("restore", 0, 45, func(int, int) string {
			return "Guardando o estado atual"
		}))
		if err != nil {
			hubFail("restore", err)
			return
		}
		progress := hubProgress("restore", 45, 55, func(done, total int) string { return fmt.Sprintf("Restaurando · %d de %d", done, total) })
		if entry.Kind == backupKindSnapshot {
			err = restoreSnapshot(entry, game, progress)
		} else {
			err = restoreInstallBackup(entry, game, progress)
		}
		if err != nil {
			hubFail("restore", fmt.Errorf("%w (o estado anterior foi guardado no backup de %s)", err, safety.CreatedAt))
			return
		}
		hubEmit(map[string]any{"type": "done", "operation": "restore", "backup": entry, "safety": safety})
	}()
	return nil
}

func hubOpenBackup(id string) error {
	entry, err := findBackup(id)
	if err != nil {
		return err
	}
	command := exec.Command("explorer.exe")
	if entry.Kind == backupKindSnapshot {
		command.SysProcAttr = &syscall.SysProcAttr{CmdLine: `explorer.exe /select,"` + entry.Path + `"`}
	} else {
		command.SysProcAttr = &syscall.SysProcAttr{CmdLine: `explorer.exe "` + entry.Path + `"`}
	}
	return command.Start()
}

func hubLaunchGame() error {
	game := hubCurrentGame()
	if _, _, err := validGame(game); err != nil {
		return errors.New("Escolha uma pasta válida do Brasfoot.")
	}
	if hubIsBusy() {
		return errors.New("Aguarde a operação em andamento terminar.")
	}
	executable := filepath.Join(game, gameExecutablePath)
	if err := checkRegular(executable); err != nil {
		return errors.New("Não encontrei o bf22-23.exe nesta pasta.")
	}
	result, _, _ := shellExecute.Call(hubWindow, uintptr(unsafe.Pointer(strPtr("open"))), uintptr(unsafe.Pointer(strPtr(executable))), 0, uintptr(unsafe.Pointer(strPtr(game))), swShow)
	if result <= 32 {
		return errors.New("Não foi possível abrir o jogo. Abra o Brasfoot pelo atalho da sua instalação.")
	}
	return nil
}

func hubOpenLink(kind string) {
	links := map[string]string{"site": siteURL, "github": repositoryURL, "guide": siteURL + "como-instalar/", "compat": siteURL + "compatibilidade/"}
	if url, ok := links[kind]; ok {
		shellExecute.Call(hubWindow, uintptr(unsafe.Pointer(strPtr("open"))), uintptr(unsafe.Pointer(strPtr(url))), 0, 0, swShow)
	}
}

func hubCopyPix() bool {
	text, err := syscall.UTF16FromString(pixPayload)
	if err != nil {
		return false
	}
	if ok, _, _ := openClipboard.Call(hubWindow); ok == 0 {
		return false
	}
	defer closeClipboard.Call()
	emptyClipboard.Call()
	size := uintptr(len(text) * 2)
	memory, _, _ := globalAlloc.Call(gmemMoveable, size)
	if memory == 0 {
		return false
	}
	pointer, _, _ := globalLock.Call(memory)
	if pointer == 0 {
		return false
	}
	copy(unsafe.Slice((*uint16)(unsafe.Pointer(pointer)), len(text)), text)
	globalUnlock.Call(memory)
	result, _, _ := setClipboardData.Call(cfUnicodeText, memory)
	return result != 0
}

func hubWindowProcedure(window uintptr, message uint32, w, l uintptr) uintptr {
	switch message {
	case wmNcCalcSize:
		if w != 0 {
			return 0
		}
	case wmClose:
		if hubIsBusy() {
			hubEmit(map[string]any{"type": "toast", "message": "Aguarde a operação terminar antes de fechar."})
			return 0
		}
	}
	result, _, _ := callWindowProc.Call(hubOriginalProc, window, uintptr(message), w, l)
	return result
}

func hubFrameless(window uintptr) {
	styleOffset, procOffset := int32(gwlStyle), int32(gwlWndProc)
	styleIndex, procIndex := uintptr(styleOffset), uintptr(procOffset)
	style, _, _ := getWindowLong.Call(window, styleIndex)
	style = (style | wsPopup | wsClipChildren | wsCaption | wsSysMenu | wsMinimizeBox) &^ (wsThickFrame | 0x00010000)
	setWindowLong.Call(window, styleIndex, style)
	hubOriginalProc, _, _ = getWindowLong.Call(window, procIndex)
	setWindowLong.Call(window, procIndex, syscall.NewCallback(hubWindowProcedure))
	if dwm.Load() == nil {
		corner := uint32(dwmCornerRound)
		dwmSetAttribute.Call(window, dwmCornerAttr, uintptr(unsafe.Pointer(&corner)), 4)
		border := uint32(0x00f3e7e1)
		dwmSetAttribute.Call(window, dwmBorderColor, uintptr(unsafe.Pointer(&border)), 4)
		frame := margins{0, 0, 1, 0}
		dwmExtendFrame.Call(window, uintptr(unsafe.Pointer(&frame)))
	}
	x, y, w, h := hubWindowRect()
	setWindowPos.Call(window, 0, uintptr(x), uintptr(y), uintptr(w), uintptr(h), swpNoZOrder|swpFrameChanged)
}

func hubStartsDark() bool {
	switch loadSettings().Theme {
	case "dark":
		return true
	case "light":
		return false
	}
	key, err := registry.OpenKey(registry.CURRENT_USER, `Software\Microsoft\Windows\CurrentVersion\Themes\Personalize`, registry.QUERY_VALUE)
	if err != nil {
		return false
	}
	defer key.Close()
	value, _, err := key.GetIntegerValue("AppsUseLightTheme")
	return err == nil && value == 0
}

func hubDataPath() string {
	root, err := backupRoot()
	if err != nil {
		return ""
	}
	return filepath.Join(filepath.Dir(root), "webview")
}

func runHub() bool {
	if _, err := webviewloader.GetInstalledVersion(); err != nil {
		return false
	}
	root, err := os.MkdirTemp("", "brasfoot-mega-patch-hub-")
	if err != nil {
		return false
	}
	hubStagingRoot = root
	defer os.RemoveAll(root)
	dark := hubStartsDark()
	theme, background := "light", "FFFFFFFF"
	if dark {
		theme, background = "dark", "FF0B1220"
	}
	_ = os.Setenv("WEBVIEW2_DEFAULT_BACKGROUND_COLOR", background)
	showSplash(dark)
	defer closeSplash()
	_, _, width, height := hubWindowRect()
	view := webview2.NewWithOptions(webview2.WebViewOptions{
		DataPath:  hubDataPath(),
		AutoFocus: true,
		WindowOptions: webview2.WindowOptions{
			Title: productName, Width: uint(width), Height: uint(height), IconId: 1, Center: true,
		},
	})
	if view == nil {
		return false
	}
	hubView = view
	hubWindow = uintptr(view.Window())
	hwnd = hubWindow
	hubFrameless(hubWindow)
	hubSetFrameTheme(dark)
	hubGame = findGame()
	bindings := map[string]any{
		"hubInfo":            hubInfo,
		"hubRefresh":         hubRefresh,
		"hubChooseGame":      hubChooseGame,
		"hubInstall":         hubInstall,
		"hubApply":           hubApply,
		"hubImportOriginals": hubImportOriginals,
		"hubGetSettings":     hubGetSettings,
		"hubSetSetting":      hubSetSetting,
		"hubUninstallHub":    hubUninstallHub,
		"hubSetFrameTheme":   hubSetFrameTheme,
		"hubListBackups":     hubListBackups,
		"hubCreateBackup":    hubCreateBackup,
		"hubRestore":         hubRestoreBackup,
		"hubOpenBackup":      hubOpenBackup,
		"hubLaunchGame":      hubLaunchGame,
		"hubOpenLink":        hubOpenLink,
		"hubCopyPix":         hubCopyPix,
		"hubFeed":            func() map[string]any { return hubFeedInfo(false) },
		"hubCheckUpdates":    hubCheckUpdates,
		"hubUpdateHub":       hubUpdateHub,
		"hubOpenExternal":    hubOpenExternal,
		"hubSplashPhase":     splashPhase,
		"hubReady":           closeSplash,
		"hubMinimize":        func() { showWindow.Call(hubWindow, swMinimize) },
		"hubClose": func() bool {
			if hubIsBusy() {
				return false
			}
			postMessage.Call(hubWindow, wmClose, 0, 0)
			return true
		},
		"hubDrag": func() {
			releaseCapture.Call()
			postMessage.Call(hubWindow, wmNcLButtonDown, htCaption, 0)
		},
	}
	for name, function := range bindings {
		if err := view.Bind(name, function); err != nil {
			return false
		}
	}
	page := strings.NewReplacer(
		"{{MARK}}", "data:image/svg+xml;base64,"+base64.StdEncoding.EncodeToString([]byte(hubMark)),
		"{{PITCH}}", "data:image/jpeg;base64,"+base64.StdEncoding.EncodeToString(hubPitch),
		"{{LIVEPITCH}}", hubLivePitch,
		"{{THEME}}", theme,
	).Replace(hubPage)
	view.SetHtml(page)
	if loadSettings().Notify {
		go func() { _ = setNotifications(true) }()
	}
	go func() {
		time.Sleep(300 * time.Millisecond)
		if err := hubCheckUpdates(); err != nil {
			hubRefresh()
		}
	}()
	view.Run()
	return true
}

func main() {
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()
	if setDpiAwarenessCtx.Find() == nil {
		setDpiAwarenessCtx.Call(^uintptr(3))
	}
	o32.NewProc("OleInitialize").Call(0)
	options := parseHubArgs(os.Args[1:])
	if options.NotifyCheck {
		runNotifyCheck()
		return
	}
	if options.Uninstall {
		uninstallHub()
		return
	}
	if ensureHubInstalled(options) {
		return
	}
	if options.Classic {
		runClassic()
		return
	}
	if runHub() {
		return
	}
	if msgbox("A interface moderna precisa do Microsoft Edge WebView2, que não foi encontrado neste computador.\n\nDeseja abrir a página oficial para instalá-lo? Você também pode continuar na interface simples.", productName, mbYesNo|mbIconInfo) == 6 {
		shellExecute.Call(0, uintptr(unsafe.Pointer(strPtr("open"))), uintptr(unsafe.Pointer(strPtr(webviewRuntimeURL))), 0, 0, swShow)
	}
	runClassic()
}
