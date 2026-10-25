package main

import (
	"bytes"
	"crypto/sha256"
	"embed"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
)

// Only delta operations are shipped. The installer needs the user's own
// licensed Brasfoot installation and never distributes original .ban files.
//
//go:embed bundled_release/manifest.json bundled_release/patches/*.json
var deltaPayload embed.FS

type patchOp struct {
	Copy []int  `json:"copy,omitempty"`
	Add  string `json:"add,omitempty"`
}
type patchRecipe struct {
	SchemaVersion  int       `json:"schemaVersion"`
	Path           string    `json:"path"`
	OriginalSHA256 string    `json:"originalSha256"`
	TargetSHA256   string    `json:"targetSha256"`
	OriginalSize   int       `json:"originalSize"`
	TargetSize     int       `json:"targetSize"`
	Operations     []patchOp `json:"operations"`
}

func digestBytes(b []byte) string {
	h := sha256.Sum256(b)
	return hex.EncodeToString(h[:])
}

func applyRecipe(original []byte, raw []byte, wanted ManifestFile) ([]byte, error) {
	var recipe patchRecipe
	if err := json.Unmarshal(raw, &recipe); err != nil {
		return nil, fmt.Errorf("instruções inválidas: %w", err)
	}
	if recipe.SchemaVersion != 1 || recipe.Path != wanted.Path ||
		recipe.TargetSHA256 != wanted.SHA256 || recipe.TargetSize != int(wanted.Size) ||
		recipe.OriginalSize != len(original) || digestBytes(original) != recipe.OriginalSHA256 ||
		len(recipe.Operations) == 0 || len(recipe.Operations) > 10000 {
		return nil, fmt.Errorf("instruções incompatíveis para %s", wanted.Path)
	}
	var output bytes.Buffer
	output.Grow(recipe.TargetSize)
	for _, op := range recipe.Operations {
		if len(op.Copy) == 2 && op.Add == "" {
			start, size := op.Copy[0], op.Copy[1]
			if start < 0 || size <= 0 || start > len(original) || size > len(original)-start {
				return nil, fmt.Errorf("intervalo inválido em %s", wanted.Path)
			}
			output.Write(original[start : start+size])
		} else if len(op.Copy) == 0 && op.Add != "" {
			b, err := base64.StdEncoding.DecodeString(op.Add)
			if err != nil {
				return nil, fmt.Errorf("dado inválido em %s: %w", wanted.Path, err)
			}
			output.Write(b)
		} else {
			return nil, fmt.Errorf("operação inválida em %s", wanted.Path)
		}
		if output.Len() > recipe.TargetSize {
			return nil, fmt.Errorf("tamanho excedido em %s", wanted.Path)
		}
	}
	if output.Len() != recipe.TargetSize || digestBytes(output.Bytes()) != recipe.TargetSHA256 {
		return nil, fmt.Errorf("o resultado não confere com SHA-256 de %s", wanted.Path)
	}
	return output.Bytes(), nil
}

func stageBundledPayload() (string, error) {
	base, err := os.MkdirTemp("", "brassfoot-2026-release-")
	if err != nil {
		return "", err
	}
	target := filepath.Join(base, "payload")
	if err = os.MkdirAll(target, 0700); err != nil {
		os.RemoveAll(base)
		return "", err
	}
	body, err := deltaPayload.ReadFile("bundled_release/manifest.json")
	if err != nil {
		os.RemoveAll(base)
		return "", err
	}
	if err = os.WriteFile(filepath.Join(target, "manifest.json"), body, 0600); err != nil {
		os.RemoveAll(base)
		return "", err
	}
	return target, nil
}

// Produces temporary patched files only AFTER comparing against the local
// originals. No game files are modified here; inspect() then validates them.
func prepareBundledPayload(gamePath, staged string) error {
	return preparePayloadWithFS(deltaPayload, gamePath, staged)
}

