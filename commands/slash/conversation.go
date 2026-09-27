package slash

import (
	"sem/bot"

	"github.com/bwmarrin/discordgo"
)

var ConversationEntry = bot.SlashCommandEntry{
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
	Handler: Conversation,
}

// Create a channel with a user.
func Conversation(s *discordgo.Session, i *discordgo.InteractionCreate) {
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
