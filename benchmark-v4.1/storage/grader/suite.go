// Package grader is the hidden gauntlet for the P2 transactional
// storage-engine benchmark. Every test is parameterized as RunX(t, mk) taking a
// harness.Maker, so the reference (wired in ref_test.go) and later model
// submissions are driven identically. Each test is meant to run as its own
// `go test -run` with a bounded timeout, so one deadlocking test fails only
// itself.
package grader

import (
	"fmt"
	"strconv"
	"sync"
	"testing"

	"v41store/harness"
)

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

func openDB(t *testing.T, mk harness.Maker, dir string) harness.DBHandle {
	t.Helper()
	db, err := mk.Open(dir)
	if err != nil {
		t.Fatalf("Open(%s): %v", dir, err)
	}
	return db
}

// putCommit writes key=val in its own committed transaction (retrying on a
// serialization failure, which a single-writer put should never actually hit).
func putCommit(t *testing.T, mk harness.Maker, db harness.DBHandle, key, val []byte) {
	t.Helper()
	for i := 0; i < 100; i++ {
		tx := db.Begin()
		tx.Set(key, val)
		err := tx.Commit()
		if err == nil {
			return
		}
		if mk.IsSerErr(err) {
			continue
		}
		t.Fatalf("Commit put %q: %v", key, err)
	}
	t.Fatalf("put %q never committed", key)
}

func getVal(db harness.DBHandle, key []byte) ([]byte, bool) {
	tx := db.Begin()
	v, ok := tx.Get(key)
	tx.Abort()
	return v, ok
}

func atoi(t *testing.T, b []byte) int {
	n, err := strconv.Atoi(string(b))
	if err != nil {
		t.Fatalf("bad int value %q: %v", b, err)
	}
	return n
}

func itob(n int) []byte { return []byte(strconv.Itoa(n)) }

// ---------------------------------------------------------------------------
// Durability / recovery
// ---------------------------------------------------------------------------

// RunBasicPutGet: single-transaction correctness, plus a clean Close/reopen
// (exercising the checkpoint-on-close + reload path).
func RunBasicPutGet(t *testing.T, mk harness.Maker) {
	dir := harness.TempDir(t)
	db := openDB(t, mk, dir)

	tx := db.Begin()
	tx.Set([]byte("a"), []byte("1"))
	tx.Set([]byte("b"), []byte("2"))
	if v, ok := tx.Get([]byte("a")); !ok || string(v) != "1" {
		t.Fatalf("read-your-write a: %q %v", v, ok)
	}
	if err := tx.Commit(); err != nil {
		t.Fatalf("commit: %v", err)
	}
	if v, ok := getVal(db, []byte("a")); !ok || string(v) != "1" {
		t.Fatalf("get a: %q %v", v, ok)
	}
	// delete
	tx = db.Begin()
	tx.Delete([]byte("a"))
	if err := tx.Commit(); err != nil {
		t.Fatalf("commit delete: %v", err)
	}
	if _, ok := getVal(db, []byte("a")); ok {
		t.Fatalf("a should be deleted")
	}
	if v, ok := getVal(db, []byte("b")); !ok || string(v) != "2" {
		t.Fatalf("get b: %q %v", v, ok)
	}

	// clean close + reopen: b survives, a stays deleted
	if err := db.Close(); err != nil {
		t.Fatalf("close: %v", err)
	}
	db2 := openDB(t, mk, dir)
	defer db2.Close()
	if _, ok := getVal(db2, []byte("a")); ok {
		t.Fatalf("a resurrected after reopen")
	}
	if v, ok := getVal(db2, []byte("b")); !ok || string(v) != "2" {
		t.Fatalf("get b after reopen: %q %v", v, ok)
	}
}

