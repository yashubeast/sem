package main

// TODO: add fallback alerts for "no-permission to do x action"

import (
	"os"

	"github.com/joho/godotenv"
)

func main() {
	// Init Env.
	godotenv.Load()
	token := os.Getenv("TOKEN")

	// Run Bot.
	if err := Bot.Run(token); err != nil { panic(err) }
}
