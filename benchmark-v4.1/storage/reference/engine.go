// Package reference is a CORRECT, self-contained transactional storage engine
// used to validate the P2 grader. It is the mirror of the P1 reference: a
// concrete implementation driven by the hidden grader through a maker, with
// proven-negative "broken" variants under reference/broken/.
//
// It implements the CONTRACT.md surface (Open/Close, Begin, Txn.Get/Set/Delete/
// Commit/Abort/Scan, ErrSerializationFailure) with:
//
//   - On-disk durability via a write-ahead log (harness.SyncFile) with fsync on
//     commit, CRC+length-framed records, and crash recovery (WAL replay +
//     periodic compacting checkpoint to an on-disk data file — an LSM-style
//     memtable+SSTable+WAL arrangement, so storage is bounded, not an
//     unbounded in-RAM log).
//   - MVCC snapshot isolation: each Txn reads a stable snapshot fixed at Begin.
//   - Serializable Snapshot Isolation: at commit a transaction is certified
//     against every transaction that committed after its snapshot. It aborts
//     (ErrSerializationFailure) if a key or range it READ was written by such a
//     transaction (read-set validation — the SSI half that catches write skew,
//     the read-only anomaly and rw-dependency cycles) or if a key it WROTE was
//     written by such a transaction (first-committer-wins, the plain-SI half
//     that catches lost updates). The combination yields serializable
//     histories.
//
// The Knobs field lets the broken/ variants disable exactly one correctness
// mechanism each to produce proven negatives. Models must use plain Open.
package reference

import (
	"bytes"
	"encoding/binary"
	"errors"
	"hash/crc32"
	"os"
	"path/filepath"
	"sort"
	"sync"

	"v41store/harness"
)

// ErrSerializationFailure is returned by Commit when committing would break
// serializability; the caller is expected to retry the transaction.
var ErrSerializationFailure = errors.New("serialization failure")

// Knobs selectively disables correctness mechanisms to build proven-negative
// variants (see reference/broken/). A correct engine leaves every field false.
// This type is test-only scaffolding; model submissions must not use it.
type Knobs struct {
	DisableReadValidation  bool // drop SSI read-set certification (-> plain SI)
	DisableWriteWriteCheck bool // drop first-committer-wins (-> lost updates)
	DisableFsync           bool // never fsync the WAL (-> data not durable)
	DisableSnapshot        bool // reads see latest committed, not the snapshot
	CheckpointThreshold    int  // WAL bytes before an automatic checkpoint (0 = default)
}

const defaultCheckpointThreshold = 1 << 20 // 1 MiB

// ---------------------------------------------------------------------------
// MVCC store
// ---------------------------------------------------------------------------

type version struct {
	ts      uint64
	val     []byte
	deleted bool
}

type keyEntry struct {
	versions []version // ascending by ts
}

// DB is an open database. It is concrete (the grader wraps it in a thin shim,
// never forcing it to satisfy an interface — see NewHandle).
type DB struct {
	mu       sync.Mutex
	dir      string
	knobs    Knobs
	data     map[string]*keyEntry
	keys     []string // sorted, for Scan
	commitTS uint64   // last assigned commit timestamp (monotone)
	ckptTS   uint64   // timestamp of the last checkpoint (base in the data file)
	wal      *harness.SyncFile
	walBytes int
	history  []commitRec       // committed txns since the oldest active snapshot
	active   map[*Txn]struct{} // open transactions (for history/version pruning)
	closed   bool
}

type commitRec struct {
	ts        uint64
	writeKeys map[string]struct{}
}

// Open opens (creating if needed) a correct database rooted at dir, recovering
// from the WAL if present.
func Open(dir string) (*DB, error) { return OpenWithKnobs(dir, Knobs{}) }

// OpenWithKnobs is Open with correctness mechanisms selectively disabled. It
// backs the proven-negative variants.
func OpenWithKnobs(dir string, k Knobs) (*DB, error) {
	if k.CheckpointThreshold == 0 {
		k.CheckpointThreshold = defaultCheckpointThreshold
	}
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, err
	}
	db := &DB{
		dir:    dir,
		knobs:  k,
		data:   map[string]*keyEntry{},
		active: map[*Txn]struct{}{},
	}
	if err := db.loadCheckpoint(); err != nil {
		return nil, err
	}
	wal, err := harness.OpenSync(dir, "wal")
	if err != nil {
		return nil, err
	}
	db.wal = wal
	if err := db.replayWAL(); err != nil {
		return nil, err
	}
	return db, nil
}

