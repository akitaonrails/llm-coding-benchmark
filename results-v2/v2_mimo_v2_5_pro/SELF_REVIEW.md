# Self-Review

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | PASS | Ruby 4.0.6 confirmed (`.ruby-version`). Rails 8.1.3.1 (`Gemfile.lock:rails (8.1.3.1)`). `config/application.rb:5-9` requires only `rails`, `active_model/railtie`, `action_controller/railtie`, `action_view/railtie`, `action_cable/engine` — no `active_record`, `action_mailer`, or `active_job`. `config.active_record.maintain_test_schema = false` at `config/application.rb:19`. App at workspace root — verified `ls` of project directory. |
| G2 | PASS | Tailwind CSS via `cssbundling-rails` (`Gemfile:15`). Stimulus controller at `app/javascript/controllers/chat_controller.js`. Turbo Streams: `turbo_stream_from` in `show.html.erb:58`, `broadcast_to_channel` calls in `chat_service.rb:125-127`. Seven partials: `_form.html.erb`, `_form_disabled.html.erb`, `_user_message.html.erb`, `_assistant_message_start.html.erb`, `_error_message.html.erb`, `_budget_exceeded_message.html.erb`, `_sidebar_list.html.erb`. Chat flow uses Turbo form submission + ActionCable token broadcast, no `fetch()+innerHTML`. |
| G3 | PASS | `ruby_llm` 1.16.0 (`Gemfile.lock`). OpenRouter API key configured at `config/initializers/ruby_llm.rb:6`. Default model `anthropic/claude-sonnet-4` overridable via `CHAT_MODEL` env var (`chat_service.rb:18`). `provider: :openrouter` passed explicitly (`chat_service.rb:99`). |
| G4 | PASS | `stream_response` (`chat_service.rb:61-71`) calls `chat.ask` with a block, each chunk broadcast via `broadcast_to_channel(type: "token", content: text)`. `chat_controller.js:33-34` receives tokens and calls `appendToken` (`chat_controller.js:48-58`) which appends text nodes incrementally via `document.createTextNode(text)`. Not a post-completion append. |
| G5 | PASS | `build_llm_messages` (`chat_service.rb:93-96`) calls `MessageStore.for_llm` then `messages[0...-1]`, excluding the last stored user message. Test `chat_service_test.rb:22-47` ("multi-turn payload correctness") asserts exact outgoing array: 4 messages (2 user, 2 assistant) from a 5-message history, confirming the current user turn is excluded. Additional test `chat_service_test.rb:6-20` confirms single-turn exclusion. |
| G6 | PARTIAL | SQLite WAL mode (`config/initializers/database.rb:16`). File-based persistence at `storage/chat.db`. Busy timeout 5000ms (`database.rb:15`). Bounded: `MessageStore#enforce_bounds!` trims at `MAX_MESSAGES` (default 100) or `MAX_BYTES` (default 1M) — `message_store.rb:57-70`. TTL: `ConversationStore.purge_expired!` exists and is tested (`conversation_store_test.rb:74-80`), but is **never called** by any application code — no scheduler, no Active Job, no initializer hook, no middleware. The TTL mechanism is dead code. Additionally, `config/cable.yml` uses the `async` adapter in all environments including production (`cable.yml:7-8`), which is in-process only. With `WEB_CONCURRENCY=2` (multiple Puma workers), broadcasts from one worker's background thread won't reach connections held by the other worker, undermining streaming for half of connected users. |
| G7 | PASS | Two tools: `ServerTimeTool` (`app/tools/server_time_tool.rb`) and `CalculatorTool` (`app/tools/calculator_tool.rb`), both subclass `RubyLLM::Tool`. Registered via `ChatService.available_tools` (`chat_service.rb:37-39`) and applied with `chat.with_tools` (`chat_service.rb:101`). `ServerTimeTool` returns UTC time. `CalculatorTool` evaluates arithmetic. Tests: `calculator_tool_test.rb` (11 tests), `server_time_tool_test.rb` (4 tests). |
| G8 | FAIL | `generate_title_if_needed` (`chat_service.rb:109-123`) generates a title via plain `chat.ask("Generate a short title...")` — a text prompt, not RubyLLM's structured-output/schema API. `ruby_llm-schema` 0.4.0 is installed as a transitive dependency but is never used. No `with_schema`, `response_format`, or structured output call exists anywhere in the codebase (grep confirmed: zero matches for `structured`, `schema`, `with_schema`, `response_format` in app/). The title IS generated and displayed, but via the wrong mechanism. |
| G9 | PASS | `ConversationStore.budget_exceeded?` (`conversation_store.rb:53-61`) checks `tokens_used >= token_budget`. Called in `MessagesController#create` (`messages_controller.rb:14`) and `ChatService#send_message` (`chat_service.rb:25-28`). Configurable via `TOKEN_BUDGET` env var (`conversation_store.rb:15`). UI partial `_budget_exceeded_message.html.erb` shown via turbo_stream (`messages_controller.rb:44-49`). Tests: `messages_controller_test.rb:45-52`, `chat_service_test.rb:55-64`. |
| G10 | PARTIAL | System prompt via `chat.with_instructions` (`chat_service.rb:100`). Missing API key preflight: `ConversationsController` sets `@api_key_missing` (`conversations_controller.rb:6,15`), index shows banner (`index.html.erb:3-14`), messages controller blocks with turbo error (`messages_controller.rb:13,31-39`). Provider failures rescued: `ChatService#send_message` rescues `StandardError` (`chat_service.rb:31-34`), broadcasts error. **However**, failed turns ARE stored into history: `MessagesController#store_and_respond` (`messages_controller.rb:55`) stores the user message immediately before the background LLM call at `process_in_background` (`messages_controller.rb:17,70-81`). If the LLM call fails, the user message persists with no matching assistant reply, violating "failed turns must never be stored into the history that gets replayed to the provider." |
| G11 | PASS | 52 tests, 97 assertions, 0 failures, 0 errors (verified by running `bin/rails test`). Components tested: ConversationStore (11 tests), MessageStore (8 tests), ChatService (6 tests), CalculatorTool (11 tests), ServerTimeTool (4 tests), ConversationsController (6 tests), MessagesController (6 tests). SimpleCov wired in `test_helper.rb:3-9` with branch coverage enabled. Mocks use `mocha` and stub `ChatService#send_message` (`messages_controller_test.rb:15`). |
| G12 | PASS | RuboCop: 38 files inspected, 0 offenses (ran `bundle exec rubocop`). Brakeman: 1 weak-confidence warning (`eval` in `calculator_tool.rb:15`, expected and excluded in `.rubocop.yml:47-49`). bundle-audit: "No vulnerabilities found" (ran `bundle exec bundle-audit check`). |
| G13 | PASS | Multi-stage Dockerfile: `asset-build` (node:20-slim), `ruby-build` (ruby:3.4-slim), `production` (ruby:3.4-slim). Non-root user `appuser` (`Dockerfile:36`). `RAILS_ENV=production` (`Dockerfile:52`). Entrypoint `bundle exec puma` (`Dockerfile:64-65`). `docker-compose.yml` with env vars, named volume for persistence, healthcheck (`docker-compose.yml:16-20`). README.md documents setup, env vars, Docker usage, architecture. |
| G14 | PASS | No authentication (demo app). No secrets committed: `git ls-files | grep -E "\.key|credentials"` returns empty. `.gitignore` excludes `/.env*` and `/config/*.key`. All secrets loaded from env vars (`OPENROUTER_API_KEY` in `ruby_llm.rb:6` and `llm_provider.rb:6`). |

