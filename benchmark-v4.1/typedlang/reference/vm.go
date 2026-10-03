package reference

import (
	"fmt"
	"strings"
)

// builtin ids = index into builtinNames (print, cons, head, tail, null, not, ref)
const (
	biPrint = iota
	biCons
	biHead
	biTail
	biNull
	biNot
	biRef
)

var builtinArity = []int{1, 2, 1, 1, 1, 1, 1}

type callFrame struct {
	ret int   // return instruction address; <0 = halt sentinel
	env int32 // caller env to restore
}

// vm is the stack VM plus its managed, generationally-collected heap.
type vm struct {
	prog *program
	opts Options

	// execution state
	ip     int
	env    int32
	stack  []value
	frames []callFrame
	out    strings.Builder

	halt    bool
	runErr  error
	baseEnv int32

	// managed heap
	objs     []object
	freeList []int32
	gen0     []int32 // nursery handles
	gen1     []int32 // old-generation handles
	remember []int32 // write-barrier remembered set (old objects with young pointers)

	liveBytes int64
	gen0Bytes int64
	gen1Bytes int64
	peakBytes int64

	nurseryLimit int64
	oldLimit     int64
	hardCap      int64

	needMinor bool
	oom       bool
	numGC     int64
}

func newVM(prog *program, opts Options) *vm {
	vm := &vm{
		prog:         prog,
		opts:         opts,
		nurseryLimit: 1 << 20,   // 1 MiB nursery
		oldLimit:     8 << 20,   // 8 MiB initial old-gen trigger
		hardCap:      64 << 20,  // 64 MiB hard live cap
	}
	// base environment: one frame per builtin, in builtinNames order, so the
	// LAST (ref) is innermost (depth 0), matching the compiler's base scope.
	var prev int32 = -1
	for i := range builtinNames {
		b := vm.alloc(object{kind: oBuiltin, bid: i})
		f := vm.alloc(object{kind: oEnv, slot: objVal(b), parent: prev})
		prev = f
	}
	vm.baseEnv = prev
	vm.env = prev
	// top-level halt sentinel frame
	vm.frames = append(vm.frames, callFrame{ret: -1, env: prev})
	return vm
}

func sizeOf(o *object) int32 {
	sz := int32(56)
	switch o.kind {
	case oString:
		sz += int32(len(o.str))
	case oRecord:
		for _, f := range o.fields {
			sz += 24 + int32(len(f.name))
		}
	case oBuiltin:
		sz += int32(16 * len(o.bargs))
	}
	return sz
}

func (vm *vm) alloc(o object) int32 {
	o.mark = false
	o.free = false
	o.gen = 0
	sz := sizeOf(&o)
	o.size = sz
	var h int32
	if n := len(vm.freeList); n > 0 {
		h = vm.freeList[n-1]
		vm.freeList = vm.freeList[:n-1]
		vm.objs[h] = o
	} else {
		vm.objs = append(vm.objs, o)
		h = int32(len(vm.objs) - 1)
	}
	vm.liveBytes += int64(sz)
	vm.gen0Bytes += int64(sz)
	vm.gen0 = append(vm.gen0, h)
	if vm.liveBytes > vm.peakBytes {
		vm.peakBytes = vm.liveBytes
	}
	if vm.liveBytes > vm.hardCap {
		vm.oom = true
	}
	if vm.gen0Bytes > vm.nurseryLimit {
		vm.needMinor = true
	}
	return h
}

func (vm *vm) allocCons(h, t value) value { return objVal(vm.alloc(object{kind: oCons, head: h, tail: t})) }

func (vm *vm) writeBarrier(container int32, stored value) {
	if stored.tag == vObj && vm.objs[container].gen == 1 && vm.objs[stored.obj].gen == 0 {
		vm.remember = append(vm.remember, container)
	}
}

// ---------------------------------------------------------------------------
// execution
// ---------------------------------------------------------------------------

func (vm *vm) push(v value) { vm.stack = append(vm.stack, v) }
func (vm *vm) pop() value {
	n := len(vm.stack) - 1
	v := vm.stack[n]
	vm.stack = vm.stack[:n]
	return v
}

