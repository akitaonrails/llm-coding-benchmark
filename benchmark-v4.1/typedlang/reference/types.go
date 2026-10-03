package reference

import "fmt"

// ---------------------------------------------------------------------------
// Types and rows. Inference uses the classic imperative level-based algorithm
// (OCaml/Rémy style): type variables are mutable cells with a generalization
// LEVEL; a let generalizes exactly the variables whose level is deeper than the
// enclosing let. Records use a row representation with row variables.
// ---------------------------------------------------------------------------

type Type interface{ isType() }

type tcon struct{ name string } // "Int" | "Bool" | "String"
type tfun struct{ arg, ret Type }
type tlist struct{ elem Type }
type tref struct{ elem Type }
type trecord struct{ row Row }
type tvar struct{ v *variable }

func (tcon) isType()    {}
func (tfun) isType()    {}
func (tlist) isType()   {}
func (tref) isType()    {}
func (trecord) isType() {}
func (tvar) isType()    {}

type Row interface{ isRow() }

type rowEmpty struct{}
type rowExtend struct {
	label string
	field Type
	rest  Row
}
type rowVar struct{ v *variable }

func (rowEmpty) isRow()  {}
func (rowExtend) isRow() {}
func (rowVar) isRow()    {}

// A variable is a unifiable cell used for BOTH type variables and row
// variables (isRow distinguishes). link is nil when unbound; otherwise it is a
// Type (for a type var) or a Row (for a row var).
type variable struct {
	id    int
	level int
	link  interface{}
	isRow bool
}

var (
	tInt_    = tcon{"Int"}
	tBool_   = tcon{"Bool"}
	tString_ = tcon{"String"}
)

// scheme is a generalized type: forall vars . body.
type scheme struct {
	vars []*variable
	body Type
}

// ---------------------------------------------------------------------------
// pruning (path compression along resolved links)
// ---------------------------------------------------------------------------

func prune(t Type) Type {
	if tv, ok := t.(tvar); ok && tv.v.link != nil {
		p := prune(tv.v.link.(Type))
		tv.v.link = p
		return p
	}
	return t
}

func pruneRow(r Row) Row {
	if rv, ok := r.(rowVar); ok && rv.v.link != nil {
		p := pruneRow(rv.v.link.(Row))
		rv.v.link = p
		return p
	}
	return r
}

// ---------------------------------------------------------------------------
// the inferer's variable factory and unification live on *inferer so they can
// consult options (occurs check / rows toggles for the broken variants).
// ---------------------------------------------------------------------------

func (inf *inferer) freshVar() Type {
	inf.counter++
	return tvar{&variable{id: inf.counter, level: inf.level}}
}
func (inf *inferer) freshVarAt(level int) Type {
	inf.counter++
	return tvar{&variable{id: inf.counter, level: level}}
}
func (inf *inferer) freshRow() Row {
	inf.counter++
	return rowVar{&variable{id: inf.counter, level: inf.level, isRow: true}}
}
func (inf *inferer) freshRowAt(level int) Row {
	inf.counter++
	return rowVar{&variable{id: inf.counter, level: level, isRow: true}}
}

// ---------------------------------------------------------------------------
// occurs check + level adjustment (one pass, cycle-guarded so the "no occurs
// check" broken variant cannot wedge the inferer).
// ---------------------------------------------------------------------------

