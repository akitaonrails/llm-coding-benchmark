package harness

import (
	"os"
	"testing"
)

// TempDir returns a fresh temp directory for an engine and registers cleanup
// that both removes the directory and clears the crash simulator's state for
// it, so failpoints and SyncFile registrations never leak between tests. Use
// it instead of t.TempDir() directly so ResetDir is always called.
func TempDir(t testing.TB) string {
	t.Helper()
	dir := t.TempDir()
	t.Cleanup(func() { ResetDir(dir) })
	return dir
}

// FreshDir is the non-testing variant (for standalone drivers): it makes a temp
// dir and returns it plus a cleanup func.
func FreshDir(prefix string) (dir string, cleanup func(), err error) {
	dir, err = os.MkdirTemp("", prefix)
	if err != nil {
		return "", nil, err
	}
	return dir, func() {
		ResetDir(dir)
		_ = os.RemoveAll(dir)
	}, nil
}
