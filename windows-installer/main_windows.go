//go:build windows

package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"unsafe"
)

// Only a single folder is requested from the user. The private candidate is
// already embedded and is verified before any game data is changed.
const (
	wsChild           = 0x40000000
	wsVisible         = 0x10000000
	wsBorder          = 0x00800000
	wsCaption         = 0x00c00000
	wsSysMenu         = 0x00080000
	wsMinimizeBox     = 0x00020000
	wsTabStop         = 0x00010000
	esAutoHScroll     = 0x0080
	wmCreate          = 0x0001
	wmDestroy         = 0x0002
	wmClose           = 0x0010
	wmCommand         = 0x0111
	wmCtlColorStatic  = 0x0138
	wmSetFont         = 0x0030
	wmAppEvent        = 0x8001
	mbOK              = 0
	mbYesNo           = 4
	mbIconWarning     = 0x30
	mbIconInfo        = 0x40
	mbDefaultButton2  = 0x100
	swShow            = 5
	colorTransparent  = 1
	idChooseGame      = 301
	idInstall         = 302
	idDiagnose        = 303
	idDetails         = 304
	idBackup          = 305
	idRestore         = 306
	idPix             = 307
	pbmSetRange32     = 0x0406
	pbmSetPos         = 0x0402
	iccProgressClass  = 0x20
	th32csSnapProcess = 0x2
	width             = 916
	height            = 660
)

var (
	u32    = syscall.NewLazyDLL("user32.dll")
	k32    = syscall.NewLazyDLL("kernel32.dll")
	g32    = syscall.NewLazyDLL("gdi32.dll")
	s32    = syscall.NewLazyDLL("shell32.dll")
	o32    = syscall.NewLazyDLL("ole32.dll")
	comctl = syscall.NewLazyDLL("comctl32.dll")

	registerClass      = u32.NewProc("RegisterClassExW")
	createWindow       = u32.NewProc("CreateWindowExW")
	defWindow          = u32.NewProc("DefWindowProcW")
	showWindow         = u32.NewProc("ShowWindow")
	updateWindow       = u32.NewProc("UpdateWindow")
	getMessage         = u32.NewProc("GetMessageW")
	translateMessage   = u32.NewProc("TranslateMessage")
	dispatchMessage    = u32.NewProc("DispatchMessageW")
	quitMessage        = u32.NewProc("PostQuitMessage")
	postMessage        = u32.NewProc("PostMessageW")
	messageBox         = u32.NewProc("MessageBoxW")
	setWindowText      = u32.NewProc("SetWindowTextW")
	getWindowText      = u32.NewProc("GetWindowTextW")
	sendMessage        = u32.NewProc("SendMessageW")
	enableWindow       = u32.NewProc("EnableWindow")
	setTextColor       = g32.NewProc("SetTextColor")
	setBkMode          = g32.NewProc("SetBkMode")
	newBrush           = g32.NewProc("CreateSolidBrush")
	newFont            = g32.NewProc("CreateFontW")
	getModule          = k32.NewProc("GetModuleHandleW")
	browseFolder       = s32.NewProc("SHBrowseForFolderW")
	pathFromID         = s32.NewProc("SHGetPathFromIDListW")
	memFree            = o32.NewProc("CoTaskMemFree")
	adjustWindowRect   = u32.NewProc("AdjustWindowRect")
	getSystemMetrics   = u32.NewProc("GetSystemMetrics")
	getDpiForSystem    = u32.NewProc("GetDpiForSystem")
	setProcessDpiAware = u32.NewProc("SetProcessDPIAware")
	createSnapshot     = k32.NewProc("CreateToolhelp32Snapshot")
	processFirst       = k32.NewProc("Process32FirstW")
	processNext        = k32.NewProc("Process32NextW")
	closeHandle        = k32.NewProc("CloseHandle")
	initCommon         = comctl.NewProc("InitCommonControlsEx")

	hwnd            uintptr
	gameEdit        uintptr
	gameBrowse      uintptr
	installButton   uintptr
	diagnoseButton  uintptr
	detailButton    uintptr
	backupButton    uintptr
	restoreButton   uintptr
	progressBar     uintptr
	progressText    uintptr
	statusHeading   uintptr
	statusReason    uintptr
	statusAction    uintptr
	darkBrush       uintptr
	labelColors     = map[uintptr]uintptr{}
	bodyFont        uintptr
	strongFont      uintptr
	headingFont     uintptr
	smallFont       uintptr
	embeddedPayload string
	embeddedRoot    string
	backupPath      string
	restoreAllowed  bool
	restorePlan     Plan
	running         bool
	lastDiagnostic  Diagnostic
	events                  = make(chan guiEvent, 128)
	scale           float64 = 1
)

