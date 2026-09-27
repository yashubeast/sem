package slash

import (
	"math/rand"
	"sem/bot"

	"github.com/bwmarrin/discordgo"
)

var CoinflipEntry = bot.SlashCommandEntry{
	Definition: &discordgo.ApplicationCommand{
		Name:        "coinflip",
		Description: "Flips a coin.",
	},
	Handler: Coinflip,
}

// Outputs Heads/Tails.
func Coinflip(s *discordgo.Session, i *discordgo.InteractionCreate) {
	result := "Heads"
	if rand.Intn(2) == 1 { result = "Tails" }
	s.InteractionRespond(i.Interaction, &discordgo.InteractionResponse{
		Type: discordgo.InteractionResponseChannelMessageWithSource,
		Data: &discordgo.InteractionResponseData{
			Content: "🪙 " + result,
		},
	})
}
