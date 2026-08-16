package main

// TODO: add fallback alerts for "no-permission to do x action"

import (
	"log/slog"
	"os"
	"semplate/config"

	"github.com/joho/godotenv"
)

func main() {
	// Init Env.
	godotenv.Load()
	token := os.Getenv("TOKEN")

	// Load file configuration.
	if err := config.LoadConfig(); err != nil {
		slog.Error("Failed to load config.json", "err", err)
	}

	// Run Bot.
	if err := Bot.Run(token); err != nil { panic(err) }
}
