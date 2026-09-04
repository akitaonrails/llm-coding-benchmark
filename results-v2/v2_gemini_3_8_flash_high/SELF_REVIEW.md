# Engineering Self-Review: AI Chat Assistant (Rails 8 & RubyLLM)

Date: 2026-09-03  
Environment: Ruby 4.0.6, Rails 8.1.3.1, Redis 7, Ubuntu Linux  
Status: Phase 3 (Self-Review Complete)

---

## Surgical Fixes Applied During Review

During review of the test configuration against the prompt requirements, the following surgical fix was applied:

- **`test/test_helper.rb` (lines 1–5):** Added `enable_coverage :branch` to the `SimpleCov.start` block. Previously, SimpleCov was configured with default line-only coverage (`"branch_coverage": false` in `coverage/coverage.json`), preventing generation of branch coverage statistics. Adding `enable_coverage :branch` enabled precise reporting of branch coverage (74.33%) without altering application logic or dependencies.

---

## 1. Goal Verification Table

| Goal ID | Verdict | Concrete Evidence |
| :--- | :--- | :--- |
| **G1** (Modern Stack without bloat) | **PASS** | `.ruby-version:1` (`ruby-4.0.6`), `Gemfile:4` (`rails ~> 8.1.3`), `config/application.rb:6-12` (commented-out railtie engines); `bin/rails runner 'puts [defined?(ActiveRecord), defined?(ActionMailer), defined?(ActiveJob)].compact'` returned empty. |
| **G2** (Hotwire SPA & Tailwind CSS) | **PASS** | `app/views/chats/show.html.erb:1-10` composition; Stimulus controllers in `app/javascript/controllers/{chat,scroll,auto_expand}_controller.js`; Turbo Stream response in `app/views/messages/create.turbo_stream.erb`; `test/controllers/messages_controller_test.rb:15` passes; `bin/rails tailwindcss:build` succeeded. |
| **G3** (RubyLLM with OpenRouter) | **PASS** | `config/initializers/ruby_llm.rb:6-11` configures OpenRouter and `anthropic/claude-sonnet-4.6`; `app/services/chat_service.rb:29-32` supports model override; `bin/rails runner 'puts RubyLLM.config.default_model'` returned `"anthropic/claude-sonnet-4.6"`. |
| **G4** (True Token Streaming) | **PASS** | `app/services/chat_service.rb:98-104` streams chunks via `chat.ask(@prompt) { \|chunk\| broadcast_chunk(chunk.content) }` to `Turbo::StreamsChannel.broadcast_append_to`; verified in `test/services/chat_service_test.rb:91` ("G4: streams tokens via Turbo Streams and persists successful exchange"). |
| **G5** (Multi-Turn Payload Correctness) | **PASS** | `app/services/chat_service.rb:38-44` iterates prior conversation messages and sends prompt separately; verified by `test/services/chat_service_test.rb:16` ("G5: multi-turn payload correctness asserts exact outgoing message array") matching exact role/content array. |
| **G6** (Concurrency-Safe Bounded Persistence) | **PASS** | `app/models/conversation_store.rb:50-58, 96-127` (TTL, Redis distributed lock with Lua atomic release); `app/models/conversation.rb:49-67` (`apply_bounds!`); verified by `test/models/conversation_store_test.rb:31, 71` and `test/models/conversation_test.rb:39, 51`. |
| **G7** (Tool Calling) | **PASS** | `app/tools/server_time.rb:5-11` (ISO 8601 UTC), `app/tools/calculator.rb:6-16` & `app/services/safe_arithmetic_evaluator.rb:1-157` (recursive descent AST evaluator without `eval`); verified by `test/tools/calculator_test.rb:25`, `test/tools/server_time_test.rb:17`, and `test/services/safe_arithmetic_evaluator_test.rb:6-45`. |
| **G8** (Structured Output) | **PASS** | `app/models/conversation_title_schema.rb:5-7`, `app/services/title_generator.rb:16-26`, `app/services/chat_service.rb:126-136, 236-252` (live header and sidebar update); verified by `test/services/title_generator_test.rb:22` and `test/services/chat_service_test.rb:185`. |
| **G9** (Token Budgeting) | **PASS** | `app/models/conversation.rb:41-47`, `app/services/chat_service.rb:79-83` (preflight turns refused without calling provider), `ChatService#broadcast_token_budget_update`; verified by `test/services/chat_service_test.rb:69` ("G9: token budgeting preflight refuses turns when budget is exceeded"). |
| **G10** (Robustness & Error Recovery) | **PASS** | `app/services/chat_service.rb:34-36` (system prompt), lines 64-71 (missing key preflight), lines 105-111 (provider failure rescue to degraded UI), lines 120-132 (failed turn omitted from history); verified by `test/services/chat_service_test.rb:47, 142`. |
| **G11** (Comprehensive Minitest Suite) | **PASS** | Suite passes 47 runs, 161 assertions, 0 failures, 0 errors (`bin/rails test`); SimpleCov measured 94.69% line coverage and 74.33% branch coverage. |
| **G12** (Clean Audits) | **PASS** | `bin/rubocop` (42 files, 0 offenses); `bin/brakeman --quiet --no-pager --exit-on-warn --exit-on-error` (0 errors, 0 warnings); `bin/bundler-audit` (0 vulnerabilities); `bin/ci` passed all 6 steps. |
| **G13** (Production Docker & Compose) | **PASS** | `Dockerfile:12-77` (multi-stage build, non-root user 1000:1000, jemalloc, bootsnap, thruster); `docker-compose.yml:8-20` (WEB_CONCURRENCY=2, RAILS_MAX_THREADS=3, Redis healthcheck dependency). |
| **G14** (Demo Mode & Secret Safety) | **PASS** | Open access in `config/routes.rb`; `.gitignore:20-23` excludes `master.key` and `.env*`; `config/initializers/filter_parameter_logging.rb:6-8`; `git status -u` confirms 0 secrets tracked or committed. |

