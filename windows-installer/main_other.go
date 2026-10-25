//go:build !windows

package main

import "fmt"

func main() { fmt.Println("This graphical installer runs on Windows. Unit tests can run on Linux.") }
