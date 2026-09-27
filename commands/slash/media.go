package slash

import (
	"fmt"
	"net/url"
	"sem/bot"
	"strings"

	"github.com/bwmarrin/discordgo"
)

var MediaEntry = bot.SlashCommandEntry{
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
	Handler: Media,
}

// Transforms supported media URLs to support embed for platforms like discord.
func Media(s *discordgo.Session, i *discordgo.InteractionCreate) {
	opts := i.ApplicationCommandData().Options
	if len(opts) == 0 {
		return
	}

	rawURL := opts[0].StringValue()

	// Parse the URL
	parsedURL, err := url.Parse(rawURL)
	if err != nil || parsedURL.Scheme == "" || parsedURL.Host == "" {
		s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
			Type: discordgo.InteractionResponseChannelMessageWithSource,
			Data: &discordgo.InteractionResponseData{
				Content: "Invalid URL provided.",
				Flags:   discordgo.MessageFlagsEphemeral,
			},
		})
		return
	}

	originalURL := parsedURL.String()

	// Replace instagram host variations with kkinstagram.com
	host := strings.ToLower(parsedURL.Host)
	if host == "instagram.com" || host == "www.instagram.com" {
		parsedURL.Host = "kkinstagram.com"
	}

	s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
		Type: discordgo.InteractionResponseChannelMessageWithSource,
		Data: &discordgo.InteractionResponseData{
			Content: fmt.Sprintf("[embeded](%s) [original](<%s>)", parsedURL.String(), originalURL),
		},
	})
}