---

## 2. Code Quality Assessment

### Clean Code Evaluation

- **Naming:** Classes, modules, and files follow standard Ruby and Rails conventions (`Conversation`, `ConversationStore`, `ChatService`, `SafeArithmeticEvaluator`, `ServerTime`, `Calculator`). Method names are intention-revealing (e.g., `token_budget_exceeded?`, `apply_bounds!`, `with_lock`). A minor naming discrepancy exists where the resource route is named `conversations` while mapped to `ChatsController` (`config/routes.rb:8`).
- **Single Responsibility Principle (SRP):**
  - Strong: `SafeArithmeticEvaluator` handles only expression parsing and calculation; `ConversationStore` manages Redis persistence and locking; `Conversation` maintains conversation data structure and truncation bounds; `TitleGenerator` is dedicated to schema title creation.
  - Weak: `app/services/chat_service.rb` acts as an orchestrator but also doubles as an HTML view renderer. It contains 8 distinct private methods (`broadcast_streaming_init`, `broadcast_chunk`, `broadcast_tool_indicator`, `broadcast_streaming_finish`, `broadcast_error`, `broadcast_budget_exceeded`, `broadcast_title_update`, `broadcast_token_budget_update`) that build raw HTML strings for Action Cable broadcasts.
- **Duplication:**
  - In `app/services/chat_service.rb`, error card HTML structure in `broadcast_error` (lines 197–206) and `broadcast_budget_exceeded` (lines 217–227) duplicates markup for SVG alert containers.
  - The `with_env` test helper method is duplicated identically between `test/services/chat_service_test.rb:269-275` and `test/services/title_generator_test.rb:38-44`.
- **Dead Code:**
  - `app/services/safe_arithmetic_evaluator.rb:64` (`raise ArgumentError, "Invalid syntax at: #{scanner.rest}"`) is unreachable because the pre-scanner regex `\A[0-9\.\+\-\*\/\%\^\(\)\s]+\z` on line 43 ensures no unhandled characters reach `scanner.rest`.
  - Empty directory placeholders (`app/models/concerns/.keep`, `app/controllers/concerns/.keep`, `test/fixtures/files/.keep`, `vendor/javascript/.keep`) exist from default Rails scaffolding.
- **Method / Class Size:**
  - Most classes are compact (under 100 lines): `Conversation` (94 lines), `ConversationStore` (145 lines), `ChatsController` (45 lines), `MessagesController` (41 lines), `SafeArithmeticEvaluator` (157 lines).
  - `ChatService` is the largest file at 279 lines, predominantly due to ~120 lines of inline broadcast templates.
- **Coupling Between Layers:**
  - `ChatService` is tightly coupled to Action Cable and Turbo Streams channels (`Turbo::StreamsChannel.broadcast_*_to`). Presentation changes require modifying Ruby service code rather than ERB templates.
  - `MessagesController` is coupled to raw background threading (`Thread.new`) via `ChatService.call(run_async: !Rails.env.test?)`, bypassing Rails backgrounding abstractions.

