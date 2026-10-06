# v4.1 — P1 (Raft) results: can a small model + harness match the frontier on hard, long-horizon code?

_2026-10-03. Suite: `benchmark-v4.1/`. Separate from v4 (Rails + sabotage vigilance; untouched)._

> Historical P1 report. The [P4–P6 follow-up](success_report.v4_1.frontier.md),
> completed 2026-10-05, found Genesys House scores of **40.901 / 0 / 0** on
> harder FrontierSWE tasks. The parity conclusions below are limited to the
> original tasks; they do not establish general frontier equivalence.

## Headline
On the hardest problem in this project — an **8-sprint accumulating build of a Raft consensus variant +
a linearizable key/value store** (PreVote, CheckQuorum, joint-consensus membership, learners, snapshots;
graded by an objective 24-test `-race` gauntlet incl. a **Porcupine linearizability check**):

| model | role | harness | score | sprints | notes |
|---|---|---|---:|:--:|---|
| **Genesys PI house** | subject | opencode (lua) | **100.0** | 8/8 | all 24 pass — incl. joint membership, learner catch-up, KV linearizability |
| **Claude Fable 5.1** | anchor | Claude Code (sub) | **100.0** | 8/8 | all 24 pass |
| **GPT-6 astra** | anchor | Codex (sub) | **100.0** | 8/8 | all 24 pass |
| Genesys PI enterprise | subject | opencode (lua) | 33.7 | 0/8 | basics only; fails hard consensus + all KV |
| gpt-oss-120b | control | opencode (OR) | **0.0** | 0/8 | DNF — no working raft by S2 |
| gpt-oss-20b | control | opencode (OR) | **0.0** | 0/8 | DNF |
| qwen3-32b | control | opencode (OR) | **0.0** | 0/8 | DNF — incoherent, broke its own imports |

**The thesis holds, and cleanly:**
1. **Small + strong post-training + harness ≈ frontier.** Genesys house (a 54–70B hybrid on opencode) ties
   Fable and GPT-6 at a perfect 100 on genuinely hard distributed-systems code — not a toy, but Raft +
   linearizable KV, the kind of task that separates real engineers.
2. **It is NOT trivial / NOT just "the harness."** Same-size open models on the *same* opencode harness
   (gpt-oss-120b/20b, qwen3-32b) all **DNF at 0** — the harness doesn't rescue a model without the
   long-horizon agentic competence to drive it.
3. **It is the house MODEL, not the Lua API/harness.** The cheaper **Genesys enterprise** tier, on the
   identical lua/opencode setup, scores **33.7** (correct elections/snapshots but broken consensus edge
   cases and no working KV). So the result is a property of the house checkpoint, not a Lua-side advantage.

## Method & honesty
- **Best-config comparison (not a harness-controlled A/B):** each model ran in its best real configuration —
  Genesys/controls on opencode, Fable on Claude Code, GPT-6 on Codex (subscription). This matches the
  "model+harness is the shipping system" framing; it is NOT a same-harness experiment (documented confound).
- **Objective grading:** the score is a Go test gauntlet (24 tests, `-race`), not a judgment call. Models got
  `harness/` + `CONTRACT.md` (fair disclosure of what's tested); the `grader/` + `reference/` were hidden and
  shielded. Grading runs in a clean workspace with only the model's `raft/`+`kvraft/` source (no tampering).
- **The grader was validated sound + sensitive** (passes a correct reference; injected bugs each fail the
  right test) BEFORE trusting results.
- **Integrity note (caught and fixed):** the first full run zeroed *every* model on two grader bugs (not model
  failures — the runs were intact): a `KVServerHandle` signature mismatch that broke test compilation, and
  single-process test running where one deadlocking test timed out the whole suite. Both were found by
  re-verifying that the *reference* also wrongly scored 0, fixed (concrete handle + raft peer by reflection;
  per-test isolation), re-validated, and the runs re-graded. No re-runs were needed.

## The one real caveat: top-end saturation
Three models hit **exactly 100** (house, Fable, GPT-6). So P1 **confirms Genesys is in the frontier band** and
**cleanly separates frontier (100) from same-size OSS (0)** — but it does **not differentiate among frontier
models** (all perfect). This echoes the v3 lesson that well-scoped tasks saturate at the top. The valuable
signal here is exactly the one the thesis needs (small matches frontier; OSS can't), not a frontier ranking.

## What this does and doesn't support
- **Supports:** "a small, well-reinforced model + a good agentic harness is a shippable frontier-class coding
  system, where comparable open models are not." That retires "only a giant lab can make something usable."
- **Does not support:** ranking Genesys *above* or precisely *against* Fable/GPT-6 (saturated); nor any claim
  about tools-off / airgapped performance (not measured here — tools-on is the shipping config, by design).

## Next
P2 (transactional storage engine: B+tree + WAL + SSI + SQL) and P3 (typed language: HM inference + bytecode VM
+ generational GC) are designed and approved to run after P1. Given P1's top saturation, they are worth running
mainly to confirm the pattern on a *different* hard domain and to probe whether a harder task de-saturates the
frontier — but expect the same shape (frontier incl. Genesys clears it; OSS controls DNF).
