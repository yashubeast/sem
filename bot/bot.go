package bot

import (
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"regexp"
	"semplate/ai"
	"slices"
	"strings"
	"errors"
	"syscall"

	"github.com/bwmarrin/discordgo"
)

// Command template.
type CommandTemplate func(s *discordgo.Session, m *discordgo.MessageCreate, args []string)
// Slash Command template.
type SlashCommandTemplate func(s *discordgo.Session, i *discordgo.InteractionCreate)
type SlashCommandEntry struct { Definition *discordgo.ApplicationCommand; Handler SlashCommandTemplate }
// AI.
type AIConfig struct {
	Enabled             bool
	ReplyToMentions     bool
	NamePatterns        []string
	SystemPrompt        string
	ContextMessageCount int
}

// Config for unique bots.
type Config struct {
	Prefix string
	OnReady func(s *discordgo.Session, event *discordgo.Ready)
	Commands map[string]CommandTemplate
	SlashCommands map[string]SlashCommandEntry
	GuildID string // Optional: empty = global, set = guild-only (instant registration)
	AI AIConfig
}

// Unique bot with its own commands, discord-bot-application and others.
type Bot struct {
	config Config
	session *discordgo.Session
}

// Creates a new Bot from the given config.
func New(config Config) (*Bot, error) {
	return &Bot{ config: config }, nil
}

// Opens the bot session and blocks until an exit signal is received.
func (b *Bot) Run(token string) error {
	session, err := discordgo.New("Bot " + token)
	if err != nil { return fmt.Errorf("Failed to create session: %w", err) }
	b.session = session

	b.session.AddHandler(b.ready)
	b.session.AddHandler(b.messageCreate)
	b.session.AddHandler(b.interactionCreate)

	b.session.Identify.Intents |= discordgo.IntentsGuilds
	b.session.Identify.Intents |= discordgo.IntentsGuildMessages
	b.session.Identify.Intents |= discordgo.IntentsMessageContent

	if err := b.session.Open(); err != nil { return fmt.Errorf("Failed to open session: %w", err) }
	defer b.session.Close()

	// Register slash commands after opening session.
	b.registerSlashCommands()

	slog.Info("Bot is now running. Press Ctrl-c to exit.")
	sc := make(chan os.Signal, 1)
	signal.Notify(sc, syscall.SIGINT, syscall.SIGTERM, os.Interrupt)
	<-sc

	return nil
}

func (b *Bot) ready(s *discordgo.Session, event *discordgo.Ready) {
	slog.Info("Ready", "username", s.State.User.Username)
	if b.config.OnReady != nil {
		b.config.OnReady(s, event)
	}
}

func (b *Bot) messageCreate(s *discordgo.Session, m *discordgo.MessageCreate) {
	// Ignore messages from self.
	if m.Author.ID == s.State.User.ID { return }

	// Detect of bot is mentioned in a chat, or mentioned literally.
	if b.config.AI.Enabled && b.shouldAIReply(s, m) {
		b.handleAIMessage(s, m)
		return
	}

	prefix := b.config.Prefix
	if len(m.Content) <= len(prefix) || m.Content[:len(prefix)] != prefix { return }

	// Parse command and args from the message.
	// e.g. "!ping foo bar" -> command = "ping", args = [ "foo", "bar" ]
	body := m.Content[len(prefix):]
	command, args := parseCommand(body)

	// Handle the command if exists.
	handler, ok := b.config.Commands[command]
	if !ok { return }
	handler(s, m, args)
}

func (b *Bot) registerSlashCommands() {
	for _, entry := range b.config.SlashCommands {
		_, err := b.session.ApplicationCommandCreate(
			b.session.State.User.ID,
			b.config.GuildID,
			entry.Definition,
		)
		if err != nil { slog.Error("Failed to register slash command", "name", entry.Definition.Name, "err", err) }
	}
}

func (b *Bot) interactionCreate(s *discordgo.Session, i *discordgo.InteractionCreate) {
    if i.Type != discordgo.InteractionApplicationCommand { return }

    name := i.ApplicationCommandData().Name
    entry, ok := b.config.SlashCommands[name]
    if !ok { return }
    entry.Handler(s, i)
}

func (b *Bot) shouldAIReply(s *discordgo.Session, m *discordgo.MessageCreate) bool {
	// Explicit Discord mention.
	if b.config.AI.ReplyToMentions {
		for _, user := range m.Mentions {
			if user.ID == s.State.User.ID {
				return true
			}
		}
	}

	// Literal name/regex patterns.
	for _, pattern := range b.config.AI.NamePatterns {
		re, err := regexp.Compile(pattern)
		if err != nil {
			slog.Error(
				"Invalid AI name regex",
				"pattern", pattern,
				"err", err,
			)
			continue
		}

		if re.MatchString(m.Content) {
			return true
		}
	}

	return false
}

func (b *Bot) handleAIMessage(s *discordgo.Session, m *discordgo.MessageCreate) {

	// Fetch previous messages + the triggering message.
	limit := b.config.AI.ContextMessageCount 
	messages, err := s.ChannelMessages(
		m.ChannelID,
		limit,
		m.ID,
		"",
		"",
	)
	if err != nil {
		slog.Error("Failed to fetch AI context", "err", err)
		return
	}

	// Discord returns newest -> oldest, so reverse them.
	slices.Reverse(messages)
	context := make([]string, 0, len(messages)+1)

	// Previous messages = context.
	for _, msg := range messages {
		if strings.TrimSpace(msg.Content) == "" {
			continue
		}

		context = append(context, fmt.Sprintf(
			"%s: %s",
			msg.Author.Username,
			msg.Content,
		))
	}

	// THIS is the actual message that triggered the AI call.
	context = append(context, fmt.Sprintf(
		"%s: %s",
		m.Author.Username,
		m.Content,
	))

	contextString := strings.Join(context, "\n")
	
	slog.Debug("AI context",
		"channel", m.ChannelID,
		"messages", len(context),
		"context", "\n" + contextString,
	)

	response, err := ai.Ask(
		b.config.AI.SystemPrompt,
		contextString,
	)
	if err != nil {
		slog.Error("AI request failed", "err", err)

		// all API keys were rate limited
		if errors.Is(err, ai.ErrAllTokensExceeded) {
			_, sendErr := s.ChannelMessageSend(
				m.ChannelID,
				"im down",
			)

			if sendErr != nil {
				slog.Error("Failed to send token limit message in discord", "err", sendErr)
			}
		}

		return
	}

	if strings.TrimSpace(response) == "" {
		return
	}

	_, err = s.ChannelMessageSend(m.ChannelID, response)
	if err != nil {
		slog.Error("Failed to send AI response", "err", err)
	}
}
