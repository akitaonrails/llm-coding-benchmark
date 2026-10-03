# SPEC — the `v41lang` toy language (AUTHORITATIVE)

This file is the **single source of truth** for the language the model implements (package `lang`) and that the
reference implements. The hidden grader checks **exact stdout** and **exact accept/reject** of type checking, so
every output format and typing rule below is pinned. When the prose and the grader disagree, the grader wins and
this file has a bug — but they are written to agree.

The language is a small statically-typed, call-by-value functional language with Hindley–Milner inference,
let-polymorphism, the value restriction, row-polymorphic records, lists, mutable references, and a `print`
builtin. All functions are **curried** (one argument each); multi-argument sugar desugars to nested lambdas.

---

## 1. Lexical structure

- **Whitespace**: spaces, tabs, carriage returns, newlines — insignificant except as token separators.
- **Comments**: `--` to end of line.
- **Integer literals**: `[0-9]+`, decimal, non-negative in the lexer. Fit in a signed 64-bit integer.
  Negation is the unary operator `-` (see §3), so `-5` is `-` applied to `5`.
- **String literals**: `"` … `"` with escapes `\n` (newline), `\t` (tab), `\\` (backslash), `\"` (quote).
  No other escapes are recognized (any other `\x` is a lex error).
- **Boolean literals**: `true`, `false`.
- **Identifiers**: `[A-Za-z_][A-Za-z0-9_]*` that are not keywords.
- **Keywords**: `let` `rec` `in` `if` `then` `else` `true` `false`.
- **Operators / punctuation**: `+ - * / ^ == != < <= > >= -> = . | ! := ( ) { } [ ] , \`
  (`\` begins a lambda; `!` is prefix dereference; `:=` is reference assignment).

Prelude identifiers (bound in the initial environment, not keywords): `print cons head tail null not ref`.
A program may shadow them with its own `let`.

---

## 2. Grammar (concrete)

```
program    ::= expr
expr       ::= "let" ["rec"] ident {ident} "=" expr "in" expr
             | "if" expr "then" expr "else" expr
             | "\" ident {ident} "->" expr
             | assign
assign     ::= cmp [":=" assign]                 -- right-assoc; left side must be a Ref
cmp        ::= concat [("=="|"!="|"<"|"<="|">"|">=") concat]   -- non-associative (at most one)
concat     ::= add ["^" concat]                  -- right-assoc string concat
add        ::= mul {("+"|"-") mul}               -- left-assoc
mul        ::= unary {("*"|"/") unary}           -- left-assoc
unary      ::= "-" unary | "!" unary | app
app        ::= postfix {postfix}                 -- application, left-assoc, juxtaposition
postfix    ::= atom {"." ident}                  -- record field access, left-assoc
atom       ::= int | string | "true" | "false"
             | ident
             | "(" expr ")"
             | "[" [expr {"," expr}] "]"                 -- list literal
             | "{" [ident "=" expr {"," ident "=" expr}] "}"         -- record literal
             | "{" expr "|" ident "=" expr {"," ident "=" expr} "}"  -- functional record update
