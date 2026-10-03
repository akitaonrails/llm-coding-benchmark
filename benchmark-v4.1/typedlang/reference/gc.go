package reference

// Generational mark-sweep collector.
//
//   - Fresh objects are allocated in the nursery (gen 0). A minor collection
//     traces the nursery from the VM roots plus the write-barrier remembered set
//     (old->young pointers), frees nursery garbage, and promotes survivors to
//     the old generation (gen 1).
//   - A major collection traces the whole heap from the roots and reclaims
//     everything unreachable, INCLUDING cycles (a tracing collector collects
//     cycles for free). It runs when the old generation outgrows a target that
//     grows after each major, so a heap that genuinely needs the memory does not
//     thrash.
//
// Options.GCCollect and Options.GCCycles gate the sweep policy so the broken
// variants can model "never frees" and "refcount-only (leaks cycles)".

// forEachChild invokes add on every heap handle this object references.
func (vm *vm) forEachChild(h int32, add func(int32)) {
	o := &vm.objs[h]
	addVal := func(v value) {
		if v.tag == vObj {
			add(v.obj)
		}
	}
	switch o.kind {
	case oCons:
		addVal(o.head)
		addVal(o.tail)
	case oRecord:
		for _, f := range o.fields {
			addVal(f.val)
		}
	case oClosure:
		add(o.env)
	case oBuiltin:
		for _, a := range o.bargs {
			addVal(a)
		}
	case oRef:
		addVal(o.cell)
	case oEnv:
		addVal(o.slot)
		if o.parent >= 0 {
			add(o.parent)
		}
	}
}

// rootHandles returns the VM's root object handles (operand stack, current and
// saved environments, base env).
func (vm *vm) rootHandles(add func(int32)) {
	for _, v := range vm.stack {
		if v.tag == vObj {
			add(v.obj)
		}
	}
	if vm.env >= 0 {
		add(vm.env)
	}
	for _, f := range vm.frames {
		if f.env >= 0 {
			add(f.env)
		}
	}
	if vm.baseEnv >= 0 {
		add(vm.baseEnv)
	}
}

func (vm *vm) freeObj(h int32) {
	o := &vm.objs[h]
	if o.free {
		return
	}
	sz := int64(o.size)
	vm.liveBytes -= sz
	if o.gen == 0 {
		vm.gen0Bytes -= sz
	} else {
		vm.gen1Bytes -= sz
	}
	*o = object{free: true}
	vm.freeList = append(vm.freeList, h)
}

// selectFreeable returns the subset of garbage that policy permits freeing.
// GCCollect=false frees nothing. GCCycles=true frees all garbage. Otherwise a
// reference-count emulation frees only garbage with no incoming edge from other
// garbage (acyclic garbage), leaking cycles — exactly a refcount collector.
func (vm *vm) selectFreeable(garbage []int32) []int32 {
	if !vm.opts.GCCollect {
		return nil
	}
	if vm.opts.GCCycles {
		return garbage
	}
	inSet := make(map[int32]bool, len(garbage))
	for _, h := range garbage {
		inSet[h] = true
	}
	indeg := make(map[int32]int, len(garbage))
	for _, h := range garbage {
		vm.forEachChild(h, func(c int32) {
			if inSet[c] {
				indeg[c]++
			}
		})
	}
	var queue []int32
	for _, h := range garbage {
		if indeg[h] == 0 {
			queue = append(queue, h)
		}
	}
	var out []int32
	for len(queue) > 0 {
		h := queue[len(queue)-1]
		queue = queue[:len(queue)-1]
		out = append(out, h)
		vm.forEachChild(h, func(c int32) {
			if inSet[c] {
				indeg[c]--
				if indeg[c] == 0 {
					queue = append(queue, c)
				}
			}
		})
	}
	return out // objects still with indeg>0 are in cycles -> leaked
}

// minorGC collects the nursery.
func (vm *vm) minorGC() {
	vm.numGC++
	// clear marks on nursery candidates
	for _, h := range vm.gen0 {
		if !vm.objs[h].free {
			vm.objs[h].mark = false
		}
	}
	// mark young reachable from roots and the remembered set
	var work []int32
	enqueue := func(h int32) { work = append(work, h) }
	vm.rootHandles(enqueue)
	for _, h := range vm.remember {
		if h < 0 || int(h) >= len(vm.objs) || vm.objs[h].free || vm.objs[h].gen != 1 {
			continue
		}
		vm.forEachChild(h, enqueue)
	}
	for len(work) > 0 {
		h := work[len(work)-1]
		work = work[:len(work)-1]
		o := &vm.objs[h]
		if o.free || o.gen != 0 || o.mark {
			continue // old objects are kept implicitly; don't trace through them
		}
		o.mark = true
		vm.forEachChild(h, enqueue)
	}
	// garbage = unmarked nursery
	var garbage []int32
	for _, h := range vm.gen0 {
		if !vm.objs[h].free && !vm.objs[h].mark {
			garbage = append(garbage, h)
		}
	}
	for _, h := range vm.selectFreeable(garbage) {
		vm.freeObj(h)
	}
	// promote every surviving (or retained-leaked) nursery object to old gen
	for _, h := range vm.gen0 {
		o := &vm.objs[h]
		if o.free {
			continue
		}
		o.gen = 1
		o.mark = false
		sz := int64(o.size)
		vm.gen0Bytes -= sz
		vm.gen1Bytes += sz
		vm.gen1 = append(vm.gen1, h)
	}
	vm.gen0 = vm.gen0[:0]
	vm.gen0Bytes = 0
	vm.remember = vm.remember[:0]
}

// majorGC traces the whole heap and reclaims all unreachable objects (cycles
// included), then retargets the old-gen trigger.
func (vm *vm) majorGC() {
	vm.numGC++
	for i := range vm.objs {
		if !vm.objs[i].free {
			vm.objs[i].mark = false
		}
	}
	var work []int32
	enqueue := func(h int32) { work = append(work, h) }
	vm.rootHandles(enqueue)
	for len(work) > 0 {
		h := work[len(work)-1]
		work = work[:len(work)-1]
		o := &vm.objs[h]
		if o.free || o.mark {
			continue
		}
		o.mark = true
		vm.forEachChild(h, enqueue)
	}
	var garbage []int32
	for i := range vm.objs {
		o := &vm.objs[i]
		if !o.free && !o.mark {
			garbage = append(garbage, int32(i))
		}
	}
	for _, h := range vm.selectFreeable(garbage) {
		vm.freeObj(h)
	}
	// rebuild generation lists / byte counts from survivors
	vm.gen0 = vm.gen0[:0]
	vm.gen1 = vm.gen1[:0]
	vm.gen0Bytes = 0
	vm.gen1Bytes = 0
	for i := range vm.objs {
		o := &vm.objs[i]
		if o.free {
			continue
		}
		o.mark = false
		if o.gen == 0 {
			vm.gen0 = append(vm.gen0, int32(i))
			vm.gen0Bytes += int64(o.size)
		} else {
			vm.gen1 = append(vm.gen1, int32(i))
			vm.gen1Bytes += int64(o.size)
		}
	}
	vm.remember = vm.remember[:0]
	// grow the old-gen target so a heap that truly needs memory won't thrash
	// (and a leaking collector reaches the hard cap in O(log) majors).
	target := vm.gen1Bytes * 2
	if target < 8<<20 {
		target = 8 << 20
	}
	vm.oldLimit = target
}
