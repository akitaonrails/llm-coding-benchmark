# Self-Review: AI Chat Application

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | PASS | Ruby 4.0.6 (`.ruby-version`), Rails 8.1.3 (`bundle exec rails --version`), no AR/AM/AJ: `config/application.rb:3-8` only requires `active_model/railtie`, `action_controller/railtie`, `action_view/railtie`, `action_cable/engine`, `rails/test_unit/railtie`. App generated at workspace root (no nested directory). |
| G2 | PASS | Tailwind via `tailwindcss-rails` gem (Gemfile:9), Hotwire via `turbo-rails` + `stimulus-rails` (Gemfile:7-8), Stimulus controller `app/javascript/controllers/chat_controller.js`, Turbo Stream broadcasts in `messages_controller.rb:67-73`, partials: `_user_message.html.erb`, `_assistant_message.html.erb`, `_chat_input.html.erb`, `_error.html.erb`. |
| G3 | PASS | `ruby_llm ~> 1.16` (Gemfile:11), resolved to 1.16.0 (`bundle exec ruby -e "require 'ruby_llm'; puts RubyLLM::VERSION"`). Configured for OpenRouter in `config/initializers/ruby_llm.rb:1-3`, default model `anthropic/claude-sonnet-4` overridable via `CHAT_MODEL` env var. |
| G4 | PASS | `ChatService#send_message` accepts `&on_chunk` block and yields per-token via `chat.ask(messages) do \|chunk\|` (`chat_service.rb:26-31`). `MessagesController#process_message_async` broadcasts each chunk via `ActionCable.server.broadcast` (`messages_controller.rb:82-84`). `chat_controller.js:47-56` appends chunks incrementally to DOM via `contentEl.textContent += content`. |
| G5 | PASS | Test `"multi-turn payload sends exact message array"` in `test/services/chat_service_test.rb:44-73` asserts `mock_chat.expects(:ask).with(expected_messages)` where `expected_messages` contains exactly the prior user+assistant turns plus the new user message, excluding the empty assistant placeholder. |
| G6 | PASS | Redis-backed persistence (`conversation_store.rb`), `MAX_MESSAGES=100` with `ltrim` (`conversation_store.rb:34`), `MAX_BYTES_PER_MESSAGE=10_000` with `byteslice` (`conversation_store.rb:31`), `TTL_SECONDS=86_400` with `expire` (`conversation_store.rb:35-36`). Survives restart (Redis is external). WEB_CONCURRENCY=2 safe (no process-local state). Proof scripts in `script/proof_restart_phase1.rb` and `script/proof_restart_phase2.rb`. |
| G7 | PASS | `Tools::ServerTimeTool` (`app/services/tools/server_time_tool.rb:1-7`) returns UTC ISO8601 time. `Tools::CalculatorTool` (`app/services/tools/calculator_tool.rb:1-20`) evaluates arithmetic with regex guard. Both extend `RubyLLM::Tool`. Registered via `chat.with_tools(...)` in `chat_service.rb:22`. |
| G8 | PASS | `ConversationTitleGenerator` uses `chat.with_schema(title_schema)` (`conversation_title_generator.rb:7`) with a JSON schema for structured output. Called after first exchange (`chat_service.rb:60` when `message_count <= 2`). Title displayed in UI (`conversations/show.html.erb:26-29`) and updated via ActionCable on complete (`chat_controller.js:59-63`). |
| G9 | PASS | `TokenCounter` (`app/services/token_counter.rb`) estimates tokens at 4 chars/token, reads `TOKEN_BUDGET` env var with default 100000 (`token_counter.rb:12`). Budget check in `messages_controller.rb:41` via `TokenCounter.budget_exceeded?`. In-UI error message rendered via `shared/_error.html.erb` partial. Token usage displayed in `conversations/show.html.erb:32-34`. |
| G10 | PARTIAL | System prompt set via `chat.with_instructions(SYSTEM_PROMPT)` (`chat_service.rb:23`). Missing API key preflight raises `ConfigurationError` with actionable message (`chat_service.rb:73-79`). Provider errors rescued into `ProviderError` (`chat_service.rb:40-44`) and rendered in degraded UI (`messages_controller.rb:88-97`). **However**, `rollback_messages` (`messages_controller.rb:115-118`) uses `lpop` (removes from list HEAD) instead of `rpop` (removes from list TAIL), which deletes the OLDEST messages instead of the just-added user+assistant messages on failure. This corrupts conversation history and leaves the failed user message in the replayed history. |
| G11 | PARTIAL | 37 tests, 74 assertions, 0 failures (`bin/rails test`). SimpleCov wired (`test/test_helper.rb:3-8`). Line coverage: 71.37% (187/262 lines). Branch coverage: not enabled. Weakest areas: `MessagesController` at 27.7% (33/119), `ConversationTitleGenerator` at 14.0% (6/43), `ChatChannel` at 0% (0/4), `Message` model at 0% (0/18). No tests for the async streaming/broadcast path. No tests for `ConversationTitleGenerator` at all. |
| G12 | PARTIAL | RuboCop: 3 offenses in `script/` files (`script/proof_streaming.rb:48` Style/IfUnlessModifier, `script/proof_tools.rb:26,28` Lint/UselessAssignment). Brakeman: 1 warning — `Dangerous Eval` (Weak confidence) for `eval(expression)` in `calculator_tool.rb:13`. bundle-audit: clean (0 vulnerabilities). None of these are in `app/` code, but the goal says "all pass clean." |
| G13 | PASS | `Dockerfile`: multi-stage build, `RAILS_ENV=production` (line 24), non-root user `rails` uid 1000 (lines 64-66), entrypoint `bin/docker-entrypoint` (line 73). `docker-compose.yml`: redis + web services, healthcheck, env vars passed through. `README.md`: documents features, setup, running locally, Docker Compose, env vars. |
| G14 | PASS | No authentication (no auth middleware, no devise, no sessions). `config/master.key` and `config/credentials.yml.enc` not tracked by git (`git ls-files` returns empty). `.gitignore` excludes `.env*` and `/config/*.key`. No hardcoded secrets in source: all references use `ENV.fetch` or `ENV[]`. `docker-compose.yml` uses `${OPENROUTER_API_KEY}` variable interpolation, not hardcoded values. |

