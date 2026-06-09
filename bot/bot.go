package bot

import (
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/bwmarrin/discordgo"
)

// Command template.
type CommandTemplate func(s *discordgo.Session, m *discordgo.MessageCreate, args []string)

// Config for unique bots.
type Config struct {
	Prefix string
	Commands map[string]CommandTemplate
	OnReady func(s *discordgo.Session, event *discordgo.Ready)
}

// Unique bot with its own commands, discord-bot-application and others.
type Bot struct {
	config Config
	session *discordgo.Session
}

// Creates a new Bot frmo the given config and Discord Token.
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

	b.session.Identify.Intents |= discordgo.IntentsGuilds
	b.session.Identify.Intents |= discordgo.IntentsGuildMessages

	if err := b.session.Open(); err != nil { return fmt.Errorf("Failed to open session: %w", err) }
	defer b.session.Close()

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