// Close flushes a compacting checkpoint and closes the WAL.
func (db *DB) Close() error {
	db.mu.Lock()
	defer db.mu.Unlock()
	if db.closed {
		return nil
	}
	db.closed = true
	if err := db.checkpointLocked(); err != nil {
		db.wal.Close()
		return err
	}
	return db.wal.Close()
}

// ---------------------------------------------------------------------------
// Transactions
// ---------------------------------------------------------------------------

type writeOp struct {
	val     []byte
	deleted bool
}

type rng struct{ lo, hi []byte } // [lo, hi); nil lo = -inf, nil hi = +inf

// Txn is a transaction. Concrete, like DB.
type Txn struct {
	db         *DB
	readTS     uint64
	writes     map[string]*writeOp
	pointReads map[string]struct{}
	rangeReads []rng
	done       bool
}

// Begin starts a transaction on a stable snapshot (the latest committed state).
func (db *DB) Begin() *Txn {
	db.mu.Lock()
	defer db.mu.Unlock()
	t := &Txn{
		db:         db,
		readTS:     db.commitTS,
		writes:     map[string]*writeOp{},
		pointReads: map[string]struct{}{},
	}
	db.active[t] = struct{}{}
	return t
}

func (t *Txn) effReadTS() uint64 {
	if t.db.knobs.DisableSnapshot {
		return t.db.commitTS // broken: see latest committed instead of the snapshot
	}
	return t.readTS
}

// Get returns the value for key as of the transaction's snapshot, honoring the
// transaction's own buffered writes (read-your-writes).
func (t *Txn) Get(key []byte) (val []byte, ok bool) {
	k := string(key)
	if w, ok := t.writes[k]; ok {
		if w.deleted {
			return nil, false
		}
		return clone(w.val), true
	}
	t.db.mu.Lock()
	defer t.db.mu.Unlock()
	t.pointReads[k] = struct{}{}
	return t.db.readAtLocked(k, t.effReadTS())
}

// Set buffers a write; it becomes visible only on Commit.
func (t *Txn) Set(key, val []byte) {
	t.writes[string(key)] = &writeOp{val: clone(val)}
}

// Delete buffers a deletion.
func (t *Txn) Delete(key []byte) {
	t.writes[string(key)] = &writeOp{deleted: true}
}

// Scan iterates [lo, hi) in key order over the snapshot merged with buffered
// writes, calling fn until it returns false. The scanned range is recorded as a
// read predicate for SSI certification.
func (t *Txn) Scan(lo, hi []byte, fn func(key, val []byte) bool) {
	type kv struct {
		k, v []byte
	}
	t.db.mu.Lock()
	ts := t.effReadTS()
	t.rangeReads = append(t.rangeReads, rng{clone(lo), clone(hi)})

	seen := map[string]struct{}{}
	var out []kv
	// buffered writes in range
	for k, w := range t.writes {
		if inRange(k, lo, hi) {
			seen[k] = struct{}{}
			if !w.deleted {
				out = append(out, kv{[]byte(k), clone(w.val)})
			}
		}
	}
	// snapshot keys in range
	for _, k := range t.db.keys {
		if !inRange(k, lo, hi) {
			continue
		}
		if _, dup := seen[k]; dup {
			continue
		}
		if v, ok := t.db.readAtLocked(k, ts); ok {
			out = append(out, kv{[]byte(k), v})
		}
	}
	t.db.mu.Unlock()

	sort.Slice(out, func(i, j int) bool { return bytes.Compare(out[i].k, out[j].k) < 0 })
	for _, e := range out {
		if !fn(e.k, e.v) {
			break
		}
	}
}

// Abort discards the transaction.
func (t *Txn) Abort() {
	if t.done {
		return
	}
	t.done = true
	t.db.mu.Lock()
	delete(t.db.active, t)
	t.db.pruneLocked()
	t.db.mu.Unlock()
}

