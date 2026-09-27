package helpers

import "strings"

func JoinArgs(args []string) string {
	var out strings.Builder
	for i, a := range args {
		if i > 0 { out.WriteString(" ") }
		out.WriteString(a)
	}
	return out.String()
}
