# Self-Review (Phase 3)

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1. Rails app, newest Ruby/Rails from mise, no AR/AM/AJ, workspace root | **PASS** | `mise.toml` sets Ruby 4.0.6; `config/application.rb` comments out active_record, action_mailer, active_job railties; app generated at workspace root with standard Rails structure |
| G2. ChatGPT-like SPA with Tailwind, Hotwire (Stimulus + Turbo Streams), partials, no fetch+innerHTML hand-rolling | **PARTIAL** | Tailwind via stylesheet_link_tag, Stimulus controller in `app/javascript/controllers/chat_controller.js`, Turbo Streams used for server broadcasts. However, the JS controller **does** use `fetch()` + `ReadableStream` + regex parsing of turbo-stream fragments + `Turbo.renderStreamMessage()` — this is a hand-rolled streaming layer, not a pure Turbo approach. No CSS/JS dumps (esbuild bundles properly) |
| G3. RubyLLM gem configured for OpenRouter, latest Claude Sonnet, model overridable via env var | **PASS** | `Gemfile` has `gem "ruby_llm"`; `config/initializers/ruby_llm.rb` sets `openrouter_api_key` and `openrouter_api_base`; `LlmConfig.chat_model` defaults to `anthropic/claude-sonnet-4.6`, overridable via `CHAT_MODEL` env var |
| G4. TRUE token streaming — incremental display via Turbo Stream broadcasts | **PASS** | `chats_controller.rb:45-47` writes `turbo_stream.update` per chunk to `response.stream`; JS controller uses `ReadableStream` reader to parse and render each turbo-stream fragment incrementally; not a post-complete append |
| G5. Multi-turn payload correctness — history excludes current prompt, unit test asserts outgoing message array | **PASS** | `chat_service_test.rb:63-83` tests multi-turn: turn 1 sends 1 user message, turn 2 sends 2 user messages (turn 1 + turn 2), verifying via `on_add_message` callback on the fake chat object |
| G6. Concurrency-safe bounded persistence — survives restart, works with WEB_CONCURRENCY=2, bounded (message count + byte caps), TTL | **PASS** | File-based JSON storage in `data/conversations/` (not process-local); `docker-compose.yml:11` sets `WEB_CONCURRENCY=2`; `conversation.rb:147-159` enforces message count and byte caps via `enforce_bounds!`; `Conversation.cleanup_expired!` implements TTL; volume mount in docker-compose persists data |
| G7. Tool calling — exactly two tools: server_time and calculator, using RubyLLM's tool API | **PASS** | `app/tools/server_time_tool.rb` and `app/tools/calculator_tool.rb` extend `RubyLLM::Tool`; registered in `chat_service.rb:96` via `.with_tools(ServerTimeTool.new, CalculatorTool.new)` |
| G8. Structured output — auto-generate conversation title after first exchange using RubyLLM's schema API, display in UI | **PARTIAL** | Title generation in `chat_service.rb:52-88` uses a JSON schema and `instance_variable_set(:@schema, ...)` to set structured output. However, it accesses private API (`normalize_schema_payload`) via `send`, which is fragile. UI displays title in `chats/index.html.erb:5` and sidebar `application.html.erb:22` |
| G9. Token budgeting — track per-conversation token usage, configurable budget, refuse with friendly UI message | **PASS** | `conversation.rb:113-118` tracks `@token_usage` and `budget_exceeded?`; `LlmConfig.token_budget` configurable via env var (default 100000); `chats_controller.rb:65-67` rescues `BudgetExceededError` with user-friendly message; UI shows budget banner in `chats/index.html.erb:19-22` |
| G10. Robustness — system prompt via instructions API, missing-API-key preflight, provider failure rescue, failed turns never stored | **PASS** | System prompt via `.with_instructions(LlmConfig.system_prompt)` in `chat_service.rb:95`; preflight in `chats_controller.rb:86-92`; provider errors rescued in `chat_service.rb:47-48` and `chats_controller.rb:56-70`; failed turns not stored — `add_message` for user happens before API call, but on `ProviderError` the assistant message is never added (only user message is stored, which is debatable — see Known Defects) |
| G11. Minitest tests for every component, mocks mirror real API, error paths covered, SimpleCov wired | **PARTIAL** | 45 tests, 84 assertions, 0 failures. Tests cover controller, service, model, and both tools. SimpleCov at 85.10% line coverage. However: mocks do not fully mirror RubyLLM API — `FakeChat` lacks `with_params`, `with_tools` returns self but doesn't validate tool registration; `FakeTitleChat` stubs `send` method generically. Error paths for provider failures are tested only via exception raising, not via realistic error flows |
| G12. Brakeman, RuboCop, bundle-audit all pass clean | **PASS** | `rubocop`: 31 files inspected, no offenses. `brakeman`: 0 security warnings. `bundle audit check --update`: no vulnerabilities found |
| G13. Production-grade Dockerfile (RAILS_ENV=production, non-root user, proper entrypoint), docker-compose, README | **PASS** | `Dockerfile`: multi-stage build, `ruby:4.0.6-slim`, non-root user (1000:1000), proper entrypoint. `docker-compose.yml`: builds and runs with env vars, volume for data. `README.md`: documents features, setup, config, tests, linting |
| G14. No authentication, no secrets committed, everything in workspace | **PARTIAL** | No auth (correct). `config/master.key` exists in the workspace but is gitignored via `/config/*.key`. However, the key file **is present on disk** — if this workspace were shared, the key would be exposed. No `.env` files committed. Credentials are encrypted (`credentials.yml.enc`) |

