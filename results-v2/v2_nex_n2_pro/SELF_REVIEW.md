# SELF_REVIEW

Review-only fix made: I removed `tmp/local_secret.txt`, which contained a generated secret-like value and was not referenced by the application. No feature code was changed.

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence |
|---|---|---|
| G1 | PASS | `config/application.rb:5-15` requires `active_model`, `action_controller`, `action_cable`, and `action_view` while leaving `active_record`, `active_job`, and `action_mailer` commented out; `bin/rails runner 'puts({active_record: defined?(ActiveRecord), action_mailer: defined?(ActionMailer), active_job: defined?(ActiveJob), action_cable: defined?(ActionCable)})'` returned `{active_record: nil, action_mailer: nil, active_job: nil, action_cable: "constant"}`; `.ruby-version:1` is `ruby-4.0.6` and `bin/rails runner 'puts "Ruby #{RUBY_VERSION}; Rails #{Rails.version}"'` returned `Ruby 4.0.6; Rails 8.1.3`. |
| G2 | PASS | The SPA uses Tailwind in `app/assets/tailwind/application.css:1-11`, Turbo Streams in `app/views/chat/_title.html.erb:1` and `app/views/chat/create.turbo_stream.erb:1-4`, Stimulus in `app/javascript/controllers/chat_controller.js:1-22`, and partials such as `app/views/chat/_message.html.erb:1-16`, `_composer.html.erb:1-22`, `_status.html.erb:1-11`, and `_title.html.erb:1-13`; `grep` found no `fetch(` or `innerHTML` chat loop in `app`. |
| G3 | PASS | `Gemfile:24-25` uses `ruby_llm`; `Gemfile.lock:290-292` pins `ruby_llm (1.16.0)`, and `ruby -ropen-uri -rjson -e ...ruby_llm.json...` reported remote latest `1.16.0`; `config/initializers/ruby_llm.rb:1-7` configures OpenRouter API key/base/default model, and `app/services/chat_service.rb:44-45` exposes `OPENROUTER_CHAT_MODEL` override with default `anthropic/claude-sonnet-4.5`. |
| G4 | PASS | `app/services/chat_service.rb:73-79` calls `chat.ask(content) do |chunk|` and broadcasts each chunk with `stream_append`; the unit test `test/services/chat_service_test.rb:43-60` asserts incremental streams containing `Hel` and then `Hello`. RubyLLM confirms streaming callbacks are passed through in `ruby_llm/chat.rb:239-330` and OpenRouter includes streaming support in `ruby_llm/providers/openrouter/streaming.rb:5-33`. |
| G5 | PASS | `app/services/chat_service.rb:68-70` replays stored history before sending the current prompt; `test/services/chat_service_test.rb:18-40` asserts the exact outgoing message array for a multi-turn exchange is only the prior user/assistant messages, not the prompt about to send. |
| G6 | PARTIAL | `app/services/chat_store.rb:40-107` uses a file-backed JSON store with TTL, message cap, byte cap, and token budget; `test/services/chat_store_test.rb:64-82` checks concurrent in-process writes. However, the implementation writes `path.tmp` then renames it over `path` (`app/services/chat_store.rb:141-145`) while flocking the target file, which can allow new file descriptors to lock the new inode while older locks are on the old inode; I did not get a WEB_CONCURRENCY=2 runtime proof. |
| G7 | PARTIAL | `app/services/chat_service.rb:124-132` exposes exactly `ServerTimeTool` and `CalculatorTool` through RubyLLM's real `.with_tools` API, and `test/services/chat_service_test.rb:18-40` asserts the tool keys are `%i[calculator server_time]`; `CalculatorTool` and `ServerTimeTool` are tested in `test/services/tools/*`. I did not run a live provider conversation proving the model actually chooses those tools. |
| G8 | PASS | `app/services/chat_service.rb:198-205` calls `TitleGenerator` after the first assistant message, and `app/services/title_generator.rb:14-24` uses RubyLLM `.with_schema(ChatService::TITLE_SCHEMA)`; `test/services/title_generator_test.rb:15-27` verifies schema output and title persistence. |
| G9 | PARTIAL | `app/services/chat_service.rb:60-63` refuses before the budget is exceeded and returns `:budget_exceeded`; `test/services/chat_service_test.rb:62-85` verifies no provider call and no failed turn storage. Edge cases are not fully correct: `within_budget?` uses `<` rather than `<=` (`app/services/chat_store.rb:104-106`), and trimming old messages does not reduce accumulated `token_usage` (`app/services/chat_store.rb:67-74`, `184-209`). |
| G10 | PASS | `app/services/chat_service.rb:33-42` defines the system prompt and friendly errors; `app/services/chat_service.rb:60-70` preflights API key and budget; `app/services/chat_service.rb:111-120` rescues provider failures and renders degraded composer state; `test/services/chat_service_test.rb:87-128` covers missing API key and provider failure without storing failed turns. |
| G11 | PARTIAL | The suite has 16 Minitest tests across controller, services, tools, and views; `bin/rails test` passed with `16 runs, 59 assertions, 0 failures`. Mocks mirror real RubyLLM methods: `ruby -e ... RubyLLM::Tool.instance_methods ...` showed `:call`, `:execute`, `:name`, etc., and `RubyLLM.chat(...).methods` included `:with_instructions`, `:with_tools`, `:with_schema`, `:add_message`, and `:ask`. Coverage is incomplete: `app/controllers/chat_controller.rb:20-31` success path is not tested, and there are no JS/Stimulus tests. |
| G12 | PASS | `bin/rails test` passed; `bundle exec rubocop` reported `36 files inspected, no offenses detected`; `bundle exec brakeman -q` reported `Security Warnings: 0`; `bundle exec bundle audit check --update` reported `No vulnerabilities found`. |
| G13 | PASS | `Dockerfile:11-76` sets `RAILS_ENV=production`, uses a non-root `rails` user, and has an entrypoint; `docker-compose.yml:1-17` defines web plus Redis. `docker build -t ruby_llm_chat_selfreview .` completed successfully, and `SECRET_KEY_BASE=... OPENROUTER_API_KEY=dummy-key ... docker compose up -d --build` followed by `curl http://localhost:3000/` returned a page containing the chat shell. |
| G14 | PARTIAL | No auth code was found; `grep -R "devise\|has_secure\|authenticate_user\|before_action :authenticate" ...` found no auth implementation. No `.env*` or credential files were present, and `.dockerignore:10-21` excludes env/log/tmp files from images. However, `tmp/local_secret.txt` existed before review and was removed, and there is no `.gitignore`, so generated logs/tmp/coverage could be accidentally committed. |