const (
	limeR, limeG, limeB    = 197, 255, 105
	whiteR, whiteG, whiteB = 238, 246, 237
)

type guiEvent struct {
	kind        string
	plan        Plan
	result      InstallResult
	diagnostic  Diagnostic
	stage       string
	done, total int
}

type winClass struct {
	Size                               uint32
	Style                              uint32
	Procedure                          uintptr
	ClassExtra, WindowExtra            int32
	Instance, Icon, Cursor, Background uintptr
	MenuName, ClassName                *uint16
	SmallIcon                          uintptr
}
type winMessage struct {
	Hwnd           uintptr
	Msg            uint32
	Padding        uint32
	WParam, LParam uintptr
	Time           uint32
	X, Y           int32
	Private        uint32
}
type rect struct{ Left, Top, Right, Bottom int32 }
type browseInfo struct {
	HwndOwner, Root, DisplayName, Title uintptr
	Flags                               uint32
	Padding                             uint32
	Callback, LParam                    uintptr
	Image                               int32
	Pad2                                uint32
}
type processEntry struct {
	Size         uint32
	Usage        uint32
	PID          uint32
	DefaultHeap  uintptr
	ModuleID     uint32
	Threads      uint32
	ParentPID    uint32
	BasePriority int32
	Flags        uint32
	Executable   [260]uint16
}

type commonControls struct {
	Size  uint32
	Flags uint32
}

func strPtr(s string) *uint16    { return syscall.StringToUTF16Ptr(s) }
func color(r, g, b byte) uintptr { return uintptr(r) | uintptr(g)<<8 | uintptr(b)<<16 }
func S(v int) int                { return int(float64(v)*scale + 0.5) }
func setText(h uintptr, text string) {
	if h != 0 {
		setWindowText.Call(h, uintptr(unsafe.Pointer(strPtr(text))))
	}
}
func msgbox(text, title string, style uintptr) int {
	ret, _, _ := messageBox.Call(hwnd, uintptr(unsafe.Pointer(strPtr(text))), uintptr(unsafe.Pointer(strPtr(title))), style)
	return int(ret)
}
func getText(h uintptr) string {
	buf := make([]uint16, 32768)
	n, _, _ := getWindowText.Call(h, uintptr(unsafe.Pointer(&buf[0])), uintptr(len(buf)))
	return syscall.UTF16ToString(buf[:n])
}
func create(class, text string, style uintptr, x, y, w, h, id int, font uintptr) uintptr {
	inst, _, _ := getModule.Call(0)
	handle, _, _ := createWindow.Call(0, uintptr(unsafe.Pointer(strPtr(class))), uintptr(unsafe.Pointer(strPtr(text))),
		style, uintptr(S(x)), uintptr(S(y)), uintptr(S(w)), uintptr(S(h)), hwnd, uintptr(id), inst, 0)
	if handle != 0 && font != 0 {
		sendMessage.Call(handle, wmSetFont, font, 1)
	}
	return handle
}
func textLabel(text string, x, y, w, h int, colorValue uintptr, font uintptr) uintptr {
	handle := create("STATIC", text, wsVisible|wsChild, x, y, w, h, 0, font)
	labelColors[handle] = colorValue
	return handle
}
func setStatus(title, reason, action string, isError bool) {
	setText(statusHeading, title)
	setText(statusReason, reason)
	setText(statusAction, action)
	if isError {
		labelColors[statusHeading] = color(255, 173, 151)
	} else {
		labelColors[statusHeading] = color(limeR, limeG, limeB)
	}
	updateWindow.Call(statusHeading)
	updateWindow.Call(statusReason)
	updateWindow.Call(statusAction)
}
func setBusy(b bool) {
	running = b
	for _, h := range []uintptr{gameEdit, gameBrowse, installButton, diagnoseButton} {
		if b {
			enableWindow.Call(h, 0)
		} else {
			enableWindow.Call(h, 1)
		}
	}
	if b || !restoreAllowed {
		enableWindow.Call(restoreButton, 0)
	} else {
		enableWindow.Call(restoreButton, 1)
	}
}
func post(ev guiEvent) {
	events <- ev
	postMessage.Call(hwnd, wmAppEvent, 0, 0)
}
func showProgress(p int, label string) {
	if p < 0 {
		p = 0
	}
	if p > 100 {
		p = 100
	}
	if progressBar != 0 {
		sendMessage.Call(progressBar, pbmSetPos, uintptr(p), 0)
	}
	setText(progressText, fmt.Sprintf("%d%%  ·  %s", p, label))
}
func chooseFolder(title string) string {
	var display [260]uint16
	info := browseInfo{HwndOwner: hwnd, DisplayName: uintptr(unsafe.Pointer(&display[0])),
		Title: uintptr(unsafe.Pointer(strPtr(title))), Flags: 0x41}
	id, _, _ := browseFolder.Call(uintptr(unsafe.Pointer(&info)))
	if id == 0 {
		return ""
	}
	defer memFree.Call(id)
	var buf [32768]uint16
	ok, _, _ := pathFromID.Call(id, uintptr(unsafe.Pointer(&buf[0])))
	if ok == 0 {
		return ""
	}
	return syscall.UTF16ToString(buf[:])
}

