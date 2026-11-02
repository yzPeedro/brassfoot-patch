//go:build !windows

package main

func installedMemory() uint64 {
	return 0
}
