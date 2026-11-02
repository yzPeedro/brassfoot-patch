package main

import (
	"archive/zip"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"sync"
)

const (
	componentRosters = "rosters"
	componentSeason  = "season"
	variantOriginal  = "original"
	variantSeason    = "season"
	variantLive      = "live"
	variantFull      = "full"
)

type TargetState struct {
	Rosters bool `json:"rosters"`
	Season  bool `json:"season"`
	Live    bool `json:"live"`
}

type ComponentReport struct {
	Targets   bool            `json:"targets"`
	Rosters   string          `json:"rosters"`
	Season    string          `json:"season"`
	Live      string          `json:"live"`
	Removable map[string]bool `json:"removable"`
	Missing   map[string]int  `json:"missingOriginals"`
}

type TargetPlan struct {
	Plan    Plan
	Deletes []string
	Empty   bool
}

var harvestMutex sync.Mutex

func supportsTargets(m Manifest) bool {
	if m.Components == nil || len(m.Components.Variants) != 4 {
		return false
	}
	for _, key := range []string{variantOriginal, variantSeason, variantLive, variantFull} {
		if _, ok := m.Components.Variants[key]; !ok {
			return false
		}
	}
	return true
}

func fileComponent(f ManifestFile) string {
	if f.Component != "" {
		return f.Component
	}
	if f.Path == nationalConfigPath {
		return componentSeason
	}
	return componentRosters
}

func variantFor(target TargetState) string {
	switch {
	case target.Season && target.Live:
		return variantFull
	case target.Season:
		return variantSeason
	case target.Live:
		return variantLive
	}
	return variantOriginal
}

func originalsRoot() (string, error) {
	root, err := backupRoot()
	if err != nil {
		return "", err
	}
	return filepath.Join(filepath.Dir(root), "originals"), nil
}

func storedOriginal(hash string) (string, bool) {
	if !validHash.MatchString(hash) {
		return "", false
	}
	root, err := originalsRoot()
	if err != nil {
		return "", false
	}
	path := filepath.Join(root, hash)
	if current, e := sha(path); e == nil && current == hash {
		return path, true
	}
	return "", false
}

func keepOriginal(source io.Reader, hash string) error {
	if _, ok := storedOriginal(hash); ok {
		return nil
	}
	root, err := originalsRoot()
	if err != nil {
		return err
	}
	if err = os.MkdirAll(root, 0700); err != nil {
		return err
	}
	return writeVerified(filepath.Join(root, hash), source, hash)
}

func keepOriginalFile(path, hash string) {
	if current, err := sha(path); err != nil || current != hash {
		return
	}
	file, err := os.Open(path)
	if err != nil {
		return
	}
	defer file.Close()
	_ = keepOriginal(file, hash)
}

func harvestOriginals(m Manifest, game string) {
	harvestMutex.Lock()
	defer harvestMutex.Unlock()
	vanilla := map[string]string{}
	for _, f := range m.Files {
		if validHash.MatchString(f.VanillaSHA256) {
			vanilla[f.Path] = f.VanillaSHA256
		}
	}
	if len(vanilla) == 0 {
		return
	}
	for path, hash := range vanilla {
		if _, ok := storedOriginal(hash); !ok {
			keepOriginalFile(filepath.Join(game, filepath.FromSlash(path)), hash)
		}
	}
	if root, err := backupRoot(); err == nil {
		if entries, e := os.ReadDir(root); e == nil {
			for _, entry := range entries {
				if !entry.IsDir() {
					continue
				}
				dir := filepath.Join(root, entry.Name())
				body, e := os.ReadFile(filepath.Join(dir, "install-report.json"))
				if e != nil {
					continue
				}
				var report struct {
					OriginalSHA256 map[string]string `json:"originalSha256"`
				}
				if json.Unmarshal(body, &report) != nil {
					continue
				}
				for path, hash := range report.OriginalSHA256 {
					if vanilla[path] == hash {
						if _, ok := storedOriginal(hash); !ok {
							if saved, e := safeTarget(dir, path); e == nil {
								keepOriginalFile(saved, hash)
							}
						}
					}
				}
			}
		}
	}
	if root, err := snapshotRoot(); err == nil {
		if entries, e := os.ReadDir(root); e == nil {
			for _, entry := range entries {
				if !strings.HasSuffix(entry.Name(), ".json") {
					continue
				}
				record, e := readSnapshotRecord(filepath.Join(root, entry.Name()))
				if e != nil {
					continue
				}
				wanted := map[string]string{}
				for _, f := range record.Files {
					if vanilla[f.Path] == f.SHA256 {
						if _, ok := storedOriginal(f.SHA256); !ok {
							wanted[f.Path] = f.SHA256
						}
					}
				}
				if len(wanted) == 0 {
					continue
				}
				reader, e := zip.OpenReader(filepath.Join(root, record.ID+".zip"))
				if e != nil {
					continue
				}
				for _, file := range reader.File {
					hash, ok := wanted[file.Name]
					if !ok {
						continue
					}
					if stream, e := file.Open(); e == nil {
						_ = keepOriginal(stream, hash)
						stream.Close()
					}
				}
				reader.Close()
			}
		}
	}
}