func (vm *vm) fail(msg string) {
	if vm.runErr == nil {
		vm.runErr = fmt.Errorf("runtime error: %s", msg)
	}
	vm.halt = true
}

func (vm *vm) run() (string, error) {
	code := vm.prog.code
	for !vm.halt {
		if vm.oom {
			vm.fail("heap limit exceeded (live set grew without bound)")
			break
		}
		if vm.needMinor {
			vm.minorGC()
			vm.needMinor = false
			if vm.gen1Bytes > vm.oldLimit {
				vm.majorGC()
			}
		}
		if vm.ip < 0 || vm.ip >= len(code) {
			break
		}
		inst := code[vm.ip]
		vm.ip++
		vm.exec(inst)
		if vm.runErr != nil {
			return "", vm.runErr
		}
	}
	if vm.runErr != nil {
		return "", vm.runErr
	}
	return vm.out.String(), nil
}

func (vm *vm) exec(inst instr) {
	switch inst.op {
	case opPushInt:
		vm.push(intVal(vm.prog.ints[inst.a]))
	case opPushBool:
		vm.push(boolVal(inst.a == 1))
	case opPushStr:
		vm.push(objVal(vm.alloc(object{kind: oString, str: vm.prog.strs[inst.a]})))
	case opVar:
		h := vm.env
		for k := 0; k < inst.a; k++ {
			h = vm.objs[h].parent
		}
		vm.push(vm.objs[h].slot)
	case opClosure:
		vm.push(objVal(vm.alloc(object{kind: oClosure, code: int32(inst.a), env: vm.env})))
	case opCall:
		vm.apply(false)
	case opTailCall:
		vm.apply(true)
	case opRet:
		f := vm.frames[len(vm.frames)-1]
		vm.frames = vm.frames[:len(vm.frames)-1]
		vm.env = f.env
		if f.ret < 0 {
			vm.halt = true
			return
		}
		vm.ip = f.ret
	case opJmp:
		vm.ip = inst.a
	case opJmpFalse:
		if vm.pop().i == 0 {
			vm.ip = inst.a
		}
	case opExtend:
		v := vm.pop()
		vm.env = vm.alloc(object{kind: oEnv, slot: v, parent: vm.env})
	case opShrink:
		vm.env = vm.objs[vm.env].parent
	case opRecSlot:
		v := vm.pop()
		vm.objs[vm.env].slot = v
		vm.writeBarrier(vm.env, v)
	case opIAdd:
		b := vm.pop()
		a := vm.pop()
		vm.push(intVal(a.i + b.i))
	case opISub:
		b := vm.pop()
		a := vm.pop()
		vm.push(intVal(a.i - b.i))
	case opIMul:
		b := vm.pop()
		a := vm.pop()
		vm.push(intVal(a.i * b.i))
	case opIDiv:
		b := vm.pop()
		a := vm.pop()
		if b.i == 0 {
			vm.fail("division by zero")
			return
		}
		vm.push(intVal(a.i / b.i))
	case opSCat:
		b := vm.pop()
		a := vm.pop()
		s := vm.objs[a.obj].str + vm.objs[b.obj].str
		vm.push(objVal(vm.alloc(object{kind: oString, str: s})))
	case opIEq:
		b := vm.pop()
		a := vm.pop()
		vm.push(boolVal(a.i == b.i))
	case opINe:
		b := vm.pop()
		a := vm.pop()
		vm.push(boolVal(a.i != b.i))
	case opILt:
		b := vm.pop()
		a := vm.pop()
		vm.push(boolVal(a.i < b.i))
	case opILe:
		b := vm.pop()
		a := vm.pop()
		vm.push(boolVal(a.i <= b.i))
	case opIGt:
		b := vm.pop()
		a := vm.pop()
		vm.push(boolVal(a.i > b.i))
	case opIGe:
		b := vm.pop()
		a := vm.pop()
		vm.push(boolVal(a.i >= b.i))
	case opINeg:
		a := vm.pop()
		vm.push(intVal(-a.i))
	case opIDeref:
		r := vm.pop()
		vm.push(vm.objs[r.obj].cell)
	case opSetRef:
		val := vm.pop()
		r := vm.pop()
		vm.objs[r.obj].cell = val
		vm.writeBarrier(r.obj, val)
		vm.push(val)
	case opMakeList:
		acc := objVal(vm.alloc(object{kind: oNil}))
		for k := 0; k < inst.a; k++ {
			e := vm.pop()
			acc = vm.allocCons(e, acc)
		}
		vm.push(acc)
	case opMakeRecord:
		names := vm.prog.recSpecs[inst.a]
		n := len(names)
		fields := make([]recField, n)
		for i := n - 1; i >= 0; i-- {
			fields[i] = recField{name: names[i], val: vm.pop()}
		}
		sortFields(fields)
		vm.push(objVal(vm.alloc(object{kind: oRecord, fields: fields})))
	case opField:
		name := vm.prog.strs[inst.a]
		r := vm.pop()
		o := &vm.objs[r.obj]
		for _, f := range o.fields {
			if f.name == name {
				vm.push(f.val)
				return
			}
		}
		vm.fail("field not found: " + name)
	case opUpdate:
		names := vm.prog.recSpecs[inst.a]
		n := len(names)
		newVals := make([]value, n)
		for i := n - 1; i >= 0; i-- {
			newVals[i] = vm.pop()
		}
		base := vm.pop()
		src := vm.objs[base.obj].fields
		fields := make([]recField, len(src))
		copy(fields, src)
		for i := 0; i < n; i++ {
			set := false
			for j := range fields {
				if fields[j].name == names[i] {
					fields[j].val = newVals[i]
					set = true
					break
				}
			}
			if !set {
				fields = append(fields, recField{name: names[i], val: newVals[i]})
			}
		}
		sortFields(fields)
		vm.push(objVal(vm.alloc(object{kind: oRecord, fields: fields})))
	default:
		vm.fail(fmt.Sprintf("bad opcode %d", inst.op))
	}
}

