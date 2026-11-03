//go:build windows

package main

import (
	"os"
	"path/filepath"
	"strings"
	"time"
	"unicode/utf16"
)

const (
	notifyRunKey      = `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
	notifyRunValue    = "BrasfootMegaPatchNovidades"
	notifyTaskName    = `Brasfoot Mega Patch\Novidades`
	protocolKey       = `HKCU\Software\Classes\brasfootmegapatch`
	notifyAppID       = "yzPeedro.BrasfootMegaPatch"
	notifyAppKey      = `HKCU\Software\Classes\AppUserModelId\` + notifyAppID
)

func notificationExecutable() string {
	if installed := hubInstalledExecutable(); installed != "" && runningFromInstallDir() {
		return installed
	}
	exe, err := os.Executable()
	if err != nil {
		return ""
	}
	return exe
}

func registerProtocol(executable string) {
	_ = hiddenCommand("reg.exe", "add", protocolKey, "/ve", "/t", "REG_SZ", "/d", "URL:Brasfoot Mega Patch", "/f").Run()
	_ = hiddenCommand("reg.exe", "add", protocolKey, "/v", "URL Protocol", "/t", "REG_SZ", "/d", "", "/f").Run()
	_ = hiddenCommand("reg.exe", "add", protocolKey+`\shell\open\command`, "/ve", "/t", "REG_SZ", "/d", `"`+executable+`" "%1"`, "/f").Run()
}

func registerNotifyApp() {
	root, err := backupRoot()
	if err != nil {
		return
	}
	icon := filepath.Join(filepath.Dir(root), "notify-icon.png")
	if current, err := os.ReadFile(icon); err != nil || string(current) != string(splashIconPNG) {
		if os.MkdirAll(filepath.Dir(icon), 0700) != nil || os.WriteFile(icon, splashIconPNG, 0600) != nil {
			return
		}
	}
	_ = hiddenCommand("reg.exe", "add", notifyAppKey, "/v", "DisplayName", "/t", "REG_SZ", "/d", productName, "/f").Run()
	_ = hiddenCommand("reg.exe", "add", notifyAppKey, "/v", "IconUri", "/t", "REG_SZ", "/d", icon, "/f").Run()
}

func registerNotifyTask(executable string) error {
	definition := `<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <TimeTrigger>
      <Repetition><Interval>PT1H</Interval><StopAtDurationEnd>false</StopAtDurationEnd></Repetition>
      <StartBoundary>` + time.Now().Add(time.Minute).Format("2006-01-02T15:04:05") + `</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals><Principal id="Author"><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author"><Exec><Command>` + xmlText(executable) + `</Command><Arguments>--notify-check</Arguments></Exec></Actions>
</Task>`
	file, err := os.CreateTemp("", "brasfoot-mega-patch-task-*.xml")
	if err != nil {
		return err
	}
	path := file.Name()
	defer os.Remove(path)
	encoded := utf16.Encode([]rune(definition))
	body := make([]byte, 2, 2+len(encoded)*2)
	body[0], body[1] = 0xFF, 0xFE
	for _, unit := range encoded {
		body = append(body, byte(unit), byte(unit>>8))
	}
	_, err = file.Write(body)
	if closeErr := file.Close(); err == nil {
		err = closeErr
	}
	if err != nil {
		return err
	}
	return hiddenCommand("schtasks.exe", "/Create", "/F", "/TN", notifyTaskName, "/XML", path).Run()
}

func setNotifications(enabled bool) error {
	executable := notificationExecutable()
	if !enabled || executable == "" {
		_ = hiddenCommand("reg.exe", "delete", notifyRunKey, "/v", notifyRunValue, "/f").Run()
		_ = hiddenCommand("schtasks.exe", "/Delete", "/F", "/TN", notifyTaskName).Run()
		_ = hiddenCommand("reg.exe", "delete", notifyAppKey, "/f").Run()
		return nil
	}
	command := `"` + executable + `" --notify-check`
	if err := hiddenCommand("reg.exe", "add", notifyRunKey, "/v", notifyRunValue, "/t", "REG_SZ", "/d", command, "/f").Run(); err != nil {
		return err
	}
	if registerNotifyTask(executable) != nil {
		_ = hiddenCommand("schtasks.exe", "/Create", "/F", "/SC", "HOURLY", "/MO", "1", "/TN", notifyTaskName, "/TR", command).Run()
	}
	registerProtocol(executable)
	registerNotifyApp()
	return nil
}

func xmlText(value string) string {
	return strings.NewReplacer("&", "&amp;", "<", "&lt;", ">", "&gt;", `"`, "&quot;", "'", "&apos;").Replace(value)
}

func showToast(title, body string) error {
	registerNotifyApp()
	payload := `<toast activationType="protocol" launch="brasfootmegapatch:abrir"><visual><binding template="ToastGeneric"><text>` +
		xmlText(title) + `</text><text>` + xmlText(body) + `</text></binding></visual></toast>`
	script := "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;" +
		"[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] > $null;" +
		"$d = New-Object Windows.Data.Xml.Dom.XmlDocument; $d.LoadXml(" + psQuote(payload) + ");" +
		"$t = [Windows.UI.Notifications.ToastNotification]::new($d);" +
		"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier(" + psQuote(notifyAppID) + ").Show($t)"
	return hiddenCommand("powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script).Run()
}

func runNotifyCheck() {
	settings := loadSettings()
	if !settings.Notify {
		return
	}
	feed, err := fetchFeed()
	if err != nil {
		return
	}
	messages := []string{}
	if feed.PatchVersion != "" && feed.PatchVersion != settings.LastSeenPatch && feed.PatchVersion != settings.LastNotifiedPatch {
		messages = append(messages, "Nova versão do patch: "+feed.PatchVersion+".")
		settings.LastNotifiedPatch = feed.PatchVersion
	}
	if hubUpdateAvailable(feed) && feed.Hub.Version != settings.LastSeenHub && feed.Hub.Version != settings.LastNotifiedHub {
		messages = append(messages, "Novo instalador: "+feed.Hub.Version+".")
		settings.LastNotifiedHub = feed.Hub.Version
	}
	if len(messages) == 0 {
		return
	}
	if showToast("Brasfoot Mega Patch", strings.Join(messages, " ")+" Abra o hub para ver as novidades e atualizar.") == nil {
		_ = saveSettings(settings)
	}
}