## 2. Code Quality Assessment

**Naming:** Consistent and descriptive. `ConversationStore`, `MessageStore`, `ChatService`, `ServerTimeTool`, `CalculatorTool` all convey purpose. Method names like `build_llm_messages`, `stream_response`, `generate_title_if_needed` are self-documenting.

**Single Responsibility:** Mostly good. `ChatService` handles LLM orchestration, stores handle persistence, tools handle their specific functions. `MessagesController` (103 lines, 8 private methods) handles request validation, user message persistence, Turbo Stream response rendering, background thread spawning, error broadcasting, and form re-enabling — too many responsibilities for one controller.

**Duplication:** Two initializers configure RubyLLM with different default model strings: `config/initializers/ruby_llm.rb:7` sets `anthropic/claude-sonnet-4`, `config/initializers/llm_provider.rb:7` sets `anthropic/claude-sonnet-4-20250514`. The `after_initialize` hook in `llm_provider.rb` runs second and wins, but having two files is confusing. Sidebar HTML is structurally duplicated between `index.html.erb:17-25` and `show.html.erb:3-11` (both render `_sidebar_list` but duplicate the wrapper).

**Dead Code:**
- `app/javascript/controllers/hello_controller.js` — Stimulus scaffold leftover, unused in any view, but eagerly loaded by `index.js:4` (`eagerLoadControllersFrom`).
- `ChatService#store_user_message` (`chat_service.rb:43-49`) — defined but never called. Coverage data confirms 0 hits. The user message is stored in `MessagesController#store_and_respond` instead.
- `ConversationStore.purge_expired!` (`conversation_store.rb:67-69`) — implemented and tested but never invoked by any code path.

