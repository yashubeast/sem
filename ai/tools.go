package ai

import (
	"encoding/json"
	"fmt"
	"time"
)

// TODO: organize tools to be like commands in default.go so its cleaner to look at the collection of tools.

var Tools = []Tool{
	{
		Type: "function",
		Function: ToolFunction{
			Name:        "get_time",
			Description: "Get the current time in a specific timezone. Use IANA timezone names such as Europe/Amsterdam, Europe/Berlin, or Asia/Kolkata.",
			Parameters: map[string]any{
				"type": "object",
				"properties": map[string]any{
					"timezone": map[string]any{
						"type":        "string",
						"description": "IANA timezone name",
					},
				},
				"required": []string{"timezone"},
			},
		},
	},
}

func executeTool(call ToolCall) (string, error) {
	switch call.Function.Name {

	case "get_time":
		var args struct {
			Timezone string `json:"timezone"`
		}

		if err := json.Unmarshal(
			[]byte(call.Function.Arguments),
			&args,
		); err != nil {
			return "", err
		}

		loc, err := time.LoadLocation(args.Timezone)
		if err != nil {
			return "", fmt.Errorf("invalid timezone: %s", args.Timezone)
		}

		return time.Now().
			In(loc).
			Format("Monday, January 2, 2006 at 3:04 PM MST"), nil

	default:
		return "", fmt.Errorf("unknown tool: %s", call.Function.Name)
	}
}
