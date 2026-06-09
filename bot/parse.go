package bot

import (
	"strings"
)

// Splits a raw message body (after prefix is stripped) into
// a command name and its arguments.
// e.g. "ping foo bar" -> ("ping", ["foo", "bar"])
func parseCommand(body string) (string, []string) {
	parts := strings.Fields(body)
	if len(parts) == 0 { return "", nil }
	return strings.ToLower(parts[0]), parts[1:]
}