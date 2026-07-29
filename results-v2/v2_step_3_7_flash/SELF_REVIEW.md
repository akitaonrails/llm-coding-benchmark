# Self-Review — Phase 3

## Project Context

Ruby on Rails 8.1.3.1 chat application with RubyLLM as the LLM client, backed by Redis (via `redis` gem) for persistent conversation state. Uses Turbo Streams + Stimulus for real-time token streaming. No Active Record, no Active Mailer, no Active Job. Minitest suite with SimpleCov; RuboCop, Brakeman, and bundle-audit run via `bin/ci`. Git repo has zero commits at time of review (uncommitted working tree).

---

## 1. Goal Verification Table

| ID  | Verdict   | Evidence |
|-----|-----------|----------|
| G1  | PARTIAL   | Rails 8.1.3.1 used (`Gemfile:10`). `config/application.rb:7-13` excludes AR/ActionMailer/ActionJob. However, many Rails generator default files are present (`app/helpers/application_helper.rb`, `app/assets/`, `public/`, `.rubocop.yml`, `.ruby-version`, `Procfile.dev`, `Rakefile`, `config/initializers/*`) — these are the full generator output, not a minimal custom scaffold. |
| G2  | PASS      | `app/views/conversations/show.html.erb` uses `turbo_stream_from`, 6 partials in `app/views/messages/_*`, Tailwind classes throughout. `app/javascript/controllers/chat_controller.js` is an isolated Stimulus controller (entry point: `app/javascript/application.js:3`). No hand-rolled `fetch()+innerHTML` for message insertion — the streaming path uses `Turbo::StreamsChannel.broadcast_append_to` server-side. |
| G3  | PASS      | `config/initializers/ruby_llm.rb:5-9`: `config.openrouter_api_key = ENV['OPENROUTER_API_KEY']`, `config.default_model = ENV.fetch('LLM_MODEL', 'anthropic/claude-sonnet-4')`. `app/services/llm_service.rb:51-53`: model resolved via `ENV.fetch('LLM_MODEL', ...)` at chat construction. |
| G4  | PASS      | `app/services/llm_service.rb:27-31`: `chat.ask(user_content) do \|chunk\| ... broadcast_callback.call(chunk.content) end`. Callback in `MessagesController#create:46-61` calls `Turbo::StreamsChannel.broadcast_append_to` on every chunk, targeting `"assistant-stream-#{conversation_id}"`. Each broadcast renders `_stream_chunk.html.erb` (one token) appended to the DOM incrementally. |
| G5  | PASS      | `app/services/llm_service.rb:22-23`: `history = @store.messages(@conversation_id)` fetches stored messages (no current prompt). `build_chat` at line 62-69 replays user+assistant turns. `test/services/llm_service_multi_turn_test.rb:22-38` (test `payload correctness`) asserts the exact message array: 4 messages total (system + 3 history turns), each user turn appears exactly once. |
| G6  | PARTIAL   | Persistence: Redis-backed `ConversationStore` (no process-local state), survives restart. Bounds: `MAX_MESSAGES=50` (`store.rb:22`), `MAX_BYTES=500_000` (`store.rb:25`), `TTL_SECONDS=86400` (`store.rb:37-38`). Gap: cap checks read-before-write (`store.rb:18-21` then `store.rb:35`) — the initial `llen` round-trip (lines 18-21) is discarded; the subsequent plain `llen` (line 21) is a non-atomic second call. Under `WEB_CONCURRENCY=2`, two concurrent requests could both pass the `count >= MAX_MESSAGES` check before either rpush. |
| G7  | PASS      | `app/services/llm_service.rb:59`: `chat.with_tools(ServerTimeTool.new, CalculatorTool.new)`. `app/tools/server_time_tool.rb:8-14` returns UTC time. `app/tools/calculator_tool.rb:7-15` evaluates arithmetic safely with character whitelist and a 200-char length cap. |
| G8  PASS      | `app/services/llm_service.rb:74-112`: `check_and_generate_title` fires after the first assistant turn (guard at line 75 checks `title_generated` meta flag, guard at line 78 checks `msgs.size >= 2`). Uses `RubyLLM::Schema` (`app/lib/chat_title_schema.rb:3-8`) with `string :title, max_length: 60`. Title stored via `@store.set_meta` (line 108) and broadcast to the `<h1 id="conversation-title">` element through the `ensure` block in `MessagesController#create:73-82`. |
| G9  PASS      | `app/services/llm_service.rb:4`: `TOKEN_BUDGET = Integer(ENV.fetch('TOKEN_BUDGET', '100_000'))`. Pre-LLM budget gate at line 16: `if current_usage >= TOKEN_BUDGET ... broadcast_error(...) ... return`. `ConversationStore#total_tokens` (store.rb:72-75) sums stored `token_count` per message. |
| G10 | PASS      | System prompt: `build_chat` calls `chat.with_instructions(system_prompt)` at line 58. API key preflight: `ApplicationController#check_api_key` (line 13-17) flashes an alert; duplicated in `MessagesController#create:17-24` with a turbo_stream error broadcast. Provider failure rescue at `llm_service.rb:33-36`: `rescue StandardError => e; broadcast_error(...)`. Failed turns: on provider exception, the method returns at line 35 before calling `@store.store_message` — failed turns are never persisted. |
| G11 | PASS      | 18 tests, 49 assertions, 0 failures (run: `bin/rails test`). Components covered: Tools (`test/tools/tools_test.rb`, 5 tests including unsafe char and division-by-zero error paths), Tokenizer (4 cases including nil), ConversationStore (7 tests covering storage, caps, meta, tokens, existence), LlmService / chat building (multi-turn history payload test), MessagesController (turbo_stream on success and 422 on empty), ConversationsController (initialization and redirect). SimpleCov wired with branch coverage (`test/test_helper.rb:5-11`). RubyLLM API surface is used directly in tests, not fabricated. |
| G12 | FAIL      | `bundle exec bundle-audit check`: **PASS** (no vulnerabilities). `bin/brakeman --quiet --no-progress`: **FAIL** — 1 security warning: `Dangerous Eval` at `app/tools/calculator_tool.rb:11` (`Kernel.eval(expression)`). `bundle exec rubocop app/`: **FAIL** — 6 offenses in application code: `MessagesController#create` (MethodLength 64/50, AbcSize 51.47/25), `ConversationStore#store_message` (AbcSize 26.55/25), `LlmService#process_user_message` (AbcSize 25.50/25), `LlmService#check_and_generate_title` (AbcSize 39.82/25, PerceivedComplexity 12/10). Total app RuboCop offenses: 6, none autocorrected. |
| G13 | PASS      | `Dockerfile:12-89`: multi-stage, `RAILS_ENV=production`, non-root `rails` user (uid 1000), `ENTRYPOINT ["/rails/bin/docker-entrypoint"]`, jemalloc, `CMD ["./bin/rails", "server"]`. `docker-compose.yml`: `redis:7-alpine` service with healthcheck, `app` service with `depends_on` healthcheck guard, `REDIS_URL`, volume mounts. `README.md` exists at workspace root and documents setup. |
| G14 | PASS      | No authentication mechanism anywhere. `.gitignore:11` commits `/.env*` and `/.env`. No `.env` file tracked in repo (verified: `git ls-files` — zero tracked files). Use of `ENV[...]` throughout, never hardcoded secrets in source. |

