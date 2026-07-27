# Self Review

No code changes were made during this review.

## Goal Verification Table

| Goal | Verdict | Evidence |
| --- | --- | --- |
| G1 | PASS | `ruby -v && bundle exec rails -v` returned `ruby 4.0.6` and `Rails 8.1.3`; `config/application.rb:5-15` excludes Active Record, Active Job, and Action Mailer. |
| G2 | PASS | `app/views/conversations/show.html.erb:3-4`, `app/views/conversations/_shell.html.erb:29-46`, `app/views/messages/_form.html.erb:1-18`, `app/javascript/controllers/composer_controller.js:1-38`, and `app/assets/tailwind/application.css:1-31` show Tailwind + Hotwire + partialized UI; `rg -n "fetch\\(|innerHTML" app/javascript app/views -S` returned no matches. |
| G3 | PASS | `Gemfile.lock:277,454` pins `ruby_llm 1.16.0`; `config/initializers/ruby_llm.rb:8-11` configures OpenRouter and defaults to `~anthropic/claude-sonnet-latest`; on 2026-07-27 I re-checked that RubyGems still lists `1.16.0` as latest and OpenRouter's alias still points at the latest Sonnet family model. |
| G4 | PARTIAL | `app/services/chat/processor.rb:48-57` emits per-chunk updates through `app/services/chat/broadcaster.rb:16-24`; a one-off command using a fake two-chunk response printed `2` `message_bodies` updates, but I did not re-run a live browser/provider streaming session in phase 3. |
| G5 | PASS | `app/models/chat/conversation.rb:32-34` replays only replayable history, `app/services/chat/processor.rb:19-25,48-57` sends prior history then calls `chat.ask(user_message.content)` once, and `test/services/chat/processor_test.rb:15-59` asserts the exact outgoing multi-turn message array. |
| G6 | PARTIAL | `test/services/chat/file_store_test.rb:13-33,46-67,70-112` proves reload persistence, message-count pruning, TTL expiry, and forked writers; `app/services/chat/file_store.rb:110-152,211-244` implements file locking and byte trimming, but byte-cap branches are untested and `app/controllers/messages_controller.rb:3-17` checks `streaming?` outside the store lock. |
| G7 | PARTIAL | `app/services/chat/processor.rb:94-95` exposes exactly `ServerTime` and `Calculator`; `test/services/chat/tool_choice_test.rb:4-13`, `test/tools/server_time_test.rb:4-9`, and `test/tools/calculator_test.rb:4-7` cover selection and tool classes, but there is no end-to-end test proving a real assistant reply came from a RubyLLM tool call. |
| G8 | PASS | `app/services/chat/title_generator.rb:9-27` uses `with_schema(Chat::TitleSchema)` after the first completed exchange and updates the header rendered by `app/views/conversations/_header.html.erb:4`; `test/services/chat/title_generator_test.rb:15-36` covers the happy path. |
| G9 | PASS | `app/controllers/messages_controller.rb:10-12` refuses over-budget turns before async work starts, `app/services/chat/token_estimator.rb:15-22` computes projected usage, and `test/controllers/messages_controller_test.rb:15-31` gets `422` with `token budget` in the response. |
| G10 | PASS | `app/services/chat/settings.rb:66-84` defines the system prompt and missing-key message; `app/controllers/messages_controller.rb:6-8` does the preflight; `app/services/chat/processor.rb:81-115` and `app/services/chat/file_store.rb:183-201` mark failed turns non-replayable and surface degraded UI; `test/services/chat/processor_test.rb:62-85` verifies failed turns stay out of replay history. |
| G11 | PARTIAL | `test/test_helper.rb:1-6` wires SimpleCov branch coverage and the suite currently passes (`bundle exec rails test` => `33 runs, 96 assertions, 0 failures, 0 errors`), but coverage is only `91.98%` lines / `66.44%` branches and `coverage/coverage.json` shows weakly tested components such as `app/services/chat/error_message.rb` at `53.85%` line / `16.67%` branch coverage. |
| G12 | PASS | Current checks are clean: `bundle exec rails test` => `33 runs, 0 failures`; `bin/rubocop` => `59 files inspected, no offenses detected`; `bin/brakeman --no-pager` => `Security Warnings: 0`; `bin/bundler-audit check --update` => `No vulnerabilities found`. |
| G13 | PASS | `Dockerfile:8-14,41-58` sets `RAILS_ENV=production`, runs as non-root `rails`, and uses `bin/docker-entrypoint:1-7`; `HOST_PORT=3200 docker compose up --build -d` followed by `curl -I http://127.0.0.1:3200/` and `curl -i http://127.0.0.1:3200/up` both returned `HTTP/1.1 200 OK`; `README.md:43-83` documents setup and run. |
| G14 | PASS | `rg -n "authenticate|devise|has_secure_password|before_action .*auth|current_user|session\\[:user_id\\]" app config test -S` returned no matches, and the secret scan only found env-var references and documentation (`docker-compose.yml:8`, `README.md:22`, `config/initializers/ruby_llm.rb:4`). |

## Code Quality Assessment

The codebase is generally readable. Naming is clear and domain-specific in most places: `Chat::FileStore`, `Chat::Processor`, `Chat::TokenEstimator`, `Chat::ToolChoice`, and the partial names all describe their roles directly. The UI is well componentized for a small Rails app, especially `app/views/conversations/_shell.html.erb`, `app/views/conversations/_header.html.erb`, `app/views/messages/_message.html.erb`, and `app/views/messages/_form.html.erb`.

