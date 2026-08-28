package ai

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"
)

// TODO: throw this in default.go
const endpoint = "https://api.groq.com/openai/v1/chat/completions"

var (
	apiKeys     []string
	apiKeyMu    sync.Mutex
	apiKeyIndex int
)
func InitApiKeysAi() {
	apiKeys = []string{
		os.Getenv("API_KEY_AI_1"),
		os.Getenv("API_KEY_AI_2"),
		os.Getenv("API_KEY_AI_3"),
		os.Getenv("API_KEY_AI_4"),
		os.Getenv("API_KEY_AI_5"),
	}
}
// returns API keys in round-robin order
func nextAPIKey() (string, int) {
	apiKeyMu.Lock()
	defer apiKeyMu.Unlock()

	for range apiKeys {
		index := apiKeyIndex
		key := apiKeys[apiKeyIndex]
		apiKeyIndex = (apiKeyIndex + 1) % len(apiKeys)

		if key != "" {
			return key, index + 1
		}
	}

	return "", 0
}

type Message struct {
	Role       string     `json:"role"`
	Content    string     `json:"content,omitempty"`
	ToolCalls  []ToolCall `json:"tool_calls,omitempty"`
	ToolCallID string     `json:"tool_call_id,omitempty"`
}

type ToolCall struct {
	ID       string `json:"id"`
	Type     string `json:"type"`
	Function struct {
		Name      string `json:"name"`
		Arguments string `json:"arguments"`
	} `json:"function"`
}

type Tool struct {
	Type     string       `json:"type"`
	Function *ToolFunction `json:"function,omitempty"`
}

type ToolFunction struct {
	Name        string         `json:"name"`
	Description string         `json:"description"`
	Parameters  map[string]any `json:"parameters"`
}

type request struct {
	Model               string    `json:"model"`
	Messages            []Message `json:"messages"`
	Tools               []Tool    `json:"tools,omitempty"`
	Temperature         float64   `json:"temperature"`
	MaxCompletionTokens int       `json:"max_completion_tokens"`
	ToolChoice          string    `json:"tool_choice,omitempty"`
}

type Usage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

type response struct {
	Choices []struct {
		Message Message `json:"message"`
	} `json:"choices"`

	Usage Usage `json:"usage"`
	Error any   `json:"error,omitempty"`
}

func call(messages []Message) (Message, error) {
	start := time.Now()

	body := request{
		// TODO: throw model in default.go
		Model:               "openai/gpt-oss-120b",
		Messages:            messages,
		Tools:               Tools,
		Temperature:         0.7,
		MaxCompletionTokens: 512,
		ToolChoice:          "auto",
	}

	data, err := json.Marshal(body)
	if err != nil {
		return Message{}, err
	}

	req, err := http.NewRequest("POST", endpoint, bytes.NewReader(data))
	if err != nil {
		return Message{}, err
	}

	req.Header.Set("Content-Type", "application/json")
	// get the next API key
	apiKey, apiKeyNumber := nextAPIKey()
	if apiKey == "" {
		return Message{}, fmt.Errorf("no API keys provided")
	}
	req.Header.Set("Authorization", "Bearer "+apiKey)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return Message{}, err
	}
	defer resp.Body.Close()

	var result response

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return Message{}, err
	}

	if resp.StatusCode >= 400 {
		slog.Error("AI API call failed",
			"status", resp.StatusCode,
			"error", result.Error,
		)

		// distinguish rate-limit errors from other API errors
		if resp.StatusCode == http.StatusTooManyRequests {
			return Message{}, fmt.Errorf("AI tokens exceeded")
		}

		return Message{}, fmt.Errorf(
			"AI provider returned HTTP %d: %v",
			resp.StatusCode,
			result.Error,
		)
	}

	if len(result.Choices) == 0 {
		return Message{}, fmt.Errorf("AI provider returned no choices")
	}

	message := result.Choices[0].Message

	slog.Debug("AI raw response",
		"content", message.Content,
		"content_len", len(message.Content),
		"tool_calls", message.ToolCalls,
	)

	slog.Info("AI API call",
    "api_key_number", apiKeyNumber,
		"model", body.Model,
		"duration", time.Since(start),
		"prompt_tokens", result.Usage.PromptTokens,
		"completion_tokens", result.Usage.CompletionTokens,
		"total_tokens", result.Usage.TotalTokens,
		"empty_response", strings.TrimSpace(message.Content) == "",
	)

	return message, nil
}

func Ask(systemPrompt string, prompt string) (string, error) {
	messages := []Message{
		{
			Role: "system",
			Content: systemPrompt,
		},
		{
			Role:    "user",
			Content: prompt,
		},
	}

	for {
		message, err := call(messages)
		if err != nil {
			return "", err
		}

		// No tool call = final response.
		if len(message.ToolCalls) == 0 {
			return message.Content, nil
		}

		// Add assistant's tool-call message.
		messages = append(messages, message)

		// Execute tools.
		for _, toolCall := range message.ToolCalls {

			if toolCall.Type != "function" {
				continue
			}

			result, err := executeTool(toolCall)
			if err != nil {
				return "", err
			}

			messages = append(messages, Message{
				Role:       "tool",
				ToolCallID: toolCall.ID,
				Content:    result,
			})
		}
	}
}
