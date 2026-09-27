package slash

import (
	"fmt"
	"log/slog"
	"sem/bot"
	"sem/config"
	"strings"

	"github.com/bwmarrin/discordgo"
)

var AnimeNotifyEntry = bot.SlashCommandEntry{
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
	Handler: AnimeNotify,
}

// Handles anime notification commands and subcommands.
func AnimeNotify(s *discordgo.Session, i *discordgo.InteractionCreate) {
	options := i.ApplicationCommandData().Options
	if len(options) == 0 {
		return
	}

	subcommand := options[0]
	switch subcommand.Name {
	case "add_channel":
		subOptions := subcommand.Options
		if len(subOptions) == 0 {
			return
		}

		channel := subOptions[0].ChannelValue(s)
		channelID := channel.ID

		// Save channel ID to config.
		if err := config.AddAnimeNotifyChannel(channelID); err != nil {
			slog.Error("Failed to save notification channel to config", "err", err)
			s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
				Type: discordgo.InteractionResponseChannelMessageWithSource,
				Data: &discordgo.InteractionResponseData{
					Content: "Failed to update configuration file.",
					Flags:   discordgo.MessageFlagsEphemeral,
				},
			})
			return
		}

		s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
			Type: discordgo.InteractionResponseChannelMessageWithSource,
			Data: &discordgo.InteractionResponseData{
				Content: fmt.Sprintf("Registered <#%s> for anime notifications.", channelID),
				Flags:   discordgo.MessageFlagsEphemeral,
			},
		})

	case "remove_channel":
		subOptions := subcommand.Options
		if len(subOptions) == 0 {
			return
		}

		channel := subOptions[0].ChannelValue(s)
		channelID := channel.ID

		if err := config.RemoveAnimeNotifyChannel(channelID); err != nil {
			slog.Error("Failed to remove notification channel from config", "err", err)
			s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
				Type: discordgo.InteractionResponseChannelMessageWithSource,
				Data: &discordgo.InteractionResponseData{
					Content: "Failed to update configuration file.",
					Flags:   discordgo.MessageFlagsEphemeral,
				},
			})
			return
		}

		s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
			Type: discordgo.InteractionResponseChannelMessageWithSource,
			Data: &discordgo.InteractionResponseData{
				Content: fmt.Sprintf("Removed <#%s> from anime notifications.", channelID),
				Flags:   discordgo.MessageFlagsEphemeral,
			},
		})

	case "whitelist_anime":
		subOptions := subcommand.Options
		if len(subOptions) < 2 {
			return
		}
		channel := subOptions[0].ChannelValue(s)
		pattern := subOptions[1].StringValue()

		if err := config.AddAnimeWhitelistPattern(channel.ID, pattern); err != nil {
			s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
				Type: discordgo.InteractionResponseChannelMessageWithSource,
				Data: &discordgo.InteractionResponseData{
					Content: fmt.Sprintf("Failed to add pattern: %s", err.Error()),
					Flags:   discordgo.MessageFlagsEphemeral,
				},
			})
			return
		}

		s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
			Type: discordgo.InteractionResponseChannelMessageWithSource,
			Data: &discordgo.InteractionResponseData{
				Content: fmt.Sprintf("Whitelisted `%s` for <#%s>.", pattern, channel.ID),
				Flags:   discordgo.MessageFlagsEphemeral,
			},
		})

	case "unwhitelist_anime":
		subOptions := subcommand.Options
		if len(subOptions) < 2 {
			return
		}
		channel := subOptions[0].ChannelValue(s)
		pattern := subOptions[1].StringValue()

		if err := config.RemoveAnimeWhitelistPattern(channel.ID, pattern); err != nil {
			slog.Error("Failed to remove whitelist pattern", "err", err)
			s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
				Type: discordgo.InteractionResponseChannelMessageWithSource,
				Data: &discordgo.InteractionResponseData{
					Content: "Failed to update configuration file.",
					Flags:   discordgo.MessageFlagsEphemeral,
				},
			})
			return
		}

		s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
			Type: discordgo.InteractionResponseChannelMessageWithSource,
			Data: &discordgo.InteractionResponseData{
				Content: fmt.Sprintf("Removed `%s` from <#%s>'s whitelist.", pattern, channel.ID),
				Flags:   discordgo.MessageFlagsEphemeral,
			},
		})

	case "list_whitelist":
		subOptions := subcommand.Options
		if len(subOptions) == 0 {
			return
		}
		channel := subOptions[0].ChannelValue(s)
		patterns := config.GetAnimeWhitelist(channel.ID)

		content := fmt.Sprintf("No whitelist patterns for <#%s> — all anime are notified there.", channel.ID)
		if len(patterns) > 0 {
			content = fmt.Sprintf("Whitelist patterns for <#%s>:\n- %s", channel.ID, strings.Join(patterns, "\n- "))
		}

		s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
			Type: discordgo.InteractionResponseChannelMessageWithSource,
			Data: &discordgo.InteractionResponseData{
				Content: content,
				Flags:   discordgo.MessageFlagsEphemeral,
			},
		})

	}
}