---

## 2. Code Quality Assessment

### Naming

Mostly clear. `LlmService`, `ConversationStore`, `Tokenizer`, `ServerTimeTool`, `CalculatorTool` are descriptive. Two issues: `ApplicationHelper` (`app/helpers/application_helper.rb`) is an empty module left from generator scaffolding and serves no purpose. `ChatTitleSchema` lives in `lib/` (not `lib/app/lib`) — technically outside Rails autoload convention; it works only because `config/autoload_lib` adds `lib` to eager-load paths.

### Single Responsibility

**`MessagesController#create` (`app/controllers/messages_controller.rb:6-84`)** — 79 lines mixing: input validation, API-key preflight check, user-message persistence, turbo_stream response construction, and a fire-and-forget background thread that handles streaming, error recovery, and title broadcasting. Single largest method in the codebase. The `ensure` block (lines 73-83) also couples lifecycle concern directly into the action rather than a dedicated service.

**`LlmService#process_user_message` (`app/services/llm_service.rb:11-46`)** Handles: budget gate, chat construction, streaming loop, output persistence, title generation, and completion broadcast. The private `check_and_generate_title` (`llm_service.rb:74-112`, 38 lines) is another SRP violation: it embeds the model name, schema instantiation, prompt assembly, raw-result normalization (Hash vs RubyLLM::Schema vs plain string), length truncation, and meta persistence in one method.

**`ConversationStore`** — respects SRP reasonably, but `store_message` mixes cap enforcement and Redis write in one method (lines 12-42).

### Duplication

