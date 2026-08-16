package config

import (
	"slices"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sync"
)

type ConfigFile struct {
	AnimeNotify AnimeNotifyConfig `json:"anime_notify"`
}

type AnimeNotifyConfig struct {
	Channels []string `json:"channels"`
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
			AnimeNotify: AnimeNotifyConfig{Channels: []string{}},
		}
		return saveConfigUnlocked(path)
	} else if err != nil {
		return err
	}

	return json.Unmarshal(data, &AppConfig)
}

// Thread-safe function to add a channel and persist changes.
func AddAnimeNotifyChannel(channelID string) error {
	configLock.Lock()
	defer configLock.Unlock()

	// Prevent duplicates
	if slices.Contains(AppConfig.AnimeNotify.Channels, channelID) {
			return nil
		}

	AppConfig.AnimeNotify.Channels = append(AppConfig.AnimeNotify.Channels, channelID)

	path, err := GetConfigFilePath()
	if err != nil {
		return err
	}

	return saveConfigUnlocked(path)
}

// Thread-safe function to remove a channel and persist changes.
func RemoveAnimeNotifyChannel(channelID string) error {
	configLock.Lock()
	defer configLock.Unlock()

	idx := slices.Index(AppConfig.AnimeNotify.Channels, channelID)
	if idx == -1 {
		return nil // not present, nothing to do
	}

	AppConfig.AnimeNotify.Channels = slices.Delete(AppConfig.AnimeNotify.Channels, idx, idx+1)

	path, err := GetConfigFilePath()
	if err != nil {
		return err
	}

	return saveConfigUnlocked(path)
}

// Returns a copy of the currently configured anime-notify channels.
func GetAnimeNotifyChannels() []string {
	configLock.RLock()
	defer configLock.RUnlock()
	return slices.Clone(AppConfig.AnimeNotify.Channels)
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
