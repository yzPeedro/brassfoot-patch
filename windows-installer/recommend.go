package main

import (
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type Recommendation struct {
	Careers    []string        `json:"careers"`
	Components map[string]bool `json:"components"`
}

func recommendFor(game string) Recommendation {
	return Recommendation{
		Careers: savedCareers(game),
		Components: map[string]bool{
			componentRosters: true,
			componentSeason:  true,
			componentLive:    true,
			componentCrests:  true,
		},
	}
}

func savedCareers(game string) []string {
	entries, err := os.ReadDir(filepath.Join(game, "sav"))
	if err != nil {
		return []string{}
	}
	careers := []string{}
	for _, entry := range entries {
		name := entry.Name()
		if entry.Type().IsRegular() && strings.EqualFold(filepath.Ext(name), ".s22") {
			careers = append(careers, strings.TrimSuffix(name, filepath.Ext(name)))
		}
	}
	sort.Strings(careers)
	return careers
}
