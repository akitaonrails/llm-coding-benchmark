# LLM Coding Benchmark: Comprehensive Success Report

Last rewritten: 2026-04-25 using the standardized audit rubric in [`audit_prompt_template.md`](audit_prompt_template.md).

## What Was Tested

Each model was given an identical prompt to autonomously build a Ruby on Rails SPA chat application (a ChatGPT-like interface using RubyLLM). The prompt explicitly requires:

1. Rails app using newest Ruby + Rails from mise
2. No ActiveRecord, Action Mailer, or Active Job
3. SPA mimicking ChatGPT-like interface
4. Tailwind CSS
5. Hotwire + Stimulus + Turbo Streams
6. Componentize via Rails partials (no single-file CSS/JS dumps)
7. `OPENROUTER_API_KEY` via env var
8. No secrets in source files
9. RubyLLM (gem name `ruby_llm`) configured for OpenRouter + latest Claude Sonnet
10. Minitest unit tests for each component
11. Brakeman, RuboCop, SimpleCov, bundle-audit for CI
12. Dockerfile (functional, not placeholder)
13. docker-compose configuration
14. README with setup and run instructions
15. Stay in workspace root (no nested `chat_app/` subdir)

Cloud models ran a two-phase flow (phase 1: build, phase 2: validate boot/Docker). Local models ran phase 1 only. All models used `opencode run --agent build --format json` as the harness, except GPT 5.4 and GPT 5.5 which used `codex exec --json` directly.

## Methodology

Scoring uses a 0-100 holistic rubric across 8 weighted dimensions:

| Dimension | Weight | What it measures |
|---|---:|---|
| Deliverable completeness | 25 | Dockerfile + compose + README + Gemfile artifacts per prompt checklist |
| RubyLLM correctness | 20 | API calls verified against gem source at `~/.local/share/mise/installs/ruby/4.0.2/lib/ruby/gems/4.0.0/gems/ruby_llm-1.14.1/` |
| Test quality | 15 | Tests exercise LLM path with mocks that match real API; error paths covered |
| Error handling | 10 | Rescue blocks around LLM calls, user-visible degraded UI |
| Persistence / multi-turn | 10 | Session cookie / cache good; singleton / class-var / none bad |
| Hotwire / Turbo / Stimulus | 10 | Real Turbo Streams, partial decomposition, Stimulus controllers |
| Architecture | 5 | Service/model separation, avoiding code dumps in controllers |
| Production readiness | 5 | Multi-worker safe, no XSS, no committed `.env`, CSRF intact |

Tier mapping:
- **A (80–100)**: ship as-is or with trivial (<30 min) patches
- **B (60–79)**: 1–2 hours to ship; architecture is sound, minor gaps
- **C (40–59)**: major rework needed — core bugs or missing deliverables
- **D (<40)**: throw away or use only for architectural inspiration

### Scope and limitations

This is a deliberately narrow benchmark: one realistic Rails/RubyLLM/Hotwire task, one fixed prompt, and one audited generated application per model run. It is useful for comparing how models handle this kind of long, agentic, framework-heavy coding session, but it is not a universal measure of programming ability across every language, stack, or workflow.

Scores are audited single-run outcomes, not statistical averages. They should be read as "what this model produced in this run under this harness," not as variance-stable leaderboards. A single API recall failure can dominate the score in this benchmark because the app's core feature depends on correct RubyLLM usage; conversely, a model that has memorized or verified the RubyLLM API can jump sharply. The GLM 5.1 → 5.2 result is both a real improvement for this task and a reminder that this benchmark is highly sensitive to framework/library knowledge.

Use the rankings as evidence for this task family:
- **Large-repo or long-session agentic work**: prefer models with high scores, large usable context, strong test doubles, and correct library APIs.
- **Small bounded fixes or tests**: cheaper Tier B models may be sufficient if you inspect the generated code.
- **Local/offline experimentation**: current local runs are useful for learning infrastructure limits, but most are not production replacements yet.
- **Production-critical changes**: treat any generated app as a starting point; run the app, read the integration code, and verify secrets, tests, persistence, and Docker paths.

### Key API verification results (prevents recurring misclassification)

Earlier rounds of this benchmark made contradictory calls about the RubyLLM API. Direct inspection of the gem source established:

**Real public methods** — do not flag as hallucinations:
- `RubyLLM.chat(model:, provider:, assume_model_exists:, context:)` — top-level entry
- `RubyLLM::Chat.new(...)` — also valid public constructor
- `Chat#ask(message, with: nil, &)` — send
- `Chat#add_message(message_or_attributes)` — accepts a `Message` or a hash. `chat.add_message(role: :user, content: "x")` works because Ruby parses it as `chat.add_message({role:, content:})` — a positional hash. This is NOT a kwargs bug.
- `Chat#complete(&block)` — real public method
- `Chat#with_instructions(text, append:, replace:)` — system prompt
- `Chat#with_model`, `with_temperature`, `with_tools`, `with_params`, `with_headers`, `with_schema`, `reset_messages!`
- `response.content` — correct response accessor

**Confirmed hallucinations** (flag when present):
- `RubyLLM::Client.new` — class does not exist
- `Openrouter::Client` (wrong casing for `OpenRouter::Client` in the `openrouter` gem)
- `c.user(msg)` / `c.assistant(msg)` / `c.system(msg)` — invented fluent DSL
- `RubyLLM.chat(model:, messages: [...])` — batch signature doesn't exist
- `response.text` / `response.message` / `response.output_text` — should be `.content`
- `RubyLLM::Chat.new.with_model { |chat| ... }` — no block form
- OpenAI-style `response.choices.first.message.content` — RubyLLM returns a `Message`, not raw JSON

---

## Final Rankings (38 scored models)

All models scored against the same rubric. **Cost column updated 2026-07-09**: per-run costs recomputed from each run's recorded token logs at rates verified against the OpenRouter live API / vendor price pages on 2026-07-09; earlier figures under-counted cache-read tokens for several models (Opus 4.7/4.8, Gemini 3.1 Pro, MiniMax M3 corrected upward). "(hist.)" marks runs whose token logs are no longer available — original estimate retained. Full pricing audit: [`cost_analysis.md`](cost_analysis.md). Note the "RubyLLM OK" column is binary (API correct vs hallucinated) and is separate from the overall score — a model can have correct RubyLLM code and still score low if deliverables or tests are missing.

| Rank | Model | Score | Tier | RubyLLM OK | Provider | Runtime | Cost |
|---:|---|---:|:---:|:---:|---|---|---|
| 1 | **Claude Opus 4.7** | **97** | A | ✅ | OpenRouter | 18m | ~$7.00 |
| 1 | **GPT 5.4 xHigh (Codex)** | **97** | A | ✅ | OpenAI direct | 22m | ~$16 |
| 3 | **GPT 5.5 xHigh (Codex)** | **96** | A | ✅ | OpenAI direct | 18m | ~$10 |
| 4 | **Claude Opus 4.8** | **95** | A | ✅ | OpenRouter | 17m | ~$6.40 |
| 5 | Claude Fable 5 | 94 | A | ✅ | OpenRouter | 24m | ~$11.20 |
| 6 | Claude Fable 5 (re-release) | 93 | A | ✅ | OpenRouter | 18m | ~$8.30 |
| 6 | Gemini 3.5 Flash | 93 | A | ✅ | OpenRouter | 18m | ~$3.55 |
| 8 | Kimi K2.6 | 87 | A | ✅ | OpenRouter | 20m | ~$1.00 |
| 8 | GLM 5.2 (Z.ai) | 87 | A | ✅ | Z.ai | 43m | subscription |
| 8 | Grok 4.5 | 87 | A | ✅ | OpenRouter | 16m | ~$5.10 |
| 11 | Kimi K2.7 Code | 86 | A | ✅ | OpenRouter | 22m | ~$1.15 |
| 12 | Claude Opus 4.6 | 83 | A | ✅ | OpenRouter | 16m | ~$1.10 (hist.) |
| 12 | Nex-N2-Pro | 83 | A | ✅ | OpenRouter | 25m | ~$0.34 (was free) |
| 14 | Gemini 3.1 Pro | 79 | B | ✅ | OpenRouter | 14m | ~$3.10 |
| 14 | Sakana Fugu Ultra | 79 | B | ✅ | Sakana | 22m | subscription |
| 16 | Claude Sonnet 4.6 | 78 | B | ✅ | OpenRouter | 16m | ~$0.63 (hist.) |
| 16 | DeepSeek V4 Flash | 78 | B | ✅ | OpenRouter | 3m | ~$0.01 |
| 16 | MiniMax M3 | 78 | B | ✅ | OpenRouter | 53m (phase 2 DNF) | ~$1.25 |
| 16 | Qwen3.7 Max | 78 | B | ✅ | OpenRouter | 19m | ~$1.40 |
| 20 | Grok 4.3 | 72 | B | ✅ | OpenRouter | 15m | ~$1.70 |
| 21 | Qwen 3.6 Plus | 71 | B | ✅ | OpenRouter | 17m | ~$0.15 (hist.) |
| 22 | DeepSeek V4 Pro | 69 | B | ✅ | OpenRouter | 22m (DNF) | ~$0.05 |
| 22 | Kimi K2.5 | 69 | B | ✅ | OpenRouter | 29m | ~$0.10 (hist.) |
| 22 | Step 3.7 Flash | 69 | B | ✅ | OpenRouter | 27m | ~$0.80 |
| 25 | Xiaomi MiMo V2.5 Pro | 67 | B | ✅ | OpenRouter | 11m | ~$0.09 |
| 26 | GLM 5 | 64 | B | ✅ | OpenRouter | 17m | ~$0.11 (hist.) |
| 27 | Claude Sonnet 5 | 58 | C | ❌ | OpenRouter | 27m | ~$2.25 |
| 28 | Step 3.5 Flash | 56 | C | ⚠️ bypass | OpenRouter | 38m | ~$0.02 (hist.) |
| 29 | Qwen 3.5 35B | 55 | C | ✅ | Local (AMD) | 28m | free |
| 30 | GLM 4.7 Flash bf16 | 52 | C | ✅ | Local (AMD) | failed | free |
| 31 | GLM 5.1 (Z.ai) | 46 | C | ❌ | Z.ai | 22m | subscription |
| 32 | DeepSeek V3.2 | 43 | C | ❌ | OpenRouter | 60m | ~$0.07 (hist.) |
| 33 | Qwen 3.5 397B A17B (base) | 42 | C | ❌ | OpenRouter | 15m | ~$0.31 |
| 34 | MiniMax M2.7 | 41 | C | ❌ | OpenRouter | 14m | ~$0.30 (hist.) |
| 35 | Qwen 3.5 122B | 37 | D | ❌ | Local (AMD) | 43m | free |
| 36 | Qwen 3 Coder Next | 32 | D | ❌ | Local (AMD) | 17m | free |
| 37 | Grok 4.20 | 25 | D | ❌ | OpenRouter | 8m | ~$0.70 |
| 38 | GPT OSS 20B | 11 | D | ❌ | Local (AMD) | failed | free |

