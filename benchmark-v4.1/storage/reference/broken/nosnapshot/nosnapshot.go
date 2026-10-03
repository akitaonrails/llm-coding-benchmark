// Package nosnapshot is a PROVEN-NEGATIVE variant: reads see the latest
// committed value instead of the transaction's snapshot, so a transaction gets
// non-repeatable reads when a concurrent transaction commits.
//
// Expected: TestSnapshotIsolation FAILS; the control TestBasicPutGet (single
// transaction, no concurrency) still PASSES.
package nosnapshot

import (
	"errors"

	"v41store/harness"
	"v41store/reference"
)

func maker() harness.Maker {
	return harness.Maker{
		Open: func(dir string) (harness.DBHandle, error) {
			db, err := reference.OpenWithKnobs(dir, reference.Knobs{DisableSnapshot: true})
			if err != nil {
				return nil, err
			}
			return reference.NewHandle(db), nil
		},
		IsSerErr: func(e error) bool { return errors.Is(e, reference.ErrSerializationFailure) },
	}
}
