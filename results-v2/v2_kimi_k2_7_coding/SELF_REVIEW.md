# Self-Review

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | PASS | `config/application.rb:6-15` comments out `active_record`, `action_mailer`, and `active_job` railties. `Gemfile:3` pins `rails, "~> 8.1.3"`. `.ruby-version` is `ruby-4.0.6`. Verified: `ruby --version` → `ruby 4.0.6`, `bin/rails --version` → `Rails 8.1.3`. |
| G2 | PASS | `app/views/conversations/show.html.erb:9` uses `turbo_stream_from`; messages and forms are rendered with partials (`app/views/messages/_message.html.erb`, `_form.html.erb`, `app/views/conversations/_title.html.erb`, `_sidebar.html.erb`). Tailwind is configured via `app/assets/tailwind/application.css:1` (`@import "tailwindcss"`). Turbo/Stimulus are wired in `app/javascript/application.js:2` and `app/javascript/controllers/index.js:3`. |
| G3 | PASS | `config/initializers/ruby_llm.rb:4-6` loads `openrouter_api_key` and `default_model` from env (`CHAT_MODEL`, default `claude-sonnet-4-6`). `app/services/chat_client.rb:11` creates `RubyLLM::Chat.new(..., provider: :openrouter)`. `test/services/chat_client_test.rb:36` confirms the resolved model id is `anthropic/claude-sonnet-4.6`. |
| G4 | PASS | `app/services/chat_service.rb:27-30` calls `stream_reply` and, for every chunk, appends to the assistant message and broadcasts a Turbo Stream `replace`. `app/services/chat_client.rb:23-25` yields each chunk as it arrives from the provider. |
| G5 | PASS | **Review fix applied:** the original implementation added the user message to the conversation before calling `stream_reply`, and `ChatClient` then called `chat.ask(content)`, which added the same prompt again. Current code: `app/services/chat_service.rb:20-22` creates/broadcasts the user message but does **not** persist it before streaming; `app/services/chat_service.rb:35-36` persists both user and assistant messages only after a successful reply; `app/services/chat_client.rb:23` uses `chat.ask(content)` to add the prompt exactly once. `test/services/chat_client_test.rb:43-67` asserts the outgoing history array excludes the prompt about to be sent. `test/services/chat_service_test.rb:48-62` and `test/services/chat_service_test.rb:102-112` verify correct persistence on success and no persistence on failure. `test/services/chat_service_test.rb:64-73` verifies the user message is broadcast immediately. |
| G6 | PASS | `app/services/conversation_store.rb:4-6` defines `TTL_SECONDS = 7.days`, `MAX_MESSAGES = 200`, `MAX_BYTES = 512.kilobytes`. Storage uses Redis (`@redis.setex` at line 23), not a process-local store. `test/services/conversation_store_test.rb:45-54` verifies restart survival. `test/services/conversation_store_test.rb:33-43` verifies message-count bounding. |
| G7 | PASS | `app/tools/server_time_tool.rb` and `app/tools/calculator_tool.rb` define the two required tools. `app/services/chat_client.rb:13` registers them with `.with_tools(ServerTimeTool, CalculatorTool)`. Tests in `test/tools/server_time_tool_test.rb` and `test/tools/calculator_tool_test.rb` exercise both. |
| G8 | PASS | `app/services/title_generator.rb:8-10` defines a `RubyLLM::Schema` with a `title` string. `app/services/chat_service.rb:67-73` generates the title only after the first complete exchange (`conversation.first_exchange_complete?`) and broadcasts a title replacement. `app/views/conversations/_title.html.erb` renders it. |
| G9 | PASS | `app/services/chat_service.rb:11` reads `TOKEN_BUDGET` (default 4000). `app/services/chat_service.rb:61-65` refuses further turns when `conversation.budget_exceeded?(@budget)` is true. The refusal message is broadcast via `broadcast_error` (`app/services/chat_service.rb:46`). Limitation: only assistant-message tokens are tracked; see §4. |
| G10 | PASS | System instruction is set via `RubyLLM::Chat.with_instructions(ChatClient::SYSTEM_INSTRUCTION)` (`app/services/chat_client.rb:4,12`). Missing-key preflight is `app/services/chat_service.rb:55-59`. Provider failures are rescued in `app/services/chat_client.rb:27-28` and `app/services/chat_service.rb:48-50`, broadcasting `shared/error`. After the review fix, failed turns are not persisted (`test/services/chat_service_test.rb:102-112`). |
| G11 | PASS | 43 tests, 93 assertions, 0 failures, 0 errors (`bin/rake test`). `test/test_helper.rb:3-9` wires SimpleCov with branch coverage enabled. `coverage/index.html` is generated. Mocks mirror RubyLLM APIs (`RubyLLM::Chat#ask`, `#with_tools`, `#with_schema`, etc.). |
| G12 | PASS | `bin/rubocop` → 46 files inspected, no offenses. `bin/brakeman -q -w2` → 0 security warnings. `bin/bundler-audit` → no vulnerabilities. |
| G13 | PASS | `Dockerfile` sets `RAILS_ENV=production`, uses a non-root user (`USER 1000:1000`), and defines `ENTRYPOINT ["/rails/bin/docker-entrypoint"]`. `docker-compose.yml` provides `redis` and `web` services. `README.md` documents setup, local run, tests, Docker, and quality gates. `docker build -t chat-app-review .` completed successfully. |
| G14 | PASS | No authentication layer is implemented. Secrets are not committed: `config/initializers/ruby_llm.rb:4` reads `OPENROUTER_API_KEY` from env; README shows a placeholder. `credentials.yml.enc` is an encrypted Rails credential file, not a plain-text secret. All code is inside the workspace. |

