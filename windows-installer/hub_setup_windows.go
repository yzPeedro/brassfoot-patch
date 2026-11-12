//go:build windows && !hubcli

package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"time"
)

const (
	hubFolderName     = "Brasfoot Mega Patch"
	hubExecutableName = "Brasfoot-Mega-Patch.exe"
	hubUninstallKey   = `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\BrasfootMegaPatchHub`
	createNoWindow    = 0x08000000
	detachedProcess   = 0x00000008
)

type hubOptions struct {
	NotifyCheck bool
	Classic     bool
	Portable    bool
	Uninstall   bool
	Updated     bool
}

func parseHubArgs(args []string) hubOptions {
	options := hubOptions{}
	for i := 0; i < len(args); i++ {
		switch strings.ToLower(args[i]) {
		case "--classic":
			options.Classic = true
		case "--portable":
			options.Portable = true
		case "--uninstall-hub":
			options.Uninstall = true
		case "--updated":
			options.Updated = true
		case "--notify-check":
			options.NotifyCheck = true
		case "--feed":
			if i+1 < len(args) {
				i++
				if absolute, err := filepath.Abs(args[i]); err == nil {
					feedOverride = absolute
				}
			}
		}
	}
	return options
}

func relaunchArgs(extra ...string) []string {
	args := []string{}
	if feedOverride != "" {
		args = append(args, "--feed", feedOverride)
	}
	return append(args, extra...)
}

func hubInstallDir() string {
	root := os.Getenv("LOCALAPPDATA")
	if root == "" {
		return ""
	}
	return filepath.Join(root, "Programs", hubFolderName)
}

func hubInstalledExecutable() string {
	dir := hubInstallDir()
	if dir == "" {
		return ""
	}
	return filepath.Join(dir, hubExecutableName)
}

func installedHubVersion() string {
	var info struct {
		Version string `json:"version"`
	}
	body, err := os.ReadFile(filepath.Join(hubInstallDir(), "hub.json"))
	if err != nil || json.Unmarshal(body, &info) != nil {
		return ""
	}
	return info.Version
}

func writeHubInfo() error {
	body, err := json.MarshalIndent(map[string]string{"version": hubVersion, "installedAt": time.Now().UTC().Format(time.RFC3339)}, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(hubInstallDir(), "hub.json"), body, 0600)
}

func runningFromInstallDir() bool {
	exe, err := os.Executable()
	if err != nil || hubInstallDir() == "" {
		return false
	}
	return sameFolder(filepath.Dir(exe), hubInstallDir())
}

func hiddenCommand(name string, args ...string) *exec.Cmd {
	command := exec.Command(name, args...)
	command.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: createNoWindow}
	return command
}

func startHub(executable string, args []string) error {
	command := exec.Command(executable, args...)
	command.Dir = filepath.Dir(executable)
	return command.Start()
}

func replaceExecutable(target string, write func(string) error) error {
	fresh := target + ".new"
	old := target + ".old"
	_ = os.Remove(fresh)
	if err := write(fresh); err != nil {
		_ = os.Remove(fresh)
		return err
	}
	_ = os.Remove(old)
	if _, err := os.Stat(target); err == nil {
		if err = os.Rename(target, old); err != nil {
			_ = os.Remove(fresh)
			return fmt.Errorf("não foi possível trocar o instalador: %w", err)
		}
	}
	if err := os.Rename(fresh, target); err != nil {
		_ = os.Rename(old, target)
		_ = os.Remove(fresh)
		return fmt.Errorf("não foi possível trocar o instalador: %w", err)
	}
	return nil
}

func cleanupOldExecutable() {
	exe, err := os.Executable()
	if err != nil {
		return
	}
	old := exe + ".old"
	go func() {
		for attempt := 0; attempt < 20; attempt++ {
			if err := os.Remove(old); err == nil || errors.Is(err, os.ErrNotExist) {
				return
			}
			time.Sleep(500 * time.Millisecond)
		}
	}()
}

func psQuote(value string) string {
	return "'" + strings.ReplaceAll(value, "'", "''") + "'"
}

