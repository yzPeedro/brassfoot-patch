package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestReleaseDeltaInstallsRestores20Teams(t *testing.T) {
	root := t.TempDir()
	game := filepath.Join(root, "game")
	if err := os.MkdirAll(filepath.Join(game, "teams"), 0700); err != nil {
		t.Fatal(err)
	}
	origRoot := os.Getenv("BRASSFOOT_TEST_ORIGINALS")
	if origRoot == "" {
		t.Skip("teste de integração requer originais privados fornecidos localmente")
	}
	originalDigests := map[string]string{}
	entries, err := os.ReadDir(origRoot)
	if err != nil {
		t.Fatal(err)
	}
	for _, e := range entries {
		data, err := os.ReadFile(filepath.Join(origRoot, e.Name()))
		if err != nil {
			t.Fatal(err)
		}
		dest := filepath.Join(game, "teams", e.Name())
		if err = os.WriteFile(dest, data, 0600); err != nil {
			t.Fatal(err)
		}
		originalDigests[e.Name()] = digestBytes(data)
	}
	origOptions := []byte("private options must never change")
	os.WriteFile(filepath.Join(game, "options.bcf"), origOptions, 0600)
	os.WriteFile(filepath.Join(game, "saved.s22"), []byte("saved career"), 0600)
	os.WriteFile(filepath.Join(game, "saved.sbck"), []byte("backup save"), 0600)
	payload, err := stageBundledPayload()
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(filepath.Dir(payload))
	if err = prepareBundledPayload(game, payload); err != nil {
		t.Fatalf("prepare delta: %v", err)
	}
	plan, err := inspect(payload, game)
	if err != nil {
		t.Fatalf("inspect delta: %v", err)
	}
	if len(plan.Items) != 20 || plan.AlreadyInstalled {
		t.Fatalf("invalid plan: %#v", plan)
	}
	t.Setenv("LOCALAPPDATA", filepath.Join(root, "appdata"))
	result, err := install(plan, InstallOptions{})
	if err != nil {
		t.Fatal(err)
	}
	for _, item := range plan.Items {
		got, err := sha(item.Target)
		if err != nil || got != item.File.SHA256 {
			t.Fatalf("patch hash %s: %v", item.File.Path, err)
		}
	}
	if err = prepareBundledPayload(game, payload); err != nil {
		t.Fatalf("idempotent prepare: %v", err)
	}
	patchedPlan, err := inspect(payload, game)
	if err != nil || !patchedPlan.AlreadyInstalled {
		t.Fatalf("inspect idempotent: %v", err)
	}
	if _, _, err = findRestorableBackup(patchedPlan); err != nil {
		t.Fatalf("find backup: %v", err)
	}
	if _, err = restorePatch(patchedPlan, nil); err != nil {
		t.Fatalf("restore: %v", err)
	}
	for name, want := range originalDigests {
		got, err := sha(filepath.Join(game, "teams", name))
		if err != nil || got != want {
			t.Fatalf("restored mismatch %s", name)
		}
	}
	for name, want := range map[string]string{"options.bcf": "private options must never change", "saved.s22": "saved career", "saved.sbck": "backup save"} {
		got, err := os.ReadFile(filepath.Join(game, name))
		if err != nil || string(got) != want {
			t.Fatalf("private file changed %s", name)
		}
	}
	if result.Files != 20 {
		t.Fatal("wrong file count")
	}
}

func TestDeltaTamperingRejected(t *testing.T) {
	wanted := ManifestFile{Path: "teams/foo.ban", Size: 4, SHA256: strings.Repeat("a", 64)}
	if _, err := applyRecipe([]byte("abc"), []byte(`{"schemaVersion":1}`), wanted); err == nil {
		t.Fatal("invalid recipe accepted")
	}
}
