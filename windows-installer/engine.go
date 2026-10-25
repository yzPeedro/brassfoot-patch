package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

// Windows homologation installer. It never downloads data or calls an API.
// The local game and the external homologation payload are never redistributed.
type Manifest struct {
	SchemaVersion             int            `json:"schemaVersion"`
	Kind                      string         `json:"kind"`
	PatchSeason               int            `json:"patchSeason"`
	Version                   string         `json:"version"`
	PublicationAllowed        bool           `json:"publicationAllowed"`
	CompatibilityTestedInGame bool           `json:"compatibilityTestedInGame"`
	Files                     []ManifestFile `json:"files"`
}
type ManifestFile struct {
	Operation              string   `json:"operation,omitempty"`
	Path                   string   `json:"path"`
	Size                   int64    `json:"size"`
	SHA256                 string   `json:"sha256"`
	AcceptedOriginalSHA256 []string `json:"acceptedOriginalSha256"`
}
type Item struct {
	File             ManifestFile
	Source, Target   string
	AlreadyInstalled bool
}
type Plan struct {
	Game, Payload    string
	Manifest         Manifest
	Items            []Item
	AlreadyInstalled bool
}
type InstallResult struct {
	Status, Version, BackupPath string
	Files                       int
	InstalledAt                 time.Time
}

type InstallOptions struct { // TestFailAfter is for automated rollback tests, never used by the GUI.
	TestFailAfter int
	Progress      func(stage string, completed, total int)
}

