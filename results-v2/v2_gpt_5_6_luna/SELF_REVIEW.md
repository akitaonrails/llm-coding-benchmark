# Self-review

Review performed against the current workspace on 2026-07-29. No application-code fix was made in phase 3; only this review file was added.

## Goal verification table

| goal id | verdict | concrete evidence |
|---|---|---|
| G1 | PASS | `.ruby-version:1` is `ruby-4.0.6`; `Gemfile.lock:193` has Rails 8.1.3.1; `config/application.rb:5-9` requires Active Model, Controller, View, Cable, and test railties only. `rails runner` reported `active_record: nil, active_job: nil, action_mailer: nil`. |
| G2 | PARTIAL | Hotwire/Stimulus/Tailwind dependencies are in `Gemfile:11-16`, and the UI is split across `app/views/chat/**` plus `app/javascript/controllers/**`. However, a current `curl http://127.0.0.1:3000/` emitted only `/assets/application-8b441ae0.css`; that asset contains only the manifest comment, while the generated Tailwind file is `app/assets/builds/tailwind.css` and is not linked. |
| G3 | PASS | `Gemfile.lock:193,256` locks Rails 8.1.3.1 and ruby_llm 1.16.0; `config/initializers/ruby_llm.rb:3-10` configures OpenRouter and `anthropic/claude-sonnet-4.6`; `ChatConfiguration.model` is env-overridable at `app/services/chat_configuration.rb:11-13`. |
| G4 | PASS | `app/services/chat_turn_service.rb:64-69` publishes each non-empty provider chunk, and `app/services/chat_stream_publisher.rb:32-38` broadcasts each delta as a Turbo Stream append; `test/services/chat_stream_publisher_test.rb:24-42` asserts two separate deltas. Phase-2 runtime validation also recorded seven frames with two assistant-token appends. |
| G5 | PASS | `ChatTurnService#complete_turn` records `history_size` before `chat.ask` at `app/services/chat_turn_service.rb:62-70`; `test/services/chat_turn_service_test.rb:18-35` asserts the exact multi-turn outgoing array and one occurrence of the current prompt. |
| G6 | PARTIAL | SQLite WAL, `BEGIN IMMEDIATE`, busy timeout, caps, and TTL are implemented at `app/services/conversation_store.rb:49-64,115-126,213-239`; persistence/TTL tests are in `test/services/conversation_store_test.rb:17-58`. A current targeted run with `CHAT_BYTE_CAP=20` stored `stored_bytes=47 cap=20`, so the byte-cap invariant fails for an oversized first payload. |
| G7 | PARTIAL | Exactly `ServerTimeTool` and `CalculatorTool` are passed to RubyLLM at `app/services/chat_turn_service.rb:75-79`, and their names/behavior are tested in `test/services/chat_turn_service_test.rb:39-48` and `test/tools/*_test.rb`. The code only instructs the model to use tools; it does not require a tool choice, and no unit test asserts an actual provider tool invocation. |
| G8 | PASS | `app/services/chat_turn_service.rb:40,83-88` calls title generation only after the first accepted exchange and publishes the saved title; `app/services/conversation_title_generator.rb:5-35` uses a structured schema, covered by `test/services/conversation_title_generator_test.rb:4-23`. |
| G9 | PASS | `Turn#over_budget?` rejects before provider work at `app/services/conversation_store.rb:25-27` and the service alerts at `app/services/chat_turn_service.rb:28-31`; `test/services/chat_turn_service_test.rb:97-108` verifies no provider call for an over-budget prompt. |
| G10 | PASS | The system prompt is installed through `with_instructions` at `app/services/chat_turn_service.rb:75-78`; missing-key, provider-failure, and non-persistence paths are tested in `test/services/chat_turn_service_test.rb:67-95`, while the UI preflight is tested in `test/controllers/chat_controller_test.rb:17-34`. |
| G11 | PARTIAL | SimpleCov is enabled with branch coverage at `test/test_helper.rb:1-6`; the suite currently passes (`21 runs, 67 assertions, 0 failures`) but there are no JavaScript/browser tests, no direct `ChatConfiguration` or `ChatMessagesController` tests, and the fake provider does not model real tool-call turns. |
| G12 | PASS | Current commands succeeded: `bundle exec rubocop --format simple` reported `39 files inspected, no offenses detected`; Brakeman reported `Errors: 0` and `Security Warnings: 0`; `bundle exec bundle-audit check` reported `No vulnerabilities found`. |
| G13 | PASS | `Dockerfile:5-9,34-46` sets production mode, creates/uses non-root `app`, and has an entrypoint; `docker-compose.yml:1-26` defines the app, Redis, two workers, and durable SQLite volume. Current `docker build --check .` completed with no warnings, `docker compose config --quiet` passed, and the running compose app returned HTTP 200 on port 3300. |
| G14 | PASS | No authentication callbacks/routes are present (`config/routes.rb:1-7` and the controllers); API keys are read from `ENV` at `config/initializers/ruby_llm.rb:4` and a secret-shaped-literal scan returned no matches. The app is rooted in this workspace and the intentional no-auth demo posture is documented in the brief/README. |

## Code quality assessment

