// Package nofsync is a PROVEN-NEGATIVE variant: the WAL is written but never
// fsynced, so a crash (which discards un-fsynced bytes) loses committed data.
//
// Expected: TestCommitDurable and TestCrashMidCommitAtomic FAIL; the controls
// (TestBasicPutGet, TestSnapshotIsolation) still PASS (they never crash).
package nofsync

import (
	"errors"

	"v41store/harness"
	"v41store/reference"
)

func maker() harness.Maker {
	return harness.Maker{
		Open: func(dir string) (harness.DBHandle, error) {
			db, err := reference.OpenWithKnobs(dir, reference.Knobs{DisableFsync: true})
			if err != nil {
				return nil, err
			}
			return reference.NewHandle(db), nil
		},
		IsSerErr: func(e error) bool { return errors.Is(e, reference.ErrSerializationFailure) },
	}
}
