package commands

import (
	"fmt"
	"time"

	"github.com/bwmarrin/discordgo"
)

// Outputs ping.
func Ping(s *discordgo.Session, m *discordgo.MessageCreate, args []string) {
	start := time.Now()
	msg, err := s.ChannelMessageSend(m.ChannelID, "pong")
	if err != nil { return }
	elapsed := time.Since(start).Milliseconds()
	s.ChannelMessageEdit(m.ChannelID, msg.ID, fmt.Sprintf("pong | %dms", elapsed))
}


// Repeats your message.
// TODO: make this delete the initiator message before repeating.
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
