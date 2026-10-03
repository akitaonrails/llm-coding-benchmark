// Package harness is the PROVIDED scaffold for the P2 transactional
// storage-engine benchmark. It is given to the model in sprint 1 and is also
// linked into the hidden grader, so every submission is driven identically.
//
// It contains three things:
//
//   - The grader-facing handle types (DBHandle / TxnHandle) and the Maker
//     bundle the grader uses to open an engine without naming the engine's
//     concrete package. (handle.go)
//   - A crash simulator with injectable failpoints and a durability-accurate
//     WAL file wrapper (SyncFile). (failpoint.go)
//   - A temp-dir manager. (tempdir.go)
//
// INTEGRATION CONTRACT (learned from P1): the grader never requires the engine
// to satisfy an interface whose method signatures differ from the written
// CONTRACT. The model implements exactly `engine.Open`, `*engine.DB`,
// `*engine.Txn` with the contract signatures; a tiny per-engine shim (≈20
// lines, authored in the wiring _test.go — see reference.NewHandle for the
// canonical copy) adapts the concrete types to DBHandle/TxnHandle at the
// grader boundary. Because `(*DB).Begin()` returns the concrete `*Txn` (not an
// interface), the engine cannot satisfy DBHandle directly; the shim is where
// adaptation happens so a contract-silent signature mismatch can never zero a
// working submission.
package harness

// TxnHandle is the minimal transaction surface the grader drives. Method
// signatures mirror CONTRACT.md exactly.
type TxnHandle interface {
	Get(key []byte) (val []byte, ok bool)
	Set(key, val []byte)
	Delete(key []byte)
	Commit() error
	Abort()
	Scan(lo, hi []byte, fn func(key, val []byte) bool)
}

// DBHandle is the minimal database surface the grader drives.
type DBHandle interface {
	Begin() TxnHandle
	Close() error
}

// Maker bundles everything the grader needs to drive one engine implementation.
//
//   - Open opens/reopens a database rooted at dir (the crash simulator calls it
//     again on the same dir to simulate a reopen after power loss).
//   - IsSerErr reports whether an error returned by Commit is the engine's
//     serialization-failure sentinel (the contract's exported
//     ErrSerializationFailure). It is supplied by the wiring rather than
//     matched by string so the grader stays decoupled from the message text.
type Maker struct {
	Open     func(dir string) (DBHandle, error)
	IsSerErr func(error) bool
}
