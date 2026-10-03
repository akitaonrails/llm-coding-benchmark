package reference

import "fmt"

type opcode uint8

const (
	opPushInt  opcode = iota // a = index into ints pool
	opPushBool               // a = 0/1
	opPushStr                // a = index into strs pool
	opVar                    // a = de Bruijn depth into env chain
	opClosure                // a = body address
	opCall                   // apply (non-tail)
	opTailCall               // apply (tail position)
	opRet
	opJmp      // a = target
	opJmpFalse // a = target (pops a bool)
	opExtend   // pop value -> push new env frame (let binding)
	opShrink   // curEnv = curEnv.parent
	opRecSlot  // pop value -> store into curEnv.slot0 (let rec backpatch)
	opIAdd
	opISub
	opIMul
	opIDiv
	opSCat
	opIEq
	opINe
	opILt
	opILe
	opIGt
	opIGe
	opINeg
	opIDeref // !r
	opSetRef // r := v   (stack: ref, val -> val)
	opMakeList
	opMakeRecord // a = index into recSpecs
	opField      // a = index into strs pool (field name)
	opUpdate     // a = index into recSpecs (updated field names)
)

type instr struct {
	op opcode
	a  int
}

type program struct {
	code     []instr
	ints     []int64
	strs     []string
	recSpecs [][]string
}

type compiler struct {
	prog  *program
	scope []string // innermost at the end; depth = len-1-index
}

func newProgram() *program { return &program{} }

func (c *compiler) emit(op opcode, a int) int {
	c.prog.code = append(c.prog.code, instr{op: op, a: a})
	return len(c.prog.code) - 1
}

func (c *compiler) intIdx(v int64) int {
	for i, x := range c.prog.ints {
		if x == v {
			return i
		}
	}
	c.prog.ints = append(c.prog.ints, v)
	return len(c.prog.ints) - 1
}
func (c *compiler) strIdx(s string) int {
	for i, x := range c.prog.strs {
		if x == s {
			return i
		}
	}
	c.prog.strs = append(c.prog.strs, s)
	return len(c.prog.strs) - 1
}
func (c *compiler) recSpecIdx(names []string) int {
	cp := append([]string(nil), names...)
	c.prog.recSpecs = append(c.prog.recSpecs, cp)
	return len(c.prog.recSpecs) - 1
}

func (c *compiler) depthOf(name string) (int, bool) {
	for i := len(c.scope) - 1; i >= 0; i-- {
		if c.scope[i] == name {
			return len(c.scope) - 1 - i, true
		}
	}
	return 0, false
}

func (c *compiler) push(name string) { c.scope = append(c.scope, name) }
func (c *compiler) pop()             { c.scope = c.scope[:len(c.scope)-1] }

// compileProgram compiles the user AST with the builtin base scope in place.
func compileProgram(n *Node) (*program, error) {
	c := &compiler{prog: newProgram()}
	// base scope order matches the VM base env (builtinNames[0] outermost).
	c.scope = append(c.scope, builtinNames...)
	if err := c.compile(n, true); err != nil {
		return nil, err
	}
	c.emit(opRet, 0)
	return c.prog, nil
}

