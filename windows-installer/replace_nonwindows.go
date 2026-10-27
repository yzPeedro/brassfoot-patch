//go:build !windows

package main

import "os"

// Source is created beside destination, so POSIX rename replaces atomically
// on the same filesystem. The shared engine checks hashes before and after.
func swapReplace(source, destination string) error { return os.Rename(source, destination) }
