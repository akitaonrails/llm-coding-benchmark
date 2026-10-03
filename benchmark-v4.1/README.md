# v4.1 — "The Hard Cut": can a small model + harness match the frontier on genuinely hard, long-horizon programming?

v4.1 is a **separate** suite from v4 (v4 = Rails + sabotage vigilance; untouched). Its thesis:

> **A small model with strong long-horizon post-training + a good agentic harness can land in the
> frontier band on genuinely hard programming — at a fraction of the cost.**

The qualifier that makes it rigorous: it is **not** "any small model + harness." Comparable-size open
models (gpt-oss-120b, Qwen-27B) **DNF** long agentic builds — they can't *drive* the harness. So the claim
is *small + strong long-horizon post-training + harness ≈ frontier*, and the **contrast set is the proof**:
the subject must land in the band while same-size controls fall short.

## Framing (deliberate)
- **Tools-on is the headline and the real product.** Relying on the harness is credited, not penalized — a
  shipping system is model+harness. We do not frame "weaker tools-off" as a defect.
- Primary axis = **objective pass-rate on hard, long-horizon tasks**, same harness for everyone.
- Secondary (neutral, optional) = an offline/limited-retrieval "deployment profile" for airgapped buyers —
  a spec-sheet line, not a gotcha.

## Why these problems discriminate
Every problem is **(a)** a long accumulating multi-sprint build (the test suite grows; prior components must
keep passing — where OSS loses coherence and DNFs); **(b)** graded by an **objective adversarial harness**
revealed only at the end (fault injection, fuzzing, differential oracles, sanitizers — no subjective scoring);
**(c)** carries a **non-standard twist** that breaks memorized reference implementations (tools-on can fetch
the *concept*, not a copy-paste answer — the fetchable-knowledge vs trained-skill split the thesis needs).

## Problems
- **P1 — Linearizable replicated KV on a Raft variant (Go).** [building first — this file's sibling `raft/`]
- **P2 — Transactional storage engine: B+tree + WAL + SSI + SQL + planner.** [after P1 lands cleanly]
- **P3 — Typed language: HM inference + bytecode VM + generational GC.** [after P1]

## Tiers (same harness: opencode, tools-on, equal budget)
| tier | models | role |
|---|---|---|
| anchors | Fable (best Claude), GPT-6 (best Codex) | the frontier band to match |
| subject | Genesys PI house + enterprise (54–70B hybrid) | small-but-reinforced |
| controls | gpt-oss-120b, Qwen-27B | same size class, not reinforced for long agency |

Expected shape that confirms the thesis: **anchors and Genesys clear the gauntlet; controls DNF partway.**

## Scoring
`score = objective grader pass-rate` (per component + the hidden adversarial reveal), reported alongside
**completion depth** (sprints cleared before incoherence — the OSS-DNF axis) and **cost/wall** (the efficiency
story). No subjective grading; the grader is code.

## Integrity
- **Validate the grader before any model run** (must pass a correct reference impl AND fail injected bugs — a
  grader that passes/fails everything is worthless). This mirrors the `verify_scores.py` "proven negative test"
  discipline.
- Same shield/isolation as v4 (isolated XDG, git-sandboxed project, no peer/answer-key access).
- Anti-contamination: non-standard twists; the hidden grader catches memorized-but-subtly-wrong solutions.
- NDA: nothing confidential from vendor conversations lives in this tree.