// Windows process enumeration prevents modifications while Brasfoot is open.
func runningBrasfoot() (string, error) {
	snap, _, err := createSnapshot.Call(th32csSnapProcess, 0)
	if snap == ^uintptr(0) {
		return "", err
	}
	defer closeHandle.Call(snap)
	p := processEntry{Size: uint32(unsafe.Sizeof(processEntry{}))}
	ok, _, _ := processFirst.Call(snap, uintptr(unsafe.Pointer(&p)))
	for ok != 0 {
		exe := syscall.UTF16ToString(p.Executable[:])
		if strings.Contains(strings.ToLower(exe), "brasfoot") || strings.EqualFold(exe, "bf22-23.exe") {
			return exe, nil
		}
		ok, _, _ = processNext.Call(snap, uintptr(unsafe.Pointer(&p)))
	}
	return "", nil
}

func normalizeGameSelection(path string) string {
	path = filepath.Clean(strings.TrimSpace(path))
	if strings.EqualFold(filepath.Base(path), "teams") {
		parent := filepath.Dir(path)
		if _, err := os.Stat(filepath.Join(parent, "options.bcf")); err == nil {
			return parent
		}
	}
	return path
}

func perform(id int) {
	if running && id != idDetails && id != idPix {
		return
	}
	switch id {
	case idPix:
		showPixDialog()
	case idChooseGame:
		if p := chooseFolder("Selecione a pasta principal do Brasfoot"); p != "" {
			setText(gameEdit, p)
			restoreAllowed = false
			restorePlan = Plan{}
			enableWindow.Call(restoreButton, 0)
			setStatus("PASTA SELECIONADA", "Pronto para conferir automaticamente o jogo e os elencos.", "Clique em INSTALAR PATCH para iniciar.", false)
			showProgress(0, "Aguardando instalação")
		}
	case idInstall, idDiagnose:
		restoreAllowed = false
		restorePlan = Plan{}
		enableWindow.Call(restoreButton, 0)
		game := strings.TrimSpace(getText(gameEdit))
		if game != "" {
			game = normalizeGameSelection(game)
			setText(gameEdit, game)
		}
		if game == "" {
			d := Diagnostic{"BF-100", "Selecione a pasta do Brasfoot", "Nenhuma instalação foi encontrada automaticamente.", "Clique em PROCURAR e escolha a pasta principal do jogo (por exemplo C:\\Brasfoot22-23).", "Caminho vazio"}
			displayError(d)
			return
		}
		setBusy(true)
		setStatus("VERIFICANDO O JOGO", "Conferindo pastas, arquivos originais e integridade do pacote...", "Nenhum save ou configuração pessoal será alterado.", false)
		showProgress(0, "Verificando compatibilidade")
		go func() {
			if e := prepareBundledPayload(game, embeddedPayload); e != nil {
				post(guiEvent{kind: "failed", diagnostic: diagnose(e)})
				return
			}
			p, e := inspect(embeddedPayload, game)
			if e != nil {
				post(guiEvent{kind: "failed", diagnostic: diagnose(e)})
				return
			}
			if id == idDiagnose {
				post(guiEvent{kind: "checked", plan: p})
				return
			}
			post(guiEvent{kind: "ready", plan: p})
		}()
	case idDetails:
		if lastDiagnostic.Code != "" {
			msgbox(lastDiagnostic.Full(), "Brassfoot Patch — Diagnóstico "+lastDiagnostic.Code, mbOK|mbIconInfo)
		} else {
			msgbox("Nenhum erro registrado. Escolha a pasta do Brasfoot e clique em INSTALAR PATCH.", "Diagnóstico", mbOK|mbIconInfo)
		}
	case idBackup:
		if backupPath != "" {
			_ = exec.Command("explorer.exe", backupPath).Start()
		}
	case idRestore:
		if !restoreAllowed || !restorePlan.AlreadyInstalled {
			return
		}
		if process, e := runningBrasfoot(); e == nil && process != "" {
			displayError(Diagnostic{"BF-112", "Feche o Brasfoot antes de restaurar", "O jogo está aberto: " + process, "Salve e feche o Brasfoot; então tente novamente.", process})
			return
		}
		if msgbox("Isto vai restaurar os 20 arquivos originais das equipes a partir do backup conferido. Os arquivos da sua carreira e suas configurações NÃO serão alterados.\n\nDeseja DESFAZER o patch?", "Restaurar elencos originais", mbYesNo|mbIconWarning|mbDefaultButton2) != 6 {
			return
		}
		setBusy(true)
		setStatus("RESTAURANDO OS ELENCOS ORIGINAIS", "Conferindo os backups e revertendo apenas os arquivos teams/*.ban...", "Não feche a janela até a verificação final.", false)
		showProgress(0, "Iniciando restauração")
		go func(plan Plan) {
			if process, e := runningBrasfoot(); e == nil && process != "" {
				post(guiEvent{kind: "failed", diagnostic: Diagnostic{"BF-112", "Brasfoot em execução", "Processo aberto: " + process, "Feche o Brasfoot e tente novamente.", process}})
				return
			}
			backup, e := restorePatch(plan, func(done, total int) { post(guiEvent{kind: "progress", stage: "restore", done: done, total: total}) })
			if e != nil {
				post(guiEvent{kind: "failed", diagnostic: diagnose(e)})
				return
			}
			post(guiEvent{kind: "restored", result: InstallResult{Status: "restored", BackupPath: backup, Files: len(plan.Items)}})
		}(restorePlan)
	}
}
func displayError(d Diagnostic) {
	lastDiagnostic = d
	setStatus(d.Code+"  |  "+d.Title, d.Reason, "COMO RESOLVER: "+d.Action, true)
	showProgress(0, "Instalação bloqueada — arquivos originais preservados")
	enableWindow.Call(detailButton, 1)
}
func enableRestoreIfAvailable(plan Plan) {
	restoreAllowed = false
	restorePlan = Plan{}
	enableWindow.Call(restoreButton, 0)
	if !plan.AlreadyInstalled {
		return
	}
	if _, _, err := findRestorableBackup(plan); err == nil {
		restoreAllowed = true
		restorePlan = plan
		enableWindow.Call(restoreButton, 1)
	}
}
func onEvent(ev guiEvent) {
	switch ev.kind {
	case "failed":
		setBusy(false)
		displayError(ev.diagnostic)
	case "checked":
		setBusy(false)
		enableRestoreIfAvailable(ev.plan)
		lastDiagnostic = Diagnostic{Code: "BF-OK", Title: "Instalação compatível", Reason: "Hashes originais e arquivos do patch verificados.", Action: "Clique em VERIFICAR E INSTALAR PATCH para instalar automaticamente."}
		if ev.plan.AlreadyInstalled {
			next := "O backup original não está disponível para restauração automática. Nenhum arquivo foi alterado."
			if restoreAllowed {
				next = "Backup original encontrado. Use DESFAZER PATCH se quiser retornar à versão anterior."
			}
			setStatus("PATCH JÁ INSTALADO", fmt.Sprintf("A versão %s já está aplicada às %d equipes.", ev.plan.Manifest.Version, len(ev.plan.Items)), next, false)
			showProgress(100, "Patch já instalado")
		} else {
			setStatus("INSTALAÇÃO RECONHECIDA", fmt.Sprintf("%d equipes verificadas. Versão %s; integridade confirmada.", len(ev.plan.Items), ev.plan.Manifest.Version), "Pronto para instalar. Backups ficarão fora da pasta do jogo.", false)
			showProgress(0, "Pronto para instalar")
		}
		enableWindow.Call(detailButton, 1)
	case "ready":
		if ev.plan.AlreadyInstalled {
			setBusy(false)
			enableRestoreIfAvailable(ev.plan)
			next := "Saves e configurações não foram modificados. Nenhum backup compatível foi localizado."
			if restoreAllowed {
				next = "Backup íntegro localizado. Clique em DESFAZER PATCH para restaurar as equipes originais."
			}
			setStatus("PATCH JÁ INSTALADO", fmt.Sprintf("A versão %s já está aplicada aos %d clubes. Nenhum arquivo foi alterado.", ev.plan.Manifest.Version, len(ev.plan.Items)), next, false)
			showProgress(100, "Nenhuma atualização necessária")
			return
		}
		if process, err := runningBrasfoot(); err == nil && process != "" {
			setBusy(false)
			displayError(Diagnostic{"BF-112", "O Brasfoot está aberto", "Detectei o processo " + process + " em execução.", "Salve sua carreira, feche o Brasfoot e tente novamente. O instalador não alterou nada.", "Processo: " + process})
			return
		}
		// Explicit consent remains necessary because this is a PRIVATE, unverified roster preview.
		warning := fmt.Sprintf("Jogo detectado e %d arquivos de equipes verificados.\n\nEsta é uma PRÉVIA COM DADOS ESTIMADOS: 713 jogadores têm atributos estimados.\n\nO instalador vai substituir SOMENTE os %d arquivos .ban aprovados em teams/. Vai salvar antes backups íntegros em AppData; NÃO vai editar saves, carreiras ou configurações.\n\nSalve e FECHE o Brasfoot antes de continuar.\n\nDeseja instalar na pasta selecionada?", len(ev.plan.Items), len(ev.plan.Items))
		if msgbox(warning, "Confirmar atualização de elencos", mbYesNo|mbIconWarning|mbDefaultButton2) != 6 {
			setBusy(false)
			setStatus("INSTALAÇÃO CANCELADA", "Nenhum arquivo do Brasfoot foi modificado.", "Quando estiver pronto, clique novamente em INSTALAR PATCH.", false)
			showProgress(0, "Aguardando confirmação")
			return
		}
		setStatus("CRIANDO BACKUPS VERIFICADOS", "O patch está sendo aplicado apenas nos arquivos .ban dos clubes selecionados.", "Não feche esta janela até a confirmação final.", false)
		showProgress(0, "Preparando instalação")
		go func(p Plan) {
			if process, err := runningBrasfoot(); err == nil && process != "" {
				post(guiEvent{kind: "failed", diagnostic: Diagnostic{"BF-112", "Brasfoot em execução", "Processo aberto: " + process, "Feche o jogo e tente novamente.", process}})
				return
			}
			result, err := install(p, InstallOptions{Progress: func(stage string, done, total int) {
				post(guiEvent{kind: "progress", stage: stage, done: done, total: total})
			}})
			if err != nil {
				post(guiEvent{kind: "failed", diagnostic: diagnose(err)})
				return
			}
			post(guiEvent{kind: "installed", result: result})
		}(ev.plan)
	case "progress":
		if ev.total <= 0 {
			return
		}
		// Progress represents *completed* backup and replacement work only.
		switch ev.stage {
		case "backup":
			showProgress(10+int(40*float64(ev.done)/float64(ev.total)), fmt.Sprintf("Backup %d de %d equipes", ev.done, ev.total))
		case "install":
			showProgress(50+int(49*float64(ev.done)/float64(ev.total)), fmt.Sprintf("Aplicando e verificando %d de %d equipes", ev.done, ev.total))
		case "done":
			showProgress(100, "Verificação final concluída")
		case "restore":
			showProgress(int(99*float64(ev.done)/float64(ev.total)), fmt.Sprintf("Restaurando %d de %d equipes", ev.done, ev.total))
		}
	case "installed":
		setBusy(false)
		// For undo, re-inspect the now-installed files and ensure a backup exists.
		if p, e := inspect(embeddedPayload, strings.TrimSpace(getText(gameEdit))); e == nil {
			enableRestoreIfAvailable(p)
		}
		backupPath = ev.result.BackupPath
		enableWindow.Call(backupButton, 1)
		setStatus("PATCH APLICADO E VERIFICADO", fmt.Sprintf("%d equipes atualizadas na versão %s. Arquivos originais salvos com segurança.", ev.result.Files, ev.result.Version), "Agora abra o Brasfoot, inicie uma NOVA carreira e teste os clubes. Seus saves anteriores não foram alterados.", false)
		showProgress(100, "Arquivos e hashes verificados")
		msgbox("A instalação terminou e os arquivos substituídos foram conferidos por SHA-256.\n\nBackups: "+backupPath+"\n\nTeste em uma carreira nova antes de usar seus saves antigos. A compatibilidade foi testada pelo criador do patch; elencos incluem atributos estimados.", "Instalação técnica concluída", mbOK|mbIconInfo)
	case "restored":
		setBusy(false)
		restoreAllowed = false
		restorePlan = Plan{}
		enableWindow.Call(restoreButton, 0)
		backupPath = ev.result.BackupPath
		enableWindow.Call(backupButton, 1)
		setStatus("ELENCOS ORIGINAIS RESTAURADOS", fmt.Sprintf("Os %d arquivos .ban originais foram restaurados e tiveram seus hashes conferidos.", ev.result.Files), "Seus saves e configurações não foram modificados. O backup continua disponível.", false)
		showProgress(100, "Restauração e hashes confirmados")
		msgbox("Arquivos originais restaurados com sucesso.\n\nBackups preservados em: "+backupPath, "Patch desfeito", mbOK|mbIconInfo)
	}
}

