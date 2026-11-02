//go:build windows

package main

import (
	"os"
	"strings"
)

const (
	notifyRunKey      = `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
	notifyRunValue    = "BrasfootMegaPatchNovidades"
	notifyTaskName    = `Brasfoot Mega Patch\Novidades`
	protocolKey       = `HKCU\Software\Classes\brasfootmegapatch`
	powershellToastID = `{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe`
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

func setNotifications(enabled bool) error {
	executable := notificationExecutable()
	if !enabled || executable == "" {
		_ = hiddenCommand("reg.exe", "delete", notifyRunKey, "/v", notifyRunValue, "/f").Run()
		_ = hiddenCommand("schtasks.exe", "/Delete", "/F", "/TN", notifyTaskName).Run()
		return nil
	}
	command := `"` + executable + `" --notify-check`
	if err := hiddenCommand("reg.exe", "add", notifyRunKey, "/v", notifyRunValue, "/t", "REG_SZ", "/d", command, "/f").Run(); err != nil {
		return err
	}
	_ = hiddenCommand("schtasks.exe", "/Create", "/F", "/SC", "DAILY", "/ST", "19:00", "/TN", notifyTaskName, "/TR", command).Run()
	registerProtocol(executable)
	return nil
}

func xmlText(value string) string {
	return strings.NewReplacer("&", "&amp;", "<", "&lt;", ">", "&gt;", `"`, "&quot;", "'", "&apos;").Replace(value)
}

func showToast(title, body string) error {
	payload := `<toast activationType="protocol" launch="brasfootmegapatch:abrir"><visual><binding template="ToastGeneric"><text>` +
		xmlText(title) + `</text><text>` + xmlText(body) + `</text></binding></visual></toast>`
	script := "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;" +
		"[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] > $null;" +
		"$d = New-Object Windows.Data.Xml.Dom.XmlDocument; $d.LoadXml(" + psQuote(payload) + ");" +
		"$t = [Windows.UI.Notifications.ToastNotification]::new($d);" +
		"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier(" + psQuote(powershellToastID) + ").Show($t)"
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
