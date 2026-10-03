package reference

import (
	"fmt"
	"strings"
)

type tokKind int

const (
	tEOF tokKind = iota
	tInt
	tStr
	tIdent
	// keywords
	tLet
	tRec
	tIn
	tIf
	tThen
	tElse
	tTrue
	tFalse
	// punctuation / operators
	tPlus
	tMinus
	tStar
	tSlash
	tCaret
	tEq   // ==
	tNe   // !=
	tLt   // <
	tLe   // <=
	tGt   // >
	tGe   // >=
	tArrow
	tAssignEq // = (binding)
	tDot
	tBar
	tBang    // !
	tColonEq // :=
	tLParen
	tRParen
	tLBrace
	tRBrace
	tLBrack
	tRBrack
	tComma
	tLambda // backslash
)

type token struct {
	kind tokKind
	str  string // identifier / string value
	ival int64  // integer value
	pos  int    // byte offset, for messages
}

var keywords = map[string]tokKind{
	"let": tLet, "rec": tRec, "in": tIn, "if": tIf,
	"then": tThen, "else": tElse, "true": tTrue, "false": tFalse,
}

type lexer struct {
	src  string
	pos  int
	toks []token
}

func isIdentStart(c byte) bool {
	return c == '_' || (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
}
func isIdentCont(c byte) bool { return isIdentStart(c) || (c >= '0' && c <= '9') }
func isDigit(c byte) bool     { return c >= '0' && c <= '9' }

func lex(src string) ([]token, error) {
	l := &lexer{src: src}
	for l.pos < len(src) {
		c := src[l.pos]
		switch {
		case c == ' ' || c == '\t' || c == '\r' || c == '\n':
			l.pos++
		case c == '-' && l.peek(1) == '-': // line comment
			for l.pos < len(src) && src[l.pos] != '\n' {
				l.pos++
			}
		case isDigit(c):
			if err := l.lexInt(); err != nil {
				return nil, err
			}
		case c == '"':
			if err := l.lexStr(); err != nil {
				return nil, err
			}
		case isIdentStart(c):
			l.lexIdent()
		default:
			if err := l.lexOp(); err != nil {
				return nil, err
			}
		}
	}
	l.toks = append(l.toks, token{kind: tEOF, pos: l.pos})
	return l.toks, nil
}

func (l *lexer) peek(n int) byte {
	if l.pos+n < len(l.src) {
		return l.src[l.pos+n]
	}
	return 0
}

func (l *lexer) emit(k tokKind, s string) { l.toks = append(l.toks, token{kind: k, str: s, pos: l.pos}) }

func (l *lexer) lexInt() error {
	start := l.pos
	var v int64
	for l.pos < len(l.src) && isDigit(l.src[l.pos]) {
		d := int64(l.src[l.pos] - '0')
		// overflow guard
		if v > (1<<62)/5 {
			return fmt.Errorf("lex error: integer literal too large at offset %d", start)
		}
		v = v*10 + d
		l.pos++
	}
	l.toks = append(l.toks, token{kind: tInt, ival: v, pos: start})
	return nil
}

func (l *lexer) lexStr() error {
	start := l.pos
	l.pos++ // opening quote
	var b strings.Builder
	for l.pos < len(l.src) {
		c := l.src[l.pos]
		if c == '"' {
			l.pos++
			l.toks = append(l.toks, token{kind: tStr, str: b.String(), pos: start})
			return nil
		}
		if c == '\\' {
			l.pos++
			if l.pos >= len(l.src) {
				break
			}
			switch l.src[l.pos] {
			case 'n':
				b.WriteByte('\n')
			case 't':
				b.WriteByte('\t')
			case '\\':
				b.WriteByte('\\')
			case '"':
				b.WriteByte('"')
			default:
				return fmt.Errorf("lex error: bad escape \\%c at offset %d", l.src[l.pos], l.pos)
			}
			l.pos++
			continue
		}
		b.WriteByte(c)
		l.pos++
	}
	return fmt.Errorf("lex error: unterminated string at offset %d", start)
}

func (l *lexer) lexIdent() {
	start := l.pos
	for l.pos < len(l.src) && isIdentCont(l.src[l.pos]) {
		l.pos++
	}
	s := l.src[start:l.pos]
	if k, ok := keywords[s]; ok {
		l.toks = append(l.toks, token{kind: k, str: s, pos: start})
	} else {
		l.toks = append(l.toks, token{kind: tIdent, str: s, pos: start})
	}
}

func (l *lexer) lexOp() error {
	start := l.pos
	two := ""
	if l.pos+1 < len(l.src) {
		two = l.src[l.pos : l.pos+2]
	}
	switch two {
	case "==":
		l.pos += 2
		l.toks = append(l.toks, token{kind: tEq, pos: start})
		return nil
	case "!=":
		l.pos += 2
		l.toks = append(l.toks, token{kind: tNe, pos: start})
		return nil
	case "<=":
		l.pos += 2
		l.toks = append(l.toks, token{kind: tLe, pos: start})
		return nil
	case ">=":
		l.pos += 2
		l.toks = append(l.toks, token{kind: tGe, pos: start})
		return nil
	case "->":
		l.pos += 2
		l.toks = append(l.toks, token{kind: tArrow, pos: start})
		return nil
	case ":=":
		l.pos += 2
		l.toks = append(l.toks, token{kind: tColonEq, pos: start})
		return nil
	}
	c := l.src[l.pos]
	l.pos++
	var k tokKind
	switch c {
	case '+':
		k = tPlus
	case '-':
		k = tMinus
	case '*':
		k = tStar
	case '/':
		k = tSlash
	case '^':
		k = tCaret
	case '<':
		k = tLt
	case '>':
		k = tGt
	case '=':
		k = tAssignEq
	case '.':
		k = tDot
	case '|':
		k = tBar
	case '!':
		k = tBang
	case '(':
		k = tLParen
	case ')':
		k = tRParen
	case '{':
		k = tLBrace
	case '}':
		k = tRBrace
	case '[':
		k = tLBrack
	case ']':
		k = tRBrack
	case ',':
		k = tComma
	case '\\':
		k = tLambda
	default:
		return fmt.Errorf("lex error: unexpected character %q at offset %d", string(c), start)
	}
	l.toks = append(l.toks, token{kind: k, pos: start})
	return nil
}