## 2. Code Quality Assessment

### Naming
Generally good. Classes and methods have clear, descriptive names (`ConversationStore`, `TokenCounter`, `ChatService`). The `MessagesController#process_message_async` method name accurately describes its behavior. One issue: the `Message` model (`app/models/message.rb`) is dead code — it is never instantiated or referenced anywhere in the application. All message handling goes through `ConversationStore` which stores raw JSON hashes.

### Single Responsibility
`ChatService` does too much: it validates configuration, builds messages, manages the RubyLLM chat lifecycle, handles streaming callbacks, stores responses, tracks tokens, and triggers title generation. The `send_message` method (`chat_service.rb:13-63`) is 50 lines and orchestrates 5+ concerns. `MessagesController` is similarly overloaded — it handles validation, service initialization, budget checks, message storage, turbo rendering, async thread management, error rollback, and ActionCable broadcasting all in one action.

### Duplication
Minimal duplication. The token tracking logic appears in both `ConversationStore.add_message` (`conversation_store.rb:38-41`) and `ChatService#send_message` (`chat_service.rb:58`), leading to potential double-counting when `add_message` is called with a `token_count` and then `hincrby` is called again.

### Dead Code
- `app/models/message.rb` — never used anywhere (0% coverage, no references in app code)
- `app/javascript/controllers/hello_controller.js` — leftover from Rails generator, never used
- `app/views/messages/create.turbo_stream.erb` — never rendered because the controller uses inline `render turbo_stream:` in `render_turbo_response`

### Method/Class Size
`MessagesController` is 119 lines with 10 private methods — borderline too large. `ChatService` is 100 lines with `send_message` being the most complex at 50 lines. Both are within the RuboCop limits (Max: 150 class, Max: 50 method) but could benefit from extraction.

### Coupling
`MessagesController` directly accesses `REDIS` for rollback (`messages_controller.rb:116-117`) instead of going through `ConversationStore`, creating a coupling leak. The `ChatService` directly calls `ConversationStore` and `REDIS` methods, tightly coupling it to the persistence layer.

### Top 3 Refactors

1. **Fix `rollback_messages` and extract error handling from `MessagesController`**: The `lpop` bug is a data-corruption defect. The entire async thread management, error handling, and broadcasting logic should be extracted into a dedicated job or service class, removing the raw `REDIS` access from the controller.

2. **Break up `ChatService#send_message`**: Extract title generation triggering, token tracking, and response storage into separate methods or a pipeline. The method currently handles streaming, error rescue, persistence, and side effects in one block.

3. **Remove dead code and add an adapter layer for persistence**: Delete `Message` model, `hello_controller.js`, and `create.turbo_stream.erb`. Introduce a repository/interface that `ChatService` depends on instead of calling `ConversationStore` and `REDIS` directly, enabling testability and future persistence swaps.

## 3. Test Coverage Assessment

### SimpleCov Results
- **Line coverage: 71.37%** (187 covered / 262 total lines)
- **Branch coverage: not enabled** (SimpleCov config does not enable `branch_coverage`)

### Per-File Coverage (weakest to strongest)

| File | Coverage |
|------|----------|
| `app/channels/chat_channel.rb` | 0.0% (0/4) |
| `app/models/message.rb` | 0.0% (0/18) — dead code |
| `app/services/conversation_title_generator.rb` | 14.0% (6/43) |
| `app/controllers/messages_controller.rb` | 27.7% (33/119) |
| `app/services/tools/calculator_tool.rb` | 45.0% (9/20) |
| `app/services/chat_service.rb` | 46.0% (46/100) |
| `app/helpers/application_helper.rb` | 50.0% (1/2) |
| `app/services/tools/server_time_tool.rb` | 57.1% (4/7) |
| `app/services/token_counter.rb` | 57.7% (15/26) |
| `app/models/conversation_store.rb` | 63.7% (51/80) |
| `app/controllers/conversations_controller.rb` | 69.0% (20/29) |