func findGame() string {
	candidates := []string{`C:\Brasfoot22-23`, `C:\Brasfoot 2022-2023`, `C:\Brasfoot2022-2023`}
	for _, key := range []string{"ProgramFiles", "ProgramFiles(x86)"} {
		if root := os.Getenv(key); root != "" {
			for _, sub := range []string{"Brasfoot22-23", "Brasfoot 2022-2023", "Brasfoot"} {
				candidates = append(candidates, filepath.Join(root, sub))
			}
		}
	}
	for _, p := range candidates {
		if _, _, err := validGame(p); err == nil {
			return p
		}
	}
	return ""
}

func labelColor(h uintptr, colorCode uintptr) { labelColors[h] = colorCode }
func setupControls() {
	green := color(limeR, limeG, limeB)
	white := color(whiteR, whiteG, whiteB)
	muted := color(177, 197, 185)
	yellow := color(255, 218, 117)
	labelColor(textLabel("BRASSFOOT PATCH 2026", 37, 26, 830, 48, green, headingFont), green)
	textLabel("INSTALADOR WINDOWS   /   PRÉVIA 2026.0.2 — ACOMPANHE LIMITAÇÕES", 39, 80, 830, 25, muted, bodyFont)
	textLabel("01   SELECIONE A PASTA DO JOGO", 40, 130, 830, 29, green, strongFont)
	gameEdit = create("EDIT", findGame(), wsChild|wsVisible|wsBorder|wsTabStop|esAutoHScroll, 40, 166, 682, 38, 0, bodyFont)
	gameBrowse = create("BUTTON", "PROCURAR…", wsChild|wsVisible|wsTabStop, 735, 165, 143, 40, idChooseGame, bodyFont)
	textLabel("Exemplo: C:\\Brasfoot22-23  ·  Detectamos a instalação automaticamente quando possível.", 41, 216, 835, 25, muted, smallFont)
	textLabel("02   PATCH INCLUSO NO INSTALADOR", 40, 264, 835, 29, green, strongFont)
	textLabel("20 clubes brasileiros  •  730 atletas  •  Temporada 2026", 41, 300, 835, 29, white, bodyFont)
	textLabel("PRÉVIA EXPERIMENTAL: 713 jogadores com atributos estimados. Compatibilidade testada; dados ainda estimados.", 41, 332, 838, 44, yellow, smallFont)
	installButton = create("BUTTON", "VERIFICAR E INSTALAR PATCH", wsChild|wsVisible|wsTabStop, 40, 390, 322, 46, idInstall, strongFont)
	diagnoseButton = create("BUTTON", "SÓ VERIFICAR", wsChild|wsVisible|wsTabStop, 376, 390, 167, 46, idDiagnose, bodyFont)
	restoreButton = create("BUTTON", "DESFAZER PATCH", wsChild|wsVisible|wsTabStop, 553, 390, 154, 46, idRestore, smallFont)
	enableWindow.Call(restoreButton, 0)
	backupButton = create("BUTTON", "ABRIR BACKUP", wsChild|wsVisible|wsTabStop, 719, 390, 159, 46, idBackup, bodyFont)
	enableWindow.Call(backupButton, 0)
	c := commonControls{Size: uint32(unsafe.Sizeof(commonControls{})), Flags: iccProgressClass}
	initCommon.Call(uintptr(unsafe.Pointer(&c)))
	progressBar = create("msctls_progress32", "", wsChild|wsVisible, 40, 460, 838, 17, 0, 0)
	sendMessage.Call(progressBar, pbmSetRange32, 0, 100)
	progressText = textLabel("0%  ·  Aguardando instalação", 40, 484, 830, 23, muted, smallFont)
	statusHeading = textLabel("PRONTO PARA COMEÇAR", 40, 523, 675, 27, green, strongFont)
	statusReason = textLabel("Selecione a pasta do Brasfoot. O instalador verificará o jogo, o pacote e fará backup automaticamente.", 40, 556, 837, 38, white, smallFont)
	statusAction = textLabel("Somente arquivos assinados serão alterados. Saves e configurações pessoais serão preservados.", 40, 600, 685, 48, muted, smallFont)
	create("BUTTON", "☕ PIX OPCIONAL", wsChild|wsVisible|wsTabStop, 737, 600, 140, 36, idPix, smallFont)
	detailButton = create("BUTTON", "DETALHES", wsChild|wsVisible|wsTabStop, 735, 520, 143, 28, idDetails, smallFont)
	enableWindow.Call(detailButton, 0)
	if getText(gameEdit) == "" {
		setStatus("LOCALIZAÇÃO NÃO ENCONTRADA", "Não localizei o Brasfoot automaticamente. Isso não significa que o jogo esteja com defeito.", "Clique em PROCURAR e selecione a pasta onde o Brasfoot está instalado.", false)
	}
}
func windowProcedure(h uintptr, msg uint32, w, l uintptr) uintptr {
	switch msg {
	case wmCreate:
		hwnd = h
		setupControls()
		return 0
	case wmCommand:
		id := int(w & 0xffff)
		switch id {
		case idChooseGame, idInstall, idDiagnose, idDetails, idBackup, idRestore, idPix:
			perform(id)
			return 0
		}
	case wmAppEvent:
		for {
			select {
			case ev := <-events:
				onEvent(ev)
			default:
				return 0
			}
		}
	case wmCtlColorStatic:
		setBkMode.Call(w, colorTransparent)
		tint, ok := labelColors[l]
		if !ok {
			tint = color(whiteR, whiteG, whiteB)
		}
		setTextColor.Call(w, tint)
		return darkBrush
	case wmClose:
		if running {
			msgbox("O instalador está verificando/atualizando arquivos. Aguarde a confirmação final antes de fechar, para preservar seus dados.", "Instalação em andamento", mbOK|mbIconWarning)
			return 0
		}
	case wmDestroy:
		quitMessage.Call(0)
		return 0
	}
	ret, _, _ := defWindow.Call(h, uintptr(msg), w, l)
	return ret
}
func main() {
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()
	setProcessDpiAware.Call()
	if getDpiForSystem.Find() == nil {
		dpi, _, _ := getDpiForSystem.Call()
		if dpi >= 96 && dpi <= 384 {
			scale = float64(dpi) / 96
		}
	}
	// Never place controls below the screen on laptops or high-DPI monitors.
	sw, _, _ := getSystemMetrics.Call(0)
	sh, _, _ := getSystemMetrics.Call(1)
	screenFit := func(available, desired int) float64 { return float64(available) / float64(desired) }
	if fit := screenFit(int(sw)-30, width+20); fit < scale {
		scale = fit
	}
	if fit := screenFit(int(sh)-65, height+45); fit < scale {
		scale = fit
	}
	if scale < 0.70 {
		scale = 0.70
	}
	oleInitialize := o32.NewProc("OleInitialize")
	oleUninitialize := o32.NewProc("OleUninitialize")
	oleInitialize.Call(0)
	defer oleUninitialize.Call()
	payload, err := stageBundledPayload()
	if err != nil {
		msgbox("O pacote interno não pôde ser extraído. Instalação cancelada.\n\n"+err.Error(), "Brassfoot Patch — Falha do pacote", mbOK|mbIconWarning)
		return
	}
	embeddedPayload = payload
	embeddedRoot = filepath.Dir(payload)
	defer os.RemoveAll(embeddedRoot)
	darkBrush, _, _ = newBrush.Call(color(7, 27, 24))
	font := func(px, weight int) uintptr {
		h, _, _ := newFont.Call(uintptr(int32(-S(px))), 0, 0, 0, uintptr(weight), 0, 0, 0, 0, 0, 0, 0, 0, uintptr(unsafe.Pointer(strPtr("Segoe UI"))))
		return h
	}
	headingFont = font(34, 800)
	strongFont = font(20, 700)
	bodyFont = font(19, 500)
	smallFont = font(17, 400)
	inst, _, _ := getModule.Call(0)
	cls := strPtr("BrassfootPatch2026FixedWindow")
	wc := winClass{Size: uint32(unsafe.Sizeof(winClass{})), Procedure: syscall.NewCallback(windowProcedure), Instance: inst, Background: darkBrush, ClassName: cls}
	ok, _, classErr := registerClass.Call(uintptr(unsafe.Pointer(&wc)))
	if ok == 0 {
		msgbox("Não foi possível iniciar a interface: "+classErr.Error(), "Brasfoot Patch", mbOK|mbIconWarning)
		return
	}
	style := uintptr(wsCaption | wsSysMenu | wsMinimizeBox) // fixed size: no resize border, no maximize button.
	r := rect{Right: int32(S(width)), Bottom: int32(S(height))}
	adjustWindowRect.Call(uintptr(unsafe.Pointer(&r)), style, 0)
	ow, oh := int(r.Right-r.Left), int(r.Bottom-r.Top)
	x, y := (int(sw)-ow)/2, (int(sh)-oh)/2
	if x < 0 {
		x = 0
	}
	if y < 0 {
		y = 0
	}
	window, _, createErr := createWindow.Call(0, uintptr(unsafe.Pointer(cls)), uintptr(unsafe.Pointer(strPtr("Brasfoot Patch 2026 — Atualização de elencos"))), style|wsVisible,
		uintptr(x), uintptr(y), uintptr(ow), uintptr(oh), 0, 0, inst, 0)
	if window == 0 {
		msgbox("Não foi possível abrir a janela: "+createErr.Error(), "Brasfoot Patch", mbOK|mbIconWarning)
		return
	}
	hwnd = window
	showWindow.Call(window, swShow)
	updateWindow.Call(window)
	var message winMessage
	for {
		n, _, _ := getMessage.Call(uintptr(unsafe.Pointer(&message)), 0, 0, 0)
		if int32(n) <= 0 {
			break
		}
		translateMessage.Call(uintptr(unsafe.Pointer(&message)))
		dispatchMessage.Call(uintptr(unsafe.Pointer(&message)))
	}
}
