package ai

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
)

// TODO: throw this in default.go
const endpoint = "https://api.groq.com/openai/v1/chat/completions"

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
	Function ToolFunction `json:"function"`
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

type response struct {
	Choices []struct {
		Message Message `json:"message"`
	} `json:"choices"`

	Error any `json:"error,omitempty"`
}

func call(messages []Message) (Message, error) {
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
	req.Header.Set("Authorization", "Bearer "+os.Getenv("API_KEY_AI"))

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
		return Message{}, fmt.Errorf("AI provider returned HTTP %d: %v", resp.StatusCode, result.Error)
	}

	if len(result.Choices) == 0 {
		return Message{}, fmt.Errorf("AI provider returned no choices")
	}

	return result.Choices[0].Message, nil
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
