package main

// TODO: add fallback alerts for "no-permission to do x action"

import (
	"log/slog"
	"os"
	"semplate/ai"
	"semplate/config"

	"github.com/joho/godotenv"
)

func main() {

	// Init slog.
	logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
		// Level: slog.LevelDebug,
	}))
	slog.SetDefault(logger)

	// Init Env.
	if err := godotenv.Load(); err != nil {
		slog.Error("Failed to init .env", "err", err)
	}

	// fetch discord bot token
	token := os.Getenv("TOKEN")
	if token == "" {
		slog.Error("TOKEN is not set")
		os.Exit(1)
	}

	// fetch api keys for ai
	ai.InitApiKeysAi()

	// Load file configuration.
	if err := config.LoadConfig(); err != nil {
		slog.Error("Failed to load config.json", "err", err)
	}

	// Run Bot.
	if err := Bot.Run(token); err != nil { panic(err) }
}
