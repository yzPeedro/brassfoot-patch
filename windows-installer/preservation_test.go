package main

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// A user's ORIGINAL game folder is the real target. Never edit saves, settings,
// or auxiliary files, even if installation fails after replacement.
func TestOriginalFolderInstallPreservesSavesAndSettings(t *testing.T) {
	game, payload, _, patchSHA := makeFixture(t)
	originalGame := filepath.Join(filepath.Dir(game), "Brasfoot22-23")
	if err := os.Rename(game, originalGame); err != nil {
		t.Fatal(err)
	}
	saves := []string{"my-career.s22", "my-save.sbck", "config.cfg", filepath.Join("saves", "franchise.s22"), "options.bcf"}
	for _, relative := range saves {
		path := filepath.Join(originalGame, relative)
		if relative == "options.bcf" {
			continue
		}
		if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(path, []byte("preserve-original-content: "+relative), 0600); err != nil {
			t.Fatal(err)
		}
	}
	expected := map[string]string{}
	for _, relative := range saves {
		digest, err := sha(filepath.Join(originalGame, relative))
		if err != nil {
			t.Fatal(err)
		}
		expected[relative] = digest
	}
	t.Setenv("LOCALAPPDATA", filepath.Join(t.TempDir(), "local"))
	plan, err := inspect(payload, originalGame)
	if err != nil {
		t.Fatal(err)
	}
	progress := []string{}
	res, err := install(plan, InstallOptions{Progress: func(stage string, done, total int) { progress = append(progress, stage) }})
	if err != nil {
		t.Fatal(err)
	}
	if res.Status != "installed" || res.BackupPath == "" {
		t.Fatalf("result: %+v", res)
	}
	patched, _ := sha(filepath.Join(originalGame, "teams", "a.ban"))
	if patched != patchSHA {
		t.Fatal("patch not applied to original game")
	}
	for _, relative := range saves {
		actual, err := sha(filepath.Join(originalGame, relative))
		if err != nil || actual != expected[relative] {
			t.Fatalf("SAVE/SETTING CHANGED %s: %s / %v", relative, actual, err)
		}
	}
	if len(progress) != 3 || progress[0] != "backup" || progress[1] != "install" || progress[2] != "done" {
		t.Fatalf("progress not bound to finished work: %v", progress)
	}
}

func TestOriginalFolderRollbackPreservesSavesAndSettings(t *testing.T) {
	game, payload, originalSHA, _ := makeFixture(t)
	save := filepath.Join(game, "save.s22")
	if err := os.WriteFile(save, []byte("precious existing save"), 0600); err != nil {
		t.Fatal(err)
	}
	expected, _ := sha(save)
	t.Setenv("LOCALAPPDATA", filepath.Join(t.TempDir(), "local"))
	plan, err := inspect(payload, game)
	if err != nil {
		t.Fatal(err)
	}
	_, err = install(plan, InstallOptions{TestFailAfter: 1})
	if err == nil || !strings.Contains(err.Error(), "originais restaurados") {
		t.Fatalf("no rollback: %v", err)
	}
	after, _ := sha(save)
	orig, _ := sha(filepath.Join(game, "teams", "a.ban"))
	if after != expected || orig != originalSHA {
		t.Fatal("rollback changed saves or originals")
	}
}

func TestDescribeUnsupportedFileWithHashes(t *testing.T) {
	game, payload, _, _ := makeFixture(t)
	target := filepath.Join(game, "teams", "a.ban")
	if err := os.WriteFile(target, []byte{0xac, 0xed, 0, 5, 89}, 0600); err != nil {
		t.Fatal(err)
	}
	_, err := inspect(payload, game)
	var unknown *UnknownOriginalError
	if !errors.As(err, &unknown) {
		t.Fatalf("expected typed hash mismatch; got %v", err)
	}
	d := diagnose(err)
	if d.Code != "BF-104" || !strings.Contains(d.Reason, "teams/a.ban") || !strings.Contains(d.Detail, "SHA-256") || !strings.Contains(d.Action, "Não apague") {
		t.Fatalf("diagnostic unclear: %+v", d)
	}
}
func TestDiagnoseWrongGameFolder(t *testing.T) {
	game, _, _, _ := makeFixture(t)
	if err := os.Remove(filepath.Join(game, "options.bcf")); err != nil {
		t.Fatal(err)
	}
	_, _, err := validGame(game)
	d := diagnose(err)
	if d.Code != "BF-102" || !strings.Contains(d.Reason, "options.bcf") {
		t.Fatalf("unclear error: %+v", d)
	}
}
