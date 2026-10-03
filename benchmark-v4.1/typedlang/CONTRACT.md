# P3 — Typed language (HM inference + bytecode VM + generational GC): the CONTRACT

Language: **Go** (go1.27). Module `v41lang`. The model implements a complete small statically-typed functional
language: lexer → parser → **Hindley–Milner type inference with let-polymorphism + row-polymorphic records**
→ bytecode compiler → stack/register VM → **generational mark-sweep GC**. Grading is an objective Go gauntlet:
conformance (program outputs + expected type errors), adversarial HM inference, and GC stress, under `-race`.

The model implements package `lang` (+ helpers). `harness/` is PROVIDED scaffold (the language spec doc + the
grader's maker types + go.mod). The language SPEC the model implements is in `harness/SPEC.md` (given in S1).

---

## What the model implements — package `lang`
```go
// TypeCheck infers types for a whole program; returns a non-nil error with a stable, greppable code/message
// for ill-typed programs, nil for well-typed ones. Must implement full HM: unification, the occurs check,
// let-generalization (let-polymorphism), the value restriction, and row-polymorphic extensible records.
func TypeCheck(source string) error

// Run type-checks then executes the program on the bytecode VM, returning everything written by the program's
// `print` to stdout (as a string). A type error returns it via err (and no output); a runtime error (should be
// rare in a well-typed program — only explicit failures like integer div-by-zero) returns a runtime error.
func Run(source string) (output string, err error)
```

### The language (full spec goes in harness/SPEC.md — summary here)
- Expressions: integers, bools, strings; `let`/`let rec`; first-class functions + closures; `if`; arithmetic
  and comparison; `print`.
- **Parametric polymorphism via let-generalization** (e.g. `let id = \x -> x` usable at Int and Bool).
- **Row-polymorphic records**: `{a = 1, b = true}`, field access `r.a`, functional update `{ r | a = 2 }`, and
  functions polymorphic over "any record with at least field a:Int" — principal types (the TWIST; textbook
  Algorithm W without rows cannot type these).
- Lists + a few builtins; recursion (so GC has real work).

### Generational GC (the runtime half)
- The VM allocates heap objects (closures, records, lists, strings). The model implements a real GC (a
  generational mark-sweep with a nursery + write barrier is expected). It must reclaim unreachable objects
  INCLUDING cycles, under sustained allocation, without unbounded growth.

---

## The GRADER gauntlet (HIDDEN; per-test, `-race`)
**Conformance (eval)**
- `TestBasicEval`, `TestClosures`, `TestRecursion`, `TestRecords`, `TestRecordUpdate`, `TestLists` —
  (program, expected stdout) pairs; output must match exactly.
**Type inference**
- `TestLetPolymorphism` — `id` used at two types type-checks.
- `TestOccursCheck` — `\x -> x x` is rejected (infinite type).
- `TestValueRestriction` — the classic unsound-generalization case is rejected.
- `TestRowPolymorphism` — a function over "records with field a" accepts `{a,b}` and `{a,c}`, rejects `{b}`
  (the decisive row-poly test; a non-row HM implementation can't get this right).
- `TestTypeErrors` — a battery of ill-typed programs, each must be rejected (and well-typed near-misses accepted).
**GC**
- `TestGCNoLeak` — a program allocating millions of short-lived objects in a loop completes with BOUNDED heap
  (the grader caps/observes memory or runs long enough that a non-collecting runtime OOMs/times out).
- `TestGCCycles` — mutually-referential records/closures become unreachable and are reclaimed (cycle collection).
- `TestGCStressMixed` — mixed lifetimes (long-lived + churn) under sustained allocation; correct results + bounded heap.

Score = weighted fraction passing; + "sprints cleared" depth.

---

## VALIDATION (before any model run)
- **SOUND:** `reference/` (a correct implementation, wired like a model's `lang` via a maker in a `_test.go`)
  passes the ENTIRE gauntlet under `-race`, 3× no flakes.
- **SENSITIVE (proven negatives):** each `reference/broken/<bug>/` fails the RIGHT test, controls pass:
  (a) no let-generalization (monomorphic let) → TestLetPolymorphism fails; (b) no occurs check →
  TestOccursCheck fails (or hangs → caught by per-test timeout); (c) records without rows → TestRowPolymorphism
  fails; (d) GC that never frees (or leaks cycles) → TestGCNoLeak / TestGCCycles fail (OOM/timeout).

## Grader-integration rules (from P1/P2 — obey)
- Drive the model via a maker returning a CONCRETE evaluator handle (or just call package funcs TypeCheck/Run
  through a thin wiring `_test.go`); fetch extra accessors by reflection, never widen an interface in a way a
  contract-silent signature could break.
- Each test runs in its own process with a per-test timeout (a GC/occurs-check hang fails only that test).

## Sprint breakdown (7, accumulating)
S1 lexer + parser + AST (from SPEC) · S2 HM inference core (unification, occurs check, let-generalization) ·
S3 row-polymorphic records + value restriction · S4 bytecode compiler + VM (eval works) · S5 generational GC
(nursery + write barrier) · S6 lists/builtins/recursion + optimization · S7 reveal: full conformance + GC
stress under `-race`.
