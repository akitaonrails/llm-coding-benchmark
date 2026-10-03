package grader

import (
	"errors"
	"testing"

	"v41store/harness"
	"v41store/reference"
)

// refMaker wires the CORRECT reference engine into the parameterized suite (the
// SOUND check). A model submission supplies an identical ~20-line maker in its
// own wiring file, pointing Open at engine.Open and IsSerErr at
// errors.Is(err, engine.ErrSerializationFailure).
func refMaker() harness.Maker {
	return harness.Maker{
		Open: func(dir string) (harness.DBHandle, error) {
			db, err := reference.Open(dir)
			if err != nil {
				return nil, err
			}
			return reference.NewHandle(db), nil
		},
		IsSerErr: func(e error) bool { return errors.Is(e, reference.ErrSerializationFailure) },
	}
}

func TestBasicPutGet(t *testing.T)          { RunBasicPutGet(t, refMaker()) }
func TestScan(t *testing.T)                 { RunScan(t, refMaker()) }
func TestCommitDurable(t *testing.T)        { RunCommitDurable(t, refMaker()) }
func TestAbortNoTrace(t *testing.T)         { RunAbortNoTrace(t, refMaker()) }
func TestCrashMidCommitAtomic(t *testing.T) { RunCrashMidCommitAtomic(t, refMaker()) }
func TestRecoveryManyTxns(t *testing.T)     { RunRecoveryManyTxns(t, refMaker()) }

func TestSnapshotIsolation(t *testing.T) { RunSnapshotIsolation(t, refMaker()) }
func TestLostUpdate(t *testing.T)        { RunLostUpdate(t, refMaker()) }
func TestWriteSkew(t *testing.T)         { RunWriteSkew(t, refMaker()) }
func TestReadOnlyAnomaly(t *testing.T)   { RunReadOnlyAnomaly(t, refMaker()) }
func TestG2Cycle(t *testing.T)           { RunG2Cycle(t, refMaker()) }

func TestSerializableFuzz(t *testing.T) { RunSerializableFuzz(t, refMaker()) }