// RunScan: ordered range scan over a snapshot, merged with buffered writes.
func RunScan(t *testing.T, mk harness.Maker) {
	dir := harness.TempDir(t)
	db := openDB(t, mk, dir)
	defer db.Close()

	tx := db.Begin()
	for _, k := range []string{"d", "b", "f", "a", "c", "e"} {
		tx.Set([]byte(k), []byte("v"+k))
	}
	if err := tx.Commit(); err != nil {
		t.Fatalf("commit: %v", err)
	}

	// full scan ordered
	var got []string
	tx = db.Begin()
	tx.Scan(nil, nil, func(k, v []byte) bool { got = append(got, string(k)); return true })
	tx.Abort()
	want := []string{"a", "b", "c", "d", "e", "f"}
	if fmt.Sprint(got) != fmt.Sprint(want) {
		t.Fatalf("full scan order: got %v want %v", got, want)
	}

	// bounded [b, e): b,c,d
	got = nil
	tx = db.Begin()
	tx.Scan([]byte("b"), []byte("e"), func(k, v []byte) bool { got = append(got, string(k)); return true })
	tx.Abort()
	if fmt.Sprint(got) != fmt.Sprint([]string{"b", "c", "d"}) {
		t.Fatalf("bounded scan: got %v", got)
	}

	// scan sees buffered writes + deletions within the same txn
	got = nil
	tx = db.Begin()
	tx.Set([]byte("aa"), []byte("x"))
	tx.Delete([]byte("c"))
	tx.Scan([]byte("a"), []byte("d"), func(k, v []byte) bool { got = append(got, string(k)); return true })
	tx.Abort()
	if fmt.Sprint(got) != fmt.Sprint([]string{"a", "aa", "b"}) {
		t.Fatalf("scan with buffered writes: got %v", got)
	}
}

// RunCommitDurable: commit, crash (discard + reopen), value present.
func RunCommitDurable(t *testing.T, mk harness.Maker) {
	dir := harness.TempDir(t)
	db := openDB(t, mk, dir)

	tx := db.Begin()
	tx.Set([]byte("k"), []byte("v"))
	if err := tx.Commit(); err != nil {
		t.Fatalf("commit: %v", err)
	}

	harness.SimulateCrash(dir) // power loss: un-fsynced bytes lost
	_ = db                     // old handle abandoned

	db2 := openDB(t, mk, dir)
	defer db2.Close()
	if v, ok := getVal(db2, []byte("k")); !ok || string(v) != "v" {
		t.Fatalf("committed value lost after crash: %q %v", v, ok)
	}
}

// RunAbortNoTrace: aborted and in-flight transactions leave nothing after a crash.
func RunAbortNoTrace(t *testing.T, mk harness.Maker) {
	dir := harness.TempDir(t)
	db := openDB(t, mk, dir)

	putCommit(t, mk, db, []byte("keep"), []byte("1")) // durable survivor

	tx := db.Begin()
	tx.Set([]byte("aborted"), []byte("x"))
	tx.Abort()

	inflight := db.Begin()
	inflight.Set([]byte("inflight"), []byte("y")) // never committed

	harness.SimulateCrash(dir)
	_ = inflight

	db2 := openDB(t, mk, dir)
	defer db2.Close()
	if v, ok := getVal(db2, []byte("keep")); !ok || string(v) != "1" {
		t.Fatalf("committed survivor lost: %q %v", v, ok)
	}
	if _, ok := getVal(db2, []byte("aborted")); ok {
		t.Fatalf("aborted write survived crash")
	}
	if _, ok := getVal(db2, []byte("inflight")); ok {
		t.Fatalf("in-flight write survived crash")
	}
}