// Commit certifies and durably commits the transaction, or returns
// ErrSerializationFailure (and aborts) if committing would break
// serializability.
func (t *Txn) Commit() error {
	if t.done {
		return nil
	}
	db := t.db
	db.mu.Lock()
	defer db.mu.Unlock()
	t.done = true
	delete(db.active, t)

	if err := t.certifyLocked(); err != nil {
		db.pruneLocked()
		return err
	}

	// Read-only transactions that pass certification need no log record.
	if len(t.writes) == 0 {
		db.pruneLocked()
		return nil
	}

	ts := db.commitTS + 1
	if err := db.walAppendCommit(ts, t.writes); err != nil {
		// A real I/O error (not a simulated crash, which panics). Leave the
		// transaction aborted; nothing was applied.
		return err
	}
	db.applyLocked(ts, t.writes)
	db.commitTS = ts
	db.history = append(db.history, commitRec{ts: ts, writeKeys: keySet(t.writes)})
	db.pruneLocked()

	if db.walBytes >= db.knobs.CheckpointThreshold {
		if err := db.checkpointLocked(); err != nil {
			return err
		}
	}
	return nil
}

// certifyLocked implements SSI certification against transactions that
// committed after this one's snapshot.
func (t *Txn) certifyLocked() error {
	db := t.db
	for _, rec := range db.history {
		if rec.ts <= t.readTS {
			continue // committed before our snapshot: not concurrent
		}
		// SSI read-set validation (catches write skew / rw-cycles / read-only anomaly).
		if !db.knobs.DisableReadValidation {
			for k := range t.pointReads {
				if _, hit := rec.writeKeys[k]; hit {
					return ErrSerializationFailure
				}
			}
			for _, r := range t.rangeReads {
				for wk := range rec.writeKeys {
					if inRange(wk, r.lo, r.hi) {
						return ErrSerializationFailure
					}
				}
			}
		}
		// First-committer-wins write-write check (catches lost updates).
		if !db.knobs.DisableWriteWriteCheck {
			for k := range t.writes {
				if _, hit := rec.writeKeys[k]; hit {
					return ErrSerializationFailure
				}
			}
		}
	}
	return nil
}

// ---------------------------------------------------------------------------
// MVCC read/apply
// ---------------------------------------------------------------------------

func (db *DB) readAtLocked(k string, ts uint64) ([]byte, bool) {
	e := db.data[k]
	if e == nil {
		return nil, false
	}
	// newest version with v.ts <= ts
	for i := len(e.versions) - 1; i >= 0; i-- {
		v := e.versions[i]
		if v.ts <= ts {
			if v.deleted {
				return nil, false
			}
			return clone(v.val), true
		}
	}
	return nil, false
}

func (db *DB) applyLocked(ts uint64, writes map[string]*writeOp) {
	for k, w := range writes {
		e := db.data[k]
		if e == nil {
			e = &keyEntry{}
			db.data[k] = e
			db.insertKeyLocked(k)
		}
		e.versions = append(e.versions, version{ts: ts, val: clone(w.val), deleted: w.deleted})
	}
}

func (db *DB) insertKeyLocked(k string) {
	i := sort.SearchStrings(db.keys, k)
	if i < len(db.keys) && db.keys[i] == k {
		return
	}
	db.keys = append(db.keys, "")
	copy(db.keys[i+1:], db.keys[i:])
	db.keys[i] = k
}

// pruneLocked bounds memory: it drops history entries and old versions no
// active snapshot can still observe.
func (db *DB) pruneLocked() {
	minTS := db.commitTS
	for t := range db.active {
		if t.readTS < minTS {
			minTS = t.readTS
		}
	}
	// history: an active txn with snapshot R only certifies against ts > R, so
	// records with ts <= minTS are unreachable.
	keep := db.history[:0]
	for _, r := range db.history {
		if r.ts > minTS {
			keep = append(keep, r)
		}
	}
	db.history = keep
	// versions: keep the newest version with ts <= minTS (what the oldest
	// snapshot sees) plus everything newer.
	for _, e := range db.data {
		cut := 0
		for i, v := range e.versions {
			if v.ts <= minTS {
				cut = i
			}
		}
		if cut > 0 {
			e.versions = append(e.versions[:0], e.versions[cut:]...)
		}
	}
}

