# Self-Review — v2_deepseek_v4_pro

Review performed against the G1–G14 contract in `prompts/benchmark_prompt_v2.txt`. All quality-gate commands and the test suite were re-run fresh in this phase. No application code changes were made during this review.

---

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | PASS | Rails 8.1.3.1, Ruby 4.0.6 (`.ruby-version:1`). No AR, AM, AJ in Gemfile or `config/application.rb:6-10`. `bin/rails` binstub present. No nested app directory. |
| G2 | PASS | Tailwind v4.3.3 (gem lock), Stimulus controller at `app/javascript/controllers/chat_controller.js:1-9`, Turbo Stream partials at `app/views/conversations/message_sent.turbo_stream.erb:1-15` and `create.turbo_stream.erb:1-7`. Views componentized into partials: `_chat`, `_sidebar`, `_message`, `_assistant_message`, `_tool_call`, `_empty_state`, `_budget_exceeded`. |
| G3 | PARTIAL | `ruby_llm` 1.16.0 (latest in Gemfile.lock). OpenRouter configured at `config/initializers/ruby_llm.rb:4`. Model overridable via `LLM_MODEL` env var. **BUT** the hardcoded default is `anthropic/claude-sonnet-4.6` (`config/initializers/ruby_llm.rb:6`, `lib/chat_service.rb:28`, `docker-compose.yml:20`, `README.md:33,76`) — two generations stale. The current latest Claude Sonnet on OpenRouter is `anthropic/claude-sonnet-5`. The env-var override mechanism works, but the default fails the "latest" requirement. |
| G4 | PASS | `ChatService.stream_response` (`lib/chat_service.rb:53-116`) yields `:delta` events per token chunk. `ConversationsController#stream_and_broadcast` (`app/controllers/conversations_controller.rb:79-106`) broadcasts incremental `Turbo::StreamsChannel.broadcast_replace_to` fragments for every chunk (lines 109-128). First chunk replaces the loading placeholder; subsequent chunks update the same element with growing content. True token streaming, not post-completion append. |
| G5 | PARTIAL | History exclusion logic at `lib/chat_service.rb:68-71` correctly slices the last user message if content matches. Test `"stream_response does not include prompt being sent in history - G5 unit test"` (`test/lib/chat_service_test.rb:103-136`) verifies `Q2` is excluded from replayed history and the ask message equals `"Q2"`. **BUT** neither this test nor the earlier multi-turn test (lines 49-83) asserts the **exact outgoing message array** — they use `assert_includes`/`assert_not_includes` checks. The exact-array assertion required by G5 is absent. |
| G6 | PARTIAL | File-based JSON store in `tmp/conversations/` survives restarts (`test/lib/conversation_store_test.rb:29-35`). Write-to-temp-then-rename for atomic saves (`lib/conversation_store.rb:39-46`). `flock(LOCK_SH)` on reads (`lib/conversation_store.rb:23`). **BUT** (1) `cleanup!` (`lib/conversation_store.rb:66-79`) has **zero production callers** — TTL is dead code. (2) Only read locks, no write locks — a read-modify-write between load and save across processes is unguarded. (3) `WEB_CONCURRENCY=2` is not tested. |
| G7 | PARTIAL | Two tools correctly defined as `RubyLLM::Tool` subclasses: `ServerTime` (`lib/tools.rb:2-12`) and `Calculator` (`lib/tools.rb:14-103`). Calculator uses a custom token-based evaluator (`safe_eval`, line 39) — NOT `Kernel.eval`. **BUT** during streaming, `handle_tool_chunk` (`lib/chat_service.rb:145-155`) captures tool metadata but broadcasts `result: "executing..."` (line 153) **without calling `execute_tool`** (`lib/chat_service.rb:164-173`, which is dead code — never called from any production path). Tool results from RubyLLM's internal execution are synced to the conversation store via `sync_messages_from_chat` (lines 132-142) **but never broadcast to the UI**. The user sees "executing..." in a `<details>` block (`app/views/conversations/_tool_call.html.erb:7`) and never the real result. |
| G8 | PASS | `ChatService.generate_title` (`lib/chat_service.rb:20-51`) uses `chat.with_schema` (line 29) with `strict: true` structured output. Called after first completed exchange at `app/controllers/conversations_controller.rb:166`. Title displayed in sidebar (`_sidebar.html.erb:6`) and chat header (`_chat.html.erb:5`). |
| G9 | PASS | `TokenBudget` module (`lib/token_budget.rb:1-22`) with configurable `TOKEN_BUDGET` env var (default 100,000). Checked at `lib/chat_service.rb:56-59` before streaming, and at `app/controllers/conversations_controller.rb:65` as a preflight. Friendly message via `_budget_exceeded` partial. Token estimation uses crude `text.bytesize / 4.0` heuristic (`lib/token_budget.rb:19-20`). |
| G10 | PASS | System prompt via `with_instructions` at `lib/chat_service.rb:3-7,121`. Missing-key preflight at `lib/chat_service.rb:14-17` raises `ApiKeyMissing` with actionable message. Provider failures rescued at `lib/chat_service.rb:111-115` into `:error` yield events → `broadcast_error` renders degraded UI. Failed turns not persisted: all rescues fire before the save at line 106. Test `"stream_response does not store failed turns"` (`test/lib/chat_service_test.rb:86-101`) verifies message count is unchanged after a failure. |
| G11 | PASS | Suite re-run: **63 runs, 113 assertions, 0 failures, 0 errors** (`bundle exec rails test`). Components covered: Conversation (13 tests), ConversationStore (8 tests), TokenBudget (8 tests), Tools (8 tests), ChatService (8 tests), ConversationsController (14 tests), ApplicationController (3 via integration). SimpleCov wired at `test/test_helper.rb:1-9`. **Line coverage: 82.62% (290/351)**. Mocks use Object-based fake stubs mirroring the real RubyLLM API methods (`add_message`, `with_instructions`, `with_tools`, `ask`, etc.). **Gaps**: Controller streaming/broadcast methods at 0% coverage (`coverage/coverage.json` — `broadcast_first_chunk` linear f109-117, `broadcast_assistant_update` L120-128, `broadcast_tool_call` L131-139, `broadcast_error` L142-152, `broadcast_budget_exceeded` L155-163, `generate_title_if_needed` L166-179, `stream_and_broadcast` event-handling arms L86-104). `handle_tool_chunk` and `execute_tool` paths at 0% coverage. Branch coverage not enabled. |
| G12 | PASS | Fresh live runs: `bundle exec rubocop` → **33 files inspected, no offenses detected**. `bundle exec brakeman -q` → **0 errors, 0 security warnings**. `bundle exec bundle-audit check --update` → **No vulnerabilities found** (1221 advisories checked). |
| G13 | PASS | `Dockerfile:1-44`: multi-stage (build+base), Ruby 4.0.6-slim, `RAILS_ENV=production` (line 12), non-root user `rails` uid 1000 (lines 34-36), `ENTRYPOINT ["/rails/bin/docker-entrypoint"]` (line 41), `EXPOSE 3000` (line 43). `docker-compose.yml:1-30`: Redis + web services, env vars, healthcheck dependency, volume. `README.md:1-112`: documents purpose, setup, env vars, Docker usage, testing, linting, and architecture (not empty template). |
| G14 | PASS | No authentication routes/controllers/callbacks. API key read exclusively from `ENV` at `config/initializers/ruby_llm.rb:4`. Secret-pattern scan of `app/ config/ lib/` returns no `sk-or-…` literals. `.gitignore` excludes `.env*`. All code within the workspace root. |