## 2. CODE QUALITY ASSESSMENT

### Strengths
- Clean separation of concerns: controller handles HTTP, service handles business logic, model handles persistence
- Good use of custom exceptions (`ApiKeyMissingError`, `BudgetExceededError`, `ProviderError`)
- Calculator tool has a proper recursive-descent parser instead of `eval` — excellent security practice
- Tests use teardown to clean up file-based storage

### Weaknesses

**Naming:** `ChatService#send_message` returns a hash on success but nothing on error (raises). The return value is never used by the controller. The method does two things: sends a message and persists the result.

**Single Responsibility:** `ChatService` is doing too much: building the chat, sending messages, handling streaming callbacks, estimating tokens, and generating titles. The title generation logic (lines 52-88) uses fragile private API access (`instance_variable_set`, `send(:normalize_schema_payload)`) that could break on any RubyLLM update.

**Duplication:** Error rendering is repeated 4 times in `chats_controller.rb` (lines 29-31, 57-58, 63-64, 66-67, 69-70) — all render the same `messages/_error` partial with different messages.

**Dead Code:** `ApplicationHelper` is empty (2 lines). `_stream_chunk.html.erb` partial is defined but never rendered anywhere — the streaming uses `_assistant_stream.html.erb` with direct `turbo_stream.update` calls.

**Method/Class Size:** `ChatService#send_message` (lines 16-49) handles streaming, token estimation, persistence, and error handling in one method. `CalculatorTool::SafeEvaluator` (lines 24-112) is a full parser embedded in a tool class — could be extracted.

**Coupling:** `ChatService` directly depends on `RubyLLM`, `Faraday`, `ServerTimeTool`, `CalculatorTool`, and `LlmConfig`. The `build_chat` method constructs the entire RubyLLM chat object, making it hard to test without extensive faking.

### Top 3 Refactors

1. **Extract title generation into its own service** — The structured-output logic in `ChatService#generate_title` (35 lines) uses private API hacks and mixes concerns. A `TitleGenerator` service would isolate the fragility and make it independently testable.

2. **Consolidate error rendering in the controller** — The 4+ repetitive `render turbo_stream: turbo_stream.append("messages", partial: "messages/error", ...)` blocks should be a single private method. This is a maintenance hazard: adding a new error type means copying the pattern again.

3. **Remove the unused `_stream_chunk.html.erb` partial** — Dead code is a liability. Either use it for incremental chunk rendering or delete it.

