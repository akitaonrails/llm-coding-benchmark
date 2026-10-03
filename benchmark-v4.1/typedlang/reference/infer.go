package reference

import "fmt"

// typeEnv is an immutable linked environment of name -> scheme.
type typeEnv struct {
	name string
	sch  scheme
	prev *typeEnv
}

func (e *typeEnv) lookup(n string) (scheme, bool) {
	for p := e; p != nil; p = p.prev {
		if p.name == n {
			return p.sch, true
		}
	}
	return scheme{}, false
}
func (e *typeEnv) extend(n string, s scheme) *typeEnv {
	return &typeEnv{name: n, sch: s, prev: e}
}

type inferer struct {
	opts       Options
	counter    int
	level      int
	unifyDepth int
}

// builtinSchemes builds the polymorphic schemes for the prelude identifiers.
// Order here MUST match the compiler's base scope and the VM's base env.
var builtinNames = []string{"print", "cons", "head", "tail", "null", "not", "ref"}

func qv(id int) *variable { return &variable{id: id} }

func builtinScheme(name string) scheme {
	switch name {
	case "print": // forall a. a -> a
		a := qv(-1)
		return scheme{vars: []*variable{a}, body: tfun{tvar{a}, tvar{a}}}
	case "cons": // forall a. a -> [a] -> [a]
		a := qv(-2)
		return scheme{vars: []*variable{a}, body: tfun{tvar{a}, tfun{tlist{tvar{a}}, tlist{tvar{a}}}}}
	case "head": // forall a. [a] -> a
		a := qv(-3)
		return scheme{vars: []*variable{a}, body: tfun{tlist{tvar{a}}, tvar{a}}}
	case "tail": // forall a. [a] -> [a]
		a := qv(-4)
		return scheme{vars: []*variable{a}, body: tfun{tlist{tvar{a}}, tlist{tvar{a}}}}
	case "null": // forall a. [a] -> Bool
		a := qv(-5)
		return scheme{vars: []*variable{a}, body: tfun{tlist{tvar{a}}, tBool_}}
	case "not": // Bool -> Bool
		return scheme{body: tfun{tBool_, tBool_}}
	case "ref": // forall a. a -> Ref a
		a := qv(-6)
		return scheme{vars: []*variable{a}, body: tfun{tvar{a}, tref{tvar{a}}}}
	}
	panic("unknown builtin " + name)
}

func baseTypeEnv() *typeEnv {
	var e *typeEnv
	for _, n := range builtinNames {
		e = e.extend(n, builtinScheme(n))
	}
	return e
}

func (inf *inferer) infer(env *typeEnv, n *Node) (Type, error) {
	switch n.kind {
	case nInt:
		return tInt_, nil
	case nBool:
		return tBool_, nil
	case nStr:
		return tString_, nil

	case nVar:
		s, ok := env.lookup(n.sval)
		if !ok {
			return nil, fmt.Errorf("unbound: identifier %q", n.sval)
		}
		return inf.instantiate(s), nil

	case nLambda:
		argT := inf.freshVar()
		bodyEnv := env.extend(n.sval, monoScheme(argT))
		retT, err := inf.infer(bodyEnv, n.a)
		if err != nil {
			return nil, err
		}
		return tfun{arg: argT, ret: retT}, nil

	case nApp:
		fnT, err := inf.infer(env, n.a)
		if err != nil {
			return nil, err
		}
		argT, err := inf.infer(env, n.b)
		if err != nil {
			return nil, err
		}
		retT := inf.freshVar()
		if err := inf.unify(fnT, tfun{arg: argT, ret: retT}); err != nil {
			return nil, err
		}
		return retT, nil

	case nLet:
		if n.rec {
			return inf.inferLetRec(env, n)
		}
		inf.level++
		vt, err := inf.infer(env, n.a)
		inf.level--
		if err != nil {
			return nil, err
		}
		sch := inf.maybeGeneralize(prune(vt), n.a)
		return inf.infer(env.extend(n.sval, sch), n.b)

	case nIf:
		condT, err := inf.infer(env, n.a)
		if err != nil {
			return nil, err
		}
		if err := inf.unify(condT, tBool_); err != nil {
			return nil, err
		}
		thenT, err := inf.infer(env, n.b)
		if err != nil {
			return nil, err
		}
		elseT, err := inf.infer(env, n.c)
		if err != nil {
			return nil, err
		}
		if err := inf.unify(thenT, elseT); err != nil {
			return nil, err
		}
		return thenT, nil

	case nBinop:
		return inf.inferBinop(env, n)

	case nUnary:
		at, err := inf.infer(env, n.a)
		if err != nil {
			return nil, err
		}
		switch n.op {
		case opNeg:
			if err := inf.unify(at, tInt_); err != nil {
				return nil, err
			}
			return tInt_, nil
		case opDeref:
			elem := inf.freshVar()
			if err := inf.unify(at, tref{elem: elem}); err != nil {
				return nil, err
			}
			return elem, nil
		}

	case nAssign:
		lhsT, err := inf.infer(env, n.a)
		if err != nil {
			return nil, err
		}
		rhsT, err := inf.infer(env, n.b)
		if err != nil {
			return nil, err
		}
		if err := inf.unify(lhsT, tref{elem: rhsT}); err != nil {
			return nil, err
		}
		return rhsT, nil

	case nList:
		elemT := inf.freshVar()
		for _, e := range n.elems {
			et, err := inf.infer(env, e)
			if err != nil {
				return nil, err
			}
			if err := inf.unify(et, elemT); err != nil {
				return nil, err
			}
		}
		return tlist{elem: elemT}, nil

	case nRecord:
		if err := checkDupFields(n.fields); err != nil {
			return nil, err
		}
		row := Row(rowEmpty{})
		// build row; order does not matter for unification
		for i := len(n.fields) - 1; i >= 0; i-- {
			ft, err := inf.infer(env, n.fields[i].val)
			if err != nil {
				return nil, err
			}
			row = rowExtend{label: n.fields[i].name, field: ft, rest: row}
		}
		return trecord{row: row}, nil

	case nUpdate:
		return inf.inferUpdate(env, n)

	case nField:
		exprT, err := inf.infer(env, n.a)
		if err != nil {
			return nil, err
		}
		fieldT := inf.freshVar()
		var tail Row
		if inf.opts.Rows {
			tail = inf.freshRow()
		} else {
			tail = rowEmpty{}
		}
		if err := inf.unify(exprT, trecord{row: rowExtend{label: n.sval, field: fieldT, rest: tail}}); err != nil {
			return nil, err
		}
		return fieldT, nil
	}
	return nil, fmt.Errorf("type error: cannot infer node kind %d", n.kind)
}