- The API-key emptiness check `ENV['OPENROUTER_API_KEY'].to_s.strip.empty?` is duplicated verbatim in `ApplicationController#check_api_key:14` and `LlmService#process_user_message:12`. The controller check flashes a notice; the service check broadcasts a turbo-stream error. Both independently check the same env var. A single `LlmaAvailabilityGuard` service would eliminate the duplication.
- The `conversation_id` derivation (`params[:conversation_id].presence || SecureRandom.uuid`) appears in `ApplicationController#conversation_id:20` and `ConversationsController#show:7` and `MessagesController#create:7` — three independent copies.
- The turbo_stream broadcast pattern for `'assistant-messages'` target is repeated three times in `MessagesController#create` (placeholder append, error append in thread rescue, stream-end marker append).

### Dead Code

- `app/helpers/application_helper.rb` — empty module, no helper methods used, no view calls any `helper :application` method.
- `ConversationStore#mark_title_generated` (`app/services/conversation_store.rb:66-70`) is defined and tested (`test/services/conversation_store_test.rb:42-45`) but never called from production code.
- `app/views/messages/_assistant_message.html.erb` — the partial exists and renders an "A" avatar bubble. However, no code path renders it as a complete assistant message after streaming finishes. The streaming path appends individual tokens via `_stream_chunk.html.erb` raw text; the stream-end marker is an invisible `<span>`. The full bubble partial is rendered in no end-to-end path.

### Method/Class Size

- `MessagesController#create`: 79 lines, AbcSize 51.47 (threshold 25)
- `LlmService#check_and_generate_title`: 38 lines, AbcSize 39.82 (threshold 25), PerceivedComplexity 12 (threshold 10)
- `ConversationStore#store_message`: 30 lines, AbcSize 26.55 (threshold 25)
- `LlmService#process_user_message`: 35 lines, AbcSize 25.50 (threshold 25)

### Coupling Between Layers

- `LlmService` calls `Turbo::StreamsChannel.broadcast_append_to` directly (line 119-125), coupling the service layer to the ActionCable/Turbo API. This makes `LlmService` untestable without Rails' full stack and harder to reuse in a non-web context.
- `MessagesController#create` instantiates `ConversationStore` and `LlmService` inline rather than through a factory or dependency injection; the controller is the orchestrator for Redis persistence, background threading, and Turbo broadcasting simultaneously.
- `build_chat` (private in `LlmService`:50-72) reads `system_prompt.md` from disk (filesystem coupling), instantiates two tool classes by name, and mutates `chat.messages` array directly — tightly coupled to RubyLLM internals.

### Top 3 Refactoring Priorities

1. **Split `MessagesController#create` into an operation/service object.** The 79-line action should become: a form handler that persists the user message and renders the turbo_stream response, then delegates to `LlmService#process_user_message` with a callback object that encapsulates all Turbo broadcasts. This eliminates the 45+ lines of thread-bound broadcast code from the controller.

2. **Extract a `ConversationTitleGenerator` from `LlmService#check_and_generate_title`.** The 38-line private method mixes model instantiation, prompt construction, schema usage, result normalization, truncation, and meta persistence. A dedicated class of ~8–10 lines would let `ConversationStore.handle_title(callback)` own the meta lifecycle, making both independently testable without a mock RubyLLM chat.

3. **Make `ConversationStore` cherry-pick atomic. The cap checks (`store.rb:18-22`, `store.rb:24-25`) are read-before-write. Replace the two separate `llen`/`get` calls with a single `multi` transaction that returns `[count, current_size]` atomically, or use a Lua EVALSHA script for `store_message`. The multi-block at lines 17-19 is dead code — it queues the LEN call but discards the result. Lines 34-39 also use multi but each call in the block is also called individually at line 21; real Redis would queue+execute atomically, but the redundant call pattern shows the intent was never cleanly expressed.

---

## 3. Test Coverage Assessment

### SimpleCov Report

| Metric   | Value       |
|----------|-------------|
| Line     | 162 / 210   | **77.14%** |
| Branch   | 20 / 49     | **40.81%** |

Run command: `bin/rails test` → 18 runs, 49 assertions, 0 failures, 0 errors, 0 skips (0.10s).

### Per-File Breakdown

| File | Line % | Branch % |
|------|--------|----------|
| `app/services/llm_service.rb` | **46.7%** | **13.6%** |
| `app/controllers/messages_controller.rb` | **58.6%** | **37.5%** |
| `app/controllers/application_controller.rb` | 81.8% | 50.0% |
| `app/tools/server_time_tool.rb` | 90.0% | 80.0% |
| `app/tools/calculator_tool.rb` | 100% | 75.0% |
| `app/services/conversation_store.rb` | 98.0% | 100% |
| `app/services/tokenizer.rb` | 100% | 100% |

### Weakest-Tested Area

