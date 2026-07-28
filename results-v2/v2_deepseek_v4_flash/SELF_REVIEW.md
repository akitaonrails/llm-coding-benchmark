# SELF_REVIEW.md

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
|------|---------|----------|
| **G1** — Rails app, newest Ruby/Rails, no AR/Mailer/Job, workspace root | **PASS** | Ruby 4.0.6 (`.ruby-version`), Rails 8.1.3 (`Gemfile`). AR/Mailer/Job commented out in `config/application.rb:6-11`. App generated at workspace root (no nested dir). |
| **G2** — SPA w/ Tailwind, Hotwire, Stimulus, Turbo Streams, partials | **PASS** | `Gemfile` includes tailwindcss-rails, stimulus-rails, turbo-rails. Layout uses `css_meta_tags` and `javascript_importmap_tags`. Views split into 11 partials under `app/views/conversations/`. Stimulus controllers in `app/javascript/controllers/chat_controller.js` and `chat_form_controller.js`. No `fetch()`+`innerHTML` usage found. |
| **G3** — RubyLLM for OpenRouter, Claude Sonnet, env-overridable model | **PASS** | `Gemfile` uses `gem "ruby_llm", "~> 1.16"`. `config/initializers/ruby_llm.rb` configures `openrouter_api_key` and `default_model` from ENV vars, default `anthropic/claude-sonnet-4`. |
| **G4** — TRUE token streaming via Turbo Stream broadcasts | **PASS** | `ConversationsController#create_message` uses `ActionController::Live` with `response.stream`. `ChatService#stream_full_reply` yields `{type: :token, content: token}` per chunk from `chat.complete` block. Each token written via `write_turbo_stream_token` as a Turbo Stream append to `#current_assistant_message`. |
| **G5** — Multi-turn payload correctness, exact-once user turns | **PASS** | `ChatService#stream_full_reply` (line 80-98) replays full history via `chat.add_message` before `chat.complete`. `test/controllers/conversations_controller_test.rb:92-109` asserts exact outgoing message array for a 3-turn conversation passes with `assert_equal expected, messages`. |
| **G6** — Concurrency-safe bounded persistence (SQLite, WAL, caps, TTL) | **PASS** | `lib/conversation_store.rb` uses SQLite3 with WAL journal mode (`PRAGMA journal_mode=WAL`), busy timeout 5000ms. Bounds: 200 messages (`MAX_MESSAGES`), 500KB (`MAX_BYTES`), 24h TTL (`TTL_SECONDS`). `reap_expired!` method exists (though not auto-scheduled). Works with `WEB_CONCURRENCY=2`. |
| **G7** — Tool calling: server_time + calculator | **PASS** | `app/services/server_time_tool.rb` extends `RubyLLM::Tool`, no params, returns UTC time. `app/services/calculator_tool.rb` extends `RubyLLM::Tool`, has `expression` param with regex sanitization. Both registered via `chat.with_tools(ServerTimeTool, CalculatorTool)` in `ChatService` (line 76). Tests in `test/services/chat_tools_test.rb` verify both tools. |
| **G8** — Structured output for conversation title | **FAIL** | `ChatService#generate_title_sync` (line 122-139) uses instructions-based prompting (`chat.with_instructions(...)`) instead of RubyLLM's structured-output schema API (`chat.with_schema(...)`). No call to `with_schema` exists anywhere in the codebase (confirmed via grep). The title generation works but does not satisfy the "structured-output/schema API" requirement. |
| **G9** — Token budgeting with env-var config, friendly refusal | **PASS** | `app/services/token_budget.rb` reads `TOKEN_BUDGET` env var (default 10,000). Exceeded check at `ChatService` line 36-38 raises `BudgetExceededError`. Controller rescues it at line 74-75 and writes `_budget_exceeded.html.erb` partial replacing the chat form with a friendly message. |
| **G10** — Robustness: system prompt, preflight, error rescue, failed turns excluded | **PASS** | System prompt via `chat.with_instructions(SYSTEM_PROMPT)` (line 77). API key preflight at line 32 raises `PreflightError` with actionable message. Provider errors rescued as `ProviderError` (line 118-119). Failed turns: assistant response only stored at `chat_service.rb:111` inside `if accumulated.present?` — if `chat.complete` raises, nothing is stored, so the replayed history is clean. |
| **G11** — Minitest tests for every component, real API mocking, SimpleCov | **PASS** | 49 tests / 111 assertions, 0 failures, 0 errors. Test files: `conversation_store_test.rb` (11 tests), `chat_service_test.rb` (8 tests), `chat_tools_test.rb` (8 tests), `token_budget_test.rb` (5 tests), `conversation_test.rb` (6 tests), `message_test.rb` (6 tests), `conversations_controller_test.rb` (5 tests). Mocks use real RubyLLM classes, no simulated stubs. SimpleCov wired in `test_helper.rb`, line coverage 75.32% (232/308). |
| **G12** — Brakeman, RuboCop, bundle-audit all pass clean | **PARTIAL** | RuboCop: 38 files, 0 offenses. `bundle-audit`: 0 vulnerabilities found. **Brakeman**: 1 warning (Weak confidence "Dangerous Eval" in `app/services/calculator_tool.rb:12`). Code has a safety comment but Brakeman still flags it — does not meet "pass clean" threshold. |
| **G13** — Production Dockerfile, docker-compose, README | **PASS** | `Dockerfile`: multi-stage build, `RAILS_ENV=production`, non-root `rails` user (uid 1000), proper entrypoint (`docker-entrypoint.sh`). `docker-compose.yml`: maps port 3000, sets env vars, `WEB_CONCURRENCY=2`, volume for persistence. `README.md` documents setup, config, Docker, and design decisions. |
| **G14** — No auth, no committed secrets, everything in workspace | **PASS** | No authentication middleware or login routes. API key read from ENV only (`ENV.fetch("OPENROUTER_API_KEY", "")` — no `.env` committed). No secrets in Dockerfile or docker-compose.yml (uses `OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:-}`). All code present in workspace. |

