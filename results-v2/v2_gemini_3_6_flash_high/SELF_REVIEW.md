# Self-Review Report

**Project**: RubyLLM Claude Sonnet SPA Demo  
**Phase**: Phase 3 of 3 (Self-Review & Verification)  
**Date**: July 30, 2026  

---

## 1. Goal Verification Table

| Goal ID | Goal Description | Verdict | Concrete Evidence |
|---|---|---|---|
| **G1** | Pure Rails SPA Stack (no Active Record, Action Mailer, Action Job) | **PASS** | `config/application.rb:5-15` explicitly omits `active_record/railtie`, `action_mailer/railtie`, and `active_job/railtie`. `Gemfile:1-40` contains no database gems. |
| **G2** | ChatGPT-like UI (Tailwind CSS dark theme, partials, Hotwire) | **PASS** | `app/views/layouts/application.html.erb:1-29`, `app/views/chats/index.html.erb:1-12`, and `app/javascript/controllers/scroll_controller.js:1-17` implement dark-themed Tailwind CSS SPA UI with auto-scrolling. |
| **G3** | RubyLLM Integration (Configured for OpenRouter with Claude Sonnet default) | **PASS** | `config/initializers/ruby_llm.rb:6-8` configures OpenRouter credentials. `app/services/llm_service.rb:11-13` resolves model via `LLM_MODEL` / `CHAT_MODEL` defaulting to `anthropic/claude-sonnet-4.6`. |
| **G4** | Real-time Token Streaming (Incremental Turbo Stream broadcasts) | **PASS** | `app/controllers/chats_controller.rb:148-154` broadcasts token chunks via `Turbo::StreamsChannel.broadcast_append_to`. Verified by `script/prove_streaming.rb` receiving incremental stream chunks. |
| **G5** | Multi-turn Payload Correctness (History excludes pending prompt) | **PASS** | `app/services/llm_service.rb:41-43` replays prior messages excluding pending prompt before `chat.ask(user_prompt)`. Asserted by `test/services/llm_service_test.rb:65-93`. |
| **G6** | Bounded Redis Persistence (TTL 24h, 50 msg cap, 50KB byte cap, Puma restart survival) | **PASS** | `app/services/conversation_store.rb:7-10,755-781` implements TTL & caps. `script/prove_g6_multiworker_restart.rb` and `script/prove_g6_post_restart.rb` verify context survival across server restart in `WEB_CONCURRENCY=2`. |
| **G7** | Integrated Tools (`server_time` and `calculator`) | **PASS** | `app/models/server_time.rb:3-8` returns UTC ISO8601 string. `app/models/calculator.rb:3-468` evaluates arithmetic safely without `eval`. Tested by `test/models/calculator_test.rb:12-25` and `script/prove_tool_calling.rb`. |
| **G8** | Structured Title Generation (`TitleSchema` schema output after turn 1) | **PASS** | `app/models/title_schema.rb:5-6` defines schema. `app/services/llm_service.rb:91-117` calls `RubyLLM.chat.with_schema(TitleSchema)`. Verified by `test/services/llm_service_test.rb:95-106`. |
| **G9** | Token Budgeting (Refuses turns when `MAX_TOKENS_PER_CONVERSATION` exceeded) | **PASS** | `app/services/conversation_store.rb:737-740` and `app/controllers/chats_controller.rb:101-111` enforce budget checks and render in-UI warnings. Tested by `test/controllers/chats_controller_test.rb:49-55`. |
| **G10** | Robust Error Rescuing (API key preflight, provider errors rescued, history uncorrupted) | **PASS** | `app/services/llm_service.rb:19-23,83-88` checks API key preflight, rescues provider errors, and omits failed turns from Redis history. Tested by `test/services/llm_service_test.rb:58-63,117-133`. |
| **G11** | Comprehensive Minitest Suite | **PASS** | `bin/rails test` ran 23 tests, 64 assertions, 0 failures, 0 errors. Coverage report generated at `coverage/index.html`. |
| **G12** | Clean Linters (RuboCop, Brakeman, bundle-audit) | **PASS** | `bin/ci` executed `rubocop` (37 files, 0 offenses), `bundler-audit` (0 vulnerabilities), `importmap audit` (0 vulnerabilities), and `brakeman` (0 warnings). |
| **G13** | Production Dockerfile & Compose | **PASS** | `Dockerfile:64-66` creates non-root user `rails:1000:1000`. `docker-compose.yml:1-28` configures multi-worker Puma (`WEB_CONCURRENCY=2`) and Redis 7-alpine. Verified by `script/prove_docker_compose_chat.rb`. |
| **G14** | Automated CI & Verification Suite | **PASS** | `bin/ci` automates linters, security scanners, and Minitest suite. Standalone proof scripts in `script/prove_*.rb` provide repeatable end-to-end verification. |