func createHubShortcuts(executable string, desktop bool) error {
	script := "$w=New-Object -ComObject WScript.Shell;" +
		"$targets=@([IO.Path]::Combine($env:APPDATA,'Microsoft\\Windows\\Start Menu\\Programs','" + hubFolderName + ".lnk'));"
	if desktop {
		script += "$targets+=[IO.Path]::Combine([Environment]::GetFolderPath('Desktop'),'" + hubFolderName + ".lnk');"
	}
	script += "foreach($p in $targets){$s=$w.CreateShortcut($p);$s.TargetPath=" + psQuote(executable) +
		";$s.WorkingDirectory=" + psQuote(filepath.Dir(executable)) +
		";$s.IconLocation=" + psQuote(executable+",0") +
		";$s.Description='Instalar, atualizar e jogar o Brasfoot com o Mega Patch';$s.Save()}"
	return hiddenCommand("powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script).Run()
}

func removeHubShortcuts() {
	script := "Remove-Item -LiteralPath ([IO.Path]::Combine($env:APPDATA,'Microsoft\\Windows\\Start Menu\\Programs','" + hubFolderName + ".lnk')) -ErrorAction SilentlyContinue;" +
		"Remove-Item -LiteralPath ([IO.Path]::Combine([Environment]::GetFolderPath('Desktop'),'" + hubFolderName + ".lnk')) -ErrorAction SilentlyContinue"
	_ = hiddenCommand("powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script).Run()
}

func registerHubUninstall(executable string) {
	values := [][2]string{
		{"DisplayName", productName},
		{"DisplayVersion", hubVersion},
		{"Publisher", productName},
		{"DisplayIcon", executable},
		{"InstallLocation", filepath.Dir(executable)},
		{"UninstallString", `"` + executable + `" --uninstall-hub`},
		{"URLInfoAbout", siteURL},
	}
	for _, value := range values {
		_ = hiddenCommand("reg.exe", "add", hubUninstallKey, "/v", value[0], "/t", "REG_SZ", "/d", value[1], "/f").Run()
	}
	for _, name := range []string{"NoModify", "NoRepair"} {
		_ = hiddenCommand("reg.exe", "add", hubUninstallKey, "/v", name, "/t", "REG_DWORD", "/d", "1", "/f").Run()
	}
	registerProtocol(executable)
}

func ensureHubInstalled(options hubOptions) bool {
	if options.Portable || options.Uninstall {
		return false
	}
	if runningFromInstallDir() {
		cleanupOldExecutable()
		return false
	}
	installed := hubInstalledExecutable()
	if installed == "" {
		return false
	}
	current, err := os.Executable()
	if err != nil {
		return false
	}
	firstInstall := false
	if _, statErr := os.Stat(installed); statErr != nil {
		firstInstall = true
	}
	if !firstInstall && compareVersions(installedHubVersion(), hubVersion) > 0 {
		return startHub(installed, relaunchArgs()) == nil
	}
	if err = os.MkdirAll(filepath.Dir(installed), 0755); err != nil {
		return false
	}
	if err = replaceExecutable(installed, func(path string) error { return copyFile(current, path) }); err != nil {
		return false
	}
	_ = writeHubInfo()
	_ = createHubShortcuts(installed, firstInstall)
	registerHubUninstall(installed)
	return startHub(installed, relaunchArgs()) == nil
}

func uninstallHub() {
	if msgbox("Remover o hub do Brasfoot Mega Patch deste computador?\n\nO jogo, os seus saves e os backups do patch não são apagados. Para desfazer o patch no jogo, restaure um backup antes de remover o hub.", productName, mbYesNo|mbIconWarning|mbDefaultButton2) != 6 {
		return
	}
	removeHubShortcuts()
	_ = setNotifications(false)
	_ = hiddenCommand("reg.exe", "delete", protocolKey, "/f").Run()
	_ = hiddenCommand("reg.exe", "delete", hubUninstallKey, "/f").Run()
	dir := hubInstallDir()
	if dir != "" && runningFromInstallDir() {
		command := exec.Command("cmd.exe", "/c", "ping -n 3 127.0.0.1 >nul & rmdir /s /q \""+dir+"\"")
		command.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: createNoWindow | detachedProcess}
		_ = command.Start()
	}
	msgbox("O hub foi removido. Seus backups continuam em %LOCALAPPDATA%\\BrassfootPatch2026.", productName, mbOK|mbIconInfo)
}

func applyHubUpdate(feed ReleaseFeed, progress func(done, total int64)) error {
	asset, ok := feed.Hub.Assets[hubAssetKey()]
	if !ok {
		return errors.New("não há instalador novo para este sistema")
	}
	data, err := loadAsset(feed, asset, false, progress)
	if err != nil {
		return err
	}
	target, err := os.Executable()
	if err != nil {
		return err
	}
	if err = replaceExecutable(target, func(path string) error { return os.WriteFile(path, data, 0755) }); err != nil {
		return err
	}
	if runningFromInstallDir() {
		previous := hubVersion
		hubVersion = feed.Hub.Version
		_ = writeHubInfo()
		registerHubUninstall(target)
		hubVersion = previous
	}
	return startHub(target, relaunchArgs("--updated"))
}
