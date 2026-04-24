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

## Final Rankings (22 models)

All models scored against the same rubric. Note the "RubyLLM OK" column is binary (API correct vs hallucinated) and is separate from the overall score — a model can have correct RubyLLM code and still score low if deliverables or tests are missing.

| Rank | Model | Score | Tier | RubyLLM OK | Provider | Runtime | Cost |
|---:|---|---:|:---:|:---:|---|---|---|
| 1 | **Claude Opus 4.7** | **94** | A | ✅ | OpenRouter | 18m | ~$1.10 |
| 1 | **GPT 5.4 xHigh (Codex)** | **94** | A | ✅ | OpenAI direct | 22m | ~$16 |
| 3 | Kimi K2.6 | 84 | A | ✅ | OpenRouter | 20m | ~$0.30 |
| 4 | Gemini 3.1 Pro | 82 | A | ✅ | OpenRouter | 14m | ~$0.40 |
| 5 | Claude Opus 4.6 | 80 | A | ✅ | OpenRouter | 16m | ~$1.10 |
| 6 | Claude Sonnet 4.6 | 75 | B | ✅ | OpenRouter | 16m | ~$0.63 |
| 6 | DeepSeek V4 Flash | 75 | B | ✅ | OpenRouter | 3m | ~$0.01 |
| 8 | Qwen 3.6 Plus | 68 | B | ✅ | OpenRouter | 17m | ~$0.15 |
| 9 | DeepSeek V4 Pro | 66 | B | ✅ | OpenRouter | 22m (DNF) | ~$0.50 |
| 9 | Kimi K2.5 | 66 | B | ✅ | OpenRouter | 29m | ~$0.10 |
| 11 | Xiaomi MiMo V2.5 Pro | 64 | B | ✅ | OpenRouter | 11m | ~$0.14 |
| 12 | GLM 5 | 61 | B | ✅ | OpenRouter | 17m | ~$0.11 |
| 13 | Step 3.5 Flash | 53 | C | ⚠️ bypass | OpenRouter | 38m | ~$0.02 |
| 14 | Qwen 3.5 35B | 52 | C | ✅ | Local (AMD) | 28m | free |
| 15 | GLM 4.7 Flash bf16 | 49 | C | ✅ | Local (AMD) | failed | free |
| 16 | GLM 5.1 (Z.ai) | 43 | C | ❌ | Z.ai | 22m | subscription |
| 17 | DeepSeek V3.2 | 40 | C | ❌ | OpenRouter | 60m | ~$0.07 |
| 18 | MiniMax M2.7 | 38 | D | ❌ | OpenRouter | 14m | ~$0.30 |
| 19 | Qwen 3.5 122B | 34 | D | ❌ | Local (AMD) | 43m | free |
| 20 | Qwen 3 Coder Next | 29 | D | ❌ | Local (AMD) | 17m | free |
| 21 | Grok 4.20 | 22 | D | ❌ | OpenRouter | 8m | ~$0.60 |
| 22 | GPT OSS 20B | 8 | D | ❌ | Local (AMD) | failed | free |

### What changed from the previous ranking

Several models moved significantly after re-audit with the corrected rubric and verified API criteria:

- **Kimi K2.5** (was Tier 3 → now Tier B): `chat.complete(&block)` and `chat.add_message(role:, content:)` are both real RubyLLM API, not hallucinations as previously claimed. Drops to B solely because tests don't exercise the LLM path and class-var storage is fragile.
- **Kimi K2.6** (was Tier 2 → now Tier A): with the kwargs "bug" revealed as non-existent, K2.6 is the only Chinese model whose tests actually mock RubyLLM with a correctly-signatured FakeChat AND rescues `RubyLLM::Error` AND uses a session-cookie store that survives restarts.
- **Gemini 3.1 Pro** (was Tier 3 → now Tier A): `Chat.new` is real, `add_message` kwargs form is valid, and Gemini is the only model with proper cache-backed server-side persistence AND real Turbo Streams AND a Ruby 3.4.1 (not fake 4.0.2) Dockerfile.
- **GPT 5.4 xHigh** (was Tier 2 → now co-leader Tier A): the `add_message` kwargs form isn't a bug. Re-audit scored it 94/100, tying Opus 4.7 on correctness but losing on cost (~15× more expensive).
- **MiMo V2.5 Pro** (was "Tier 1" overclaim → now Tier B at 64): still the cleanest RubyLLM integration from a non-Anthropic model, but demoted because tests never exercise the LLM path and the `ChatStore` Singleton is process-local (dies on Puma restart, not multi-worker safe).
- **DeepSeek V4 Pro** (was "Tier 1 code" → now Tier B at 66): DNF harness run. Clean RubyLLM usage but ships stock Rails README template + no docker-compose + missing bundle-audit. Concrete gaps, not just harness incompatibility.
- **GLM 5.1** (was Tier 2 → now Tier C at 43): `c.user()` / `c.assistant()` fluent DSL confirmed as hallucinated via grep of the gem source. Plus: every request rebuilds `ChatSession.new`, discarding history entirely. Two bugs compound.