## 2. CODE QUALITY ASSESSMENT

The codebase is compact and mostly readable, but several areas are doing too much.

- **Naming:** Names are generally clear: `ChatService`, `ChatStore`, `TitleGenerator`, `CalculatorTool`, and `ServerTimeTool` map to responsibilities. `ArithmeticEvaluator` is clear but hides parser/scanner classes inside one file (`app/services/arithmetic_evaluator.rb:29-156`).
- **Single responsibility:** `ChatService` is the main concern. At 230 lines (`wc -l app/services/chat_service.rb`), it mixes provider setup, streaming, rendering, token estimation, title generation, budget checks, error handling, and message construction (`app/services/chat_service.rb:60-230`). `ChatStore` is also broad at 217 lines, mixing JSON persistence, locking, TTL, caps, token accounting, and environment defaults (`app/services/chat_store.rb:1-217`).
- **Duplication:** `ChatService` and `TitleGenerator` both build OpenRouter RubyLLM chat objects (`app/services/chat_service.rb:124-132`, `app/services/title_generator.rb:14-24`). A small provider client would centralize model/config/schema behavior.
- **Dead code / unused artifacts:** `app/views/chat/create.html.erb:1-4` is an unused stock-style view; `app/javascript/controllers/hello_controller.js` is generated but unused; `jbuilder` and `kamal` are in the Gemfile but not used by the app.
- **Method/class size:** `ChatService#reply` is the largest behavior block and would benefit from extraction (`app/services/chat_service.rb:60-120`). `ArithmeticEvaluator` is acceptable for a tiny parser, but nested scanner/parser classes make it less approachable (`app/services/arithmetic_evaluator.rb:29-156`).
- **Coupling:** `ChatService` depends directly on RubyLLM, `ApplicationController.render`, Turbo stream helpers, `ChatStore`, and view partial names (`app/services/chat_service.rb:51-58`, `151-164`). This makes service tests possible but keeps the service tightly coupled to Rails rendering details.
- **Positive points:** The service-object split is better than putting chat logic in the controller; `ChatController` is small (`app/controllers/chat_controller.rb:1-33`). Partialized views keep the UI maintainable. Error paths are explicit rather than hidden.