---

## 2. Code Quality Assessment

### Clean Code Principles Evaluation

- **Naming**: Domain abstractions (`ConversationStore`, `LlmService`, `Calculator`, `ServerTime`, `TitleSchema`) have clear, intention-revealing names adhering to standard Ruby conventions.
- **Single Responsibility Principle (SRP)**:
  - **Violation in `ChatsController`**: `ChatsController` (`app/controllers/chats_controller.rb:93-191`) handles HTTP request dispatching, but also manages background thread execution (`Thread.new`), LLM stream processing, and Turbo Stream Action Cable broadcasting (`process_llm_stream`).
  - **Violation in `Calculator`**: `Calculator` (`app/models/calculator.rb:396-467`) encapsulates token scanning, infix-to-postfix parsing, operator precedence evaluation, stack calculation, and output formatting inside a single monolithic private method.
- **Duplication**:
  - Redis connection instantiation is repeated across `ConversationStore.redis` (`app/services/conversation_store.rb:14-16`) and verification scripts (`script/prove_streaming.rb:27`).
  - HTTP helper methods (`send_chat_message`) are duplicated across `script/prove_tool_calling.rb`, `script/prove_g6_multiworker_restart.rb`, and `script/prove_g6_post_restart.rb`.
- **Dead Code**:
  - `app/helpers/application_helper.rb:1-2` is an unused empty module.
  - `config/ci.rb:13-22` contains commented-out optional steps for system testing and GitHub signoff.
- **Method / Class Size**:
  - `Calculator#evaluate` (`app/models/calculator.rb:396-467`) is 72 lines long with complex nested branch conditions.
  - `ChatsController#messages` and `process_llm_stream` (`app/controllers/chats_controller.rb:93-191`) total nearly 100 lines combining web flow and streaming orchestration.
- **Coupling between Layers**:
  - `ChatsController` directly calls lower-level `Turbo::StreamsChannel.broadcast_*` API methods instead of delegating broadcasting responsibilities to a dedicated channel helper or event subscriber layer.

### Top 3 Refactoring Recommendations

1. **Extract Background LLM Execution to ActiveJob / Worker Queue**:
   Replace raw `Thread.new` inside `ChatsController#messages` (`app/controllers/chats_controller.rb:130-132`) with a managed background job or thread pool. Raw threads bypass Rails connection pool management and risk premature termination during worker recycling.
2. **Decompose `Calculator` into Tokenizer, Parser, and Evaluator**:
   Refactor `Calculator#evaluate` (`app/models/calculator.rb:396-467`) into discrete, single-responsibility components (`Calculator::Tokenizer`, `Calculator::Parser`, `Calculator::Evaluator`) to simplify unit testing of individual arithmetic parsing stages.
3. **Decouple Action Cable Broadcasting from Controller**:
   Extract `Turbo::StreamsChannel.broadcast_*` calls out of `ChatsController` into a dedicated `ChatBroadcaster` service to decouple HTTP controller logic from UI stream delivery.

---