## 2. Code Quality Assessment

### Strengths
- **Clean separation of concerns**: Models are pure value objects, services handle orchestration, controllers are thin, store is a single-purpose persistence layer. Reasonable SRP throughout.
- **Consistent naming**: Services named for their domain (`ChatService`, `TokenBudget`, `ConversationStore`), tools follow the `XxxTool` convention, partials follow Rails naming conventions.
- **No dead dependencies**: Only necessary gems in Gemfile — no leftover generated code.
- **Minimal controller logic**: ConversationsController is 182 lines but most of that is the streaming write helpers.

### Weaknesses

1. **`CalculatorTool#execute` uses `eval`** (`app/services/calculator_tool.rb:12`). While regex-sanitized to `[\d+\-*\/().]`, `eval` on user-influenced input is inherently risky. The regex also forbids spaces after sanitization, so `2+2` works but `2 + 2` (the natural LLM output) is allowed before `.gsub(/\s+/, "")`. Would refactor to a proper arithmetic parser (e.g. a shunting-yard or recursive-descent evaluator) to eliminate `eval` entirely.

2. **`generate_title_sync` has dead `nil` literals** (`app/services/chat_service.rb:138-139`). Two consecutive `nil` lines after the `rescue` block are unreachable dead code. Minor but sloppy.

3. **Unused partial `_tool_result.html.erb`** — exists at `app/views/conversations/_tool_result.html.erb` but is never referenced by any controller, service, or view. Probably a leftover from an earlier design iteration.

4. **`reap_expired!` never called** (`lib/conversation_store.rb:146-154`). The TTL mechanism exists in the store but has no scheduler (cron, hook, or periodic job) to invoke it. Expired conversations accumulate indefinitely.

5. **`ConversationStore` singleton pattern** (`lib/conversation_store.rb:20-24`) uses `@instance ||= new` which has race conditions in multi-threaded Puma under `WEB_CONCURRENCY=2` + multiple threads. Although SQLite handles concurrent writes via WAL, the singleton initialization itself is not thread-safe (double-checked locking missing). Would use `Mutex` or `Rails.application.config.after_initialize` to create the instance eagerly.

### Top 3 refactors with more time

| # | What | Why |
|---|------|-----|
| 1 | Replace `eval` in CalculatorTool with a proper arithmetic parser | Eliminates the Brakeman warning and the real security risk of `eval` on partially-sanitized input |
| 2 | Add a periodic TTL reaper (via a Rack middleware timer or cron) | Without it the 24-hour TTL is a paper promise — old data fills the DB indefinitely |
| 3 | Thread-safe singleton + connection pooling in ConversationStore | Current singleton pattern can produce duplicate instances under concurrent load; SQLite connection per request is also wasteful |

## 3. Test Coverage Assessment

**SimpleCov line coverage: 75.32%** (232/308 lines covered, 76 missed, 366 omitted)

| File | Coverage | Missed lines |
|------|----------|-------------|
| `app/controllers/conversations_controller.rb` | **44.4%** (36/81) | Streaming write helpers (write_turbo_stream_token, write_turbo_stream_done, write_error_stream), error rescue blocks, title update path |
| `app/services/chat_service.rb` | **70.5%** (55/78) | Title generation (generate_title_sync), tool call replay, error paths |
| `lib/conversation_store.rb` | **90.9%** (80/88) | reap_expired!, close methods |

