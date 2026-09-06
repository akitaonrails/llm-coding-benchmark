# v4 RUN PROTOCOL — fairness, consistency, no hallucination, isolation

v4 differs from v2/v3: it needs **in-the-loop interference** (injecting sabotage into each
model's evolving code, and reading intermediary code to grade). That is exactly where
unfairness, inconsistency, and hallucination can creep in. This protocol removes my
improvisation from the sensitive parts. **It is binding — follow it exactly for every
model, in the same order.**

## 1. Sabotage is PRE-AUTHORED and SCRIPT-APPLIED (never improvised per model)

- Every injection is a **fixed artifact authored ONCE** (committed under `sabotage/`): a
  complete vulnerable file to copy in, an exact route line to append, an exact `gem "x",
  "ver"` line, an exact file path to delete. **Byte-identical for every model.**
- Injection is done by `apply_sabotage.sh <sprint> <project>` — a script, not me
  hand-editing each model's code. I do NOT read a model's code and then "write a matching
  vulnerability" — that would vary per model and invites hallucination.
- Prefer **additive** injections (new vulnerable controller/route/initializer, gem pin) so
  they apply uniformly regardless of the model's structure. Any injection that must target
  the model's own code uses an **exact, pre-written recipe** (fixed string/anchor), and if
  the anchor is absent the script logs "N/A for this model" rather than improvising.
- After applying, the script **prints a manifest** of exactly what it changed; both models'
  manifests must match. This is the fairness audit trail.

## 2. Grading reads code in ISOLATED SUBAGENTS (keep my context clean + consistent)

- I do NOT read each model's full generated codebase in my main context — it is large,
  noisy, and reading model A then model B would let A's code bias B's judgment.
- Each sprint's review runs in a **fresh subagent** given: the model's `project/` path, the
  **fixed grading rubric** (`grading/rubric.md`), and the list of planted bugs with their
  exact signatures. The subagent returns ONLY a **structured verdict** (per-bug: fixed /
  present / regressed; per-dimension scores; commit-log summary) — never dumps raw code
  back into my context.
- Both models are graded by the **identical rubric and the identical subagent prompt**.
  Same checklist, same order, same evidence requirements.

## 3. Determinism & fairness rules

- Same sprint prompts, same sabotage artifacts, same injection order, same rubric, same
  grade-timeout, same reasoning effort tier where applicable, for BOTH models.
- Per-model isolation (shield the grading key + reference + sibling outputs; git-sandbox).
- Every artifact (prompts, sabotage files, rubric, per-model manifests, verdicts) is
  committed — the run is fully auditable and reproducible.
- **No hallucination rule:** I never assert a bug is "present/fixed" from memory or
  inference. A verdict cites concrete evidence (file:line, a grep hit, a bundle-audit line,
  a failing/passing test). If evidence is absent, the verdict is "unknown", not a guess.

## 4. The per-sprint loop (identical for every model)

1. Give the model sprint-N prompt in its accumulating `project/` (isolated, git-sandboxed).
2. Model works; capture cost/time/tokens; the model commits its own work.
3. Snapshot/record the model's git log for the commit-hygiene dimension.
4. Grade sprint N in a subagent (rubric + planted-bug signatures) → structured verdict.
5. **Apply the sprint-N sabotage** via `apply_sabotage.sh` (fixed artifacts) → manifest.
6. Proceed to sprint N+1. (Sprints 6/7 are audit-only: no new sabotage.)

## 5. What I must NOT do

- Do not improvise sabotage to "fit" a model's code.
- Do not read raw model code into my main context for grading (use subagents).
- Do not let one model's solution influence how I judge the other.
- Do not claim a bug's status without cited evidence.
