//go:build windows && hubcli

package main

import (
	"errors"
	"os/exec"
	"strings"
)

const portablePlatformNotice = "Modo de linha de comando para desenvolvimento; não faz parte da distribuição."

func folderPicker() (string, error) {
	return "", errors.New("informe a pasta do jogo com --game")
}

func graphicalConfirmation(string) (bool, bool) {
	return false, false
}

func detectedPortableGame() string {
	return ""
}

func checkPortableGameClosed() error {
	out, err := exec.Command("tasklist", "/FO", "CSV", "/NH").Output()
	if err != nil {
		return errors.New("não foi possível identificar processos; confira se o comando tasklist está disponível")
	}
	for _, line := range strings.Split(string(out), "\n") {
		image := strings.Trim(strings.SplitN(strings.TrimSpace(line), ",", 2)[0], `"`)
		for _, name := range []string{"bf22-23.exe", "brasfoot.exe", "brasfoot22-23.exe"} {
			if strings.EqualFold(image, name) {
				return errors.New("o Brasfoot está aberto; salve sua carreira, feche o jogo e tente novamente")
			}
		}
	}
	return nil
}
