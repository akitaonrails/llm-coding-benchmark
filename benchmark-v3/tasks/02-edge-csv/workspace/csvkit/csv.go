// Package csvkit parses a single CSV record (RFC 4180 subset, no embedded
// newlines) into its fields.
package csvkit

import (
	"errors"
	"strings"
)

// ErrMalformed is returned for any input that violates the record grammar
// (see TASK.md): a bare quote in an unquoted field, text after a closing quote,
// or an unterminated quoted field.
var ErrMalformed = errors.New("malformed CSV record")

// ParseRecord splits one CSV record into fields.
//
// NAIVE STARTER IMPLEMENTATION — it only splits on commas and does not handle
// quoting, escaped quotes, or malformed input at all. Make it correct per the
// rules in TASK.md.
func ParseRecord(line string) ([]string, error) {
	return strings.Split(line, ","), nil
}