**Note on score adjustment**: The original audit rubric wrongly penalized `RUBY_VERSION=4.0.2` as a fake placeholder. It's actually the current stable Ruby (released 2026-03-17). Scores for every model except Gemini 3.1 Pro have been adjusted +3 to remove that deduction. Gemini used Ruby 3.4.1 (older LTS, valid) so its score is unchanged. Relative ordering is preserved; only **MiniMax M2.7 crossed a tier boundary (D → C)** due to this correction.

### Quality × Time × Cost (verified 2026-07-09)

Score alone doesn't answer "which model should I use?" — this table adds the two axes that matter in practice. **Score/$** is benchmark points per dollar of run cost (recorded tokens × verified 2026-07-09 rates). It rewards cheap models mercilessly, so read it *together with the tier*: a Tier B model isn't "80% as useful" as a Tier A model — it's a model whose output still needs 1-2 engineer-hours before it ships (see [`cost_analysis.md`](cost_analysis.md) for the full argument). Subscription-billed and local models are excluded from Score/$ (no marginal per-run price).

| Model | Score | Tier | Runtime | Cost/run | Score/$ | Value verdict |
|---|---:|:---:|---:|---:|---:|---|
| Nex-N2-Pro | 83 | A | 25m | ~$0.34 | 244 | **Best value in the benchmark** — Tier A at pocket change (was free at run time; now $0.25/$1.00 per M) |
| Kimi K2.6 | 87 | A | 20m | ~$1.00 | 87 | Cheapest *dependable* Tier A; rates rose ~30% since its run |
| Kimi K2.7 Code | 86 | A | 22m | ~$1.15 | 75 | Nearly K2.6 value; no system prompt |
| Gemini 3.5 Flash | 93 | A | 18m | ~$3.55 | 26 | Best quality-per-dollar above 90; the token churn eats the low per-M rate |
| Grok 4.5 | 87 | A | 16m | ~$5.10 | 17 | Fastest Tier A run, but K2.6 gives the same score for 5× less |
| Claude Opus 4.8 | 95 | A | 17m | ~$6.40 | 15 | The frontier-quality/price sweet spot among the 95+ cluster |
| Claude Opus 4.7 | 97 | A | 18m | ~$7.00 | 14 | Highest score per dollar of the two 97s |
| Claude Fable 5 (re-release) | 93 | A | 18m | ~$8.30 | 11 | Gemini 3.5 Flash matches it for 40% of the price |
| GPT 5.5 xHigh | 96 | A | 18m | ~$10 | 10 | — |
| Claude Fable 5 | 94 | A | 24m | ~$11.20 | 8 | — |
| GPT 5.4 xHigh | 97 | A | 22m | ~$16 | 6 | Co-leader on quality, worst $/point in Tier A |
| DeepSeek V4 Flash | 78 | B | 3m | ~$0.01 | 7800 | The Score/$ outlier — but Tier B: needs its known 30-second fix + review |
| Xiaomi MiMo V2.5 Pro | 67 | B | 11m | ~$0.09 | 744 | Cheap, but tests don't cover the LLM path |
| Step 3.7 Flash | 69 | B | 27m | ~$0.80 | 86 | Multi-turn broken at LLM level — cheap run, expensive fix |
| MiniMax M3 | 78 | B | 53m | ~$1.25 | 62 | Phase-2 DNF + secret-hygiene penalty |
| Qwen3.7 Max | 78 | B | 19m | ~$1.40 | 56 | — |
| Grok 4.3 | 72 | B | 15m | ~$1.70 | 42 | Superseded by Grok 4.5 at every axis except price |
| Gemini 3.1 Pro | 79 | B | 14m | ~$3.10 | 25 | Superseded by 3.5 Flash: +14 points for similar money |
| Claude Sonnet 5 | 58 | C | 27m | ~$2.25 | 26 | Below the productive floor — run cost is irrelevant |

**How to read it**: within Tier A, value peaks at Nex-N2-Pro ($0.34) and Kimi K2.6 ($1.00); the 93+ cluster starts at ~$3.55 (Gemini 3.5 Flash) and frontier 95+ at ~$6.40 (Opus 4.8). Below Tier A, low run cost is mostly an illusion — the fix cost is human time. The two defensible exceptions are DeepSeek V4 Flash (known, 30-second fix) and cases where you review everything anyway.

### What changed from the previous ranking

