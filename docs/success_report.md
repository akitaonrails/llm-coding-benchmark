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

Cloud models ran a two-phase flow (phase 1: build, phase 2: validate boot/Docker). Local models ran phase 1 only. All models used `opencode run --agent build --format json` as the harness, except GPT 5.4 which used `codex exec --json` directly.

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

## Final Rankings (31 scored models)

All models scored against the same rubric. Note the "RubyLLM OK" column is binary (API correct vs hallucinated) and is separate from the overall score — a model can have correct RubyLLM code and still score low if deliverables or tests are missing.

| Rank | Model | Score | Tier | RubyLLM OK | Provider | Runtime | Cost |
|---:|---|---:|:---:|:---:|---|---|---|
| 1 | **Claude Opus 4.7** | **97** | A | ✅ | OpenRouter | 18m | ~$1.10 |
| 1 | **GPT 5.4 xHigh (Codex)** | **97** | A | ✅ | OpenAI direct | 22m | ~$16 |
| 3 | **GPT 5.5 xHigh (Codex)** | **96** | A | ✅ | OpenAI direct | 18m | ~$10 |
| 4 | **Claude Opus 4.8** | **95** | A | ✅ | OpenRouter | 17m | ~$1.10 |
| 5 | Claude Fable 5 | 94 | A | ✅ | OpenRouter | 24m | ~$11 (est.) |
| 6 | Gemini 3.5 Flash | 93 | A | ✅ | OpenRouter | 18m | ~$3.50 |
| 7 | Kimi K2.6 | 87 | A | ✅ | OpenRouter | 20m | ~$0.30 |
| 7 | GLM 5.2 (Z.ai) | 87 | A | ✅ | Z.ai | 43m | subscription |
| 9 | Kimi K2.7 Code | 86 | A | ✅ | OpenRouter | 22m | ~$0.30 |
| 10 | Claude Opus 4.6 | 83 | A | ✅ | OpenRouter | 16m | ~$1.10 |
| 11 | Gemini 3.1 Pro | 82 | A | ✅ | OpenRouter | 14m | ~$0.40 |
| 12 | Claude Sonnet 4.6 | 78 | B | ✅ | OpenRouter | 16m | ~$0.63 |
| 12 | DeepSeek V4 Flash | 78 | B | ✅ | OpenRouter | 3m | ~$0.01 |
| 12 | MiniMax M3 | 78 | B | ✅ | OpenRouter | 53m (phase 2 DNF) | ~$0.10 |
| 12 | Qwen3.7 Max | 78 | B | ✅ | OpenRouter | 19m | ~$1.40 |
| 16 | Grok 4.3 | 72 | B | ✅ | OpenRouter | 15m | ~$1.74 |
| 17 | Qwen 3.6 Plus | 71 | B | ✅ | OpenRouter | 17m | ~$0.15 |
| 18 | DeepSeek V4 Pro | 69 | B | ✅ | OpenRouter | 22m (DNF) | ~$0.50 |
| 18 | Kimi K2.5 | 69 | B | ✅ | OpenRouter | 29m | ~$0.10 |
| 20 | Xiaomi MiMo V2.5 Pro | 67 | B | ✅ | OpenRouter | 11m | ~$0.14 |
| 21 | GLM 5 | 64 | B | ✅ | OpenRouter | 17m | ~$0.11 |
| 22 | Step 3.5 Flash | 56 | C | ⚠️ bypass | OpenRouter | 38m | ~$0.02 |
| 23 | Qwen 3.5 35B | 55 | C | ✅ | Local (AMD) | 28m | free |
| 24 | GLM 4.7 Flash bf16 | 52 | C | ✅ | Local (AMD) | failed | free |
| 25 | GLM 5.1 (Z.ai) | 46 | C | ❌ | Z.ai | 22m | subscription |
| 26 | DeepSeek V3.2 | 43 | C | ❌ | OpenRouter | 60m | ~$0.07 |
| 27 | MiniMax M2.7 | 41 | C | ❌ | OpenRouter | 14m | ~$0.30 |
| 28 | Qwen 3.5 122B | 37 | D | ❌ | Local (AMD) | 43m | free |
| 29 | Qwen 3 Coder Next | 32 | D | ❌ | Local (AMD) | 17m | free |
| 30 | Grok 4.20 | 25 | D | ❌ | OpenRouter | 8m | ~$0.60 |
| 31 | GPT OSS 20B | 11 | D | ❌ | Local (AMD) | failed | free |