func (inf *inferer) occursAdjust(v *variable, t Type, seen map[*variable]bool) error {
	inf.unifyDepth++
	defer func() { inf.unifyDepth-- }()
	if inf.unifyDepth > maxUnifyDepth {
		// traversing a cyclic type built without the occurs check
		return fmt.Errorf("occurs check: cannot construct the infinite type")
	}
	t = prune(t)
	switch tt := t.(type) {
	case tvar:
		if tt.v == v {
			if inf.opts.OccursCheck {
				return fmt.Errorf("occurs check: cannot construct the infinite type")
			}
			return nil // broken variant: silently allow (creates a cyclic type)
		}
		if seen[tt.v] {
			return nil
		}
		seen[tt.v] = true
		if tt.v.level > v.level {
			tt.v.level = v.level
		}
	case tcon:
	case tfun:
		if err := inf.occursAdjust(v, tt.arg, seen); err != nil {
			return err
		}
		return inf.occursAdjust(v, tt.ret, seen)
	case tlist:
		return inf.occursAdjust(v, tt.elem, seen)
	case tref:
		return inf.occursAdjust(v, tt.elem, seen)
	case trecord:
		return inf.occursAdjustRow(v, tt.row, seen)
	}
	return nil
}

func (inf *inferer) occursAdjustRow(v *variable, r Row, seen map[*variable]bool) error {
	inf.unifyDepth++
	defer func() { inf.unifyDepth-- }()
	if inf.unifyDepth > maxUnifyDepth {
		return fmt.Errorf("occurs check: cannot construct the infinite record")
	}
	r = pruneRow(r)
	switch rr := r.(type) {
	case rowEmpty:
	case rowVar:
		if rr.v == v {
			if inf.opts.OccursCheck {
				return fmt.Errorf("occurs check: cannot construct the infinite record")
			}
			return nil
		}
		if seen[rr.v] {
			return nil
		}
		seen[rr.v] = true
		if rr.v.level > v.level {
			rr.v.level = v.level
		}
	case rowExtend:
		if err := inf.occursAdjust(v, rr.field, seen); err != nil {
			return err
		}
		return inf.occursAdjustRow(v, rr.rest, seen)
	}
	return nil
}

func (inf *inferer) bindVar(v *variable, t Type) error {
	if err := inf.occursAdjust(v, t, map[*variable]bool{}); err != nil {
		return err
	}
	v.link = t
	return nil
}

// ---------------------------------------------------------------------------
// unification
// ---------------------------------------------------------------------------

// maxUnifyDepth bounds unification recursion. Legitimate types unify in very
// shallow depth; this only trips on the cyclic (infinite) types that arise when
// the occurs check is disabled, converting an otherwise-fatal stack overflow
// into a clean type error so a single test (not the whole binary) is affected.
const maxUnifyDepth = 10000

func (inf *inferer) unify(a, b Type) error {
	inf.unifyDepth++
	defer func() { inf.unifyDepth-- }()
	if inf.unifyDepth > maxUnifyDepth {
		return fmt.Errorf("type error: unification too deep (cyclic type without occurs check)")
	}
	a = prune(a)
	b = prune(b)
	if av, ok := a.(tvar); ok {
		if bv, ok := b.(tvar); ok && av.v == bv.v {
			return nil
		}
		return inf.bindVar(av.v, b)
	}
	if bv, ok := b.(tvar); ok {
		return inf.bindVar(bv.v, a)
	}
	switch at := a.(type) {
	case tcon:
		if bt, ok := b.(tcon); ok && at.name == bt.name {
			return nil
		}
	case tfun:
		if bt, ok := b.(tfun); ok {
			if err := inf.unify(at.arg, bt.arg); err != nil {
				return err
			}
			return inf.unify(at.ret, bt.ret)
		}
	case tlist:
		if bt, ok := b.(tlist); ok {
			return inf.unify(at.elem, bt.elem)
		}
	case tref:
		if bt, ok := b.(tref); ok {
			return inf.unify(at.elem, bt.elem)
		}
	case trecord:
		if bt, ok := b.(trecord); ok {
			return inf.unifyRow(at.row, bt.row)
		}
	}
	return fmt.Errorf("type error: cannot unify %s with %s", typeString(a), typeString(b))
}

// ---------------------------------------------------------------------------
// row unification by rewriting (Rémy / Leijen style)
// ---------------------------------------------------------------------------

