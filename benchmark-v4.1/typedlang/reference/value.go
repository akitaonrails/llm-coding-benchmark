package reference

import (
	"sort"
	"strconv"
	"strings"
)

// value is a VM value. Integers and booleans are immediate; everything else is
// a handle (index) into the VM's managed heap so the GC can move/reclaim it.
type valTag uint8

const (
	vInt valTag = iota
	vBool
	vObj
)

type value struct {
	tag valTag
	i   int64 // int payload, or 0/1 for bool
	obj int32 // heap handle when tag==vObj, else -1
}

func intVal(n int64) value  { return value{tag: vInt, i: n, obj: -1} }
func boolVal(b bool) value  { v := value{tag: vBool, obj: -1}; if b { v.i = 1 }; return v }
func objVal(h int32) value  { return value{tag: vObj, i: 0, obj: h} }

type objKind uint8

const (
	oString objKind = iota
	oNil
	oCons
	oRecord
	oClosure
	oBuiltin
	oRef
	oEnv
)

type recField struct {
	name string
	val  value
}

// object is a tagged union of every heap-allocated value kind. A fat struct
// keeps the GC's child-enumeration simple (one switch) at a modest memory cost.
type object struct {
	kind objKind

	str string // oString

	head value // oCons
	tail value // oCons

	fields []recField // oRecord

	code int32 // oClosure: body address
	env  int32 // oClosure: captured env handle

	bid   int     // oBuiltin: builtin id
	bargs []value // oBuiltin: partially-applied args

	cell value // oRef

	slot   value // oEnv: the single binding
	parent int32 // oEnv: parent frame handle (-1 at base)

	// GC bookkeeping
	mark bool
	gen  uint8
	free bool
	size int32 // accounted bytes, set at allocation
}

// formatValue renders a value exactly per SPEC §5.
func (vm *vm) formatValue(v value) string {
	var b strings.Builder
	vm.writeValue(&b, v, 0)
	return b.String()
}

func (vm *vm) writeValue(b *strings.Builder, v value, depth int) {
	if depth > 10000 {
		b.WriteString("…")
		return
	}
	switch v.tag {
	case vInt:
		b.WriteString(strconv.FormatInt(v.i, 10))
		return
	case vBool:
		if v.i != 0 {
			b.WriteString("true")
		} else {
			b.WriteString("false")
		}
		return
	}
	o := &vm.objs[v.obj]
	switch o.kind {
	case oString:
		b.WriteString(quoteString(o.str))
	case oNil:
		b.WriteString("[]")
	case oCons:
		b.WriteByte('[')
		first := true
		cur := v
		for {
			co := &vm.objs[cur.obj]
			if co.kind == oNil {
				break
			}
			if !first {
				b.WriteString(", ")
			}
			first = false
			vm.writeValue(b, co.head, depth+1)
			cur = co.tail
		}
		b.WriteByte(']')
	case oRecord:
		b.WriteByte('{')
		// fields stored sorted; render in that order
		for i, f := range o.fields {
			if i > 0 {
				b.WriteString(", ")
			}
			b.WriteString(f.name)
			b.WriteString(" = ")
			vm.writeValue(b, f.val, depth+1)
		}
		b.WriteByte('}')
	case oRef:
		b.WriteString("<ref>")
	case oClosure, oBuiltin:
		b.WriteString("<fun>")
	default:
		b.WriteString("<?>")
	}
}

func quoteString(s string) string {
	var b strings.Builder
	b.WriteByte('"')
	for i := 0; i < len(s); i++ {
		switch s[i] {
		case '\n':
			b.WriteString(`\n`)
		case '\t':
			b.WriteString(`\t`)
		case '\\':
			b.WriteString(`\\`)
		case '"':
			b.WriteString(`\"`)
		default:
			b.WriteByte(s[i])
		}
	}
	b.WriteByte('"')
	return b.String()
}

func sortFields(fs []recField) {
	sort.Slice(fs, func(i, j int) bool { return fs[i].name < fs[j].name })
}
