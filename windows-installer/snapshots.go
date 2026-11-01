package main

import (
	"archive/zip"
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

const (
	backupKindInstall  = "install"
	backupKindSnapshot = "snapshot"
	maxSnapshotBytes   = 4 << 30
)

var (
	backupID          = regexp.MustCompile(`^[0-9]{8}-[0-9]{6}-[0-9A-Za-z-]+$`)
	snapshotPrunedDir = map[string]bool{"teams": true, "conf_ligas_nacionais": true, "conf_estadual": true}
)

type BackupEntry struct {
	ID        string `json:"id"`
	Kind      string `json:"kind"`
	Label     string `json:"label"`
	CreatedAt string `json:"createdAt"`
	Files     int    `json:"files"`
	Size      int64  `json:"size"`
	Version   string `json:"version,omitempty"`
	Game      string `json:"game"`
	Path      string `json:"path"`
}

type snapshotFile struct {
	Path   string `json:"path"`
	Size   int64  `json:"size"`
	SHA256 string `json:"sha256"`
}

type snapshotRecord struct {
	SchemaVersion int            `json:"schemaVersion"`
	ID            string         `json:"id"`
	Label         string         `json:"label"`
	CreatedAt     string         `json:"createdAt"`
	Game          string         `json:"game"`
	Version       string         `json:"version"`
	Files         []snapshotFile `json:"files"`
}

func snapshotRoot() (string, error) {
	root, err := backupRoot()
	if err != nil {
		return "", err
	}
	return filepath.Join(filepath.Dir(root), "snapshots"), nil
}

func newBackupID(now time.Time) string {
	return now.Format("20060102-150405") + fmt.Sprintf("-%d", now.UnixNano()%1000000000)
}

func listBackups() ([]BackupEntry, error) {
	entries := []BackupEntry{}
	if root, err := backupRoot(); err == nil {
		dirs, _ := os.ReadDir(root)
		for _, dir := range dirs {
			if !dir.IsDir() || !backupID.MatchString(dir.Name()) {
				continue
			}
			path := filepath.Join(root, dir.Name())
			body, err := os.ReadFile(filepath.Join(path, "install-report.json"))
			if err != nil {
				continue
			}
			var report struct {
				Status         string            `json:"status"`
				Version        string            `json:"version"`
				Game           string            `json:"game"`
				InstalledAt    string            `json:"installedAt"`
				OriginalSHA256 map[string]string `json:"originalSha256"`
				AddedPaths     []string          `json:"addedPaths"`
			}
			if json.Unmarshal(body, &report) != nil || report.Status != "installed" {
				continue
			}
			if len(report.OriginalSHA256) == 0 && len(report.AddedPaths) == 0 {
				continue
			}
			var size int64
			for name := range report.OriginalSHA256 {
				if info, e := os.Stat(filepath.Join(path, filepath.FromSlash(name))); e == nil {
					size += info.Size()
				}
			}
			entries = append(entries, BackupEntry{
				ID: dir.Name(), Kind: backupKindInstall, Label: "Antes da instalação " + report.Version,
				CreatedAt: report.InstalledAt, Files: len(report.OriginalSHA256) + len(report.AddedPaths),
				Size: size, Version: report.Version, Game: report.Game, Path: path,
			})
		}
	}
	if root, err := snapshotRoot(); err == nil {
		files, _ := os.ReadDir(root)
		for _, file := range files {
			name := file.Name()
			if file.IsDir() || !strings.HasSuffix(name, ".json") || !backupID.MatchString(strings.TrimSuffix(name, ".json")) {
				continue
			}
			record, err := readSnapshotRecord(filepath.Join(root, name))
			if err != nil {
				continue
			}
			archive := filepath.Join(root, record.ID+".zip")
			info, err := os.Stat(archive)
			if err != nil {
				continue
			}
			entries = append(entries, BackupEntry{
				ID: record.ID, Kind: backupKindSnapshot, Label: record.Label, CreatedAt: record.CreatedAt,
				Files: len(record.Files), Size: info.Size(), Version: record.Version, Game: record.Game, Path: archive,
			})
		}
	}
	sort.Slice(entries, func(i, j int) bool { return entries[i].ID > entries[j].ID })
	return entries, nil
}

func readSnapshotRecord(path string) (snapshotRecord, error) {
	var record snapshotRecord
	body, err := os.ReadFile(path)
	if err != nil {
		return record, err
	}
	if err = json.Unmarshal(body, &record); err != nil {
		return record, err
	}
	if record.SchemaVersion != 1 || !backupID.MatchString(record.ID) || len(record.Files) == 0 {
		return record, errors.New("registro de backup inválido")
	}
	return record, nil
}

func gameFiles(game string) ([]string, int64, error) {
	files := []string{}
	var total int64
	err := filepath.WalkDir(game, func(path string, entry os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.Type()&os.ModeSymlink != 0 {
			if entry.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}
		if entry.IsDir() || !entry.Type().IsRegular() {
			return nil
		}
		info, err := entry.Info()
		if err != nil {
			return err
		}
		total += info.Size()
		if total > maxSnapshotBytes {
			return errors.New("a pasta do jogo é grande demais para um backup completo")
		}
		relative, err := filepath.Rel(game, path)
		if err != nil {
			return err
		}
		files = append(files, filepath.ToSlash(relative))
		return nil
	})
	sort.Strings(files)
	return files, total, err
}

func createGameSnapshot(gamePath, label, version string, progress func(done, total int)) (BackupEntry, error) {
	game, _, err := validGame(gamePath)
	if err != nil {
		return BackupEntry{}, err
	}
	root, err := snapshotRoot()
	if err != nil {
		return BackupEntry{}, err
	}
	if err = os.MkdirAll(root, 0700); err != nil {
		return BackupEntry{}, err
	}
	files, _, err := gameFiles(game)
	if err != nil {
		return BackupEntry{}, err
	}
	now := time.Now()
	id := newBackupID(now)
	archivePath := filepath.Join(root, id+".zip")
	partial := archivePath + ".partial"
	out, err := os.OpenFile(partial, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		return BackupEntry{}, err
	}
	record := snapshotRecord{SchemaVersion: 1, ID: id, Label: label, CreatedAt: now.UTC().Format(time.RFC3339), Game: game, Version: version}
	writer := zip.NewWriter(out)
	fail := func(cause error) (BackupEntry, error) {
		writer.Close()
		out.Close()
		os.Remove(partial)
		return BackupEntry{}, cause
	}
	for index, name := range files {
		source, err := os.Open(filepath.Join(game, filepath.FromSlash(name)))
		if err != nil {
			return fail(err)
		}
		header := &zip.FileHeader{Name: name, Method: zip.Deflate, Modified: now}
		target, err := writer.CreateHeader(header)
		if err != nil {
			source.Close()
			return fail(err)
		}
		hash := sha256.New()
		size, err := io.Copy(io.MultiWriter(target, hash), source)
		source.Close()
		if err != nil {
			return fail(err)
		}
		record.Files = append(record.Files, snapshotFile{Path: name, Size: size, SHA256: hex.EncodeToString(hash.Sum(nil))})
		if progress != nil {
			progress(index+1, len(files))
		}
	}
	if err = writer.Close(); err != nil {
		return fail(err)
	}
	if err = out.Sync(); err != nil {
		return fail(err)
	}
	if err = out.Close(); err != nil {
		os.Remove(partial)
		return BackupEntry{}, err
	}
	if err = verifySnapshot(partial, record); err != nil {
		os.Remove(partial)
		return BackupEntry{}, err
	}
	body, err := json.MarshalIndent(record, "", "  ")
	if err != nil {
		os.Remove(partial)
		return BackupEntry{}, err
	}
	if err = os.Rename(partial, archivePath); err != nil {
		os.Remove(partial)
		return BackupEntry{}, err
	}
	if err = os.WriteFile(filepath.Join(root, id+".json"), body, 0600); err != nil {
		os.Remove(archivePath)
		return BackupEntry{}, err
	}
	info, _ := os.Stat(archivePath)
	entry := BackupEntry{ID: id, Kind: backupKindSnapshot, Label: label, CreatedAt: record.CreatedAt, Files: len(record.Files), Version: version, Game: game, Path: archivePath}
	if info != nil {
		entry.Size = info.Size()
	}
	return entry, nil
}

func verifySnapshot(archivePath string, record snapshotRecord) error {
	reader, err := zip.OpenReader(archivePath)
	if err != nil {
		return err
	}
	defer reader.Close()
	expected := map[string]snapshotFile{}
	for _, f := range record.Files {
		expected[f.Path] = f
	}
	if len(reader.File) != len(expected) {
		return errors.New("o backup não contém todos os arquivos registrados")
	}
	for _, f := range reader.File {
		want, ok := expected[f.Name]
		if !ok {
			return fmt.Errorf("arquivo inesperado no backup: %s", f.Name)
		}
		hash, size, err := zipEntryDigest(f)
		if err != nil {
			return err
		}
		if hash != want.SHA256 || size != want.Size {
			return fmt.Errorf("o backup não conferiu: %s", f.Name)
		}
	}
	return nil
}

func zipEntryDigest(f *zip.File) (string, int64, error) {
	source, err := f.Open()
	if err != nil {
		return "", 0, err
	}
	defer source.Close()
	hash := sha256.New()
	size, err := io.Copy(hash, io.LimitReader(source, maxSnapshotBytes))
	return hex.EncodeToString(hash.Sum(nil)), size, err
}

func safeTarget(game, relative string) (string, error) {
	clean := filepath.Clean(filepath.FromSlash(relative))
	if relative == "" || filepath.IsAbs(clean) || strings.HasPrefix(clean, "..") || strings.Contains(relative, "\\") {
		return "", fmt.Errorf("caminho inválido no backup: %s", relative)
	}
	target := filepath.Join(game, clean)
	if !within(target, game) {
		return "", fmt.Errorf("caminho fora do jogo: %s", relative)
	}
	return target, nil
}

func writeVerified(target string, source io.Reader, expected string) error {
	if err := os.MkdirAll(filepath.Dir(target), 0700); err != nil {
		return err
	}
	temporary, err := os.CreateTemp(filepath.Dir(target), ".mega-restore-*.tmp")
	if err != nil {
		return err
	}
	name := temporary.Name()
	hash := sha256.New()
	_, err = io.Copy(io.MultiWriter(temporary, hash), source)
	if closeErr := temporary.Close(); err == nil {
		err = closeErr
	}
	if err == nil && hex.EncodeToString(hash.Sum(nil)) != expected {
		err = errors.New("arquivo restaurado não conferiu")
	}
	if err == nil {
		err = os.Rename(name, target)
	}
	if err != nil {
		os.Remove(name)
	}
	return err
}

func restoreSnapshot(entry BackupEntry, game string, progress func(done, total int)) error {
	root, err := snapshotRoot()
	if err != nil {
		return err
	}
	record, err := readSnapshotRecord(filepath.Join(root, entry.ID+".json"))
	if err != nil {
		return err
	}
	archivePath := filepath.Join(root, record.ID+".zip")
	if err = verifySnapshot(archivePath, record); err != nil {
		return err
	}
	reader, err := zip.OpenReader(archivePath)
	if err != nil {
		return err
	}
	defer reader.Close()
	expected := map[string]string{}
	for _, f := range record.Files {
		expected[f.Path] = f.SHA256
	}
	for index, f := range reader.File {
		target, err := safeTarget(game, f.Name)
		if err != nil {
			return err
		}
		if current, e := sha(target); e == nil && current == expected[f.Name] {
			if progress != nil {
				progress(index+1, len(reader.File))
			}
			continue
		}
		source, err := f.Open()
		if err != nil {
			return err
		}
		err = writeVerified(target, source, expected[f.Name])
		source.Close()
		if err != nil {
			return fmt.Errorf("%s: %w", f.Name, err)
		}
		if progress != nil {
			progress(index+1, len(reader.File))
		}
	}
	current, _, err := gameFiles(game)
	if err != nil {
		return err
	}
	for _, name := range current {
		top := strings.SplitN(name, "/", 2)[0]
		if _, kept := expected[name]; kept || !snapshotPrunedDir[top] || !strings.Contains(name, "/") {
			continue
		}
		if target, e := safeTarget(game, name); e == nil {
			if e = os.Remove(target); e != nil {
				return e
			}
		}
	}
	return nil
}

func restoreInstallBackup(entry BackupEntry, game string, progress func(done, total int)) error {
	root, err := backupRoot()
	if err != nil {
		return err
	}
	dir := filepath.Join(root, entry.ID)
	body, err := os.ReadFile(filepath.Join(dir, "install-report.json"))
	if err != nil {
		return err
	}
	var report struct {
		Game           string            `json:"game"`
		OriginalSHA256 map[string]string `json:"originalSha256"`
		AddedPaths     []string          `json:"addedPaths"`
	}
	if err = json.Unmarshal(body, &report); err != nil {
		return err
	}
	if report.Game != "" && !sameFolder(report.Game, game) {
		return errors.New("este backup pertence a outra pasta do Brasfoot")
	}
	names := make([]string, 0, len(report.OriginalSHA256))
	for name := range report.OriginalSHA256 {
		names = append(names, name)
	}
	sort.Strings(names)
	total := len(names) + len(report.AddedPaths)
	for index, name := range names {
		if name != gameExecutablePath && name != nationalConfigPath && !teamName.MatchString(name) {
			return fmt.Errorf("arquivo não autorizado no backup: %s", name)
		}
		target, err := safeTarget(game, name)
		if err != nil {
			return err
		}
		saved, err := safeTarget(dir, name)
		if err != nil {
			return err
		}
		expected := report.OriginalSHA256[name]
		if hash, e := sha(saved); e != nil || hash != expected {
			return fmt.Errorf("cópia de %s não confere", name)
		}
		if current, e := sha(target); e != nil || current != expected {
			if err = replaceVerified(saved, target, expected); err != nil {
				return fmt.Errorf("%s: %w", name, err)
			}
		}
		if progress != nil {
			progress(index+1, total)
		}
	}
	for index, name := range report.AddedPaths {
		if !teamName.MatchString(name) {
			continue
		}
		if target, e := safeTarget(game, name); e == nil {
			if _, statErr := os.Lstat(target); statErr == nil {
				if err = os.Remove(target); err != nil {
					return err
				}
			}
		}
		if progress != nil {
			progress(len(names)+index+1, total)
		}
	}
	return nil
}

func findBackup(id string) (BackupEntry, error) {
	entries, err := listBackups()
	if err != nil {
		return BackupEntry{}, err
	}
	for _, entry := range entries {
		if entry.ID == id {
			return entry, nil
		}
	}
	return BackupEntry{}, errors.New("backup não encontrado")
}
