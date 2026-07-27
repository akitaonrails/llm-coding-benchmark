# Self-Review

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1: Rails app, newest Ruby+Rails from mise | PASS | `Gemfile:3` has `rails ~> 8.1.3`, `.ruby-version` is `3.4.10`, `Dockerfile:11` `ARG RUBY_VERSION=3.4.10`. Rubric accepts 3.4.x. |
| G2: No ActiveRecord, Action Mailer, Active Job | PASS | `config/application.rb:7-8` all three commented out. Uses raw SQLite3 via `lib/llm_chat/database.rb` instead of AR. |
| G3: SPA mimicking ChatGPT-like interface | PASS | Conversation list (`conversations/index.html.erb`), chat view with streaming (`conversations/show.html.erb`), user/assistant message bubbles (`messages/_message.html.erb`). |
| G4: Tailwind CSS | PASS | `Gemfile:9` `tailwindcss-rails`, `app/assets/tailwind/application.css:1` `@import "tailwindcss"`, all views use Tailwind utility classes. |
| G5: Hotwire + Stimulus + Turbo Streams | PASS | `Gemfile:7-8` `turbo-rails` + `stimulus-rails`. Stimulus controller at `app/javascript/controllers/chat_controller.js`. Server streams Turbo Stream fragments via `ActionController::Live` (`messages_controller.rb:4`), client renders them with `Turbo.renderStreamMessage()` (`chat_controller.js:48`). |
| G6: Componentize via Rails partials | PASS | 6 partials: `_message`, `_assistant_placeholder`, `_error`, `_budget_exceeded`, `_token_counter`, `_api_key_warning`. CSS in `app/assets/tailwind/application.css`, JS in separate controller files. No single-file dumps. |
| G7: OPENROUTER_API_KEY via env var | PASS | `config/initializers/ruby_llm.rb:4` reads `ENV["OPENROUTER_API_KEY"]`. `docker-compose.yml:9` passes `${OPENROUTER_API_KEY}` from host env. |
| G8: No secrets in source files | PASS | No `.env` file committed. README uses placeholder `your-key-here`. Docker-compose uses shell variable substitution `${OPENROUTER_API_KEY}`. Grep of Dockerfile/compose/README found no hardcoded keys. |
| G9: RubyLLM + OpenRouter + Claude Sonnet | PASS | `chat_service.rb:39` `RubyLLM.chat(model: MODEL, provider: :openrouter)` — valid entry. `chat_service.rb:50` `chat.ask(user_message)` — valid send. `chat_service.rb:58` `response.content` — correct accessor. `chat_service.rb:40` `chat.with_instructions(SYSTEM_PROMPT)` — valid. `chat_service.rb:46` `chat.add_message(role:, content:)` — valid (positional hash). `with_tool` confirmed real at `ruby_llm-1.14.1/lib/ruby_llm/chat.rb:54`. Default model `anthropic/claude-sonnet-4.6` (`chat_service.rb:11`). |
| G10: Minitest unit tests for each component | PASS | 5 test files: `conversations_controller_test.rb` (7 tests), `messages_controller_test.rb` (5 tests), `chat_service_test.rb` (11 tests), `database_test.rb` (9 tests), `tools_test.rb` (10 tests). Tests exercise LLM path via mocks, error paths, multi-turn history, streaming, tool registration, DB CRUD, and calculator security (injection rejection). |
| G11: Brakeman, RuboCop, SimpleCov, bundle-audit | PASS | `Gemfile:21-23` `bundler-audit`, `brakeman`, `rubocop-rails-omakase`. `Gemfile:31` `simplecov`. `.github/workflows/ci.yml` has dedicated jobs for brakeman (line 22), bundler-audit (line 25), rubocop (line 66), and tests (line 92). SimpleCov configured with branch coverage in `test/test_helper.rb:3-8`. |
| G12: Dockerfile (functional) | PASS | Multi-stage build: base image, build stage with gem install + bootsnap + asset precompile, final stage with non-root user. Runs via Thruster + Puma. |
| G13: docker-compose configuration | PASS | `docker-compose.yml` present. Maps port 3000:80, passes env vars, uses named volume for DB persistence. |
| G14: README (not stock template) | PASS | Custom README with features, setup, configuration table, test/lint commands, Docker instructions, and architecture notes. Not the Rails stock template. |

## 2. Code Quality Assessment

**Naming and clarity.** Generally good. `ChatService`, `LlmChat::Database`, controller names are conventional Rails. Method names (`send_message`, `generate_title`, `enforce_bounds!`) communicate intent.

**Single responsibility.** `ChatService` handles chat completion, title generation, token estimation, history building, and API key validation — arguably 5 responsibilities in one class. `LlmChat::Database` is both a schema manager and a full data access layer with 12 public class methods.

**Duplication.** `update_conversation` (`database.rb:81-99`) has three conditional branches that repeat the same UPDATE pattern with different columns. Could be a single dynamic query.

**Dead code.** Two methods are defined but never called in production:
- `ChatService.build_history_for_provider` (`chat_service.rb:124-128`) — only called in tests.
- `LlmChat::Database.cleanup_expired!` (`database.rb:146-153`) — tested but never triggered by any request lifecycle hook, cron, or scheduler. Expired conversations accumulate forever.

