// ABOUTME: No-op debug logging implementation for production builds without -tags debug
// ABOUTME: Ensures zero overhead when debug logging is not enabled at compile time

//go:build !debug
// +build !debug

// Package debug provides conditional debug logging that is only compiled
// when the -tags debug build flag is used. This file provides no-op
// implementations when debug mode is not enabled.
package debug

import "log"

// Printf is a no-op when debug mode is not enabled
func Printf(component, format string, args ...interface{}) {
	// No-op
}

// Println is a no-op when debug mode is not enabled
func Println(component string, args ...interface{}) {
	// No-op
}

// SetLogger is a no-op when debug mode is not enabled
func SetLogger(l *log.Logger) {
	// No-op
}
