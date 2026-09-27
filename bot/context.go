package bot

import (
	"encoding/json"
	"fmt"
	"slices"
	"strings"

	"github.com/bwmarrin/discordgo"
)

// NOTE: currently if a message is replying to another message that is outside ContextMessageCount
// we add the replied message to the aiContext.Messages, without caring about the chronological order
// for example this is how aiContext.Messages would look like, with a ContextMessageCount value 5
// { msg 1 }
// { msg 2 }
// { msg 3 }
// { msg 4 }
// { msg 5 }
// { msg 7 } // this is the message that isn't in the ContextMessageCount scope
// { msg 6, ReplyTo: 7 }
// so in conclusion, it just appends the replied message above the parent message
// the only worry it uproots is breaking the flow of conversation in chronology :/
// cba to fix this right now so i'll just mention this here, also can't really think of a structure to use to separate replied messages from the main conversation
// maybe add a second aiContext.Messages[] that is specifically for messages that are relevant but not in the scope of ContextMessageCount

// aiContext is the root object sent to the AI as the
// payload. See systemPrompt.md for the schema the model is
// expected to understand.
type aiContext struct {
	Server   string   `json:"server"`
	Channel  string   `json:"channel"`
	Topic    string   `json:"topic,omitempty"`
	Messages []ctxMsg `json:"messages"`
}

// ctxMsg is a single Discord message used in the AI context.
// The last entry in aiContext.Messages is always the message that triggered the AI call.
type ctxMsg struct {
	ID      int    `json:"id"`
	User    string `json:"user,omitempty"`
	Display string `json:"display,omitempty"`
	Bot     bool   `json:"bot,omitempty"`
	Self    bool   `json:"self,omitempty"`
	// ReplyTo is the local id of the message this one replies to, if any.
	// If the replied-to message falls outside ContextMessageCount, it is
	// injected into aiContext.Messages using Discord's referenced_message (sent for free on reply-type messages).
	// It's only left unset if Discord shits itself and couldn't fetch the parent (e.g. it was deleted).
	ReplyTo int    `json:"reply_to,omitempty"`
	Text    string `json:"text"`
}

// displayName returns the best available user's name for a message
// 1. their server nickname if set
// 2. display name (if it differs from their username)
// 3. User is already the best available name and they have no overlaying user/nick/display name
func displayName(user *discordgo.User, member *discordgo.Member) string {
	if member != nil && member.Nick != "" {
		return member.Nick
	}
	if user.GlobalName != "" && user.GlobalName != user.Username {
		return user.GlobalName
	}
	return ""
}

// buildAIContext fetches recent channel history and serializes it, along
// with the triggering message m, into the JSON payload passed to ai.Ask.
func (b *Bot) buildAIContext(s *discordgo.Session, m *discordgo.MessageCreate) (string, error) {
	limit := b.config.AI.ContextMessageCount

	history, err := s.ChannelMessages(m.ChannelID, limit, m.ID, "", "")
	if err != nil {
		return "", fmt.Errorf("failed to fetch channel history: %w", err)
	}
	// Discord returns newest -> oldest, so reverse to chronological order.
	slices.Reverse(history)

	channel, err := s.Channel(m.ChannelID)
	if err != nil {
		return "", fmt.Errorf("failed to fetch channel: %w", err)
	}
	guild, err := s.Guild(m.GuildID)
	if err != nil {
		return "", fmt.Errorf("failed to fetch guild: %w", err)
	}

	ctx := aiContext{
		Server:  guild.Name,
		Channel: channel.Name,
		Topic:   channel.Topic,
	}

	// Maps a real Discord message ID -> the small local id assigned to it,
	// so "reply_to" can reference earlier messages cheaply and use this instead of 18-digit ids.
	idMap := make(map[string]int, len(history)+1)
	nextID := 1

	// addMsg appends a message to the context and returns the local id it was assigned (0 if skipped as empty).
	// refMsg is Discord's referenced_message for this message,
	// if it's a reply - used to recursively inject the parent when it isn't already in idMap.
	var addMsg func(discordID string, author *discordgo.User, member *discordgo.Member, content string, ref *discordgo.MessageReference, refMsg *discordgo.Message, force bool) int
	addMsg = func(discordID string, author *discordgo.User, member *discordgo.Member, content string, ref *discordgo.MessageReference, refMsg *discordgo.Message, force bool) int {
		if !force && strings.TrimSpace(content) == "" {
			return 0
		}

		local := nextID
		nextID++
		idMap[discordID] = local

		cm := ctxMsg{ID: local, Text: content}

		if s.State.User != nil && author.ID == s.State.User.ID {
			cm.Self = true
		} else {
			cm.User = author.Username
			cm.Bot = author.Bot
			cm.Display = displayName(author, member)
		}

		if ref != nil {
			if localRef, ok := idMap[ref.MessageID]; ok {
				cm.ReplyTo = localRef
			} else if refMsg != nil {
				// Parent isn't in idMap because it's outside our fetched window.
				// Discord sends the replied-to message on the reply itself (no extra API call needed)
				// inject it as its own context entry, otherwise it silently drops reply_to.
				parentLocal := addMsg(
					refMsg.ID,
					refMsg.Author,
					refMsg.Member,
					refMsg.Content,
					refMsg.MessageReference,
					refMsg.ReferencedMessage,
					true,
				)
				if parentLocal != 0 {
					cm.ReplyTo = parentLocal
				}
			}
			// If refMsg is also nil, Discord couldn't fetch the parent itself (deleted message fetch it)
			// nothing much we can do without a s.ChannelMessage(...) fetch,
			// so reply_to is left unset.
		}

		ctx.Messages = append(ctx.Messages, cm)
		return local
	}

	for _, msg := range history {
		addMsg(msg.ID, msg.Author, msg.Member, msg.Content, msg.MessageReference, msg.ReferencedMessage, false)
	}
	// The message that triggered this call is always included, and always last.
	addMsg(m.ID, m.Author, m.Member, m.Content, m.MessageReference, m.ReferencedMessage, true)

	data, err := json.Marshal(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to marshal AI context: %w", err)
	}

	return string(data), nil
}