The main quality issue is responsibility concentration in the service layer. `app/services/chat/processor.rb:13-115` orchestrates provider setup, prompt replay, tool-status UX, token streaming, usage accounting, persistence finalization, header updates, and error handling. `app/services/chat/file_store.rb:12-259` combines locking, JSON persistence, TTL refresh, stale-stream repair, replay filtering, pruning, and byte trimming. Both classes are still understandable, but they are the places where future changes are most likely to introduce regressions.

Duplication is low, but there is some abstraction leakage. `app/services/chat/settings.rb:22-24,62-64` exposes `request_timeout` and `openrouter_api_base`, while `config/initializers/ruby_llm.rb:4-11` reads the raw ENV values directly instead of going through `Chat::Settings`; that makes the settings object slightly less authoritative than it looks. I did not find obvious dead product code, but some branches are effectively "dead to tests" rather than dead at runtime, especially in `app/services/chat/error_message.rb:5-24`.

Coupling between layers is moderate to high. `MessagesController` knows about persistence and async orchestration details (`app/controllers/messages_controller.rb:14-28`), and `Chat::Processor` knows about both provider behavior and Turbo broadcast presentation (`app/services/chat/processor.rb:27-57,77-115`). That is acceptable for a small app, but it narrows the margin for concurrency and error-handling mistakes.

Top 3 refactors with more time:

- Move the "only one streaming turn per conversation" invariant into the persistence/service boundary instead of checking it in `MessagesController#create` before `prepare_turn`. Right now the guard is not atomic (`app/controllers/messages_controller.rb:3-17` vs. `app/services/chat/file_store.rb:20-58`), which is both a quality issue and a real race.
- Split `Chat::FileStore` into smaller units: storage/serialization, retention policy, and stale-stream recovery. That would make `app/services/chat/file_store.rb:110-244` easier to reason about and much easier to test branch-by-branch.
- Split `Chat::Processor` into a chat-session builder/stream runner and a completion/failure finalizer. That would reduce coupling to both `RubyLLM` and `Turbo::StreamsChannel`, and it would make tool-callback and failure-path tests more focused than the current large orchestration test.

## Test Coverage Assessment

Actual SimpleCov result from the last suite run is:

- Line coverage: `91.98%`
- Branch coverage: `66.44%`
- Source: `coverage/.last_run.json:1-5`

The weakest-tested area is provider/title error handling rather than the happy-path chat flow. `coverage/coverage.json` shows:

- `app/services/chat/error_message.rb`: `53.85%` line coverage, `16.67%` branch coverage
- `app/services/chat/title_generator.rb`: `89.29%` line coverage, `50.00%` branch coverage
- `app/services/chat/processor.rb`: `90.20%` line coverage, `50.00%` branch coverage

Failure modes not covered by any test:

- Unauthorized, forbidden, context-length, model-not-found, and generic provider branches in `app/services/chat/error_message.rb:7-18`
- Title-generation rescue and warning broadcast path in `app/services/chat/title_generator.rb:28-34`
- Non-Hash schema response path in `app/services/chat/title_generator.rb:45-49`
- Tool callback UX (`before_tool_call` / `after_tool_result`) in `app/services/chat/processor.rb:27-45`
- Real Turbo broadcast integration in `app/services/chat/broadcaster.rb:3-56`; current tests use `TestSupport::FakeBroadcaster`
- Byte-cap trimming, corrupted JSON recovery, and stale-stream repair in `app/services/chat/file_store.rb:124-133,171-180,228-244`
- A same-session concurrent POST race through `MessagesController#create`; there is no test for two overlapping submits hitting `app/controllers/messages_controller.rb:3-28`

## Known Defects And Risks

- The single-reply guard is racy. `MessagesController#create` checks `@conversation.streaming?` before `prepare_turn` (`app/controllers/messages_controller.rb:3-17`), but `prepare_turn` does not enforce that invariant inside the lock (`app/services/chat/file_store.rb:20-58`). Two near-simultaneous requests from the same session can both queue a turn.
- Background work is unbounded and ephemeral. `Chat::AsyncRunner.start!` spawns a raw `Thread.new` for every message (`app/services/chat/async_runner.rb:3-10`). There is no queue, retry, or back-pressure, and a worker crash loses the in-flight reply until stale-stream repair runs on a later fetch.
- Corrupted conversation JSON is treated as an empty conversation. `Chat::FileStore#load_conversation` rescues `JSON::ParserError` by returning `fresh_conversation` (`app/services/chat/file_store.rb:124-133`), which avoids a crash but silently drops the prior history for that conversation.
- Title generation is effectively one-shot. `Chat::Processor` only triggers `@title_generator.call` when `completed_turns == 1` (`app/services/chat/processor.rb:80`), so if the first title request fails, later turns do not retry and the conversation can stay untitled permanently.
- Multi-worker streaming depends on Redis being configured. `config/cable.yml:1-14` uses the in-process `async` adapter in development when `REDIS_URL` is absent, and `README.md:56-57` explicitly warns that multi-worker streaming needs Redis. Running `WEB_CONCURRENCY=2` in development without Redis is fragile.
- Test strength is uneven around robustness features. The happy path is fairly well covered, but the low coverage in `app/services/chat/error_message.rb`, `app/services/chat/title_generator.rb`, and the uncovered branches in `app/services/chat/file_store.rb` mean regressions in degraded-mode behavior are more likely than the overall `91.98%` line number suggests.
