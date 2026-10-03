// Package lostupdate is a PROVEN-NEGATIVE variant: last-writer-wins with NO
// conflict detection at all (neither SSI read validation nor first-committer-
// wins). Concurrent read-modify-write updates silently clobber each other.
//
// Expected: TestLostUpdate FAILS; the controls (TestBasicPutGet,
// TestSnapshotIsolation) still PASS.
package lostupdate

import (
	"errors"

	"v41store/harness"
	"v41store/reference"
)

func maker() harness.Maker {
	return harness.Maker{
		Open: func(dir string) (harness.DBHandle, error) {
			db, err := reference.OpenWithKnobs(dir, reference.Knobs{
				DisableReadValidation:  true,
				DisableWriteWriteCheck: true,
			})
			if err != nil {
				return nil, err
			}
			return reference.NewHandle(db), nil
		},
		IsSerErr: func(e error) bool { return errors.Is(e, reference.ErrSerializationFailure) },
	}
}