var (
	teamName     = regexp.MustCompile(`^teams/[a-zA-Z0-9_-]+\.banpackage main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

// Windows homologation installer. It never downloads data or calls an API.
// The local game and the external homologation payload are never redistributed.
type Manifest struct {
	SchemaVersion             int            `json:"schemaVersion"`
	Kind                      string         `json:"kind"`
	PatchSeason               int            `json:"patchSeason"`
	Version                   string         `json:"version"`
	PublicationAllowed        bool           `json:"publicationAllowed"`
	CompatibilityTestedInGame bool           `json:"compatibilityTestedInGame"`
	Files                     []ManifestFile `json:"files"`
}
type ManifestFile struct {
	Operation              string   `json:"operation,omitempty"`
	Path                   string   `json:"path"`
	Size                   int64    `json:"size"`
	SHA256                 string   `json:"sha256"`
	AcceptedOriginalSHA256 []string `json:"acceptedOriginalSha256"`
}
type Item struct {
	File             ManifestFile
	Source, Target   string
	AlreadyInstalled bool
}
type Plan struct {
	Game, Payload    string
	Manifest         Manifest
	Items            []Item
	AlreadyInstalled bool
}
type InstallResult struct {
	Status, Version, BackupPath string
	Files                       int
	InstalledAt                 time.Time
}

type InstallOptions struct { // TestFailAfter is for automated rollback tests, never used by the GUI.
	TestFailAfter int
	Progress      func(stage string, completed, total int)
}

var (
	)
	nationalConfigPath = "conf_ligas_nacionais/BRA.cfg"
	validHash    = regexp.MustCompile(`^[0-9a-f]{64}$`)
	validVersion = regexp.MustCompile(`^2026\.[0-9]+\.[0-9]+$`)
)

func sha(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	h := sha256.New()
	if _, err = io.Copy(h, f); err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}
func checkRegular(path string) error {
	info, err := os.Lstat(path)
	if err != nil {
		return err
	}
	if !info.Mode().IsRegular() {
		return fmt.Errorf("arquivo precisa ser regular (sem atalhos/links): %s", path)
	}
	return nil
}
func canonical(path string) (string, error) {
	full, err := filepath.Abs(path)
	if err != nil {
		return "", err
	}
	return filepath.EvalSymlinks(full)
}
func within(path, root string) bool {
	p, err := filepath.Rel(root, path)
	return err == nil && p != ".." && !strings.HasPrefix(p, ".."+string(filepath.Separator)) && !filepath.IsAbs(p)
}
func validGame(game string) (string, int, error) {
	game, err := canonical(game)
	if err != nil {
		return "", 0, fmt.Errorf("pasta do jogo não encontrada: %w", err)
	}
	if err = checkRegular(filepath.Join(game, "options.bcf")); err != nil {
		return "", 0, errors.New("pasta incompatível: não encontrei options.bcf regular")
	}
	dir := filepath.Join(game, "teams")
	d, err := os.Lstat(dir)
	if err != nil || !d.IsDir() || d.Mode()&os.ModeSymlink != 0 {
		return "", 0, errors.New("pasta incompatível: não encontrei teams/ válida")
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		return "", 0, err
	}
	count, valid := 0, 0
	for _, entry := range entries {
		if !strings.HasSuffix(strings.ToLower(entry.Name()), ".ban") || !entry.Type().IsRegular() {
			continue
		}
		count++
		f, err := os.Open(filepath.Join(dir, entry.Name()))
		if err != nil {
			continue
		}
		header := [4]byte{}
		n, e := io.ReadFull(f, header[:])
		f.Close()
		if e == nil && n == 4 && header == [4]byte{0xac, 0xed, 0x00, 0x05} {
			valid++
		}
	}
	if count < 10 || valid < 10 {
		return "", 0, fmt.Errorf("estrutura de equipes não reconhecida (%d .ban, %d assinaturas válidas)", count, valid)
	}
	return game, count, nil
}
func inspect(payloadPath, gamePath string) (Plan, error) {
	var p Plan
	game, _, err := validGame(gamePath)
	if err != nil {
		return p, err
	}
	payload, err := canonical(payloadPath)
	if err != nil {
		return p, fmt.Errorf("pasta do pacote ausente: %w", err)
	}
	if within(game, payload) || within(payload, game) {
		return p, errors.New("pacote e jogo precisam ficar em pastas separadas")
	}
	manifestPath := filepath.Join(payload, "manifest.json")
	if err = checkRegular(manifestPath); err != nil {
		return p, fmt.Errorf("manifest.json ausente ou inválido: %w", err)
	}
	stat, err := os.Stat(manifestPath)
	if err != nil {
		return p, err
	}
	if stat.Size() > 1024*1024 {
		return p, errors.New("manifesto grande demais")
	}
	buf, err := os.ReadFile(manifestPath)
	if err != nil {
		return p, err
	}
	var m Manifest
	if err = json.Unmarshal(buf, &m); err != nil {
		return p, fmt.Errorf("manifesto JSON inválido: %w", err)
	}
	if (m.SchemaVersion != 2 && m.SchemaVersion != 3) || m.PatchSeason != 2026 || !validVersion.MatchString(m.Version) {
		return p, errors.New("formato ou versão do pacote incompatível")
	}
	if !((m.Kind == "BRASFOOT_HOMOLOGATION_PATCH" && !m.PublicationAllowed && !m.CompatibilityTestedInGame) ||
		(m.Kind == "BRASFOOT_VERIFIED_PATCH" && m.PublicationAllowed && m.CompatibilityTestedInGame)) {
		return p, errors.New("marcadores de homologação/publicação incoerentes; instalação recusada")
	}
	if len(m.Files) < 1 || len(m.Files) > 512 {
		return p, errors.New("o pacote precisa ter de 1 a 512 arquivos .ban")
	}
	p = Plan{Game: game, Payload: payload, Manifest: m, AlreadyInstalled: true, Items: make([]Item, 0, len(m.Files))}
	seen := map[string]bool{}
	states := map[bool]bool{}
	for _, entry := range m.Files {
		isNationalConfig := entry.Path == nationalConfigPath && m.SchemaVersion == 3
		if !teamName.MatchString(entry.Path) && !isNationalConfig {
			return Plan{}, fmt.Errorf("caminho de patch proibido: %s", entry.Path)
		}
		mode := entry.Operation
		if mode == "" { mode = "replace" }
		if (m.SchemaVersion == 2 && entry.Operation != "") || (mode != "replace" && mode != "add" && mode != "verify") {
			return Plan{}, fmt.Errorf("operação não suportada para %s", entry.Path)
		}
		if m.SchemaVersion == 2 && mode == "add" {
			return Plan{}, errors.New("schema 2 não permite adicionar equipes")
		}
		if isNationalConfig && mode != "replace" {
			return Plan{}, errors.New("configuração de liga só pode substituir um BRA.cfg conhecido")
		}
		entry.Operation = mode
		key := strings.ToLower(entry.Path)
		if seen[key] {
			return Plan{}, errors.New("caminhos duplicados no pacote")
		}
		seen[key] = true
		if entry.Size < 4 || entry.Size > 25*1024*1024 || !validHash.MatchString(entry.SHA256) {
			return Plan{}, errors.New("tamanho/hash do pacote inválidos")
		}
		if mode == "replace" && (len(entry.AcceptedOriginalSHA256) == 0 || len(entry.AcceptedOriginalSHA256) > 64) {
			return Plan{}, errors.New("falta assinatura do arquivo original homologado")
		}
		if (mode == "add" || mode == "verify") && len(entry.AcceptedOriginalSHA256) != 0 {
			return Plan{}, errors.New("nova equipe não pode declarar hashes de originais")
		}
		allowed := false
		for _, v := range entry.AcceptedOriginalSHA256 {
			if !validHash.MatchString(v) {
				return Plan{}, errors.New("hash original inválido")
			}
			if v == entry.SHA256 {
				allowed = true
			}
		}
		if allowed {
			return Plan{}, errors.New("hash original não pode ser idêntico ao patch")
		}
		pathParts := strings.Split(entry.Path, "/")
		source := filepath.Join(payload, pathParts[0], pathParts[1])
		target := filepath.Join(game, pathParts[0], pathParts[1])
		// Replacement originals must exist; additions must not overwrite any unknown file.
		if err = checkRegular(source); err != nil {
			return Plan{}, fmt.Errorf("arquivo inválido no pacote: %s: %w", entry.Path, err)
		}
		actual, er := canonical(source)
		if er != nil || !within(actual, payload) {
			return Plan{}, errors.New("arquivo fora da pasta permitida")
		}
		if isNationalConfig {
			configDir := filepath.Dir(target)
			info, dirErr := os.Lstat(configDir)
			if dirErr != nil || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
				return Plan{}, errors.New("pasta conf_ligas_nacionais incompatível ou ausente")
			}
			resolved, dirErr := canonical(configDir)
			if dirErr != nil || !within(resolved, game) {
				return Plan{}, errors.New("pasta de ligas fora do Brasfoot")
			}
		}
		targetExists := true
		if err = checkRegular(target); err != nil {
			if mode == "add" && errors.Is(err, os.ErrNotExist) {
				targetExists = false
			} else {
				return Plan{}, fmt.Errorf("arquivo de equipe de destino incompatível: %s: %w", entry.Path, err)
			}
		}
		if !targetExists && mode == "verify" { return Plan{}, fmt.Errorf("clube historico a conferir esta ausente: %s",entry.Path) }
		if targetExists {
			actual, er = canonical(target)
			if er != nil || !within(actual, game) {
				return Plan{}, errors.New("arquivo de destino fora da pasta do jogo")
			}
		}

		data, err := os.Stat(source)
		if err != nil {
			return Plan{}, err
		}
		if data.Size() != entry.Size {
			return Plan{}, fmt.Errorf("tamanho divergente de %s", entry.Path)
		}
		f, err := os.Open(source)
		if err != nil {
			return Plan{}, err
		}
		h := [4]byte{}
		_, err = io.ReadFull(f, h[:])
		f.Close()
		if err != nil || h != [4]byte{0xac, 0xed, 0x00, 0x05} {
			return Plan{}, fmt.Errorf("arquivo serializado sem cabeçalho esperado: %s", entry.Path)
		}
		result, err := sha(source)
		if err != nil {
			return Plan{}, err
		}
		if result != entry.SHA256 {
			return Plan{}, fmt.Errorf("hash corrompido: %s", entry.Path)
		}
		isInstalled := false
		if targetExists {
			existing, e := sha(target)
			if e != nil { return Plan{}, e }
			isInstalled = existing == entry.SHA256
			if mode == "verify" && !isInstalled { return Plan{}, fmt.Errorf("arquivo historico difere do esperado: %s", entry.Path) }
			if !isInstalled {
				if mode == "add" {
					return Plan{}, fmt.Errorf("recusada adição: %s já existe com outro hash", entry.Path)
				}
				ok := false
				for _, v := range entry.AcceptedOriginalSHA256 { if existing == v { ok = true; break } }
				if !ok { return Plan{}, &UnknownOriginalError{Relative: entry.Path, Actual: existing, Accepted: entry.AcceptedOriginalSHA256} }
			}
		}
		if !isInstalled { p.AlreadyInstalled = false }
		states[isInstalled] = true
		p.Items = append(p.Items, Item{File: entry, Source: source, Target: target, AlreadyInstalled: isInstalled})
	}
	if m.SchemaVersion == 2 && len(states) > 1 {
		return Plan{}, errors.New("pacote parcialmente instalado: restaure sua cópia original antes de tentar novamente")
	}
	return p, nil
}
func copyFile(src, dst string) (err error) {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	f, err := os.OpenFile(dst, os.O_CREATE|os.O_WRONLY|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	defer func() {
		closeErr := f.Close()
		if err == nil {
			err = closeErr
		}
		if err != nil {
			_ = os.Remove(dst)
		}
	}()
	_, err = io.Copy(f, in)
	if err != nil {
		return err
	}
	return f.Sync()
}
func replaceVerified(source, target, expected string) error {
	dir := filepath.Dir(target)
	tmp, err := os.CreateTemp(dir, ".brassfoot-2026-*.tmp")
	if err != nil {
		return err
	}
	path := tmp.Name()
	tmp.Close()
	_ = os.Remove(path)
	defer os.Remove(path)
	if err = copyFile(source, path); err != nil {
		return err
	}
	h, err := sha(path)
	if err != nil {
		return err
	}
	if h != expected {
		return errors.New("integridade da cópia temporária inválida")
	}
	if err = swapReplace(path, target); err != nil {
		return err
	}
	h, err = sha(target)
	if err != nil {
		return err
	}
	if h != expected {
		return errors.New("hash final não confere")
	}
	return nil
}
func backupRoot() (string, error) {
	root := os.Getenv("LOCALAPPDATA")
	if root == "" {
		var err error
		root, err = os.UserConfigDir()
		if err != nil {
			return "", err
		}
	}
	return filepath.Join(root, "BrassfootPatch2026", "backups"), nil
}
// Check permissions before backups or replacements.
func checkWritableDirectory(dir string) error {
	f, err := os.CreateTemp(dir, ".brassfoot-write-check-*.tmp")
	if err != nil { return err }
	name := f.Name()
	closeErr := f.Close()
	removeErr := os.Remove(name)
	if closeErr != nil { return closeErr }
	return removeErr
}

func install(p Plan, opts InstallOptions) (InstallResult, error) {
	var res InstallResult
	if p.AlreadyInstalled {
		return InstallResult{Status: "already_installed", Version: p.Manifest.Version, Files: len(p.Items)}, nil
	}
	fresh, err := inspect(p.Payload, p.Game)
	if err != nil {
		return res, err
	}
	if fresh.AlreadyInstalled {
		return InstallResult{Status: "already_installed", Version: fresh.Manifest.Version, Files: len(fresh.Items)}, nil
	}
	if err = checkWritableTeams(p.Game); err != nil {
		return res, err
	}
	for _, item := range fresh.Items {
		if item.File.Path == nationalConfigPath {
			if err = checkWritableDirectory(filepath.Join(p.Game, "conf_ligas_nacionais")); err != nil {
				return res, fmt.Errorf("não consigo gravar a configuração nacional: %w", err)
			}
			break
		}
	}
	if len(fresh.Items) != len(p.Items) {
		return res, errors.New("pacote mudou após a verificação")
	}
	for i := range p.Items {
		if p.Items[i].File.SHA256 != fresh.Items[i].File.SHA256 || p.Items[i].File.Operation != fresh.Items[i].File.Operation || p.Items[i].AlreadyInstalled != fresh.Items[i].AlreadyInstalled || p.Items[i].Source != fresh.Items[i].Source || p.Items[i].Target != fresh.Items[i].Target {
			return res, errors.New("pacote mudou após a verificação")
		}
	}
	active := make([]Item, 0, len(fresh.Items))
	skipped := []string{}
	added := []string{}
	for _, item := range fresh.Items {
		if item.AlreadyInstalled { skipped = append(skipped, item.File.Path); continue }
		active = append(active, item)
		if item.File.Operation == "add" { added = append(added, item.File.Path) }
	}
	root, err := backupRoot()
	if err != nil {
		return res, err
	}
	if err = os.MkdirAll(root, 0700); err != nil {
		return res, err
	}
	root, err = canonical(root)
	if err != nil {
		return res, err
	}
	if within(root, p.Game) || within(p.Game, root) || within(root, p.Payload) {
		return res, errors.New("destino de backup inválido")
	}
	backup := filepath.Join(root, fmt.Sprintf("%s-%d", time.Now().UTC().Format("20060102-150405"), time.Now().UnixNano()))
	if err = os.Mkdir(backup, 0700); err != nil {
		return res, err
	}
	replaced := []Item{}
	backups := map[string]string{}
	report := map[string]any{"version": p.Manifest.Version, "files": len(p.Items), "game": p.Game, "backupsRetained": true, "addedPaths": added, "skippedPaths": skipped, "schemaVersion": p.Manifest.SchemaVersion}
	reportFile := func(name string) {
		b, e := json.MarshalIndent(report, "", "  ")
		if e == nil {
			_ = os.WriteFile(filepath.Join(backup, name), b, 0600)
		}
	}
	fail := func(cause error) (InstallResult, error) {
		failures := []string{}
		for i := len(replaced) - 1; i >= 0; i-- {
			item := replaced[i]
			if item.File.Operation == "add" {
				current, e := sha(item.Target)
				if errors.Is(e, os.ErrNotExist) { continue }
				if e != nil || current != item.File.SHA256 {
					failures = append(failures, item.File.Path+": arquivo criado foi modificado; exclusão automática recusada")
					continue
				}
				if e = os.Remove(item.Target); e != nil {
					failures = append(failures, item.File.Path+": "+e.Error())
				}
				continue
			}
			saved := backups[item.File.Path]
			hash, _ := sha(saved)
			expected := item.File.AcceptedOriginalSHA256
			valid := false
			for _, x := range expected {
				if x == hash {
					valid = true
					break
				}
			}
			if !valid {
				failures = append(failures, item.File.Path+": backup hash incorreto")
				continue
			}
			if e := replaceVerified(saved, item.Target, hash); e != nil {
				failures = append(failures, item.File.Path+": "+e.Error())
			}
		}
		report["status"] = "rolled_back"
		if len(failures) > 0 {
			report["status"] = "rollback_failed"
		}
		report["rollbackErrors"] = failures
		report["failure"] = cause.Error()
		reportFile("failure-report.json")
		if len(failures) > 0 {
			return InstallResult{}, fmt.Errorf("ERRO CRÍTICO: rollback incompleto; preserve backup %s: %w", backup, cause)
		}
		return InstallResult{}, fmt.Errorf("falha de instalação; originais restaurados; backup em %s: %w", backup, cause)
	}
	for idx, item := range active {
		if item.File.Operation == "add" { continue } // no existing file to back up
		saved := filepath.Join(backup, filepath.FromSlash(item.File.Path))
		if err = os.MkdirAll(filepath.Dir(saved), 0700); err != nil {
			return fail(err)
		}
		if err = copyFile(item.Target, saved); err != nil {
			return fail(err)
		}
		before, err := sha(item.Target)
		if err != nil {
			return fail(err)
		}
		after, err := sha(saved)
		if err != nil || before != after {
			return fail(errors.New("cópia de segurança não conferiu"))
		}
		backups[item.File.Path] = saved
		if opts.Progress != nil {
			opts.Progress("backup", idx+1, len(active))
		}
	}
	for idx, item := range active {
		if item.File.Operation == "add" {
			// O_EXCL refuses unexpected existing files; copyFile cleans partial creations.
			if err = copyFile(item.Source, item.Target); err != nil { return fail(err) }
			replaced = append(replaced, item)
			hash, e := sha(item.Target)
			if e != nil || hash != item.File.SHA256 { return fail(errors.New("arquivo adicionado não passou na verificação SHA-256")) }
		} else {
			// A failed atomic replacement might already have replaced the original.
			replaced = append(replaced, item)
			if err = replaceVerified(item.Source, item.Target, item.File.SHA256); err != nil { return fail(err) }
		}
		if opts.Progress != nil {
			opts.Progress("install", idx+1, len(active))
		}
		if opts.TestFailAfter > 0 && len(replaced) >= opts.TestFailAfter {
			return fail(errors.New("falha injetada em teste"))
		}
	}
	report["status"] = "installed"
	report["installedAt"] = time.Now().UTC().Format(time.RFC3339)
	report["originalSha256"] = func() map[string]string {
		out := map[string]string{}
		for k, v := range backups {
			h, _ := sha(v)
			out[k] = h
		}
		return out
	}()
	reportFile("install-report.json")
	if opts.Progress != nil {
		opts.Progress("done", len(active), len(active))
	}
	return InstallResult{Status: "installed", Version: p.Manifest.Version, BackupPath: backup, Files: len(p.Items), InstalledAt: time.Now()}, nil
}

// Inventory contains only local filenames, sizes and SHA-256 hashes. It never
// copies or distributes proprietary .ban contents and never modifies the game.
type InventoryRow struct {
	Path   string `json:"path"`
	Size   int64  `json:"size"`
	SHA256 string `json:"sha256"`
}
type Inventory struct {
	SchemaVersion int            `json:"schemaVersion"`
	Game          string         `json:"game"`
	ScannedAt     time.Time      `json:"scannedAt"`
	TeamCount     int            `json:"teamCount"`
	Teams         []InventoryRow `json:"teams"`
}

func exportInventory(game string) (string, error) {
	game, _, err := validGame(game)
	if err != nil {
		return "", err
	}
	entries, err := os.ReadDir(filepath.Join(game, "teams"))
	if err != nil {
		return "", err
	}
	rows := []InventoryRow{}
	for _, v := range entries {
		if !strings.HasSuffix(strings.ToLower(v.Name()), ".ban") || !v.Type().IsRegular() {
			continue
		}
		path := filepath.Join(game, "teams", v.Name())
		if err := checkRegular(path); err != nil {
			return "", err
		}
		h, err := sha(path)
		if err != nil {
			return "", err
		}
		stat, err := os.Stat(path)
		if err != nil {
			return "", err
		}
		rows = append(rows, InventoryRow{Path: "teams/" + v.Name(), Size: stat.Size(), SHA256: h})
	}
	sort.Slice(rows, func(i, j int) bool { return rows[i].Path < rows[j].Path })
	root, err := backupRoot()
	if err != nil {
		return "", err
	}
	dir := filepath.Join(filepath.Dir(root), "reports")
	if err = os.MkdirAll(dir, 0700); err != nil {
		return "", err
	}
	path := filepath.Join(dir, "brassfoot-inventory.json")
	result := Inventory{SchemaVersion: 1, Game: game, ScannedAt: time.Now().UTC(), TeamCount: len(rows), Teams: rows}
	buf, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return "", err
	}
	if err = os.WriteFile(path, buf, 0600); err != nil {
		return "", err
	}
	return path, nil
}
