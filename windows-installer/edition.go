package main

import "strconv"

// Release builds read config/edition.json and inject these values with -X.
// Defaults keep a source checkout usable without running a code generator.
var productName = "Brasfoot Mega Patch"
var productVersion = "2026.4.1"
var patchYearText = "2026"
var sourceCommit = "development"

func patchYear() int {
	year, err := strconv.Atoi(patchYearText)
	if err != nil || year < 2000 || year > 9999 {
		panic("invalid PATCH_YEAR in build metadata")
	}
	return year
}
