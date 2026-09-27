package main

// TODO: add fallback alerts for "no-permission to do x action"

import (
	"log/slog"
	"os"
	"sem/ai"
	"sem/config"

	"github.com/joho/godotenv"
)

func main() {

	// Init Env.
	if err := godotenv.Load(); err != nil {
		slog.Error("Failed to init .env", "err", err)
	}

	// Init slog.
	logLevel := slog.LevelInfo
	if os.Getenv("SEM_DEBUG") == "true" { logLevel = slog.LevelDebug }
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: logLevel,
	}))
	slog.SetDefault(logger)

	// Fetch discord bot token.
	token := os.Getenv("TOKEN")
	if token == "" {
		slog.Error("TOKEN is not set")
		os.Exit(1)
	}

	// Fetch api keys for AI.
	ai.InitApiKeysAi()

	// Load file configuration.
	if err := config.LoadConfig(); err != nil {
		slog.Error("Failed to load config.json", "err", err)
	}

	// Run Bot.
	if err := Bot.Run(token); err != nil { panic(err) }
}
