package commands

import (
	"fmt"
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

	// Delete the ephemeral acknowledgement.
	s.InteractionResponseDelete(i.Interaction)

	s.ChannelMessageSend(i.ChannelID, opts[0].StringValue())
}