**Summary: 10 PASS, 4 PARTIAL, 0 FAIL.**

---

## 2. Code Quality Assessment

### Strengths

- **Clean separation of concerns at the lib level**: `ChatService`, `ConversationStore`, `TokenBudget`, and `Tools` are well-factored modules with single responsibilities. `ConversationStore` uses atomic write-temp-then-rename (`lib/conversation_store.rb:39-46`) and file advisory locks for reads, which is a good file-based persistence pattern.
- **Views are properly componentized**: 9 partials in `app/views/conversations/`, no inlined HTML blobs except the error broadcast (`conversations_controller.rb:145-150`).
- **Custom calculator evaluator avoids the recurring benchmark eval hazard**: `Tools::Calculator#safe_eval` (`lib/tools.rb:39-102`) uses a token-based shunting-yard evaluator rather than `Kernel.eval` — the only model in the v2 cohort to do this correctly.
- **Consistent error taxonomy**: `ChatService` defines `ApiKeyMissing`, `ProviderError`, and `BudgetExceeded` as named error classes and yields typed `:error` / `:budget_exceeded` / `:delta` / `:tool_call` / `:done` events through a consistent callback protocol.

### Weaknesses

- **`ChatService` is an everything-class**: 185 lines as a class-level singleton handling streaming, tool handling, history reconstruction, title generation, error recovery, and chunk-content parsing. Building and configuring the chat, adding history messages, handling tool chunks, executing tools, parsing chunk deltas, and syncing results are all private methods on the same class. A `ChatFactory`, `HistoryBuilder`, and `ToolRunner` extraction would reduce coupling.
- **Duplicate model pin**: The default model string `"anthropic/claude-sonnet-4.6"` is hardcoded in 4 places (`config/initializers/ruby_llm.rb:6`, `lib/chat_service.rb:28`, `docker-compose.yml:20`, `README.md:33,76`). The config initializer sets `default_model` and the env var fallback makes the title-generation call override redundant, but all 4 must be kept in sync.
- **Unbounded background thread**: `ConversationsController#stream_create` (`app/controllers/conversations_controller.rb:47`) spawns a raw `Thread.new` per request with no pool, no timeout, no backpressure, and no error isolation beyond inline rescue blocks within `ChatService.stream_response`. A crashed thread leaves the Turbo Stream placeholder dangling.

