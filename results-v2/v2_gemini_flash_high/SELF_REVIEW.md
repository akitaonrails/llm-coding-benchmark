# Self-Review: RubyLLM Chat Application (Phase 3)

This document represents an honest, evidence-based evaluation of the implementation of the RubyLLM Chat Application.

---

## 1. Goal Verification Table

| Goal ID | Verdict | Concrete Evidence (File & Line / Test Name / Executed Command & Output) |
|:---|:---:|:---|
| **G1** | **PASS** | `config/application.rb:6-12` (AR/AJ/AM disabled); `.ruby-version:1` (`ruby-4.0.6`); `Gemfile:4` (`gem "rails", "~> 8.1.3"`). App is at workspace root. |
| **G2** | **PASS** | Hotwire SPA with Stimulus and Turbo Streams. Form, Message, and Sidebar partials exist under `app/views/conversations/`. No fetch or `innerHTML` calls under `app/javascript/`. |
| **G3** | **PASS** | `config/initializers/ruby_llm.rb:3-6` configures RubyLLM for OpenRouter with model overridable via `CHAT_MODEL` env var. |
| **G4** | **PASS** | Real-time token streaming via `ConversationsController#ask` lines 90-99 using Action Cable broadcasts. Verified in `tmp/verify_streaming.log` (5 incremental broadcasts captured). |
| **G5** | **PASS** | `test/services/chat_service_test.rb:131` (`test "G5 multi-turn payload correctness"`) asserts replayed history is exact and user prompt is sent exactly once. |
| **G6** | **PASS** | Bounded sqlite store in `app/models/conversation_store.rb`. `MAX_MESSAGES_PER_CONVERSATION = 50` and `MAX_MESSAGE_BYTES = 50_000` with 24-hour `TTL` cleanup. Tested in `test/models/conversation_store_test.rb:30,52`. |
| **G7** | **PASS** | Tools `ServerTimeTool` and `CalculatorTool` exposed via RubyLLM Tool API. Tested in `test/services/chat_service_test.rb:189,195`. Verified in `tmp/verify_tools.log`. |
| **G8** | **PASS** | Title generated via `TitleSchema` after first completed exchange (`app/services/chat_service.rb:64-80`). Tested in `test/services/chat_service_test.rb:126` (`conv[:title] == "Mock Title"`). |
| **G9** | **PASS** | Budget check of `tokens_used` against env var threshold in `app/services/chat_service.rb:19-23`. Tested in `test/services/chat_service_test.rb:165` (`test "G9 token budgeting enforcement"`). |
| **G10** | **PASS** | Preflight checked `ENV["OPENROUTER_API_KEY"]` in `app/services/chat_service.rb:13-17`. System instructions set at line 30. Failed turns never stored in DB. Rescued errors displayed using `_error_message.html.erb` partial. |
| **G11** | **PASS** | Minitest tests executed via `bin/rails test` pass clean (20 tests, 78 assertions). SimpleCov wired, report generated with **94.21%** line coverage. |
| **G12** | **PASS** | RuboCop, Brakeman, and bundle-audit pass clean. Verified with `bundle exec rubocop`, `bundle exec brakeman` (0 warnings), and `bundle exec bundle-audit check` (0 vulnerabilities). |
| **G13** | **PASS** | Production Dockerfile runs with non-root user `1000:1000`, `ENTRYPOINT ["/rails/bin/docker-entrypoint"]`. `docker-compose.yml` configures local running. `README.md` documents setup, build, and tests. |
| **G14** | **PASS** | No authentication system present. Secrets managed via environment variables. `git status` verifies no `.env` or master keys are committed. |

---

## 2. Code Quality Assessment

### Evaluation Against Clean Code Principles
- **Naming**: Consistently clear and standard. Controller, service, and model names (`ConversationsController`, `ChatService`, `ConversationStore`) align with Rails naming conventions.
- **Single Responsibility Principle (SRP)**:
  - `ConversationStore` strictly handles customized database logic.
  - `ChatService` focuses on interaction with the LLM.
  - *Violation*: `ConversationsController#ask` coordinates too many things: broadcasting user messages, setting up stream containers, requesting LLM stream with block, checking database states, and handling different exception paths.
