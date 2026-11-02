package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

const (
	componentPatch     = "patch"
	componentLive      = "live"
	componentPatchLive = "patch+live"
)

var recipeName = regexp.MustCompile(`^[A-Za-z0-9._-]+\.json$`)

type ComponentConfig struct {
	SchemaVersion            int                            `json:"schemaVersion"`
	OriginalExecutableSHA256 string                         `json:"originalExecutableSha256"`
	LiveExecutableSHA256     []string                       `json:"liveExecutableSha256"`
	LiveOnlyExecutableSHA256 []string                       `json:"liveOnlyExecutableSha256,omitempty"`
	SeasonExecutableSHA256   []string                       `json:"seasonExecutableSha256,omitempty"`
	Executables              map[string]ComponentExecutable `json:"executables"`
	Variants                 map[string]ComponentExecutable `json:"variants,omitempty"`
}

type ComponentExecutable struct {
	SHA256                 string   `json:"sha256"`
	Size                   int64    `json:"size"`
	Recipe                 string   `json:"recipe"`
	AcceptedOriginalSHA256 []string `json:"acceptedOriginalSha256,omitempty"`
}

type Selection struct {
	Patch bool `json:"patch"`
	Live  bool `json:"live"`
}

type GameState struct {
	Game              string `json:"game"`
	ExecutableSHA256  string `json:"executableSha256"`
	ExecutableKnown   bool   `json:"executableKnown"`
	ExecutableMissing bool   `json:"executableMissing"`
	Patch             bool   `json:"patch"`
	Live              bool   `json:"live"`
	TeamsInstalled    int    `json:"teamsInstalled"`
	TeamsTotal        int    `json:"teamsTotal"`
}

const (
	statusCurrent  = "current"
	statusOutdated = "outdated"
	statusAbsent   = "absent"
)

func componentStatus(m Manifest, s GameState) (string, string) {
	full, _ := executableEntry(m)
	patchCurrent := map[string]bool{full.SHA256: true}
	liveCurrent := map[string]bool{full.SHA256: true}
	if c := m.Components; c != nil {
		if target, ok := c.Executables[componentPatch]; ok {
			patchCurrent[target.SHA256] = true
		}
		if target, ok := c.Executables[componentLive]; ok {
			liveCurrent[target.SHA256] = true
		}
	}
	live := statusAbsent
	if s.Live {
		live = statusOutdated
		if liveCurrent[s.ExecutableSHA256] {
			live = statusCurrent
		}
	}
	patch := statusAbsent
	if s.Patch || s.TeamsInstalled > 0 {
		patch = statusOutdated
		if patchCurrent[s.ExecutableSHA256] && s.TeamsTotal > 0 && s.TeamsInstalled == s.TeamsTotal {
			patch = statusCurrent
		}
	}
	return patch, live
}

func contains(values []string, wanted string) bool {
	for _, value := range values {
		if value == wanted {
			return true
		}
	}
	return false
}

func executableEntry(m Manifest) (ManifestFile, bool) {
	for _, f := range m.Files {
		if f.Path == gameExecutablePath {
			return f, true
		}
	}
	return ManifestFile{}, false
}

func detectState(m Manifest, gamePath string) (GameState, error) {
	game, _, err := validGame(gamePath)
	if err != nil {
		return GameState{}, err
	}
	state := GameState{Game: game}
	full, hasExecutable := executableEntry(m)
	if hasExecutable {
		hash, e := sha(filepath.Join(game, gameExecutablePath))
		if e != nil {
			state.ExecutableMissing = true
		} else {
			state.ExecutableSHA256 = hash
			known := hash == full.SHA256 || contains(full.AcceptedOriginalSHA256, hash)
			if c := m.Components; c != nil {
				for _, target := range c.Executables {
					if hash == target.SHA256 || contains(target.AcceptedOriginalSHA256, hash) {
						known = true
					}
				}
				state.Live = contains(c.LiveExecutableSHA256, hash)
				liveOnly := hash == c.Executables[componentLive].SHA256 || contains(c.LiveOnlyExecutableSHA256, hash)
				state.Patch = known && hash != c.OriginalExecutableSHA256 && !liveOnly
			} else {
				state.Patch = hash == full.SHA256
			}
			state.ExecutableKnown = known
		}
	}
	for _, f := range m.Files {
		if f.Path == gameExecutablePath || isCrestFile(f) {
			continue
		}
		state.TeamsTotal++
		if hash, e := sha(filepath.Join(game, filepath.FromSlash(f.Path))); e == nil && hash == f.SHA256 {
			state.TeamsInstalled++
		}
	}
	return state, nil
}