### Weakest-Tested Area
**`MessagesController`** at 27.7% — the core controller handling message creation, streaming, async processing, and error rollback. Only 3 tests exist, all testing early-return error paths (empty content, missing API key, budget exceeded). The happy path (successful message send, turbo stream rendering, async thread spawning) is completely untested.

### Failure Modes NOT Covered by Any Test

1. **Async streaming/broadcast path** — `process_message_async` (`messages_controller.rb:76-101`) spawns a `Thread.new` that streams chunks and broadcasts via ActionCable. No test exercises this code path.
2. **`ConversationTitleGenerator`** — 0 tests. The title generation flow (structured output, error fallback to "New Conversation") is entirely untested.
3. **`ChatChannel`** — 0 tests. WebSocket subscription and streaming to the client are untested.
4. **Rollback on provider failure in the controller** — The `rollback_messages` method is never tested. The `lpop` vs `rpop` bug has no test coverage.
5. **Concurrent access** — No tests for race conditions when multiple threads/workers access the same conversation simultaneously.
6. **Token double-counting** — `ChatService#send_message` calls `hincrby` at line 58, but `ConversationStore.add_message` also calls `hincrby` when `token_count` is positive (line 40). No test verifies the total token count after a message exchange.
7. **`Faraday::Error` rescue path** — `chat_service.rb:42-43` rescues `Faraday::Error` but no test covers this.

## 4. Known Defects and Risks

### Defects

1. **`rollback_messages` uses `lpop` instead of `rpop`** (`messages_controller.rb:116-117`): When a provider call fails, this method is supposed to remove the just-added user message and assistant placeholder from the Redis list. Instead, `lpop` removes from the HEAD of the list, deleting the oldest messages. This corrupts conversation history on any provider failure in a multi-turn conversation. Should be `rpop`.

2. **Token double-counting**: `ChatService#send_message` stores the assistant message via `ConversationStore.add_message(..., token_count: total_tokens)` (line 54-55), which internally calls `REDIS.hincrby` (`conversation_store.rb:40`). Then `ChatService` calls `REDIS.hincrby` again at line 58 with the same `total_tokens`. This doubles the recorded token usage for every assistant response.

3. **`eval()` in `CalculatorTool`** (`calculator_tool.rb:13`): Although guarded by a regex (`ALLOWED_PATTERN` at line 8) that restricts input to digits and arithmetic operators, `eval()` is inherently dangerous. The regex `\A[\d\s+\-*/().]+\z` does prevent code injection, but Ruby's `eval` can still behave unexpectedly with certain numeric expressions (e.g., very large numbers causing memory issues). A proper expression parser would be safer.

### Risks

4. **Unmanaged threads**: `process_message_async` (`messages_controller.rb:80`) spawns `Thread.new` without any lifecycle management. If the Puma worker shuts down mid-stream, the thread is killed without cleanup. No thread pool, no error reporting for thread-level exceptions outside the explicit rescue blocks. Under load, unbounded thread creation could exhaust resources.

5. **Non-atomic compound Redis operations**: `ConversationStore.add_message` performs `rpush` + `ltrim` + `expire` as three separate commands (`conversation_store.rb:33-36`). Under concurrent access, another client could read the list between `rpush` and `ltrim`, seeing a temporarily over-bounded list. Not critical but violates the stated concurrency-safety guarantee.

6. **No Redis connection pooling**: The global `REDIS` constant (`config/initializers/redis.rb:2`) creates a single `Redis` connection shared across all threads in a Puma worker. While the `redis` gem is thread-safe for individual commands, the connection itself could become a bottleneck under concurrent streaming requests.

7. **`ConversationTitleGenerator` makes a synchronous LLM call**: Title generation (`chat_service.rb:60`) is called inline within `send_message`, adding latency to every first-exchange response. If the title generation LLM call is slow or fails, it blocks the response. The `rescue StandardError` fallback (`conversation_title_generator.rb:13`) prevents crashes but adds latency.

8. **No CSRF protection on WebSocket connections**: `ApplicationCable::Connection` (`app/channels/application_cable/connection.rb`) has no `identified_by` or origin checking. Any page could open a WebSocket connection to the ActionCable server and subscribe to any conversation's channel by guessing the UUID.

9. **`docker-compose.yml` generates `SECRET_KEY_BASE` with `openssl rand`**: The `$(openssl rand -hex 64)` in `docker-compose.yml:21` generates a new secret on every `docker compose up`, invalidating all existing sessions and encrypted cookies. This is acceptable for a demo but would be a problem in any persistent deployment.

10. **No rate limiting or request throttling**: The application has no protection against abuse — a user (or bot) could send unlimited messages, each triggering an LLM API call and consuming tokens from the OpenRouter account.
