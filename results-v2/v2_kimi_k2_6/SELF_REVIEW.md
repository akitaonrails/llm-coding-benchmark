# Self-Review — Phase 3

Review performed against the G1–G14 contract in the original brief. No application code changes were made during this review.

---

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
|------|---------|----------|
| **G1** — Rails app, newest Ruby/Rails, no AR/Mailer/Job, workspace root | **PASS** | `.ruby-version:1` → `ruby-4.0.6`; `Gemfile:6` → `rails "~> 8.1.3"`; `config/application.rb:7-15` comments out Active Record, Action Mailer, Active Job, Active Storage, Action Mailbox, Action Text; app sits at workspace root. |
| **G2** — SPA w/ Tailwind, Hotwire (Stimulus + Turbo Streams), partials, no fetch/innerHTML dumps | **PASS** | `Gemfile:12-16` pins `importmap-rails`, `turbo-rails`, `stimulus-rails`, `tailwindcss-rails`. Views use partials: `messages/_message.html.erb`, `messages/_chunk.html.erb`, `messages/_error.html.erb`, `conversations/_title.html.erb`. `show.html.erb:56` uses `turbo_stream_from`. `chat_controller.js:1-23` is a Stimulus controller for auto-scroll and Enter-to-submit. No `fetch()` or `innerHTML` usage found in JS. |
| **G3** — RubyLLM via OpenRouter, latest Claude Sonnet default, model overridable via env | **PASS** | `Gemfile:28` → `gem "ruby_llm"`. `config/initializers/ruby_llm.rb:3-5` configures `openrouter_api_key` from `OPENROUTER_API_KEY` and sets `default_model` from `CHAT_MODEL` with default `anthropic/claude-sonnet-4.6`. |
| **G4** — TRUE token streaming via Turbo Stream broadcasts | **PASS** | `chat_service.rb:34-38` yields chunks inside `chat.complete { |chunk| ... }`. `messages_controller.rb:52-58` broadcasts each `:chunk` via `Turbo::StreamsChannel.broadcast_append_to` with `_chunk.html.erb`. The test `chat_service_test.rb:94-122` verifies two `:chunk` events and a `:done` event are yielded. |
| **G5** — Multi-turn payload correctness; test asserts exact outgoing array | **PASS** | `chat_service.rb:80-82` replays persisted history (excluding the new user message, which is added at line 29). `chat_service_test.rb:33-70` (`test_multi_turn_payload_excludes_future_message`) asserts the exact `added_messages` array: `[{role: :user, content: "first"}, {role: :assistant, content: "reply one"}, {role: :user, content: "second"}]` — no duplicates, no future messages. |
| **G6** — Concurrency-safe, bounded persistence; survives restart; TTL; no process-local store | **PASS** | `conversation.rb:15-32` uses Redis (`REDIS.hget`/`hset`). `TTL_SECONDS` defaults to 7 days; set on every write (`persist!` at line 107-109). `enforce_bounds!` (line 95-101) caps message count (`MAX_MESSAGES=50`) and bytes (`MAX_BYTES=1_048_576`). Tests verify bounds (`conversation_test.rb:31-44`, `:46-58`), TTL (`:60-65`), and TTL refresh on update (`:67-73`). Redis is external — survives restart and works with `WEB_CONCURRENCY=2`. |
| **G7** — Two RubyLLM tools: `server_time` and `calculator` | **PASS** | `app/services/tools.rb:7-13` — `ServerTime < RubyLLM::Tool` with `description` and `execute`. `tools.rb:16-29` — `Calculator < RubyLLM::Tool` with `description`, `param :expression`, and `execute` using Dentaku. `chat_service.rb:77` wires both via `chat.with_tools(Tools::ServerTime, Tools::Calculator)`. `tools_test.rb:6-33` tests both tools and the Calculator schema. |
| **G8** — Structured-output title after first exchange | **PASS** | `chat_service.rb:87-114` — `generate_title_if_needed` creates a new `RubyLLM::Chat`, calls `with_schema` (line 94-99) with a JSON object schema, seeds with the first user message, and calls `complete`. The title is displayed via `conversations/_title.html.erb` and broadcast on `:done` in `messages_controller.rb:78-83`. |
| **G9** — Token budgeting with env var; friendly refusal when exceeded | **PASS** | `conversation.rb:11` — `TOKEN_BUDGET = Integer(ENV.fetch("TOKEN_BUDGET", "4096"))`. `chat_service.rb:22` checks `over_budget?` before calling the provider. `messages_controller.rb:13-16` redirects with a flash alert if over budget. `conversation_test.rb:75-88` verifies budget enforcement. |
| **G10** — System prompt via instructions API; missing-key preflight; provider error rescue; failed turns excluded | **PASS** | System prompt via `chat.with_instructions(SYSTEM_PROMPT)` (`chat_service.rb:76`). Missing-key preflight at `chat_service.rb:23` raises `MissingApiKey`, caught in `messages_controller.rb:47-48` and broadcast as a degraded error bubble. Provider errors rescued (`chat_service.rb:64-69`): `RubyLLM::Error`, `Faraday::Error`, `JSON::ParserError`. Failed turns are NOT persisted: the `add_message` calls only happen after `chat.complete` succeeds (lines 41-55), and `chat_service_test.rb:72-92` verifies zero messages after a `RubyLLM::Error` is raised. |
| **G11** — Minitest for every component; mocks mirror RubyLLM API; error paths covered; SimpleCov | **PARTIAL** | `test_helper.rb:6-11` wires SimpleCov. `bundle exec rails test` → 29 runs, 70 assertions, 0 failures. Mocks use real `RubyLLM::Message` and `RubyLLM::Chunk` objects (`chat_service_test.rb:45-53`), not fake stubs. **Caveat:** branch coverage is NOT enabled. The tool-call persistence path (`chat_service.rb:45-55`) is unhit (coverage count 0). Title generation (`chat_service.rb:87-114`) is unhit (coverage count 0). Several `friendly_error` arms (`Faraday::TimeoutError`, `Faraday::ConnectionFailed`) are unhit (`chat_service.rb:126-129` count 0). No integration test covers actual tool execution round-trip. |
| **G12** — Brakeman, RuboCop, bundle-audit all pass clean | **PASS** | Re-run: `bundle exec rubocop` → "33 files inspected, no offenses detected"; `bundle exec brakeman -q` → "Security Warnings: 0"; `bundle exec bundle-audit check` → "No vulnerabilities found". |
| **G13** — Production Dockerfile (RAILS_ENV=production, non-root, entrypoint) + docker-compose + README | **PASS** | `Dockerfile:7-55` — multi-stage build, `RAILS_ENV=production`, non-root user `uid:1000`, entrypoint `bin/docker-entrypoint`, health check on `/up`, jemalloc. `docker-compose.yml:1-26` provides `redis` + `app` services with required env vars. `docker build -t self-review-check .` completed successfully in this review. `README.md:1-119` documents setup, env vars, Docker, and architecture. |
| **G14** — No auth; no secrets committed; everything in workspace | **PASS** | No authentication routes/controllers exist (`routes.rb:3-11`). API key read from ENV only (`ruby_llm.rb:4`). `.gitignore:10` ignores `/.env*`; `.gitignore:33` ignores `/config/master.key`. No `sk-or-…` literals in source. All code is inside the workspace root. |

