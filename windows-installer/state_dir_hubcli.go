//go:build hubcli

package main

import (
	"errors"
	"flag"
	"os"
	"path/filepath"
	"strings"
)

func init() {
	stateDirRequired = true
	flag.Func("state-dir", "pasta descartável para cofre de originais, backups, cache do feed, relatórios, registros e temporários (obrigatória)", useStateDir)
}

func useStateDir(value string) error {
	if strings.TrimSpace(value) == "" {
		return errors.New("pasta vazia")
	}
	dir, err := filepath.Abs(value)
	if err != nil {
		return err
	}
	if real, err := defaultStateDir(); err == nil && (pathWithin(dir, real) || pathWithin(real, dir)) {
		return errors.New("a pasta coincide com o estado real do hub (" + real + "); use uma pasta descartável")
	}
	temporary := filepath.Join(dir, "tmp")
	if err := os.MkdirAll(temporary, 0o700); err != nil {
		return err
	}
	for _, name := range []string{"TMP", "TEMP", "TMPDIR"} {
		if err := os.Setenv(name, temporary); err != nil {
			return err
		}
	}
	stateDir = dir
	return nil
}

func pathWithin(path, root string) bool {
	relative, err := filepath.Rel(root, path)
	return err == nil && relative != ".." && !strings.HasPrefix(relative, ".."+string(filepath.Separator))
}
