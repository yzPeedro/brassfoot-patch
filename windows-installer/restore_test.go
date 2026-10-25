package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestRestoreOnOriginalGameLeavesSaveUnchanged(t *testing.T) {
	game, payload, originalSHA, patchSHA := makeFixture(t)
	t.Setenv("LOCALAPPDATA", filepath.Join(t.TempDir(), "local"))
	save := filepath.Join(game, "my-career.s22")
	if err := os.WriteFile(save, []byte("my important career unchanged"), 0600); err != nil {
		t.Fatal(err)
	}
	originalSave, _ := sha(save)
	plan, err := inspect(payload, game)
	if err != nil {
		t.Fatal(err)
	}
	first, err := install(plan, InstallOptions{})
	if err != nil {
		t.Fatal(err)
	}
	patched, _ := sha(filepath.Join(game, "teams", "a.ban"))
	if patched != patchSHA {
		t.Fatal("didn't patch")
	}
	reread, err := inspect(payload, game)
	if err != nil || !reread.AlreadyInstalled {
		t.Fatal(err)
	}
	backed, _, err := findRestorableBackup(reread)
	if err != nil || backed != first.BackupPath {
		t.Fatalf("backup lookup failed: %s %v", backed, err)
	}
	restored, err := restorePatch(reread, nil)
	if err != nil || restored != backed {
		t.Fatalf("restoration failed: %s / %v", restored, err)
	}
	actual, _ := sha(filepath.Join(game, "teams", "a.ban"))
	saveHash, _ := sha(save)
	if actual != originalSHA || saveHash != originalSave {
		t.Fatal("original team or save changed")
	}
	if _, err := os.Stat(filepath.Join(restored, "restore-report.json")); err != nil {
		t.Fatal(err)
	}
}
func TestRestoreRefusesCorruptBackupAndModifiedGame(t *testing.T) {
	game, payload, _, _ := makeFixture(t)
	t.Setenv("LOCALAPPDATA", filepath.Join(t.TempDir(), "local"))
	plan, err := inspect(payload, game)
	if err != nil {
		t.Fatal(err)
	}
	result, err := install(plan, InstallOptions{})
	if err != nil {
		t.Fatal(err)
	}
	installed, err := inspect(payload, game)
	if err != nil {
		t.Fatal(err)
	}
	original := filepath.Join(result.BackupPath, "teams", "a.ban")
	if err := os.WriteFile(original, []byte("tampered backup"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err := restorePatch(installed, nil); err == nil || !strings.Contains(err.Error(), "backup íntegro") {
		t.Fatalf("bad backup accepted: %v", err)
	}
	// Still keep the patch intact on failure.
	got, _ := sha(filepath.Join(game, "teams", "a.ban"))
	if got != installed.Items[0].File.SHA256 {
		t.Fatal("modified game during rejected restore")
	}
}