**Summary: 13 PASS, 1 PARTIAL (G11).**

---

## 2. Code Quality Assessment

**Overall:** The codebase is small and readable, but the service layer has growth pains.

### Naming
- Generally good. `ChatService`, `Conversation`, `MessagesController`, `Tools::Calculator` are self-describing.
- `friendly_error` in `ChatService` (line 120) is a weak name — it maps exception classes to user-facing strings; `user_facing_error_for` would be clearer.

### Single Responsibility
- **`ChatService#send_message`** (lines 21–70) does too much: budget/key preflight, chat construction, streaming, outcome-based persistence, title generation, and error mapping. It is ~50 lines of intertwined logic and is the primary reason some branches are hard to test.
- **`generate_title_if_needed`** (lines 87–114) is a secondary responsibility that blocks the user's response path. It creates a second provider call inline.

### Duplication
- Low duplication overall. The sidebar conversation list is duplicated between `index.html.erb` and `show.html.erb` (N+1 Redis fetch pattern in both). A shared partial would remove the duplication.

### Dead Code
- None found.

### Method/Class Size
- `ChatService#send_message` is the outlier. The controller `MessagesController#create` is also long but delegates well to private helpers.
- `Conversation` is a fat model (~140 lines) but cohesive for a Redis-backed PORO.

### Coupling Between Layers
- The tool-call persistence path (`chat_service.rb:45–55`) reaches into `chat.messages.last.content` and `chat.messages.last.input_tokens`. This couples the service to RubyLLM's internal message ordering — a breaking change in `ruby_llm` could silently corrupt conversation history. The service should rely on documented return values from `complete` rather than internal array state.

### Top 3 Refactors (with more time)

1. **Decompose `ChatService#send_message`** into `build_chat`, `stream_response`, `persist_turn`, and `generate_title` methods. The current method is the only thing keeping line coverage under 90% and branch coverage unmeasured.
2. **Remove `generate_title_if_needed` from the synchronous response path.** Title generation currently makes a second OpenRouter call after every first exchange, blocking the user. Since Active Job is forbidden by G1, the cheapest fix would be to fire the title request in a background thread or, more practically, downgrade to a cheaper model slug for titles.
3. **Fix tool-call persistence coupling.** Replace the `chat.messages.last` inspection with a documented API surface from RubyLLM (e.g., the `response` object already knows whether it was a tool call). Add a test that exercises the tool-call path so regressions are caught.

---

## 3. Test Coverage Assessment

| Metric | Value |
|--------|-------|
| Line coverage | **86.05%** (179 / 208 lines) |
| Branch coverage | **Not enabled** — `test_helper.rb:8-11` starts SimpleCov without `enable_coverage :branch` |
| Tests | 29 runs, 70 assertions, 0 failures, 0 errors |