Names are generally descriptive (`ConversationStore`, `ChatTurnService`, `approx_tokens`, `bound_payloads`) and the main responsibilities have been given service objects instead of being put in controllers. The Rails views are reasonably componentized. RuboCop is clean, but that is not the same as low coupling or complete design quality.

The main structural problem is `app/services/conversation_store.rb:7-320`. It owns schema creation, SQLite connection setup, transaction/locking policy, TTL purging, snapshot reconstruction, RubyLLM message serialization, tool-call rehydration, UTF-8 truncation, and message/byte bounding. That is too many reasons to change in one class, and it couples the persistence layer directly to RubyLLM classes.

`app/services/chat_turn_service.rb:14-57` also coordinates input validation, API-key preflight, database transactions, provider calls, streaming, error UI, budgeting, and title generation. In particular, the provider network call is made while the store transaction is open. `ChatStreamPublisher` is a useful boundary, but its methods still hard-code view partial paths and repeat three broadcast wrappers (`app/services/chat_stream_publisher.rb:88-98`). `ConversationTitleGenerator` rescues all `StandardError` (`app/services/conversation_title_generator.rb:33-35`), which protects the turn but can hide programming errors.

There is dead/generated material: `app/javascript/controllers/hello_controller.js` is not used by the chat UI, and the PWA templates/routes remain disabled (`app/views/pwa/**`, `config/routes.rb:15-17`). The empty `app/assets/stylesheets/application.css` alongside the separately generated Tailwind output also makes asset ownership unclear and caused the missing stylesheet defect above.

Top three refactors with more time:

1. Split `ConversationStore` into a SQLite repository, a message codec/rehydrator, and a bounded-history policy. This would isolate RubyLLM coupling and make the cap and corruption cases independently testable.
2. Redesign `ChatTurnService`/persistence around a shorter transaction or explicit turn state. Holding a database-wide SQLite write lock across provider I/O is the largest coupling and operational risk.
3. Add an explicit asset/build boundary and remove unused generated controllers/PWA remnants; then add a browser-level adapter test for the actual stylesheet link, Turbo stream DOM updates, and reconnect behavior.

## Test coverage assessment

The current full run was:

```text
bundle exec rails test
21 runs, 67 assertions, 0 failures, 0 errors, 0 skips
Line coverage: 358 / 380 (94.21%)
Branch coverage: 70 / 109 (64.22%)
```

The weakest-tested area is the browser/runtime boundary: `app/javascript/**`, the actual asset pipeline, Action Cable Redis behavior, and Turbo DOM application have no tests. The Ruby fake in `test/support/fake_ruby_llm.rb` emits one ordinary assistant chunk and does not exercise provider tool-call messages, tool results, or streaming exceptions.

Failure modes not covered by any test include:

- Two simultaneous turns contending for SQLite, a busy-timeout failure, or a two-worker turn race.
- A provider failure after one or more chunks have already been published, or a Redis/broadcast failure or WebSocket reconnect during streaming.
- Actual RubyLLM tool selection/execution for a time request or calculation, rather than only tool registration and standalone tool behavior.
- A single payload whose metadata/content still exceeds the byte cap after `fit_payload`, including the reproduced `CHAT_BYTE_CAP=20` case.
- Malformed persisted JSON, malformed tool-call/thinking payloads, or an invalid conversation ID through the HTTP controller.
- JavaScript controller behavior, stylesheet inclusion, Docker/Compose health beyond the manually observed runtime, and title-schema rejection/invalid JSON responses.

## Known defects and risks

1. **Tailwind is built but not served.** `app/assets/builds/tailwind.css` contains the utility output, but the rendered page links only `application.css`, whose served content is the empty generated manifest. The UI therefore loses its intended Tailwind styling in the current runtime.
2. **The byte cap is not an invariant.** `bound_payloads` accepts the newest payload even when it alone exceeds the cap (`app/services/conversation_store.rb:218-226`), and `fit_payload` only truncates content to half the cap. The reproduced result was 47 stored serialized bytes for a 20-byte cap.
3. **Concurrent turns serialize behind provider I/O.** `BEGIN IMMEDIATE` starts at `app/services/conversation_store.rb:53`, and `chat.ask` runs inside that transaction via `app/services/chat_turn_service.rb:26-35,61-72`. The connection waits only 10 seconds (`conversation_store.rb:123-126`) while the provider timeout defaults to 300 seconds (`config/initializers/ruby_llm.rb:10`), so a second worker can fail a turn during a slow first request, even for another conversation.
4. **Tool use is advisory rather than enforced.** `with_tools(ServerTimeTool, CalculatorTool)` registers tools, but there is no required tool choice. A model can theoretically answer a time or arithmetic prompt without invoking the server tool; the current unit tests would not detect that.
5. **Streaming is not replayable.** If the browser loses its Action Cable subscription during a turn, broadcasts are not queued for that client. The completed history is persisted, but the current page must be reloaded to recover it.
6. **The demo has no conversation ownership.** This is intentional for G14, but a known conversation UUID can be supplied in the cookie/form and then read or written by another client. The cookie is a durable identifier, not an authentication boundary.
7. **TTL cleanup is request-driven.** Expired rows are purged only when `snapshot` or `with_turn` runs; there is no background cleanup. Under sustained creation of abandoned conversations, storage cleanup depends on later traffic.

