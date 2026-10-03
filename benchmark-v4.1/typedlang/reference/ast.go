package reference

// AST node kinds. A single Node struct (tagged union) keeps the compiler and
// inferer simple to traverse.

type nodeKind int

const (
	nInt nodeKind = iota
	nBool
	nStr
	nVar
	nLambda  // \param -> body
	nApp     // fn arg
	nLet     // let name = val in body  (Rec set for let rec)
	nIf      // if cond then a else b
	nBinop   // a op b  (op in Op)
	nUnary   // -x or !x
	nList    // [elems...]
	nRecord  // {fields...}
	nUpdate  // {base | fields...}
	nField   // expr.name
	nAssign  // lhs := rhs   (lhs is a Ref)
	nPrim    // internal primitive application (prelude bodies only)
)

// primitive opcodes for prelude bodies (not reachable from source syntax)
type primKind int

const (
	primPrint primKind = iota
	primCons
	primHead
	primTail
	primNull
	primRef
)

type field struct {
	name string
	val  *Node
}

type Node struct {
	kind nodeKind
	pos  int

	ival int64  // nInt
	bval bool    // nBool
	sval string  // nStr / nVar(name) / nLambda(param) / nField(name)
	op   binop   // nBinop / nUnary
	prim primKind

	a, b, c *Node // generic children (fn/arg, cond/then/else, let val/body, binop lhs/rhs, assign lhs/rhs, field expr)
	rec     bool  // nLet: is it let rec
	elems   []*Node
	fields  []field
}

type binop int

const (
	opAdd binop = iota
	opSub
	opMul
	opDiv
	opCat // ^
	opEq
	opNe
	opLt
	opLe
	opGt
	opGe
	opNeg  // unary -
	opDeref // unary !
)

// isSyntacticValue implements the value restriction (SPEC §6.2): only
// identifiers, literals, and lambdas may be generalized.
func isSyntacticValue(n *Node) bool {
	switch n.kind {
	case nInt, nBool, nStr, nVar, nLambda:
		return true
	default:
		return false
	}
}