```

Sugar:
- `\x y z -> e`  ≡  `\x -> \y -> \z -> e`.
- `let f a b = e1 in e2`  ≡  `let f = \a -> \b -> e1 in e2`.
- `let rec f a b = e1 in e2`  ≡  `let rec f = \a -> \b -> e1 in e2`  (the `rec` binding `f` is in scope in `e1`).
- A `let rec` right-hand side **must be a lambda** (syntactically `\…`); otherwise it is a type/compile error.

Precedence, lowest → highest: `let`/`if`/`\` (prefix forms) < `:=` < comparisons < `^` < `+ -` < `* /` <
unary `-`/`!` < application < `.` < atoms.

---

## 3. Operators and builtins

| form            | type                              | notes                                             |
|-----------------|-----------------------------------|---------------------------------------------------|
| `a + b` `a - b` `a * b` `a / b` | `Int -> Int -> Int` | `/` is truncated toward zero; `/ 0` is a runtime error |
| `-a`            | `Int -> Int`                      | unary negation                                    |
| `a == b` `a != b` `a < b` `a <= b` `a > b` `a >= b` | `Int -> Int -> Bool` | compare integers only |
| `a ^ b`         | `String -> String -> String`      | string concatenation                              |
| `print e`       | `∀a. a -> a`                      | formats `e` (§5) + `"\n"` to stdout; returns `e`  |
| `cons`          | `∀a. a -> [a] -> [a]`             | prepend                                           |
| `head`          | `∀a. [a] -> a`                    | head; runtime error on `[]`                       |
| `tail`          | `∀a. [a] -> [a]`                  | tail; runtime error on `[]`                       |
| `null`          | `∀a. [a] -> Bool`                 | is the list empty                                 |
| `not`           | `Bool -> Bool`                    |                                                   |
| `ref e`         | `∀a. a -> Ref a`                  | allocate a mutable cell (an application: see §6.3)|
| `!r`            | `∀a. Ref a -> a`                  | dereference                                       |
| `r := e`        | `∀a. Ref a -> a -> a`             | store; result is the stored value                 |

`cons head tail null not ref print` are ordinary (prelude-bound, first-class) values and may be partially
applied. `== != < <= > >=`, `+ - * / ^`, unary `-`/`!`, and `:=` are operators, not first-class values.

---

## 4. Evaluation semantics

Call-by-value, left-to-right. `if` evaluates the condition then exactly one branch. `let x = e1 in e2` binds
`x` to the value of `e1` while evaluating `e2`. `let rec f = \… in e2` binds `f` to a closure that can call
itself. Closures capture their defining environment. Application `f a` evaluates `f` to a closure (or builtin),
`a` to a value, then runs the body. Tail calls run in constant control-stack space (tail-call optimization),
so deep recursion does not overflow.

Runtime errors (returned via `err` from `Run`, with whatever was printed before the error discarded — i.e. on a
runtime error `Run` returns `("", err)`): division by zero, `head`/`tail` of `[]`, and exhausting the VM heap
limit. Well-typed programs do not otherwise fail at runtime.

---

## 5. `print` output format (EXACT — the grader greps stdout byte-for-byte)

`print v` writes the formatting of `v` below, followed by a single `"\n"`. Formatting is **uniform** (a value
prints the same at top level and when nested inside a list/record):

- **Int**: decimal, no leading zeros, a leading `-` if negative. `0`, `42`, `-7`.
- **Bool**: `true` or `false`.
- **String**: ALWAYS double-quoted with escapes re-applied: `"` wrapped, and inside, newline→`\n`, tab→`\t`,
  `\`→`\\`, `"`→`\"`. So the value of `"a\"b"` prints as `"a\"b"` (6 characters).
- **List**: `[` + elements formatted recursively and joined by `, ` (comma then space) + `]`. Empty: `[]`.
  Example: `[1, 2, 3]`, `["a", "b"]`, `[[1], []]`.
- **Record**: `{` + `field = value` entries joined by `, ` + `}`, with **fields in ascending byte order of the
  field name** (deterministic regardless of literal/update order). `field` is the bare name, then ` = ` (space
  equals space), then the value formatted recursively. Empty record: `{}`. Example: the value of
  `{b = true, a = 1}` prints as `{a = 1, b = true}`.
- **Ref**: `<ref>` (the cell contents are not shown — avoids divergence on cyclic refs).
- **Function** (closure or builtin): `<fun>`.

There is no trailing space anywhere; the only newline is the one `print` appends.

---

## 6. Typing rules (Hindley–Milner + rows)

Types: `Int`, `Bool`, `String`, type variables, `t1 -> t2`, `[t]` (list), `Ref t`, and record types
`{ l1: t1, …, ln: tn | ρ }` where the row tail `ρ` is either empty (a closed record) or a **row variable**
(an open / extensible record). `TypeCheck` returns `nil` iff the program has a principal type.

### 6.1 Let-polymorphism (generalization)
At `let x = e1 in e2`, infer `e1`'s type, **generalize** the type variables not free in the surrounding
environment, bind `x` to that scheme in `e2`, and instantiate the scheme afresh at each use. So
`let id = \x -> x in …` gives `id : ∀a. a -> a` and `id` may be used at `Int` and at `Bool` in the same program.
(`let rec` generalizes the same way after the recursive binding is solved.)

### 6.2 The value restriction
Generalization at `let` applies **only when `e1` is a syntactic value**: an identifier, a literal
(int/bool/string), or a lambda. If `e1` is not a syntactic value (e.g. an application such as `ref (\x -> x)`
or `id id`), `x` gets a **monomorphic** type — its free variables are left ungeneralized. This keeps mutable
references sound: `let r = ref (\x -> x) in …` does **not** give `r` a polymorphic cell type, so using the one
cell at two element types is correctly rejected.

### 6.3 Unification, the occurs check
Unification is first-order with the **occurs check**: unifying a variable `a` with a type that contains `a`
(e.g. `a = a -> b`) is rejected as an infinite type. Hence `\x -> x x` does **not** type-check.

### 6.4 Row-polymorphic records (the twist)
Field access `r.a` constrains `r` to `{ a: α | ρ }` with a **fresh row variable** `ρ`, i.e. "any record that has
at least field `a`". So a function `\r -> r.a` has principal type `∀a ρ. { a: a | ρ } -> a` and accepts both
`{a=1, b=2}` and `{a=1, c=3}`, while rejecting `{b=2}` (no field `a`). Record **literals** `{a=…, b=…}` have a
**closed** row (empty tail — exactly those fields). **Functional update** `{ r | a = e }` requires `r` to have
field `a` and yields a record equal to `r` but with `a` re-bound to `e` (the field's type may change); it is
row-polymorphic in the other fields. Duplicate field names in a literal or update are a type error.

Record unification is by row rewriting: two records unify iff they have the same set of present labels with
unifiable field types and unifiable tails (a closed row only unifies with a row having exactly the same labels;
an open row absorbs the extra labels into its tail variable). A non-row (textbook Algorithm W) implementation
cannot accept `{a=1,b=2}` and `{a=1,c=3}` at the same `\r -> r.a` — that is the decisive row test.

### 6.5 Everything else
`if c then a else b`: `c:Bool`, `a` and `b` unify, result is their type. Arithmetic/comparison/concat per §3.
List literals: all elements unify; `[]` has type `∀a. [a]` at each occurrence (it is a value). `print`, `cons`,
`head`, `tail`, `null`, `not`, `ref`, `!`, `:=` have the schemes in §3. A program's top-level type may be any
type (it need not be a particular type); it only needs to *have* a principal type.

### 6.6 Error reporting
Ill-typed programs return a non-nil `error` whose message begins with a stable, greppable code. The grader only
checks nil vs non-nil, but the reference uses these prefixes: `type error:` (general mismatch),
`occurs check:` (infinite type), `unbound:` (unbound identifier / field-less record access that resolves to a
closed row without the field), `parse error:`, `lex error:`.

---

## 7. Heap / GC (runtime half)

The VM allocates its values (strings, list cells, records, closures, environment frames, reference cells) on a
**managed heap** with a generational mark-sweep collector (a nursery for fresh objects, promotion of survivors
to an old generation, a write barrier recording old→young pointers, and a major collection that reclaims
**cycles**). Under sustained allocation the live set — not the total allocated — bounds memory: a program that
allocates millions of short-lived objects, or repeatedly builds and drops cyclic structures (e.g. self-
referential `let rec` closures), runs in **bounded** heap and completes. The VM enforces a hard live-heap cap
and returns a runtime error if a program's *live* set truly exceeds it (a non-collecting runtime trips this; a
correct one never does on the gauntlet's programs).

Optional grader hook (fetched by reflection, see harness/maker.go): a handle may expose
`RunInstrumented(source string) (output string, peakHeapBytes uint64, numCollections int64, err error)`
reporting the high-water mark of its own live heap. If absent, the grader falls back to a wall-clock/process-
memory budget that a leaking runtime still blows.
