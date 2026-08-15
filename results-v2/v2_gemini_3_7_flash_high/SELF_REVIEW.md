# Self-Review Report: Rails LLM Single-Page Application (SPA)

**Phase:** Phase 3 of 3 (Self-Review)  
**Date:** August 15, 2026  
**Environment:** Rails 8.1.3.1 | Ruby 4.0.6 | Turbo 8 / Hotwire | RubyLLM 1.16.0 | SQLite3 2.0+ (WAL mode)

---

## 1. Goal Verification Table

| Goal ID | Goal Name | Verdict | Concrete Evidence |
|---|---|---|---|
| **G1** | Modern Rails Stack without ActiveRecord | **PASS** | `config/application.rb:5-15` omits ActiveRecord/Mailer/Job; `Gemfile:4` bundles Rails 8.1.3.1 with Ruby 4.0.6 (`.ruby-version:1`). |
| **G2** | ChatGPT-like SPA | **PASS** | Componentized partials in `app/views/chats/` and `app/views/messages/`, Hotwire Turbo Streams in `app/views/chats/index.html.erb:54`, Stimulus controllers in `app/javascript/controllers/*.js`; `ChatsControllerTest#test_GET_root_path_renders_SPA_with_initial_conversation_and_sidebar` passes. |
| **G3** | RubyLLM Integration | **PASS** | `config/initializers/ruby_llm.rb:3-7` configures OpenRouter with `anthropic/claude-sonnet-4.6`; `ChatOrchestrator.build_chat` (`app/services/chat_orchestrator.rb:34-38`) instantiates `RubyLLM.chat(provider: :openrouter)`. |
| **G4** | True Token Streaming | **PASS** | `app/controllers/messages_controller.rb:61-78` broadcasts token chunks via `Turbo::StreamsChannel.broadcast_update_to`; verified in `test/services/chat_orchestrator_test.rb:146-191` and `test/controllers/messages_controller_test.rb:12-28`. |
| **G5** | Multi-Turn Payload Correctness | **PASS** | `app/services/chat_orchestrator.rb:44-50` replays history once before calling `chat.ask(prompt)`; unit test `test/services/chat_orchestrator_test.rb:19-72` asserts 6-message ordered sequence and single prompt inclusion. |
| **G6** | Concurrency-Safe Bounded Persistence | **PASS** | `app/repositories/conversation_repository.rb:50-53,178-211` sets WAL mode, busy timeout (5000ms), retry backoff, max messages (50), max bytes (500 KB), and TTL pruning (7 days); 7 tests pass in `test/repositories/conversation_repository_test.rb`. |
| **G7** | Tool Calling | **PASS** | `app/tools/server_time.rb:3` and `app/tools/calculator.rb:3` subclass `RubyLLM::Tool`; arithmetic evaluated safely without `eval` via AST parser in `app/services/safe_calculator.rb:3-163`; verified in `ToolsTest` and `SafeCalculatorTest`. |
| **G8** | Structured Output | **PASS** | `app/services/title_generator_service.rb:4-19,40` invokes `chat.with_schema(TITLE_SCHEMA)` with `strict: true`; verified in `TitleGeneratorServiceTest#test_generates_title_using_structured_schema`. |
| **G9** | Token Budgeting | **PASS** | `app/services/chat_orchestrator.rb:58-61` enforces `CONVERSATION_TOKEN_BUDGET` (default 8000) and aborts prior to provider call; `app/views/chats/_token_budget.html.erb` renders live meter; verified in `ChatOrchestratorTest:83-96`. |
| **G10** | Robustness & Error Handling | **PASS** | `app/services/chat_orchestrator.rb:25-31,39,66-75,85` validates API key preflight, isolates failed turns from SQLite, renders degraded UI state (`app/views/messages/_error_message.html.erb`); verified in `ChatOrchestratorTest:98-144`. |
| **G11** | Comprehensive Minitest Test Suite | **PASS** | Test suite runs 55 tests, 213 assertions, 0 failures/errors via `PARALLEL_WORKERS=1 bin/rails test`, with SimpleCov line and branch coverage enabled. |
| **G12** | Clean Code & Security | **PASS** | `bin/rubocop` reports 0 offenses across 42 files; `bin/brakeman -q` reports 0 security warnings; `bin/bundler-audit check` reports 0 known vulnerabilities. |
| **G13** | Production Docker & Compose | **PASS** | Multi-stage `Dockerfile` (`base`, `build`, non-root user `rails:1000`, `ENTRYPOINT ["/rails/bin/docker-entrypoint"]`, `RAILS_ENV=production`) and local `docker-compose.yml` with Redis and persistent volume mounts. |
| **G14** | Zero Secrets Committed | **PASS** | `git grep -i "sk-ant\|sk-or\|openrouter_api_key="` verifies zero hardcoded API keys; all credentials resolved dynamically via `ENV["OPENROUTER_API_KEY"]`. |

---

## 2. Code Quality Assessment

### Clean Code Principles Review