### Top 3 Recommended Refactorings

1. **Extract Action Cable HTML generation from `ChatService` into dedicated ERB view partials or a Turbo Stream Presenter:**
   - *Why:* `app/services/chat_service.rb` contains ~120 lines of heredoc HTML strings for broadcasting chunks, tool execution indicators, error banners, and budget pills. Moving these to `app/views/chats/streams/` or a presenter separates presentation from orchestration and enables standard template caching and styling consistency.
2. **Introduce an explicit connection pool for Redis (`ConnectionPool.new { Redis.new(...) }`):**
   - *Why:* `app/config/initializers/redis.rb` currently exposes a single singleton `Redis.new` instance across all threads. In Puma clustered mode with multiple threads (`RAILS_MAX_THREADS: 3`) and asynchronous streaming threads (`Thread.new`), concurrent commands multiplexing over the same socket can interleave raw protocol data or trigger socket connection resets.
3. **Isolate Redis Distributed Locking into a standalone `RedisLock` utility:**
   - *Why:* `app/models/conversation_store.rb` currently mixes conversation JSON serialization, sorted set indexing, and TTL logic with low-level locking mechanics (monotonic clock spin-wait loops and raw Lua scripts). Decoupling the lock into a separate class improves testability and reusability.

---

## 3. Test Coverage Assessment

### Coverage Metrics (SimpleCov)

- **Total Line Coverage:** **94.69%** (393 / 415 lines)
- **Total Branch Coverage:** **74.33%** (84 / 113 branches)

### File-by-File Coverage Breakdown

| File | Line Coverage | Branch Coverage | Missed Lines |
| :--- | :--- | :--- | :--- |
| `app/controllers/application_controller.rb` | 100.00% (3/3) | 100.00% (0/0) | None |
| `app/controllers/chats_controller.rb` | 100.00% (26/26) | 100.00% (2/2) | None |
| `app/controllers/messages_controller.rb` | 100.00% (17/17) | 100.00% (4/4) | None |
| `app/helpers/application_helper.rb` | 100.00% (1/1) | 100.00% (0/0) | None |
| `app/models/conversation.rb` | 100.00% (47/47) | 77.78% (7/9) | None |
| `app/models/conversation_store.rb` | **86.25%** (69/80) | 63.16% (12/19) | 43, 44, 60, 61, 76, 83, 84, 92, 93, 108, 142 |
| `app/models/conversation_title_schema.rb` | 100.00% (3/3) | 100.00% (0/0) | None |
| `app/services/chat_service.rb` | 95.19% (99/104) | **61.54%** (16/26) | 17, 18, 19, 258, 277 |
| `app/services/safe_arithmetic_evaluator.rb` | 94.85% (92/97) | 81.63% (40/49) | 50, 64, 114, 115, 136 |
| `app/services/title_generator.rb` | 95.83% (23/24) | 75.00% (3/4) | 35 |
| `app/tools/calculator.rb` | 100.00% (8/8) | 100.00% (0/0) | None |
| `app/tools/server_time.rb` | 100.00% (5/5) | 100.00% (0/0) | None |

### Weakest-Tested Area

- **By Line Coverage:** `app/models/conversation_store.rb` (86.25% line coverage, 11 missed lines). All Redis exception rescue blocks and the internal spin-wait sleep in `with_lock` are unexercised.
- **By Branch Coverage:** `app/services/chat_service.rb` (61.54% branch coverage, 10 missed branches). Branches covering async execution, warning color tiers, and heuristic token calculations are unexercised.

### Failure Modes NOT Covered by Tests

1. **Redis Down / Network Partitions during Persistence Operations:**
   - In `app/models/conversation_store.rb`, `find` (lines 43–44), `save` (lines 60–61), `all` (lines 83–84), `delete` (lines 92–93), and `release_lock` (line 142) each rescue `StandardError => e` and log warnings. No test disconnects Redis or stubs Redis exceptions to verify that the application degrades gracefully when Redis is offline.
2. **Distributed Lock Contention and Timeout:**
   - In `app/models/conversation_store.rb:96-118`, the retry spin loop (`sleep 0.05`, line 108) and `Timeout::Error` raise condition (line 111) are not tested under concurrent contention.
3. **Index Cleanup for Expired Conversations (`stale_ids`):**
   - In `app/models/conversation_store.rb:76`, line 76 (`stale_ids << id`) cleans up keys in the sorted set `conversations:index` whose data keys have expired. No test simulates an expired conversation key inside an active index.
