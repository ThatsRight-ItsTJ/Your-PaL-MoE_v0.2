// Package profiling provides utilities for CPU and memory profiling in the Go-LLMs project.
package profiling

// ABOUTME: Integration profiling utilities for end-to-end performance analysis
// ABOUTME: Captures detailed metrics across entire LLM operation lifecycle

import (
	"context"
)

// ProfiledOperation represents a specific operation that can be profiled
type ProfiledOperation string

// Common profiled operations
const (
	OpSchemaValidation     ProfiledOperation = "schema_validation"
	OpSchemaJsonMarshaling ProfiledOperation = "schema_json_marshaling"
	OpPromptProcessing     ProfiledOperation = "prompt_processing"
	OpStructuredExtraction ProfiledOperation = "structured_extraction"
	OpPoolAllocation       ProfiledOperation = "pool_allocation"
	OpPoolReturn           ProfiledOperation = "pool_return"
)

// ProfileStructuredOp profiles a structured output operation and returns its result
// This is a convenience function that creates a profiler for structured operations
func ProfileStructuredOp(ctx context.Context, op ProfiledOperation, fn func(context.Context) (interface{}, error)) (interface{}, error) {
	profiler := GetGlobalProfiler()
	if !profiler.IsEnabled() {
		return fn(ctx)
	}

	return profiler.ProfileOperation(ctx, string(op), fn)
}

// ProfileSchemaOp profiles a schema validation or marshaling operation
func ProfileSchemaOp(ctx context.Context, op ProfiledOperation, fn func(context.Context) (interface{}, error)) (interface{}, error) {
	profiler := GetGlobalProfiler()
	if !profiler.IsEnabled() {
		return fn(ctx)
	}

	return profiler.ProfileOperation(ctx, string(op), fn)
}

// ProfilePoolOp profiles a memory pool operation (allocation or return)
func ProfilePoolOp(ctx context.Context, op ProfiledOperation, fn func(context.Context) (interface{}, error)) (interface{}, error) {
	profiler := GetGlobalProfiler()
	if !profiler.IsEnabled() {
		return fn(ctx)
	}

	return profiler.ProfileOperation(ctx, string(op), fn)
}

// EnableProfilingForComponent enables profiling for a specific component
// It returns a function that can be called to disable profiling
func EnableProfilingForComponent(componentName string) func() {
	profiler := NewProfiler(componentName)
	profiler.Enable()

	getLogger().Printf("Profiling enabled for component: %s", componentName)
	getLogger().Printf("Profiles will be written to: %s", profileDir)

	return func() {
		profiler.Disable()
		getLogger().Printf("Profiling disabled for component: %s", componentName)
	}
}

// GetProfileDir returns the current profile output directory
func GetProfileDir() string {
	return profileDir
}
