//go:build !windows

package main

import "os"

// Portable analogue used only by automated tests on non-Windows systems.
func swapReplace(source, destination string) error { return os.Rename(source, destination) }
