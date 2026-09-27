package main

import (
	_ "embed"
	"sem/bot"
	"sem/commands/prefix"
	"sem/commands/slash"
	"sem/routines"

	"github.com/bwmarrin/discordgo"
)

//go:embed systemPrompt.md
var systemPrompt string

var Bot *bot.Bot

func init() {
	Bot, _ = bot.New(bot.Config{

		Prefix: ",",
		OnReady: func(s *discordgo.Session, event *discordgo.Ready) {
			routines.StartAnimeNotify(s)
		},

		AI: bot.AIConfig{
			Enabled: true,
			ReplyToMentions: true,
			NamePatterns: []string{
				// TODO: fix this weird string bullshit, and instead just make it normal regex /.*sem.*/
				`(?i)\bsem\b`,
			},
			SystemPrompt: systemPrompt,
			ContextMessageCount: 10,
		},

		Commands: map[string]bot.CommandTemplate{
			"ping": prefix.Ping,
			"say": prefix.Say,
		},

		SlashCommands: map[string]bot.SlashCommandEntry{
			"coinflip": slash.CoinflipEntry,
			"purge": slash.PurgeEntry,
			"conversation": slash.ConversationEntry,
			"media": slash.MediaEntry,
			"anime_notify": slash.AnimeNotifyEntry,
		},

	})
}
