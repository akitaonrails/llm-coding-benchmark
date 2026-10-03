# P2 — Transactional storage engine: the CONTRACT (interface + grader spec)

Language: **Go** (go1.27). Module `v41store`. The model implements an embedded transactional key/value
engine with **Serializable Snapshot Isolation (SSI)**, a write-ahead log, and crash recovery. Grading is an
objective Go gauntlet: crash-recovery, concurrency-anomaly detection, and **differential fuzzing vs a
reference serializable oracle**, all under `-race`.

The model implements package `engine` (+ helpers). `harness/` is PROVIDED scaffold (given in sprint 1; do not
reimplement) so the grader can drive any submission identically.

---

## What the model implements — package `engine`
```go
// Open/reopen a database rooted at a directory. Reopening after a crash must recover from the WAL:
// every committed txn durable, no partial/aborted writes visible.
func Open(dir string) (*DB, error)
func (db *DB) Close() error

// A transaction. Reads see a consistent snapshot; writes are buffered until Commit.
func (db *DB) Begin() *Txn
func (tx *Txn) Get(key []byte) (val []byte, ok bool)
func (tx *Txn) Set(key, val []byte)
func (tx *Txn) Delete(key []byte)
// Commit returns ErrSerializationFailure (exported) if committing would violate serializability
// (e.g. write skew, read-write dependency cycle). The caller is expected to retry.
func (tx *Txn) Commit() error
func (tx *Txn) Abort()

// Range scan over the snapshot, ordered by key (needed for predicate reads / SSI).
func (tx *Txn) Scan(lo, hi []byte, fn func(key, val []byte) bool)

var ErrSerializationFailure = errors.New("serialization failure")
```

### Durability / recovery (the WAL half)
- `Commit` must be durable before returning (fsync the WAL). After `Close()` (or a simulated crash =
  discarding the in-memory DB and calling `Open` on the same dir), **every committed txn is present and every
  aborted/in-flight txn leaves no trace**. No torn writes.
- **REQUIRED — write your WAL through the provided crash-accurate file, not raw `os.File`.** The grader
  simulates power-loss by truncating back to the last fsync; this only works if your WAL uses
  `harness.OpenSync(dir, name)` → a `*harness.SyncFile` (`Append`, `Sync`, `ReadAll`, `Size`, `Truncate`,
  `Close`). Call `wal.Sync()` to fsync on commit. And around commit, call the crash hooks so the grader can
  inject a crash at each point: `wal.Reached("commit.beforeWrite")` → append your commit record →
  `wal.Reached("commit.beforeFsync")` → `wal.Sync()` → `wal.Reached("commit.afterFsync")`. Frame WAL records
  with a length + CRC so a torn (partially-fsynced) record is discarded on recovery. (A WAL on raw `os.File`
  will not be crash-tested correctly and is a contract violation.)

### Isolation (the SSI half — the TWIST)
- **Serializable Snapshot Isolation**, not plain SI. Concurrent txns run on snapshots; on commit the engine
  must detect read-write dependency cycles and abort one party with `ErrSerializationFailure` so the committed
  history is **serializable**. This must catch **write skew** and the **read-only-transaction anomaly** —
  exactly the cases plain SI lets through. (Plain-SI submissions pass the SI tests but FAIL the SSI tests.)

### Storage
- On-disk, crash-safe. A B+tree or LSM is fine; the grader does not inspect internals, only behavior +
  (loosely) that storage is bounded (no unbounded in-RAM-only map masquerading as a DB — the recovery tests
  force real on-disk persistence).

---

## The GRADER gauntlet (HIDDEN until grading; per-test, `-race`)
Score = weighted fraction passing. Each test runs as its own `go test -run` with a timeout.

**Durability / recovery**
- `TestBasicPutGet`, `TestScan` — single-txn correctness + ordered scan.
- `TestCommitDurable` — commit, crash (discard+reopen), value present.
- `TestAbortNoTrace` — abort/in-flight txn leaves nothing after crash.
- `TestCrashMidCommitAtomic` — crash injected at many points across a commit → all-or-nothing (no torn txn).
- `TestRecoveryManyTxns` — N committed txns survive a crash; counts/values exact.

**Isolation (SI then SSI)**
- `TestSnapshotIsolation` — a txn sees a stable snapshot despite concurrent commits (no dirty/non-repeatable reads).
- `TestLostUpdate` — concurrent read-modify-write on the same key: one must abort (no lost update).
- `TestWriteSkew` — the classic SSI case (two txns each read {x,y}, write the other) MUST abort one
  (plain SI would allow both → non-serializable). **The decisive SSI test.**
- `TestReadOnlyAnomaly` — the SSI read-only-transaction anomaly is prevented.
- `TestG2Cycle` — a read-write dependency cycle is broken (one txn aborts).

**Differential serializability (the apex)**
- `TestSerializableFuzz` — a randomized concurrent workload (many txns, overlapping keys, retries on
  `ErrSerializationFailure`) is recorded; the committed history is checked against a reference serializable
  oracle: there must exist a serial order of the committed txns reproducing every read. A subtly-wrong
  isolation implementation produces a history with no valid serial order → fail.

Grader output: JSON `{test: pass|fail, elapsed}` + weighted total + "sprints cleared" depth.

---

## VALIDATION requirement (before any model run)
- **SOUND:** a reference-correct engine (`reference/engine.go`) passes the ENTIRE gauntlet under `-race`,
  repeatably (≥3×, no flakes).
- **SENSITIVE (proven negatives):** each `reference/broken/<bug>/` fails the RIGHT test, controls still pass:
  (a) plain SI, no SSI cycle check → `TestWriteSkew` (and `TestSerializableFuzz`) fail; (b) no WAL fsync /
  recovery → `TestCommitDurable`/`TestCrashMidCommitAtomic` fail; (c) no snapshot (reads see uncommitted) →
  `TestSnapshotIsolation` fails; (d) last-writer-wins, no lost-update check → `TestLostUpdate` fails.
Only sound+sensitive → run models.

## Grader-integration rules (learned from P1 — bake in, don't rediscover)
- The grader drives the model via a maker: `func(dir string) (DBHandle, error)`; `DBHandle` is the minimal
  interface the grader needs. Keep handles **concrete** where a name/registration matters; fetch any extra
  accessor by reflection rather than widening the interface (so a contract-silent method signature can't
  zero a working submission).
- The grader runs **each test in its own process** with a per-test timeout, so one deadlock fails only that
  test, never the whole suite.

## Sprint breakdown (7, accumulating)
S1 on-disk B+tree (Put/Get/Scan, no txn) · S2 WAL + crash recovery · S3 MVCC snapshot isolation ·
S4 SSI (write-skew + cycle detection) · S5 range-predicate SSI + read-only-anomaly · S6 crash-during-commit
atomicity + compaction/checkpoint · S7 reveal: full differential serializability fuzz under `-race`.
