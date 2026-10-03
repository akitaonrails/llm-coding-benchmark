package reference

import "fmt"

type parser struct {
	toks []token
	i    int
}

func parse(src string) (*Node, error) {
	toks, err := lex(src)
	if err != nil {
		return nil, err
	}
	p := &parser{toks: toks}
	n, err := p.parseExpr()
	if err != nil {
		return nil, err
	}
	if p.cur().kind != tEOF {
		return nil, fmt.Errorf("parse error: unexpected trailing token at offset %d", p.cur().pos)
	}
	return n, nil
}

func (p *parser) cur() token  { return p.toks[p.i] }
func (p *parser) next() token { t := p.toks[p.i]; p.i++; return t }
func (p *parser) at(k tokKind) bool { return p.toks[p.i].kind == k }

func (p *parser) expect(k tokKind, what string) (token, error) {
	if p.cur().kind != k {
		return token{}, fmt.Errorf("parse error: expected %s at offset %d", what, p.cur().pos)
	}
	return p.next(), nil
}

func (p *parser) parseExpr() (*Node, error) {
	switch p.cur().kind {
	case tLet:
		return p.parseLet()
	case tIf:
		return p.parseIf()
	case tLambda:
		return p.parseLambda()
	default:
		return p.parseAssign()
	}
}

func (p *parser) parseLet() (*Node, error) {
	pos := p.next().pos // 'let'
	isRec := false
	if p.at(tRec) {
		p.next()
		isRec = true
	}
	nameTok, err := p.expect(tIdent, "identifier after let")
	if err != nil {
		return nil, err
	}
	// optional params: let f a b = ...  == let f = \a -> \b -> ...
	var params []string
	for p.at(tIdent) {
		params = append(params, p.next().str)
	}
	if _, err := p.expect(tAssignEq, "'=' in let"); err != nil {
		return nil, err
	}
	val, err := p.parseExpr()
	if err != nil {
		return nil, err
	}
	for i := len(params) - 1; i >= 0; i-- {
		val = &Node{kind: nLambda, pos: pos, sval: params[i], a: val}
	}
	if isRec && val.kind != nLambda {
		return nil, fmt.Errorf("parse error: 'let rec' requires a function (lambda) right-hand side at offset %d", pos)
	}
	if _, err := p.expect(tIn, "'in' in let"); err != nil {
		return nil, err
	}
	body, err := p.parseExpr()
	if err != nil {
		return nil, err
	}
	return &Node{kind: nLet, pos: pos, sval: nameTok.str, rec: isRec, a: val, b: body}, nil
}

func (p *parser) parseIf() (*Node, error) {
	pos := p.next().pos // 'if'
	cond, err := p.parseExpr()
	if err != nil {
		return nil, err
	}
	if _, err := p.expect(tThen, "'then'"); err != nil {
		return nil, err
	}
	a, err := p.parseExpr()
	if err != nil {
		return nil, err
	}
	if _, err := p.expect(tElse, "'else'"); err != nil {
		return nil, err
	}
	b, err := p.parseExpr()
	if err != nil {
		return nil, err
	}
	return &Node{kind: nIf, pos: pos, a: cond, b: a, c: b}, nil
}

func (p *parser) parseLambda() (*Node, error) {
	pos := p.next().pos // '\'
	var params []string
	for p.at(tIdent) {
		params = append(params, p.next().str)
	}
	if len(params) == 0 {
		return nil, fmt.Errorf("parse error: lambda needs at least one parameter at offset %d", pos)
	}
	if _, err := p.expect(tArrow, "'->' in lambda"); err != nil {
		return nil, err
	}
	body, err := p.parseExpr()
	if err != nil {
		return nil, err
	}
	for i := len(params) - 1; i >= 0; i-- {
		body = &Node{kind: nLambda, pos: pos, sval: params[i], a: body}
	}
	return body, nil
}

