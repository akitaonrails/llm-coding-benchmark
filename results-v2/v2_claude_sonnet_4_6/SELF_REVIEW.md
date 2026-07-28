# Self-Review

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 — Use real `RubyLLM::Chat#add_message(role:, content:)` for history replay | PASS | `chat.rb:165`: `def add_message(message_or_attributes)` where the argument is a hash; `chat_service.rb:102`: `chat.add_message(role: msg[:role].to_sym, content: msg[:content].to_s)` — valid positional hash call. `Message.new` uses `options.fetch(:role)` and `options.fetch(:content)`. |
| G2 — Two `RubyLLM::Tool` subclasses with `description`, `param`, `execute` | PASS | `calculator_tool.rb:1`: `class CalculatorTool < RubyLLM::Tool`; `server_time_tool.rb:1`: `class ServerTimeTool < RubyLLM::Tool`. Both declare `description` and `def execute`. CalculatorTool adds `param :expression`. |
| G3 — CalculatorTool uses a safe recursive-descent parser (no `eval`) | PASS | `calculator_tool.rb:8-78`: hand-written tokenizer + recursive `parse_expr/parse_term/parse_factor`. No `eval`, `send`, `public_send`, or `constantize`. Input validated via `/\A[\d\s+\-*\/().]+\z/` allowlist at `line 24`. |
| G4 — Structured output via `RubyLLM::Schema` subclass for title generation | PASS | `conversation_title_schema.rb:1`: `class ConversationTitleSchema < RubyLLM::Schema`; `chat_service.rb:58`: `title_chat.with_schema(ConversationTitleSchema)`. `with_schema` exists in `chat.rb:111`. `RubyLLM::Schema` exists in `ruby_llm-schema-0.4.0`. |
| G5 — Unit test asserting exact multi-turn outgoing message array (no doubling) | PASS | `chat_service_test.rb:20-52`: seeds `[user: Hello, asst: Hi there!]`, calls `stream_reply` with "Second question", captures the full array sent to the provider, asserts exactly 3 turn messages in correct order, and asserts "Second question" appears exactly once. |
| G6 — Streaming via Action Cable / Turbo Streams | PASS | `messages_controller.rb:69-129`: `Thread.new` calls `service.stream_reply` which yields chunks; each chunk is broadcast via `Turbo::StreamsChannel.broadcast_append_to` targeting `response-#{message_id}`. Spinner removal and done-marker set via `broadcast_replace_to`. View subscribes at `show.html.erb:20` via `turbo_stream_from`. |
| G7 — Token budget enforcement (blocks messages when over budget) | PASS | `conversation_store.rb:43-45`: `budget_exceeded?` checks `token_count >= TOKEN_BUDGET` (default 50,000). `messages_controller.rb:16-19`: returns `render_budget_exceeded` before spawning stream thread. `_budget_exceeded.html.erb` shows link to new conversation. Tested in `messages_controller_test.rb:26-35`. |
| G8 — Tailwind CSS v4 (cssbundling style) | PASS | `Gemfile:16`: `gem "tailwindcss-rails"`; `Gemfile.lock` resolves `tailwindcss-rails (4.6.0)` with `tailwindcss-ruby (~> 4.0)`. `app/assets/tailwind/application.css:1`: `@import "tailwindcss";` — v4 import syntax. Views use Tailwind utility classes throughout. |
| G9 — Docker multi-stage build with Redis in docker-compose | PASS | `Dockerfile`: two-stage build (`base` / `build`), `ARG RUBY_VERSION=4.0.6`, non-root user `rails:1000`, `ENTRYPOINT` + `CMD`. `docker-compose.yml`: `redis:7-alpine` service with named volume, `web` depends on `redis`, `REDIS_URL` wired, `WEB_CONCURRENCY: 2`. |
| G10 — Conversation history stored in Redis (TTL-backed) | PASS | `conversation_store.rb:1-104`: all reads/writes go through Redis keys `conv:{id}`. TTL defaults to 86,400s (24h), set on every write at `line 20` and `line 96`. |
| G11 — Concurrency-safe Redis updates for WEB_CONCURRENCY=2 | PASS | `conversation_store.rb:88-103`: `update_atomically` uses Redis `WATCH` / `MULTI` optimistic locking with up to 10 retries. Action Cable uses Redis adapter (`cable.yml:2`). `WEB_CONCURRENCY: 2` set in `docker-compose.yml:18`. |
| G12 — No injection risk in calculator (safe input validation) | PASS | `calculator_tool.rb:24`: regex `/\A[\d\s+\-*\/().]+\z/` rejects any character outside digits, whitespace, and the five operators. `calculator_tool_test.rb:43-49`: tests reject `system('echo hi')` and backtick expressions. No `eval` anywhere in the file. |
| G13 — Tests mock RubyLLM / Redis: no real API calls | PASS | `ChatServiceTest`: uses `FakeChat` local class (no network). `ConversationStoreTest`: uses `MockRedis` local class (no network). Controller tests use `ConversationStore.stub` and `ChatService.stub`. Tool tests are pure unit tests. `grep` of test dir finds no real HTTP clients. |
| G14 — SimpleCov configured and reporting | PASS | `test_helper.rb:1-6`: `require "simplecov"`, `SimpleCov.start "rails"`. `coverage/.last_run.json`: `{"result": {"line": 81.55}}`. `Gemfile:27`: `gem "simplecov", require: false`. |