func componentReport(m Manifest, game string) ComponentReport {
	report := ComponentReport{Removable: map[string]bool{}, Missing: map[string]int{}}
	if !supportsTargets(m) {
		state, err := detectState(m, game)
		if err == nil {
			patch, live := componentStatus(m, state)
			report.Rosters, report.Season, report.Live = patch, patch, live
		}
		return report
	}
	report.Targets = true
	variants := m.Components.Variants
	exeHash, _ := sha(filepath.Join(game, gameExecutablePath))
	seasonFeature := contains(m.Components.SeasonExecutableSHA256, exeHash) || exeHash == variants[variantFull].SHA256 || exeHash == variants[variantSeason].SHA256
	liveFeature := contains(m.Components.LiveExecutableSHA256, exeHash) || exeHash == variants[variantFull].SHA256 || exeHash == variants[variantLive].SHA256
	exeCurrent := exeHash == variants[variantFull].SHA256 || exeHash == variants[variantSeason].SHA256 || exeHash == variants[variantLive].SHA256
	counts := map[string]map[string]int{componentRosters: {}, componentSeason: {}}
	for _, f := range m.Files {
		if f.Path == gameExecutablePath {
			continue
		}
		component := fileComponent(f)
		hash, err := sha(filepath.Join(game, filepath.FromSlash(f.Path)))
		state := "other"
		switch {
		case err == nil && hash == f.SHA256:
			state = "current"
		case err != nil && f.VanillaMissing:
			state = "vanilla"
		case err == nil && hash == f.VanillaSHA256:
			state = "vanilla"
		}
		counts[component][state]++
		counts[component]["total"]++
		if state != "vanilla" && !f.VanillaMissing {
			if _, ok := storedOriginal(f.VanillaSHA256); !ok {
				report.Missing[component]++
			}
		}
	}
	rosters := counts[componentRosters]
	switch {
	case rosters["total"] > 0 && rosters["current"] == rosters["total"]:
		report.Rosters = statusCurrent
	case rosters["vanilla"] == rosters["total"]:
		report.Rosters = statusAbsent
	default:
		report.Rosters = statusOutdated
	}
	season := counts[componentSeason]
	configCurrent := season["total"] == 0 || season["current"] == season["total"]
	configVanilla := season["total"] == 0 || season["vanilla"] == season["total"]
	switch {
	case seasonFeature && exeCurrent && configCurrent:
		report.Season = statusCurrent
	case !seasonFeature && configVanilla:
		report.Season = statusAbsent
	default:
		report.Season = statusOutdated
	}
	switch {
	case liveFeature && exeCurrent:
		report.Live = statusCurrent
	case liveFeature:
		report.Live = statusOutdated
	default:
		report.Live = statusAbsent
	}
	report.Removable[componentRosters] = report.Rosters != statusAbsent && report.Missing[componentRosters] == 0
	report.Removable[componentSeason] = report.Season != statusAbsent && report.Missing[componentSeason] == 0
	report.Removable[componentLive] = report.Live != statusAbsent
	return report
}

func targetManifest(m Manifest, game string, target TargetState) (Manifest, []string, error) {
	out := m
	out.Files = nil
	deletes := []string{}
	for _, f := range m.Files {
		if f.Path == gameExecutablePath {
			continue
		}
		want := target.Rosters
		if fileComponent(f) == componentSeason {
			want = target.Season
		}
		path := filepath.Join(game, filepath.FromSlash(f.Path))
		hash, err := sha(path)
		if want {
			if err == nil && hash == f.SHA256 {
				continue
			}
			out.Files = append(out.Files, f)
			continue
		}
		if err != nil {
			if f.VanillaMissing && errors.Is(err, os.ErrNotExist) {
				continue
			}
			return Manifest{}, nil, fmt.Errorf("arquivo do Brasfoot ausente: %s", f.Path)
		}
		if hash == f.VanillaSHA256 {
			continue
		}
		if f.VanillaMissing {
			if hash == f.SHA256 || contains(f.AcceptedOriginalSHA256, hash) {
				deletes = append(deletes, f.Path)
				continue
			}
			return Manifest{}, nil, &UnknownOriginalError{Relative: f.Path, Actual: hash, Accepted: f.AcceptedOriginalSHA256}
		}
		source, ok := storedOriginal(f.VanillaSHA256)
		if !ok {
			return Manifest{}, nil, fmt.Errorf("cópia original indisponível neste computador: %s", f.Path)
		}
		out.Files = append(out.Files, ManifestFile{
			Operation: "replace", Path: f.Path, Size: f.VanillaSize, SHA256: f.VanillaSHA256,
			AcceptedOriginalSHA256: []string{hash}, Component: f.Component, LocalSource: source,
		})
	}
	full, hasExecutable := executableEntry(m)
	if hasExecutable {
		variant := m.Components.Variants[variantFor(target)]
		hash, err := sha(filepath.Join(game, gameExecutablePath))
		if err != nil {
			return Manifest{}, nil, fmt.Errorf("executável do Brasfoot ausente: %w", err)
		}
		if hash != variant.SHA256 {
			if variant.SHA256 == full.SHA256 {
				out.Files = append(out.Files, full)
			} else {
				entry := ManifestFile{Operation: "replace", Path: gameExecutablePath, Size: variant.Size, SHA256: variant.SHA256,
					AcceptedOriginalSHA256: append([]string{}, variant.AcceptedOriginalSHA256...), Recipe: variant.Recipe}
				if !contains(entry.AcceptedOriginalSHA256, hash) {
					if hash != full.SHA256 && !contains(full.AcceptedOriginalSHA256, hash) {
						return Manifest{}, nil, &UnknownOriginalError{Relative: gameExecutablePath, Actual: hash, Accepted: full.AcceptedOriginalSHA256}
					}
					via := full
					via.Recipe = ""
					via.Via = nil
					entry.Via = &via
					entry.AcceptedOriginalSHA256 = append(entry.AcceptedOriginalSHA256, hash)
				}
				out.Files = append(out.Files, entry)
			}
		}
	}
	return out, deletes, nil
}

