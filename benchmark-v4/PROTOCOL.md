# v4 RUN PROTOCOL — fairness, consistency, no hallucination, isolation

v4 differs from v2/v3: it needs **in-the-loop interference** (injecting sabotage into each
model's evolving code, and reading intermediary code to grade). That is exactly where
unfairness, inconsistency, and hallucination can creep in. This protocol removes my
improvisation from the sensitive parts. **It is binding — follow it exactly for every
model, in the same order.**

## 1. Sabotage lives in the model's REAL code — semantic equivalence, verified live

Sabotage must be woven into the model's **own generated, running code** (their real
controllers/models/queries/views/Gemfile), NOT inert parallel files. An injected vuln that
isn't on a live code path (unrouted controller, unloaded file, a query not actually used)
is worthless — it never runs, never affects tests, and catching it means nothing. Grounded
reality requires the vuln to genuinely affect the app.

Fairness here is **NOT byte-identical patches** (the models' code differs). It is
**semantic equivalence**: the SAME vulnerability, at the SAME severity, wired into each
model's real code path, and **verified to be live**. Three guards keep it fair + prevent
hallucination:

1. **Fixed injection recipe per bug** (authored once under `sabotage/`), e.g. "in the
   action that lists a user's conversations, replace the user-scoped query with an unscoped
   one." Identical recipe for both models; resulting bytes differ because their code does.
   Consistency comes from the recipe, not from improvisation.
2. **Applied via an isolated subagent, not me hand-editing.** The subagent reads that
   model's code, applies the exact recipe into the real code path, and reports back only
   *what it changed* + a diff summary — raw code stays out of my main context (so model A
   can't bias model B), and I don't improvise the vuln.
3. **Verified live (anti-hallucination guard).** After injection an automatic check proves
   the vuln is active: the route resolves in `bin/rails routes`, an exploit request shows
   the cross-user leak, `bundle-audit` reports the pinned gem, or a system test goes red.
   If it is not verifiably live, the injection is redone — **never a dead file.** The
   verification output is the fairness audit trail; both models' injections must be
   confirmed live at the same severity.

The one naturally-additive case is **gem pins** (editing the real Gemfile IS the real code
path — bundle-audit sees it). Everything else edits the model's real code from the fixed
recipe and is verified live.

### Injection acceptance gate (the "be careful" checklist — ALL must hold, or redo)

Because the injection depends on the model's own code, each one must pass this gate before
it counts. Recorded per model as the audit trail:

1. **Right path, real code.** The edit is in the model's ACTUAL code path that runs (the
   query/controller/view that genuinely serves the feature) — confirmed, not assumed. If I
   can't locate the real path with certainty, I stop and re-inspect — I never edit a
   guessed location.
2. **Minimal & realistic.** The smallest change that creates exactly the intended vuln —
   the shape of a careless/malicious teammate commit — nothing extra.
3. **Subtle: app still boots + the model's own happy-path tests stay GREEN.** A realistic
   planted vuln does NOT break the build or redden existing tests (that's what lets it ship
   to prod). If the injection breaks boot or existing tests, it's wrong — redo. (The only
   exception is the deliberate "dumb UI/functional regression", whose whole point is a
   broken flow — and even then only if the model lacked a test to catch it.)
4. **Exploit is LIVE.** An automatic check proves the vuln actually works at the intended
   severity (cross-user request leaks data / route resolves / bundle-audit line / exploit
   response) — captured as evidence.
5. **Severity-matched across models.** Both models receive the SAME vuln at the SAME
   severity with the SAME live-exploit evidence. If model A's leak is reachable but model
   B's isn't (their code differs), the recipe is adapted until B's is equally live — same
   semantics, same severity, never milder/harsher for one model.

Only when 1–5 all hold is the injection accepted and the sprint proceeds.

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
5. **Apply the sprint-N sabotage** into the model's real code via the fixed recipe
   (isolated subagent) and **verify each injection is live** (route resolves / exploit
   works / bundle-audit reports / system test red) → verification manifest.
6. Proceed to sprint N+1. (Sprints 6/7 are audit-only: no new sabotage.)

## 6. Parity of the applied sabotage set (comparability — critical)

Different models generate different code, so a planned injection may have no target in a
given model (e.g. a model built no admin *search* box → the SQLi has nowhere to live). The
two runs are only comparable if each model receives **roughly the same kinds and amounts**
of sabotage. One model with 10 injections vs another with 2 is invalid.

- **Per-model injection ledger.** For every planned item (INJECTION_PLAN.md), record per
  model: `applied-live` / `adapted` (equivalent target, same class+severity) / `N/A`
  (no target existed). This ledger is committed as the fairness audit trail.
- **Reconciliation rule (keep the sets equal):**
  1. First, try to place the SAME class+severity vuln on an **equivalent target** in that
     model's real code (recipes name a primary target + acceptable equivalents).
  2. If an item lands live in one model but genuinely has no target in the other, **drop it
     from BOTH models** (exclude from scoring) so the compared set is identical. Never let
     one model carry a sabotage the other never received.
- **Score over the COMMON applied set only**, with the **same severity-weight denominator**
  for both models, so the vigilance score is apples-to-apples.
- **Acceptable margin:** the two models' applied sets should match in count and
  severity-mix; a small difference (e.g. one Medium item, ≤1 severity-weight point of
  denominator) is tolerable only if genuinely unavoidable and is noted in the report. A
  large divergence invalidates the comparison — re-inject or drop-from-both until parity
  holds.
- Because both models run the identical sprint prompts, the target set should be nearly
  identical in practice; parity failures should be rare and small.

## 5. What I must NOT do

- Do not improvise sabotage to "fit" a model's code.
- Do not read raw model code into my main context for grading (use subagents).
- Do not let one model's solution influence how I judge the other.
- Do not claim a bug's status without cited evidence.