func rowTailVar(r Row) *variable {
	r = pruneRow(r)
	switch rr := r.(type) {
	case rowVar:
		return rr.v
	case rowExtend:
		return rowTailVar(rr.rest)
	}
	return nil
}

func (inf *inferer) bindRowVar(v *variable, r Row) error {
	if err := inf.occursAdjustRow(v, r, map[*variable]bool{}); err != nil {
		return err
	}
	v.link = r
	return nil
}

func (inf *inferer) unifyRow(r1, r2 Row) error {
	inf.unifyDepth++
	defer func() { inf.unifyDepth-- }()
	if inf.unifyDepth > maxUnifyDepth {
		return fmt.Errorf("type error: row unification too deep (cyclic row without occurs check)")
	}
	r1 = pruneRow(r1)
	r2 = pruneRow(r2)
	switch rr1 := r1.(type) {
	case rowEmpty:
		switch r2.(type) {
		case rowEmpty:
			return nil
		case rowVar:
			return inf.bindRowVar(r2.(rowVar).v, rowEmpty{})
		default:
			return fmt.Errorf("type error: record has extra fields")
		}
	case rowVar:
		if rv2, ok := r2.(rowVar); ok && rv2.v == rr1.v {
			return nil
		}
		return inf.bindRowVar(rr1.v, r2)
	case rowExtend:
		field2, rest2, err := inf.rewriteRow(r2, rr1.label, rowTailVar(rr1.rest))
		if err != nil {
			return err
		}
		if err := inf.unify(rr1.field, field2); err != nil {
			return err
		}
		return inf.unifyRow(rr1.rest, rest2)
	}
	return fmt.Errorf("type error: cannot unify records")
}

// rewriteRow finds `label` in `row`, returning its field type and the remaining
// row. If `row` ends in a row variable, it extends that variable with the label
// (this is what makes records row-polymorphic: an open row absorbs new labels).
// A closed row (rowEmpty tail) without the label is a type error.
func (inf *inferer) rewriteRow(row Row, label string, forbidden *variable) (Type, Row, error) {
	row = pruneRow(row)
	switch rr := row.(type) {
	case rowEmpty:
		return nil, nil, fmt.Errorf("type error: record is missing field %q", label)
	case rowExtend:
		if rr.label == label {
			return rr.field, rr.rest, nil
		}
		f2, rest2, err := inf.rewriteRow(rr.rest, label, forbidden)
		if err != nil {
			return nil, nil, err
		}
		return f2, rowExtend{label: rr.label, field: rr.field, rest: rest2}, nil
	case rowVar:
		if rr.v == forbidden {
			return nil, nil, fmt.Errorf("type error: recursive row type")
		}
		beta := inf.freshVarAt(rr.v.level)
		gamma := inf.freshRowAt(rr.v.level)
		ext := rowExtend{label: label, field: beta, rest: gamma}
		rr.v.link = Row(ext)
		return beta, gamma, nil
	}
	return nil, nil, fmt.Errorf("type error: malformed row")
}

// ---------------------------------------------------------------------------
// generalization + instantiation
// ---------------------------------------------------------------------------

// generalize collects the unbound variables whose level is deeper than the
// current (enclosing) level — those are not referenced by the outer env and may
// become polymorphic.
func (inf *inferer) generalize(t Type) scheme {
	var vars []*variable
	seen := map[*variable]bool{}
	inf.collectGen(t, &vars, seen)
	return scheme{vars: vars, body: t}
}

func (inf *inferer) collectGen(t Type, out *[]*variable, seen map[*variable]bool) {
	t = prune(t)
	switch tt := t.(type) {
	case tvar:
		if seen[tt.v] {
			return
		}
		seen[tt.v] = true
		if tt.v.level > inf.level {
			*out = append(*out, tt.v)
		}
	case tcon:
	case tfun:
		inf.collectGen(tt.arg, out, seen)
		inf.collectGen(tt.ret, out, seen)
	case tlist:
		inf.collectGen(tt.elem, out, seen)
	case tref:
		inf.collectGen(tt.elem, out, seen)
	case trecord:
		inf.collectGenRow(tt.row, out, seen)
	}
}

