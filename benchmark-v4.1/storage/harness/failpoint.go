package harness

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

// ---------------------------------------------------------------------------
// Crash simulator + durability-accurate WAL file.
//
// A "crash" models power loss: the in-memory DB is discarded and Open is called
// again on the same dir. For that to be a MEANINGFUL test of fsync, bytes that
// were written but not yet fsynced must be lost on reopen. A plain *os.File
// cannot model this (the OS page cache survives a simulated crash because the
// process never actually dies), so the engine routes its WAL through SyncFile,
// which remembers the last fsynced ("durable") offset. On crash the simulator
// truncates every registered SyncFile back to its durable offset — exactly the
// bytes a real power loss would keep.
//
// Everything here is keyed by the engine's directory, so the grader can arm a
// crash and reopen without holding a reference to the engine's internals.
// ---------------------------------------------------------------------------

// crashSentinel is what Reached / a torn Append panics with; RunMaybeCrash
// recovers exactly this value and nothing else.
type crashSentinel struct{ point string }

func (c crashSentinel) String() string { return "harness: simulated crash at " + c.point }

// dirState holds all SyncFiles and armed failpoints for one engine directory.
type dirState struct {
	files map[*SyncFile]struct{}
	armed map[string]Policy // failpoint name -> policy
}

// Policy selects what an armed failpoint does when Reached.
type Policy int

const (
	// CrashHard: truncate all this dir's SyncFiles to their durable offset
	// (discard un-fsynced bytes), mark them dead, then panic(crashSentinel).
	// Models a power loss AT this point: whatever was fsynced before the point
	// survives, everything else is gone.
	CrashHard Policy = iota
	// CrashTorn: like CrashHard, but first simulate a torn write — the NEXT
	// SyncFile.Append writes only a prefix of its bytes, fsyncs that prefix
	// (so a partial record becomes durable), and then crashes. This exercises
	// the recovery CRC/length path: the trailing record is durable but
	// corrupt and must be discarded.
	CrashTorn
)

var (
	regMu sync.Mutex
	reg   = map[string]*dirState{} // abs dir -> state
)

func stateFor(dir string) *dirState {
	abs, err := filepath.Abs(dir)
	if err != nil {
		abs = dir
	}
	s := reg[abs]
	if s == nil {
		s = &dirState{files: map[*SyncFile]struct{}{}, armed: map[string]Policy{}}
		reg[abs] = s
	}
	return s
}

// ArmCrash arms the named failpoint for dir with the given policy. The next
// time the engine Reaches that name (or, for CrashTorn, the next Append), the
// crash fires. Call from the grader before driving the commit you want to
// interrupt.
func ArmCrash(dir, name string, p Policy) {
	regMu.Lock()
	defer regMu.Unlock()
	stateFor(dir).armed[name] = p
}

// DisarmAll clears every armed failpoint for dir (not the registered files).
func DisarmAll(dir string) {
	regMu.Lock()
	defer regMu.Unlock()
	if s := reg[absOf(dir)]; s != nil {
		s.armed = map[string]Policy{}
	}
}

func absOf(dir string) string {
	abs, err := filepath.Abs(dir)
	if err != nil {
		return dir
	}
	return abs
}

// Reached is called by the engine's WAL writer at named crash points (e.g.
// "commit.beforeWrite", "commit.beforeFsync", "commit.afterFsync"). If a
// CrashHard failpoint of that name is armed for the file's dir, it discards
// un-fsynced bytes and panics. CrashTorn is handled inside Append, not here.
func (s *SyncFile) Reached(name string) {
	regMu.Lock()
	st := reg[s.dir]
	if st == nil {
		regMu.Unlock()
		return
	}
	p, ok := st.armed[name]
	if !ok || p != CrashHard {
		regMu.Unlock()
		return
	}
	delete(st.armed, name)
	crashDirLocked(st, name)
	regMu.Unlock()
	panic(crashSentinel{point: name})
}

// crashDirLocked truncates every SyncFile of the state to its durable offset
// and marks them dead. Caller holds regMu.
func crashDirLocked(st *dirState, point string) {
	for f := range st.files {
		f.crash()
	}
}

// SimulateCrash performs a power-loss crash for dir WITHOUT a panic: it
// discards un-fsynced bytes from every registered SyncFile and marks them dead.
// Use it for tests that crash between operations (commit, then crash, then
// reopen) rather than mid-operation. After it returns, drop the old handle and
// call the maker again on the same dir.
func SimulateCrash(dir string) {
	regMu.Lock()
	defer regMu.Unlock()
	if s := reg[absOf(dir)]; s != nil {
		crashDirLocked(s, "SimulateCrash")
		// A reopen will register fresh SyncFiles; clear the dead ones so the
		// registry stays bounded and a later crash can't touch stale handles.
		s.files = map[*SyncFile]struct{}{}
		s.armed = map[string]Policy{}
	}
}

// ResetDir forgets all simulator state for dir. The temp-dir manager calls it
// on cleanup so one test's failpoints never leak into another.
func ResetDir(dir string) {
	regMu.Lock()
	defer regMu.Unlock()
	delete(reg, absOf(dir))
}

// ---------------------------------------------------------------------------
// SyncFile: an append-oriented file that tracks its durable (fsynced) offset.
// ---------------------------------------------------------------------------