## 2. Code Quality Assessment

The codebase is small and readable, but several areas violate clean-code principles:

- **Mixed responsibilities in `ChatService`**. `app/services/chat_service.rb:15-51` validates API keys/budgets, broadcasts UI updates, streams from the provider, persists messages, and generates titles. At 37 lines it is not huge, but it coordinates four distinct concerns. A future refactor would split persistence, broadcasting, and title-generation into focused collaborators.
- **`SafeCalculator` uses `Kernel.eval`.** `app/services/safe_calculator.rb:18` validates tokens first, but `eval` is still a latent security hazard and a code smell. If the token whitelist ever drifts, arbitrary Ruby execution becomes possible. A hand-written parser or a dedicated arithmetic gem would be safer and clearer.
- **Inefficient byte trimming.** `app/services/conversation_store.rb:49-52` calls `conversation.to_h.to_json` inside a `while` loop. This is `O(n²)` in message count and could be a hot path under memory pressure.
- **Duplication in broadcast helpers.** `app/services/chat_service.rb:75-104` has three near-identical wrappers around `broadcast_action_to`. They could collapse into a single helper with sensible defaults.
- **Boilerplate in models.** `app/models/conversation.rb` and `app/models/message.rb` include `ActiveModel::Conversion` and re-implement `model_name` solely to satisfy Rails form/partial helpers. This is necessary but noisy.

**Top 3 refactor targets with more time:**

1. **Replace `SafeCalculator.evaluate` with a real parser.** Reason: remove `Kernel.eval` entirely; the current "validate then eval" pattern is fragile and hard to audit.
2. **Decompose `ChatService`.** Reason: separate streaming orchestration, persistence, and broadcasting so each class has one reason to change and can be tested in isolation without heavy stubbing.
3. **Make `ConversationStore#trim!` efficient and atomic.** Reason: avoid repeated JSON serialization; consider using Redis data structures or a single bounded serialization pass, and add a test for byte-size trimming (currently only count trimming is tested).

## 3. Test Coverage Assessment

Ran `REDIS_URL=redis://localhost:6380/0 bin/rake test`:

- **Line coverage:** 251 / 263 (95.43%)
- **Branch coverage:** 22 / 36 (61.11%)

Branch coverage was enabled during this review by adding `enable_coverage :branch` to `test/test_helper.rb:5`.

**Weakest-tested area:** `app/services/chat_service.rb` error/branch paths and `app/services/conversation_store.rb` byte-size trimming. The happy path is well covered; failure branches, early returns, and trimming edge cases are not.

**Failure modes NOT covered by any test:**

- Redis unavailable at read/write time (connection errors are not rescued).
- Concurrent updates to the same conversation (race between read and save).
- Actual provider streaming failure mid-response (tests stub a single error, not a partial stream followed by failure).
- `TitleGenerator` returning a non-Hash string or malformed Hash after all retries.
- `ConversationStore#trim!` byte-size cap (only message-count cap is tested).
- `SafeCalculator` bypass attempts or very long expressions.
- Missing/empty `SECRET_KEY_BASE` causing production boot failure in Docker.

## 4. Known Defects and Risks

1. **User-message token counts are zero.** `app/models/message.rb:29` computes `tokens` as `input_tokens + output_tokens`, but user messages are created without token values, so they contribute `0` to `conversation.total_tokens`. The budget is therefore based almost entirely on assistant-message tokens and lags real usage by one turn.
2. **Title-generation tokens are not tracked.** `app/services/title_generator.rb:21` makes an additional provider call whose tokens are never added to the conversation budget.
3. **Concurrent conversation updates can lose messages.** `ConversationStore#find` reads the whole conversation, `ChatService` appends in memory, and `ConversationStore#save` writes the whole JSON back with `setex`. Two workers processing messages for the same conversation simultaneously can overwrite each other.
4. **`SafeCalculator` relies on `Kernel.eval`.** Even with token whitelisting, this is a latent code-injection risk and should be replaced.
5. **Failed assistant placeholders linger in the UI.** On a provider error, `broadcast_append` has already added an empty assistant placeholder; `broadcast_error` only appends an error message, leaving the placeholder visible.
6. **Auto-scroll is not implemented.** `app/views/messages/_message.html.erb` receives a `scroll` local in the final replace, but no controller or Stimulus action scrolls the message list when new content arrives.
7. **Docker Compose requires `SECRET_KEY_BASE`.** `docker-compose.yml:30` passes `${SECRET_KEY_BASE}` verbatim; if unset, the web container starts with an empty secret and Rails production boot fails.
8. **Redis connection failures are unhandled.** If Redis is unreachable, requests fail with raw exceptions rather than a degraded UI state.
