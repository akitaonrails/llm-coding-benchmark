// Package grader is the HIDDEN gauntlet from CONTRACT.md. The test LOGIC lives
// here as exported Run* functions parameterized by a harness.MakeLangFunc, so a
// single source of truth runs against either the correct reference (the SOUND
// check, grader/reference_test.go) or a deliberately-broken variant (the
// SENSITIVE / proven-negative checks, reference/broken/*).
//
// Three families: conformance (program -> exact stdout), type inference
// (accept/reject), and GC stress (bounded heap / completion). Every Run* runs
// its work under a per-test timeout so a GC or occurs-check hang fails only that
// test, never the whole binary.
package grader

import (
	"reflect"
	"testing"
	"time"

	"v41lang/harness"
)

// defaultTimeout bounds a single grader test. A hung model (e.g. no occurs
// check -> infinite type, or a non-collecting GC) fails only that test.
const defaultTimeout = 60 * time.Second

// withTimeout runs fn in its own goroutine and fails the test if it does not
// finish within d. The goroutine never touches *testing.T, so a late finish
// cannot race with the test framework.
func withTimeout(t *testing.T, d time.Duration, fn func()) {
	t.Helper()
	done := make(chan any, 1) // carries nil on clean finish, or a recovered panic
	go func() {
		var pv any
		defer func() { done <- pv }()
		defer func() {
			if r := recover(); r != nil {
				pv = r
			}
		}()
		fn()
	}()
	timer := time.NewTimer(d)
	defer timer.Stop()
	select {
	case p := <-done:
		if p != nil {
			t.Fatalf("panic in test body: %v", p)
		}
	case <-timer.C:
		t.Fatalf("test timed out after %s (possible infinite loop / unbounded allocation)", d)
	}
}

// ---------------------------------------------------------------------------
// reflection hook: fetch the OPTIONAL RunInstrumented accessor without widening
// the harness.Lang interface (INTEGRATION RULE).
//   RunInstrumented(string) (string, uint64, int64, error)
// ---------------------------------------------------------------------------

type instrResult struct {
	out  string
	peak uint64
	ngc  int64
	err  error
	ok   bool // whether the hook was present and well-typed
}

func tryInstrumented(l harness.Lang, src string) instrResult {
	m := reflect.ValueOf(l).MethodByName("RunInstrumented")
	if !m.IsValid() {
		return instrResult{ok: false}
	}
	mt := m.Type()
	if mt.NumIn() != 1 || mt.In(0).Kind() != reflect.String {
		return instrResult{ok: false}
	}
	if mt.NumOut() != 4 ||
		mt.Out(0).Kind() != reflect.String ||
		mt.Out(1).Kind() != reflect.Uint64 ||
		mt.Out(2).Kind() != reflect.Int64 ||
		mt.Out(3).String() != "error" {
		return instrResult{ok: false}
	}
	res := m.Call([]reflect.Value{reflect.ValueOf(src)})
	r := instrResult{
		out:  res[0].String(),
		peak: res[1].Uint(),
		ngc:  res[2].Int(),
		ok:   true,
	}
	if e := res[3].Interface(); e != nil {
		r.err = e.(error)
	}
	return r
}

// conformCase is a (program, expected stdout) pair.
type conformCase struct {
	name string
	src  string
	want string
}

func runConformance(t *testing.T, mk harness.MakeLangFunc, cases []conformCase) {
	for _, c := range cases {
		c := c
		t.Run(c.name, func(t *testing.T) {
			withTimeout(t, defaultTimeout, func() {
				l := mk()
				got, err := l.Run(c.src)
				if err != nil {
					t.Fatalf("Run(%q) returned error: %v", c.src, err)
				}
				if got != c.want {
					t.Fatalf("Run(%q)\n got  = %q\n want = %q", c.src, got, c.want)
				}
			})
		})
	}
}

// expectWellTyped / expectIllTyped assert TypeCheck's verdict.
func expectWellTyped(t *testing.T, mk harness.MakeLangFunc, name, src string) {
	t.Run(name, func(t *testing.T) {
		withTimeout(t, defaultTimeout, func() {
			if err := mk().TypeCheck(src); err != nil {
				t.Fatalf("TypeCheck(%q) = %v, want well-typed (nil)", src, err)
			}
		})
	})
}

func expectIllTyped(t *testing.T, mk harness.MakeLangFunc, name, src string) {
	t.Run(name, func(t *testing.T) {
		withTimeout(t, defaultTimeout, func() {
			if err := mk().TypeCheck(src); err == nil {
				t.Fatalf("TypeCheck(%q) = nil, want a type error (rejected)", src)
			}
		})
	})
}