**`app/services/llm_service.rb`** — critical. Only 28 of 60 lines covered, 3 of 22 branches covered.

Untested lines/branches in `llm_service.rb`:
- Line 12: `raise 'Missing OPENROUTER_API_KEY'` branch
- Lines 16-19: `current_usage >= TOKEN_BUDGET` early-return path (both condition and broadcast_error call)
- Lines 26-36: `chat.ask` block, including the `rescue StandardError => e` error path (Inner `next unless chunk.content` branch also unexercised)
- Lines 39-40: assistant message persistence in success path
- Lines 74-112: entire `check_and_generate_title` method — all 5 guard branches (meta flag, message count ≥ 2, last message role, schema instantiation, raw_title normalization) plus the rescue block at line 109-111
- Line 115-116: `current_token_usage` private helper (called by itself via budget gate already counted as unvisited)
- Line 119-125: `broadcast_error` private method

**`app/controllers/messages_controller.rb`** — lines 42-84 (the Thread block) are entirely uncovered. This means: the `LlmService` thread execution path, all provider-error rescue broadcasts, the stream completion callback (`broadcast_callback.call(nil)`), and the `ensure` block that updates the conversation title are untested.

### Failure Modes NOT Covered

1. **`LlmService#process_user_message` — token budget exceeded**: No test calls `process_user_message` with usage ≥ TOKEN_BUDGET. Verifies: friendly broadcast message is sent, no LLM call is made.
2. **`LlmService#process_user_message` — provider raises**: No test simulates `chat.ask` raising `StandardError`. Verifies: `broadcast_error` called with class/message, no assistant message stored.
3. **`LlmService#process_user_message` — missing API key**: `raise 'Missing OPENROUTER_API_KEY'` untested in LlmService unit test (only covered at the controller layer).
4. **`CalculatorTool` — expression > 200 chars**: `raise 'Too complex'` branch (`calculator_tool.rb:8`) never triggered. Test suite has no case with a 201-char expression.
5. **`ServerTimeTool` — `rfc2822` format**: branch `when 'rfc2822'` (`server_time_tool.rb:11`) untested — only `nil` and `'iso8601'` covered.
6. **`ConversationStore#messages` — malformed JSON**: the `JSON.parse(json) rescue nil` path at `conversation_store.rb:51-53` is untested. A corrupted Redis entry silently disappears; no test verifies this.
7. **`ConversationStore#store_message` — non-string `format`**: `ServerTimeTool.execute` rescues `NoMethodError` when `format` is not a String (e.g., a number). Only rescued, not asserted.
8. **`MessagesController#create` — API key missing**: `turbo_stream` error path (lines 18-23) is tested, but only under that one controller; the `LlmService` path for the same condition is not tested.
9. **`ConversationStore` — exactly at cap boundary**: All-cap tests fill to 50 messages then fail on the 51st. The boundary case of 50 succeeding and 51 failing is correct, but there is no test that verifies exactly 50 messages *are* stored and retrievable *after* the 50th store call completes.
10. **`check_and_generate_title` — all guard combinations**: No test verifies that title generation is skipped when `title_generated == true`, or when `msgs.size < 2`, or when the last message is a user turn. All tested at controller/integration level, not at the service level.

### JavaScript Test Coverage

There are **no tests** for `app/javascript/controllers/chat_controller.js`. No `test/javascript/` directory exists. Stimulus controller behavior (form submission, scroll-sentry state, auto-scroll on stream-connected) is unverified.

---

## 4. Known Defects and Risks

### Concurrency / Atomicity

**`ConversationStore` cap checks are a TOCTOU race** (`app/services/conversation_store.rb:17-25`): the method does `@redis.multi { txn.llen(key) }` on line 17 but discards the returned count. On line 21 it calls `@redis.llen(key)` again — a second round-trip. Two concurrent requests can both observe `count < MAX_MESSAGES` before either `rpush` at line 35 executes. The same pattern applies to the byte-size check (lines 24-25 vs lines 34-36). In WEB_CONCURRENCY=2 this window exists.

**`MockRedis#multi` is a faithful no-op** (`test/support/mock_redis.rb:60-62`): `def multi; yield self; end` does not queue commands. Redis writes inside `multi` blocks execute immediately, one at a time — which is why the test "rejects exceeding message cap" passes: each store_message call runs synchronously in the test, not in a cluster. The tests do not surface the race, and they pass for the wrong reason.

### Stimulus Auto-Scroll Bug

