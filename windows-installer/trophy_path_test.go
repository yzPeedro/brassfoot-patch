package main

import "testing"

func TestTrophyPath(t *testing.T) {
	cases := map[string]bool{
		"trofeus/tr_supercopa_ING.png": true,
		"trofeus/tr_nacional_ALE.png":  true,
		"trofeus/../bf22-23.exe":       false,
		"trofeus/supercopa.png":        false,
		"trofeus/tr_copa_TUR.jpg":      false,
		"trofeus/sub/tr_copa_TUR.png":  false,
		"Trofeus/tr_copa_TUR.png":      false,
	}
	for path, want := range cases {
		if got := trophyName.MatchString(path); got != want {
			t.Errorf("%s: esperado %v, obtido %v", path, want, got)
		}
	}
	if fileComponent(ManifestFile{Path: "trofeus/tr_copa_ALE.png"}) != componentRosters {
		t.Errorf("troféu deveria pertencer ao componente de elencos")
	}
}