// RunCrashMidCommitAtomic: a crash injected at many points across a commit is
// all-or-nothing, and prior committed state is never damaged.
func RunCrashMidCommitAtomic(t *testing.T, mk harness.Maker) {
	points := []struct {
		name   string
		policy harness.Policy
	}{
		{"commit.beforeWrite", harness.CrashHard},
		{"commit.beforeFsync", harness.CrashHard},
		{"commit.afterFsync", harness.CrashHard},
		{"wal.torn", harness.CrashTorn},
	}
	for _, p := range points {
		t.Run(p.name, func(t *testing.T) {
			dir := harness.TempDir(t)
			db := openDB(t, mk, dir)

			// durable prior state
			putCommit(t, mk, db, []byte("a"), []byte("1"))

			harness.ArmCrash(dir, p.name, p.policy)
			crashed := harness.RunMaybeCrash(func() {
				tx := db.Begin()
				tx.Set([]byte("a"), []byte("99"))
				tx.Set([]byte("b"), []byte("2"))
				_ = tx.Commit()
			})
			harness.DisarmAll(dir)
			if !crashed {
				t.Fatalf("%s: commit was not interrupted (failpoint never reached)", p.name)
			}

			db2 := openDB(t, mk, dir)
			va, okA := getVal(db2, []byte("a"))
			vb, okB := getVal(db2, []byte("b"))
			db2.Close()

			committed := okA && string(va) == "99" && okB && string(vb) == "2"
			absent := okA && string(va) == "1" && !okB
			if !committed && !absent {
				t.Fatalf("%s: torn commit: a=(%q,%v) b=(%q,%v) — neither all nor nothing",
					p.name, va, okA, vb, okB)
			}
		})
	}
}

// RunRecoveryManyTxns: N committed transactions survive a crash exactly.
func RunRecoveryManyTxns(t *testing.T, mk harness.Maker) {
	const N = 300
	dir := harness.TempDir(t)
	db := openDB(t, mk, dir)
	for i := 0; i < N; i++ {
		putCommit(t, mk, db, itob(i), itob(i*7))
	}
	harness.SimulateCrash(dir)

	db2 := openDB(t, mk, dir)
	defer db2.Close()
	for i := 0; i < N; i++ {
		v, ok := getVal(db2, itob(i))
		if !ok || atoi(t, v) != i*7 {
			t.Fatalf("key %d: got (%q,%v) want %d", i, v, ok, i*7)
		}
	}
	// count via scan
	n := 0
	tx := db2.Begin()
	tx.Scan(nil, nil, func(k, v []byte) bool { n++; return true })
	tx.Abort()
	if n != N {
		t.Fatalf("recovered %d keys, want %d", n, N)
	}
}

// ---------------------------------------------------------------------------
// Isolation (SI then SSI)
// ---------------------------------------------------------------------------

// RunSnapshotIsolation: a transaction sees a stable snapshot despite a
// concurrent commit (no non-repeatable / dirty reads).
func RunSnapshotIsolation(t *testing.T, mk harness.Maker) {
	dir := harness.TempDir(t)
	db := openDB(t, mk, dir)
	defer db.Close()

	putCommit(t, mk, db, []byte("k"), []byte("1"))

	t1 := db.Begin() // snapshot at k=1
	if v, ok := t1.Get([]byte("k")); !ok || string(v) != "1" {
		t.Fatalf("t1 initial read: %q %v", v, ok)
	}

	// concurrent writer commits k=2
	t2 := db.Begin()
	t2.Set([]byte("k"), []byte("2"))
	if err := t2.Commit(); err != nil {
		t.Fatalf("t2 commit: %v", err)
	}

	// t1 must still observe its snapshot
	if v, ok := t1.Get([]byte("k")); !ok || string(v) != "1" {
		t.Fatalf("snapshot not stable: t1 sees %q (ok=%v), want 1", v, ok)
	}
	t1.Abort() // read-only; outcome of its commit is irrelevant to the snapshot

	// a fresh transaction sees the new value
	if v, ok := getVal(db, []byte("k")); !ok || string(v) != "2" {
		t.Fatalf("post-commit read: %q %v", v, ok)
	}
}

