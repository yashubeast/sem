package prefix

import (
	"github.com/bwmarrin/discordgo"
	"sem/commands/helpers"
)

// Repeats your message.
// TODO: make this delete the initiator message before repeating.
func Say(s *discordgo.Session, m *discordgo.MessageCreate, args []string) {
	if len(args) == 0 { return }

	s.ChannelMessageSend(m.ChannelID, helpers.JoinArgs(args))
}