func (inf *inferer) inferLetRec(env *typeEnv, n *Node) (Type, error) {
	inf.level++
	recT := inf.freshVar()
	valEnv := env.extend(n.sval, monoScheme(recT))
	vt, err := inf.infer(valEnv, n.a)
	if err != nil {
		inf.level--
		return nil, err
	}
	if err := inf.unify(recT, vt); err != nil {
		inf.level--
		return nil, err
	}
	inf.level--
	// a let rec rhs is always a lambda (a syntactic value) -> generalizable.
	sch := inf.maybeGeneralize(prune(recT), n.a)
	return inf.infer(env.extend(n.sval, sch), n.b)
}

// maybeGeneralize applies let-generalization subject to the value restriction
// and the Options toggles (so the broken variants can turn each off).
func (inf *inferer) maybeGeneralize(t Type, rhs *Node) scheme {
	gen := inf.opts.Generalize
	if gen && inf.opts.ValueRestriction && !isSyntacticValue(rhs) {
		gen = false
	}
	if gen {
		return inf.generalize(t)
	}
	return monoScheme(t)
}

func (inf *inferer) inferBinop(env *typeEnv, n *Node) (Type, error) {
	lt, err := inf.infer(env, n.a)
	if err != nil {
		return nil, err
	}
	rt, err := inf.infer(env, n.b)
	if err != nil {
		return nil, err
	}
	switch n.op {
	case opAdd, opSub, opMul, opDiv:
		if err := inf.unify(lt, tInt_); err != nil {
			return nil, err
		}
		if err := inf.unify(rt, tInt_); err != nil {
			return nil, err
		}
		return tInt_, nil
	case opCat:
		if err := inf.unify(lt, tString_); err != nil {
			return nil, err
		}
		if err := inf.unify(rt, tString_); err != nil {
			return nil, err
		}
		return tString_, nil
	case opEq, opNe, opLt, opLe, opGt, opGe:
		if err := inf.unify(lt, tInt_); err != nil {
			return nil, err
		}
		if err := inf.unify(rt, tInt_); err != nil {
			return nil, err
		}
		return tBool_, nil
	}
	return nil, fmt.Errorf("type error: bad binop")
}

func (inf *inferer) inferUpdate(env *typeEnv, n *Node) (Type, error) {
	if err := checkDupFields(n.fields); err != nil {
		return nil, err
	}
	baseT, err := inf.infer(env, n.a)
	if err != nil {
		return nil, err
	}
	// shared tail: open if rows are enabled, closed otherwise.
	var tail Row
	if inf.opts.Rows {
		tail = inf.freshRow()
	} else {
		tail = rowEmpty{}
	}
	// expected base row: must contain each updated field (with fresh field vars);
	expRow := tail
	for i := len(n.fields) - 1; i >= 0; i-- {
		expRow = rowExtend{label: n.fields[i].name, field: inf.freshVar(), rest: expRow}
	}
	if err := inf.unify(baseT, trecord{row: expRow}); err != nil {
		return nil, err
	}
	// result row: same tail, updated fields get their new value types.
	resRow := tail
	for i := len(n.fields) - 1; i >= 0; i-- {
		ft, err := inf.infer(env, n.fields[i].val)
		if err != nil {
			return nil, err
		}
		resRow = rowExtend{label: n.fields[i].name, field: ft, rest: resRow}
	}
	return trecord{row: resRow}, nil
}

func checkDupFields(fs []field) error {
	seen := map[string]bool{}
	for _, f := range fs {
		if seen[f.name] {
			return fmt.Errorf("type error: duplicate field %q", f.name)
		}
		seen[f.name] = true
	}
	return nil
}