// assign := cmp [":=" assign]  (right-assoc)
func (p *parser) parseAssign() (*Node, error) {
	lhs, err := p.parseCmp()
	if err != nil {
		return nil, err
	}
	if p.at(tColonEq) {
		pos := p.next().pos
		rhs, err := p.parseAssign()
		if err != nil {
			return nil, err
		}
		return &Node{kind: nAssign, pos: pos, a: lhs, b: rhs}, nil
	}
	return lhs, nil
}

var cmpOps = map[tokKind]binop{tEq: opEq, tNe: opNe, tLt: opLt, tLe: opLe, tGt: opGt, tGe: opGe}

// cmp := concat [cmpop concat]  (non-associative)
func (p *parser) parseCmp() (*Node, error) {
	lhs, err := p.parseConcat()
	if err != nil {
		return nil, err
	}
	if op, ok := cmpOps[p.cur().kind]; ok {
		pos := p.next().pos
		rhs, err := p.parseConcat()
		if err != nil {
			return nil, err
		}
		return &Node{kind: nBinop, pos: pos, op: op, a: lhs, b: rhs}, nil
	}
	return lhs, nil
}

// concat := add ["^" concat]  (right-assoc)
func (p *parser) parseConcat() (*Node, error) {
	lhs, err := p.parseAdd()
	if err != nil {
		return nil, err
	}
	if p.at(tCaret) {
		pos := p.next().pos
		rhs, err := p.parseConcat()
		if err != nil {
			return nil, err
		}
		return &Node{kind: nBinop, pos: pos, op: opCat, a: lhs, b: rhs}, nil
	}
	return lhs, nil
}

func (p *parser) parseAdd() (*Node, error) {
	lhs, err := p.parseMul()
	if err != nil {
		return nil, err
	}
	for p.at(tPlus) || p.at(tMinus) {
		t := p.next()
		op := opAdd
		if t.kind == tMinus {
			op = opSub
		}
		rhs, err := p.parseMul()
		if err != nil {
			return nil, err
		}
		lhs = &Node{kind: nBinop, pos: t.pos, op: op, a: lhs, b: rhs}
	}
	return lhs, nil
}

func (p *parser) parseMul() (*Node, error) {
	lhs, err := p.parseUnary()
	if err != nil {
		return nil, err
	}
	for p.at(tStar) || p.at(tSlash) {
		t := p.next()
		op := opMul
		if t.kind == tSlash {
			op = opDiv
		}
		rhs, err := p.parseUnary()
		if err != nil {
			return nil, err
		}
		lhs = &Node{kind: nBinop, pos: t.pos, op: op, a: lhs, b: rhs}
	}
	return lhs, nil
}

func (p *parser) parseUnary() (*Node, error) {
	if p.at(tMinus) {
		pos := p.next().pos
		e, err := p.parseUnary()
		if err != nil {
			return nil, err
		}
		return &Node{kind: nUnary, pos: pos, op: opNeg, a: e}, nil
	}
	if p.at(tBang) {
		pos := p.next().pos
		e, err := p.parseUnary()
		if err != nil {
			return nil, err
		}
		return &Node{kind: nUnary, pos: pos, op: opDeref, a: e}, nil
	}
	return p.parseApp()
}

// app := postfix {postfix}  (application by juxtaposition, left-assoc)
func (p *parser) parseApp() (*Node, error) {
	fn, err := p.parsePostfix()
	if err != nil {
		return nil, err
	}
	for p.startsAtom() {
		arg, err := p.parsePostfix()
		if err != nil {
			return nil, err
		}
		fn = &Node{kind: nApp, pos: fn.pos, a: fn, b: arg}
	}
	return fn, nil
}

func (p *parser) startsAtom() bool {
	switch p.cur().kind {
	case tInt, tStr, tTrue, tFalse, tIdent, tLParen, tLBrack, tLBrace:
		return true
	}
	return false
}

// postfix := atom {"." ident}
func (p *parser) parsePostfix() (*Node, error) {
	e, err := p.parseAtom()
	if err != nil {
		return nil, err
	}
	for p.at(tDot) {
		pos := p.next().pos
		nameTok, err := p.expect(tIdent, "field name after '.'")
		if err != nil {
			return nil, err
		}
		e = &Node{kind: nField, pos: pos, sval: nameTok.str, a: e}
	}
	return e, nil
}