**Note on score adjustment**: The original audit rubric wrongly penalized `RUBY_VERSION=4.0.2` as a fake placeholder. It's actually the current stable Ruby (released 2026-03-17). Scores for every model except Gemini 3.1 Pro have been adjusted +3 to remove that deduction. Gemini used Ruby 3.4.1 (older LTS, valid) so its score is unchanged. Relative ordering is preserved; only **MiniMax M2.7 crossed a tier boundary (D → C)** due to this correction.

### What changed from the previous ranking

- **Gemini 3.5 Flash** (added 2026-06-15, scored 93/100, Tier A, #6): the benchmark's biggest surprise — a Flash-tier model is now the #6 model overall and the best non-Anthropic/non-OpenAI result, 11 points clear of Gemini 3.1 Pro (82). Textbook RubyLLM idiom (`chat(model:, provider: :openrouter, assume_model_exists: true)` + `with_instructions` + `add_message` replay + `complete` + `content`, latest sonnet-4.6), the strongest test suite of the cohort, real Turbo Streams, and file-backed persistence (capped at 50 messages, system message preserved) that survives restart. Run in-house after closing community PR #6 (which under-claimed 86 and whose committed excerpt showed an older model pin). Score validated by a blind A/B cross-audit (independent judge, projects anonymized) that scored it 91 and confirmed it clearly outranks Gemini 3.1 Pro. Held below the frontier-lab models by file-store concurrency/ephemerality gaps and no missing-key preflight.
- **Qwen3.7 Max** (added 2026-06-15, scored 78/100, Tier B, #12): run in-house after closing community PR #4, which claimed 82/A on a phase-2 DNF. Under our harness it completed both phases (the DNF was the author's environment), but scored 78/B not 82/A: it pins the non-latest `claude-sonnet-4`, skips the required Turbo Streams entirely (raw SSE via `ActionController::Live`), and uses an unbounded class-level `@conversations` hash (process-local, memory-leaking). RubyLLM API itself is correct. Ties the existing 78/B cluster (Sonnet 4.6, DeepSeek V4 Flash, MiniMax M3).
- **Kimi K2.7 Code** (added 2026-06-13, scored 86/100, Tier A, #9): exposed on OpenRouter as `moonshotai/kimi-k2.7-code`. Real RubyLLM throughout (`RubyLLM.chat` + `add_message` full-history-replay + `complete` + `response.content`), verified against gem source 1.16.0; session-cookie persistence, error-path-tested, real Turbo Streams + 3 Stimulus controllers. **Methodology note**: the structural scanner flagged six `chat.user`/`chat.assistant` "hallucinations" that were all false positives — they resolve to the app's own `Chat`/`Message` domain methods, not RubyLLM's DSL. Hand-reading confirmed genuine Tier 1 API; trusting the scanner would have wrongly tanked it like GLM 5.1. Lands just below the K2.6/GLM 5.2 pair (87) because it ships no `with_instructions` system prompt (its main regression from K2.6), no message cap on the cookie, and embeds LLM I/O in the session value-object model rather than a service.
- **GLM 5.2** (added 2026-06-14): the benchmark's biggest single-version jump — 46→87, Tier C→A, #21→#6. GLM 5.1's fatal hallucination (invented `chat.user`/`chat.assistant`, multi-turn crash) is gone; 5.2 replays history with the real `add_message` and verifies clean against gem source 1.16.0. Cleanest dependency-injection design in the cohort. Held to a tie with Kimi K2.6 (and ranked just behind it) only by an uncapped process-local singleton store — the persistence axis again. Slowest Tier A run at 43m on the throttled Z.ai coding endpoint.
- **Claude Fable 5** (added 2026-06-11): first Claude 5-generation entry, debuting at 94/100 Tier A (#5). Verified-correct RubyLLM path (`RubyLLM.chat(model:, provider: :openrouter, assume_model_exists: true)` + `with_instructions` + `add_message` + `ask` + `response.content`, all checked against ruby_llm 1.16.0 gem source). Uniquely, it grepped the installed gem source mid-run to verify the API before writing the integration — the only model observed doing the audit’s own verification step unprompted. 36 tests / 99.3% line coverage with a signature-faithful `FakeChat`, capped LRU history, missing-key preflight, and a zero-fix phase 2 (boot + Docker + compose + live chat). Held back by process-local singleton persistence (lost on restart, not multi-worker safe) and price: ~$11 est. per run at $10/$50 per M — roughly 10× an Opus 4.8 run for one point less.
- **Claude Opus 4.8** (added 2026-06-01): new Tier A entry at 95/100. It keeps Opus 4.7's correct RubyLLM path (`RubyLLM.chat(model:, provider: :openrouter, assume_model_exists: true)` + `with_instructions` + `add_message` + `ask` + `response.content`), upgrades to Ruby 4.0.3, writes 34 tests with a correctly-shaped `FakeChat`, and phase 2 validates local boot, live OpenRouter POST, Docker build, and compose health. Main deductions: unbounded session-cookie history and no explicit missing-key preflight before RubyLLM initialization.
- **MiniMax M3** (added 2026-06-01): jumps MiniMax from C to B at 78/100. M3 fixes M2.7's fatal `RubyLLM.chat(messages:)` hallucination and uses the real API (`RubyLLM.chat` + `with_instructions` + `add_message` + `ask` + `response.content`). It has a respectable 19-test suite, session cap, Turbo Streams, and service-layer separation. Two blockers keep it out of Tier A: phase 2 stalled during compose validation, and the model originally wrote a real `.env` with `OPENROUTER_API_KEY` into its result project. That file was deleted and the exact key was redacted from all discovered historical artifacts, but the output is penalized for the secret hygiene failure.
- **Grok 4.3** (added 2026-05-04): entry at 72/100 Tier B. Real RubyLLM API throughout (`RubyLLM::Chat.new` + `add_message` + `ask` + `response.content` + `RubyLLM::Error` rescue, all verified against gem source). Server-side Turbo Streams work, real README and `compose.yaml` ship. **Killer weakness**: Stimulus is dead at runtime — `app/javascript/application.js` is a one-line comment, no `import "./controllers"`, no `Application.start()`, so every `data-controller="chat"` action is silently broken. Tests stub `RubyLLM.stub :chat` but the controller calls `RubyLLM::Chat.new` — the stub is bypassed. Stale model pin to `claude-3.7-sonnet` despite README claiming "latest Claude Sonnet". Cost $1.74 / 15m — ~5× Kimi K2.6 for a worse result. Big jump from Grok 4.20 (25/100, Tier D) but doesn't reach Tier A.

Several earlier models also moved significantly after re-audit with the corrected rubric and verified API criteria:

- **Kimi K2.5** (was Tier 3 → now Tier B): `chat.complete(&block)` and `chat.add_message(role:, content:)` are both real RubyLLM API, not hallucinations as previously claimed. Drops to B solely because tests don't exercise the LLM path and class-var storage is fragile.
- **Kimi K2.6** (was Tier 2 → now Tier A): with the kwargs "bug" revealed as non-existent, K2.6 is the only Chinese model whose tests actually mock RubyLLM with a correctly-signatured FakeChat AND rescues `RubyLLM::Error` AND uses a session-cookie store that survives restarts.
- **Gemini 3.1 Pro** (was Tier 3 → now Tier A): `Chat.new` is real, `add_message` kwargs form is valid, and Gemini has proper cache-backed server-side persistence plus real Turbo Streams. Uses Ruby 3.4.1 (older LTS, valid) rather than 4.0.2 — both are production-viable.
- **GPT 5.4 xHigh** (was Tier 2 → now co-leader Tier A): the `add_message` kwargs form isn't a bug. Re-audit scored it 94/100, tying Opus 4.7 on correctness but losing on cost (~15× more expensive).
- **MiMo V2.5 Pro** (was "Tier 1" overclaim → now Tier B at 64): still the cleanest RubyLLM integration from a non-Anthropic model, but demoted because tests never exercise the LLM path and the `ChatStore` Singleton is process-local (dies on Puma restart, not multi-worker safe).
- **DeepSeek V4 Pro** (was "Tier 1 code" → now Tier B at 66): DNF harness run. Clean RubyLLM usage but ships stock Rails README template + no docker-compose + missing bundle-audit. Concrete gaps, not just harness incompatibility.
- **GLM 5.1** (was Tier 2 → now Tier C at 43): `c.user()` / `c.assistant()` fluent DSL confirmed as hallucinated via grep of the gem source. Plus: every request rebuilds `ChatSession.new`, discarding history entirely. Two bugs compound.

---

## Tier A — Ship as-is (11 models)

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

### 6. Gemini 3.5 Flash (93/100) — best non-Anthropic/non-OpenAI result, a Flash that beats Pro

Run + scored in-house (2026-06-15) after closing community PR #6, which submitted pre-scored results without the gitignored project code. The result is the benchmark's biggest surprise: a *Flash*-tier model lands at **93/100, #6 overall** — above GLM 5.2 / Kimi K2.6 (87) and **11 points above Gemini 3.1 Pro** (82), behind only Opus 4.7/4.8, GPT 5.4/5.5, and Fable 5. Newer generation (3.5 vs 3.1) beats the tier gap.

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

### 7. Kimi K2.6 (87/100) — best Chinese-model output

The standout of the non-Anthropic/non-OpenAI cohort. `RubyLLM.chat` + `with_instructions(SYSTEM_INSTRUCTION)` + `chat.add_message(role:, content:)` + `chat.ask` + `response.content` — all real API.

- **Only Chinese model that combines**: real LLM-path tests (`FakeChat` with correct signatures) + error-path rescue (`rescue RubyLLM::Error` with flash via turbo_stream) + session-cookie persistence with `MAX_MESSAGES = 50` cap.
- Full Gemfile: ruby_llm, turbo, stimulus, tailwindcss, brakeman, bundler-audit, rubocop-rails, simplecov, capybara.
- Session cookie survives restart and is multi-worker safe.

**Only meaningful deduction**: full history replay each turn (wastes tokens vs persistent-instance pattern).

At ~$0.30/run, Kimi K2.6 is the cheapest Tier A model — 3-50× cheaper than the top 2.

### 7. GLM 5.2 / Z.ai (87/100) — biggest single-version turnaround in the benchmark

GLM 5.2 fixes the exact bug that put GLM 5.1 in Tier C (46/100): where 5.1 invented `chat.user`/`chat.assistant` to seed multi-turn history (crashing on turn 2), 5.2 uses the real `chat.add_message(role:, content:)` to replay prior turns. Every RubyLLM call is verified against gem source 1.16.0 — `RubyLLM.chat(model:)` (via an injected `client`), `with_instructions`, `add_message`, `ask`, `response.content` — zero hallucinations. Phase 2 live-validated the full path end-to-end (real OpenRouter chat, Docker, compose, CSRF correctly rejecting a bare curl POST).

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

### 9. Kimi K2.7 Code (86/100) — correct API the scanner nearly mis-flagged

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

### 10. Claude Opus 4.6 (83/100) — thinner than 4.7 but clean

Correct RubyLLM usage (`RubyLLM.chat` + `chat.ask` + `response.content`). History replay via `service.chat.messages << RubyLLM::Message.new(...)` — works because `Chat#messages` is `attr_reader` on an Array, but reaches into internal state (Demeter violation).

**Biggest weakness**: no rescue around `chat_service.ask` in the controller. A transient OpenRouter 5xx produces a 500 page with stack trace. This is the difference between 4.6 (Tier A low) and 4.7 (Tier A high).

### 11. Gemini 3.1 Pro (82/100) — cache-backed persistence, real Turbo Streams

Previously misclassified as Tier 3 for "invented `Chat.new` + `add_message`" — both are real API.

- `RubyLLM::Chat.new(model:, provider:, assume_model_exists:)` — real constructor
- `chat.add_message(role:, content:)` — valid positional hash form
- `chat.ask` + `response.content` — correct
- Dockerfile uses Ruby 3.4.1 (older LTS, still production-viable)
- Real Turbo Streams (not fetch+innerHTML): `remove empty-state → append user + assistant → replace form`
- Rails.cache-backed session persistence with 2h expiry
- FakeChat mocks match real API shape + error path tested

**Killer weakness**: uses stale model string `claude-3.7-sonnet` instead of current Sonnet 4.x. One-character fix.

---

## Tier B — 1-2 hours to ship (11 models)

### 12. Claude Sonnet 4.6 (78/100) — ambitious scope, subtle bug

Most feature-rich UI of the benchmark (multi-conversation sidebar with per-chat titles). Best controller separation (ChatsController + MessagesController). Mocha-based tests.

**Killer weakness**: `LlmChatService#call` has a silent control-flow bug — only calls `ask` if the last history message is a user message, returns `""` otherwise. The test at `llm_chat_service_test.rb:32-50` rubber-stamps this bug (passes against the broken path). Also: entire conversation graph stored in 4KB session cookie → overflows after ~10 turns.

### 12. DeepSeek V4 Flash (78/100) — cheapest viable option

~$0.01/run (!). `RubyLLM.chat(model:, provider:)` + `add_message(role:, content:)` + `ask` + `.content` — real API throughout. Session-replay multi-turn via `session[:messages]`. WebMock tests on the actual OpenRouter HTTP endpoint — genuine exercise of the LLM path.

**Killer weakness**: model slug `"claude-sonnet-4"` missing `anthropic/` prefix — will 404 against OpenRouter at runtime. One-character fix, but fatal as-is. Also: no rescue around `chat.ask`, 4KB cookie limit on long chats.

### 12. MiniMax M3 (78/100) — fixed API recall, failed secret hygiene

M3 is the first MiniMax result with correct RubyLLM usage. `app/services/chat_service.rb` uses `RubyLLM.chat(model: @model)`, `with_instructions`, `add_message(role:, content:)`, `ask`, and `response.content`, all real API per the verified table. It also caps session history (`MAX_HISTORY_TURNS = 20`), separates `ChatService` from `ChatController`, ships Turbo Stream append/update responses, and has 19 tests across service, controller, and integration paths.

The test suite is better than M2.7's hallucination-mocking setup, but still relies heavily on `ChatService.any_instance.stubs(:ask)` rather than a FakeChat matching RubyLLM itself. Phase 2 verified local boot and Docker build according to the transcript, then stalled during compose validation and the harness marked the run `failed` after six minutes of no progress.

**Killer strength**: MiniMax M3 completely fixes M2.7's fatal `RubyLLM.chat(messages:)` batch-form hallucination. **Killer weakness**: the model originally wrote a real `.env` containing `OPENROUTER_API_KEY` into the result project. The file was deleted and exact key occurrences were redacted from historical artifacts, but this is a severe prompt violation and keeps the result out of Tier A.

### 12. Qwen3.7 Max (78/100) — correct API, but skips Turbo Streams and leaks memory

Run + scored in-house (2026-06-15) after closing community PR #4, which claimed **82/A on a phase-2 DNF**. Under our harness it actually **completed both phases** — so the DNF was the author's environment, not the model — but the hand-read surfaced gaps the PR's prose glossed over, landing it at 78/B rather than 82/A. The RubyLLM usage itself is clean (`app/services/chat_service.rb`), all verified real: `RubyLLM.chat(model:)`, `with_instructions`, `ask(message, &block)` streaming, `reset_messages!`, `response.content` / `chunk.content`. Multi-turn uses the persistent-instance pattern (one `RubyLLM::Chat` kept alive per conversation).

- **Pins `anthropic/claude-sonnet-4`, not the latest 4.6** (−2 on RubyLLM correctness) — the brief asks for latest Claude Sonnet.
- **No Turbo Streams at all** — it streams via raw SSE (`ActionController::Live` + `EventSource` in `chat_controller.js`). A legitimate streaming approach, but explicitly not the Hotwire/Turbo Streams mechanism the brief requires (−5 on Hotwire). It does ship a substantial Stimulus controller and partials.
- **Persistence is the worst tier seen so far**: a class-level `@conversations = {}` hash holding live `Chat` objects keyed by conversation id. Process-local (lost on restart), not multi-worker safe, and **unbounded — never evicted, a memory leak** under sustained use.
- `FakeChat` tests exercise the LLM path with correct signatures; missing-key preflight + blank guard + a broad `rescue StandardError` → friendly SSE error. Both phases validated live.

**Killer strength**: correct RubyLLM API + completes phase 2 cleanly (contradicting the PR's DNF claim). **Killer weakness**: ignores the required Turbo Streams in favor of SSE, and the leaky class-var store would degrade a long-running production process.

### 16. Grok 4.3 (72/100) — clean controller, dead Stimulus

`RubyLLM::Chat.new(model:)` + `add_message(role:, content:)` + `chat.ask` + `response.content` + `RubyLLM::Error` rescue — real API throughout, all verified against gem source. Cleanest hand-written chat controller in the cohort (48 lines, no service-object over-engineering, no fluent-DSL flourishes). Real Turbo Streams in the controller. Real README, real `compose.yaml`, multi-stage Dockerfile. Cookie-based session persistence. ~$1.74/run, 15m wall time.

**Killer weakness**: **Stimulus is dead code at runtime.** `app/javascript/application.js` is a one-line comment with no `import "./controllers"` and no `Application.start()`. Built `app/assets/builds/application.js` is 48 bytes (just a sourcemap pointer). So `data-controller="chat"` is inert — Enter-to-send, autoresize, autoscroll, clear-input all silently broken. Phase 2 self-reported "local boot OK" without exercising the JS layer (a confidence-vs-verification gap distinct from Claude/Kimi which over-test).

**Other issues**: tests stub `RubyLLM.stub :chat` but the controller calls `RubyLLM::Chat.new` — the stub is bypassed (the test would actually hit the network or fail on missing key). Stale model pin `anthropic/claude-3.7-sonnet` (current is 4.7) despite README claiming "latest Claude Sonnet". No `with_instructions` system prompt.

Cost ($1.74) is ~5× Kimi K2.6 for a worse output, putting Grok 4.3 in an awkward price/quality slot. Big jump from Grok 4.20 (25/100, Tier D below) but doesn't reach Tier A.

### 17. Qwen 3.6 Plus (71/100) — cleanest open-model RubyLLM integration

Real RubyLLM usage with service-layer separation. Stimulus controller is well-built (escapeHtml, loading state, auto-scroll). Partials decomposed cleanly.

**Biggest weaknesses**: tests make *real* network calls (no WebMock), history is client-side JS only (lost on refresh), uses `fetch` + `innerHTML` instead of Turbo Streams (no `turbo-rails` gem).

### 18. DeepSeek V4 Pro (69/100) — Tier 1 code, Tier 3 deliverables

Previously ranked higher based on code quality alone. Re-audited:

**Clean RubyLLM usage**: `@chat = RubyLLM.chat; @chat.ask(content); result.content` — persistent Chat instance lets RubyLLM manage history internally (same pattern as MiMo). Tests use WebMock on real OpenRouter URL.

**But deliverables are broken**:
- README is the stock Rails "This README would normally document..." template (**not** customized)
- **No `docker-compose.yml`** — prompt explicitly required it

Run DNF'd because DeepSeek's thinking mode requires the client to echo `reasoning_content` back and opencode strips it. `reasoning: false` in opencode config didn't prevent DeepSeek from emitting thinking tokens server-side. The code written before the harness crashed is Tier 1 quality, but the deliverables are demo-level.

### 18. Kimi K2.5 (69/100) — reclassified up from Tier 3

Previously ranked as Tier 3 for "inventing `chat.add_message()` + `complete()`". **Both are real public methods** in RubyLLM 1.14.1 — the previous audit was wrong.

Uses `RubyLLM.chat(model:)` + `client.add_message(role:, content:)` + `client.complete(&block)` — valid API chain. Also attempts true server-push streaming via `Turbo::StreamsChannel.broadcast_append_to`. 37 test methods (most thorough count in the benchmark).

**Killer weakness**: none of the 37 tests actually mock RubyLLM — they test PORO CRUD and `respond_to?`, not the gem interaction. Also uses class-var storage (`Chat.storage = @storage ||= {}`) — worse than Singleton because it's not mutex-protected.

### 20. Xiaomi MiMo V2.5 Pro (67/100) — cleanest multi-turn idiom

Uses `RubyLLM::Chat.new(model:, provider:)` + `@llm_chat.ask(content, &)` + `response.content`. Persistent `@llm_chat` instance means RubyLLM tracks history internally — the cleanest multi-turn pattern in the entire benchmark, cleaner than explicit history replay.

**But**:
- Tests never exercise the LLM path (only blank-guard + constants assertions)
- No error handling around `@chat.ask` — any API hiccup = 500 page
- `ChatStore` Singleton is process-local (dies on Puma restart, not shared across workers)
- No system prompt via `with_instructions`

~$0.14/run and 11 minutes makes this the fastest viable non-Anthropic option, but it needs ~2 engineer-hours of patching (add `rescue RubyLLM::Error`, swap Singleton for `Rails.cache`, add FakeChat mocks, add system prompt) to reach production quality.

### 21. GLM 5 (64/100) — correct API, stateless design

`RubyLLM.chat(model: "anthropic/claude-sonnet-4")` + `chat.ask` + `response.content` — correct. Mocha stubs match real API shape. Only one happy-path test, no error-path coverage.

**Killer weakness**: **zero multi-turn state** — every POST creates a fresh `RubyLLM.chat` with no history. The "chat app" is a stateless echo service. User asks "what did I just say?" → model replies "I don't know."

---

## Tier C — major rework needed (6 models)

### 22. Step 3.5 Flash (56/100)

Bypasses `ruby_llm` entirely using raw `Net::HTTP` to OpenRouter. The HTTP implementation itself is competent (timeouts, JSON parse errors, missing-key preflight all rescued with user-visible fallbacks). Session-backed multi-turn works. Best error handling of any model.

**But**: non-compliant with the prompt requirement (missing `ruby_llm` gem). Also: the Stimulus `afterSubmit` flow never renders the user's message into `#messages` — only the assistant reply appears, so the UI is silently broken.

### 23. Qwen 3.5 35B (55/100) — local model

Real `RubyLLM.chat` + `chat.ask` + `chat.messages.last.content` — correct API. No service layer (logic in controller). No multi-turn (fresh `RubyLLM.chat` per request).

**Killer weakness**: `test/models/ruby_llm_service_test.rb:14-22` wraps the real call in `rescue => e; assert true` — tests pass even if RubyLLM is completely broken.

### 24. GLM 4.7 Flash bf16 (52/100) — local model, near-miss

**Most RubyLLM-literate local model** of the benchmark — correctly uses the fluent chain `.with_model().with_temperature().with_params().with_instructions().complete(&block)`, all real API per gem source.

**Fatal bug**: `gem "ruby_llm"` is placed in `group :development, :test` with `require: false` — won't load in production. App would crash on boot with `NameError`. Also uses class-var `Message.all` storage (process-local).

### 25. GLM 5.1 / Z.ai (46/100) — hallucinated fluent DSL

`RubyLLM.chat(model:, provider:)` is correct, but history is replayed via hallucinated `c.user(msg)` / `c.assistant(msg)` fluent DSL — these methods do not exist in RubyLLM. Confirmed via grep of the gem source.

Compounded bug: every HTTP request constructs a brand-new `ChatSession.new` that discards history — so the hallucinated DSL calls are rarely entered in practice because there's never any history to replay. Two bugs mask each other.

Stimulus controller uses `fetch` + manual `innerHTML` for streaming — SSE-based but not Turbo Streams.

### 26. DeepSeek V3.2 (43/100)

Uses `RubyLLM::Client.new` + `client.chat(messages: [...])` — **both hallucinated**. Treats response as raw OpenAI JSON via `result.dig("choices", 0, "message", "content")`. Tests mock `RubyLLM::Client.any_instance` — mocking a class that doesn't exist. The entire LLM integration is fictional.

**Redeeming qualities**: best error-rescue discipline of any Tier 3 model (try/rescue/log/user-message), real docker-compose, substantive 265-line README.

---

### 27. MiniMax M2.7 (41/100) — moved from Tier D after Ruby 4.0.2 correction

Hallucinated `RubyLLM.chat(model:, messages: [...])` batch signature — crashes on first call (`ArgumentError: unknown keyword: messages`). Best architectural decomposition of any Tier C/D model (service + form object + POROs + partials), wrapped around a corpse.

Tests mock the hallucinated API so they pass green against a bug.

## Tier D — throw away (4 models)

### 28. Qwen 3.5 122B (37/100) — local model

Doesn't use `ruby_llm` at all. Uses `Openrouter::Client.new(api_key: @api_key)` — wrong casing for the real `OpenRouter::Client` (exists in `openrouter` gem but requires a configuration object, not a bare `api_key:` kwarg). Plus calls `client.chat(model:, messages:)` — real gem method is `completion`, not `chat`.

### 29. Qwen 3 Coder Next (32/100) — local model

Invented `RubyLLM::Client.new(api_key:, model:)` + `client.chat(messages: [...])` + OpenAI-shaped `response.choices.first.message.content` — pure hallucination. Also commits a placeholder `.env` file to the repo.

### 30. Grok 4.20 (25/100)

Bypasses RubyLLM with `ruby-openai`, but the gem is in `:development, :test` group with `require: false` — production `NameError` on first request. Gemfile missing turbo-rails, stimulus-rails, bundle-audit.

Stimulus controller JavaScript is **uncompilable** (`class ChatFormController < StimulusController` — uses Ruby's `<` inheritance syntax in JS, `StimulusController` never imported). Uses CDN Tailwind script tag inside the layout (CSP risk).

At ~$0.60/run, Grok is the most expensive Tier D model.

### 31. GPT OSS 20B (11/100) — local model

Benchmark low. Stock Rails README template (no customization), nested `app/app/` directory (violates "stay in workspace root" rule), **no tests folder at all**, no docker-compose, Gemfile has `gem "tailwindcss"` (CLI gem, not the Rails binding) with brakeman commented out.

Invented `RubyLLM::Client.new(provider:, api_key:)` + `client.chat(content:, model:)` + `response.output_text`. Zero rescue blocks, zero persistence, zero Stimulus controllers.

20B local models on llama.cpp can't reliably follow long agentic instructions.

---

## Cross-Cutting Findings

### 1. Ruby version choice varies but is uniformly valid

Almost every model shipped `ARG RUBY_VERSION=4.0.2` or `FROM ruby:4.0.2-slim` (current stable, released 2026-03-17). Gemini 3.1 Pro shipped Ruby 3.4.1 (older LTS, still supported). Both are production-viable. An earlier version of this report incorrectly treated 4.0.2 as a fake placeholder — it's not; the Rails 8.1 generator defaults to the current stable, and every model inheriting that default is correct. No deductions apply.

### 2. Test coverage measures nothing without mock-fidelity

Kimi K2.5 wrote 37 tests (most in the benchmark) but none of them mock RubyLLM. They test PORO CRUD and `respond_to?`. A test suite that doesn't exercise the LLM code path cannot catch bugs in that path, no matter how many test methods you count.

Gemini 3.1 Pro's test suite is smaller (11 tests) but uses a correctly-signatured `FakeChat` that exercises real API paths including error handling. Gemini scored higher on test quality despite fewer tests.

### 3. RubyLLM idiomatic usage varies wildly

Models use three different legitimate multi-turn patterns:
- **Persistent instance** (MiMo, DeepSeek V4 Pro): create `Chat` once, call `.ask()` repeatedly. RubyLLM tracks history internally. Cleanest, but persistence is fragile (process-local objects).
- **Explicit history replay** (Gemini 3.5 Flash, Kimi K2.7, GLM 5.2, Claude Fable 5, Opus 4.8/4.7/4.6, Sonnet 4.6, Kimi K2.6, Gemini, DeepSeek V4 Flash, MiniMax M3): rebuild `Chat`, call `.add_message()` per historic message, then `.ask()`. More code but persistence-friendly (store messages in cookie/cache, reconstruct Chat per request).
- **Batch single-shot** (GLM 5 — intentional one-shot, not multi-turn): just `RubyLLM.chat` + `ask` with no history. Fine for stateless echo services, not a chat app.

### 4. Harness compatibility matters as much as model capability

DeepSeek V4 Pro has Tier 1 code but can't complete the run because opencode doesn't handle DeepSeek's thinking-mode `reasoning_content` echo requirement. GPT 5.4 couldn't run via OpenRouter (tool calling not exposed) — Codex CLI was required. Gemma 4 can't run via local llama.cpp due to parser bugs, but works via Ollama Cloud up to ~20K tokens.

A model that runs correctly is more valuable than a model with nominally better code that can't be exercised.

Kimi K2.7 Code exposed a concrete opencode workspace-routing issue: setting `cwd=project_dir` in Python was not enough to make opencode use the result project as its workspace. The first K2.7 attempt wrote into the repository-level placeholder `llm-chat/` directory and the benchmark result directory stayed empty. The runner now passes opencode's explicit `--dir <absolute project_dir>` flag, matching Codex's existing `-C` behavior; the re-run wrote to `results/kimi_k2_7_code/project` and completed.

Local provider probing on `192.168.0.90` is documented in `docs/local-provider-status.md`. Short version: Ollama on `:11434` is reachable but only lists `qwen3:32b` and embeddings; llama-swap on `:11435/v1` has the known Qwen/Gemma/GLM/etc. models but no MiniMax/Kimi; a protected vLLM-like service on `:8080` returns 401 and the required API key is not available in this workspace. Local MiniMax V3 is therefore blocked on vLLM auth/model visibility, not benchmark code.

### 5. Most cost-efficient picks

- **Under $0.05/run**: DeepSeek V4 Flash (Tier B, ~$0.01), Step 3.5 Flash (Tier C, ~$0.02)
- **Under $0.50/run that actually work**: Kimi K2.6 (Tier A, ~$0.30), Gemini 3.1 Pro (Tier A, ~$0.40), MiMo V2.5 Pro (Tier B, ~$0.14)
- **Cheap near-miss**: MiniMax M3 (Tier B, ~$0.10) has correct RubyLLM and good architecture, but phase 2 DNF + original `.env` secret leak mean it needs cleanup before use.
- **Premium**: Opus 4.8/4.7 (Tier A, ~$1.10), Claude Fable 5 (Tier A, ~$11 est.), GPT 5.4 xHigh (Tier A, ~$16)

For production use where code correctness matters, **Kimi K2.6 at ~$0.30/run is the cheapest Tier A** — 3-50× cheaper than the other Tier A models at comparable quality. If budget is extremely tight, **DeepSeek V4 Flash at ~$0.01/run** is Tier B with one known bug (model slug needs `anthropic/` prefix) that's a 30-second fix.

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
- [`codex-integration.md`](codex-integration.md) — Codex CLI integration guide (GPT 5.4 xHigh runs through Codex, not opencode)
- [`llama-swap.md`](llama-swap.md) — Local NVIDIA llama-swap Docker setup
- [`pricing.md`](pricing.md) — Per-token pricing reference for cost calculations
