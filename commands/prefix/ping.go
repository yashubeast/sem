package prefix

import (
	"fmt"
	"time"

	"github.com/bwmarrin/discordgo"
)

// Outputs bot latency.
func Ping(s *discordgo.Session, m *discordgo.MessageCreate, args []string) {
	start := time.Now()
	msg, err := s.ChannelMessageSend(m.ChannelID, "pong")
	if err != nil { return }
	elapsed := time.Since(start).Milliseconds()
	s.ChannelMessageEdit(m.ChannelID, msg.ID, fmt.Sprintf("pong | %dms", elapsed))
}