---

## 2. CODE QUALITY ASSESSMENT

**Naming and single responsibility:** Generally good. `ConversationStore` owns all Redis I/O; `ChatService` owns all LLM I/O; controllers are thin. `MessagesController` is the main SRP concern: it builds Turbo Stream HTML inline (`token_counter_html`, `error_placeholder_html`) rather than delegating to partials or helpers. These 20-line inline HTML methods sit in the controller layer and would move to view helpers or partials in a real project.

**Duplication:** `api_key_present?` is defined on both `ApplicationController` (line 16) and `ChatService` (line 77). The controller delegates to the service in the `create` action but also inherits the method from `ApplicationController`. The separate definition in `ChatService` exists to allow the service to be instantiated independently, but the `preflight!` guard and the controller-level guard check the same env var in different code paths.

**Method/class size:** `spawn_stream_thread` (`messages_controller.rb:66-130`) is 64 lines and handles initial streaming, spinner removal, done-marker, title generation, token counter update, and two error branches. It has too many responsibilities for a single method.

**Dead code:** `hello_controller.js` is Stimulus boilerplate that was never wired to any element in the views. Not harmful but unused.

**Coupling:** `MessagesController` directly instantiates `ConversationStore` via `ApplicationController#store` and also `ChatService` via `ApplicationController#chat_service`. The background thread closes over `service` and `store` references, bypassing Rails' request lifecycle. This is the only practical pattern for background streaming without a job queue, but it means the thread holds live references to per-request objects.

**Top 3 things to refactor:**

1. **Extract `spawn_stream_thread` into a dedicated streaming object.** The method is too long and mixes LLM streaming, DOM update broadcasting, title generation, and token counter refresh. A `ConversationStreamer` class with a single `#call` method would make each step independently testable, and crucially would allow testing the streaming-thread logic — currently 0% covered.

2. **Move inline HTML builders to view helpers or partials.** `token_counter_html` and `error_placeholder_html` in `MessagesController` are untested, produce raw HTML strings, and would be cleaner as partials rendered via `render_to_string`. This would also bring them under SimpleCov.

3. **Deduplicate `api_key_present?`.** The double definition in `ApplicationController` and `ChatService` is a maintenance hazard. The controller should delegate entirely to `chat_service.api_key_present?` (it already does in the `create` action via the `check_api_key` before_action), or the service should be the only authoritative source.

---

## 3. TEST COVERAGE ASSESSMENT

**SimpleCov last run:** 81.55% line coverage (from `coverage/.last_run.json`). No branch coverage data is tracked (SimpleCov `start "rails"` default does not enable branch tracking; `coverage/.resultset.json` shows empty `branches: {}` for all files).

**Weakest-tested area:** The background streaming thread in `MessagesController#spawn_stream_thread` (`messages_controller.rb:69-129`). Uncovered lines include: all five Action Cable broadcasts (spinner removal, done-marker, title broadcast, token counter update), the `RubyLLM::Error` rescue handler, and the generic rescue handler. The `NoopChatService` stub in `messages_controller_test.rb` bypasses the thread entirely — the test asserts the synchronous initial turbo-stream response, not the async streaming path.

