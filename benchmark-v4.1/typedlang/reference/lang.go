// Package reference is a CORRECT implementation of the v41lang language from
// harness/SPEC.md: lexer, parser, Hindley–Milner type inference (unification,
// occurs check, let-generalization, the value restriction, and row-polymorphic
// records), a bytecode compiler, a stack VM with tail-call optimization, and a
// generational mark-sweep garbage collector.
//
// It is wired into the grader exactly like a model's `lang` package: a maker in
// grader/reference_test.go returns *reference.Lang as the concrete handle. The
// Options flags exist so the reference/broken/* variants can disable one
// correctness property each (the SENSITIVE / proven-negative checks) without
// duplicating the whole implementation — the ONLY difference between a broken
// variant and the reference is a single flag.
package reference

// Options toggles individual correctness properties. Default() is the correct
// configuration; each broken variant flips exactly one flag to false.
type Options struct {
	Generalize       bool // let-generalization (let-polymorphism)
	ValueRestriction bool // restrict generalization to syntactic values
	OccursCheck      bool // reject infinite types during unification
	Rows             bool // row-polymorphic (extensible) records
	GCCollect        bool // the GC frees unreachable objects at all
	GCCycles         bool // the GC reclaims cycles (vs refcount-only)
}

// Default returns the fully-correct configuration.
func Default() Options {
	return Options{
		Generalize:       true,
		ValueRestriction: true,
		OccursCheck:      true,
		Rows:             true,
		GCCollect:        true,
		GCCycles:         true,
	}
}

// Lang is the concrete evaluator handle the grader drives.
type Lang struct{ opts Options }

// New builds a Lang with the given options.
func New(opts Options) *Lang { return &Lang{opts: opts} }

// NewDefault builds the correct reference.
func NewDefault() *Lang { return &Lang{opts: Default()} }

// TypeCheck infers types for the whole program, returning a non-nil error for
// ill-typed programs and nil for well-typed ones. It does not execute.
func (l *Lang) TypeCheck(source string) error {
	ast, err := parse(source)
	if err != nil {
		return err
	}
	inf := &inferer{opts: l.opts}
	if _, err := inf.infer(baseTypeEnv(), ast); err != nil {
		return err
	}
	return nil
}

// Run type-checks then executes the program, returning its printed output.
func (l *Lang) Run(source string) (string, error) {
	out, _, _, err := l.runInternal(source)
	return out, err
}

// RunInstrumented is the optional grader hook (fetched by reflection, see
// harness/maker.go): it additionally reports the high-water mark of the managed
// heap's live bytes and the number of collections performed.
func (l *Lang) RunInstrumented(source string) (output string, peakHeapBytes uint64, numCollections int64, err error) {
	return l.runInternal(source)
}

func (l *Lang) runInternal(source string) (string, uint64, int64, error) {
	ast, err := parse(source)
	if err != nil {
		return "", 0, 0, err
	}
	inf := &inferer{opts: l.opts}
	if _, err := inf.infer(baseTypeEnv(), ast); err != nil {
		return "", 0, 0, err
	}
	prog, err := compileProgram(ast)
	if err != nil {
		return "", 0, 0, err
	}
	machine := newVM(prog, l.opts)
	out, rerr := machine.run()
	if rerr != nil {
		return "", uint64(machine.peakBytes), machine.numGC, rerr
	}
	return out, uint64(machine.peakBytes), machine.numGC, nil
}
