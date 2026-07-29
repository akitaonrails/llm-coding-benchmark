# Self-Review

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | PASS | `config/application.rb:3-15` — ActiveRecord, ActionMailer, ActiveJob, ActionCable, ActiveStorage all commented out. `ruby -v` = 4.0.6, `Rails.version` = 8.1.3. App generated at workspace root. |
| G2 | PASS | Tailwind via `tailwindcss-rails`, Stimulus in `app/javascript/controllers/`, Turbo Streams for streaming. Views are 15 componentized partials. No inline fetch+innerHTML. |
| G3 | PASS | `Gemfile:11` — `gem "ruby_llm"`. `config/initializers/ruby_llm.rb` configures OpenRouter with `config.openrouter_api_key`. Default model `anthropic/claude-sonnet-4` overridable via `CHAT_MODEL` env var. |
| G4 | PASS | `app/controllers/chat_controller.rb:2` includes `ActionController::Live`. Lines 27-52 use `response.stream` (SSE) with `turbo_stream.update` per chunk, flushed every 3 chars or on newline. Tokens appear incrementally, not batched at end. |
| G5 | PASS | `app/controllers/chat_controller.rb:112-114` — `replay_messages` returns all prior messages; the user message is added once via `add_message` at line 22, then included in the replay. Test `test/models/conversation_store_test.rb:66-82` asserts the exact outgoing array for a 3-turn conversation. |
| G6 | PARTIAL | File-based JSON in `tmp/conversations/` survives restarts and multi-worker (no process-local state). `MAX_MESSAGES` and `MAX_BYTES` are defined as constants (`lib/conversation_store.rb:6-7`) but **never enforced** — no code checks `@messages.length >= MAX_MESSAGES` or serialized bytes against `MAX_BYTES`. `TTL` is enforced via `cleanup_expired`. |
| G7 | PASS | `lib/server_time_tool.rb` and `lib/calculator_tool.rb` registered via `chat.with_tool` in `chat_controller.rb:109-110`. Both extend `RubyLLM::Tool`. Tests in `test/lib/tools_test.rb` cover all formats and sanitization. |
| G8 | PARTIAL | Title generation works (`chat_controller.rb:119-135`) but uses `chat.complete` with `with_instructions`, **not** RubyLLM's structured-output/schema API as specified in the goal. |
| G9 | PASS | `lib/conversation_store.rb:101-103` — `budget_exceeded?` checks `@token_count >= TOKEN_BUDGET`. `chat_controller.rb:17-19` refuses further turns with a friendly in-UI message when budget is exceeded. `TOKEN_BUDGET` configurable via env var (default 100000). |
| G10 | PARTIAL | System prompt via `with_instructions` (`chat_controller.rb:107`). Missing API key preflight (`check_api_key` at line 88-91) renders a friendly partial. Provider errors are rescued (`RubyLLM::Error` at line 53, `StandardError` at line 55). **However**, the user message is stored in history (`add_message` at line 22) **before** the API call — if the call fails, the failed turn's user message is already in the history and will be replayed on retry. The `check_api_key` before_action does not halt the action chain (`throw(:abort)` is missing), so the action continues after rendering and may cause double-render/stream errors. |
| G11 | PASS | 34 Minitest tests across 3 test files, 0 failures, 0 errors. SimpleCov wired in `test/test_helper.rb`. Tools tested with real `RubyLLM::Tool` subclass (not mocked API). |
| G12 | PASS | RuboCop: 29 files inspected, no offenses. Brakeman: 2 warnings (weak — eval in calculator, file access in conversations controller), no high-confidence warnings. Bundle-audit: no vulnerabilities found. |
| G13 | PASS | `Dockerfile:1-56` — multi-stage build, `RAILS_ENV=production`, non-root user (`rails:rails`), proper entrypoint (`bin/docker-entrypoint`). `docker-compose.yml` with persisted volume for conversation data. `README.md` documents setup, env vars, Docker, and testing. |
| G14 | PASS | No authentication. No secrets committed — `OPENROUTER_API_KEY` is env-var only, not in any source file, `.env`, Dockerfile, or compose file. Everything in workspace root. |

## 2. Code Quality Assessment

### Naming
Generally good. `ConversationStore` is a clear name. `replay_messages` and `budget_exceeded?` are descriptive. The test name `"multi-turn payload correctness excludes prompt to be sent"` is misleading — the test actually asserts the prompt IS included in the replay.

### Single Responsibility
`ConversationStore` (`lib/conversation_store.rb:135`) handles persistence, serialization, budgeting, TTL, and RubyLLM message conversion. It mixes persistence concerns with domain logic. The `save` method also calls `cleanup_expired` as a side effect, which is surprising.

### Duplication
`cleanup_expired` is defined as both a class method (`self.cleanup_expired` at line 39) and an instance method (`cleanup_expired` at line 132) that delegates to the class method. The instance method is unnecessary overhead.