// ---------------------------------------------------------------------------
// WAL + recovery + checkpoint
// ---------------------------------------------------------------------------
//
// WAL record layout (one per committed txn):
//   [u32 payloadLen][u32 crc32(payload)][payload]
// payload:
//   [u64 ts][u32 count]{ [u8 op][u32 klen][key][u32 vlen][val] }   op: 0=set 1=del

var crcTab = crc32.MakeTable(crc32.Castagnoli)

func (db *DB) walAppendCommit(ts uint64, writes map[string]*writeOp) error {
	payload := encodeTxn(ts, writes)
	rec := make([]byte, 8+len(payload))
	binary.BigEndian.PutUint32(rec[0:4], uint32(len(payload)))
	binary.BigEndian.PutUint32(rec[4:8], crc32.Checksum(payload, crcTab))
	copy(rec[8:], payload)

	db.wal.Reached("commit.beforeWrite")
	if _, err := db.wal.Append(rec); err != nil {
		return err
	}
	db.wal.Reached("commit.beforeFsync")
	if !db.knobs.DisableFsync {
		if err := db.wal.Sync(); err != nil {
			return err
		}
	}
	db.wal.Reached("commit.afterFsync")
	db.walBytes += len(rec)
	return nil
}

func encodeTxn(ts uint64, writes map[string]*writeOp) []byte {
	var b bytes.Buffer
	var u8 [8]byte
	binary.BigEndian.PutUint64(u8[:], ts)
	b.Write(u8[:])
	putU32(&b, uint32(len(writes)))
	// deterministic key order for reproducibility
	ks := make([]string, 0, len(writes))
	for k := range writes {
		ks = append(ks, k)
	}
	sort.Strings(ks)
	for _, k := range ks {
		w := writes[k]
		if w.deleted {
			b.WriteByte(1)
		} else {
			b.WriteByte(0)
		}
		putU32(&b, uint32(len(k)))
		b.WriteString(k)
		putU32(&b, uint32(len(w.val)))
		b.Write(w.val)
	}
	return b.Bytes()
}

func (db *DB) replayWAL() error {
	buf, err := db.wal.ReadAll()
	if err != nil {
		return err
	}
	off := 0
	for off+8 <= len(buf) {
		plen := int(binary.BigEndian.Uint32(buf[off : off+4]))
		crc := binary.BigEndian.Uint32(buf[off+4 : off+8])
		if off+8+plen > len(buf) {
			break // torn tail: incomplete record, discard
		}
		payload := buf[off+8 : off+8+plen]
		if crc32.Checksum(payload, crcTab) != crc {
			break // torn tail: corrupt record, discard
		}
		ts, writes, ok := decodeTxn(payload)
		if !ok {
			break
		}
		db.applyLocked(ts, writesToOps(writes))
		if ts > db.commitTS {
			db.commitTS = ts
		}
		off += 8 + plen
	}
	return nil
}

func decodeTxn(p []byte) (ts uint64, writes map[string]*writeOp, ok bool) {
	defer func() {
		if recover() != nil {
			ok = false
		}
	}()
	ts = binary.BigEndian.Uint64(p[0:8])
	off := 8
	count := int(binary.BigEndian.Uint32(p[off : off+4]))
	off += 4
	writes = make(map[string]*writeOp, count)
	for i := 0; i < count; i++ {
		del := p[off] == 1
		off++
		klen := int(binary.BigEndian.Uint32(p[off : off+4]))
		off += 4
		k := string(p[off : off+klen])
		off += klen
		vlen := int(binary.BigEndian.Uint32(p[off : off+4]))
		off += 4
		v := append([]byte(nil), p[off:off+vlen]...)
		off += vlen
		writes[k] = &writeOp{val: v, deleted: del}
	}
	return ts, writes, true
}

func writesToOps(w map[string]*writeOp) map[string]*writeOp { return w }