- **Naming:** Classes, modules, and file paths adhere strictly to Rails and Ruby conventions (`Conversation`, `ConversationRepository`, `ChatOrchestrator`, `SafeCalculator`, `TitleGeneratorService`, `ServerTime`, `Calculator`). Method names are descriptive and intention-revealing (e.g., `first_exchange_completed?`, `preflight_check!`, `cleanup_expired!`, `apply_bounds`).
- **Single Responsibility Principle (SRP):**
  - Domain model `Conversation` (`app/models/conversation.rb`) encapsulates conversation attributes, message structures, and token counting without database I/O.
  - `ConversationRepository` (`app/repositories/conversation_repository.rb`) encapsulates raw SQLite connection management, schema initialization, retry mechanisms, and bounded storage policies (message caps, byte caps, TTL).
  - `ChatOrchestrator` (`app/services/chat_orchestrator.rb`) orchestrates LLM payload preparation, tool binding, budget enforcement, and streaming chunk callbacks.
  - `SafeCalculator` (`app/services/safe_calculator.rb`) encapsulates arithmetic tokenization and RPN evaluation with zero `eval`.
  - `TitleGeneratorService` (`app/services/title_generator_service.rb`) isolates structured output title generation and fallback handling.
- **Duplication:** Minimal duplication. Timestamp parsing logic is centralized in `Conversation#parse_time`, though ISO8601 formatting occurs in both `Conversation` and `ConversationRepository`.
- **Dead Code:** Unused helper stub `ApplicationHelper` (`app/helpers/application_helper.rb`). Unused predicate `Conversation#empty?` (views call `messages.empty?` directly).
- **Method & Class Size:** Classes remain concise: `ConversationRepository` (213 lines), `SafeCalculator` (163 lines), `MessagesController` (156 lines), `ChatOrchestrator` (113 lines), `Conversation` (97 lines). All methods are under 60 lines.
- **Coupling Between Layers:** `MessagesController` is moderately coupled to Turbo Streams DOM identifiers and partial rendering during streaming. `ConversationRepository` uses a class-level connection variable `@connection` per Puma process rather than a pooled interface.

### Top 3 Refactoring Priorities

1. **Connection Pooling in `ConversationRepository` (`app/repositories/conversation_repository.rb`):**
   - *Why:* `ConversationRepository` maintains a single class-level `@connection` instance per Puma worker process. Under heavy multi-threaded Puma loads (`RAILS_MAX_THREADS > 3`), concurrent database access relies solely on SQLite WAL mode and busy timeouts. Wrapping database connections in a `ConnectionPool` or thread-local storage (`Concurrent::ThreadLocalVar`) would isolate thread queries and reduce busy contention.
2. **Decouple Turbo Stream Broadcaster from `MessagesController` (`app/controllers/messages_controller.rb`):**
   - *Why:* `MessagesController#create` currently orchestrates streaming chunks, HTML rendering of partials, and Turbo broadcast dispatching inline. Extracting this into a dedicated `ChatStreamBroadcaster` service would isolate UI push mechanics from HTTP controller lifecycle and simplify controller testing.
3. **Refactor Procedural Shunting-Yard Parser in `SafeCalculator` (`app/services/safe_calculator.rb`):**
   - *Why:* `SafeCalculator.to_rpn` and `SafeCalculator.tokenize` utilize procedural `while` loops with index manipulation. Refactoring to an object-oriented Lexer/Parser with token objects (`NumberToken`, `OperatorToken`, `ParenthesisToken`) would improve extensibility (e.g., adding trigonometric or algebraic functions) and unit testability.

---

## 3. Test Coverage Assessment

### SimpleCov Coverage Metrics

- **Overall Line Coverage:** **93.64%** (398 / 425 covered lines)
- **Overall Branch Coverage:** **72.05%** (98 / 136 covered branches)

### Per-File Breakdown

| File | Line Coverage | Branch Coverage |
|---|---|---|
| `app/controllers/application_controller.rb` | 100.0% (3/3) | 100.0% (0/0) |
| `app/controllers/chats_controller.rb` | 100.0% (10/10) | 100.0% (0/0) |
| `app/controllers/conversations_controller.rb` | 100.0% (27/27) | 100.0% (2/2) |
| `app/controllers/messages_controller.rb` | 91.30% (42/46) | 66.67% (4/6) |
| `app/helpers/application_helper.rb` | 100.0% (1/1) | 100.0% (0/0) |
| `app/helpers/markdown_helper.rb` | 100.0% (5/5) | 100.0% (2/2) |
| `app/models/conversation.rb` | 93.75% (45/48) | 75.00% (6/8) |
| `app/repositories/conversation_repository.rb` | 91.84% (90/98) | 64.00% (16/25) |
| `app/services/chat_orchestrator.rb` | 96.23% (51/53) | 55.00% (11/20) |
| `app/services/safe_calculator.rb` | 97.80% (89/91) | 85.45% (47/55) |
| `app/services/title_generator_service.rb` | 83.87% (26/31) | 50.00% (9/18) |
| `app/tools/calculator.rb` | 85.71% (6/7) | 100.0% (0/0) |
| `app/tools/server_time.rb` | 100.0% (4/4) | 100.0% (0/0) |

### Weakest-Tested Areas