- **Duplication**: Extremely low. Reused database initializer cached per-thread is clean.
- **Method/Class Size**: `ConversationsController#ask` spans 71 lines of dense streaming and rendering code, which could be refactored for brevity.
- **Coupling**: The system relies heavily on `ConversationStore` using raw SQLite. While G1 constraints (no ActiveRecord) require this, direct DB references bypass standard Rails active validation patterns.

### Top 3 Refactoring Candidates (With More Time)
1. **Extract Broadcasting Concerns from Controller**:
   Create a dedicated `ChatBroadcaster` service to encapsulate Action Cable streaming mechanics. This would extract WebSocket-formatting code (`Turbo::StreamsChannel.broadcast_append_to`) from `ConversationsController#ask`, making the controller much slimmer and easier to maintain.
2. **Introduce Connection Pooling & WAL Mode for SQLite**:
   Refactor `ConversationStore` to use a robust SQLite connection manager rather than raw thread-local caches (`Thread.current[:custom_store_db]`). Additionally, enable Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) to guarantee high-performance concurrency and avoid database lockups when running under multiple Puma worker processes.
3. ** Tiktoken Token Tokenizer Integration**:
   Replace the crude character division approximation (`length / 4.0`) with an actual tokenizer gem (like `tiktoken_ruby`). This is essential to prevent token budgeting bypasses or premature budget exhaustion for non-ASCII or multi-byte unicode inputs.

---

## 3. Test Coverage Assessment

### Coverage Statistics
- **SimpleCov Line Coverage**: **94.21%** (179 out of 190 lines covered).
- **SimpleCov Branch Coverage**: **0.00% (Not Enabled / N/A)**. Branch coverage is not configured in `test/test_helper.rb`.

### Weakest-Tested Area
- **`app/controllers/conversations_controller.rb` (84.38% coverage)**: This file remains the weakest-tested area due to multiple untested execution paths, including Turbo Stream formats for specific deletion scenarios and the global rescue handlers for general unexpected standard errors.

### Failure Modes NOT Covered by Tests
1. **Action Cable Connection Drops**: No integration test covers how the client or server behaves if the WebSocket socket connection terminates midway through token streaming.
2. **Database Write Locks / Busy Deadlocks**: Although a busy timeout is configured, tests do not simulate database concurrency failures (such as `SQLite3::BusyException`) when multiple parallel Puma processes write to SQLite simultaneously.
3. **OpenRouter Service Outage / Throttling**: Tests use static mocks to verify provider returns, but there are no tests covering actual rate limit HTTP status codes (e.g., 429) or connection timeouts.
4. **Prompt Injection / Escaping Breaches**: Tests do not evaluate the security behavior of the HTML template when executing prompts containing script tags or malicious Markdown sequences.

---

## 4. Known Defects and Risks

1. **SQLite Concurrent Write Hazard (`BusyException`)**:
   Under high concurrent load with `WEB_CONCURRENCY=2`, both Puma processes will attempt to write messages back to SQLite. Since SQLite is in default rollback journal mode, writing locks the whole database file. While `busy_timeout` is set to 5000ms, writes could still raise exceptions if transactions overlap beyond this duration.
2. **Thread-Local Connection Leakage**:
   `ConversationStore.db` registers a database connection on `Thread.current`. In a concurrent web server like Puma that dynamically provisions and recycles threads, this can result in connection leaks, hanging file descriptors, and increased thread memory overhead.
3. **Inaccurate Token Budget Accounting**:
   The `approximate_tokens` method uses a simple division ratio (`length / 4.0`). This works reasonably for English text, but fails completely for code syntax, JSON formatting, or non-English characters. This creates an exploitation risk where users can bypass token budgets, or converse in languages that prematurely trigger the budget warning.
4. **Absence of Programmatic DB Schema Migration**:
   Table structures are initialized programmatically on first connection. Any changes to the sqlite database schema in future releases lack a standard migration tracking system, risking schema desynchronization between environments.
