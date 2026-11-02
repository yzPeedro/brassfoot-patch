//go:build windows

package main

import (
	"syscall"
	"unsafe"
)

var (
	installedMemoryProc = syscall.NewLazyDLL("kernel32.dll").NewProc("GetPhysicallyInstalledSystemMemory")
	memoryStatusProc    = syscall.NewLazyDLL("kernel32.dll").NewProc("GlobalMemoryStatusEx")
)

type memoryStatus struct {
	Length, MemoryLoad                        uint32
	TotalPhys, AvailPhys, TotalPageFile       uint64
	AvailPageFile, TotalVirtual, AvailVirtual uint64
	AvailExtendedVirtual                      uint64
}

func installedMemory() uint64 {
	var kilobytes uint64
	if installedMemoryProc.Find() == nil {
		if ok, _, _ := installedMemoryProc.Call(uintptr(unsafe.Pointer(&kilobytes))); ok != 0 && kilobytes > 0 {
			return kilobytes * 1024
		}
	}
	status := memoryStatus{Length: uint32(unsafe.Sizeof(memoryStatus{}))}
	if memoryStatusProc.Find() == nil {
		if ok, _, _ := memoryStatusProc.Call(uintptr(unsafe.Pointer(&status))); ok != 0 {
			return status.TotalPhys
		}
	}
	return 0
}