// preparePayloadWithFS accepts a variable-size validated manifest and allows tests
// to inject a synthetic release without changing production embedded assets.
func preparePayloadWithFS(fsys fs.FS, gamePath, staged string) error {
	game, _, err := validGame(gamePath)
	if err != nil {
		return err
	}
	body, err := fs.ReadFile(fsys, "bundled_release/manifest.json")
	if err != nil {
		return err
	}
	var manifest Manifest
	if err = json.Unmarshal(body, &manifest); err != nil {
		return err
	}
	if (manifest.SchemaVersion != 2 && manifest.SchemaVersion != 3) || manifest.PatchSeason != 2026 || !validVersion.MatchString(manifest.Version) {
		return fmt.Errorf("manifesto do pacote inválido")
	}
	if len(manifest.Files) < 1 || len(manifest.Files) > 512 {
		return fmt.Errorf("pacote incompatível: esperado de 1 a 512 arquivos .ban, encontrados %d", len(manifest.Files))
	}
	seen := make(map[string]bool, len(manifest.Files))
	for _, f := range manifest.Files {
		if !teamName.MatchString(f.Path) {
			return fmt.Errorf("arquivo não autorizado no pacote: %s", f.Path)
		}
		key := strings.ToLower(f.Path)
		if seen[key] {
			return fmt.Errorf("arquivo de equipe duplicado no pacote: %s", f.Path)
		}
		seen[key] = true
		if f.Operation != "" && (manifest.SchemaVersion != 3 || (f.Operation != "replace" && f.Operation != "add")) {
			return fmt.Errorf("operação do pacote incompatível: %s", f.Path)
		}
	}
	for _, f := range manifest.Files {
		src := filepath.Join(game, filepath.FromSlash(f.Path))
		mode := f.Operation
		if mode == "" { mode = "replace" }
		var original []byte
		if mode == "replace" {
			if err = checkRegular(src); err != nil {
				return fmt.Errorf("arquivo do Brasfoot ausente: %s: %w", f.Path, err)
			}
			original, err = os.ReadFile(src)
			if err != nil { return err }
		} else {
			if e := checkRegular(src); e == nil {
				original, err = os.ReadFile(src)
				if err != nil { return err }
				if digestBytes(original) != f.SHA256 || int64(len(original)) != f.Size {
					return fmt.Errorf("nova equipe não pode sobrescrever arquivo existente: %s", f.Path)
				}
			} else if !os.IsNotExist(e) {
				return fmt.Errorf("arquivo de destino incompatível: %s: %w",f.Path,e)
			}
		}
		current := digestBytes(original)
		var output []byte
		if current == f.SHA256 && int64(len(original)) == f.Size {
			output = original
		} else {
			if mode == "replace" {
				allowed := false
				for _, h := range f.AcceptedOriginalSHA256 { if current == h { allowed = true; break } }
				if !allowed { return &UnknownOriginalError{Relative:f.Path,Actual:current,Accepted:f.AcceptedOriginalSHA256} }
			} else if len(f.AcceptedOriginalSHA256) != 0 {
				return fmt.Errorf("adição com hashes de originais indevidos: %s", f.Path)
			}
			name := filepath.Base(f.Path)
			if strings.ContainsAny(name, "/\\") { return fmt.Errorf("nome de equipe inválido") }
			data,e := fs.ReadFile(fsys,"bundled_release/patches/"+name+".json")
			if e != nil { return fmt.Errorf("instruções de %s ausentes: %w",f.Path,e) }
			output,e = applyRecipe(original,data,f)
			if e != nil { return e }
		}
		target := filepath.Join(staged, filepath.FromSlash(f.Path))
		if err = os.MkdirAll(filepath.Dir(target), 0700); err != nil {
			return err
		}
		if err = os.WriteFile(target, output, 0600); err != nil {
			return err
		}
		if h, e := sha(target); e != nil || h != f.SHA256 {
			return fmt.Errorf("falha na verificação de %s", f.Path)
		}
	}
	return nil
}
