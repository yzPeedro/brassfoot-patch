package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
)

type HubSettings struct {
	Theme             string `json:"theme"`
	Notify            bool   `json:"notify"`
	OriginalFolder    string `json:"originalFolder,omitempty"`
	LastSeenPatch     string `json:"lastSeenPatch,omitempty"`
	LastSeenHub       string `json:"lastSeenHub,omitempty"`
	LastNotifiedPatch string `json:"lastNotifiedPatch,omitempty"`
	LastNotifiedHub   string `json:"lastNotifiedHub,omitempty"`
}

var settingsMutex sync.Mutex

func settingsPath() (string, error) {
	root, err := backupRoot()
	if err != nil {
		return "", err
	}
	return filepath.Join(filepath.Dir(root), "hub-settings.json"), nil
}

func loadSettings() HubSettings {
	settingsMutex.Lock()
	defer settingsMutex.Unlock()
	settings := HubSettings{Theme: "system"}
	path, err := settingsPath()
	if err != nil {
		return settings
	}
	body, err := os.ReadFile(path)
	if err == nil {
		_ = json.Unmarshal(body, &settings)
	}
	if settings.Theme != "light" && settings.Theme != "dark" {
		settings.Theme = "system"
	}
	return settings
}

func saveSettings(settings HubSettings) error {
	settingsMutex.Lock()
	defer settingsMutex.Unlock()
	path, err := settingsPath()
	if err != nil {
		return err
	}
	if err = os.MkdirAll(filepath.Dir(path), 0700); err != nil {
		return err
	}
	body, err := json.MarshalIndent(settings, "", "  ")
	if err != nil {
		return err
	}
	temporary := path + ".tmp"
	if err = os.WriteFile(temporary, body, 0600); err != nil {
		return err
	}
	_ = os.Remove(path)
	return os.Rename(temporary, path)
}

func rememberSeenVersions(feed ReleaseFeed) {
	if feed.PatchVersion == "" {
		return
	}
	settings := loadSettings()
	settings.LastSeenPatch = feed.PatchVersion
	settings.LastSeenHub = feed.Hub.Version
	_ = saveSettings(settings)
}
