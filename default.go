package main

import (
	"semplate/bot"
	"semplate/commands"
	"semplate/routines"

	"github.com/bwmarrin/discordgo"
)

var Bot *bot.Bot

func init() {
	Bot, _ = bot.New(bot.Config{
		Prefix: ",",
		OnReady: func(s *discordgo.Session, event *discordgo.Ready) {
			routines.StartAnimeNotify(s)
		},
		Commands: map[string]bot.CommandTemplate{
			"ping": commands.Ping,
			"say": commands.Say,
		},
		SlashCommands: map[string]bot.SlashCommandEntry{

			"ping": {
				Definition: &discordgo.ApplicationCommand{
					Name: "ping",
					Description: "Replies with pong.",
				},
				Handler: commands.SlashPing,
			},

			"say": {
				Definition: &discordgo.ApplicationCommand{
					Name: "say",
					Description: "Repeats your Message.",
					Options: []*discordgo.ApplicationCommandOption{
						{
							Type: discordgo.ApplicationCommandOptionString,
							Name: "message",
							Description: "What to repeat.",
							Required: true,
						},
					},
				},
				Handler: commands.SlashSay,
			},

			"coinflip": {
				Definition: &discordgo.ApplicationCommand{
					Name: "coinflip",
					Description: "Flips a coin.",
				},
				Handler: commands.SlashCoinflip,
			},

			"purge": {
				Definition: &discordgo.ApplicationCommand{
					Name: "purge",
					Description: "Deletes messages in current channel.",
					DefaultMemberPermissions: func() *int64 {
						p := int64(discordgo.PermissionManageMessages)
						return &p
					}(),
					Options: []*discordgo.ApplicationCommandOption{
						{
							Type: discordgo.ApplicationCommandOptionInteger,
							Name: "amount",
							Description: "Number of messages to delete (max 100).",
							Required: true,
							MinValue: func() *float64 { v := 1.0; return &v }(),
							MaxValue: 100,
						},
						{
							Type: discordgo.ApplicationCommandOptionUser,
							Name: "user",
							Description: "Only delete messages from this user.",
							Required: false,
						},
					},
				},
				Handler: commands.SlashPurge,
			},

			"conversation": {
				Definition: &discordgo.ApplicationCommand{
					Name: "conversation",
					Description: "Create a private-channel.",
					DefaultMemberPermissions: func() *int64 {
						p := int64(discordgo.PermissionAdministrator)
						return &p
					}(),
					Options: []*discordgo.ApplicationCommandOption{
						{
							Type: discordgo.ApplicationCommandOptionUser,
							Name: "user",
							Description: "Add this member to the private-channel.",
							Required: true,
						},
					},
				},
				Handler: commands.SlashConversation,
			},

		},
	})
}