## 3. Test Coverage Assessment

- **SimpleCov Line Coverage**: **87.55%** (239 lines covered / 34 lines missed out of 273 total lines).
- **SimpleCov Branch Coverage**: **Not Tracked / 0%** (`branch_coverage: false` configured in `test/test_helper.rb:6-10`).
- **Weakest-Tested Area**: `ChatsController` (`app/controllers/chats_controller.rb`), with **73.68% line coverage** (15 missed lines out of 57 executable lines).
  - *Missed lines*: Lines 216, 241-242, 303, 310-311, 313, 319, 326, 334-339, 348, 352, corresponding to asynchronous stream processing, Turbo Stream deletion rendering, and exception rescue callbacks in the controller thread.

### Uncovered Failure Modes

1. **Concurrent Message Mutation Hazards**: No test attempts concurrent message writes or concurrent title updates for the same conversation ID to test Redis serialization.
2. **Unmanaged Thread Failure**: No test covers unexpected thread termination or exceptions occurring inside `Thread.new` before broadcasting starts.
3. **Action Cable / Redis Network Interruption**: No test verifies behavior when Action Cable or Redis connection drops mid-stream during token broadcasting.
4. **Provider API Rate Limits & Error Variants**: Non-standard provider error responses (HTTP 429 rate limiting, HTTP 400 context limit exceeded, or malformed JSON payloads) are un-stubbed.
5. **Calculator Unary Operators**: Expressions using unary minus (e.g. `-5 + 10` or `10 * -2`) trigger parsing failure strings and are not covered in `test/models/calculator_test.rb`.
6. **Redis Key Expiry Mid-Session**: Behavior when a conversation key expires via Redis TTL during an active session is untested.

---

## 4. Known Defects and Risks

1. **Unmanaged Threads in Controller Request Lifecycle (`ChatsController#messages`)**:
   Spawning `Thread.new` inside `ChatsController` (`app/controllers/chats_controller.rb:130`) creates raw OS threads that do not inherit Rails request thread contexts or connection pool cleanup. Under Puma worker recycling (`WEB_CONCURRENCY=2`), active worker processes can terminate in-flight threads without cleanup.
2. **Redis State Mutation Race Conditions (No Mutex / Transactional Locking)**:
   `ConversationStore.save` (`app/services/conversation_store.rb:755-768`) performs read-modify-write cycles on Redis hash keys without transactional locks (`WATCH/MULTI/EXEC` or Redlock). Concurrent requests to the same conversation can overwrite prior messages or title updates.
3. **Escaped Raw Markdown Output in UI**:
   `ChatsController#process_llm_stream` (`app/controllers/chats_controller.rb:152`) uses `ERB::Util.html_escape(chunk)` to append token text directly into HTML elements. Response markdown formatting (bold text, code blocks, bullet points) is rendered as raw escaped text rather than parsed HTML.
4. **Calculator Unary Minus & Floating-Point Edge Cases**:
   `Calculator` (`app/models/calculator.rb:399,409`) treats `-` strictly as a binary operator. Expressions containing unary negative numbers (e.g., `-10 + 5`) return `"Error: Invalid expression format"`. In addition, standard floating-point arithmetic can yield imprecise decimal outputs (e.g. `0.1 + 0.2` => `0.30000000000000004`).
5. **O(N) Redis `KEYS` Command in `clear_all!`**:
   `ConversationStore.clear_all!` (`app/services/conversation_store.rb:748`) uses `redis.keys("conversation:*")`. `KEYS` is a blocking O(N) Redis operation that freezes server execution on production databases; `SCAN` should be used instead.
6. **O(N²) Repeated JSON Serialization in Bounded Persistence**:
   `ConversationStore.enforce_bounds!` (`app/services/conversation_store.rb:779-781`) evaluates `JSON.generate(conv[:messages]).bytesize` repeatedly inside a `while` loop while shifting messages, causing O(N²) string allocations under heavy payload trimming.
