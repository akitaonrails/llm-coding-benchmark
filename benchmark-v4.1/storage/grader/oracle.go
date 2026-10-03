package grader

import (
	"encoding/binary"
	"fmt"
	"sort"
	"sync"
)

// ---------------------------------------------------------------------------
// Serializability oracle (multiversion serialization graph acyclicity).
//
// Every committed transaction records the keys it read (attributed to the exact
// writer whose value it observed) and the keys it wrote. Each write carries a
// globally unique id embedded in its value, so a read can be mapped to its
// writer unambiguously. The oracle builds the MVSG and reports whether it is
// acyclic; an acyclic MVSG is exactly a conflict-serializable history.
//
// Edges (over committed-txn nodes), for each key k:
//   wr: writer(v) -> reader       (reader observed version v written by writer)
//   rw: reader -> w'              (reader observed v; w' wrote a LATER version of k)
//   ww: w_i -> w_{i+1}            (consecutive writers of k, by commit order)
// A cycle means no serial order reproduces the observed reads -> not serializable.
// ---------------------------------------------------------------------------

// txnObs is one committed transaction's observations.
type txnObs struct {
	id     uint64            // unique id; also the id embedded in this txn's writes
	order  uint64            // real commit order (monotone)
	reads  map[string]uint64 // key -> id of the writer whose value was observed
	writes map[string]struct{}
}

// recorder collects committed transactions concurrently and hands out unique ids.
type recorder struct {
	mu     sync.Mutex
	nextID uint64
	ord    uint64
	txns   []txnObs
}

func newRecorder() *recorder { return &recorder{} }

func (r *recorder) newID() uint64 {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.nextID++
	return r.nextID
}

// commit records a committed transaction, stamping it with the next commit order.
func (r *recorder) commit(o txnObs) {
	r.mu.Lock()
	defer r.mu.Unlock()
	o.order = r.ord
	r.ord++
	r.txns = append(r.txns, o)
}

func (r *recorder) snapshot() []txnObs {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]txnObs, len(r.txns))
	copy(out, r.txns)
	return out
}

// encID embeds a writer id in a value (8-byte big-endian prefix).
func encID(id uint64) []byte {
	b := make([]byte, 8)
	binary.BigEndian.PutUint64(b, id)
	return b
}

// decID extracts the writer id embedded by encID (0 if absent/short).
func decID(b []byte) uint64 {
	if len(b) < 8 {
		return 0
	}
	return binary.BigEndian.Uint64(b[:8])
}

// checkSerializable reports whether the committed history is conflict-
// serializable. On failure it returns a human-readable cycle description.
func checkSerializable(txns []txnObs) (bool, string) {
	byID := make(map[uint64]*txnObs, len(txns))
	for i := range txns {
		byID[txns[i].id] = &txns[i]
	}

	// writers[k] = txn ids that wrote k, sorted by commit order.
	writers := map[string][]uint64{}
	for i := range txns {
		for k := range txns[i].writes {
			writers[k] = append(writers[k], txns[i].id)
		}
	}
	for k := range writers {
		ids := writers[k]
		sort.Slice(ids, func(a, b int) bool { return byID[ids[a]].order < byID[ids[b]].order })
		writers[k] = ids
	}

	adj := map[uint64]map[uint64]struct{}{}
	addEdge := func(from, to uint64) {
		if from == to {
			return
		}
		if adj[from] == nil {
			adj[from] = map[uint64]struct{}{}
		}
		adj[from][to] = struct{}{}
	}

	// ww edges
	for _, ids := range writers {
		for i := 0; i+1 < len(ids); i++ {
			addEdge(ids[i], ids[i+1])
		}
	}
	// wr + rw edges
	for i := range txns {
		r := &txns[i]
		for k, w := range r.reads {
			if w != 0 && w != r.id {
				addEdge(w, r.id) // wr: writer before reader
			}
			ids := writers[k]
			// find the observed writer's position; later writers get rw edges.
			pos := -1
			for p, id := range ids {
				if id == w {
					pos = p
					break
				}
			}
			start := 0
			if pos >= 0 {
				start = pos + 1
			}
			for p := start; p < len(ids); p++ {
				if ids[p] != r.id {
					addEdge(r.id, ids[p]) // rw: reader before any later writer
				}
			}
		}
	}

	// cycle detection (iterative DFS with colors)
	const (
		white = 0
		gray  = 1
		black = 2
	)
	color := map[uint64]int{}
	var stack []uint64

	var cyclePath string
	var dfs func(u uint64) bool
	dfs = func(u uint64) bool {
		color[u] = gray
		stack = append(stack, u)
		for v := range adj[u] {
			switch color[v] {
			case white:
				if dfs(v) {
					return true
				}
			case gray:
				// found a back edge: build the cycle description
				cyclePath = fmt.Sprintf("cycle involving txns %v -> %d", stack, v)
				return true
			}
		}
		stack = stack[:len(stack)-1]
		color[u] = black
		return false
	}

	// deterministic node iteration
	nodes := make([]uint64, 0, len(byID))
	for id := range byID {
		nodes = append(nodes, id)
	}
	sort.Slice(nodes, func(a, b int) bool { return byID[nodes[a]].order < byID[nodes[b]].order })
	for _, id := range nodes {
		if color[id] == white {
			stack = stack[:0]
			if dfs(id) {
				return false, cyclePath
			}
		}
	}
	return true, ""
}