// RunLostUpdate: concurrent read-modify-write on one key; exactly one commits.
func RunLostUpdate(t *testing.T, mk harness.Maker) {
	dir := harness.TempDir(t)
	db := openDB(t, mk, dir)
	defer db.Close()

	putCommit(t, mk, db, []byte("c"), itob(0))

	t1 := db.Begin()
	t2 := db.Begin()
	v1, _ := t1.Get([]byte("c"))
	v2, _ := t2.Get([]byte("c"))
	t1.Set([]byte("c"), itob(atoi(t, v1)+1))
	t2.Set([]byte("c"), itob(atoi(t, v2)+1))

	e1 := t1.Commit()
	e2 := t2.Commit()

	ok1, ok2 := e1 == nil, e2 == nil
	ser1, ser2 := e1 != nil && mk.IsSerErr(e1), e2 != nil && mk.IsSerErr(e2)
	if ok1 == ok2 {
		t.Fatalf("lost update: both committed or both failed (e1=%v e2=%v)", e1, e2)
	}
	if !(ok1 && ser2) && !(ok2 && ser1) {
		t.Fatalf("one commit must fail with ErrSerializationFailure: e1=%v e2=%v", e1, e2)
	}

	// retry the loser; final counter must be 2 (no lost update)
	for i := 0; i < 100; i++ {
		tr := db.Begin()
		vr, _ := tr.Get([]byte("c"))
		tr.Set([]byte("c"), itob(atoi(t, vr)+1))
		if err := tr.Commit(); err == nil {
			break
		} else if !mk.IsSerErr(err) {
			t.Fatalf("retry commit: %v", err)
		}
	}
	if v, _ := getVal(db, []byte("c")); atoi(t, v) != 2 {
		t.Fatalf("lost update: final counter %s, want 2", v)
	}
}

// RunWriteSkew: the decisive SSI case. Two txns each read {x,y} and write one;
// SSI must abort one so the x+y>=1 invariant survives.
func RunWriteSkew(t *testing.T, mk harness.Maker) {
	dir := harness.TempDir(t)
	db := openDB(t, mk, dir)
	defer db.Close()

	putCommit(t, mk, db, []byte("x"), itob(1))
	putCommit(t, mk, db, []byte("y"), itob(1))

	t1 := db.Begin()
	t2 := db.Begin()
	_, _ = t1.Get([]byte("x")) // read x into t1's read set (value unused by its rule)
	y1, _ := t1.Get([]byte("y"))
	x2, _ := t2.Get([]byte("x"))
	_, _ = t2.Get([]byte("y")) // read y into t2's read set
	// t1 zeroes x if y keeps the invariant; t2 zeroes y if x keeps it.
	if atoi(t, y1) >= 1 {
		t1.Set([]byte("x"), itob(0))
	}
	if atoi(t, x2) >= 1 {
		t2.Set([]byte("y"), itob(0))
	}
	e1 := t1.Commit()
	e2 := t2.Commit()

	if (e1 == nil) == (e2 == nil) {
		t.Fatalf("write skew: SSI must abort exactly one (e1=%v e2=%v)", e1, e2)
	}
	if e1 != nil && !mk.IsSerErr(e1) {
		t.Fatalf("e1 not a serialization failure: %v", e1)
	}
	if e2 != nil && !mk.IsSerErr(e2) {
		t.Fatalf("e2 not a serialization failure: %v", e2)
	}

	// The loser aborted, so only the winner's single zeroing applied; the
	// x+y>=1 invariant must therefore still hold. (Plain SI would have let both
	// commit -> x=y=0 -> invariant violated.)
	xv, _ := getVal(db, []byte("x"))
	yv, _ := getVal(db, []byte("y"))
	if atoi(t, xv)+atoi(t, yv) < 1 {
		t.Fatalf("invariant violated: x=%s y=%s", xv, yv)
	}
}

