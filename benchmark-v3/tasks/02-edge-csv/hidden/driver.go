// Hidden grader driver for task 02. Compiled together with the candidate
// csvkit package in a temp module by harness.py. NEVER shipped to the model.
package main

import (
	"encoding/json"
	"fmt"
	"reflect"

	"v3task/csvkit"
)

type tcase struct {
	name    string
	tag     string
	input   string
	want    []string
	wantErr bool
}

type result struct {
	Name   string `json:"name"`
	Tag    string `json:"tag"`
	Pass   bool   `json:"pass"`
	Detail string `json:"detail"`
}

func main() {
	cases := []tcase{
		// base
		{"simple", "base", "a,b,c", []string{"a", "b", "c"}, false},
		{"empty_unquoted_middle", "base", "a,,c", []string{"a", "", "c"}, false},
		{"trailing_empty", "base", "a,b,", []string{"a", "b", ""}, false},
		{"empty_string", "base", "", []string{""}, false},
		{"single_field", "base", "hello", []string{"hello"}, false},
		// edge: quoting
		{"quoted_comma", "edge", `a,"b,c",d`, []string{"a", "b,c", "d"}, false},
		{"escaped_quote", "edge", `a,"b""c",d`, []string{"a", `b"c`, "d"}, false},
		{"empty_quoted_first", "edge", `"",x`, []string{"", "x"}, false},
		{"only_escaped_quote", "edge", `""""`, []string{`"`}, false},
		{"quoted_only_comma", "edge", `","`, []string{","}, false},
		{"empty_quoted", "edge", `""`, []string{""}, false},
		{"two_empty_quoted", "edge", `"",""`, []string{"", ""}, false},
		// edge: whitespace significant
		{"significant_spaces", "edge", " a , b ", []string{" a ", " b "}, false},
		{"spaces_in_quotes", "edge", `"a b","c d"`, []string{"a b", "c d"}, false},
		// edge: unicode
		{"unicode", "edge", `"héllo",wörld`, []string{"héllo", "wörld"}, false},
		// edge: errors
		{"bare_quote_unquoted", "edge", `ab"c`, nil, true},
		{"leading_space_then_quote", "edge", `  "x"`, nil, true},
		{"text_after_close", "edge", `"a"b`, nil, true},
		{"unterminated", "edge", `"unterminated`, nil, true},
		{"unterminated_second", "edge", `a,"b`, nil, true},
		// variant: subtle quote adjacency / trailing empties / trap for naive quote-handlers
		{"escaped_quote_then_close", "variant", `"a""","b"`, []string{`a"`, "b"}, false},
		{"quote_inside_second_unquoted", "variant", `a,b"c`, nil, true},
		{"multi_escaped", "variant", `"multi""quote""s"`, []string{`multi"quote"s`}, false},
		{"all_trailing_empties", "variant", "a,,,", []string{"a", "", "", ""}, false},
		{"empty_quoted_between", "variant", `x,"",y`, []string{"x", "", "y"}, false},
	}

	// large stress (variant): many quoted fields containing commas & escaped quotes
	var big string
	var bigWant []string
	for i := 0; i < 150; i++ {
		if i > 0 {
			big += ","
		}
		big += `"v,` + fmt.Sprintf("%d", i) + `""x"`
		bigWant = append(bigWant, fmt.Sprintf(`v,%d"x`, i))
	}
	cases = append(cases, tcase{"large_quoted_stress", "variant", big, bigWant, false})

	results := make([]result, 0, len(cases))
	for _, c := range cases {
		got, err := csvkit.ParseRecord(c.input)
		pass := false
		detail := ""
		if c.wantErr {
			pass = err != nil
			if !pass {
				detail = fmt.Sprintf("expected error, got %q", got)
			}
		} else {
			if err != nil {
				detail = fmt.Sprintf("unexpected error: %v", err)
			} else if !reflect.DeepEqual(got, c.want) {
				detail = fmt.Sprintf("want %q got %q", c.want, got)
			} else {
				pass = true
			}
		}
		results = append(results, result{c.name, c.tag, pass, detail})
	}
	out, _ := json.Marshal(map[string]any{"load_error": nil, "results": results})
	fmt.Println(string(out))
}