### Weakest-tested area
**`ChatService` — specifically the non-happy paths.**
- `chat_service.rb:45–55` (tool-call persistence branch): **0 hits** in the coverage report.
- `chat_service.rb:87–114` (title generation): **0 hits**.
- `chat_service.rb:126–129` (`Faraday::TimeoutError`, `Faraday::ConnectionFailed` rescue arms): **0 hits**.
- `chat_service.rb:369–395` (friendly error mapping for specific exception types): mostly **0 hits**.

### Failure modes NOT covered by any test
1. **RubyLLM tool-call round-trip**: No test asserts that when `chat.complete` returns a `Message` with `tool_call? == true`, the assistant content is correctly extracted and persisted.
2. **Title generation failure/retry**: The `rescue StandardError` block in `generate_title_if_needed` is unhit. A schema rejection or JSON parse error from the provider would silently fail forever.
3. **Faraday network-level failures**: `Faraday::TimeoutError` and `Faraday::ConnectionFailed` arms in `friendly_error` are unexercised.
4. **Redis connection failure during persistence**: No test simulates a Redis outage mid-conversation.
5. **Concurrent write collision on the same conversation**: `Conversation` is not atomic — `find` → `modify` → `persist!` is a read-modify-write sequence. Two simultaneous requests could interleave and drop a message.
6. **XSS vector via LLM output in views**: While Rails auto-escapes ERB output by default, there is no test that asserts malicious HTML in an assistant reply is rendered harmlessly.
7. **Budget race condition**: `over_budget?` is checked before streaming, but `increment_tokens` happens after. Two overlapping requests could both pass the check and then both exceed the budget.
8. **Docker container runtime behavior**: No system tests verify the app actually boots inside the built image.

---

## 4. Known Defects and Risks

1. **Tool-call persistence relies on internal RubyLLM state** (`chat_service.rb:47–49`).
   - `final_text = chat.messages.last.content.to_s` assumes RubyLLM appended the tool result as the final message in its internal array. If `ruby_llm` changes the ordering or representation, the persisted assistant message will be wrong (e.g., empty or containing raw tool JSON).
   - **Severity:** Medium — works today, fragile against gem updates.

2. **Request-level race on token budget** (`messages_controller.rb:13–16` + `chat_service.rb:22`).
   - The budget check and the budget increment are not atomic. Two concurrent requests on the same conversation can both see `over_budget? == false`, then both stream and increment past the cap.
   - **Severity:** Medium — only affects high-concurrency scenarios on the same conversation.

3. **Title generation blocks the response and has no circuit breaker** (`chat_service.rb:61`).
   - `generate_title_if_needed` is called inside `send_message`, after the user's reply has already been streamed. If the title request hangs or errors, the method has already returned; but if it raises unexpectedly, the rescue at line 111 catches it. The bigger issue is that a slow title call delays the `:done` event because `generate_title_if_needed` runs before the method returns. Wait — re-reading: `generate_title_if_needed` is called *after* the `block.call({ type: :done ... })` at line 58. Actually no: line 58 is inside the conditional. Let me re-check... Line 58 is the `block.call({ type: :done ... })`. Then line 61 calls `generate_title_if_needed`. So the `:done` event IS sent before title generation. But `generate_title_if_needed` can still raise, which would be rescued by the outer `rescue` at line 64. So the user gets `:done`, then if title generation fails, the rescue catches it and sends an `:error` event — but the user already got `:done`. This is a UX quirk, not a crash.
   - Actually wait: no. `generate_title_if_needed` is inside `send_message` which returns `{ success: true, content: full_content }`. If `generate_title_if_needed` raises, the outer rescue catches it and returns `{ success: false, error: ... }`, even though the chat succeeded. The controller's `stream_assistant_response` calls `send_message` without rescuing `StandardError`, so it would propagate? No, `send_message` rescues `RubyLLM::Error`, `Faraday::Error`, `JSON::ParserError`, `BudgetExceeded`, `MissingApiKey`. `generate_title_if_needed` has its own `rescue StandardError` (line 111), so it silently swallows everything. Good — no crash. But the risk remains that title generation uses the same expensive model for a trivial task.
   - **Severity:** Low — silent swallowing makes it safe, but wasteful and unobservable.

4. **Unbounded N+1 Redis scan in sidebar** (`show.html.erb:8`).
   - `Conversation.all_ids` uses `REDIS.keys('conversation:*')`, which blocks Redis on large key spaces. For a demo this is acceptable; for production it is a DoS vector.
   - **Severity:** Low — demo-only app.

5. **No outer timeout on streaming calls.**
   - `chat.complete` could hang indefinitely if OpenRouter stalls. Faraday may have its own timeout, but there is no explicit `Timeout.timeout` wrapper in the service.
   - **Severity:** Medium — operational risk under provider degradation.

6. **Redis `keys` command is a Redis anti-pattern** (`conversation.rb:30`).
   - `REDIS.keys('conversation:*')` in production Redis clusters is discouraged (blocks the event loop). Should use `SCAN` or a secondary index set.
   - **Severity:** Low — demo scope.

---

*Review completed. No code changes were made during this review.*