func (vm *vm) apply(tail bool) {
	arg := vm.pop()
	fn := vm.pop()
	if fn.tag != vObj {
		vm.fail("cannot apply a non-function")
		return
	}
	o := vm.objs[fn.obj]
	switch o.kind {
	case oClosure:
		frame := vm.alloc(object{kind: oEnv, slot: arg, parent: o.env})
		if !tail {
			vm.frames = append(vm.frames, callFrame{ret: vm.ip, env: vm.env})
		}
		vm.env = frame
		vm.ip = int(o.code)
	case oBuiltin:
		vm.applyBuiltin(o.bid, o.bargs, arg)
	default:
		vm.fail("cannot apply a non-function")
	}
}

func (vm *vm) applyBuiltin(bid int, bargs []value, arg value) {
	args := make([]value, 0, len(bargs)+1)
	args = append(args, bargs...)
	args = append(args, arg)
	if len(args) < builtinArity[bid] {
		vm.push(objVal(vm.alloc(object{kind: oBuiltin, bid: bid, bargs: args})))
		return
	}
	switch bid {
	case biPrint:
		vm.out.WriteString(vm.formatValue(args[0]))
		vm.out.WriteByte('\n')
		vm.push(args[0])
	case biCons:
		vm.push(vm.allocCons(args[0], args[1]))
	case biHead:
		o := vm.objs[args[0].obj]
		if o.kind == oNil {
			vm.fail("head of empty list")
			return
		}
		vm.push(o.head)
	case biTail:
		o := vm.objs[args[0].obj]
		if o.kind == oNil {
			vm.fail("tail of empty list")
			return
		}
		vm.push(o.tail)
	case biNull:
		vm.push(boolVal(vm.objs[args[0].obj].kind == oNil))
	case biNot:
		vm.push(boolVal(args[0].i == 0))
	case biRef:
		vm.push(objVal(vm.alloc(object{kind: oRef, cell: args[0]})))
	default:
		vm.fail("unknown builtin")
	}
}
