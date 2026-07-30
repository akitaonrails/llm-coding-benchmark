# Self-Review Report

## 1. Goal Verification Table

| Goal ID | Verdict | Concrete Evidence |
| :--- | :--- | :--- |
| **G1** | PASS | `config/application.rb:8-13` (Active Record, Mailer, Job railties explicitly commented out); `Gemfile:1-60` (no database gems included). |
| **G2** | PASS | `app/views/chats/index.html.erb:1-110` (Tailwind CSS SPA layout with side drawer); `app/javascript/controllers/chat_controller.js:1-47` (Stimulus auto-scroll & submit listeners); `app/controllers/chats_controller.rb:59-65` (Turbo Stream response). |
| **G3** | PASS | `config/initializers/ruby_llm.rb:5-11` (RubyLLM OpenRouter configuration with `LLM_MODEL`/`OPENROUTER_MODEL` env overrides); `app/services/llm_service.rb:33-35,62` (`RubyLLM.chat(model: default_model, provider: :openrouter)`). |
| **G4** | PASS | `app/controllers/chats_controller.rb:70-81` (`LlmService.process_turn` block calls `Turbo::StreamsChannel.broadcast_update_to("chat_#{conv_id}", target: assistant_placeholder_id, html: ...)` for each chunk); verified in `script/test_streaming_proof.rb:85-87`. |
| **G5** | PASS | `app/services/llm_service.rb:68-73` (replays stored history into RubyLLM chat instance prior to calling `chat.say(user_prompt)`); verified in `test/services/llm_service_test.rb:34-63`. |
| **G6** | PASS | `app/services/conversation_store.rb:76-80,157-176` (atomic Redis multi transactions, `enforce_bounds!` enforcing max 20 messages and 100KB byte cap); verified in `test/services/conversation_store_test.rb:34-57` and `script/test_restart_proof.rb:7`. |
| **G7** | PASS | `app/tools/server_time_tool.rb:5-11` and `app/tools/calculator_tool.rb:5-139` (safe AST parser without `eval`); registered in `app/services/llm_service.rb:64`; verified in `test/tools/tools_test.rb:6-46` and `script/test_tools_proof.rb:74`. |
| **G8** | PASS | `app/services/llm_service.rb:15-30,108-113,129-150` (defines `TITLE_SCHEMA` and executes `with_schema` title generation when `messages.size == 2`); verified in `test/services/llm_service_test.rb:87-116`. |
| **G9** | PASS | `app/services/llm_service.rb:52-58,81` (evaluates `used >= max_tokens_budget` and raises `TokenBudgetExceededError`); verified in `test/services/llm_service_test.rb:27-32`. |
| **G10** | PASS | `app/services/llm_service.rb:45-50,103-106,123-126` (preflight API key validation, catching provider exceptions prior to `ConversationStore.append_message`); verified in `test/services/llm_service_test.rb:18-25,65-85`. |
| **G11** | PASS | `app/services/llm_service.rb:37-39,63` (`chat.with_instructions(system_prompt)` using `ENV['SYSTEM_PROMPT']` or default prompt). |
| **G12** | PASS | `bundle exec rubocop` (0 offenses across 36 files), `bundle exec brakeman --no-pager` (0 security warnings), `bundle exec bundle-audit check` (0 vulnerabilities found). All exit with code 0. |
| **G13** | PASS | `bin/rails test` ran 24 tests, 63 assertions with 0 failures, 0 errors. SimpleCov generated line coverage: 86.51% (295 / 341 lines). |
| **G14** | PASS | `Dockerfile:1-68` (multi-stage Ruby 4.0.6 build with asset compilation & production Puma configuration) and `docker-compose.yml:1-26` (orchestrates `web` & `redis` containers). |

---

## 2. Code Quality Assessment

### Architectural & Clean Code Evaluation

* **Naming Conventions**: Variables, classes, and method signatures follow standard Ruby/Rails conventions (`LlmService`, `ConversationStore`, `ServerTimeTool`, `CalculatorTool`). Method names clearly convey intent (e.g., `validate_preflight!`, `enforce_bounds!`).
* **Single Responsibility Principle (SRP)**:
  * [app/services/conversation_store.rb](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/app/services/conversation_store.rb) handles Redis serialization, TTL expiration, and bounding limits exclusively.
  * [app/services/llm_service.rb](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/app/services/llm_service.rb) encapsulates RubyLLM integration, instruction setup, tool registration, streaming callbacks, and title generation schemas.
  * [app/controllers/chats_controller.rb](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/app/controllers/chats_controller.rb) handles web request orchestration and Turbo Stream template rendering.
* **Duplication**: Minimal duplication. HTML layout logic is refactored into partials (`_message.html.erb`, `_conversation_item.html.erb`, `_form.html.erb`, `_token_count.html.erb`).
* **Dead Code**: RuboCop scan confirms zero unused variables or unreferenced parameters across 36 files.
* **Method/Class Size**: All methods remain under 30 lines, with complex AST parsing in `CalculatorTool` isolated into internal helper classes (`CalculatorTool::Evaluator`).
* **Coupling Between Layers**: `ChatsController` directly spawns unmanaged threads (`Thread.new`) to handle streaming responses, coupling request context lifecycle directly to raw Ruby thread execution rather than an abstraction like ActiveJob or a managed executor.

### Top 3 Refactoring Priorities