**Method size.** `MessagesController#create` (`messages_controller.rb:6-43`) is 37 lines with inline streaming logic. Reasonable but approaching the edge.

**Top 3 refactors with more time:**

1. **Extract a `ConversationRepository` from `LlmChat::Database`.** The Database class conflates connection management, schema initialization, and all CRUD operations. Splitting connection lifecycle from data access would improve testability and make it possible to swap storage backends.

2. **Split `ChatService` into `ChatCompletion` and `TitleGenerator`.** Title generation (`generate_title`) uses a different RubyLLM configuration (schema mode, no tools, no history), making it a natural seam. The dead `build_history_for_provider` method suggests unfinished extraction.

3. **Fix token accounting.** `chat_service.rb:59` computes `estimate_tokens(content) + (response.input_tokens || 0) + (response.output_tokens || 0)` — this double-counts by adding a character-based estimate AND the actual API token counts. Should use actual token counts when available, falling back to the estimate only when they are nil.

## 3. Test Coverage Assessment

**Reported coverage** (from `coverage/.last_run.json`):
- Line coverage: **92.73%**
- Branch coverage: **64.63%**

**Per-file breakdown** (from `coverage/coverage.json`):
| File | Line % |
|------|--------|
| `application_controller.rb` | 100% |
| `conversations_controller.rb` | 100% |
| `messages_controller.rb` | 89.2% |
| `chat_service.rb` | 98.5% |
| `calculator.rb` | 91.7% |
| `server_time.rb` | 100% |
| `database.rb` | 89.7% |

**Weakest-tested area:** `messages_controller.rb` at 89.2% — the streaming path (`ActionController::Live`) is inherently hard to test in integration tests. The `generate_title_if_needed` private method's error-rescue branch and the `write_turbo_stream` IOError rescue are likely uncovered.

**Branch coverage gap:** 64.63% overall indicates many conditional branches are only tested in one direction. The `update_conversation` method has 3 branches based on which arguments are provided — likely only the `title`-only path is tested.

**Failure modes NOT covered by any test:**
- Concurrent write contention on the SQLite database (multi-thread scenario).
- `write_turbo_stream` `IOError` rescue (client disconnect during streaming).
- The `with_schema` title generation path when `response.content` is a plain string (vs Hash).
- Calculator with deeply nested parentheses or very large numbers (stack overflow / precision).
- `enforce_bounds!` byte-cap eviction under concurrent message insertion.
- Database connection failure / SQLite file permissions errors.

## 4. Known Defects and Risks

1. **Thread-safety of shared SQLite connection.** `LlmChat::Database.connection` (`database.rb:36-49`) uses a mutex only for lazy initialization. Once created, the single `SQLite3::Database` instance is shared across all threads without per-query synchronization. Under multi-threaded Puma (`WEB_CONCURRENCY=1, RAILS_MAX_THREADS>1`), concurrent reads and writes on the same connection object may cause `BusyException` or corrupted results. WAL mode helps with multi-process, not multi-thread-same-connection.

2. **Token double-counting.** `chat_service.rb:59`: `estimate_tokens(content) + (response.input_tokens || 0) + (response.output_tokens || 0)` adds a heuristic text-length estimate to the actual API-reported token counts. This inflates the token_count, causing conversations to hit the budget limit prematurely.

3. **Streaming/final rendering inconsistency.** During streaming, chunks are rendered via `helpers.sanitize(chunk)` (`messages_controller.rb:81`), which allows certain HTML tags through. The final complete message is rendered via `_message.html.erb:6` using `<%= content %>`, which HTML-escapes everything. Users may see formatting appear during streaming then vanish when the final message replaces the placeholder.

4. **Dead `cleanup_expired!` method.** Defined (`database.rb:146`) and tested but never called. No scheduled task, no request hook, no TTL enforcement. Conversations persist forever despite the `CONVERSATION_TTL_SECONDS` config suggesting otherwise. The README documents a 24h TTL that does not actually work.

5. **Dead `build_history_for_provider` method.** `chat_service.rb:124-128` is unused in production — only exercised in tests. Suggests incomplete refactoring.

6. **No individual message size limit.** `enforce_bounds!` caps total message count and total byte size per conversation, but a single very large user message (e.g., 500KB paste) is accepted without validation, potentially consuming the entire byte budget in one insert.

7. **`reset_connection!` concurrency hazard.** `database.rb:52-56` closes and nils the connection while other threads may be mid-query. The mutex protects the nil-and-reassign, but does not prevent a thread that already holds a reference to the old connection from using it after close.

8. **No CSRF protection for streaming endpoint.** The Stimulus controller sends POST requests via `fetch()` with the CSRF token from a meta tag (`chat_controller.js:20-21`). If the meta tag is missing (e.g., layout change), the request silently proceeds without CSRF protection in development but would fail in production. This is a fragile dependency.

9. **No rate limiting.** Any client can fire unlimited chat requests. Each request triggers an LLM API call (billed). There is no per-session or per-IP throttling.

10. **Conversation list is unbounded.** `list_conversations` (`database.rb:77`) returns all conversations with no pagination or limit. As conversations accumulate (since cleanup never runs), the index page load time grows linearly.