**Method/Class Size:** `ChatService` at 132 lines is reasonable. `MessagesController` at 103 lines is borderline. All methods are under 15 lines. No class exceeds 200 lines.

**Coupling:** `MessageStore#enforce_bounds!` (`message_store.rb:61`) references `ConversationStore::MAX_MESSAGES` and `ConversationStore::MAX_BYTES` directly, coupling the two stores. `ChatService` directly calls `ActionCable.server.broadcast` (`chat_service.rb:126`), coupling it to the transport layer.

### Top 3 Refactoring Priorities

1. **Consolidate RubyLLM initializers.** `config/initializers/ruby_llm.rb` and `config/initializers/llm_provider.rb` both configure the same `RubyLLM` with different model defaults. The `after_initialize` hook wins silently. Delete `ruby_llm.rb` and keep the single `llm_provider.rb`.

2. **Extract background processing from `MessagesController`.** `process_in_background` (`messages_controller.rb:70-81`) spawns raw `Thread.new` with no pool, no backpressure, no timeout, and no error isolation beyond rescue. This should be a bounded thread pool or a lightweight job runner. Additionally, the user message storage should move into the background job (after successful LLM response) to fix the G10 violation.

3. **Replace `eval` in `CalculatorTool`.** Despite the regex allowlist (`calculator_tool.rb:9`), `eval` is a code execution primitive. Expressions like `9**999999999` pass the regex and would cause extreme CPU/memory consumption (no `**` is blocked). Replace with a proper expression parser — either a gem like `dentaku` or a recursive-descent parser for the four arithmetic operations and parentheses.

## 3. Test Coverage Assessment

**SimpleCov results** (verified by running `bin/rails test`):
- **Line coverage: 76.95%** (187/243 lines)
- **Branch coverage: 73.68%** (28/38 branches)

**Coverage by group:**
| Group | Line % | Branch % |
|-------|--------|----------|
| Controllers | 95.6% (65/68) | 100.0% (14/14) |
| Models | 100.0% (71/71) | 90.0% (9/10) |
| Channels | 0.0% (0/9) | N/A (0/0) |
| Services | 42.5% (31/73) | 25.0% (3/12) |
| Tools | 90.5% (19/21) | 100.0% (2/2) |

**Weakest-tested area:** `ChatService` at 42.5% line / 25.0% branch coverage. The methods `process_llm_response`, `stream_response`, `replay_history`, `generate_title_if_needed`, `build_chat`, `store_assistant_response`, and `broadcast_to_channel` have zero test coverage — they all depend on real RubyLLM calls or ActionCable broadcasting and are not tested even with mocks.

**Channels:** `ChatChannel` has 0% line coverage. No test exercises subscription or message receipt.

**Failure modes NOT covered by any test:**
- LLM provider timeout or network error during streaming
- ActionCable broadcast failure
- SQLite database locked / busy timeout exhausted
- Concurrent writes to the same conversation
- Title generation failure (rescued but not tested)
- `build_llm_messages` with tool-role messages in history (tool_call_id/tool_name)
- The `enforce_bounds!` byte-size path (`MAX_BYTES` trigger — only count path is tested)
- Calculator tool with expressions that pass the regex but are dangerous (e.g., `9**999999999`)
- Docker build/run (no automated Docker test)

