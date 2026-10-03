// Package plainsi is a PROVEN-NEGATIVE variant: plain Snapshot Isolation with
// first-committer-wins write-write detection but NO SSI read-set certification.
// It therefore allows write skew and the read-only anomaly.
//
// Expected: TestWriteSkew and TestSerializableFuzz FAIL; the controls
// (TestBasicPutGet, TestSnapshotIsolation) and even TestLostUpdate still PASS
// (lost updates are caught by the surviving write-write check).
package plainsi

import (
	"errors"

	"v41store/harness"
	"v41store/reference"
)

func maker() harness.Maker {
	return harness.Maker{
		Open: func(dir string) (harness.DBHandle, error) {
			db, err := reference.OpenWithKnobs(dir, reference.Knobs{DisableReadValidation: true})
			if err != nil {
				return nil, err
			}
			return reference.NewHandle(db), nil
		},
		IsSerErr: func(e error) bool { return errors.Is(e, reference.ErrSerializationFailure) },
	}
}