`app/javascript/controllers/chat_controller.js:49-51`: `streamConnected()` calls `this.scrollSentry()` and if `this.autoScroll` is true, `scrollToBottom()`. But `this.autoScroll` is computed once in `connect()` (line 7-12) based on `this.listTarget.scrollHeight` at that moment — before any stream chunks have appended. `scrollSentry()` updates `this.autoScroll` only on the list's own scroll event (line 54-57). When new stream chunks arrive and are appended as DOM nodes, `this.scrollSentry` is not called back, so `autoScroll` is never recalculated. If a user scrolled the list up before the stream arrived, auto-scroll will remain true from `connect()` and force-scroll back down even when the user is trying to read earlier content.

DOM mismatch exacerbates this: `chat_controller.js:4` declares `static targets = ["input", "list", "stream"]`, but `app/views/messages/_assistant_placeholder.html.erb:6` sets `id="assistant-stream-#{...}"` manually — it does not carry `data-chat-target="stream"`. So `this.streamTargets` is always empty, and `streamConnected` only fires on Turbo `stream-connected` events on the list element (data-action at line 4 of show.html.erb: `stream-connected@turbo:frame-load->chat#streamConnected`), which is not the event Turbo fires for appended streams.

### Security: `Kernel.eval` in CalculatorTool

`app/tools/calculator_tool.rb:11`: `Kernel.send(:eval, expression)` — despite input whitelisting (`%r{\A[\d\s+\-*/.%()]+\z}`) and the 200-char length cap at line 8, Brakeman categorically flags any `Kernel.eval`. The character whitelist does not allow method names or constants, so the immediate risk is low — but the pattern is fragile, and the warning will reappear if the character class is ever relaxed.

### Threading Risk

`MessagesController#create:45`: `Thread.new do ...` fires an unbounded thread per message with no join, no timeout, no thread-pool limit. Under sustained traffic (e.g. 50 concurrent messages), 50 threads could be active simultaneously, each holding a Redis connection and an open HTTP connection to OpenRouter. No `ensure` clause on `Thread.new` for closing the Redis connection. If the Puma worker shuts down (SIGTERM), threads are orphaned — there's no `Thread.handle_interrupt` or at_exit handler.

### Docker / Container Risk

`docker-compose.yml:29`: `volumes: - rails_data:/rails/tmp`. The `Dockerfile:82` copies the Rails app as uid 1000 (`rails`). On a fresh volume, `/rails/tmp` is owned by root (Docker creates the mount point). The `rails` user cannot write to `tmp/` unless `rails_data` was previously initialized with correct ownership, which it isn't on first `docker compose up`. The app will crash on any cache or session write attempt.

### API Key Check Is Informational Only in ApplicationController

`ApplicationController#check_api_key:13-17` sets `flash.now[:alert]` but does not halt the request. For HTML page loads the flash renders in the layout (`app/views/layouts/application.html.erb:15-19`), but for `MessagesController#create` (turbo_stream response), no flash is rendered in the turbo_stream template — the turbo_stream response goes directly to the client without layout rendering. The actual enforcement is in `MessagesController#create:17-24` and `LlmService#process_user_message:12` — duplicate enforcement logic not shared with the before_action.

### Edge Case: Failed User Messages Pollute History

`MessagesController#create:28` persists the user message to Redis *before* calling `LlmService`. If `LlmService` raises (e.g., RubyLLM internal error during streaming), the user's message remains in the conversation. On the next turn, `LlmService#build_chat` will replay that message to the provider, so the provider sees a dangling user turn with no assistant response. The current rescue at `llm_service.rb:33-35` only prevents *assistant* messages from being stored; it does not remove or mark the orphaned user message.

### Other Observations

- `app/services/conversation_store.rb:24`: `current_size = @redis.get(size_key).to_i` — if the size_key is absent (e.g., first message in a conversation), `get` returns `nil`, `.to_i` yields `0`. Correct, but not documented.
- `MockRedis` `lrange` (`test/support/mock_redis.rb:19-25`): only handles positive `start..stop` ranges and `-1`. Real Redis supports negative indices, and `store_message` requests `MAX_MESSAGES-1..MAX_MESSAGES-1` when cap enforcement is tested, which doesn't align with Ruby's array slicing semantics. The test passes by accident because the mock returns the entire list via `list[start..stop] || []` when `start > stop`, which is a Ruby quirk, not Redis behavior.
- `app/services/llm_service.rb:95-104`: `result.content` fallback `result.to_s` is fragile — if `ask` returns a string, the rescue at line 13 (of that block) is never hit, but the `is_a?(Hash)` branch fails silently and falls through to `raw_title.to_s.strip`, which would produce a stringified hash e.g. `"{:title=>\"Chat\"}"` rather than the title alone.