// SyncFile is the crash-accurate file the engine must use for its WAL. Writes
// extend the file; only Sync advances the durable offset; a simulated crash
// truncates back to the durable offset.
type SyncFile struct {
	mu      sync.Mutex
	f       *os.File
	dir     string // abs dir key for the registry
	path    string
	written int64 // bytes handed to the OS
	durable int64 // bytes known fsynced
	dead    bool  // post-crash: further writes are refused, Sync is a no-op
}

// OpenSync opens (creating if needed) a crash-accurate file named `name` inside
// dir and registers it with the crash simulator for dir. The engine calls this
// for its WAL instead of os.OpenFile so durability can be modeled. A reopen
// after a crash picks up the file truncated to its last durable offset.
func OpenSync(dir, name string) (*SyncFile, error) {
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, err
	}
	abs := absOf(dir)
	path := filepath.Join(dir, name)
	f, err := os.OpenFile(path, os.O_RDWR|os.O_CREATE, 0o644)
	if err != nil {
		return nil, err
	}
	fi, err := f.Stat()
	if err != nil {
		f.Close()
		return nil, err
	}
	s := &SyncFile{f: f, dir: abs, path: path, written: fi.Size(), durable: fi.Size()}
	// fsync the parent dir so the file's existence is durable.
	syncDir(dir)
	regMu.Lock()
	stateFor(dir).files[s] = struct{}{}
	regMu.Unlock()
	return s, nil
}

// Append writes p, extending the file. It honors a CrashTorn failpoint: if one
// is armed for this dir, it writes a prefix of p, fsyncs that prefix (a durable
// but partial record), marks the file dead and panics — simulating a torn
// write whose header survived a crash.
func (s *SyncFile) Append(p []byte) (int, error) {
	// Check for an armed torn-write policy before taking the file lock.
	regMu.Lock()
	torn := false
	if st := reg[s.dir]; st != nil {
		for name, pol := range st.armed {
			if pol == CrashTorn {
				delete(st.armed, name)
				torn = true
				break
			}
		}
	}
	regMu.Unlock()

	s.mu.Lock()
	if s.dead {
		s.mu.Unlock()
		return 0, fmt.Errorf("harness: write to crashed file %s", s.path)
	}
	if torn && len(p) > 1 {
		half := len(p)/2 + 1 // guarantee a non-empty, strictly-partial record
		n, err := s.f.WriteAt(p[:half], s.written)
		s.written += int64(n)
		_ = s.f.Sync() // the torn prefix becomes durable
		s.durable = s.written
		s.dead = true
		s.mu.Unlock()
		if err == nil {
			panic(crashSentinel{point: "wal.tornWrite"})
		}
		return n, err
	}
	n, err := s.f.WriteAt(p, s.written)
	s.written += int64(n)
	s.mu.Unlock()
	return n, err
}

// Sync fsyncs the file and advances the durable offset. A no-op on a dead file.
func (s *SyncFile) Sync() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.dead {
		return nil
	}
	if err := s.f.Sync(); err != nil {
		return err
	}
	s.durable = s.written
	return nil
}

// ReadAll returns the file's current on-disk bytes (used by recovery on Open).
func (s *SyncFile) ReadAll() ([]byte, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return os.ReadFile(s.path)
}

// Size returns the current written length.
func (s *SyncFile) Size() int64 {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.written
}

// Truncate shrinks the file to n and resets offsets (used by the engine after a
// checkpoint truncates the WAL).
func (s *SyncFile) Truncate(n int64) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.dead {
		return nil
	}
	if err := s.f.Truncate(n); err != nil {
		return err
	}
	if _, err := s.f.Seek(0, 0); err != nil {
		return err
	}
	s.written = n
	if s.durable > n {
		s.durable = n
	}
	if err := s.f.Sync(); err != nil {
		return err
	}
	s.durable = s.written
	return nil
}

// Close closes the underlying file and unregisters it.
func (s *SyncFile) Close() error {
	s.mu.Lock()
	err := s.f.Close()
	s.dead = true
	s.mu.Unlock()
	regMu.Lock()
	if st := reg[s.dir]; st != nil {
		delete(st.files, s)
	}
	regMu.Unlock()
	return err
}

// crash truncates to the durable offset and marks the file dead. Caller holds
// regMu (so it is serialized with arming).
func (s *SyncFile) crash() {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.dead {
		return
	}
	// Discard un-fsynced bytes: truncate the real file to the durable offset.
	_ = s.f.Truncate(s.durable)
	_ = s.f.Sync()
	s.written = s.durable
	s.dead = true
}

func syncDir(dir string) {
	d, err := os.Open(dir)
	if err != nil {
		return
	}
	_ = d.Sync()
	_ = d.Close()
}

// RunMaybeCrash runs fn, recovering a simulated crash panic. It returns true if
// fn crashed (was interrupted by an armed failpoint), false if it ran to
// completion. Any non-crash panic is re-raised.
func RunMaybeCrash(fn func()) (crashed bool) {
	defer func() {
		if r := recover(); r != nil {
			if _, ok := r.(crashSentinel); ok {
				crashed = true
				return
			}
			panic(r)
		}
	}()
	fn()
	return false
}