// compile emits code for n. tail indicates n is in tail position.
func (c *compiler) compile(n *Node, tail bool) error {
	switch n.kind {
	case nInt:
		c.emit(opPushInt, c.intIdx(n.ival))
	case nBool:
		b := 0
		if n.bval {
			b = 1
		}
		c.emit(opPushBool, b)
	case nStr:
		c.emit(opPushStr, c.strIdx(n.sval))
	case nVar:
		d, ok := c.depthOf(n.sval)
		if !ok {
			return fmt.Errorf("compile error: unbound identifier %q", n.sval)
		}
		c.emit(opVar, d)
	case nLambda:
		c.compileLambda(n)
	case nApp:
		if err := c.compile(n.a, false); err != nil {
			return err
		}
		if err := c.compile(n.b, false); err != nil {
			return err
		}
		if tail {
			c.emit(opTailCall, 0)
		} else {
			c.emit(opCall, 0)
		}
	case nLet:
		return c.compileLet(n, tail)
	case nIf:
		return c.compileIf(n, tail)
	case nBinop:
		return c.compileBinop(n)
	case nUnary:
		if err := c.compile(n.a, false); err != nil {
			return err
		}
		switch n.op {
		case opNeg:
			c.emit(opINeg, 0)
		case opDeref:
			c.emit(opIDeref, 0)
		}
	case nAssign:
		if err := c.compile(n.a, false); err != nil {
			return err
		}
		if err := c.compile(n.b, false); err != nil {
			return err
		}
		c.emit(opSetRef, 0)
	case nList:
		for _, e := range n.elems {
			if err := c.compile(e, false); err != nil {
				return err
			}
		}
		c.emit(opMakeList, len(n.elems))
	case nRecord:
		names := make([]string, len(n.fields))
		for i, f := range n.fields {
			names[i] = f.name
			if err := c.compile(f.val, false); err != nil {
				return err
			}
		}
		c.emit(opMakeRecord, c.recSpecIdx(names))
	case nUpdate:
		if err := c.compile(n.a, false); err != nil {
			return err
		}
		names := make([]string, len(n.fields))
		for i, f := range n.fields {
			names[i] = f.name
			if err := c.compile(f.val, false); err != nil {
				return err
			}
		}
		c.emit(opUpdate, c.recSpecIdx(names))
	case nField:
		if err := c.compile(n.a, false); err != nil {
			return err
		}
		c.emit(opField, c.strIdx(n.sval))
	default:
		return fmt.Errorf("compile error: unknown node kind %d", n.kind)
	}
	return nil
}

func (c *compiler) compileLambda(n *Node) {
	closureAt := c.emit(opClosure, 0)
	jmpAt := c.emit(opJmp, 0)
	bodyStart := len(c.prog.code)
	c.prog.code[closureAt].a = bodyStart
	c.push(n.sval)
	c.compile(n.a, true)
	c.pop()
	c.emit(opRet, 0)
	c.prog.code[jmpAt].a = len(c.prog.code)
}

func (c *compiler) compileLet(n *Node, tail bool) error {
	if n.rec {
		c.emit(opPushInt, c.intIdx(0)) // placeholder value for the rec slot
		c.emit(opExtend, 0)
		c.push(n.sval)
		if err := c.compile(n.a, false); err != nil { // lambda captures this frame
			return err
		}
		c.emit(opRecSlot, 0)
		if err := c.compile(n.b, tail); err != nil {
			return err
		}
		c.pop()
		if !tail {
			c.emit(opShrink, 0)
		}
		return nil
	}
	if err := c.compile(n.a, false); err != nil {
		return err
	}
	c.emit(opExtend, 0)
	c.push(n.sval)
	if err := c.compile(n.b, tail); err != nil {
		return err
	}
	c.pop()
	if !tail {
		c.emit(opShrink, 0)
	}
	return nil
}

func (c *compiler) compileIf(n *Node, tail bool) error {
	if err := c.compile(n.a, false); err != nil {
		return err
	}
	jf := c.emit(opJmpFalse, 0)
	if err := c.compile(n.b, tail); err != nil {
		return err
	}
	jend := c.emit(opJmp, 0)
	c.prog.code[jf].a = len(c.prog.code)
	if err := c.compile(n.c, tail); err != nil {
		return err
	}
	c.prog.code[jend].a = len(c.prog.code)
	return nil
}

func (c *compiler) compileBinop(n *Node) error {
	if err := c.compile(n.a, false); err != nil {
		return err
	}
	if err := c.compile(n.b, false); err != nil {
		return err
	}
	var op opcode
	switch n.op {
	case opAdd:
		op = opIAdd
	case opSub:
		op = opISub
	case opMul:
		op = opIMul
	case opDiv:
		op = opIDiv
	case opCat:
		op = opSCat
	case opEq:
		op = opIEq
	case opNe:
		op = opINe
	case opLt:
		op = opILt
	case opLe:
		op = opILe
	case opGt:
		op = opIGt
	case opGe:
		op = opIGe
	default:
		return fmt.Errorf("compile error: bad binop")
	}
	c.emit(op, 0)
	return nil
}
