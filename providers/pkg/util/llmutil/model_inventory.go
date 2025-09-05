package llmutil

// ABOUTME: Manages available model inventory across all providers
// ABOUTME: Provides discovery and caching of model capabilities and metadata

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/lexlapax/go-llms/pkg/util/llmutil/modelinfo" // Corrected import
	"github.com/lexlapax/go-llms/pkg/util/llmutil/modelinfo/cache"
	"github.com/lexlapax/go-llms/pkg/util/llmutil/modelinfo/domain"
)

const (
	defaultCacheDirPerm = 0755
	defaultCacheFile    = "model_inventory.json"
	defaultMaxCacheAge  = 24 * time.Hour
	defaultSubDir       = "go-llms"
)

// GetAvailableModelsOptions specifies options for the GetAvailableModels function.
type GetAvailableModelsOptions struct {
	// UseCache enables or disables the caching mechanism.
	// Defaults to true.
	UseCache bool

	// CachePath specifies the full file path for the cache file.
	// If empty, a default path under the user's cache directory is used
	// (e.g., ~/.cache/go-llms/model_inventory.json on Linux).
	CachePath string

	// MaxCacheAge defines the maximum age for a cache entry to be considered valid.
	// If zero when passed in opts, a default of 24 hours is used.
	MaxCacheAge time.Duration
}

// GetAvailableModels fetches an aggregated inventory of available LLM models
// from various providers. It supports caching to reduce redundant data fetching.
//
// Parameters:
//
//	opts: An optional *GetAvailableModelsOptions struct to customize behavior.
//	      If nil, default options are used (caching enabled, default path and age).
//
// Returns:
//
//	A *domain.ModelInventory containing the aggregated list of models and metadata.
//	An error if fetching or processing fails and cache is unavailable or invalid.
//
// Caching:
//   - If opts.UseCache is true (default behavior if opts is nil or opts.UseCache is not explicitly false),
//     the function first attempts to load a valid (non-expired) inventory from the cache path.
//   - The cache path is determined by opts.CachePath if provided. Otherwise, a default path
//     is constructed, typically under os.UserCacheDir()/go-llms/model_inventory.json.
//     If os.UserCacheDir() fails, it falls back to a local ".cache/go-llms/model_inventory.json".
//   - The maximum cache age is determined by opts.MaxCacheAge if provided and non-zero.
//     Otherwise, a default of 24 hours (defaultMaxCacheAge) is used.
//   - If fresh data is fetched successfully and caching is enabled, the new inventory
//     is saved to the cache.
func GetAvailableModels(opts *GetAvailableModelsOptions) (*domain.ModelInventory, error) {
	// 1. Handle Options and Defaults
	options := GetAvailableModelsOptions{
		UseCache:    true, // Default to using cache
		MaxCacheAge: defaultMaxCacheAge,
	}

	if opts != nil {
		// Apply the UseCache setting from opts (default is true in options)
		// Note: bool's zero value is false, so if opts is passed and UseCache is not
		// explicitly set to true, it will disable caching
		options.UseCache = opts.UseCache

		if opts.CachePath != "" {
			options.CachePath = opts.CachePath
		}
		if opts.MaxCacheAge != 0 {
			options.MaxCacheAge = opts.MaxCacheAge
		}
	}

	if options.CachePath == "" {
		userCacheDir, err := os.UserCacheDir()
		if err != nil {
			// Fallback strategy: try to create a local .cache directory
			cwd, CwdErr := os.Getwd()
			if CwdErr != nil {
				// Very unlikely, but as a last resort, use a relative path from where the binary might be.
				// This might not be writable.
				userCacheDir = filepath.Join(".", ".cache")
			} else {
				userCacheDir = filepath.Join(cwd, ".cache")
			}
		}
		options.CachePath = filepath.Join(userCacheDir, defaultSubDir, defaultCacheFile)
	}

	// 2. Caching Logic
	if options.UseCache {
		loadedInventory, err := cache.LoadInventory(options.CachePath)
		if err == nil && loadedInventory != nil { // Cache hit
			if cache.IsCacheValid(loadedInventory, options.MaxCacheAge) {
				return &loadedInventory.Inventory, nil
			}
			// Cache is expired or invalid, proceed to fetch fresh data
		}
		// For any error (including non-existent files), we proceed to fetch fresh data
		// If os.ErrNotExist, that's fine, we just need to fetch.
	}

	// 3. Data Fetching
	modelInfoService := modelinfo.NewModelInfoServiceFunc() // Use the func variable
	freshInventoryData, err := modelInfoService.AggregateModels()
	if err != nil {
		// AggregateModels returns partial results even when some providers fail
		// Only return nil if we have no data at all
		if freshInventoryData == nil || len(freshInventoryData.Models) == 0 {
			return nil, fmt.Errorf("failed to aggregate model data: %w", err)
		}
		// Continue with partial results
	}

	// If fetching was successful and caching is enabled, save the fresh data.
	if options.UseCache && freshInventoryData != nil {
		// Ensure the directory exists
		cacheDir := filepath.Dir(options.CachePath)
		// Create cache directory - ignore errors as cache is best-effort
		_ = os.MkdirAll(cacheDir, defaultCacheDirPerm)

		// Create the cache data
		cachedDataToSave := domain.CachedModelInventory{
			Inventory: *freshInventoryData,
			FetchedAt: time.Now(),
		}

		// Save the inventory - ignore errors as cache is best-effort
		_ = cache.SaveInventory(&cachedDataToSave, options.CachePath)
	}

	return freshInventoryData, nil
}