func componentKey(patch, live bool) string {
	switch {
	case patch && live:
		return componentPatchLive
	case patch:
		return componentPatch
	case live:
		return componentLive
	}
	return ""
}

func componentManifest(m Manifest, selection Selection, state GameState) (Manifest, error) {
	if !selection.Patch && !selection.Live {
		return Manifest{}, errors.New("selecione ao menos um item para instalar")
	}
	out := m
	out.Files = nil
	full, hasExecutable := executableEntry(m)
	for _, f := range m.Files {
		if f.Path != gameExecutablePath && !isCrestFile(f) && selection.Patch {
			out.Files = append(out.Files, f)
		}
	}
	if hasExecutable {
		key := componentKey(selection.Patch || state.Patch, selection.Live || state.Live)
		switch {
		case key == componentPatchLive || m.Components == nil:
			out.Files = append(out.Files, full)
		default:
			target, ok := m.Components.Executables[key]
			if !ok || !validHash.MatchString(target.SHA256) || !recipeName.MatchString(target.Recipe) {
				return Manifest{}, fmt.Errorf("componente %s indisponível neste pacote", key)
			}
			accepted := []string{}
			for _, hash := range append(append([]string{}, target.AcceptedOriginalSHA256...), full.AcceptedOriginalSHA256...) {
				if hash != target.SHA256 && !contains(accepted, hash) {
					accepted = append(accepted, hash)
				}
			}
			if len(accepted) > 64 {
				accepted = accepted[:64]
			}
			via := full
			via.Recipe = ""
			via.Via = nil
			out.Files = append(out.Files, ManifestFile{
				Operation: "replace", Path: gameExecutablePath, Size: target.Size, SHA256: target.SHA256,
				AcceptedOriginalSHA256: accepted, Recipe: target.Recipe, Via: &via,
			})
		}
	}
	if len(out.Files) == 0 {
		return Manifest{}, errors.New("nada a instalar para a seleção escolhida")
	}
	return out, nil
}

func stageComponents(root, gamePath string, selection Selection) (Plan, error) {
	m := bundledManifestFromFS()
	if len(m.Files) == 0 {
		return Plan{}, errors.New("nenhuma versão do patch foi carregada; conecte-se à internet e tente de novo")
	}
	state, err := detectState(m, gamePath)
	if err != nil {
		return Plan{}, err
	}
	cm, err := componentManifest(m, selection, state)
	if err != nil {
		return Plan{}, err
	}
	staged, err := os.MkdirTemp(root, "selection-")
	if err != nil {
		return Plan{}, err
	}
	body, err := json.MarshalIndent(cm, "", "  ")
	if err != nil {
		return Plan{}, err
	}
	if err = os.WriteFile(filepath.Join(staged, "manifest.json"), body, 0600); err != nil {
		return Plan{}, err
	}
	if err = preparePayloadManifest(currentPayload(), cm, state.Game, staged); err != nil {
		return Plan{}, err
	}
	return inspect(staged, state.Game)
}

func bundledManifestFromFS() Manifest {
	var m Manifest
	body, err := fs.ReadFile(currentPayload(), "bundled_release/manifest.json")
	if err == nil {
		_ = json.Unmarshal(body, &m)
	}
	return m
}

func sameFolder(a, b string) bool {
	ca, ea := canonical(a)
	cb, eb := canonical(b)
	if ea != nil || eb != nil {
		return strings.EqualFold(filepath.Clean(a), filepath.Clean(b))
	}
	return strings.EqualFold(ca, cb)
}
