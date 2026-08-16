package routines

// TODO: fetch specific animes only
// TODO: a command to whitelist notifying animes (admin only).
// TODO: server specific notifying, and whitelisting.
// TODO: allow user specific notifying in dms (a single user can make the bot notify them in dms)
// TODO: store data in json/sql

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"time"
	"semplate/config"
	"regexp"

	"github.com/bwmarrin/discordgo"
)

const (
	anilistEndpoint = "https://graphql.anilist.co"
)

// Query for all episodes that aired in a given time window.
// airingAt_greater / airingAt_lesser are Unix timestamps.
// Using Page so burst situations are handlable (e.g. several shows airing at once).
const query = `
query ($from: Int, $to: Int, $page: Int) {
  Page(page: $page, perPage: 50) {
    pageInfo { hasNextPage }
    airingSchedules(
      airingAt_greater: $from
      airingAt_lesser:  $to
      sort: [TIME]
    ) {
      episode
      airingAt
      media {
				episodes
        title { romaji english }
        siteUrl
        coverImage { medium }
      }
    }
  }
}
`

type anilistRequest struct {
	Query     string         `json:"query"`
	Variables map[string]any `json:"variables"`
}

type anilistResponse struct {
	Data struct {
		Page struct {
			PageInfo struct {
				HasNextPage bool `json:"hasNextPage"`
			} `json:"pageInfo"`
			AiringSchedules []struct {
				Episode  int   `json:"episode"`
				AiringAt int64 `json:"airingAt"`
				Media    struct {
					Episodes int `json:"episodes"`
					Title struct {
						Romaji  string `json:"romaji"`
						English string `json:"english"`
					} `json:"title"`
					SiteUrl    string `json:"siteUrl"`
					CoverImage struct {
						Medium string `json:"medium"`
					} `json:"coverImage"`
				} `json:"media"`
			} `json:"airingSchedules"`
		} `json:"Page"`
	} `json:"data"`
}

// Upper bound of the previous window.
// On first tick it covers "the last minute before bot started".
var lastTick = time.Now().Add(-1 * time.Minute)

// Launches the background scheduler, call this from OnReady.
func StartAnimeNotify(s *discordgo.Session) {
	slog.Info("AnimeNotify started", "interval", "1m")
	go func() {
		tick(s)
		for range time.NewTicker(1 * time.Minute).C {
			tick(s)
		}
	}()
}

// Fetches every episode that aired since the last tick and notifies for each.
func tick(s *discordgo.Session) {
	now := time.Now()
	from := lastTick.Unix()
	to := now.Unix()
	lastTick = now

	episodes, err := fetchAiredBetween(from, to)
	if err != nil {
		slog.Error("Failed to fetch airing schedule", "err", err)
		return
	}

	slog.Info("Tick", "window_from", from, "window_to", to, "episodes_found", len(episodes))

	for _, ep := range episodes {
		displayTitle := ep.Media.Title.English
		if displayTitle == "" {
			displayTitle = ep.Media.Title.Romaji
		}
		notify(s, displayTitle, ep.Media.Title.English, ep.Media.Title.Romaji, ep.Episode, ep.TotalEpisodes, ep.AiringAt, ep.Media.SiteUrl, ep.Media.CoverImage.Medium)
	}
}

type episode struct {
	Episode  int
	TotalEpisodes int
	AiringAt int64
	Media    struct {
		Title      struct{ Romaji, English string }
		SiteUrl    string
		CoverImage struct{ Medium string }
	}
}

// Pages through all episodes that aired in [from, to].
func fetchAiredBetween(from, to int64) ([]episode, error) {
	var all []episode
	page := 1

	for {
		body, err := json.Marshal(anilistRequest{
			Query: query,
			Variables: map[string]any{
				"from": from,
				"to":   to,
				"page": page,
			},
		})
		if err != nil {
			return nil, err
		}

		resp, err := http.Post(anilistEndpoint, "application/json", bytes.NewReader(body))
		if err != nil {
			return nil, err
		}
		defer resp.Body.Close()

		var result anilistResponse
		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			return nil, err
		}

		for _, s := range result.Data.Page.AiringSchedules {
			all = append(all, episode{
				Episode:  s.Episode,
				TotalEpisodes: s.Media.Episodes,
				AiringAt: s.AiringAt,
				Media: struct {
					Title      struct{ Romaji, English string }
					SiteUrl    string
					CoverImage struct{ Medium string }
				}{
					Title:      struct{ Romaji, English string }{s.Media.Title.Romaji, s.Media.Title.English},
					SiteUrl:    s.Media.SiteUrl,
					CoverImage: struct{ Medium string }{s.Media.CoverImage.Medium},
				},
			})
		}

		if !result.Data.Page.PageInfo.HasNextPage {
			break
		}
		page++
	}

	return all, nil
}

// Sends a Discord embed to every registered notification channel whose whitelist matches.
// titleEnglish/titleRomaji are checked against each channel's patterns; displayTitle is just what's shown.
func notify(s *discordgo.Session, displayTitle, titleEnglish, titleRomaji string, episode int, totalEpisodes int, airedAt int64, url, thumbnail string) {
	airedTime := time.Unix(airedAt, 0)

	var episodeStringPrefix string = fmt.Sprintf("**Episode %d** just aired!\n", episode)
	var episodeString string = ""
	if totalEpisodes > 0 {
		episodeString = fmt.Sprintf("*%d/%d*", episode, totalEpisodes)
	}

	embed := &discordgo.MessageEmbed{
		Title:       fmt.Sprintf("New Episode — %s", displayTitle),
		Description: episodeStringPrefix + episodeString,
		URL:         url,
		Color:       0x02A9FF,
		Thumbnail:   &discordgo.MessageEmbedThumbnail{URL: thumbnail},
		Footer: &discordgo.MessageEmbedFooter{
			Text: fmt.Sprintf("Aired %s", airedTime.Format("Jan 2, 2006 at 15:04 UTC")),
		},
	}

	channels := config.GetAnimeNotifyChannels()
	for channelID, patterns := range channels {
		if !animeMatchesWhitelist(patterns, titleEnglish, titleRomaji) {
			continue
		}
		if _, err := s.ChannelMessageSendEmbed(channelID, embed); err != nil {
			slog.Error("Failed to send notification", "channel", channelID, "title", displayTitle, "episode", episode, "err", err)
		} else {
			slog.Info("Notified", "channel", channelID, "title", displayTitle, "episode", episode)
		}
	}
}

// Returns true if any title matches any pattern (case-insensitive substring/regex).
// An empty pattern list means "match everything".
func animeMatchesWhitelist(patterns []string, titles ...string) bool {
	if len(patterns) == 0 {
		return true
	}
	for _, pattern := range patterns {
		re, err := regexp.Compile("(?i)" + pattern)
		if err != nil {
			slog.Error("Invalid whitelist regex, skipping", "pattern", pattern, "err", err)
			continue
		}
		for _, title := range titles {
			if title != "" && re.MatchString(title) {
				return true
			}
		}
	}
	return false
}
