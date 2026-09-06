# External benchmark analysis — `rails/ai-evals` ("Agents on Rails")

Analyzed 2026-09-06. Question we set out to answer: people say this benchmark is "not
saturated yet" — is that true? Short answer: **essentially true, but with an important
nuance**, and its design independently validates our own v3 findings.

Source: [rails/ai-evals](https://github.com/rails/ai-evals) ·
[methodology.md](https://github.com/rails/ai-evals/blob/main/methodology.md) ·
first report [rubyonrails.org 2026-08-13](https://rubyonrails.org/2026/8/13/agents-on-rails-the-first-benchmark-report) ·
[open-source announcement 2026-08-24](https://rubyonrails.org/2026/8/24/agents-on-rails-lemans).
(Numbers below are THEIR published results, gathered by a research agent — not our runs.)

## What it is
The task corpus for **"Agents on Rails,"** the Rails Foundation's ongoing coding-agent
benchmark, built by **Evil Martians**. Rails-specific, real-application work (not general
puzzles).

- **Stage 1 = 21 atomic tasks** against **Writebook** (a real Rails app; sandbox image
  `ghcr.io/evilmartians/lemans-writebook`, Writebook v1.2.1) + one `hello-world` pipeline
  check.
- Task mix: bug fixes, security hardening, performance, small features, a flaky test
  suite. Each is framed as a realistic report (bug/security/feature) and **hinges on one
  Rails API the instructions never name** — the agent must *know* the right current Rails
  API without being told.
- Layout: `tasks/<name>/` (instructions, env patch that seeds the defect, reference
  solution patch, hidden verification test), `docker/`, `runs/` (raw outputs), `bench.yml`,
  `methodology.md`, MIT. Tasks carry a **canary string** to stay out of training data.

## How it grades (deterministic, no LLM judge)
After the agent finishes, graded files are restored from a pre-agent snapshot, then:
```
bin/rails test && ruby "$TESTS/verification_test.rb"
```
A run passes only if **the app's own suite stays green AND hidden verification tests
pass**. Tests check **behavior, not implementation** (multiple valid solutions pass).
**3 runs per model per task.** Metrics: accuracy (share of passing runs), cost/tokens,
wall-clock + step counts, and **"Rails API recall"** (did it use the intended current
API vs. rolling its own/outdated pattern). Difficulty from measured first-pass success:
easy ≥90%, medium 50–89%, hard <50%.

## Published scores (Stage 1, 8 frontier + open-weight models)
| Model | Accuracy | Notes |
|---|---|---|
| Claude Opus 5 | **92%** (58/63) | top accuracy; best API recall of the field at **only 35%** |
| Claude Fable 5 | ~95% | refused one security task |
| Kimi K3 | ~90% | ~half the cost of Sol |
| GPT-5.6 Sol | 84% | "best overall combo": ~$0.52, ~5 min/run |
| GPT-5.6 Luna | 73% → **89%** at max reasoning | cheapest (~$0.012/run low effort) |
| DeepSeek V4 Flash | — | API recall just **8%** |

`runs/` holds dated raw folders (`2026-08-13-atomic-tasks`,
`2026-08-24-atomic-tasks-new-models`, `2026-09-01-...-fable-5-1-and-glm-5-3-flash`).

## Saturation verdict: NOT saturated overall — but raw accuracy is near the ceiling
- **Toward saturation:** top is 92–95%; **6 of 21 tasks are solved by every run of every
  model** (~⅓ of the corpus no longer discriminates).
- **Against (the stronger case):** no model hits 100%; a real **hard tail** (hardest task —
  purging embedded images, "a bug whose visible half hides a second one" — solved in only
  **8/24 runs, ~33%**); the most discriminating metric, **Rails API recall, tops out at
  35%** and runs as low as 8% — huge headroom; multi-dimensional (accuracy × cost × speed
  × recall) so models separate even where accuracy clusters high. Luna "had more room to
  grow than any model in the field" (73%→89% with more reasoning).

## Why it isn't (fully) saturated
- **Latent-API design:** the task never names the required Rails API → measures *recall of
  current idiomatic Rails*, not just producing working code. This is why recall is 35%
  even when accuracy is 92%.
- **Real-app, multi-file context** with seeded defects that have **hidden second halves**.
- **Strict deterministic grading:** must pass the existing suite *and* hidden tests;
  snapshot-restored so it can't be gamed; no partial credit, no lenient judge.
- **Currency of framework knowledge:** rewards up-to-date idioms, penalizes outdated /
  custom reimplementations.

## Cross-validation with our v3 (the important part)
Their design independently matches what our v3 investigation converged on: **latent /
no-hints tasks, a real multi-file app, deterministic hidden grading, and a
multi-dimensional accuracy × cost × speed score.** Their conclusion matches ours too:
**raw working-code correctness is near parity at the frontier** (their 92–95% ≈ our
95–100%); the live signal has moved elsewhere.

The one axis that is NOT saturated for them — **framework-API currency ("recall")** — is
exactly the differentiator we had in **v2** (RubyLLM real-API vs hallucination = Tier
1/2/3) and *removed* in v3 by choosing pure-logic stdlib tasks. See
`docs/success_report.v2.md` and `docs/success_report.v3.md`.

## Actionable lever for us
To de-saturate v3's *quality* dimension, add an **API-recall axis**: tasks that hinge on
using a specific, **unnamed, current** library/framework API (Rails, or RubyLLM as in
v2), graded on whether the model used the real intended API — not just whether the code
runs. That is the one *grounded* axis demonstrably still separating the frontier. (Also
worth borrowing: stricter "must keep the whole existing suite green + no partial credit,"
and reporting accuracy over 3 runs to capture reliability.)