func (p *parser) parseAtom() (*Node, error) {
	t := p.cur()
	switch t.kind {
	case tInt:
		p.next()
		return &Node{kind: nInt, pos: t.pos, ival: t.ival}, nil
	case tStr:
		p.next()
		return &Node{kind: nStr, pos: t.pos, sval: t.str}, nil
	case tTrue:
		p.next()
		return &Node{kind: nBool, pos: t.pos, bval: true}, nil
	case tFalse:
		p.next()
		return &Node{kind: nBool, pos: t.pos, bval: false}, nil
	case tIdent:
		p.next()
		return &Node{kind: nVar, pos: t.pos, sval: t.str}, nil
	case tLParen:
		p.next()
		e, err := p.parseExpr()
		if err != nil {
			return nil, err
		}
		if _, err := p.expect(tRParen, "')'"); err != nil {
			return nil, err
		}
		return e, nil
	case tLBrack:
		return p.parseList()
	case tLBrace:
		return p.parseRecord()
	default:
		return nil, fmt.Errorf("parse error: unexpected token at offset %d", t.pos)
	}
}

func (p *parser) parseList() (*Node, error) {
	pos := p.next().pos // '['
	n := &Node{kind: nList, pos: pos}
	if p.at(tRBrack) {
		p.next()
		return n, nil
	}
	for {
		e, err := p.parseExpr()
		if err != nil {
			return nil, err
		}
		n.elems = append(n.elems, e)
		if p.at(tComma) {
			p.next()
			continue
		}
		break
	}
	if _, err := p.expect(tRBrack, "']'"); err != nil {
		return nil, err
	}
	return n, nil
}

func (p *parser) parseRecord() (*Node, error) {
	pos := p.next().pos // '{'
	if p.at(tRBrace) { // empty record
		p.next()
		return &Node{kind: nRecord, pos: pos}, nil
	}
	// Could be a literal {a=..} or an update {expr | a=..}. Disambiguate:
	// an update begins with an expression then '|'. A literal begins with
	// ident '='. We try the update form only if we can parse an expr then see '|'.
	save := p.i
	// Attempt literal: ident '=' ...
	if p.at(tIdent) {
		// peek next token after ident
		if p.toks[p.i+1].kind == tAssignEq {
			return p.parseRecordLiteral(pos)
		}
	}
	// Otherwise parse update: expr '|' fields
	base, err := p.parseExpr()
	if err != nil {
		return nil, err
	}
	if !p.at(tBar) {
		// Not an update; restore and require literal (will error cleanly)
		p.i = save
		return p.parseRecordLiteral(pos)
	}
	p.next() // '|'
	fields, err := p.parseFieldList()
	if err != nil {
		return nil, err
	}
	if _, err := p.expect(tRBrace, "'}'"); err != nil {
		return nil, err
	}
	return &Node{kind: nUpdate, pos: pos, a: base, fields: fields}, nil
}

func (p *parser) parseRecordLiteral(pos int) (*Node, error) {
	fields, err := p.parseFieldList()
	if err != nil {
		return nil, err
	}
	if _, err := p.expect(tRBrace, "'}'"); err != nil {
		return nil, err
	}
	return &Node{kind: nRecord, pos: pos, fields: fields}, nil
}

func (p *parser) parseFieldList() ([]field, error) {
	var fields []field
	for {
		nameTok, err := p.expect(tIdent, "field name")
		if err != nil {
			return nil, err
		}
		if _, err := p.expect(tAssignEq, "'=' in field"); err != nil {
			return nil, err
		}
		val, err := p.parseExpr()
		if err != nil {
			return nil, err
		}
		fields = append(fields, field{name: nameTok.str, val: val})
		if p.at(tComma) {
			p.next()
			continue
		}
		break
	}
	return fields, nil
}
