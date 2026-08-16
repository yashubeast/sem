package config

import (
	"slices"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"regexp"
	"sync"
)

type ConfigFile struct {
	AnimeNotify AnimeNotifyConfig `json:"anime_notify"`
}

type AnimeNotifyConfig struct {
	// Channels maps a channel ID to a list of regex patterns (case-insensitive).
	// An empty pattern list means "notify for everything" (no filter).
	Channels map[string][]string `json:"channels"`
}

var (
	configLock sync.RWMutex
	AppConfig  ConfigFile
)

// Returns the path to config.json inside the ./data directory.
func GetConfigFilePath() (string, error) {
	dir := "data"
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", err
	}
	return filepath.Join(dir, "config.json"), nil
}

// Loads the configuration file into memory. Creates a default file if missing.
func LoadConfig() error {
	configLock.Lock()
	defer configLock.Unlock()

	path, err := GetConfigFilePath()
	if err != nil {
		return err
	}

	data, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		AppConfig = ConfigFile{
			AnimeNotify: AnimeNotifyConfig{Channels: map[string][]string{}},
		}
		return saveConfigUnlocked(path)
	} else if err != nil {
		return err
	}

	if err := json.Unmarshal(data, &AppConfig); err != nil {
		return err
	}
	if AppConfig.AnimeNotify.Channels == nil {
		AppConfig.AnimeNotify.Channels = map[string][]string{}
	}
	return nil
}

// Registers a channel for anime notifications (no filter by default).
func AddAnimeNotifyChannel(channelID string) error {
	configLock.Lock()
	defer configLock.Unlock()

	if _, ok := AppConfig.AnimeNotify.Channels[channelID]; ok {
		return nil // already registered
	}
	AppConfig.AnimeNotify.Channels[channelID] = []string{}

	path, err := GetConfigFilePath()
	if err != nil {
		return err
	}
	return saveConfigUnlocked(path)
}

// Removes a channel from anime notifications entirely (including its whitelist).
func RemoveAnimeNotifyChannel(channelID string) error {
	configLock.Lock()
	defer configLock.Unlock()

	if _, ok := AppConfig.AnimeNotify.Channels[channelID]; !ok {
		return nil
	}
	delete(AppConfig.AnimeNotify.Channels, channelID)

	path, err := GetConfigFilePath()
	if err != nil {
		return err
	}
	return saveConfigUnlocked(path)
}

// Adds a whitelist regex pattern to a channel, auto-registering the channel if needed.
// Returns an error if the pattern doesn't compile as a regex.
func AddAnimeWhitelistPattern(channelID, pattern string) error {
	if _, err := regexp.Compile("(?i)" + pattern); err != nil {
		return errors.New("invalid pattern: " + err.Error())
	}

	configLock.Lock()
	defer configLock.Unlock()

	patterns := AppConfig.AnimeNotify.Channels[channelID]
	if slices.Contains(patterns, pattern) {
			return nil // already whitelisted
		}
	AppConfig.AnimeNotify.Channels[channelID] = append(patterns, pattern)

	path, err := GetConfigFilePath()
	if err != nil {
		return err
	}
	return saveConfigUnlocked(path)
}

// Removes a whitelist pattern from a channel.
func RemoveAnimeWhitelistPattern(channelID, pattern string) error {
	configLock.Lock()
	defer configLock.Unlock()

	patterns, ok := AppConfig.AnimeNotify.Channels[channelID]
	if !ok {
		return nil
	}

	idx := -1
	for i, p := range patterns {
		if p == pattern {
			idx = i
			break
		}
	}
	if idx == -1 {
		return nil
	}
	AppConfig.AnimeNotify.Channels[channelID] = append(patterns[:idx], patterns[idx+1:]...)

	path, err := GetConfigFilePath()
	if err != nil {
		return err
	}
	return saveConfigUnlocked(path)
}

// Returns a snapshot of channelID -> whitelist patterns.
func GetAnimeNotifyChannels() map[string][]string {
	configLock.RLock()
	defer configLock.RUnlock()

	out := make(map[string][]string, len(AppConfig.AnimeNotify.Channels))
	for k, v := range AppConfig.AnimeNotify.Channels {
		out[k] = append([]string{}, v...)
	}
	return out
}

// Returns the whitelist patterns for a single channel.
func GetAnimeWhitelist(channelID string) []string {
	configLock.RLock()
	defer configLock.RUnlock()
	return append([]string{}, AppConfig.AnimeNotify.Channels[channelID]...)
}

// Atomically writes config to disk using a temporary file.
func saveConfigUnlocked(path string) error {
	data, err := json.MarshalIndent(AppConfig, "", "  ")
	if err != nil {
		return err
	}

	tmpFile := path + ".tmp"
	if err := os.WriteFile(tmpFile, data, 0644); err != nil {
		return err
	}

	return os.Rename(tmpFile, path)
}
