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
		AI: bot.AIConfig{
			Enabled: true,
			ReplyToMentions: true,
			NamePatterns: []string{
				// TODO: fix this weird string bullshit
				`(?i)\bsem\b`,
			},
			SystemPrompt: `
			you are a concise discord bot.
			keep responses short, usually one sentence.
			do not explain things unless asked to.
			use tools whenever they can provide accurate information.
			`,
		},
		Commands: map[string]bot.CommandTemplate{
			"ping": commands.Ping,
			"say": commands.Say,
		},
		SlashCommands: map[string]bot.SlashCommandEntry{
			"ping": SlashPingEntry,
			"say": SlashSayEntry,
			"coinflip": SlashCoinflipEntry,
			"purge": SlashPurgeEntry,
			"conversation": SlashConversationEntry,
			"media": SlashMediaEntry,
			"anime_notify": SlashAnimeNotifyEntry,
		},
	})
}

var SlashPingEntry = bot.SlashCommandEntry{
	Definition: &discordgo.ApplicationCommand{
		Name:        "ping",
		Description: "Replies with pong.",
	},
	Handler: commands.SlashPing,
}

var SlashSayEntry = bot.SlashCommandEntry{
	Definition: &discordgo.ApplicationCommand{
		Name:        "say",
		Description: "Repeats your Message.",
		Options: []*discordgo.ApplicationCommandOption{
			{
				Type:        discordgo.ApplicationCommandOptionString,
				Name:        "message",
				Description: "What to repeat.",
				Required:    true,
			},
		},
	},
	Handler: commands.SlashSay,
}

var SlashCoinflipEntry = bot.SlashCommandEntry{
	Definition: &discordgo.ApplicationCommand{
		Name:        "coinflip",
		Description: "Flips a coin.",
	},
	Handler: commands.SlashCoinflip,
}

var SlashPurgeEntry = bot.SlashCommandEntry{
	Definition: &discordgo.ApplicationCommand{
		Name:        "purge",
		Description: "Deletes messages in current channel.",
		DefaultMemberPermissions: func() *int64 {
			p := int64(discordgo.PermissionManageMessages)
			return &p
		}(),
		Options: []*discordgo.ApplicationCommandOption{
			{
				Type:        discordgo.ApplicationCommandOptionInteger,
				Name:        "amount",
				Description: "Number of messages to delete (max 100).",
				Required:    true,
				MinValue:    func() *float64 { v := 1.0; return &v }(),
				MaxValue:    100,
			},
			{
				Type:        discordgo.ApplicationCommandOptionUser,
				Name:        "user",
				Description: "Only delete messages from this user.",
				Required:    false,
			},
		},
	},
	Handler: commands.SlashPurge,
}

var SlashConversationEntry = bot.SlashCommandEntry{
	Definition: &discordgo.ApplicationCommand{
		Name:        "conversation",
		Description: "Create a private-channel.",
		DefaultMemberPermissions: func() *int64 {
			p := int64(discordgo.PermissionAdministrator)
			return &p
		}(),
		Options: []*discordgo.ApplicationCommandOption{
			{
				Type:        discordgo.ApplicationCommandOptionUser,
				Name:        "user",
				Description: "Add this member to the private-channel.",
				Required:    true,
			},
		},
	},
	Handler: commands.SlashConversation,
}

var SlashMediaEntry = bot.SlashCommandEntry{
	Definition: &discordgo.ApplicationCommand{
		Name:        "media",
		Description: "Convert links to include embeds. Supported: instagram",
		Options: []*discordgo.ApplicationCommandOption{
			{
				Type:        discordgo.ApplicationCommandOptionString,
				Name:        "url",
				Description: "The url duh",
				Required:    true,
			},
		},
	},
	Handler: commands.SlashMedia,
}

var SlashAnimeNotifyEntry = bot.SlashCommandEntry{
	Definition: &discordgo.ApplicationCommand{
		Name:        "anime_notify",
		Description: "Manage anime notification settings.",
		Options: []*discordgo.ApplicationCommandOption{
			{
				Type:        discordgo.ApplicationCommandOptionSubCommand,
				Name:        "add_channel",
				Description: "Set a channel for anime notifications.",
				Options: []*discordgo.ApplicationCommandOption{
					{
						Type:         discordgo.ApplicationCommandOptionChannel,
						Name:         "channel",
						Description:  "The channel to send notifications in.",
						Required:     true,
						ChannelTypes: []discordgo.ChannelType{discordgo.ChannelTypeGuildText},
					},
				},
			},
			{
				Type:        discordgo.ApplicationCommandOptionSubCommand,
				Name:        "remove_channel",
				Description: "Remove a channel from anime notifications.",
				Options: []*discordgo.ApplicationCommandOption{
					{
						Type:         discordgo.ApplicationCommandOptionChannel,
						Name:         "channel",
						Description:  "The channel to stop sending notifications in.",
						Required:     true,
						ChannelTypes: []discordgo.ChannelType{discordgo.ChannelTypeGuildText},
					},
				},
			},
			{
				Type:        discordgo.ApplicationCommandOptionSubCommand,
				Name:        "whitelist_anime",
				Description: "Only notify a channel for anime matching this pattern.",
				Options: []*discordgo.ApplicationCommandOption{
					{
						Type:         discordgo.ApplicationCommandOptionChannel,
						Name:         "channel",
						Description:  "The channel to whitelist for.",
						Required:     true,
						ChannelTypes: []discordgo.ChannelType{discordgo.ChannelTypeGuildText},
					},
					{
						Type:        discordgo.ApplicationCommandOptionString,
						Name:        "pattern",
						Description: "Text/regex to match titles against, e.g. \"one piece\" or \"dying day\".",
						Required:    true,
					},
				},
			},
			{
				Type:        discordgo.ApplicationCommandOptionSubCommand,
				Name:        "unwhitelist_anime",
				Description: "Remove a whitelist pattern from a channel.",
				Options: []*discordgo.ApplicationCommandOption{
					{
						Type:         discordgo.ApplicationCommandOptionChannel,
						Name:         "channel",
						Description:  "The channel to remove the pattern from.",
						Required:     true,
						ChannelTypes: []discordgo.ChannelType{discordgo.ChannelTypeGuildText},
					},
					{
						Type:        discordgo.ApplicationCommandOptionString,
						Name:        "pattern",
						Description: "The exact pattern string to remove.",
						Required:    true,
					},
				},
			},
			{
				Type:        discordgo.ApplicationCommandOptionSubCommand,
				Name:        "list_whitelist",
				Description: "List whitelist patterns for a channel.",
				Options: []*discordgo.ApplicationCommandOption{
					{
						Type:         discordgo.ApplicationCommandOptionChannel,
						Name:         "channel",
						Description:  "The channel to inspect.",
						Required:     true,
						ChannelTypes: []discordgo.ChannelType{discordgo.ChannelTypeGuildText},
					},
				},
			},
		},
	},
	Handler: commands.SlashAnimeNotify,
}
