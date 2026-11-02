package main

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestLivePitchMatchesSite(t *testing.T) {
	site, err := os.ReadFile(filepath.Join("..", "site", "live-pitch.js"))
	if err != nil {
		t.Fatal(err)
	}
	hub, err := os.ReadFile(filepath.Join("ui", "live-pitch.js"))
	if err != nil {
		t.Fatal(err)
	}
	normalize := func(data []byte) []byte { return bytes.ReplaceAll(data, []byte("\r\n"), []byte("\n")) }
	if !bytes.Equal(normalize(site), normalize(hub)) {
		t.Fatal("windows-installer/ui/live-pitch.js difere de site/live-pitch.js")
	}
	if bytes.Contains(hub, []byte("</script")) || bytes.Contains(hub, []byte("{{")) {
		t.Fatal("live-pitch.js não pode conter </script nem {{")
	}
}
