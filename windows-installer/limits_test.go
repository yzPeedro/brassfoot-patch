package main

import (
	"fmt"
	"testing"
)

func synthetic(n int, size int64) []ManifestFile {
	files := make([]ManifestFile, n)
	for i := range files {
		files[i] = ManifestFile{Path: fmt.Sprintf("teams/clube%05d.ban", i), Size: size}
	}
	return files
}

func TestManifestLimits(t *testing.T) {
	if err := validateManifestLimits(synthetic(3000, 40000)); err != nil {
		t.Fatalf("3000 arquivos deveriam passar: %v", err)
	}
	if err := validateManifestLimits(synthetic(maxBundleFiles, 40000)); err != nil {
		t.Fatalf("o limite exato deveria passar: %v", err)
	}
	if validateManifestLimits(synthetic(maxBundleFiles+1, 40000)) == nil {
		t.Fatal("acima do limite de arquivos deveria falhar")
	}
	if validateManifestLimits(nil) == nil {
		t.Fatal("pacote vazio deveria falhar")
	}
	if validateManifestLimits(synthetic(100, maxBundleFileBytes+1)) == nil {
		t.Fatal("arquivo grande demais deveria falhar")
	}
	if validateManifestLimits(synthetic(100, 3)) == nil {
		t.Fatal("arquivo pequeno demais deveria falhar")
	}
	if validateManifestLimits(synthetic(100, maxBundleFileBytes)) == nil {
		t.Fatal("soma acima do total permitido deveria falhar")
	}
}