4. **Asynchronous Thread Crash / Unhandled Exception:**
   - In `app/services/chat_service.rb:17-19`, `run_async: true` (`Thread.new`) is skipped during test execution (`run_async: !Rails.env.test?`). Any failure or deadlock inside the unmanaged thread is not asserted by automated tests.
5. **Fallback Token Calculation Heuristic:**
   - In `app/services/chat_service.rb:277`, the heuristic fallback calculation `[ ((prompt.length + accumulated_text.length) / 4.0).ceil, 1 ].max` is not tested with a mock response that omits `input_tokens`/`output_tokens`.
6. **Title Generator Unstructured Content:**
   - In `app/services/title_generator.rb:35`, `content.to_s` is used when the LLM returns a plain string instead of a structured hash. This branch is untested.

---

## 4. Known Defects and Risks

### Concurrency Hazards

1. **Unbounded `Thread.new` Spawning:**
   - In `app/controllers/messages_controller.rb:33` and `app/services/chat_service.rb:17-19`, every submitted message spawns an unmanaged OS thread inside the Puma worker process. Under moderate or burst traffic, unbounded thread allocation can lead to thread exhaustion, CPU contention, and memory spikes.
2. **Unpooled Redis Client across Threads:**
   - `AppRedis.client` in `config/initializers/redis.rb:7` instantiates a single `Redis` object. In CRuby, sharing one socket connection across Puma request threads and `ChatService` background threads without `connection_pool` creates socket contention that can corrupt protocol buffers or raise `Redis::InheritedError`.
3. **Race Condition on Rapid Concurrent Prompts in Same Conversation:**
   - If a user submits two messages in rapid succession to the same conversation before the first stream finishes, prompt 2 reads the conversation history before prompt 1 has completed and committed. Prompt 2 will be sent to the LLM without prompt 1 in its context window. Additionally, two assistant responses will broadcast concurrently into the same Action Cable DOM targets.
4. **Worker Shutdown Thread Abort:**
   - Puma worker restarts or deployments (`SIGTERM`) terminate detached `Thread.new` threads immediately without waiting for LLM streaming or persistence to finalize, resulting in orphaned UI streaming states and lost messages.

### Edge Cases

1. **Byte-Limit Content Truncation String Slicing:**
   - In `app/models/conversation.rb:63-66`, `serialized_bytesize` measures JSON bytes (`bytesize`), but truncation calculates character count (`current_content.length - excess`) and slices by character index (`current_content[0...truncated_len]`). If messages contain multi-byte Unicode (e.g. CJK characters, emoji), byte-to-character mismatch can over-truncate text.
2. **Sorted-Set Index TTL Bumping vs Key Expiration:**
   - In `app/models/conversation_store.rb:57`, `redis.expire(INDEX_KEY, ttl)` resets the TTL of the entire index on every save. Active usage ensures the index never expires, while individual conversation data keys expire after 7 days of inactivity. If more than 50 expired IDs accumulate, `ConversationStore.all(limit: 50)` will return fewer than 50 active chats on the first fetch.
3. **Arithmetic Evaluator Unary Minus Precedence:**
   - In `app/services/safe_arithmetic_evaluator.rb:96-105`, `-2 ^ 2` evaluates unary minus inside `parse_unary` before exponentiation, producing `(-2)^2 = 4` instead of `-(2^2) = -4`.

### Security Concerns

1. **Unauthenticated Public Access (Demo Mode):**
   - In accordance with G14, there is no authentication. Any user who can reach the port can view all conversations, post messages, trigger LLM API spend, or delete conversations (`ChatsController#destroy`).
2. **Lack of Rate Limiting / Prompt Length Encasement:**
   - `MessagesController#create` does not enforce per-IP rate limiting (such as `rack-attack`) or maximum input string lengths. An adversary could send arbitrarily large prompt payloads to consume server memory or exhaust OpenRouter budget.

### Operational Risks

1. **Test Suite Redis Dependency:**
   - The test suite executes directly against a live Redis instance on `redis://localhost:6379/15` (`test/test_helper.rb:14, 26`). If the local Redis daemon is stopped, `bin/rails test` fails immediately.
2. **Docker Compose Port Divergence:**
   - `docker-compose.yml:26` exposes Redis externally on `${REDIS_PORT:-6380}:6379` to avoid conflicting with host Redis on 6379. Operators attempting to connect directly to `localhost:6379` will connect to their local machine instance rather than the containerized service.