Top 3 refactors with more time:

1. **Extract a RubyLLM client/provider adapter.** This would centralize OpenRouter config, model selection, tools, structured output, and streaming, reducing duplication between `ChatService` and `TitleGenerator`.
2. **Rewrite `ChatStore` persistence/locking.** Use a separate stable lock file or same-inode atomic write strategy, add fsync, validate env integers, and adjust token usage when capped messages are removed.
3. **Split `ChatService` into smaller collaborators.** Separate request orchestration, stream rendering, token budgeting, and title generation so the main reply flow is easier to test and reason about.

## 3. TEST COVERAGE ASSESSMENT

Command run: `bin/rails test`.

Result:

```text
16 runs, 59 assertions, 0 failures, 0 errors, 0 skips
Line coverage: 348 / 364 (95.60%)
Branch coverage: 56 / 81 (69.13%)
```

Weakest-tested area: controller success path and title/provider error branches. `app/controllers/chat_controller.rb:20-31` was the lowest line-coverage file from the SimpleCov data, and the controller tests only cover empty submit and index rendering (`test/controllers/chat_controller_test.rb:1-21`). `TitleGenerator` also has low branch coverage (`test/services/title_generator_test.rb:15-27` covers the happy path only).

Failure modes not covered by tests:

- Successful `ChatController#create` request and successful broadcast path.
- Live OpenRouter streaming, live tool invocation, and live structured-output behavior; current tests use `FakeChat`.
- Invalid title JSON, missing title field, and `TitleGenerator` rescue paths.
- `ChatStore` invalid/corrupt JSON, invalid integer env values, zero/negative caps, and multi-process lock/rename race behavior.
- Token budget edge case where usage equals the budget, and token usage after message/byte trimming.
- Stimulus controller behavior in a browser.
- Provider failure visible text in the rendered composer, not just the service status.
- Docker Compose live chat end-to-end with a real provider.

## 4. KNOWN DEFECTS AND RISKS

- **`ChatStore` file locking is fragile with rename.** `save` writes `path.tmp` and renames it over `path` (`app/services/chat_store.rb:141-145`) while flocking the opened target file. Across processes, new opens can lock the replacement inode while older locks are on the old inode, creating a real concurrency/corruption risk under multi-worker writes.
- **No fsync after persistence writes.** A process crash after rename could still lose recently written conversation data.
- **Token usage is not reduced when history is capped.** `append_exchange` increments `token_usage` (`app/services/chat_store.rb:67-74`) even when `enforce_caps!` later removes old messages (`app/services/chat_store.rb:184-209`), so budget can stay exceeded after the replay history is bounded.
- **Environment integer parsing is permissive.** `integer_env` uses `to_i`, so `CHAT_MAX_MESSAGES=abc` becomes `0` (`app/services/chat_store.rb:22-27`), likely trimming all messages.
- **Calculator parser limitations.** It only accepts ASCII spaces, digits, `.`, and `+ - * / ()`; tabs/newlines are rejected, unary minus is not supported, and numeric overflow/infinity behavior is not explicitly handled (`app/services/arithmetic_evaluator.rb:38-156`).
- **Title generation depends on `response.raw.body` parsing.** `TitleGenerator#raw_content` parses `response.raw.body` and rescues JSON errors (`app/services/title_generator.rb:36-44`); if RubyLLM normalizes structured output differently, title extraction can silently fail.
- **Broad provider rescue hides details.** `ChatService` rescues all `StandardError` and logs only the class (`app/services/chat_service.rb:111-120`), which is user-friendly but operationally thin.
- **No live provider validation in this review.** Streaming, tool calling, and structured output are supported by code and fakes, but I did not send a real chat through OpenRouter in this phase.
- **Compose environment interpolation can leak secrets in logs.** `docker compose config` prints interpolated environment values; during review, an unfiltered run exposed the host `OPENROUTER_API_KEY` in tool output. Rotate that key if it was a real credential. Use dummy values or redacted output when debugging compose.
- **No `.gitignore` in the workspace.** `.dockerignore` exists, but without `.gitignore`, logs, coverage, tmp files, and local generated files could be committed accidentally.
- **Unused/generated artifacts remain.** `app/views/chat/create.html.erb`, `hello_controller.js`, and unused gems increase surface area without providing value.