func (inf *inferer) collectGenRow(r Row, out *[]*variable, seen map[*variable]bool) {
	r = pruneRow(r)
	switch rr := r.(type) {
	case rowEmpty:
	case rowVar:
		if seen[rr.v] {
			return
		}
		seen[rr.v] = true
		if rr.v.level > inf.level {
			*out = append(*out, rr.v)
		}
	case rowExtend:
		inf.collectGen(rr.field, out, seen)
		inf.collectGenRow(rr.rest, out, seen)
	}
}

// monomorphic scheme (no quantified vars) — used for lambda params, value
// restriction, and let bindings in the broken "no generalization" variant.
func monoScheme(t Type) scheme { return scheme{body: t} }

func (inf *inferer) instantiate(s scheme) Type {
	if len(s.vars) == 0 {
		return s.body
	}
	sub := map[*variable]interface{}{} // *variable -> Type or Row
	for _, v := range s.vars {
		if v.isRow {
			sub[v] = inf.freshRow()
		} else {
			sub[v] = inf.freshVar()
		}
	}
	return inf.substType(s.body, sub)
}

func (inf *inferer) substType(t Type, sub map[*variable]interface{}) Type {
	t = prune(t)
	switch tt := t.(type) {
	case tvar:
		if r, ok := sub[tt.v]; ok {
			return r.(Type)
		}
		return tt
	case tcon:
		return tt
	case tfun:
		return tfun{arg: inf.substType(tt.arg, sub), ret: inf.substType(tt.ret, sub)}
	case tlist:
		return tlist{elem: inf.substType(tt.elem, sub)}
	case tref:
		return tref{elem: inf.substType(tt.elem, sub)}
	case trecord:
		return trecord{row: inf.substRow(tt.row, sub)}
	}
	return t
}

func (inf *inferer) substRow(r Row, sub map[*variable]interface{}) Row {
	r = pruneRow(r)
	switch rr := r.(type) {
	case rowEmpty:
		return rr
	case rowVar:
		if x, ok := sub[rr.v]; ok {
			return x.(Row)
		}
		return rr
	case rowExtend:
		return rowExtend{label: rr.label, field: inf.substType(rr.field, sub), rest: inf.substRow(rr.rest, sub)}
	}
	return r
}

// ---------------------------------------------------------------------------
// best-effort type printing for error messages (depth-guarded against cycles
// that the no-occurs-check variant can create). Not graded; nil-vs-error is.
// ---------------------------------------------------------------------------

func typeString(t Type) string { return typeStringD(t, 0) }

func typeStringD(t Type, depth int) string {
	if depth > 12 {
		return "…"
	}
	t = prune(t)
	switch tt := t.(type) {
	case tvar:
		return fmt.Sprintf("t%d", tt.v.id)
	case tcon:
		return tt.name
	case tfun:
		return "(" + typeStringD(tt.arg, depth+1) + " -> " + typeStringD(tt.ret, depth+1) + ")"
	case tlist:
		return "[" + typeStringD(tt.elem, depth+1) + "]"
	case tref:
		return "Ref " + typeStringD(tt.elem, depth+1)
	case trecord:
		return "{" + rowStringD(tt.row, depth+1) + "}"
	}
	return "?"
}

func rowStringD(r Row, depth int) string {
	if depth > 12 {
		return "…"
	}
	r = pruneRow(r)
	switch rr := r.(type) {
	case rowEmpty:
		return ""
	case rowVar:
		return fmt.Sprintf("|r%d", rr.v.id)
	case rowExtend:
		s := rr.label + ":" + typeStringD(rr.field, depth+1)
		rest := rowStringD(rr.rest, depth+1)
		if rest != "" {
			s += ", " + rest
		}
		return s
	}
	return "?"
}