1. **`TitleGeneratorService` Branch Fallbacks (`app/services/title_generator_service.rb` — 50.0% Branch Coverage):** The JSON parse string fallback path (`lines 57-64`) when `response.content` returns an unparsed JSON string or multiline text is not fully exercised under mocked schema responses.
2. **`ChatOrchestrator` Token Estimation Branches (`app/services/chat_orchestrator.rb` — 55.0% Branch Coverage):** Branches where API responses lack `input_tokens` or `output_tokens` attributes (falling back to character-based heuristic estimation `estimate_tokens`) are not triggered because test doubles supply explicit token counts.
3. **`ConversationRepository` Busy Retry Loop (`app/repositories/conversation_repository.rb` — 64.0% Branch Coverage):** The exponential backoff rescue loop in `with_retry` handling `SQLite3::BusyException` is not simulated under sustained lock contention.

### Failure Modes NOT Covered by Tests

1. **Storage Disk Full / Read-Only Filesystem:** SQLite failures resulting from filesystem write errors or partition exhaustion during `save` are unhandled and untested.
2. **Concurrent Request Race Conditions on the Same Conversation:** Concurrent `POST /conversations/:id/messages` requests for the identical conversation ID will race on reading history and writing updated turns; this race condition is prevented in UI by client-side button disabling, but is not rejected by server-side locking.
3. **ActionCable / WebSocket Disconnects During Streaming:** Client disconnection mid-stream does not abort provider requests or test downstream Turbo channel drops.
4. **Tampered / Malformed SQLite JSON:** If `messages_json` contains corrupted or non-JSON content in the database, behavior during `Conversation.new` normalization is untested.
5. **OpenRouter API Hanging Indefinitely:** HTTP socket timeout or gateway timeouts beyond the configured 60-second request timeout are not simulated with mock network stalls.

---

## 4. Known Defects and Risks

### Concurrency Hazards

- **No Row-Level or Optimistic Locking on Conversation Records:** If a user submits two messages simultaneously (e.g., via automated scripts or multiple tabs), both requests will read the same prior message list, execute independent LLM calls, and overwrite each other's state in SQLite. A version column (`lock_version`) or per-conversation mutex is recommended.
- **Process-Wide SQLite Connection in Multithreaded Puma:** A single `@connection` instance is shared across threads in each Puma worker. While WAL mode allows concurrent readers and one writer, write spikes can encounter `SQLite3::BusyException` if transactions queue beyond the 5000ms timeout.

### Edge Cases & Data Limits

- **Large Single Message Payload Memory Spikes:** While `apply_bounds` ensures the stored payload does not exceed 500 KB upon saving, an incoming prompt of 1 MB would be processed in memory by `ChatOrchestrator` before being bounded or trimmed.
- **Worker Thread Starvation During Long Streaming Sessions:** Each active streaming request holds an open Puma worker thread while waiting on external OpenRouter tokens. Under high concurrent user traffic, thread pool exhaustion could occur unless offloaded to asynchronous streaming or background jobs.

### Security Concerns

- **Absence of User Authentication & Multi-Tenant Scoping:** Conversations are referenced purely by UUID. Without session or user scoping, knowledge of a UUID grants full read/delete access to that conversation's history.
- **Sanitization of Rendered Markdown:** Initial Kramdown output was marked `html_safe` directly. A surgical fix was applied during self-review to wrap output with `ActionController::Base.helpers.sanitize` to prevent cross-site scripting (XSS) from LLM-generated HTML.

### Operational & Infrastructure Risks

- **SQLite on Network / Shared Volumes:** SQLite WAL mode requires POSIX shared memory (`-shm` and `-wal` files). Running SQLite on NFS, AWS EFS, or certain distributed file systems can cause silent database corruption. The production Docker volume must reside on a local block device.
- **Production Redis Dependency for ActionCable:** Clustered Puma in production requires Redis (`REDIS_URL`) for ActionCable Turbo Stream broadcasting across worker processes. A Redis outage will halt real-time UI token streaming.

---

## 5. Surgical Fixes Applied During Review

1. **HTML Sanitization in Markdown Helper (`app/helpers/markdown_helper.rb`):**
   - *Issue Discovered:* Kramdown was rendering HTML and returning `.html_safe` without sanitizing potentially dangerous tags (e.g., `<script>`) if emitted by LLM prompt injection.
   - *Fix Applied:* Wrapped Kramdown HTML output with `ActionController::Base.helpers.sanitize` before returning.
   - *Verification:* Added `test/helpers/markdown_helper_test.rb` verifying script tag removal; test passes with 0 RuboCop offenses.
2. **Turbo Stream Format Integration Tests (`test/controllers/conversations_controller_test.rb` & `test/controllers/messages_controller_test.rb`):**
   - *Issue Discovered:* Controller turbo_stream response formats for `destroy` and streaming token block callbacks lacked integration test coverage.
   - *Fix Applied:* Added turbo stream format tests in `ConversationsControllerTest` and exercised the streaming block yield in `MessagesControllerTest`.
   - *Verification:* Test suite increased from 51 to 55 passing tests; line coverage increased to 93.64%.
