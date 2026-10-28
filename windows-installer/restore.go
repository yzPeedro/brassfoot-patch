package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

type backupRecord struct {
	SchemaVersion  int               `json:"schemaVersion"`
	AddedPaths     []string          `json:"addedPaths"`
	SkippedPaths   []string          `json:"skippedPaths"`
	Version        string            `json:"version"`
	Files          int               `json:"files"`
	Game           string            `json:"game"`
	Status         string            `json:"status"`
	OriginalSHA256 map[string]string `json:"originalSha256"`
}

// Locate the newest complete, validated backup belonging to exactly this
// installation and version. No writes are made by this function.
func findRestorableBackup(plan Plan) (string, backupRecord, error) {
	if !plan.AlreadyInstalled {
		return "", backupRecord{}, errors.New("o patch não está totalmente instalado; restauração automática bloqueada")
	}
	root, err := backupRoot()
	if err != nil {
		return "", backupRecord{}, err
	}
	// Use the same canonical backup root as install(); Windows temp paths can
	// have different textual spellings after symlink/short-path resolution.
	root, err = canonical(root)
	if err != nil {
		return "", backupRecord{}, err
	}
	dirs, err := os.ReadDir(root)
	if os.IsNotExist(err) {
		return "", backupRecord{}, errors.New("não existe backup anterior para esta instalação")
	}
	if err != nil {
		return "", backupRecord{}, err
	}
	names := []string{}
	for _, v := range dirs {
		if v.IsDir() && !v.Type().IsRegular() {
			names = append(names, v.Name())
		}
	}
	sort.Sort(sort.Reverse(sort.StringSlice(names)))
	for _, name := range names {
		dir := filepath.Join(root, name)
		if !within(dir, root) {
			continue
		}
		if info, err := os.Lstat(dir); err != nil || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
			continue
		}
		report := filepath.Join(dir, "install-report.json")
		if err := checkRegular(report); err != nil {
			continue
		}
		bytes, err := os.ReadFile(report)
		if err != nil || len(bytes) > 1024*1024 {
			continue
		}
		var saved backupRecord
		if err := json.Unmarshal(bytes, &saved); err != nil {
			continue
		}
		if saved.Status != "installed" || saved.Version != plan.Manifest.Version || !strings.EqualFold(filepath.Clean(saved.Game), filepath.Clean(plan.Game)) || saved.Files != len(plan.Items) || (plan.Manifest.SchemaVersion == 2 && len(saved.OriginalSHA256) != len(plan.Items)) || (plan.Manifest.SchemaVersion >= 3 && saved.SchemaVersion != plan.Manifest.SchemaVersion) {
			continue
		}
		valid := true
		additions := map[string]bool{}
		skipped := map[string]bool{}
		for _, name := range saved.AddedPaths {
			if additions[name] {
				valid = false
				break
			}
			additions[name] = true
		}
		for _, name := range saved.SkippedPaths {
			if skipped[name] || additions[name] {
				valid = false
				break
			}
			skipped[name] = true
		}
		if len(additions)+len(skipped)+len(saved.OriginalSHA256) != len(plan.Items) {
			valid = false
		}
		for _, item := range plan.Items {
			if !valid {
				break
			}
			if skipped[item.File.Path] {
				continue
			}
			if additions[item.File.Path] {
				if item.File.Operation != "add" && !item.File.AllowMissing {
					valid = false
				}
				if !additions[item.File.Path] {
					valid = false
				}
				continue
			}
			expected := saved.OriginalSHA256[item.File.Path]
			recognized := false
			for _, allowed := range item.File.AcceptedOriginalSHA256 {
				if expected == allowed {
					recognized = true
					break
				}
			}
			if !recognized {
				valid = false
				break
			}
			source := filepath.Join(dir, filepath.FromSlash(item.File.Path))
			if err := checkRegular(source); err != nil {
				valid = false
				break
			}
			full, err := canonical(source)
			if err != nil || !within(full, dir) {
				valid = false
				break
			}
			digest, err := sha(full)
			if err != nil || digest != expected {
				valid = false
				break
			}
		}
		if valid {
			return dir, saved, nil
		}
	}
	return "", backupRecord{}, errors.New("não encontrei backup íntegro e compatível com este patch; restauração automática indisponível")
}