### Top 3 Refactor Targets

1. **Extract `ChatService` into focused collaborators**: `ChatBuilder`, `HistoryReplayer`, `ToolRunner`, and `StreamHandler`. Currently one class does everything; mocking it for tests requires monkeypatching a class-level singleton (`test/lib/chat_service_test.rb:185-193`). Splitting would make each class individually testable and eliminate the metaclass aliasing hack.

2. **Extract background processing from `ConversationsController`**: The `Thread.new` + `Rails.application.executor.wrap` pattern at `conversations_controller.rb:47-51` should be a bounded thread pool or a lightweight job abstraction with timeout and error-surfacing. This also fixes the orphaned streaming-placeholder defect — a timed-out or crashed thread leaves the bouncing-dots placeholder in the UI forever.

3. **DRY the model pin**: Define the default model string once (e.g., a `MODEL_DEFAULT` constant or an `AppConfig` helper) and reference it from the initializer and `ChatService`. The title-generation call at `chat_service.rb:28` duplicates the initializer's `default_model` using the same `ENV.fetch` — if the initializer already wires `config.default_model`, `build_chat` at line 121 doesn't need to override it at all.

---

## 3. Test Coverage Assessment

### Coverage Numbers

- **Line coverage: 82.62%** (290 covered / 351 relevant, per `COVERAGE=1 bundle exec rails test` re-run this session, verified in `coverage/.last_run.json:3` and `coverage/coverage.json`).
- **Branch coverage: NOT ENABLED** (`coverage.json` confirms `"branch_coverage": false`). The test_helper wires SimpleCov but does not configure `enable_coverage :branch`.

### Per-File Coverage (from re-run)

| File | Line % | Notes |
|------|--------|-------|
| `application_controller.rb` | 100.0% | |
| `application_helper.rb` | 100.0% | |
| `token_budget.rb` | 100.0% | |
| `conversation_store.rb` | 95.92% | Only `rescue nil` branches uncovered |
| `tools.rb` | 95.31% | Calculator error paths (division by zero, invalid token, empty expr) uncovered |
| `conversation.rb` | 93.02% | `persisted?`, `serialize`, and `to_h` uncovered |
| `conversations_controller.rb` | 74.07% | All broadcast methods + stream event handling arms at 0% |
| `chat_service.rb` | 67.35% | Tool chunk handling, chunk_content, sync_messages_from_chat, delta path, error rescue arms at 0% |

### Weakest-Tested Area

The **`ChatService` streaming path** is the weakest-tested area. The `handle_tool_chunk`, `chunk_content`, `sync_messages_from_chat`, and the `:delta`/`:error`/`:budget_exceeded` yield arms all have 0% line coverage. The tests mock `build_chat` to return a stub that either raises or returns empty messages — the actual streaming callback logic (`chat.ask { |chunk| ... }`) is never exercised. The `generate_title` happy paths are tested, but the error branch (`result.respond_to?(:content)` returning false) and JSON parse failures are not.

### Failure Modes NOT Covered by Any Test