---

## Tier A — Ship as-is (5 models)

### 1. Claude Opus 4.7 (94/100) — most test-disciplined

The benchmark leader by a hair. `LlmClient#reply_to` uses the full real API chain:

```ruby
chat = @client.chat(model:, provider:)
chat.with_instructions(@system_prompt)
previous_messages.each { |msg| chat.add_message({role: msg.role.to_sym, content: msg.content}) }
response = chat.ask(user_message)
response.content
```

Textbook correct. The `FakeChat` test double matches every real signature (`with_instructions`, `add_message(attrs)`, `ask`). Tests verify history replay, error wrapping, model/provider override, and system prompt application. Session cookie persistence via `to_a`/`from_session` round-trip is multi-worker safe. Error handling: `rescue RubyLLM::Error + StandardError` → user-friendly truncated bubble.

**Only significant deduction**: Dockerfile `ARG RUBY_VERSION=4.0.2` placeholder (Rails 8.1 generator default that no model caught).

**Killer strength**: test suite uses exact real-API signatures. **Killer weakness**: fake Ruby 4.0.2 in Dockerfile (shared with every other model in the benchmark — it's a generator artifact).

### 1. GPT 5.4 xHigh (Codex CLI) (94/100) — most production-polish, most expensive

Ties Opus 4.7 on score. Uses `RubyLLM.chat(model:, provider: :openrouter, assume_model_exists: true)` + `with_instructions` + `add_message(role:, content:)` + `chat.ask` + `response.content`. Textbook plus provider pinning and registry-skip.

The only model with:
- **Explicit API-key preflight** (`ensure_api_key!` raises `MissingConfigurationError`)
- **Differentiated HTTP status codes**: 503 for config errors, 502 for runtime errors
- **Rails cache persistence with TTL + message cap** (24 msgs × 12h expiry)
- **Dedicated form object** (`PromptSubmission`) separate from domain model (`ChatMessage`)

10 test files including view-partial render tests. `FakeChat`/`FakeClient` match real signatures.

**Killer strength**: only model with differentiated 503/502 for config vs runtime. **Killer weakness**: 7.6M total tokens → ~$16/run, roughly 15× the cost of Opus for essentially tied output quality. Hard to justify unless you can't iterate on the first run.

### 3. Kimi K2.6 (84/100) — best Chinese-model output

The standout of the non-Anthropic/non-OpenAI cohort. `RubyLLM.chat` + `with_instructions(SYSTEM_INSTRUCTION)` + `chat.add_message(role:, content:)` + `chat.ask` + `response.content` — all real API.

- **Only Chinese model that combines**: real LLM-path tests (`FakeChat` with correct signatures) + error-path rescue (`rescue RubyLLM::Error` with flash via turbo_stream) + session-cookie persistence with `MAX_MESSAGES = 50` cap.
- Full Gemfile: ruby_llm, turbo, stimulus, tailwindcss, brakeman, bundler-audit, rubocop-rails, simplecov, capybara.
- Session cookie survives restart and is multi-worker safe.

**Only meaningful deduction**: full history replay each turn (wastes tokens vs persistent-instance pattern), and fake Ruby 4.0.2 Dockerfile.

At ~$0.30/run, Kimi K2.6 is the cheapest Tier A model — 3-50× cheaper than the top 2.

### 4. Gemini 3.1 Pro (82/100) — only model with correct Dockerfile Ruby version

Previously misclassified as Tier 3 for "invented `Chat.new` + `add_message`" — both are real API.

- `RubyLLM::Chat.new(model:, provider:, assume_model_exists:)` — real constructor
- `chat.add_message(role:, content:)` — valid positional hash form
- `chat.ask` + `response.content` — correct
- **Only model with valid Ruby 3.4.1 in the Dockerfile** (not the fake 4.0.2 placeholder every other model shipped)
- Real Turbo Streams (not fetch+innerHTML): `remove empty-state → append user + assistant → replace form`
- Rails.cache-backed session persistence with 2h expiry
- FakeChat mocks match real API shape + error path tested

**Killer weakness**: uses stale model string `claude-3.7-sonnet` instead of current Sonnet 4.x. One-character fix.

### 5. Claude Opus 4.6 (80/100) — thinner than 4.7 but clean

Correct RubyLLM usage (`RubyLLM.chat` + `chat.ask` + `response.content`). History replay via `service.chat.messages << RubyLLM::Message.new(...)` — works because `Chat#messages` is `attr_reader` on an Array, but reaches into internal state (Demeter violation).

**Biggest weakness**: no rescue around `chat_service.ask` in the controller. A transient OpenRouter 5xx produces a 500 page with stack trace. This is the difference between 4.6 (Tier A low) and 4.7 (Tier A high).

---

## Tier B — 1-2 hours to ship (7 models)

### 6. Claude Sonnet 4.6 (75/100) — ambitious scope, subtle bug

Most feature-rich UI of the benchmark (multi-conversation sidebar with per-chat titles). Best controller separation (ChatsController + MessagesController). Mocha-based tests.

**Killer weakness**: `LlmChatService#call` has a silent control-flow bug — only calls `ask` if the last history message is a user message, returns `""` otherwise. The test at `llm_chat_service_test.rb:32-50` rubber-stamps this bug (passes against the broken path). Also: entire conversation graph stored in 4KB session cookie → overflows after ~10 turns.

### 6. DeepSeek V4 Flash (75/100) — cheapest viable option

~$0.01/run (!). `RubyLLM.chat(model:, provider:)` + `add_message(role:, content:)` + `ask` + `.content` — real API throughout. Session-replay multi-turn via `session[:messages]`. WebMock tests on the actual OpenRouter HTTP endpoint — genuine exercise of the LLM path.

**Killer weakness**: model slug `"claude-sonnet-4"` missing `anthropic/` prefix — will 404 against OpenRouter at runtime. One-character fix, but fatal as-is. Also: no rescue around `chat.ask`, 4KB cookie limit on long chats.

### 8. Qwen 3.6 Plus (68/100) — cleanest open-model RubyLLM integration

Real RubyLLM usage with service-layer separation. Stimulus controller is well-built (escapeHtml, loading state, auto-scroll). Partials decomposed cleanly.

**Biggest weaknesses**: tests make *real* network calls (no WebMock), history is client-side JS only (lost on refresh), uses `fetch` + `innerHTML` instead of Turbo Streams (no `turbo-rails` gem).

### 9. DeepSeek V4 Pro (66/100) — Tier 1 code, Tier 3 deliverables

Previously ranked higher based on code quality alone. Re-audited:

**Clean RubyLLM usage**: `@chat = RubyLLM.chat; @chat.ask(content); result.content` — persistent Chat instance lets RubyLLM manage history internally (same pattern as MiMo). Tests use WebMock on real OpenRouter URL.

**But deliverables are broken**:
- README is the stock Rails "This README would normally document..." template (**not** customized)
- **No `docker-compose.yml`** — prompt explicitly required it
- Fake `RUBY_VERSION=4.0.2` in Dockerfile

Run DNF'd because DeepSeek's thinking mode requires the client to echo `reasoning_content` back and opencode strips it. `reasoning: false` in opencode config didn't prevent DeepSeek from emitting thinking tokens server-side. The code written before the harness crashed is Tier 1 quality, but the deliverables are demo-level.

### 9. Kimi K2.5 (66/100) — reclassified up from Tier 3

Previously ranked as Tier 3 for "inventing `chat.add_message()` + `complete()`". **Both are real public methods** in RubyLLM 1.14.1 — the previous audit was wrong.

Uses `RubyLLM.chat(model:)` + `client.add_message(role:, content:)` + `client.complete(&block)` — valid API chain. Also attempts true server-push streaming via `Turbo::StreamsChannel.broadcast_append_to`. 37 test methods (most thorough count in the benchmark).

**Killer weakness**: none of the 37 tests actually mock RubyLLM — they test PORO CRUD and `respond_to?`, not the gem interaction. Also uses class-var storage (`Chat.storage = @storage ||= {}`) — worse than Singleton because it's not mutex-protected.

### 11. Xiaomi MiMo V2.5 Pro (64/100) — cleanest multi-turn idiom

Uses `RubyLLM::Chat.new(model:, provider:)` + `@llm_chat.ask(content, &)` + `response.content`. Persistent `@llm_chat` instance means RubyLLM tracks history internally — the cleanest multi-turn pattern in the entire benchmark, cleaner than explicit history replay.

**But**:
- Tests never exercise the LLM path (only blank-guard + constants assertions)
- No error handling around `@chat.ask` — any API hiccup = 500 page
- `ChatStore` Singleton is process-local (dies on Puma restart, not shared across workers)
- No system prompt via `with_instructions`

~$0.14/run and 11 minutes makes this the fastest viable non-Anthropic option, but it needs ~2 engineer-hours of patching (add `rescue RubyLLM::Error`, swap Singleton for `Rails.cache`, add FakeChat mocks, add system prompt) to reach production quality.

### 12. GLM 5 (61/100) — correct API, stateless design

`RubyLLM.chat(model: "anthropic/claude-sonnet-4")` + `chat.ask` + `response.content` — correct. Mocha stubs match real API shape. Only one happy-path test, no error-path coverage.

**Killer weakness**: **zero multi-turn state** — every POST creates a fresh `RubyLLM.chat` with no history. The "chat app" is a stateless echo service. User asks "what did I just say?" → model replies "I don't know."

---

## Tier C — major rework needed (5 models)

### 13. Step 3.5 Flash (53/100)

Bypasses `ruby_llm` entirely using raw `Net::HTTP` to OpenRouter. The HTTP implementation itself is competent (timeouts, JSON parse errors, missing-key preflight all rescued with user-visible fallbacks). Session-backed multi-turn works. Best error handling of any model.

**But**: non-compliant with the prompt requirement (missing `ruby_llm` gem). Also: the Stimulus `afterSubmit` flow never renders the user's message into `#messages` — only the assistant reply appears, so the UI is silently broken.

### 14. Qwen 3.5 35B (52/100) — local model

Real `RubyLLM.chat` + `chat.ask` + `chat.messages.last.content` — correct API. No service layer (logic in controller). No multi-turn (fresh `RubyLLM.chat` per request).

**Killer weakness**: `test/models/ruby_llm_service_test.rb:14-22` wraps the real call in `rescue => e; assert true` — tests pass even if RubyLLM is completely broken.

### 15. GLM 4.7 Flash bf16 (49/100) — local model, near-miss

**Most RubyLLM-literate local model** of the benchmark — correctly uses the fluent chain `.with_model().with_temperature().with_params().with_instructions().complete(&block)`, all real API per gem source.

**Fatal bug**: `gem "ruby_llm"` is placed in `group :development, :test` with `require: false` — won't load in production. App would crash on boot with `NameError`. Also uses class-var `Message.all` storage (process-local).

### 16. GLM 5.1 / Z.ai (43/100) — hallucinated fluent DSL

`RubyLLM.chat(model:, provider:)` is correct, but history is replayed via hallucinated `c.user(msg)` / `c.assistant(msg)` fluent DSL — these methods do not exist in RubyLLM. Confirmed via grep of the gem source.

Compounded bug: every HTTP request constructs a brand-new `ChatSession.new` that discards history — so the hallucinated DSL calls are rarely entered in practice because there's never any history to replay. Two bugs mask each other.

Stimulus controller uses `fetch` + manual `innerHTML` for streaming — SSE-based but not Turbo Streams.

### 17. DeepSeek V3.2 (40/100)

Uses `RubyLLM::Client.new` + `client.chat(messages: [...])` — **both hallucinated**. Treats response as raw OpenAI JSON via `result.dig("choices", 0, "message", "content")`. Tests mock `RubyLLM::Client.any_instance` — mocking a class that doesn't exist. The entire LLM integration is fictional.

**Redeeming qualities**: best error-rescue discipline of any Tier 3 model (try/rescue/log/user-message), real docker-compose, substantive 265-line README.

---

## Tier D — throw away (5 models)

### 18. MiniMax M2.7 (38/100)

Hallucinated `RubyLLM.chat(model:, messages: [...])` batch signature — crashes on first call (`ArgumentError: unknown keyword: messages`). Best architectural decomposition of any Tier D model (service + form object + POROs + partials), wrapped around a corpse.

Tests mock the hallucinated API so they pass green against a bug.

### 19. Qwen 3.5 122B (34/100) — local model

Doesn't use `ruby_llm` at all. Uses `Openrouter::Client.new(api_key: @api_key)` — wrong casing for the real `OpenRouter::Client` (exists in `openrouter` gem but requires a configuration object, not a bare `api_key:` kwarg). Plus calls `client.chat(model:, messages:)` — real gem method is `completion`, not `chat`.

### 20. Qwen 3 Coder Next (29/100) — local model

Invented `RubyLLM::Client.new(api_key:, model:)` + `client.chat(messages: [...])` + OpenAI-shaped `response.choices.first.message.content` — pure hallucination. Also commits a placeholder `.env` file to the repo.

### 21. Grok 4.20 (22/100)

Bypasses RubyLLM with `ruby-openai`, but the gem is in `:development, :test` group with `require: false` — production `NameError` on first request. Gemfile missing turbo-rails, stimulus-rails, bundle-audit.

Stimulus controller JavaScript is **uncompilable** (`class ChatFormController < StimulusController` — uses Ruby's `<` inheritance syntax in JS, `StimulusController` never imported). Uses CDN Tailwind script tag inside the layout (CSP risk).

At ~$0.60/run, Grok is the most expensive Tier D model.

### 22. GPT OSS 20B (8/100) — local model

Benchmark low. Stock Rails README template (no customization), nested `app/app/` directory (violates "stay in workspace root" rule), **no tests folder at all**, no docker-compose, Gemfile has `gem "tailwindcss"` (CLI gem, not the Rails binding) with brakeman commented out.

Invented `RubyLLM::Client.new(provider:, api_key:)` + `client.chat(content:, model:)` + `response.output_text`. Zero rescue blocks, zero persistence, zero Stimulus controllers.

20B local models on llama.cpp can't reliably follow long agentic instructions.

---

## Cross-Cutting Findings

### 1. The Ruby 4.0.2 placeholder is benchmark-universal

**Every single model** (cloud and local, Tier A through D) ships a Dockerfile with `ARG RUBY_VERSION=4.0.2` or `FROM ruby:4.0.2-slim`. Ruby 4.0.2 doesn't exist (current stable is 3.4.x). It's the Rails 8.1 generator's default — every model ran `rails new` and none of them corrected the generated placeholder. This is a -3 deduction across the board and evidence that models don't verify the scaffolding they inherit.

### 2. Test coverage measures nothing without mock-fidelity

Kimi K2.5 wrote 37 tests (most in the benchmark) but none of them mock RubyLLM. They test PORO CRUD and `respond_to?`. A test suite that doesn't exercise the LLM code path cannot catch bugs in that path, no matter how many test methods you count.

Gemini 3.1 Pro's test suite is smaller (11 tests) but uses a correctly-signatured `FakeChat` that exercises real API paths including error handling. Gemini scored higher on test quality despite fewer tests.

### 3. RubyLLM idiomatic usage varies wildly

Models use three different legitimate multi-turn patterns:
- **Persistent instance** (MiMo, DeepSeek V4 Pro): create `Chat` once, call `.ask()` repeatedly. RubyLLM tracks history internally. Cleanest, but persistence is fragile (process-local objects).
- **Explicit history replay** (Opus 4.7/4.6, Sonnet 4.6, Kimi K2.6, Gemini, DeepSeek V4 Flash): rebuild `Chat`, call `.add_message()` per historic message, then `.ask()`. More code but persistence-friendly (store messages in cookie/cache, reconstruct Chat per request).
- **Batch single-shot** (GLM 5 — intentional one-shot, not multi-turn): just `RubyLLM.chat` + `ask` with no history. Fine for stateless echo services, not a chat app.

### 4. Harness compatibility matters as much as model capability

DeepSeek V4 Pro has Tier 1 code but can't complete the run because opencode doesn't handle DeepSeek's thinking-mode `reasoning_content` echo requirement. GPT 5.4 couldn't run via OpenRouter (tool calling not exposed) — Codex CLI was required. Gemma 4 can't run via local llama.cpp due to parser bugs, but works via Ollama Cloud up to ~20K tokens.

A model that runs correctly is more valuable than a model with nominally better code that can't be exercised.

### 5. Most cost-efficient picks

- **Under $0.05/run**: DeepSeek V4 Flash (Tier B, ~$0.01), Step 3.5 Flash (Tier C, ~$0.02)
- **Under $0.50/run that actually work**: Kimi K2.6 (Tier A, ~$0.30), Gemini 3.1 Pro (Tier A, ~$0.40), MiMo V2.5 Pro (Tier B, ~$0.14)
- **Premium**: Opus 4.7 (Tier A, ~$1.10), GPT 5.4 xHigh (Tier A, ~$16)

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
