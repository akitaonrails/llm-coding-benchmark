// Package csvkit — reference solution.
package csvkit

import (
	"errors"
	"strings"
)

var ErrMalformed = errors.New("malformed CSV record")

// ParseRecord splits one CSV record into fields (RFC 4180 subset).
func ParseRecord(line string) ([]string, error) {
	fields := []string{}
	r := []rune(line)
	i := 0
	n := len(r)
	for {
		// Parse one field starting at i.
		if i < n && r[i] == '"' {
			// Quoted field.
			var sb strings.Builder
			i++ // consume opening quote
			closed := false
			for i < n {
				c := r[i]
				if c == '"' {
					if i+1 < n && r[i+1] == '"' {
						sb.WriteRune('"')
						i += 2
						continue
					}
					// closing quote
					i++
					closed = true
					break
				}
				sb.WriteRune(c)
				i++
			}
			if !closed {
				return nil, ErrMalformed // unterminated quoted field
			}
			// After closing quote, must be comma or EOL.
			if i < n && r[i] != ',' {
				return nil, ErrMalformed // text after closing quote
			}
			fields = append(fields, sb.String())
		} else {
			// Unquoted field: up to next comma or EOL; no bare quotes allowed.
			start := i
			for i < n && r[i] != ',' {
				if r[i] == '"' {
					return nil, ErrMalformed // bare quote in unquoted field
				}
				i++
			}
			fields = append(fields, string(r[start:i]))
		}
		if i >= n {
			break
		}
		// r[i] == ',' : consume separator and continue with the next field.
		i++
	}
	return fields, nil
}
