package bot

import "github.com/bwmarrin/discordgo"

// Replies with "pong".
func Ping(s *discordgo.Session, m *discordgo.MessageCreate, args []string) {
	s.ChannelMessageSend(m.ChannelID, "pong")
}

//
func Say(s *discordgo.Session, m *discordgo.MessageCreate, args []string) {
	if len(args) == 0 { return }

	s.ChannelMessageSend(m.ChannelID, joinArgs(args))
}

func joinArgs(args []string) string {
	out := ""
	for i, a := range args {
		if i > 0 { out += " " }
		out += a
	}
	return out
}