// RunReadOnlyAnomaly: a read-only transaction participating in a would-be
// non-serializable history (write skew observed by a reader). SSI must make the
// committed history serializable. Checked with the MVSG oracle.
func RunReadOnlyAnomaly(t *testing.T, mk harness.Maker) {
	dir := harness.TempDir(t)
	db := openDB(t, mk, dir)
	defer db.Close()

	rec := newRecorder()
	seedID := rec.newID()
	seed := db.Begin()
	seed.Set([]byte("x"), encID(seedID))
	seed.Set([]byte("y"), encID(seedID))
	if err := seed.Commit(); err != nil {
		t.Fatalf("seed commit: %v", err)
	}
	rec.commit(txnObs{id: seedID, reads: map[string]uint64{},
		writes: map[string]struct{}{"x": {}, "y": {}}})

	// t1 and t2: the write-skew pair.
	id1, id2, id3 := rec.newID(), rec.newID(), rec.newID()
	t1 := db.Begin()
	t2 := db.Begin()
	o1 := txnObs{id: id1, reads: map[string]uint64{}, writes: map[string]struct{}{}}
	o2 := txnObs{id: id2, reads: map[string]uint64{}, writes: map[string]struct{}{}}
	readInto(t1, "x", o1.reads)
	readInto(t1, "y", o1.reads)
	readInto(t2, "x", o2.reads)
	readInto(t2, "y", o2.reads)
	t1.Set([]byte("x"), encID(id1))
	o1.writes["x"] = struct{}{}
	if e := t1.Commit(); e == nil {
		rec.commit(o1)
	} else if !mk.IsSerErr(e) {
		t.Fatalf("t1 commit: %v", e)
	}

	// read-only observer begins AFTER t1 but BEFORE t2 commits.
	t3 := db.Begin()
	o3 := txnObs{id: id3, reads: map[string]uint64{}, writes: map[string]struct{}{}}
	readInto(t3, "x", o3.reads)
	readInto(t3, "y", o3.reads)
	if e := t3.Commit(); e == nil {
		rec.commit(o3)
	} else if !mk.IsSerErr(e) {
		t.Fatalf("t3 commit: %v", e)
	}

	t2.Set([]byte("y"), encID(id2))
	o2.writes["y"] = struct{}{}
	if e := t2.Commit(); e == nil {
		rec.commit(o2)
	} else if !mk.IsSerErr(e) {
		t.Fatalf("t2 commit: %v", e)
	}

	if ok, why := checkSerializable(rec.snapshot()); !ok {
		t.Fatalf("read-only anomaly: committed history not serializable: %s", why)
	}
}

// RunG2Cycle: a two-transaction read-write dependency cycle must be broken.
func RunG2Cycle(t *testing.T, mk harness.Maker) {
	dir := harness.TempDir(t)
	db := openDB(t, mk, dir)
	defer db.Close()

	rec := newRecorder()
	seedID := rec.newID()
	seed := db.Begin()
	seed.Set([]byte("A"), encID(seedID))
	seed.Set([]byte("B"), encID(seedID))
	if err := seed.Commit(); err != nil {
		t.Fatalf("seed: %v", err)
	}
	rec.commit(txnObs{id: seedID, reads: map[string]uint64{},
		writes: map[string]struct{}{"A": {}, "B": {}}})

	id1, id2 := rec.newID(), rec.newID()
	t1 := db.Begin()
	t2 := db.Begin()
	o1 := txnObs{id: id1, reads: map[string]uint64{}, writes: map[string]struct{}{}}
	o2 := txnObs{id: id2, reads: map[string]uint64{}, writes: map[string]struct{}{}}
	readInto(t1, "A", o1.reads) // t1: read A, write B
	readInto(t2, "B", o2.reads) // t2: read B, write A
	t1.Set([]byte("B"), encID(id1))
	o1.writes["B"] = struct{}{}
	t2.Set([]byte("A"), encID(id2))
	o2.writes["A"] = struct{}{}

	e1 := t1.Commit()
	e2 := t2.Commit()
	if e1 == nil {
		rec.commit(o1)
	}
	if e2 == nil {
		rec.commit(o2)
	}
	if (e1 == nil) == (e2 == nil) {
		t.Fatalf("G2 cycle: exactly one of the cyclic txns must abort (e1=%v e2=%v)", e1, e2)
	}
	if ok, why := checkSerializable(rec.snapshot()); !ok {
		t.Fatalf("G2 cycle not broken: %s", why)
	}
}

func readInto(tx harness.TxnHandle, key string, into map[string]uint64) {
	v, ok := tx.Get([]byte(key))
	if ok {
		into[key] = decID(v)
	}
}