// checkpointLocked writes a compacting snapshot of the live state to the data
// file (temp + rename for atomicity), then truncates the WAL. Crash-safe: if we
// crash before the WAL truncate, recovery re-applies the (idempotent) WAL on
// top of the checkpoint.
func (db *DB) checkpointLocked() error {
	type kv struct {
		k string
		v []byte
	}
	var live []kv
	for _, k := range db.keys {
		if v, ok := db.readAtLocked(k, db.commitTS); ok {
			live = append(live, kv{k, v})
		}
	}
	var b bytes.Buffer
	var u8 [8]byte
	binary.BigEndian.PutUint64(u8[:], db.commitTS)
	b.Write(u8[:])
	putU32(&b, uint32(len(live)))
	for _, e := range live {
		putU32(&b, uint32(len(e.k)))
		b.WriteString(e.k)
		putU32(&b, uint32(len(e.v)))
		b.Write(e.v)
	}

	tmp := filepath.Join(db.dir, "data.tmp")
	final := filepath.Join(db.dir, "data")
	if err := os.WriteFile(tmp, b.Bytes(), 0o644); err != nil {
		return err
	}
	if f, err := os.Open(tmp); err == nil {
		_ = f.Sync()
		_ = f.Close()
	}
	if err := os.Rename(tmp, final); err != nil {
		return err
	}
	if d, err := os.Open(db.dir); err == nil {
		_ = d.Sync()
		_ = d.Close()
	}
	// Now that the checkpoint is durable, the WAL prefix is redundant.
	if err := db.wal.Truncate(0); err != nil {
		return err
	}
	db.walBytes = 0
	db.ckptTS = db.commitTS
	// collapse MVCC to the checkpointed state
	db.pruneLocked()
	return nil
}

func (db *DB) loadCheckpoint() error {
	buf, err := os.ReadFile(filepath.Join(db.dir, "data"))
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	if len(buf) < 12 {
		return nil
	}
	ts := binary.BigEndian.Uint64(buf[0:8])
	off := 8
	count := int(binary.BigEndian.Uint32(buf[off : off+4]))
	off += 4
	for i := 0; i < count; i++ {
		klen := int(binary.BigEndian.Uint32(buf[off : off+4]))
		off += 4
		k := string(buf[off : off+klen])
		off += klen
		vlen := int(binary.BigEndian.Uint32(buf[off : off+4]))
		off += 4
		v := append([]byte(nil), buf[off:off+vlen]...)
		off += vlen
		e := &keyEntry{versions: []version{{ts: ts, val: v}}}
		db.data[k] = e
		db.insertKeyLocked(k)
	}
	db.commitTS = ts
	db.ckptTS = ts
	return nil
}

// ---------------------------------------------------------------------------
// Grader shim (the per-engine adapter; a model submission ships its own copy in
// its wiring _test.go — the engine itself stays concrete).
// ---------------------------------------------------------------------------

// NewHandle adapts a concrete *DB to the grader's harness.DBHandle. It is the
// canonical ~20-line shim the run harness replicates for each model.
func NewHandle(db *DB) harness.DBHandle { return dbShim{db} }

type dbShim struct{ db *DB }

func (s dbShim) Begin() harness.TxnHandle { return txShim{s.db.Begin()} }
func (s dbShim) Close() error             { return s.db.Close() }

type txShim struct{ tx *Txn }

func (t txShim) Get(k []byte) ([]byte, bool)                   { return t.tx.Get(k) }
func (t txShim) Set(k, v []byte)                               { t.tx.Set(k, v) }
func (t txShim) Delete(k []byte)                               { t.tx.Delete(k) }
func (t txShim) Commit() error                                 { return t.tx.Commit() }
func (t txShim) Abort()                                        { t.tx.Abort() }
func (t txShim) Scan(lo, hi []byte, fn func(k, v []byte) bool) { t.tx.Scan(lo, hi, fn) }

// ---------------------------------------------------------------------------
// small helpers
// ---------------------------------------------------------------------------

func clone(b []byte) []byte {
	if b == nil {
		return nil
	}
	c := make([]byte, len(b))
	copy(c, b)
	return c
}

func keySet(w map[string]*writeOp) map[string]struct{} {
	s := make(map[string]struct{}, len(w))
	for k := range w {
		s[k] = struct{}{}
	}
	return s
}

// inRange reports whether k is in [lo, hi) (nil lo = -inf, nil hi = +inf).
func inRange(k string, lo, hi []byte) bool {
	if lo != nil && bytes.Compare([]byte(k), lo) < 0 {
		return false
	}
	if hi != nil && bytes.Compare([]byte(k), hi) >= 0 {
		return false
	}
	return true
}

func putU32(b *bytes.Buffer, v uint32) {
	var u [4]byte
	binary.BigEndian.PutUint32(u[:], v)
	b.Write(u[:])
}