1. **Replace Raw `Thread.new` with Managed Async Execution / ActiveJob**:
   * *Location*: [app/controllers/chats_controller.rb#L67-L121](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/app/controllers/chats_controller.rb#L67-L121)
   * *Rationale*: Spawning raw, unmanaged threads per request under Puma causes worker thread leak hazards, skips Rails app executor context (`Rails.application.executor.wrap`), and lacks proper thread lifecycle tracking under process restarts.
2. **Implement Optimistic Locking / Lua Script in `ConversationStore`**:
   * *Location*: [app/services/conversation_store.rb#L87-L99](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/app/services/conversation_store.rb#L87-L99)
   * *Rationale*: `append_message` performs a non-atomic `find_or_create` (`redis.get`) followed by `save` (`redis.set`). Concurrent turns on the same conversation ID can race, causing turn overwrites. A Redis Lua script or `WATCH`/`MULTI` pipeline would guarantee atomic message appends.
3. **Clean Up Expired Entries from Redis Index Set (`INDEX_KEY`)**:
   * *Location*: [app/services/conversation_store.rb#L58-L64](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/app/services/conversation_store.rb#L58-L64)
   * *Rationale*: `INDEX_KEY` (`llm_chat:conversations`) stores conversation IDs in a Redis `SET`. When individual conversation keys expire after 24 hours via Redis TTL, their IDs remain in the `INDEX_KEY` set indefinitely. `ConversationStore.all` filters them out dynamically, but the Redis set size grows unbounded over time.

---

## 3. Test Coverage Assessment

### SimpleCov Coverage Summary
* **Line Coverage**: **86.51%** (295 of 341 relevant lines covered across `app/`).
* **Branch Coverage**: **Not Enabled** / **0% Tracked** in SimpleCov configuration ([test/test_helper.rb#L4](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/test/test_helper.rb#L4) runs `SimpleCov.start 'rails'` without `enable_coverage :branch`).

### Weakest-Tested Area
* **Background Thread Streaming in `ChatsController#message`**:
  * While `ChatsControllerTest` tests synchronous turbo stream response initialization, the execution of the asynchronous `Thread.new` block ([app/controllers/chats_controller.rb#L67-L121](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/app/controllers/chats_controller.rb#L67-L121)) and Action Cable Turbo Stream broadcasts (`Turbo::StreamsChannel.broadcast_update_to`) are exercised primarily via integration proof scripts (`script/test_streaming_proof.rb`) rather than unit/controller assertions in Minitest.

### Failure Modes NOT Covered by Unit Tests
1. **Redis Network Disconnection During Streaming**:
   * No unit test simulates a Redis connection failure or timeout occurring mid-stream while `Turbo::StreamsChannel.broadcast_update_to` is executing inside the background thread.
2. **Concurrent Request Mutations on Same Conversation**:
   * No unit test fires concurrent parallel requests to `ConversationStore.append_message` to verify atomic consistency under race conditions.
3. **Action Cable Client Disconnection**:
   * No unit test verifies behavior when a WebSocket client disconnects mid-stream while chunks are being generated by the LLM provider.
4. **Exponentiation Overflow in `CalculatorTool`**:
   * No test verifies behavior when evaluating nested high-exponent expressions (e.g. `9^9^9^9`), which could raise `FloatDomainError` or CPU lockups.

---

## 4. Known Defects and Risks

### Concurrency Hazards
* **Non-Atomic Read-Modify-Write in `ConversationStore`**:
  * `ConversationStore.append_message` loads the existing conversation Hash from Redis via `GET`, mutates the array in Ruby memory, and writes it back via `SET` ([app/services/conversation_store.rb#L87-L99](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/app/services/conversation_store.rb#L87-L99)). If two turns are submitted simultaneously for the same conversation ID, one turn may overwrite the other in Redis.
* **Unmanaged `Thread.new` Execution**:
  * `ChatsController#message` spawns raw `Thread.new` instances for streaming ([app/controllers/chats_controller.rb#L67](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/app/controllers/chats_controller.rb#L67)). Spawning threads outside `Rails.application.executor.wrap` bypasses Rails thread pooling, database connection management, and signal trapping during web server shutdown.

### Edge Cases & Operational Risks
* **Unbounded Redis `INDEX_KEY` Memory Growth**:
  * `ConversationStore.save` adds every conversation ID to a Redis `SET` named `llm_chat:conversations` ([app/services/conversation_store.rb#L79](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/app/services/conversation_store.rb#L79)). While individual conversation keys expire via TTL (`CONVERSATION_TTL_SECONDS`), the Redis `SET` entries are never removed unless `delete` or `clear_all` is called explicitly.
* **Token Estimation Inaccuracy**:
  * `LlmService.estimate_tokens` ([app/services/llm_service.rb#L166-L170](file:///mnt/data/Projects/llm-coding-benchmark/results-v2/v2_gemini_3_1_pro_agy/project/app/services/llm_service.rb#L166-L170)) uses a simplistic word count multiplier (`words * 1.3`) when the provider response object omits explicit `input_tokens` / `output_tokens`. This can lead to minor discrepancies in token budget enforcement under non-standard models or languages.
* **Lack of Rate Limiting on Message Endpoint**:
  * The `POST /chats/:id/message` endpoint has no request rate limiter or CAPTCHA, allowing malicious clients to flood OpenRouter API calls and exhaust the configured token budget or API key quotas.
