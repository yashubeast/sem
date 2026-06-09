package commands

import (
	"fmt"
	"math/rand"
	"time"

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