// Restore ONLY signed targets recorded in the successful install report.
// On failure we attempt to roll back the restore to the patched state, so a
// partially undone patch is not silently left behind.
func restorePatch(plan Plan, progress func(int, int)) (string, error) {
	fresh, err := inspect(plan.Payload, plan.Game)
	if err != nil {
		return "", err
	}
	if !fresh.AlreadyInstalled {
		return "", errors.New("arquivos foram modificados após a instalação; não posso desfazer com segurança")
	}
	dir, record, err := findRestorableBackup(fresh)
	if err != nil {
		return "", err
	}
	if err := checkWritableTeams(fresh.Game); err != nil {
		return "", err
	}
	for _, item := range fresh.Items {
		if item.File.Path == gameExecutablePath {
			if err = checkWritableDirectory(fresh.Game); err != nil {
				return "", fmt.Errorf("não consigo restaurar o executável original: %w", err)
			}
		}
		if item.File.Path == nationalConfigPath {
			if err = checkWritableDirectory(filepath.Join(fresh.Game, "conf_ligas_nacionais")); err != nil {
				return "", fmt.Errorf("não consigo restaurar a configuração nacional: %w", err)
			}
			break
		}
	}
	completed := []Item{}
	addedPaths := map[string]bool{}
	for _, name := range record.AddedPaths {
		addedPaths[name] = true
	}
	rollback := func(problem error) (string, error) {
		failures := []string{}
		for i := len(completed) - 1; i >= 0; i-- {
			item := completed[i]
			if addedPaths[item.File.Path] {
				if _, err := os.Lstat(item.Target); errors.Is(err, os.ErrNotExist) {
					if e := copyFile(item.Source, item.Target); e != nil {
						failures = append(failures, item.File.Path+": "+e.Error())
					}
				} else if err != nil {
					failures = append(failures, item.File.Path+": "+err.Error())
				} else {
					failures = append(failures, item.File.Path+": inesperadamente presente durante rollback")
				}
				continue
			}
			if e := replaceVerified(item.Source, item.Target, item.File.SHA256); e != nil {
				failures = append(failures, item.File.Path+": "+e.Error())
			}
		}
		if len(failures) > 0 {
			return "", fmt.Errorf("restauração incompleta E recuperação do patch falhou: %s (backup: %s); causa: %w", strings.Join(failures, "; "), dir, problem)
		}
		return "", fmt.Errorf("restauração não concluída; patch anterior reaplicado. Backup preservado em %s: %w", dir, problem)
	}
	skippedPaths := map[string]bool{}
	for _, name := range record.SkippedPaths {
		skippedPaths[name] = true
	}
	for i, item := range fresh.Items {
		if skippedPaths[item.File.Path] {
			if progress != nil {
				progress(i+1, len(fresh.Items))
			}
			continue
		}
		if addedPaths[item.File.Path] {
			// Never remove a user-modified file.
			current, e := sha(item.Target)
			if e != nil || current != item.File.SHA256 {
				return rollback(fmt.Errorf("arquivo adicionado foi alterado: %s", item.File.Path))
			}
			if e = os.Remove(item.Target); e != nil {
				return rollback(e)
			}
			completed = append(completed, item)
		} else {
			original := filepath.Join(dir, filepath.FromSlash(item.File.Path))
			expected := record.OriginalSHA256[item.File.Path]
			completed = append(completed, item)
			if err := replaceVerified(original, item.Target, expected); err != nil {
				return rollback(err)
			}
		}
		if progress != nil {
			progress(i+1, len(fresh.Items))
		}
	}
	report := map[string]any{"status": "restored_original", "game": fresh.Game, "version": fresh.Manifest.Version, "restoredAt": time.Now().UTC().Format(time.RFC3339), "files": len(fresh.Items), "backupRetained": true}
	if b, e := json.MarshalIndent(report, "", "  "); e == nil {
		_ = os.WriteFile(filepath.Join(dir, "restore-report.json"), b, 0600)
	}
	return dir, nil
}