// ---------------------------------------------------------------------------
// Differential serializability (the apex)
// ---------------------------------------------------------------------------

// RunSerializableFuzz: a randomized, barrier-synchronized concurrent workload
// (overlapping snapshots, retries on ErrSerializationFailure) is recorded and
// checked against the MVSG oracle. A subtly-wrong isolation produces a history
// with no valid serial order.
func RunSerializableFuzz(t *testing.T, mk harness.Maker) {
	dir := harness.TempDir(t)
	db := openDB(t, mk, dir)
	defer db.Close()

	const (
		keys    = 8
		workers = 4
		rounds  = 40
	)
	key := func(i int) []byte { return []byte(fmt.Sprintf("k%02d", i)) }

	rec := newRecorder()
	seedID := rec.newID()
	seed := db.Begin()
	sw := map[string]struct{}{}
	for i := 0; i < keys; i++ {
		seed.Set(key(i), encID(seedID))
		sw[string(key(i))] = struct{}{}
	}
	if err := seed.Commit(); err != nil {
		t.Fatalf("seed: %v", err)
	}
	rec.commit(txnObs{id: seedID, reads: map[string]uint64{}, writes: sw})

	// Deterministic per-(round,worker) key choices via a seeded splitmix.
	plan := func(round, w int) (ka, kb int) {
		switch w {
		case 0:
			return 0, 1 // write-skew pair on (k0,k1): read both, write k0
		case 1:
			return 1, 0 // ... read both, write k1 (the other half)
		default:
			s := uint64(round)*1000003 + uint64(w)*31 + 12345
			s ^= s >> 16
			ka = int(s % keys)
			s = s*2654435761 + 1
			kb = int(s % keys)
			return ka, kb
		}
	}

	for round := 0; round < rounds; round++ {
		txns := make([]harness.TxnHandle, workers)
		obs := make([]txnObs, workers)
		var ready sync.WaitGroup
		var done sync.WaitGroup
		gate := make(chan struct{})
		ready.Add(workers)
		done.Add(workers)

		for w := 0; w < workers; w++ {
			go func(w int) {
				defer done.Done()
				ka, kb := plan(round, w)
				tx := db.Begin() // phase A: all snapshots overlap
				txns[w] = tx
				o := txnObs{id: rec.newID(), reads: map[string]uint64{}, writes: map[string]struct{}{}}
				// read both keys (predicate), then write one.
				readInto(tx, string(key(ka)), o.reads)
				readInto(tx, string(key(kb)), o.reads)
				tx.Set(key(ka), encID(o.id))
				o.writes[string(key(ka))] = struct{}{}
				obs[w] = o
				ready.Done()
				<-gate // commit together
				if err := tx.Commit(); err == nil {
					rec.commit(obs[w])
				} else if !mk.IsSerErr(err) {
					panic(fmt.Sprintf("commit: %v", err))
				}
			}(w)
		}
		ready.Wait() // every txn has snapshotted + done its ops
		close(gate)  // release all commits concurrently
		done.Wait()

		// Retry losers serially so the workload makes progress (and exercises
		// the retry-on-ErrSerializationFailure path).
		for w := 0; w < workers; w++ {
			ka, _ := plan(round, w)
			for i := 0; i < 50; i++ {
				tx := db.Begin()
				o := txnObs{id: rec.newID(), reads: map[string]uint64{}, writes: map[string]struct{}{}}
				readInto(tx, string(key(ka)), o.reads)
				tx.Set(key(ka), encID(o.id))
				o.writes[string(key(ka))] = struct{}{}
				err := tx.Commit()
				if err == nil {
					rec.commit(o)
					break
				}
				if !mk.IsSerErr(err) {
					t.Fatalf("serial retry commit: %v", err)
				}
			}
		}
	}

	hist := rec.snapshot()
	if ok, why := checkSerializable(hist); !ok {
		t.Fatalf("fuzz: committed history (%d txns) not serializable: %s", len(hist), why)
	}
}
