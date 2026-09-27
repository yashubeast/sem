package slash

import (
	"fmt"
	"sem/bot"
	"time"

	"github.com/bwmarrin/discordgo"
)

var PurgeEntry = bot.SlashCommandEntry{
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
	Handler: Purge,
}

// Purges messages in a channel, optionally filtered to a specific user.
// TODO: fix not deleting messages out of session.
func Purge(s *discordgo.Session, i *discordgo.InteractionCreate) {
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