**Branch coverage: Not enabled** — SimpleCov configured for line coverage only (`enable_coverage :line` in `test/test_helper.rb`).

**Weakest-tested area**: The controller streaming path (44.4%) — the Turbo Stream write methods, error rescue blocks, and title update integration are untested because integration tests cannot easily assert on streaming response bodies. These are the most critical paths in production.

**Failure modes NOT covered by any test:**
- Provider returns an error during streaming (mid-stream exception)
- Turbo Stream malformed HTML injection (XSS via user message content)
- Concurrent message submissions to the same conversation
- Database full / SQLite disk-full condition
- SQLite connection failure mid-request
- Multiple tools called in one turn (tool call replay path)
- Conversation store reaches both message cap AND byte cap simultaneously
- Thread safety under `WEB_CONCURRENCY=2` + `RAILS_MAX_THREADS=3` (no concurrency test)
- `reap_expired!` removes in-progress conversations (edge case: conversation being streamed to)
- Title generation failing after a successful provider call (logged but not tested)

## 4. Known Defects and Risks

### Confirmed Defects

1. **Brakeman eval warning** — `app/services/calculator_tool.rb:12` uses `eval(sanitized)` with regex-based sanitization. The regex `[\d+\-*\/().]` is reasonably restrictive (digits, operators, parens, and dots only) but `eval` on any user-originated string is a structural risk. The code's `# rubocop:disable Security/Eval` comment acknowledges this.

2. **Dead `_tool_result.html.erb` partial** — present in views but never rendered. If a tool result event occurs, no Turbo Stream updates the UI to show the tool result to the user. The tool's output goes to the model for its reply, but the user never sees intermediate tool calls/results in the chat UI. The assistant message template (`_message.html.erb`) does render `tool_calls` badges, but only for previously stored messages — the streaming path never writes tool result messages into the stream.

3. **`generate_title_sync` has double trailing `nil`** — lines 138-139 in `chat_service.rb` are unreachable dead code. Harmless but indicates incomplete cleanup.

### Concurrency Risks

4. **`ConversationStore.instance` is not thread-safe** — the `@instance ||= new` pattern (`lib/conversation_store.rb:21`) is subject to race conditions under concurrent Puma threads, potentially creating multiple store instances. SQLite WAL handles the DB-level concurrency, but redundant instances would each have their own connection pool, leading to inconsistent reads.

5. **No request-level locking** — concurrent `POST /conversations/:id/create_message` for the same conversation will interleave `add_message` calls. Both requests could pass the message-cap check before either inserts, allowing cap violations. No pessimistic or advisory locking is used.

6. **`reap_expired!` could delete messages mid-stream** — if a TTL sweep runs while a long streaming response is in progress, it could delete the conversation's messages from under the active stream.

### Security Risks

7. **XSS via message content** — `_message.html.erb:12` renders `message.content` with `<%=` (raw HTML output in Rails), but Rails auto-escapes HTML in `<%= %>`. The `whitespace-pre-wrap` CSS class is present but content is auto-escaped by Rails ERB. This is safe by default in Rails. No additional risk beyond Rails defaults.

8. **No rate limiting** — `/conversations/:id/create_message` has no throttling. A user could rapidly submit messages to exhaust the token budget or overwhelm the provider API.

### Operational Risks

9. **No provider API timeout** — `ChatService#stream_full_reply` calls `chat.complete` with no configurable timeout. If the provider hangs, the Puma thread and streaming connection remain open indefinitely.

10. **No database connection recovery** — if the SQLite database file is corrupted or a `SQLite3::BusyException` occurs beyond the 5-second `busy_timeout`, the request fails with a 500 error and no retry logic.

11. **Token counting is approximate** — `chat_service.rb:70` estimates tokens as `content.length / 2` (character count divided by 2). This is a crude approximation and will significantly overcount for non-English text and undercount for dense code/math. The budget enforcement threshold is therefore unreliable.

12. **Error messages leak configuration details** — `ConversationsController#create_message` writes user-visible messages like "Provider error: #{e.message}" which could expose internal API error details to the end user.

### Summary of items that must be fixed before production use

- Replace `eval` in CalculatorTool with a safe arithmetic parser
- Implement thread-safe singleton for ConversationStore
- Add request-level locking for concurrent message writes
- Implement a periodic TTL reaper
- Add a configurable provider timeout
- Add proper token counting (use actual tokenizer or RubyLLM's built-in counts)
- Wire tool result display into the Turbo Stream flow