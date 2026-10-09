// Package ds — REFERENCE (quality==1.0 baseline). Order-statistics treap
// (split/merge) as a multiset keyed by value via harness.Cmp, plus a ring
// buffer of the window's values so Push can evict the oldest. insert/erase/kth
// are O(log size) comparisons; the naive baseline sorts the whole window per
// Kth. Treap priorities use a fixed seed so comparison counts are deterministic.
package ds

import "v42slidingkth/harness"

type node struct {
	key, prio, size int
	l, r            *node
}

func sz(n *node) int {
	if n == nil {
		return 0
	}
	return n.size
}

func upd(n *node) *node {
	n.size = 1 + sz(n.l) + sz(n.r)
	return n
}

// split t into (<= key if inclusive else < key) and the rest.
func split(t *node, key int, inclusive bool) (*node, *node) {
	if t == nil {
		return nil, nil
	}
	c := harness.Cmp(t.key, key)
	goLeft := c < 0 || (inclusive && c == 0) // t.key belongs to left part?
	if goLeft {
		l, r := split(t.r, key, inclusive)
		t.r = l
		return upd(t), r
	}
	l, r := split(t.l, key, inclusive)
	t.l = r
	return l, upd(t)
}

func merge(a, b *node) *node {
	if a == nil {
		return b
	}
	if b == nil {
		return a
	}
	if a.prio > b.prio {
		a.r = merge(a.r, b)
		return upd(a)
	}
	b.l = merge(a, b.l)
	return upd(b)
}

type rng struct{ s uint64 }

func (r *rng) next() int {
	r.s ^= r.s << 13
	r.s ^= r.s >> 7
	r.s ^= r.s << 17
	return int(r.s & 0x7fffffff)
}

type tree struct {
	root *node
	rnd  *rng
}

func (t *tree) insert(key int) {
	l, r := split(t.root, key, true) // l: <= key, r: > key
	n := upd(&node{key: key, prio: t.rnd.next()})
	t.root = merge(merge(l, n), r)
}

func (t *tree) erase(key int) {
	l, mid := split(t.root, key, false) // l: < key
	midEq, r := split(mid, key, true)   // midEq: == key, r: > key
	// drop one occurrence: merge the root's children
	if midEq != nil {
		midEq = merge(midEq.l, midEq.r)
	}
	t.root = merge(l, merge(midEq, r))
}

func (t *tree) kth(k int) int {
	n := t.root
	for n != nil {
		ls := sz(n.l)
		if k <= ls {
			n = n.l
		} else if k == ls+1 {
			return n.key
		} else {
			k -= ls + 1
			n = n.r
		}
	}
	return 0 // unreachable for valid k
}

type structure struct {
	w    int
	ring []int
	head int
	cnt  int
	tr   *tree
}

func New(w int) harness.Stream {
	return &structure{w: w, ring: make([]int, w), tr: &tree{rnd: &rng{s: 0x9e3779b97f4a7c15}}}
}

func (s *structure) Push(x int) {
	if s.cnt == s.w {
		old := s.ring[s.head]
		s.tr.erase(old)
		s.ring[s.head] = x
		s.head = (s.head + 1) % s.w
	} else {
		s.ring[(s.head+s.cnt)%s.w] = x
		s.cnt++
	}
	s.tr.insert(x)
}

func (s *structure) Kth(k int) int { return s.tr.kth(k) }
