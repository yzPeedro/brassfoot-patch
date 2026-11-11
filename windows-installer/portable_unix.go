//go:build !windows

package main

import (
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

const portablePlatformNotice = "O jogo Windows requer uma camada de compatibilidade já configurada."

func folderPicker() (string, error) {
	if runtime.GOOS == "darwin" {
		out, err := exec.Command("osascript", "-e", `POSIX path of (choose folder with prompt "Selecione a pasta do Brasfoot dentro da sua instalação Wine/CrossOver")`).Output()
		return strings.TrimSpace(string(out)), err
	}
	if path, err := exec.LookPath("zenity"); err == nil {
		out, err := exec.Command(path, "--file-selection", "--directory", "--title="+productName+" — Pasta do jogo").Output()
		return strings.TrimSpace(string(out)), err
	}
	if path, err := exec.LookPath("kdialog"); err == nil {
		out, err := exec.Command(path, "--getexistingdirectory", ".", "--title", productName).Output()
		return strings.TrimSpace(string(out)), err
	}
	return "", errors.New("seletor de pastas indisponível; use --game /caminho/da/pasta/do/Brasfoot")
}

func graphicalConfirmation(message string) (bool, bool) {
	if runtime.GOOS == "darwin" {
		// Message is passed as argv, never interpolated into AppleScript.
		return exec.Command("osascript", "-e", `on run argv
display dialog (item 1 of argv) with title "Brasfoot Mega Patch" buttons {"Cancelar", "Continuar"} default button "Cancelar" cancel button "Cancelar"
end run`, "--", message).Run() == nil, true
	}
	if path, err := exec.LookPath("zenity"); err == nil {
		return exec.Command(path, "--question", "--title="+productName, "--text="+message, "--default-cancel").Run() == nil, true
	}
	if path, err := exec.LookPath("kdialog"); err == nil {
		return exec.Command(path, "--title", productName, "--yesno", message).Run() == nil, true
	}
	return false, false
}

func detectedPortableGame() string {
	home, _ := os.UserHomeDir()
	prefixes := []string{os.Getenv("WINEPREFIX"), filepath.Join(home, ".wine")}
	for _, pattern := range []string{
		filepath.Join(home, "Library", "Application Support", "CrossOver", "Bottles", "*"),
		filepath.Join(home, ".local", "share", "bottles", "bottles", "*"),
		filepath.Join(home, ".var", "app", "com.usebottles.bottles", "data", "bottles", "bottles", "*"),
	} {
		matches, _ := filepath.Glob(pattern)
		prefixes = append(prefixes, matches...)
	}
	for _, prefix := range prefixes {
		if prefix == "" {
			continue
		}
		for _, name := range []string{"Brasfoot22-23", "Brasfoot 2022-2023", "Program Files/Brasfoot22-23", "Program Files (x86)/Brasfoot22-23"} {
			candidate := filepath.Join(prefix, "drive_c", filepath.FromSlash(name))
			if _, _, err := validGame(candidate); err == nil {
				return candidate
			}
		}
	}
	return ""
}

func checkPortableGameClosed() error {
	out, err := exec.Command("ps", "-axo", "command=").Output()
	if err != nil {
		return errors.New("não foi possível identificar processos; confira se o comando ps está disponível")
	}
	for _, line := range strings.Split(string(out), "\n") {
		lower := strings.ToLower(line)
		if strings.Contains(lower, "bf22-23.exe") || (strings.Contains(lower, "java") && strings.Contains(lower, "brasfoot") && strings.Contains(lower, ".jar")) {
			return errors.New("o Brasfoot está aberto; salve sua carreira, feche o jogo e tente novamente")
		}
	}
	return nil
}
