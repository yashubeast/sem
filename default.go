package main

import "semplate/bot"

// Do Not Edit.

// This is a reference template for creating a bot,
// to create your own bot, copy this file into my_bot.go,
// and change:
// - the first line from "default" to "my_bot"
// - whatever you want to configure.

// Build your custom bot via passing "-tags my_bot" in the build command.

func init() {
	Bot, _ = bot.New(bot.Config{
		Prefix: ",",
		Commands: map[string]bot.CommandTemplate{
			// The entire list of available commands.
			// Define commands like this:
			// "string": function
			// "string" means the command name (users will send ",string" to execute the command).
			// and the function is what will be executed.
			"ping": bot.Ping,
			"say": bot.Say,
		},
	})
}