**Also uncovered:**
- `ChatService#generate_title` (`chat_service.rb:48-75`) — 0% covered. No test exercises structured output, schema response parsing, or the `RubyLLM::Error` rescue in title generation.
- `ConversationTitleSchema` (`conversation_title_schema.rb`) — never loaded in tests.
- `ApplicationCable::Channel` and `ApplicationCable::Connection` — Rails boilerplate, but 0% covered.
- `ConversationStore#byte_size` and the MAX_BYTES enforcement branch (`conversation_store.rb:79-81`) — the MAX_BYTES cap path is not exercised; only MAX_MESSAGES is tested.
- `MockRedis` never simulates a WATCH conflict. The `update_atomically` retry loop (`conversation_store.rb:89-101`) runs exactly once in every test — the retry logic is untested.

**Failure modes not covered by any test:**
- `generate_title` called with a Hash-format response vs string-format (the `if raw.is_a?(Hash)` branch at `chat_service.rb:64`).
- `enforce_bounds!` hitting the byte-size cap (MAX_BYTES path).
- `update_atomically` exhausting all 10 retries and raising the error string.
- `stream_reply` returning an empty `full_content` from non-streaming (tool-call path) response (`chat_service.rb:37`).
- `error_placeholder_html` called from a background thread rescue — no test covers error broadcasts.

---

## 4. KNOWN DEFECTS AND RISKS

**D1 — `error_placeholder_html` assigns a random ID that mismatches the broadcast target (minor, cosmetic)**
`messages_controller.rb:140`: the replacement HTML has `id="placeholder-#{SecureRandom.uuid}"` (a fresh UUID), but the `broadcast_replace_to` that calls it targets `"placeholder-#{message_id}"` (lines 118, 125). After the replace, the resulting DOM element has the wrong ID. In practice no further code targets it after an error, so this doesn't cause visible breakage, but it is an inconsistency. The correct fix is `id="placeholder-#{message_id}"`.

**D2 — Background thread has no lifecycle management**
`messages_controller.rb:69`: `Thread.new` spawns a detached thread with no reference stored, no join, no timeout. If Puma receives a SIGTERM during a stream, the thread may be killed mid-broadcast, leaving the client with a spinner that never resolves. A timeout around the `service.stream_reply` call or a Concurrent::Future would mitigate this.

**D3 — Concurrent requests to the same conversation race on title generation**
If the user sends two messages in rapid succession, two threads may both read `first_exchange = store.find_or_create(...)[:messages].empty?` as `true` (before either has written) and both attempt `generate_title`, making two API calls. The second title silently overwrites the first. Not a data-integrity issue but wastes API budget.

**D4 — `ConversationStore#byte_size` uses `m[:content]` (symbol key) but JSON round-trips with `symbolize_names: true`**
`conversation_store.rb:85`: `m[:content].to_s.bytesize`. After `JSON.parse(raw, symbolize_names: true)` the key is `:content`, which matches. This is correct. However, if any code path ever inserts a message without JSON round-tripping (direct hash), the key could be a string. Currently only `add_message` writes messages and it always stringifies via `data.to_json`, so this is safe — but fragile.

**D5 — `MockRedis` does not simulate WATCH conflicts**
`conversation_store_test.rb:98-117`: `MockRedis#multi` always returns results (never returns nil). The retry logic in `update_atomically` is therefore never exercised. A real concurrent conflict would exercise the retry loop; a test-time conflict would require making `multi` return `nil` on first call.

**D6 — No test exercises `generate_title` or `ConversationTitleSchema`**
The structured output path (schema gem, provider returning a Hash vs a string, title storage) is entirely untested. A regression in the schema integration or a provider returning an unexpected format would silently surface only in production.

**D7 — Token count uses post-completion `response.tokens` which may be 0 for tool-call turns**
`chat_service.rb:39`: if the model invokes a tool, `full_content` is empty and the block-based streaming path yields nothing. The fallback at line 37 catches the content. But `response.tokens` at that point may reflect only the final turn (after tool resolution), underreporting the tool-call turn's input tokens. This means `token_count` in Redis may undercount for tool-augmented conversations, causing the budget to be hit later than expected.