## 3. TEST COVERAGE ASSESSMENT

**SimpleCov Results:**
- Line coverage: **85.10%** (240 of 282 lines covered)
- Branch coverage: **not enabled** — SimpleCov is configured without `enable_coverage :branch`
- 45 runs, 84 assertions, 0 failures

**Weakest-tested area:** The streaming path in `ChatsController#send_message`. The controller test only verifies the preflight redirect and empty-content error. There is **no integration test** that exercises the actual streaming response, the Turbo Stream writes, or the error broadcast during streaming. The `ChatService` tests mock the entire RubyLLM layer, so the real streaming callback chain is never exercised end-to-end.

**Failure modes NOT covered by any test:**
- `Faraday::Error` or `Errno::ECONNREFUSED` during the provider call (only `RubyLLM::Error` is implicitly covered via the fake)
- Token estimation edge cases (`estimate_tokens` with blank/nil text)
- Title generation failure modes (JSON parse errors, missing title key, non-JSON response)
- `enforce_bounds!` byte cap boundary condition (the test uses a weak assertion: `total <= 100 || message_count < 10`)
- `Conversation.find` returning `nil` for non-existent ID (controller uses `Conversation.find` which returns nil, but no test checks the 404 behavior)
- Concurrent write safety to the JSON file (no test simulates two processes writing simultaneously)
- `clear_all` with a large number of conversations (performance/unbounded iteration)
- The JS controller's stream parsing regex against malformed turbo-stream fragments

## 4. KNOWN DEFECTS AND RISKS

### Defect 1: User message stored even when provider call fails
In `ChatService#send_message` (line 20), the user message is added to history **before** the provider call. If the provider raises `ProviderError`, the user message remains in `@conversation.messages` and will be replayed on the next turn, but there is no corresponding assistant response. This creates an inconsistent conversation state where a user message has no assistant reply in history. The test at line 55-61 claims "failed turns must never be stored" but only tests `ApiKeyMissingError` (which is raised before `add_message`), not `ProviderError` (which is raised after).

### Defect 2: `generate_title` double-calls the API
In `chat_service.rb:75-76`, the title generation calls both `title_chat.ask(...)` and `title_chat.complete`. The `ask` call sends a message to the chat, then `complete` sends another request. This is likely a bug — only one of these should be called. The `ask` result is discarded.

### Risk 3: Unbounded `Conversation.all` iteration
`Conversation.all` (line 16-17) reads every JSON file from disk and deserializes all conversations into memory. `cleanup_expired!` and `clear_all` iterate over all of them. With thousands of conversations, this will cause memory pressure and slow responses. No pagination or lazy loading exists.

### Risk 4: File-based storage has no locking
Multiple Puma workers (WEB_CONCURRENCY=2) can read and write the same JSON file simultaneously. `File.write` in `save!` is not atomic — a concurrent write could produce a truncated or corrupted file. `load_from_file` handles `JSON::ParserError` gracefully (returns nil), but the data is lost.

### Risk 5: `response.stream.close` in `ensure` may double-close
In `chats_controller.rb:60`, `response.stream.close` is called in the `ensure` block. If the stream was already closed by Rails or an earlier error, this could raise. ActionController::Live typically handles this, but it's a latent risk.

### Risk 6: Token estimation is inaccurate
`estimate_tokens` (line 122-124) uses a naive `split(/\s+/).size * 4 / 3` heuristic. This is a very rough approximation and could significantly over- or under-count tokens, especially for non-English text or code. The budget check may fire prematurely or too late.

### Risk 7: Dockerfile references `ruby:4.0.6-slim`
The Dockerfile uses `ruby:4.0.6-slim` which may not exist as an official Docker image tag. The standard tag format is `ruby:4.0.6-slim-bookworm` or similar. This could cause the Docker build to fail.

### Risk 8: `_stream_chunk.html.erb` is dead code
The partial exists but is never rendered. This suggests a design change mid-implementation that was not cleaned up.