## 4. Known Defects and Risks

### Defects

1. **Duplicate RubyLLM configuration with conflicting defaults.** `config/initializers/ruby_llm.rb:7` sets default model to `anthropic/claude-sonnet-4`. `config/initializers/llm_provider.rb:7` sets it to `anthropic/claude-sonnet-4-20250514`. The `after_initialize` hook wins, but the first initializer runs at boot. Confusing and error-prone.

2. **Failed user turns stored in history (violates G10).** `MessagesController#store_and_respond` (`messages_controller.rb:55`) stores the user message before `process_in_background` calls the LLM. If the LLM call fails, the user message remains in history with no assistant reply. On the next turn, `build_llm_messages` replays history ending with a user message and no assistant response, which may confuse the LLM or cause provider errors.

3. **G8 does not use structured-output/schema API.** `generate_title_if_needed` (`chat_service.rb:116-118`) uses plain `chat.ask()` with a text prompt. The brief specifies "RubyLLM's structured-output/schema API". `ruby_llm-schema` is installed but unused.

4. **`purge_expired!` is dead code.** `ConversationStore.purge_expired!` (`conversation_store.rb:67-69`) is implemented and tested but never called by any code path. No scheduler, no Active Job, no initializer hook, no middleware invokes it. The TTL is defined but conversations never expire.

### Risks

5. **`eval` DoS in CalculatorTool.** `calculator_tool.rb:15` uses `eval(clean)` after regex filtering. The regex `%r{\A[\d\s+\-*/%().,]+\z}` blocks most injection, but allows `**`. An expression like `9**999999999` passes the regex and would cause extreme CPU and memory consumption. Brakeman flags this (weak confidence). There is no timeout or resource limit.

6. **Unbounded `Thread.new` in MessagesController.** `messages_controller.rb:71` spawns a new OS thread per message with no pool limit, no backpressure, and no timeout on LLM calls. Under load, this can exhaust OS threads or memory. A hung provider accumulates zombie threads indefinitely.

7. **Database singleton not thread-safe.** `Database.db` (`config/initializers/database.rb:11-21`) uses `@db ||= begin...end` with no mutex. The `Thread.new` in `MessagesController` means multiple threads within one process share `@db`. SQLite's WAL mode handles concurrent reads, but concurrent writes from multiple threads may hit `SQLITE_BUSY` even with the 5s timeout under heavy load.

8. **ActionCable `async` adapter does not work across processes.** `config/cable.yml` sets `adapter: async` for all environments including production. The async adapter is in-process only — with `WEB_CONCURRENCY=2` (multiple Puma workers), broadcasts from one worker's background thread will not reach WebSocket connections held by the other worker. A cross-process adapter (Redis or Solid Cable) is needed for multi-worker deployments.

9. **Token estimation is crude.** `estimate_tokens` (`chat_service.rb:105-107`) divides character count by 4. This can be off by 50%+ for non-English text or code. Budget enforcement depends on this estimate, so the actual token limit may be significantly different from the configured budget.

10. **`store_user_message` in ChatService is dead code.** `chat_service.rb:43-49` defines `store_user_message` but it is never called. The user message is stored in `MessagesController#store_and_respond` instead. This suggests an incomplete refactoring.

11. **`hello_controller.js` is eagerly loaded dead code.** `app/javascript/controllers/hello_controller.js` is a Stimulus scaffold leftover, not referenced in any view, but `index.js:4` eagerly loads all controllers from the directory. It won't cause bugs (no element uses `data-controller="hello"`), but it adds unnecessary bytes to the JavaScript bundle.

12. **`simple_format` renders LLM output.** `show.html.erb:38` uses `simple_format(message[:content])` to render assistant messages. While Rails' `simple_format` internally calls `sanitize` to strip dangerous HTML, it still adds `<p>` and `<br>` tags to the LLM output. If the LLM returns HTML-like content (e.g., code examples with angle brackets), the rendering may not match the original text exactly. This is a minor cosmetic risk, not a security vulnerability.