- **Grok 4.5** (added 2026-07-09, scored 87/100, Tier A, #8): the Grok family finally reaches Tier A — 25 (4.20/D) → 72 (4.3/B) → 87. Fixes all three of 4.3's failure modes (dead Stimulus wiring, bypassable test stubs, stale model pin) and uses a fully real RubyLLM surface with a DI'd client, latest sonnet-4.6, capped cookie persistence. Held to the 87 cluster (ties Kimi K2.6 and GLM 5.2) by a **double-send bug** the blind cross-audit caught: the controller appends the user message before the service replays history, so every user turn is sent to the LLM twice — and the service test's preconditions differ from production, masking it. Reasoning effort note: Grok 4.5's max effort is `high`, which is also its default (no xhigh tier), so the standard run is already highest-effort. ~$5.10 est. / 16m.

- **Claude Fable 5 re-release** (added 2026-07-02, scored 93/100, Tier A, #6 tie): separate run under `claude_fable_5_rerelease` after Anthropic/OpenRouter re-released Fable 5. It completed both phases in 17m39s and is **slightly worse but not benchmark-breakingly worse** than the original 94/A result. RubyLLM is still correct (`RubyLLM.chat` + `with_instructions` + `add_message` history replay + `ask` + `response.content`), and it fixes the original's biggest architectural weakness by storing conversations in `Rails.cache` with a 12h TTL instead of a process-local singleton. Offsetting deductions: the generated app still defaults to `anthropic/claude-sonnet-4.6` instead of the now-live Sonnet 5 / floating latest alias, phase 2 only validated `/up` rather than a full live HTTP chat, and the cache entry itself is TTL-bound but not hard-capped even though LLM history replay is capped. A manual post-run live `ChatCompletion` smoke test returned `live_chat_ok`.

- **Claude Sonnet 5** (added 2026-07-01, scored 58/100, Tier C, #26): newly available on Anthropic and OpenRouter (`anthropic/claude-sonnet-5` / `claude-sonnet-5`). The harness completed both phases in 27m and validated local boot, Docker build, and Docker Compose, but the generated app's first real chat request would crash before contacting the model: `ChatResponder#build_chat` assigns `chat.messages = history`, while RubyLLM 1.16 exposes `messages` and `add_message` but no `messages=` writer. The service test's `FakeChat` defines `attr_accessor :messages`, masking the nonexistent API. It also defaults the generated app to `anthropic/claude-sonnet-4.6` instead of Sonnet 5.

- **Sakana Fugu Ultra** (added 2026-06-23, scored 79/100, Tier B, #13 tie): first Sakana/Fugu run, using Sakana's OpenAI-compatible Chat Completions endpoint through opencode (`sakana/fugu-ultra`). Completed both phases in 21m37s: phase 1 generated the Rails app, phase 2 passed local Rails boot, Docker build, and Docker Compose. RubyLLM calls are real (`RubyLLM.chat` + `with_instructions` + `ask` + `response.content`) and tests use a `FakeChat`, but the service sends only the latest user message to RubyLLM — prior turns are stored/displayed but never replayed into the model. Combined with process-local in-memory persistence, it lands exactly at the B/A boundary rather than Tier A.

- **Step 3.7 Flash** (added 2026-06-15 per Issue #7, scored 69/100, Tier B, #21): up from Step 3.5's 56/C. Fixes the headline 3.5 problem — it uses the real `ruby_llm` gem (`RubyLLM.chat` + streaming `ask` + `chunk.content`) instead of the `ruby-openai` bypass, no hallucinations, at root. Held to mid-Tier-B because multi-turn never reaches the model (fresh `RubyLLM.chat` per request, history kept in a `@@all` class-var `ChatStore` but never replayed into RubyLLM), plus no system prompt and a non-latest `claude-sonnet-4-5` slug. Ties DeepSeek V4 Pro and Kimi K2.5 at 69.

- **Qwen 3.5 397B A17B (base)** (added 2026-06-15, scored 42/100, Tier C, #32): the raw base behind Nex-N2-Pro, run as a controlled comparison. Hallucinates the RubyLLM API (`chat.system`/`chat.user`/`response.text`, crashes at runtime), built in a nested `chat-app/` subdir, and its tests mock the hallucinated API. Confirms the base lacks the API correctness that Nex AGI's fine-tune adds (83/A) — see Cross-Cutting Finding #6.

- **Nex-N2-Pro** (added 2026-06-15, scored 83/100, Tier A, #11): Nex AGI's free, open-weight agentic model on the Qwen3.5-397B-A17B base. The notable result — it is the **first Qwen-family model in the benchmark to use the real RubyLLM API with zero hallucinations** (the lineage otherwise reliably invents the gem's API), and it ties Claude Opus 4.6 at 83 despite being free. Real `RubyLLM.chat(provider:, assume_model_exists:)` + `ask` + `content`, latest-Sonnet floating alias, excellent error handling (explicit preflight), real Turbo Streams. Held to the bottom of Tier A by two shortcuts: multi-turn via transcript-flattening (no `add_message`/`with_instructions`, RubyLLM reduced to single-shot) and client-carried hidden-field persistence (stateless but lost on reload, tamperable).

- **Gemini 3.5 Flash** (added 2026-06-15, scored 93/100, Tier A, #6 tie): the benchmark's biggest surprise — a Flash-tier model is now tied at #6 on this Rails/RubyLLM task and the best non-Anthropic/non-OpenAI result here, 14 points clear of Gemini 3.1 Pro (79, re-tiered to B). Textbook RubyLLM idiom (`chat(model:, provider: :openrouter, assume_model_exists: true)` + `with_instructions` + `add_message` replay + `complete` + `content`, latest sonnet-4.6), the strongest test suite of the cohort, real Turbo Streams, and file-backed persistence (capped at 50 messages, system message preserved) that survives restart. Run in-house after closing community PR #6 (which under-claimed 86 and whose committed excerpt showed an older model pin). Score validated by a blind A/B cross-audit (independent judge, projects anonymized) that scored it 91 and confirmed it clearly outranks Gemini 3.1 Pro on the audited dimensions. Held below the frontier-lab models by file-store concurrency/ephemerality gaps and no missing-key preflight.
- **Qwen3.7 Max** (added 2026-06-15, scored 78/100, Tier B, #15): run in-house after closing community PR #4, which claimed 82/A on a phase-2 DNF. Under our harness it completed both phases (the DNF was the author's environment), but scored 78/B not 82/A: it pins the non-latest `claude-sonnet-4`, skips the required Turbo Streams entirely (raw SSE via `ActionController::Live`), and uses an unbounded class-level `@conversations` hash (process-local, memory-leaking). RubyLLM API itself is correct. Ties the existing 78/B cluster (Sonnet 4.6, DeepSeek V4 Flash, MiniMax M3).
- **Kimi K2.7 Code** (added 2026-06-13, scored 86/100, Tier A, #10): exposed on OpenRouter as `moonshotai/kimi-k2.7-code`. Real RubyLLM throughout (`RubyLLM.chat` + `add_message` full-history-replay + `complete` + `response.content`), verified against gem source 1.16.0; session-cookie persistence, error-path-tested, real Turbo Streams + 3 Stimulus controllers. **Methodology note**: the structural scanner flagged six `chat.user`/`chat.assistant` "hallucinations" that were all false positives — they resolve to the app's own `Chat`/`Message` domain methods, not RubyLLM's DSL. Hand-reading confirmed genuine Tier 1 API; trusting the scanner would have wrongly tanked it like GLM 5.1. Lands just below the K2.6/GLM 5.2 pair (87) because it ships no `with_instructions` system prompt (its main regression from K2.6), no message cap on the cookie, and embeds LLM I/O in the session value-object model rather than a service.
- **GLM 5.2** (added 2026-06-14): the benchmark's biggest single-version jump — 46→87, Tier C→A, #30→#8. GLM 5.1's fatal hallucination (invented `chat.user`/`chat.assistant`, multi-turn crash) is gone; 5.2 replays history with the real `add_message` and verifies clean against gem source 1.16.0. Cleanest dependency-injection design in the cohort. This is real progress for this task, but it also demonstrates the benchmark's sensitivity to exact library API knowledge: fixing one core API family can move a model by an entire tier. Held to a tie with Kimi K2.6 (and ranked just behind it) only by an uncapped process-local singleton store — the persistence axis again. Slowest Tier A run at 43m on the throttled Z.ai coding endpoint.
- **Claude Fable 5** (added 2026-06-11): first Claude 5-generation entry, debuting at 94/100 Tier A (#5). Verified-correct RubyLLM path (`RubyLLM.chat(model:, provider: :openrouter, assume_model_exists: true)` + `with_instructions` + `add_message` + `ask` + `response.content`, all checked against ruby_llm 1.16.0 gem source). Uniquely, it grepped the installed gem source mid-run to verify the API before writing the integration — the only model observed doing the audit’s own verification step unprompted. 36 tests / 99.3% line coverage with a signature-faithful `FakeChat`, capped LRU history, missing-key preflight, and a zero-fix phase 2 (boot + Docker + compose + live chat). Held back by process-local singleton persistence (lost on restart, not multi-worker safe) and price: ~$11 est. per run at $10/$50 per M — roughly 10× an Opus 4.8 run for one point less.
- **Claude Opus 4.8** (added 2026-06-01): new Tier A entry at 95/100. It keeps Opus 4.7's correct RubyLLM path (`RubyLLM.chat(model:, provider: :openrouter, assume_model_exists: true)` + `with_instructions` + `add_message` + `ask` + `response.content`), upgrades to Ruby 4.0.3, writes 34 tests with a correctly-shaped `FakeChat`, and phase 2 validates local boot, live OpenRouter POST, Docker build, and compose health. Main deductions: unbounded session-cookie history and no explicit missing-key preflight before RubyLLM initialization.
- **MiniMax M3** (added 2026-06-01): jumps MiniMax from C to B at 78/100. M3 fixes M2.7's fatal `RubyLLM.chat(messages:)` hallucination and uses the real API (`RubyLLM.chat` + `with_instructions` + `add_message` + `ask` + `response.content`). It has a respectable 19-test suite, session cap, Turbo Streams, and service-layer separation. Two blockers keep it out of Tier A: phase 2 stalled during compose validation, and the model originally wrote a real `.env` with `OPENROUTER_API_KEY` into its result project. That file was deleted and the exact key was redacted from all discovered historical artifacts, but the output is penalized for the secret hygiene failure.
- **Grok 4.3** (added 2026-05-04): entry at 72/100 Tier B. Real RubyLLM API throughout (`RubyLLM::Chat.new` + `add_message` + `ask` + `response.content` + `RubyLLM::Error` rescue, all verified against gem source). Server-side Turbo Streams work, real README and `compose.yaml` ship. **Killer weakness**: Stimulus is dead at runtime — `app/javascript/application.js` is a one-line comment, no `import "./controllers"`, no `Application.start()`, so every `data-controller="chat"` action is silently broken. Tests stub `RubyLLM.stub :chat` but the controller calls `RubyLLM::Chat.new` — the stub is bypassed. Stale model pin to `claude-3.7-sonnet` despite README claiming "latest Claude Sonnet". Cost $1.74 / 15m — ~5× Kimi K2.6 for a worse result. Big jump from Grok 4.20 (25/100, Tier D) but doesn't reach Tier A.

Several earlier models also moved significantly after re-audit with the corrected rubric and verified API criteria:

- **Kimi K2.5** (was Tier 3 → now Tier B): `chat.complete(&block)` and `chat.add_message(role:, content:)` are both real RubyLLM API, not hallucinations as previously claimed. Drops to B solely because tests don't exercise the LLM path and class-var storage is fragile.
- **Kimi K2.6** (was Tier 2 → now Tier A): with the kwargs "bug" revealed as non-existent, K2.6 is the only Chinese model whose tests actually mock RubyLLM with a correctly-signatured FakeChat AND rescues `RubyLLM::Error` AND uses a session-cookie store that survives restarts.
- **Gemini 3.1 Pro** (was Tier 3 → Tier A → re-tiered to Tier B at 79 on 2026-06-15): `Chat.new` is real, `add_message` kwargs form is valid, and Gemini has proper cache-backed server-side persistence plus real Turbo Streams. Uses Ruby 3.4.1 (older LTS, valid) rather than 4.0.2 — both are production-viable. The later re-audit dropped it below the A/B line for the missing `with_instructions` system prompt and stale `claude-3.7-sonnet` pin (see its Tier B entry).
- **GPT 5.4 xHigh** (was Tier 2 → now co-leader Tier A): the `add_message` kwargs form isn't a bug. Re-audit scored it 94/100, tying Opus 4.7 on correctness but losing on cost (~15× more expensive).
- **MiMo V2.5 Pro** (was "Tier 1" overclaim → now Tier B at 64): still the cleanest RubyLLM integration from a non-Anthropic model, but demoted because tests never exercise the LLM path and the `ChatStore` Singleton is process-local (dies on Puma restart, not multi-worker safe).
- **DeepSeek V4 Pro** (was "Tier 1 code" → now Tier B at 66): DNF harness run. Clean RubyLLM usage but ships stock Rails README template + no docker-compose + missing bundle-audit. Concrete gaps, not just harness incompatibility.
- **GLM 5.1** (was Tier 2 → now Tier C at 43): `c.user()` / `c.assistant()` fluent DSL confirmed as hallucinated via grep of the gem source. Plus: every request rebuilds `ChatSession.new`, discarding history entirely. Two bugs compound.

---

## Tier A — Ship as-is (13 models)

### 1. Claude Opus 4.7 (97/100) — most test-disciplined

The benchmark leader by a hair. `LlmClient#reply_to` uses the full real API chain:

```ruby
chat = @client.chat(model:, provider:)
chat.with_instructions(@system_prompt)
previous_messages.each { |msg| chat.add_message({role: msg.role.to_sym, content: msg.content}) }
response = chat.ask(user_message)
response.content
```

Textbook correct. The `FakeChat` test double matches every real signature (`with_instructions`, `add_message(attrs)`, `ask`). Tests verify history replay, error wrapping, model/provider override, and system prompt application. Session cookie persistence via `to_a`/`from_session` round-trip is multi-worker safe. Error handling: `rescue RubyLLM::Error + StandardError` → user-friendly truncated bubble.

**Killer strength**: test suite uses exact real-API signatures. **Killer weakness**: no concrete defects — Opus 4.7 is the cleanest output in the benchmark.

### 1. GPT 5.4 xHigh (Codex CLI) (97/100) — most production-polish, most expensive

Ties Opus 4.7 on score. Uses `RubyLLM.chat(model:, provider: :openrouter, assume_model_exists: true)` + `with_instructions` + `add_message(role:, content:)` + `chat.ask` + `response.content`. Textbook plus provider pinning and registry-skip.

The only model with:
- **Explicit API-key preflight** (`ensure_api_key!` raises `MissingConfigurationError`)
- **Differentiated HTTP status codes**: 503 for config errors, 502 for runtime errors
- **Rails cache persistence with TTL + message cap** (24 msgs × 12h expiry)
- **Dedicated form object** (`PromptSubmission`) separate from domain model (`ChatMessage`)

10 test files including view-partial render tests. `FakeChat`/`FakeClient` match real signatures.

**Killer strength**: only model with differentiated 503/502 for config vs runtime. **Killer weakness**: 7.6M total tokens → ~$16/run, roughly 15× the cost of Opus for essentially tied output quality. Hard to justify unless you can't iterate on the first run.

### 3. GPT 5.5 xHigh (Codex CLI) (96/100) — cheaper and faster than 5.4 at equivalent quality

Essentially ties GPT 5.4 xHigh on every rubric dimension — same Tier A output shape, same DI-injected `RubyLlmChat` service, same Turbo Streams skeleton, same clean error handling. The headline wins are **cost and time**:

| | GPT 5.4 xHigh | GPT 5.5 xHigh | Δ |
|---|---|---|---|
| Elapsed | 22m | 18m | 20% faster |
| Total tokens | 7.6M | 4.9M | 35% fewer |
| Output tokens | 63K | 29K | 54% fewer |
| Est. cost | ~$16 | ~$10 | 40% cheaper |
| Score | 94/100 | 93/100 | noise |

Integration code uses the full real RubyLLM API:

```ruby
chat = RubyLLM.chat(model:, provider: :openrouter, assume_model_exists: true)
chat.with_instructions(SYSTEM_PROMPT)
history.each { |m| chat.add_message(role: m.role.to_sym, content: m.content) }
response = chat.ask(prompt)
response.content.to_s.strip
```

Ships with:
- Dependency-injected `client_factory:` lets tests exercise full seed-history-then-ask path via `FakeClient` without WebMock
- `rescue_from RubyLLM::Error, RubyLLM::ConfigurationError` — both real error classes
- Session-cookie persistence with 20-message cap
- Real Turbo Streams (`turbo_stream.replace "chat-thread"` + composer)
- Stimulus composer controller with proper lifecycle (disable-on-submit, reset, auto-scroll)

At ~$10/run and 18m, GPT 5.5 xHigh is more cost-effective than 5.4 for this benchmark. It doesn't unlock new capabilities — same Tier A shape, just cheaper. For OpenAI-preferred deployments where Codex CLI is already in use, 5.5 replaces 5.4 with no behavioral regression.

**Killer strength**: DI-injected test pattern + real error class rescue + session cookie persistence — most defensive production patterns in the benchmark. **Killer weakness**: no significant defect in this run; same shape as 5.4 at lower cost.

### 4. Claude Opus 4.8 (95/100) — fastest Opus, live-validated end-to-end

Opus 4.8 keeps the Opus 4.7 quality bar but ships a smaller, cleaner Rails 8.1/Ruby 4.0.3 app. The RubyLLM path is fully verified in `app/services/chat_service.rb`:

```ruby
chat = @chat || RubyLLM.chat(model: model, provider: :openrouter, assume_model_exists: true)
chat.with_instructions(SYSTEM_PROMPT)
conversation.messages[0...-1].each { |message| chat.add_message(role: message.role.to_sym, content: message.content) }
response = chat.ask(prompt.content)
response.content.to_s
```

34 tests cover Message/Conversation objects, service behavior, controller paths, helper output, and error wrapping. `test/services/chat_service_test.rb` defines a `FakeChat` with the same real signatures (`with_instructions`, `add_message(role:, content:)`, `ask`). Phase 2 did stronger validation than most runs: HTTP boot, `/up`, a real Turbo Stream POST returning Claude's `pong`, Docker build, production container boot, and compose health.

**Killer strength**: combines Opus-level API correctness with live Rails+Docker+OpenRouter verification in 16m48s, faster than 4.7. **Killer weakness**: session-cookie persistence has no message cap, so long chats can hit the 4KB cookie ceiling; no explicit missing-key preflight before RubyLLM initialization.

### 5. Claude Fable 5 (94/100) — first Claude 5-gen entry, fixed 4.8's deductions

Fable 5 (snapshot `claude-5-fable-20260609`) is the first Claude 5-generation model on the board. The RubyLLM path in `app/services/chat/completion.rb` is fully verified against the ruby_llm 1.16.0 gem source:

```ruby
chat = RubyLLM.chat(model: self.class.model, provider: :openrouter, assume_model_exists: true)
chat.with_instructions(SYSTEM_INSTRUCTIONS)
previous_turns.each { |message| chat.add_message(role: message.role, content: message.content) }
response = chat.ask(latest_user_message.content)
Message.new(role: :assistant, content: response.content)
```

Notably, it read the installed gem source mid-run before writing any integration code ("Now let me verify the real RubyLLM 1.16 API from the installed gem source") — the only model observed performing the audit's own verification step unprompted.

- 36 tests across 7 files (service, store, form, message PORO, both controllers, helper), 99.3% line / 100% branch coverage. `FakeChat` carries exact real signatures (`with_instructions`, `add_message(attributes)`, `ask` returning `.content`); error and missing-key paths tested.
- Fixes both of Opus 4.8's deductions: history is capped (`MAX_MESSAGES_PER_CONVERSATION = 200`, LRU eviction at 500 conversations) and there is an explicit `OPENROUTER_API_KEY` preflight with a friendly error.
- Real Turbo Streams (`create`/`error`/`invalid` templates), 3 wired Stimulus controllers (auto-scroll, chat form, dismissable), proper partial decomposition.
- Phase 2 passed all gates with zero code fixes: local boot, Docker build, compose health, and a live end-to-end chat against the compose stack.

**Killer weakness**: persistence is a process-local singleton (`Chat::ConversationStore`) — thread-safe and capped, but history dies on restart and breaks under multi-worker Puma. The rubric rates that below 4.8's session cookie, which is what keeps Fable 5 at #5 despite otherwise stronger engineering. It is also the priciest Claude run yet: ~$11 est. ($10/M input, $50/M output) over 24m — roughly 10× an Opus 4.8 run for one point less. The 4.8-vs-Fable ordering was confirmed by a blind head-to-head cross-audit (independent judge, projects anonymized): 19 vs 18 on the contested dimensions, with the judge noting Fable's test suite is actually the stronger of the two, and that a single change — backing `ConversationStore` with `Rails.cache` instead of an in-process hash — would flip the ranking.

### 6. Claude Fable 5 re-release (93/100) — slight regression vs original, still Tier A

Run separately as `claude_fable_5_rerelease` after Anthropic/OpenRouter re-released `anthropic/claude-fable-5`. The output is structurally different from the original Fable run but lands at **93/A**, one point below the original rather than a large rumored regression.

RubyLLM usage in `app/services/chat_completion.rb` remains correct and was verified against gem source during the run:

```ruby
chat = RubyLLM.chat(model: model)
chat.with_instructions(SYSTEM_PROMPT)
history.each { |message| chat.add_message(role: message.role.to_sym, content: message.content) }
response = chat.ask(prompt)
response.content.to_s
```

The scanner's `chat.user` / `chat.assistant` hits are false positives: they are `ChatMessage.user(...)` and `ChatMessage.assistant(...)` factory methods in the app domain, not RubyLLM DSL calls. Tests are stronger on paper than the original (41 tests, 107 assertions, 100% line coverage) and the `FakeChat` matches the real `with_instructions`, `add_message(attributes)`, `ask`, and `.content` surface. A post-run live smoke test of `ChatCompletion.new.call` returned `live_chat_ok`.

**What improved vs original Fable 5**: persistence moved from a process-local singleton to `Rails.cache` with a 12h TTL and a tiny session cookie containing only the conversation id. That is more restart/multi-worker friendly than the original `Chat::ConversationStore` singleton.

**What regressed or stayed weaker**: the app still defaults to `anthropic/claude-sonnet-4.6` even though Sonnet 5 is live now and RubyLLM exposed a floating `~anthropic/claude-sonnet-latest` alias; phase 2 validated local boot/Docker/Compose with `/up` only, whereas the original Fable phase 2 performed live Turbo Stream chat through both local Rails and Compose; and the cache entry is TTL-bound but not hard-capped even though the LLM replay history is capped. Net: **93/A** — a small regression from the original 94/A, but still a strong Tier A result rather than a collapse.

### 6. Gemini 3.5 Flash (93/100) — best non-Anthropic/non-OpenAI result, a Flash that beats Pro

Run + scored in-house (2026-06-15) after closing community PR #6, which submitted pre-scored results without the gitignored project code. The result is the benchmark's biggest surprise: a *Flash*-tier model lands at **93/100, tied #6 on this benchmark** — above GLM 5.2 / Kimi K2.6 (87) and **14 points above Gemini 3.1 Pro** (79), behind only Opus 4.7/4.8, GPT 5.4/5.5, and original Fable 5. Newer generation (3.5 vs 3.1) beats the tier gap on this task.

The RubyLLM integration is textbook, verified against gem source 1.16.0 in `app/services/chat_service.rb`:

```ruby
chat = RubyLLM.chat(model: @model, provider: :openrouter, assume_model_exists: true)
chat.with_instructions(SYSTEM_INSTRUCTION)
@conversation.messages.each { |msg| chat.add_message(role: msg.role.to_sym, content: msg.content) }
response = chat.complete
@conversation.add_message(role: :assistant, content: response.content)
```

- Pins the **latest** `anthropic/claude-sonnet-4.6` (PR #6's committed excerpt showed an older `claude-3.5-sonnet` plan — our run got the canonical result, which is exactly why we re-run in-house).
- Best test suite of this cohort: `FakeChat` mirrors the real signature precisely (`model:, provider:, assume_model_exists:` / `with_instructions` / `add_message(role:, content:)` / `complete`→`.content`), stubs the real `RubyLLM.chat` entry, asserts the params + history replay, and has an error-path test; 5 test files (service, controller, store, conversation, message).
- Real server-side Turbo Streams (append user+assistant, replace form; error/blank/clear paths all stream), 2 Stimulus controllers, partials. XSS handled correctly — `format_message_content` HTML-escapes the LLM output *before* applying code-block formatting.
- **File-backed persistence** (`tmp/chats/<id>.json`, keyed by session, auto-saved on `add_message`): survives restart, is single-host multi-worker safe, and is **capped at `MAX_MESSAGES = 50` with the system message preserved** (`Chat::Conversation#trim_messages!`) — better than a singleton.

**Killer weaknesses** (why 93, not higher): persistence has no file locking (concurrent writes to one conversation can race) and `tmp/` is ephemeral in containerized deploys; no dedicated missing-key preflight (a missing key surfaces via the generic rescue rather than a friendly message). Also, despite the low $1.50/$9 per-M rate, the run cost ~$3.50 — *more* than an Opus 4.8 run — because it churned far more tokens (1.1M input + 11M cache reads). Every dimension was hand-verified, then independently confirmed by a blind A/B cross-audit that scored it 91/100 (vs. this 93) — a 2-point spread within noise — and found the persistence cap I initially missed.

### 8. Kimi K2.6 (87/100) — best Chinese-model output

The standout of the non-Anthropic/non-OpenAI cohort. `RubyLLM.chat` + `with_instructions(SYSTEM_INSTRUCTION)` + `chat.add_message(role:, content:)` + `chat.ask` + `response.content` — all real API.

- **Only Chinese model that combines**: real LLM-path tests (`FakeChat` with correct signatures) + error-path rescue (`rescue RubyLLM::Error` with flash via turbo_stream) + session-cookie persistence with `MAX_MESSAGES = 50` cap.
- Full Gemfile: ruby_llm, turbo, stimulus, tailwindcss, brakeman, bundler-audit, rubocop-rails, simplecov, capybara.
- Session cookie survives restart and is multi-worker safe.

**Only meaningful deduction**: full history replay each turn (wastes tokens vs persistent-instance pattern).

At ~$0.30/run, Kimi K2.6 is the cheapest Tier A model — 3-50× cheaper than the top 2.

### 8. GLM 5.2 / Z.ai (87/100) — biggest single-version turnaround in the benchmark

GLM 5.2 fixes the exact bug that put GLM 5.1 in Tier C (46/100): where 5.1 invented `chat.user`/`chat.assistant` to seed multi-turn history (crashing on turn 2), 5.2 uses the real `chat.add_message(role:, content:)` to replay prior turns. Every RubyLLM call is verified against gem source 1.16.0 — `RubyLLM.chat(model:)` (via an injected `client`), `with_instructions`, `add_message`, `ask`, `response.content` — zero hallucinations. Phase 2 live-validated the full path end-to-end (real OpenRouter chat, Docker, compose, CSRF correctly rejecting a bare curl POST). Interpret the jump narrowly: it shows a major improvement in RubyLLM/API recall and agentic Rails execution for this task, not a blanket proof that GLM 5.2 dominates unrelated programming domains.

```ruby
def chat
  chat = client.chat(model: model)          # client = RubyLLM (dependency-injected)
  chat.with_instructions(system_prompt)
  prior_turns.each { |t| chat.add_message(role: t[:role].to_sym, content: t[:content]) }
  chat
end
response = chat.ask(latest_user_content, &block)
conversation.add(role: "assistant", content: response.content)
```

- **Cleanest dependency injection in the cohort**: both the RubyLLM client and the controller's `service_class` are injectable, so the 26-test suite mocks the LLM path with a correctly-signatured `FakeChat`/`FakeClient` — no external mock lib, and the tests exercise streaming, system-prompt application, and `RubyLLM::Error` wrapping.
- Targets the latest Claude slug (`anthropic/claude-sonnet-4.6`), real Turbo Streams + 2 Stimulus controllers, full Gemfile (Tailwind via cssbundling-rails), real README, valid Ruby 4.0.5.

**Killer weakness**: persistence is an **uncapped** process-local `Singleton` `ConversationStore` — lost on restart, not multi-worker safe, and (unlike Kimi K2.6 and Claude Fable 5's capped stores) free to grow without bound. It is honest about this in code comments, but the rubric rates it below Kimi's restart-surviving, multi-worker-safe capped cookie. That single axis is why it ties Kimi at 87 yet ranks just behind it — the same persistence axis that separated Fable 5 from Opus 4.8. Also the slowest Tier A run (43m on a throttled Z.ai coding endpoint at 12-55 tok/s).

### 8. Grok 4.5 (87/100) — the Grok family finally reaches Tier A, with one subtle correctness bug

Run 2026-07-08 (snapshot `grok-4.5-20260708`, released the same day; reasoning effort maxes at `high`, which is the default, so this is already the highest-effort configuration). The family trajectory is now 25 (4.20, Tier D) → 72 (4.3, Tier B) → **87 (4.5, Tier A)** — and 4.5 fixes **all three of 4.3's failure modes**:

- **Stimulus is alive**: `application.js` imports controllers and `controllers/index.js` eager-loads them (4.3 shipped a one-line comment and every `data-controller` was dead).
- **Tests can't bypass the stub**: `LlmClient` takes `client:` via constructor DI, and the tests inject `FakeClient`/`FakeChat` through the exact path production uses (4.3 stubbed `RubyLLM.chat` while the controller called `Chat.new`).
- **Latest model pin**: `anthropic/claude-sonnet-4.6` (4.3 pinned the stale `claude-3.7-sonnet`).

The RubyLLM surface is fully real, verified against gem source 1.16.0 (`llm_client.rb`): DI'd `client.chat(model:, provider:, assume_model_exists: true)` + `with_instructions` + `add_message` replay + `ask` + `.content`, with a graceful `ArgumentError` fallback. Real Turbo Streams ×4 including a degraded error bubble; capped session-cookie persistence (`MAX_HISTORY = 40`); XSS-safe via `simple_format`; 28 tests incl. error paths.

**Killer weakness — the double-send bug**: `chats_controller.rb` appends the user message to the session **before** calling the service, and `LlmClient#previous_messages` only filters system messages — so the history replay already contains the new user turn, and `chat.ask(user_message)` then sends it **again**. Every user turn reaches the LLM twice (token waste + a subtly corrupted conversation shape). The service test builds history *without* the pending message — a different precondition than production — which is why the suite stays green. Found by the blind cross-audit, not the primary hand-read. Smaller deductions: the rescue path stores the apology *as an assistant message* that gets replayed into future LLM context; no missing-key preflight; the 40-message cap is a count cap, not a byte cap (CookieOverflow still reachable). Ordering vs Fable 5 (94) confirmed by a blind anonymized A/B: 84 vs 90 on the judge's stricter scale, decisive. At ~$5.10 (est.) / 16m it's the second-priciest Tier A run.

### 11. Kimi K2.7 Code (86/100) — correct API the scanner nearly mis-flagged

K2.7 is the textbook case for why this benchmark mandates hand-reading the integration. The structural scanner flagged **six hallucinated `chat.user`/`chat.assistant` DSL calls** — the exact signature that put GLM 5.1 in Tier C — but every one is a **false positive**: they resolve to the app's *own* domain methods (`Chat#user`/`Chat#assistant` defined on a session-backed value object, and `Message.user`/`Message.assistant` factory methods), not RubyLLM's API. The real RubyLLM usage lives in `Chat#complete!` and is all genuine, verified against gem source 1.16.0:

```ruby
def complete!
  chat = RubyLLM.chat                                   # real entry (uses config.default_model)
  to_rubyllm_messages.each { |m| chat.add_message(m) }  # real add_message(hash), full history replay
  response = chat.complete                              # real complete (not ask)
  assistant(response.content)                           # response.content — real accessor
  response.content
end
```

- Session-cookie persistence (`session[:chat] = @chat.to_a`) — survives restart, multi-worker safe.
- Controller `rescue RubyLLM::Error` → flash + re-render at `:unprocessable_entity`; initializer raises a missing-key preflight at boot.
- 22 tests across 4 files exercise the LLM path with a `Minitest::Mock` whose signatures (`add_message(hash)`, `complete`, `.content`) match the real gem, plus a genuine error-path test (`RubyLLM.stub(:chat, -> { raise RubyLLM::Error })`).
- Real Turbo Streams (append + remove empty-state), 3 Stimulus controllers (reset-form, auto-scroll, textarea autogrow), proper partials.

**Killer weaknesses** (why 86, just below K2.6 and GLM 5.2 at 87): no `with_instructions` system prompt — the assistant ships with no persona or guardrails, a real product gap for a "ChatGPT-like" app and the main regression from K2.6, which has one. The session cookie has no message cap (K2.6 caps at 50), so long chats risk `CookieOverflow`. And the RubyLLM I/O is embedded in the `Chat` value object — which is also the session-serialization object — rather than isolated in a service. Pins `anthropic/claude-sonnet-4.5` rather than the newer 4.6, and relies on default provider inference instead of `provider: :openrouter` (works — phase 2 live-validated the OpenRouter path end-to-end).

### 12. Claude Opus 4.6 (83/100) — thinner than 4.7 but clean

Correct RubyLLM usage (`RubyLLM.chat` + `chat.ask` + `response.content`). History replay via `service.chat.messages << RubyLLM::Message.new(...)` — works because `Chat#messages` is `attr_reader` on an Array, but reaches into internal state (Demeter violation).

**Biggest weakness**: no rescue around `chat_service.ask` in the controller. A transient OpenRouter 5xx produces a 500 page with stack trace. This is the difference between 4.6 (Tier A low) and 4.7 (Tier A high).

### 12. Nex-N2-Pro (83/100) — the first Qwen-family model that doesn't hallucinate RubyLLM

The headline: a **free**, open-weight model built on the **Qwen3.5-397B-A17B** base (Nex AGI's agentic fine-tune) is the first model of that lineage in this benchmark to use the **real RubyLLM API with zero hallucinations** — the Qwen3.5 family otherwise reliably invents the gem's API. It ties Claude Opus 4.6 at 83 and completed both phases on the rate-limited `:free` endpoint. Verified real in `app/services/llm_chat_service.rb`:

```ruby
def chat
  RubyLLM.chat(model: @model, provider: @provider, assume_model_exists: true)
end
response = chat.ask(prompt_for(history:, message:))
ChatMessage.new(role: :assistant, content: response.content.to_s)
```

- Targets `~anthropic/claude-sonnet-latest` — OpenRouter's floating alias for the newest Sonnet, so it never goes stale.
- Excellent error handling: explicit `MissingApiKey` preflight, `rescue RubyLLM::Error` → friendly `ResponseError`, blank/length guards, all surfaced as degraded Turbo Streams.
- Real server-side Turbo Streams (remove/append/replace/update), 2 Stimulus controllers, rich partial decomposition. `FakeChat` test stubs the real `RubyLLM.chat` and asserts `provider: :openrouter` + `assume_model_exists` + prompt contents + `response.content`.

**Killer weakness — non-idiomatic RubyLLM**: it never uses the gem's conversation primitives. Multi-turn is done by **flattening the whole transcript into one text prompt** (`prompt_for`), and the system instruction is **embedded in that prompt rather than `with_instructions`** — so RubyLLM is reduced to a single-shot completion endpoint (−5 on correctness vs. peers that use `add_message`/`with_instructions`). Persistence is **client-carried**: history round-trips through a `hidden_field_tag :history` (JSON, capped at 12), so the server is stateless — multi-worker safe and restart-proof, but lost on page reload and client-tamperable (a mild prompt-injection surface). Strong result for a free model, but the shortcuts keep it at the bottom of Tier A rather than higher.

## Tier B — 1-2 hours to ship (13 models)

### 14. Gemini 3.1 Pro (79/100) — real API, but stale model + no system prompt

**Re-audited 2026-06-15: 82 → 79, re-tiered A → B.** The RubyLLM usage is genuinely real (`RubyLLM::Chat.new(model:, provider:, assume_model_exists:)` + `add_message(role:, content:)` replay + `ask` + `response.content`), and it ships real Turbo Streams (`remove empty-state → append user + assistant → replace form`), a Stimulus scroll controller, partials, and `Rails.cache`-backed persistence with a 2h TTL. Tests use a correctly-signatured `FakeChat` (stubs `RubyLLM::Chat.new`) and cover the error path.

The drop from the original 82 comes from deductions that pass weren't fully charged:

- **No `with_instructions` system prompt at all** (−4 on RubyLLM correctness) — the assistant has no persona/guardrails despite the ChatGPT-like brief.
- **Stale `anthropic/claude-3.7-sonnet`** pin instead of current Sonnet 4.x (−2).
- **No initializer / no missing-key preflight** — `LlmService.ask` sets `RubyLLM.config.openrouter_api_key` inline on every call.
- **`Rails.cache` history has TTL but no size cap**, and the cache store is the defaulted file_store (multi-worker safe on one host, but ephemeral in containers).
- Lighter CI tooling (no rubocop config, brakeman binstub, or CI workflow) and only 2 test files.

The re-tier was corroborated by an independent blind A/B cross-audit that scored this project 71 (vs. this deliberate re-read's 79) — both clearly sub-80. **Borderline call** (79 is one point under the A/B line), but the missing system prompt is a concrete, uncontested deduction, not noise.

---

### 14. Sakana Fugu Ultra (79/100) — validates end-to-end, but history never reaches the model

First Sakana run, using `sakana/fugu-ultra` via opencode's OpenAI-compatible provider. The harness completed both phases in **1297s / 21m37s** and phase 2 self-validated local boot, Docker build, and Docker Compose. The project is structurally complete: Rails app at root, `ruby_llm`, Turbo/Stimulus/Tailwind, README, Dockerfile, compose, SimpleCov, Brakeman, RuboCop, and bundler-audit.

RubyLLM usage in `app/services/chat_service.rb` is real but incomplete:

```ruby
llm.chat(model: chat.model, provider: :openrouter, assume_model_exists: true)
  .with_instructions(SYSTEM_PROMPT)
response = llm_chat.ask(user_message.content)
assistant_message = chat.add_message(role: "assistant", content: response.content.to_s)
```

`RubyLLM.chat`, `with_instructions`, `ask`, and `response.content` are all valid, and the service test injects a `FakeRubyLLM`/`FakeChat` with matching `chat(**options)`, `with_instructions`, and `ask` signatures. Error handling rescues `RubyLLM::Error`/`Faraday::Error`, records an error message, and the UI renders it as a degraded bubble. Hotwire is real (`send_message.turbo_stream.erb` removes empty state, appends messages, replaces header/sidebar), with a Stimulus composer controller for autoresize/submit state.

**Killer strength**: excellent harness compatibility for a brand-new provider — opencode tool calls worked, the app built quickly, tests/style/security passed, and Docker/Compose validated cleanly. **Killer weakness**: multi-turn is silently broken at the LLM layer. `ChatRepository` stores messages in a process-local class-instance hash, but `ChatService#llm_chat` builds a fresh RubyLLM chat and calls `ask` with only the latest user message; it never replays prior turns with `add_message` or keeps a persistent `Chat`. That puts it in the same failure family as Step 3.7 Flash, though with better deliverables, a system prompt, and phase-2 validation.

Borderline B/A call: one small code patch could replay history, but production readiness also needs replacing the process-local repository with Rails.cache/session-backed persistence and a message cap. Score: **79/B**, tied with Gemini 3.1 Pro.

### 16. Claude Sonnet 4.6 (78/100) — ambitious scope, subtle bug

Most feature-rich UI of the benchmark (multi-conversation sidebar with per-chat titles). Best controller separation (ChatsController + MessagesController). Mocha-based tests.

**Killer weakness**: `LlmChatService#call` has a silent control-flow bug — only calls `ask` if the last history message is a user message, returns `""` otherwise. The test at `llm_chat_service_test.rb:32-50` rubber-stamps this bug (passes against the broken path). Also: entire conversation graph stored in 4KB session cookie → overflows after ~10 turns.

### 16. DeepSeek V4 Flash (78/100) — cheapest viable option

~$0.01/run (!). `RubyLLM.chat(model:, provider:)` + `add_message(role:, content:)` + `ask` + `.content` — real API throughout. Session-replay multi-turn via `session[:messages]`. WebMock tests on the actual OpenRouter HTTP endpoint — genuine exercise of the LLM path.

**Killer weakness**: model slug `"claude-sonnet-4"` missing `anthropic/` prefix — will 404 against OpenRouter at runtime. One-character fix, but fatal as-is. Also: no rescue around `chat.ask`, 4KB cookie limit on long chats.

### 16. MiniMax M3 (78/100) — fixed API recall, failed secret hygiene

M3 is the first MiniMax result with correct RubyLLM usage. `app/services/chat_service.rb` uses `RubyLLM.chat(model: @model)`, `with_instructions`, `add_message(role:, content:)`, `ask`, and `response.content`, all real API per the verified table. It also caps session history (`MAX_HISTORY_TURNS = 20`), separates `ChatService` from `ChatController`, ships Turbo Stream append/update responses, and has 19 tests across service, controller, and integration paths.

The test suite is better than M2.7's hallucination-mocking setup, but still relies heavily on `ChatService.any_instance.stubs(:ask)` rather than a FakeChat matching RubyLLM itself. Phase 2 verified local boot and Docker build according to the transcript, then stalled during compose validation and the harness marked the run `failed` after six minutes of no progress.

**Killer strength**: MiniMax M3 completely fixes M2.7's fatal `RubyLLM.chat(messages:)` batch-form hallucination. **Killer weakness**: the model originally wrote a real `.env` containing `OPENROUTER_API_KEY` into the result project. The file was deleted and exact key occurrences were redacted from historical artifacts, but this is a severe prompt violation and keeps the result out of Tier A.

### 16. Qwen3.7 Max (78/100) — correct API, but skips Turbo Streams and leaks memory

Run + scored in-house (2026-06-15) after closing community PR #4, which claimed **82/A on a phase-2 DNF**. Under our harness it actually **completed both phases** — so the DNF was the author's environment, not the model — but the hand-read surfaced gaps the PR's prose glossed over, landing it at 78/B rather than 82/A. The RubyLLM usage itself is clean (`app/services/chat_service.rb`), all verified real: `RubyLLM.chat(model:)`, `with_instructions`, `ask(message, &block)` streaming, `reset_messages!`, `response.content` / `chunk.content`. Multi-turn uses the persistent-instance pattern (one `RubyLLM::Chat` kept alive per conversation).

- **Pins `anthropic/claude-sonnet-4`, not the latest 4.6** (−2 on RubyLLM correctness) — the brief asks for latest Claude Sonnet.
- **No Turbo Streams at all** — it streams via raw SSE (`ActionController::Live` + `EventSource` in `chat_controller.js`). A legitimate streaming approach, but explicitly not the Hotwire/Turbo Streams mechanism the brief requires (−5 on Hotwire). It does ship a substantial Stimulus controller and partials.
- **Persistence is the worst tier seen so far**: a class-level `@conversations = {}` hash holding live `Chat` objects keyed by conversation id. Process-local (lost on restart), not multi-worker safe, and **unbounded — never evicted, a memory leak** under sustained use.
- `FakeChat` tests exercise the LLM path with correct signatures; missing-key preflight + blank guard + a broad `rescue StandardError` → friendly SSE error. Both phases validated live.

**Killer strength**: correct RubyLLM API + completes phase 2 cleanly (contradicting the PR's DNF claim). **Killer weakness**: ignores the required Turbo Streams in favor of SSE, and the leaky class-var store would degrade a long-running production process.

### 20. Grok 4.3 (72/100) — clean controller, dead Stimulus

`RubyLLM::Chat.new(model:)` + `add_message(role:, content:)` + `chat.ask` + `response.content` + `RubyLLM::Error` rescue — real API throughout, all verified against gem source. Cleanest hand-written chat controller in the cohort (48 lines, no service-object over-engineering, no fluent-DSL flourishes). Real Turbo Streams in the controller. Real README, real `compose.yaml`, multi-stage Dockerfile. Cookie-based session persistence. ~$1.74/run, 15m wall time.

**Killer weakness**: **Stimulus is dead code at runtime.** `app/javascript/application.js` is a one-line comment with no `import "./controllers"` and no `Application.start()`. Built `app/assets/builds/application.js` is 48 bytes (just a sourcemap pointer). So `data-controller="chat"` is inert — Enter-to-send, autoresize, autoscroll, clear-input all silently broken. Phase 2 self-reported "local boot OK" without exercising the JS layer (a confidence-vs-verification gap distinct from Claude/Kimi which over-test).

**Other issues**: tests stub `RubyLLM.stub :chat` but the controller calls `RubyLLM::Chat.new` — the stub is bypassed (the test would actually hit the network or fail on missing key). Stale model pin `anthropic/claude-3.7-sonnet` (current is 4.7) despite README claiming "latest Claude Sonnet". No `with_instructions` system prompt.

Cost ($1.74) is ~5× Kimi K2.6 for a worse output, putting Grok 4.3 in an awkward price/quality slot. Big jump from Grok 4.20 (25/100, Tier D below) but doesn't reach Tier A.

### 21. Qwen 3.6 Plus (71/100) — cleanest open-model RubyLLM integration

Real RubyLLM usage with service-layer separation. Stimulus controller is well-built (escapeHtml, loading state, auto-scroll). Partials decomposed cleanly.

**Biggest weaknesses**: tests make *real* network calls (no WebMock), history is client-side JS only (lost on refresh), uses `fetch` + `innerHTML` instead of Turbo Streams (no `turbo-rails` gem).

### 22. DeepSeek V4 Pro (69/100) — Tier 1 code, Tier 3 deliverables

Previously ranked higher based on code quality alone. Re-audited:

**Clean RubyLLM usage**: `@chat = RubyLLM.chat; @chat.ask(content); result.content` — persistent Chat instance lets RubyLLM manage history internally (same pattern as MiMo). Tests use WebMock on real OpenRouter URL.

**But deliverables are broken**:
- README is the stock Rails "This README would normally document..." template (**not** customized)
- **No `docker-compose.yml`** — prompt explicitly required it

Run DNF'd because DeepSeek's thinking mode requires the client to echo `reasoning_content` back and opencode strips it. `reasoning: false` in opencode config didn't prevent DeepSeek from emitting thinking tokens server-side. The code written before the harness crashed is Tier 1 quality, but the deliverables are demo-level.

### 22. Kimi K2.5 (69/100) — reclassified up from Tier 3

Previously ranked as Tier 3 for "inventing `chat.add_message()` + `complete()`". **Both are real public methods** in RubyLLM 1.14.1 — the previous audit was wrong.

Uses `RubyLLM.chat(model:)` + `client.add_message(role:, content:)` + `client.complete(&block)` — valid API chain. Also attempts true server-push streaming via `Turbo::StreamsChannel.broadcast_append_to`. 37 test methods (most thorough count in the benchmark).

**Killer weakness**: none of the 37 tests actually mock RubyLLM — they test PORO CRUD and `respond_to?`, not the gem interaction. Also uses class-var storage (`Chat.storage = @storage ||= {}`) — worse than Singleton because it's not mutex-protected.

### 22. Step 3.7 Flash (69/100) — fixes 3.5's gem bypass, but multi-turn is broken at the LLM level

Run in-house 2026-06-15 per community **Issue #7**. The win over Step 3.5 (56/C, ⚠️ bypass) is real: 3.7 **uses the `ruby_llm` gem with the correct API** — no more `ruby-openai` bypass, no hallucinations, built at the workspace root. `app/services/chat_service.rb`:

```ruby
ruby_llm_chat.ask(user_content) { |chunk| response += chunk.content.to_s }   # real streaming ask + chunk.content
# ruby_llm_chat = RubyLLM.chat(model: chat.model)
```

- Real Turbo Streams (`format.turbo_stream` across create/show/destroy), a `chat_form` Stimulus controller, partials, turbo+stimulus wired via importmap. Error handling rescues and renders a degraded error message.

**Killer weakness — multi-turn doesn't reach the model**: `ChatService` builds a fresh `RubyLLM.chat` per request and calls `ask(user_content)` with only the current message. Prior turns are stored in `ChatStore` (a `@@all` class variable) but **never replayed into RubyLLM**, so the model has no memory of the conversation — the core feature of a chat app is silently broken. Combined with the class-var store (process-local, unbounded, not multi-worker safe), no `with_instructions` system prompt, and a non-latest, un-prefixed `claude-sonnet-4-5` slug, a bypass-fixed model lands only mid-Tier-B. Ties DeepSeek V4 Pro and Kimi K2.5 at 69.

### 25. Xiaomi MiMo V2.5 Pro (67/100) — cleanest multi-turn idiom

Uses `RubyLLM::Chat.new(model:, provider:)` + `@llm_chat.ask(content, &)` + `response.content`. Persistent `@llm_chat` instance means RubyLLM tracks history internally — the cleanest multi-turn pattern in the entire benchmark, cleaner than explicit history replay.

**But**:
- Tests never exercise the LLM path (only blank-guard + constants assertions)
- No error handling around `@chat.ask` — any API hiccup = 500 page
- `ChatStore` Singleton is process-local (dies on Puma restart, not shared across workers)
- No system prompt via `with_instructions`

~$0.14/run and 11 minutes makes this the fastest viable non-Anthropic option, but it needs ~2 engineer-hours of patching (add `rescue RubyLLM::Error`, swap Singleton for `Rails.cache`, add FakeChat mocks, add system prompt) to reach production quality.

### 26. GLM 5 (64/100) — correct API, stateless design

`RubyLLM.chat(model: "anthropic/claude-sonnet-4")` + `chat.ask` + `response.content` — correct. Mocha stubs match real API shape. Only one happy-path test, no error-path coverage.

**Killer weakness**: **zero multi-turn state** — every POST creates a fresh `RubyLLM.chat` with no history. The "chat app" is a stateless echo service. User asks "what did I just say?" → model replies "I don't know."

---

## Tier C — major rework needed (8 models)

### 27. Claude Sonnet 5 (58/100) — complete shell, broken first chat request

Newly available Sonnet 5 (`openrouter/anthropic/claude-sonnet-5`) completed both phases in **1625s / 27m05s**. Phase 2 validated local Rails boot, Docker build, and Docker Compose, and the project is structurally complete: Rails app at root, `ruby_llm`, Turbo/Stimulus/Tailwind, README, Dockerfile, compose, SimpleCov, Brakeman, RuboCop, and bundler-audit.

The core LLM path is broken. `app/services/chat_responder.rb` captures history, adds the user message, then builds a RubyLLM chat like this:

```ruby
RubyLLM.chat(model: MODEL, provider: PROVIDER).tap do |chat|
  chat.messages = history
end
```

RubyLLM 1.16 exposes `messages`, `add_message`, `ask`, and `with_instructions`, but **not `messages=`**. A direct method check returned `messages=true`, `messages==false`, `add_message=true`, `ask=true`, `with_instructions=true`, so the first real request raises `NoMethodError` before `chat.ask` can run. The test suite misses this because `test/services/chat_responder_test.rb` defines `FakeChat` with `attr_accessor :messages`, exactly the nonexistent writer the production code calls.

Other deductions: no `with_instructions` system prompt, default model pin is still `anthropic/claude-sonnet-4.6` despite running the benchmark with Sonnet 5, and the rescue ladder only catches `RubyLLM::*` errors, not the `NoMethodError` it actually triggers. The session-cookie transcript is capped and the Turbo/Stimulus UI is solid, but the application needs core RubyLLM replay rewritten with `add_message` before it is usable. Score: **58/C**.

### 28. Step 3.5 Flash (56/100)

Bypasses `ruby_llm` entirely using raw `Net::HTTP` to OpenRouter. The HTTP implementation itself is competent (timeouts, JSON parse errors, missing-key preflight all rescued with user-visible fallbacks). Session-backed multi-turn works. Best error handling of any model.

**But**: non-compliant with the prompt requirement (missing `ruby_llm` gem). Also: the Stimulus `afterSubmit` flow never renders the user's message into `#messages` — only the assistant reply appears, so the UI is silently broken.

### 29. Qwen 3.5 35B (55/100) — local model

Real `RubyLLM.chat` + `chat.ask` + `chat.messages.last.content` — correct API. No service layer (logic in controller). No multi-turn (fresh `RubyLLM.chat` per request).

**Killer weakness**: `test/models/ruby_llm_service_test.rb:14-22` wraps the real call in `rescue => e; assert true` — tests pass even if RubyLLM is completely broken.

### 30. GLM 4.7 Flash bf16 (52/100) — local model, near-miss

**Most RubyLLM-literate local model** of the benchmark — correctly uses the fluent chain `.with_model().with_temperature().with_params().with_instructions().complete(&block)`, all real API per gem source.

**Fatal bug**: `gem "ruby_llm"` is placed in `group :development, :test` with `require: false` — won't load in production. App would crash on boot with `NameError`. Also uses class-var `Message.all` storage (process-local).

### 31. GLM 5.1 / Z.ai (46/100) — hallucinated fluent DSL

`RubyLLM.chat(model:, provider:)` is correct, but history is replayed via hallucinated `c.user(msg)` / `c.assistant(msg)` fluent DSL — these methods do not exist in RubyLLM. Confirmed via grep of the gem source.

Compounded bug: every HTTP request constructs a brand-new `ChatSession.new` that discards history — so the hallucinated DSL calls are rarely entered in practice because there's never any history to replay. Two bugs mask each other.

Stimulus controller uses `fetch` + manual `innerHTML` for streaming — SSE-based but not Turbo Streams.

### 32. DeepSeek V3.2 (43/100)

Uses `RubyLLM::Client.new` + `client.chat(messages: [...])` — **both hallucinated**. Treats response as raw OpenAI JSON via `result.dig("choices", 0, "message", "content")`. Tests mock `RubyLLM::Client.any_instance` — mocking a class that doesn't exist. The entire LLM integration is fictional.

**Redeeming qualities**: best error-rescue discipline of any Tier 3 model (try/rescue/log/user-message), real docker-compose, substantive 265-line README.

---

### 33. Qwen 3.5 397B A17B (base) (42/100) — the raw base behind Nex-N2-Pro, and it hallucinates

This is the **un-fine-tuned Qwen3.5-397B-A17B base** (OpenRouter `qwen/qwen3.5-397b-a17b`) — the exact architecture Nex AGI fine-tuned into Nex-N2-Pro (#11, 83/A). Run head-to-head, it is a clean natural experiment, and the base **fails the one thing that matters**: it hallucinates the RubyLLM API in `chat-app/app/services/chat_service.rb`:

```ruby
chat = RubyLLM.chat(model: "anthropic/claude-sonnet-4")
chat.system(SYSTEM_PROMPT)        # hallucinated — no such method (real: with_instructions)
response = chat.user(@message)     # hallucinated — no such method (real: ask)
response.respond_to?(:text) ? response.text : response.to_s  # hallucinated — should be .content
```

`chat.system` raises `NoMethodError` on the first call — Tier 3, dead at runtime. Compounding failures: it built the whole app in a **nested `chat-app/` subdirectory** (the brief explicitly forbids this; `completed_with_errors`), and its tests **mock the hallucinated API** (`FakeChat#system`/`#user`), so the suite passes green while the real code is broken — worse than no tests. Real Turbo Streams, Stimulus, and a full Gemfile/Dockerfile/compose keep it out of Tier D, but the hallucination + nesting cap it at Tier C.

**Why it matters**: see Cross-Cutting Finding "Agentic fine-tuning *can* instill library-API correctness the base lacks" below. Base = 42/C; Nex-N2-Pro fine-tune = 83/A — a 41-point swing from identical architecture.

---

### 34. MiniMax M2.7 (41/100) — moved from Tier D after Ruby 4.0.2 correction

Hallucinated `RubyLLM.chat(model:, messages: [...])` batch signature — crashes on first call (`ArgumentError: unknown keyword: messages`). Best architectural decomposition of any Tier C/D model (service + form object + POROs + partials), wrapped around a corpse.

Tests mock the hallucinated API so they pass green against a bug.

## Tier D — throw away (4 models)

### 35. Qwen 3.5 122B (37/100) — local model

Doesn't use `ruby_llm` at all. Uses `Openrouter::Client.new(api_key: @api_key)` — wrong casing for the real `OpenRouter::Client` (exists in `openrouter` gem but requires a configuration object, not a bare `api_key:` kwarg). Plus calls `client.chat(model:, messages:)` — real gem method is `completion`, not `chat`.

### 36. Qwen 3 Coder Next (32/100) — local model

Invented `RubyLLM::Client.new(api_key:, model:)` + `client.chat(messages: [...])` + OpenAI-shaped `response.choices.first.message.content` — pure hallucination. Also commits a placeholder `.env` file to the repo.

### 37. Grok 4.20 (25/100)

Bypasses RubyLLM with `ruby-openai`, but the gem is in `:development, :test` group with `require: false` — production `NameError` on first request. Gemfile missing turbo-rails, stimulus-rails, bundle-audit.

Stimulus controller JavaScript is **uncompilable** (`class ChatFormController < StimulusController` — uses Ruby's `<` inheritance syntax in JS, `StimulusController` never imported). Uses CDN Tailwind script tag inside the layout (CSP risk).

At ~$0.60/run, Grok is the most expensive Tier D model.

### 38. GPT OSS 20B (11/100) — local model

Benchmark low. Stock Rails README template (no customization), nested `app/app/` directory (violates "stay in workspace root" rule), **no tests folder at all**, no docker-compose, Gemfile has `gem "tailwindcss"` (CLI gem, not the Rails binding) with brakeman commented out.

Invented `RubyLLM::Client.new(provider:, api_key:)` + `client.chat(content:, model:)` + `response.output_text`. Zero rescue blocks, zero persistence, zero Stimulus controllers.

This 20B local llama.cpp run did not reliably follow this long agentic Rails prompt; that should not be generalized to every short or non-agentic coding task.

---

## Cross-Cutting Findings

### 1. Ruby version choice varies but is uniformly valid

Almost every model shipped `ARG RUBY_VERSION=4.0.2` or `FROM ruby:4.0.2-slim` (current stable, released 2026-03-17). Gemini 3.1 Pro shipped Ruby 3.4.1 (older LTS, still supported). Both are production-viable. An earlier version of this report incorrectly treated 4.0.2 as a fake placeholder — it's not; the Rails 8.1 generator defaults to the current stable, and every model inheriting that default is correct. No deductions apply.

### 2. Test coverage measures nothing without mock-fidelity

Kimi K2.5 wrote 37 tests (most in the benchmark) but none of them mock RubyLLM. They test PORO CRUD and `respond_to?`. A test suite that doesn't exercise the LLM code path cannot catch bugs in that path, no matter how many test methods you count.

Gemini 3.1 Pro's test suite is smaller (11 tests) but uses a correctly-signatured `FakeChat` that exercises real API paths including error handling. Gemini scored higher on test quality despite fewer tests.

### 3. RubyLLM idiomatic usage varies wildly

Models use three different legitimate multi-turn patterns, plus one recurring broken pattern:
- **Persistent instance** (MiMo, DeepSeek V4 Pro): create `Chat` once, call `.ask()` repeatedly. RubyLLM tracks history internally. Cleanest, but persistence is fragile (process-local objects).
- **Explicit history replay** (Gemini 3.5 Flash, Kimi K2.7, GLM 5.2, Claude Fable 5 original/re-release, Opus 4.8/4.7/4.6, Sonnet 4.6, Kimi K2.6, Gemini, DeepSeek V4 Flash, MiniMax M3): rebuild `Chat`, call `.add_message()` per historic message, then `.ask()`. More code but persistence-friendly (store messages in cookie/cache, reconstruct Chat per request).
- **Batch single-shot** (GLM 5 — intentional one-shot, not multi-turn): just `RubyLLM.chat` + `ask` with no history. Fine for stateless echo services, not a chat app.
- **Display-only history** (Sakana Fugu Ultra, Step 3.7 Flash): store previous messages for the UI, but create a fresh RubyLLM chat and send only the newest user message. This looks like a chat app but the model has no memory of the conversation.
- **Invalid direct history assignment** (Claude Sonnet 5): tries to replay history with `chat.messages = history`, but RubyLLM's `Chat` has no `messages=` writer. Use `add_message` for each historic turn instead.

### 4. Harness compatibility matters as much as model capability

DeepSeek V4 Pro has Tier 1 code but can't complete the run because opencode doesn't handle DeepSeek's thinking-mode `reasoning_content` echo requirement. GPT 5.4 couldn't run via OpenRouter (tool calling not exposed) — Codex CLI was required. Gemma 4 can't run via local llama.cpp due to parser bugs, but works via Ollama Cloud up to ~20K tokens.

A model that runs correctly is more valuable than a model with nominally better code that can't be exercised.

Kimi K2.7 Code exposed a concrete opencode workspace-routing issue: setting `cwd=project_dir` in Python was not enough to make opencode use the result project as its workspace. The first K2.7 attempt wrote into the repository-level placeholder `llm-chat/` directory and the benchmark result directory stayed empty. The runner now passes opencode's explicit `--dir <absolute project_dir>` flag, matching Codex's existing `-C` behavior; the re-run wrote to `results/kimi_k2_7_code/project` and completed.

Local provider probing on `192.168.0.90` is documented in `docs/local-provider-status.md`. Short version: Ollama on `:11434` is reachable but only lists `qwen3:32b` and embeddings; llama-swap on `:11435/v1` has the known Qwen/Gemma/GLM/etc. models but no MiniMax/Kimi; a protected vLLM-like service on `:8080` returns 401 and the required API key is not available in this workspace. Local MiniMax V3 is therefore blocked on vLLM auth/model visibility, not benchmark code.

### 5. Most cost-efficient picks

*(Figures re-verified 2026-07-09 against the OpenRouter live API and vendor price pages; per-run costs recomputed from recorded token logs — earlier numbers under-counted cache reads for several models. Full audit: [`cost_analysis.md`](cost_analysis.md).)*

- **Under $0.05/run**: DeepSeek V4 Flash (Tier B, ~$0.01), Step 3.5 Flash (Tier C, ~$0.02 hist.)
- **Under $1.50/run that actually work**: Nex-N2-Pro (Tier A, ~$0.34), Kimi K2.6 (Tier A, ~$1.00), Kimi K2.7 Code (Tier A, ~$1.15)
- **Cheap near-miss**: MiniMax M3 (Tier B, ~$1.25) has correct RubyLLM and good architecture, but phase 2 DNF + original `.env` secret leak mean it needs cleanup before use.
- **Premium**: Opus 4.8 (~$6.40) / Opus 4.7 (~$7.00), Claude Fable 5 original (~$11.20) / re-release (~$8.30), GPT 5.4 xHigh (~$16)

**Nex-N2-Pro is the cheapest Tier A at ~$0.34/run.** It was free at run time (2026-06-15, OpenRouter `:free` endpoint); that endpoint has since been delisted and the model is now paid at $0.25/$1.00 per M — which still makes it roughly 3× cheaper than the next Tier A option. For a more battle-tested pick, **Kimi K2.6 at ~$1.00/run** (rates rose ~30% since its run: now $0.65/$3.41 per M) is the cheapest dependable Tier A from a major lab. If budget is extremely tight, **DeepSeek V4 Flash at ~$0.01/run** is Tier B with one known bug (model slug needs `anthropic/` prefix) that's a 30-second fix.

Practical reading of the tiers:
- **Production-critical or long-context agentic work**: start with Tier A, then still hand-review library calls, persistence, secrets, and tests.
- **Routine implementation with human supervision**: Tier B can be cost-effective, especially when the known defects are small and easy to patch.
- **Local model evaluation**: use the local results to understand hardware/runtime constraints; do not treat current local Tier C/D runs as replacements for the stronger cloud models on this task.
- **Model research**: the most diagnostic signal here is not just score, but why the score moved — API recall, harness compatibility, persistence strategy, and mock fidelity explain most tier changes.

### 6. Agentic fine-tuning *can* instill library-API correctness the base lacks

The single most interesting result of this batch comes from running Nex-N2-Pro and its raw base head-to-head:

| Model | RubyLLM API | Score | Tier |
|---|---|---|---|
| Qwen 3.5 397B A17B (raw base) | hallucinates `chat.system`/`chat.user`/`response.text` → crashes | 42 | C |
| Nex-N2-Pro (Nex AGI agentic fine-tune of that base) | real `RubyLLM.chat`/`ask`/`response.content` | 83 | A |

**A 41-point swing from identical architecture.** The base exhibits the exact Qwen3.5-family hallucination the whole lineage shares; Nex AGI's agentic fine-tune is what corrected it. This is the **inverse** of this benchmark's other headline (`success_report.nvidia.md`: "Claude reasoning *distillation* does NOT transfer library API knowledge"). The contrast suggests the mechanism matters: distilling reasoning traces doesn't carry API facts, but **task-targeted agentic fine-tuning can** — presumably because the fine-tune corpus contains real tool/library call sequences, not just reasoning. A model's RubyLLM correctness is therefore a property of its post-training, not just its base architecture or parameter count.

---

## Failed Models (no usable code)

| Model | Issue | Root Cause |
|---|---|---|
| Gemma 4 31B (local) | Infinite tool-call repetition after ~11 steps | llama.cpp bug #21375, partially fixed in b8665 |
| Gemma 4 31B (Ollama Cloud) | 504 timeout at ~20K tokens | Cloudflare 100s edge timeout; can't complete 50K+ token run |
| Llama 4 Scout (local) | Tool calls emitted as plain text | llama.cpp lacks Llama 4 pythonic parser |
| Qwen 3 32B (local) | Too slow (7.3 tok/s) | Hardware bottleneck |
| Qwen 2.5 Coder 32B (local) | 90m timeout with 0 files | Infinite reasoning loop |
| GPT 5.4 Pro (OpenRouter) | Stalled after tool-calls | OpenRouter tool-calling integration broken for GPT; use Codex CLI instead |

---

## Why Ollama Fails for Benchmarks

1. **Silent model unloading** — Ollama unloads models mid-session during long autonomous runs, causing opencode to hang waiting for a response from a model that's no longer loaded.
2. **Context drift** — Ollama ignores the requested `num_ctx` and reverts to defaults mid-run, causing OOM or degraded output.
3. **Flaky lifecycle** — `keep_alive: 0` unload requests don't always work. Models stay resident and block the next model from loading.
4. **Format mismatches** — Ollama-native bf16 variants often fail to load, while the same model as a HuggingFace GGUF Q8 works fine under llama-swap.

## Why "Just Use llama.cpp" Isn't Magic Either

llama-swap (wrapping llama-server from llama.cpp) solves Ollama's lifecycle problems but introduces its own:

1. **Tool-call parser gaps** — Each model needs a dedicated parser. Llama 4 (pythonic) and Gemma 4 (repetition loops) don't work.
2. **Reasoning token handling** — GLM and Qwen 3.5 emit `reasoning_content` or `<think>` tags that require `--reasoning-format none` on the server.
3. **Build version sensitivity** — Gemma 4 requires b8665+; older builds give cryptic "Failed to parse input at pos 13" errors.
4. **Repetition loops** — Even with the correct parser, Gemma 4 enters infinite loops after ~11 tool calls.

**Bottom line**: llama.cpp is better than Ollama for unattended runs, but plug-and-play it is not. Each model needs specific flags, and some can't do agentic tool calling yet.

---

## Cross-references

- [`success_report.nvidia.md`](success_report.nvidia.md) — NVIDIA RTX 5090 workstation profile (Q3_K_M / Q4_K_M local models, 32 GB VRAM, subset of the cloud benchmark with different hardware constraints)
- [`success_report.multi_model.md`](success_report.multi_model.md) — Multi-agent orchestration variants (Claude Code subagents, opencode multi-agent, Codex multi-agent). Zero delegations happened across all 7 runs.
- [`audit_prompt_template.md`](audit_prompt_template.md) — The standardized prompt used to score every model consistently. Use this for any future model added to the benchmark.
- [`codex-integration.md`](codex-integration.md) — Codex CLI integration guide (GPT 5.4/GPT 5.5 xHigh runs through Codex, not opencode)
- [`llama-swap.md`](llama-swap.md) — Local NVIDIA llama-swap Docker setup
- [`pricing.md`](pricing.md) — Per-token pricing reference (verified 2026-07-09)
- [`cost_analysis.md`](cost_analysis.md) — Pricing audit, quality × time × cost analysis, and the productivity-floor argument (why going too cheap is a false economy for programming)
