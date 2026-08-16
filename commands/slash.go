package commands

import (
	"fmt"
	"math/rand"
	"time"
	"semplate/config"
	"log/slog"
	"strings"

	"github.com/bwmarrin/discordgo"
)

// Outputs ping.
func SlashPing(s *discordgo.Session, i *discordgo.InteractionCreate) {
	start := time.Now()
	s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
		Type: discordgo.InteractionResponseChannelMessageWithSource,
		Data: &discordgo.InteractionResponseData{
			Content: "pong",
		},
	})
	elapsed := time.Since(start).Milliseconds()
	content := fmt.Sprintf("pong | %dms", elapsed)
	s.InteractionResponseEdit(i.Interaction, &discordgo.WebhookEdit{
		Content: &content,
	})
}

// Repeats your message.
func SlashSay(s *discordgo.Session, i *discordgo.InteractionCreate) {
	opts := i.ApplicationCommandData().Options
	if len(opts) == 0 { return }

	// Acknowledge the interaction.
	s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
		Type: discordgo.InteractionResponseDeferredChannelMessageWithSource,
		Data: &discordgo.InteractionResponseData{
			Flags: discordgo.MessageFlagsEphemeral,
		},
	})
	// Send the message.
	s.ChannelMessageSend(i.ChannelID, opts[0].StringValue())
	// Delete the ephemeral acknowledgement.
	s.InteractionResponseDelete(i.Interaction)
}

// Outputs Heads/Tails.
func SlashCoinflip(s *discordgo.Session, i *discordgo.InteractionCreate) {
	result := "Heads"
	if rand.Intn(2) == 1 { result = "Tails" }
	s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
		Type: discordgo.InteractionResponseChannelMessageWithSource,
		Data: &discordgo.InteractionResponseData{
			Content: "🪙 " + result,
		},
	})
}

// Purges messages in a channel, optionally filtered to a specific user.
// TODO: fix not deleting messages out of session.
func SlashPurge(s *discordgo.Session, i *discordgo.InteractionCreate) {
	opts := i.ApplicationCommandData().Options
	amount := int(opts[0].IntValue())

	var filterUserID string
	if len(opts) > 1 { filterUserID = opts[1].UserValue(nil).ID }

	// Fetch messages (i think discord caps at 100 per request).
	if amount > 100 { amount = 100 }
	messages, err := s.ChannelMessages(i.ChannelID, amount, "", "", "")
	if err != nil {
		s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
			Type: discordgo.InteractionResponseChannelMessageWithSource,
			Data: &discordgo.InteractionResponseData{
				Content: "Failed to fetch messages.",
				Flags: discordgo.MessageFlagsEphemeral,
			},
		})
		return
	}

	// Filter by user if provided.
	var ids []string
	for _, m := range messages {
		if filterUserID == "" || m.Author.ID == filterUserID {
			ids = append(ids, m.ID)
		}
	}

	if len(ids) == 0 {
		s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
			Type: discordgo.InteractionResponseChannelMessageWithSource,
			Data: &discordgo.InteractionResponseData{
				Content: "No messages found to delete.",
				Flags: discordgo.MessageFlagsEphemeral,
			},
		})
		return
	}

	s.ChannelMessagesBulkDelete(i.ChannelID, ids)

	s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
		Type: discordgo.InteractionResponseChannelMessageWithSource,
		Data: &discordgo.InteractionResponseData{
			Content: fmt.Sprintf("🗑️ Deleted %d message(s).\n-# auto-deleting in 3s...", len(ids)),
			Flags: discordgo.MessageFlagsEphemeral,
		},
	})
	// NOTE: Not sure if this sleep is a concern.
	time.Sleep(3 * time.Second)
	s.InteractionResponseDelete(i.Interaction)
}

// Create a channel with a user.
func SlashConversation(s *discordgo.Session, i *discordgo.InteractionCreate) {
	s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
		Type: discordgo.InteractionResponseDeferredChannelMessageWithSource,
		Data: &discordgo.InteractionResponseData{
			Flags: discordgo.MessageFlagsEphemeral,
		},
	})

	guildID := i.GuildID
	opts := i.ApplicationCommandData().Options
	userId := opts[0].UserValue(nil).ID

	channel, err := s.GuildChannelCreateComplex(guildID, discordgo.GuildChannelCreateData{
		Name: "private-channel",
		Type: discordgo.ChannelTypeGuildText,
		PermissionOverwrites: []*discordgo.PermissionOverwrite{
			{
				// Deny @everyone.
				ID: guildID,
				Type: discordgo.PermissionOverwriteTypeRole,
				Deny: discordgo.PermissionViewChannel,
			},
			{
				// Allow target user.
				ID: userId,
				Type: discordgo.PermissionOverwriteTypeMember,
				Allow: discordgo.PermissionViewChannel,
			},
		},
	})
	if err != nil {
		s.FollowupMessageCreate(i.Interaction, true, &discordgo.WebhookParams{
			Content: "Failed to create channel.",
			Flags: discordgo.MessageFlagsEphemeral,
		})
	}

	s.FollowupMessageCreate(i.Interaction, true, &discordgo.WebhookParams{
		Content: "Created private-channel: <#" + channel.ID + ">",
		Flags: discordgo.MessageFlagsEphemeral,
	})
}

// Handles anime notification commands and subcommands.
func SlashAnimeNotify(s *discordgo.Session, i *discordgo.InteractionCreate) {
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