1. **Tool execution during streaming**: No test verifies that tool calls trigger real execution and result display. The `handle_tool_chunk` path has 0% coverage.
2. **Streaming delta reception**: No test verifies that `chunk.delta["content"]` extraction works with real RubyLLM chunk objects. `chunk_content` has 0% coverage.
3. **Provider timeout/connection failures**: The rescue arms for `Faraday::Error`, `Net::OpenTimeout`, `Net::ReadTimeout` are unreachable in tests (the mock raises `StandardError`, not a network error).
4. **API-key-missing error broadcast**: The `rescue ApiKeyMissing` branch at `chat_service.rb:109-110` has 0% coverage.
5. **Budget-exceeded UI broadcast via controller**: The controller test at `test/controllers/conversations_controller_test.rb:72-79` only verifies `assert_response :success`, not the rendered content of the budget-exceeded partial.
6. **`Conversation#enforce_bounds` intermediate-reallocation loop**: The byte-bound branch that shifts messages and re-serializes (`conversation.rb:85-88`) is tested for final state but not for the intermediate reserialization cost.
7. **`ConversationStore#cleanup!` with real TTL**: The cleanup test uses `TTL=0`, not actual time-based expiry.
8. **`WEB_CONCURRENCY=2` multi-process read-modify-write**: No test spawns two Puma workers and interleaves reads/writes against the shared file store.
9. **Title generation missing both user/assistant messages**: `ChatService.generate_title` has `return unless user_msg && assistant_msg` (line 26) — not tested.
10. **Conversation not found in `find_conversation`**: The rescue `render_bad_request("Conversation not found")` at `conversations_controller.rb:58-59` has 0% coverage.

---

## 4. Known Defects and Risks

### Confirmed Defects

1. **Tool results never broadcast to the UI (G7 partial failure).** `handle_tool_chunk` at `lib/chat_service.rb:145-155` yields `:tool_call` with `result: "executing..."` but never calls `execute_tool`. The real tool results from RubyLLM's internal execution are synced to the conversation file store via `sync_messages_from_chat` (lines 132-142) but never broadcast via Turbo Streams. The user sees "executing..." in the tool-call `<details>` block forever. The `execute_tool` method at line 164 is dead code — no production caller.

2. **TTL / `cleanup!` is dead code.** `ConversationStore.cleanup!` (`lib/conversation_store.rb:66-79`) is defined and tested, but no production code path ever calls it. There is no cron job, no Rake task, no middleware hook, no startup cleanup. Conversations accumulate on disk indefinitely despite the `CONVERSATION_TTL_SECONDS` env var being wired.

3. **Stale model pin.** The default model `anthropic/claude-sonnet-4.6` is two generations behind the current latest `anthropic/claude-sonnet-5`. Hardcoded in 4 files.

### Risks

4. **Unbounded background threads.** `ConversationsController#stream_create` (`app/controllers/conversations_controller.rb:47`) spawns `Thread.new` per request. No thread pool, no thread limit, no timeout, no backpressure. Under concurrent usage, this can exhaust the process's thread capacity. A crashed or hung thread leaves the streaming placeholder (`message_sent.turbo_stream.erb:7-12`) in the DOM permanently — there is no client-side timeout or error-healing.

5. **Read-modify-write race in ConversationStore.** The file store uses `flock(LOCK_SH)` for reads (`lib/conversation_store.rb:23`) but no write locking on the load-save cycle. Under `WEB_CONCURRENCY=2`, two workers can simultaneously load the same conversation, each add a message, and each save — the second save overwrites the first's changes. The write-temp-then-rename pattern ensures each individual save is atomic, but the load-then-modify-then-save sequence is not.

6. **Conversation history access is unauthenticated and un-scoped.** Any `conversation_id` supplied in a URL renders the conversation (`app/controllers/conversations_controller.rb:11-14`), which is acceptable for a demo (G14 requires no auth) but means anyone who obtains a UUID can read and post into any conversation. Not a defect per the brief, but an operational risk worth acknowledging.

7. **`ChatService::BudgetExceeded` exception class is defined but never raised.** Only `ApiKeyMissing` is raised; budget checks use inline `if TokenBudget.exceeded?` with early returns. The unused exception class is dead code (`lib/chat_service.rb:11`).

8. **Token estimation is a crude heuristic.** `TokenBudget.estimate_tokens` uses `text.bytesize / 4.0` (`lib/token_budget.rb:19-20`), which both overcounts CJK characters (~1 byte per token vs ~4 bytes) and undercounts ASCII (~4 bytes would map to ~1 token). The budget tripping point is therefore unpredictable in multi-language use.
