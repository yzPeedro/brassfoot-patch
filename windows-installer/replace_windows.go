//go:build windows

package main

import (
	"fmt"
	"syscall"
	"unsafe"
)

const (
	moveFileReplaceExisting = 0x1
	moveFileWriteThrough    = 0x8
)

var moveFileExW = syscall.NewLazyDLL("kernel32.dll").NewProc("MoveFileExW")

// Go 1.23's os.Rename on Windows uses MoveFileW, which cannot replace a
// destination already present. This native Windows API replaces an EXISTING
// .ban atomically on the same volume. A checked backup is created first.
func swapReplace(source, destination string) error {
	from, err := syscall.UTF16PtrFromString(source)
	if err != nil {
		return err
	}
	to, err := syscall.UTF16PtrFromString(destination)
	if err != nil {
		return err
	}
	ok, _, callErr := moveFileExW.Call(
		uintptr(unsafe.Pointer(from)), uintptr(unsafe.Pointer(to)),
		uintptr(moveFileReplaceExisting|moveFileWriteThrough),
	)
	if ok == 0 {
		return fmt.Errorf("Windows não permitiu substituir o arquivo existente %s: %w", destination, callErr)
	}
	return nil
}
