package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing/fstest"
)

var (
	payloadMutex sync.Mutex
	deltaPayload fs.FS = fstest.MapFS{}
)

func setPayload(fsys fs.FS) {
	payloadMutex.Lock()
	deltaPayload = fsys
	payloadMutex.Unlock()
}

func currentPayload() fs.FS {
	payloadMutex.Lock()
	defer payloadMutex.Unlock()
	return deltaPayload
}

type patchOp struct {
	Copy []int  `json:"copy,omitempty"`
	Add  string `json:"add,omitempty"`
}
type patchRecipe struct {
	SchemaVersion  int           `json:"schemaVersion"`
	Path           string        `json:"path"`
	OriginalSHA256 string        `json:"originalSha256"`
	TargetSHA256   string        `json:"targetSha256"`
	OriginalSize   int           `json:"originalSize"`
	TargetSize     int           `json:"targetSize"`
	Operations     []patchOp     `json:"operations"`
	Variants       []patchRecipe `json:"variants,omitempty"`
	Steps          []patchRecipe `json:"steps,omitempty"`
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
	if recipe.SchemaVersion == 2 {
		matched := false
		for _, variant := range recipe.Variants {
			if variant.OriginalSHA256 == digestBytes(original) {
				recipe = variant
				matched = true
				break
			}
		}
		if !matched {
			return nil, fmt.Errorf("base não reconhecida para %s", wanted.Path)
		}
	}
	if recipe.SchemaVersion == 3 {
		current := original
		steps, ok := flattenSteps(recipe, 0)
		if !ok || len(steps) < 2 || len(steps) > 8 {
			return nil, fmt.Errorf("cadeia de instruções incompatível para %s", wanted.Path)
		}
		for _, step := range steps {
			var err error
			current, err = applyRecipeV1(current, step, wanted.Path)
			if err != nil {
				return nil, err
			}
		}
		if digestBytes(current) != wanted.SHA256 || int64(len(current)) != wanted.Size {
			return nil, fmt.Errorf("o resultado encadeado não confere com SHA-256 de %s", wanted.Path)
		}
		return current, nil
	}
	return applyRecipeV1(original, recipe, wanted.Path)
}

func flattenSteps(recipe patchRecipe, depth int) ([]patchRecipe, bool) {
	if recipe.SchemaVersion == 1 {
		return []patchRecipe{recipe}, true
	}
	if recipe.SchemaVersion != 3 || depth > 4 {
		return nil, false
	}
	steps := []patchRecipe{}
	for _, step := range recipe.Steps {
		inner, ok := flattenSteps(step, depth+1)
		if !ok {
			return nil, false
		}
		steps = append(steps, inner...)
	}
	return steps, true
}

func applyRecipeV1(original []byte, recipe patchRecipe, wantedPath string) ([]byte, error) {
	if recipe.SchemaVersion != 1 || recipe.Path != wantedPath ||
		recipe.OriginalSize != len(original) || digestBytes(original) != recipe.OriginalSHA256 ||
		len(recipe.Operations) == 0 || len(recipe.Operations) > 10000 {
		return nil, fmt.Errorf("instruções incompatíveis para %s", wantedPath)
	}
	var output bytes.Buffer
	output.Grow(recipe.TargetSize)
	for _, op := range recipe.Operations {
		if len(op.Copy) == 2 && op.Add == "" {
			start, size := op.Copy[0], op.Copy[1]
			if start < 0 || size <= 0 || start > len(original) || size > len(original)-start {
				return nil, fmt.Errorf("intervalo inválido em %s", wantedPath)
			}
			output.Write(original[start : start+size])
		} else if len(op.Copy) == 0 && op.Add != "" {
			b, err := base64.StdEncoding.DecodeString(op.Add)
			if err != nil {
				return nil, fmt.Errorf("dado inválido em %s: %w", wantedPath, err)
			}
			output.Write(b)
		} else {
			return nil, fmt.Errorf("operação inválida em %s", wantedPath)
		}
		if output.Len() > recipe.TargetSize {
			return nil, fmt.Errorf("tamanho excedido em %s", wantedPath)
		}
	}
	if output.Len() != recipe.TargetSize || digestBytes(output.Bytes()) != recipe.TargetSHA256 {
		return nil, fmt.Errorf("o resultado não confere com SHA-256 de %s", wantedPath)
	}
	return output.Bytes(), nil
}

