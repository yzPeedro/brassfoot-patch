package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func makeFixture(t *testing.T) (string, string, string, string) {
	t.Helper()
	root := t.TempDir()
	game := filepath.Join(root, "game")
	payload := filepath.Join(root, "payload")
	for _, d := range []string{filepath.Join(game, "teams"), filepath.Join(payload, "teams")} {
		if err := os.MkdirAll(d, 0700); err != nil {
			t.Fatal(err)
		}
	}
	os.WriteFile(filepath.Join(game, "options.bcf"), []byte("options"), 0600)
	for i := 0; i < 10; i++ {
		os.WriteFile(filepath.Join(game, "teams", string(rune('a'+i))+".ban"), []byte{0xac, 0xed, 0x00, 0x05, byte('a' + i)}, 0600)
	}
	original := filepath.Join(game, "teams", "a.ban")
	target := filepath.Join(payload, "teams", "a.ban")
	os.WriteFile(target, []byte{0xac, 0xed, 0x00, 0x05, 80, 65, 84, 67, 72}, 0600)
	originalSHA, _ := sha(original)
	patchSHA, _ := sha(target)
	m := Manifest{SchemaVersion: 2, Kind: "BRASFOOT_HOMOLOGATION_PATCH", PatchSeason: 2026, Version: "2026.1.0", Files: []ManifestFile{{Path: "teams/a.ban", Size: 9, SHA256: patchSHA, AcceptedOriginalSHA256: []string{originalSHA}}}}
	b, _ := json.Marshal(m)
	os.WriteFile(filepath.Join(payload, "manifest.json"), b, 0600)
	return game, payload, originalSHA, patchSHA
}
func TestInspectInstallIdempotentAndBackup(t *testing.T) {
	game, payload, originalHash, patchHash := makeFixture(t)
	p, err := inspect(payload, game)
	if err != nil {
		t.Fatal(err)
	}
	if p.AlreadyInstalled {
		t.Fatal("initially already installed")
	}
	t.Setenv("LOCALAPPDATA", filepath.Join(t.TempDir(), "app"))
	r, err := install(p, InstallOptions{})
	if err != nil {
		t.Fatal(err)
	}
	if r.Status != "installed" {
		t.Fatal(r)
	}
	installed, _ := sha(filepath.Join(game, "teams", "a.ban"))
	if installed != patchHash {
		t.Fatal("not patched")
	}
	copied, _ := sha(filepath.Join(r.BackupPath, "teams", "a.ban"))
	if copied != originalHash {
		t.Fatal("backup corrupted")
	}
	p, err = inspect(payload, game)
	if err != nil || !p.AlreadyInstalled {
		t.Fatalf("idempotency: %+v / %v", p, err)
	}
}
func TestRollbackInjectedFailure(t *testing.T) {
	game, payload, original, _ := makeFixture(t)
	p, err := inspect(payload, game)
	if err != nil {
		t.Fatal(err)
	}
	t.Setenv("LOCALAPPDATA", filepath.Join(t.TempDir(), "app"))
	_, err = install(p, InstallOptions{TestFailAfter: 1})
	if err == nil {
		t.Fatal("failure not injected")
	}
	got, _ := sha(filepath.Join(game, "teams", "a.ban"))
	if got != original {
		t.Fatalf("rollback failed: %s", got)
	}
}
func TestCorruptSourceCannotInstall(t *testing.T) {
	game, payload, _, _ := makeFixture(t)
	os.WriteFile(filepath.Join(payload, "teams", "a.ban"), []byte("bad"), 0600)
	if _, err := inspect(payload, game); err == nil {
		t.Fatal("expected corruption detection")
	}
}
func TestRefuseTraversalOrUnknownOriginal(t *testing.T) {
	game, payload, _, _ := makeFixture(t)
	manifest := filepath.Join(payload, "manifest.json")
	b, _ := os.ReadFile(manifest)
	var m Manifest
	json.Unmarshal(b, &m)
	m.Files[0].Path = "../save.s22"
	b, _ = json.Marshal(m)
	os.WriteFile(manifest, b, 0600)
	if _, err := inspect(payload, game); err == nil {
		t.Fatal("expected traversal refusal")
	}
	m.Files[0].Path = "teams/a.ban"
	m.Files[0].AcceptedOriginalSHA256 = []string{strings.Repeat("f", 64)}
	b, _ = json.Marshal(m)
	os.WriteFile(manifest, b, 0600)
	if _, err := inspect(payload, game); err == nil {
		t.Fatal("expected unknown-version refusal")
	}
}
func TestRefuseUncertifiedPublishedFlags(t *testing.T) {
	game, payload, _, _ := makeFixture(t)
	manifest := filepath.Join(payload, "manifest.json")
	b, _ := os.ReadFile(manifest)
	var m Manifest
	json.Unmarshal(b, &m)
	m.PublicationAllowed = true
	b, _ = json.Marshal(m)
	os.WriteFile(manifest, b, 0600)
	if _, err := inspect(payload, game); err == nil {
		t.Fatal("expected incoherent flags refusal")
	}
}
func TestInventoryIsReadOnly(t *testing.T) {
	game, _, original, _ := makeFixture(t)
	t.Setenv("LOCALAPPDATA", filepath.Join(t.TempDir(), "app"))
	path, err := exportInventory(game)
	if err != nil {
		t.Fatal(err)
	}
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var r Inventory
	if err = json.Unmarshal(b, &r); err != nil {
		t.Fatal(err)
	}
	if r.TeamCount != 10 || len(r.Teams) != 10 {
		t.Fatalf("invalid report: %+v", r)
	}
	got, _ := sha(filepath.Join(game, "teams", "a.ban"))
	if got != original {
		t.Fatal("game mutated")
	}
}