func stageTarget(root, game string, target TargetState) (TargetPlan, error) {
	m := bundledManifestFromFS()
	if len(m.Files) == 0 {
		return TargetPlan{}, errors.New("nenhuma versão do patch foi carregada; conecte-se à internet e tente de novo")
	}
	if !supportsTargets(m) {
		return TargetPlan{}, errors.New("esta versão do patch ainda não permite escolher ou remover componentes")
	}
	resolved, _, err := validGame(game)
	if err != nil {
		return TargetPlan{}, err
	}
	harvestOriginals(m, resolved)
	cm, deletes, err := targetManifest(m, resolved, target)
	if err != nil {
		return TargetPlan{}, err
	}
	if len(cm.Files) == 0 {
		return TargetPlan{Deletes: deletes, Empty: len(deletes) == 0, Plan: Plan{Game: resolved, Manifest: cm, AlreadyInstalled: true}}, nil
	}
	staged, err := os.MkdirTemp(root, "target-")
	if err != nil {
		return TargetPlan{}, err
	}
	body, err := json.MarshalIndent(cm, "", "  ")
	if err != nil {
		return TargetPlan{}, err
	}
	if err = os.WriteFile(filepath.Join(staged, "manifest.json"), body, 0600); err != nil {
		return TargetPlan{}, err
	}
	if err = preparePayloadManifest(currentPayload(), cm, resolved, staged); err != nil {
		return TargetPlan{}, err
	}
	plan, err := inspect(staged, resolved)
	if err != nil {
		return TargetPlan{}, err
	}
	return TargetPlan{Plan: plan, Deletes: deletes}, nil
}

func applyTarget(tp TargetPlan, options InstallOptions) (InstallResult, error) {
	result := InstallResult{Status: "installed", Version: tp.Plan.Manifest.Version}
	if len(tp.Plan.Items) > 0 && !tp.Plan.AlreadyInstalled {
		var err error
		result, err = install(tp.Plan, options)
		if err != nil {
			return result, err
		}
	}
	if len(tp.Deletes) == 0 {
		return result, nil
	}
	backup := result.BackupPath
	if backup == "" {
		root, err := backupRoot()
		if err != nil {
			return result, err
		}
		backup, err = os.MkdirTemp(root, "remocao-")
		if err != nil {
			return result, err
		}
		result.BackupPath = backup
	}
	reportPath := filepath.Join(backup, "install-report.json")
	report := map[string]any{}
	if body, err := os.ReadFile(reportPath); err == nil {
		_ = json.Unmarshal(body, &report)
	}
	report["game"] = tp.Plan.Game
	originals, _ := report["originalSha256"].(map[string]any)
	if originals == nil {
		originals = map[string]any{}
	}
	for _, path := range tp.Deletes {
		source := filepath.Join(tp.Plan.Game, filepath.FromSlash(path))
		saved, err := safeTarget(backup, path)
		if err != nil {
			return result, err
		}
		if err = os.MkdirAll(filepath.Dir(saved), 0700); err != nil {
			return result, err
		}
		if err = copyFile(source, saved); err != nil {
			return result, err
		}
		hash, err := sha(saved)
		if err != nil {
			return result, err
		}
		originals[path] = hash
		if err = os.Remove(source); err != nil {
			return result, err
		}
		result.Files++
	}
	report["originalSha256"] = originals
	report["status"] = "installed"
	body, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return result, err
	}
	return result, os.WriteFile(reportPath, body, 0600)
}

func importOriginalsFrom(m Manifest, folder string) (int, error) {
	if _, _, err := validGame(folder); err != nil {
		return 0, err
	}
	imported := 0
	for _, f := range m.Files {
		if !validHash.MatchString(f.VanillaSHA256) {
			continue
		}
		if _, ok := storedOriginal(f.VanillaSHA256); ok {
			continue
		}
		path := filepath.Join(folder, filepath.FromSlash(f.Path))
		keepOriginalFile(path, f.VanillaSHA256)
		if _, ok := storedOriginal(f.VanillaSHA256); ok {
			imported++
		}
	}
	return imported, nil
}