func stageBundledPayload() (string, error) {
	base, err := os.MkdirTemp("", "brasfoot-mega-patch-release-")
	if err != nil {
		return "", err
	}
	target := filepath.Join(base, "payload")
	if err = os.MkdirAll(target, 0700); err != nil {
		os.RemoveAll(base)
		return "", err
	}
	body, err := fs.ReadFile(currentPayload(), "bundled_release/manifest.json")
	if err != nil {
		os.RemoveAll(base)
		return "", errors.New("nenhuma versão do patch foi carregada")
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
	return preparePayloadWithFS(currentPayload(), gamePath, staged)
}

// preparePayloadWithFS accepts a variable-size validated manifest and allows tests
// to inject a synthetic release without changing production embedded assets.
func preparePayloadWithFS(fsys fs.FS, gamePath, staged string) error {
	body, err := fs.ReadFile(fsys, "bundled_release/manifest.json")
	if err != nil {
		return err
	}
	var manifest Manifest
	if err = json.Unmarshal(body, &manifest); err != nil {
		return err
	}
	game, _, err := validGame(gamePath)
	if err != nil {
		return err
	}
	filtered := withoutForeignCrests(manifest, game)
	if body, err = json.MarshalIndent(filtered, "", "  "); err != nil {
		return err
	}
	if err = os.WriteFile(filepath.Join(staged, "manifest.json"), body, 0600); err != nil {
		return err
	}
	return preparePayloadManifest(fsys, filtered, gamePath, staged)
}

func readRecipe(fsys fs.FS, f ManifestFile) ([]byte, error) {
	name := filepath.Base(f.Path) + ".json"
	if f.Recipe != "" {
		if !recipeName.MatchString(f.Recipe) {
			return nil, fmt.Errorf("instruções com nome inválido: %s", f.Recipe)
		}
		name = f.Recipe
	}
	if strings.ContainsAny(name, "/\\") {
		return nil, fmt.Errorf("nome de equipe inválido")
	}
	data, err := fs.ReadFile(fsys, "bundled_release/patches/"+name)
	if err != nil {
		return nil, fmt.Errorf("instruções de %s ausentes: %w", f.Path, err)
	}
	return data, nil
}

func buildFromRecipe(fsys fs.FS, original []byte, f ManifestFile) ([]byte, error) {
	data, err := readRecipe(fsys, f)
	if err != nil {
		return nil, err
	}
	output, err := applyRecipe(original, data, f)
	if err == nil || f.Via == nil {
		return output, err
	}
	via := *f.Via
	via.Via = nil
	viaData, viaErr := readRecipe(fsys, via)
	if viaErr != nil {
		return nil, err
	}
	intermediate, viaErr := applyRecipe(original, viaData, via)
	if viaErr != nil || digestBytes(intermediate) != via.SHA256 {
		return nil, err
	}
	return applyRecipe(intermediate, data, f)
}

func preparePayloadManifest(fsys fs.FS, manifest Manifest, gamePath, staged string) error {
	game, _, err := validGame(gamePath)
	if err != nil {
		return err
	}
	if (manifest.SchemaVersion != 2 && manifest.SchemaVersion != 3 && manifest.SchemaVersion != 4) || manifest.PatchSeason != patchYear() || !validVersion.MatchString(manifest.Version) || !strings.HasPrefix(manifest.Version, patchYearText+".") {
		return fmt.Errorf("manifesto do pacote inválido")
	}
	if len(manifest.Files) < 1 || len(manifest.Files) > 2048 {
		return fmt.Errorf("pacote incompatível: esperado de 1 a 2048 arquivos autorizados, encontrados %d", len(manifest.Files))
	}
	seen := make(map[string]bool, len(manifest.Files))
	for _, f := range manifest.Files {
		isNationalConfig := manifest.SchemaVersion >= 3 && f.Path == nationalConfigPath
		isExecutable := manifest.SchemaVersion == 4 && f.Path == gameExecutablePath
		isCrest := manifest.SchemaVersion == 4 && crestName.MatchString(f.Path)
		if !teamName.MatchString(f.Path) && !isNationalConfig && !isExecutable && !isCrest {
			return fmt.Errorf("arquivo não autorizado no pacote: %s", f.Path)
		}
		if isCrest && f.LocalSource == "" && !recipeName.MatchString(f.Recipe) {
			return fmt.Errorf("escudo sem instruções nomeadas: %s", f.Path)
		}
		if (isNationalConfig || isExecutable || isCrest) && f.Operation != "replace" {
			return fmt.Errorf("este arquivo só pode substituir um original conhecido: %s", f.Path)
		}
		key := strings.ToLower(f.Path)
		if seen[key] {
			return fmt.Errorf("arquivo de equipe duplicado no pacote: %s", f.Path)
		}
		seen[key] = true
		if f.Operation != "" && (manifest.SchemaVersion < 3 || (f.Operation != "replace" && f.Operation != "add")) {
			return fmt.Errorf("operação do pacote incompatível: %s", f.Path)
		}
	}
	for _, f := range manifest.Files {
		src := filepath.Join(game, filepath.FromSlash(f.Path))
		mode := f.Operation
		if mode == "" {
			mode = "replace"
		}
		var original []byte
		if mode == "replace" {
			if err = checkRegular(src); err != nil {
				if !(f.AllowMissing && teamName.MatchString(f.Path) && os.IsNotExist(err)) {
					return fmt.Errorf("arquivo do Brasfoot ausente: %s: %w", f.Path, err)
				}
			} else {
				original, err = os.ReadFile(src)
				if err != nil {
					return err
				}
			}
			if f.Path == gameExecutablePath && (len(original) < 2 || original[0] != 0x4d || original[1] != 0x5a) {
				return fmt.Errorf("executável original não possui assinatura MZ reconhecida")
			}
		} else {
			if e := checkRegular(src); e == nil {
				original, err = os.ReadFile(src)
				if err != nil {
					return err
				}
				if digestBytes(original) != f.SHA256 || int64(len(original)) != f.Size {
					return fmt.Errorf("nova equipe não pode sobrescrever arquivo existente: %s", f.Path)
				}
			} else if !os.IsNotExist(e) {
				return fmt.Errorf("arquivo de destino incompatível: %s: %w", f.Path, e)
			}
		}
		current := digestBytes(original)
		var output []byte
		if current == f.SHA256 && int64(len(original)) == f.Size {
			output = original
		} else if f.LocalSource != "" {
			if !contains(f.AcceptedOriginalSHA256, current) {
				return &UnknownOriginalError{Relative: f.Path, Actual: current, Accepted: f.AcceptedOriginalSHA256}
			}
			output, err = os.ReadFile(f.LocalSource)
			if err != nil {
				return fmt.Errorf("cópia original de %s indisponível: %w", f.Path, err)
			}
			if digestBytes(output) != f.SHA256 || int64(len(output)) != f.Size {
				return fmt.Errorf("cópia original de %s não confere", f.Path)
			}
		} else {
			if mode == "replace" {
				allowed := f.AllowMissing && len(original) == 0
				for _, h := range f.AcceptedOriginalSHA256 {
					if current == h {
						allowed = true
						break
					}
				}
				if !allowed {
					return &UnknownOriginalError{Relative: f.Path, Actual: current, Accepted: f.AcceptedOriginalSHA256}
				}
			} else if len(f.AcceptedOriginalSHA256) != 0 {
				return fmt.Errorf("adição com hashes de originais indevidos: %s", f.Path)
			}
			var e error
			output, e = buildFromRecipe(fsys, original, f)
			if e != nil {
				return e
			}
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