### Dead Code
Five partials in `app/views/chat/` are never rendered from any controller:
- `_user_message.turbo_stream.erb`
- `_assistant_chunk.turbo_stream.erb`
- `_streaming_chunk.html.erb`
- `_done.turbo_stream.erb`
- `_error.turbo_stream.erb`

All streaming is done inline in the controller via `sse.write turbo_stream.append(...)` etc.

### Method/Class Size
`ChatController#send_message` (`app/controllers/chat_controller.rb:13-69`) is 57 lines with inline SSE writes, rescue blocks, and an ensure block. This is too long for a single method.

### Coupling
`ChatController` directly depends on `ConversationStore` (file persistence), `RubyLLM::Chat` (API), `ServerTimeTool`, and `CalculatorTool`. The `ensure` block in `send_message` tightly couples streaming cleanup with persistence logic.

### Top 3 Refactoring Priorities

1. **Enforce MAX_MESSAGES and MAX_BYTES bounds** — These constants are defined but never checked. `ConversationStore#add_message` should reject messages when `@messages.length >= MAX_MESSAGES` or the estimated serialized size exceeds `MAX_BYTES`. This is a functional gap, not just cosmetic.

2. **Extract streaming logic from `ChatController#send_message`** — The 57-line method mixes SSE streaming, token accumulation, error handling, and persistence. Extract the streaming loop into a dedicated service object (e.g., `ChatStreamer`) that accepts a `ConversationStore` and returns a stream, leaving the controller to handle HTTP concerns.

3. **Fix `check_api_key` before_action** — It renders a response but does not halt the action chain (`throw(:abort)` is missing). The action will attempt to use `response.stream` after the before_action has already set the response, causing a `DoubleRenderError` or `IOError` in production. This should be `render ... and return` or the callback should `throw(:abort)`.

## 3. Test Coverage Assessment

**SimpleCov line coverage: 82.59%** (166/201 lines). Branch coverage is not collected — the SimpleCov configuration uses `start "rails"` which does not enable branch coverage by default.

**Per-group:**
- Controllers: 69.9% (72/103 lines)
- Libraries: 95.9% (93/97 lines)
- Helpers: 100.0% (1/1 line)

**Weakest area:** `ConversationsController` — 0% covered (all 18 lines missed). No integration tests hit the `index`, `show`, or `destroy` actions. `ChatController` has 13 missed lines, including the entire `friendly_error` method (lines 94-101), the `RubyLLM::Error` and `StandardError` rescue blocks (lines 54-57), and the `budget_exceeded` branch (lines 18-19).

**Failure modes NOT covered by any test:**
- Token budget exceeded flow (line 18-19)
- `RubyLLM::Error` rescue (line 53-54)
- `StandardError` rescue (line 55-57)
- `friendly_error` categorization (all when clauses, lines 96-100)
- `generate_title_after_first_exchange` failure path (line 132)
- `ConversationsController#index`, `#show`, `#destroy` (all 0%)
- `ConversationStore#expired?` (line 98)
- `ConversationStore#cleanup_expired` file deletion (line 45)
- `ConversationStore.find` JSON parse error (line 26)
- `ConversationStore.all` JSON parse error (line 15)

## 4. Known Defects and Risks

1. **`check_api_key` before_action does not halt the action chain** (`app/controllers/chat_controller.rb:88-91`). Renders a turbo_stream response but does not `throw(:abort)`. The `send_message` action continues executing and attempts to use `response.stream` after the response is already set, causing a `DoubleRenderError` in production.

2. **User message stored before API call** (`app/controllers/chat_controller.rb:22`). If the API call fails (network error, provider error, rate limit), the user message is already persisted in the conversation history. On retry, the failed turn's message is replayed to the provider.

3. **`MAX_MESSAGES` and `MAX_BYTES` are never enforced** (`lib/conversation_store.rb:6-7`). Conversations can grow unbounded in message count and byte size. Only the TTL and token budget limit growth.

4. **`eval` in `CalculatorTool`** (`lib/calculator_tool.rb:10`). While sanitized via regex, `eval` on user-influenced input is inherently risky. Brakeman flags this as a weak-confidence warning. A parser-based evaluator (e.g., `dentaku` gem) would be safer.

5. **File-based persistence is racy under concurrent writes** (`lib/conversation_store.rb:116`). `File.write` is not atomic — a concurrent request could read a partially-written JSON file. With `WEB_CONCURRENCY=2` or multiple threads, concurrent reads of the same conversation file may see inconsistent state.

6. **No CSRF protection for streaming endpoint** — `send_message` uses `ActionController::Live` with SSE. The `before_action :check_api_key` renders a response without verifying the authenticity token, which is standard for Turbo Streams but should be verified.

7. **`generate_title_after_first_exchange` makes a blocking API call** (`app/controllers/chat_controller.rb:119-135`) inside the streaming response handler. This delays the first streaming chunk while waiting for the title generation API call to complete.

8. **No timeout on response streaming** — The `ensure` block in `send_message` closes the SSE stream, but if the API call hangs indefinitely, the connection remains open with no timeout, potentially leaking threads in Puma.