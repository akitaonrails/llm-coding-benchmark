# Self-review

## Goal verification

| Goal | Verdict | Concrete evidence |
| --- | --- | --- |
| G1 | PASS | `mise current ruby` reported `4.0.6`; `bundle exec rails --version` reported `Rails 8.1.3.1` (both current remote stable releases), and `config/application.rb:3-15` omits Active Record, Active Job, and Action Mailer. |
| G2 | PASS | `app/views/conversations/show.html.erb:1-24` subscribes with `turbo_stream_from` and composes partials; `app/javascript/controllers/chat_form_controller.js:1-16` is a focused Stimulus controller; `app/assets/tailwind/application.css:1-4` is Tailwind-only and no application `fetch()`/`innerHTML` implementation exists. |
| G3 | PASS | `Gemfile:62` resolves to `ruby_llm` 1.16.0 (confirmed by `gem list --remote --exact ruby_llm --all`); `config/initializers/ruby_llm.rb:3-6` configures OpenRouter and the env-overridable `anthropic/claude-sonnet-4.6` default. |
| G4 | PASS | `ChatApp::ChatTurnTest#test_streams_incrementally_persists_only_after_success_and_titles_the_first_exchange` asserts `Hel` then `Hello`; the path is `chat_client.rb:25-27` → `chat_turn.rb:41-43` → `response_broadcaster.rb:11-12,58-64`, which broadcasts each yielded chunk through Turbo Streams. |
| G5 | PASS | `ChatApp::ChatClientTest#test_sends_every_persisted_turn_once_and_appends_the_pending_prompt_once` asserts the exact system/user/assistant/user outgoing array; `chat_client.rb:30-35` replays only history and `:25-27` adds the pending prompt once. |
| G6 | PASS | Redis is the source of truth with expiry, bounded messages, WATCH/MULTI, and a lock in `conversation_store.rb:21-25,55-85` and `conversation.rb:97-117`; `compose.yml:20-22` sets `WEB_CONCURRENCY: 2`, and a current `docker compose ... up --build -d` check returned HTTP 200 from `/up`. |
| G7 | PASS | `chat_client.rb:38-40` registers only `ServerTimeTool` and `CalculatorTool`, `server_time_tool.rb:3-9` returns UTC ISO-8601, and `calculator_tool.rb:3-12` uses `SafeCalculator` rather than `eval`; the real RubyLLM chat test asserts the two tool names and forced choices. |
| G8 | PASS | After the first successful exchange, `chat_turn.rb:40,54-55` calls `TitleGenerator`; `title_generator.rb:22-26` uses `with_schema`, and `ChatApp::TitleGeneratorTest#test_uses_ruby_llms_with_schema_api_to_generate_a_title` verifies the schema/provider path. |
| G9 | PASS | `chat_turn.rb:37` refuses a turn at the configurable budget set in `:9-12`; `ChatApp::ChatTurnTest#test_refuses_a_turn_already_over_budget_without_contacting_the_provider` asserts no provider call and a user-facing failure. |
| G10 | PASS | The system instructions and tools are configured in `chat_client.rb:7-12,30-34`; key preflight and provider rescue are in `chat_turn.rb:28,57-61`, with covered missing-key and provider-failure tests at `chat_turn_test.rb:149-205`. |
| G11 | PARTIAL | `bundle exec rails test` passed 26 runs/88 assertions and SimpleCov is enabled in `test/test_helper.rb:2-7`, but no test covers the Stimulus controller or a real Redis, Action Cable, browser, or OpenRouter interaction. |
| G12 | PASS | Final checks all exited 0: `bundle exec rubocop` (50 files, no offenses), `bundle exec brakeman --no-pager` (0 warnings), and `bundle exec bundle-audit check --update` (no vulnerabilities). |
| G13 | PASS | `Dockerfile:23-29,64-78` sets production defaults, uses the non-root `rails` user, and has an `exec` entrypoint; `docker build -t relay-chat:self-review-final .` succeeded, and the compose smoke test served `/up` with HTTP 200. README setup and Compose instructions are at `README.md:17-47`. |
| G14 | PASS | There are no authentication routes/controllers; `.gitignore:10-11,28` and `.dockerignore:10-15` exclude env/key files, and a current literal-secret scan found only the `${OPENROUTER_API_KEY:?...}` environment reference in `compose.yml:22`, not a credential. |

## Surgical fixes made during this review

- Removed duplicate optimistic message inserts from `app/views/messages/create.turbo_stream.erb`. `ResponseBroadcaster#start` is now the single producer of the user/placeholder Turbo broadcasts; `MessagesControllerTest` asserts the request response no longer contains the prompt (`test/controllers/messages_controller_test.rb:34-43`).
- Re-read the conversation after acquiring the Redis turn lock in `app/services/chat_app/chat_turn.rb:30-37`. Previously, a request could replay a snapshot read before another completed turn. `ChatTurnTest#test_re_reads_conversation_history_after_acquiring_the_turn_lock` checks the order (`test/services/chat_app/chat_turn_test.rb:132-147`).
- Removed a duplicate `javascript_importmap_tags` invocation from `app/views/layouts/application.html.erb`; it emitted duplicate import-map/module tags.

## Code quality assessment

The Ruby application code is generally small and named clearly. `ConversationStore`, `ResponseBroadcaster`, `SafeCalculator`, and the two tool classes have narrow, understandable responsibilities. Controller actions are short (`app/controllers/conversations_controller.rb:2-5`; `app/controllers/messages_controller.rb:2-16`) and dependencies are injectable in the service tests.

The main exception is `ChatApp::ChatTurn#call` (`app/services/chat_app/chat_turn.rb:23-62`). It mixes validation, locking, provider streaming, persistence, token accounting, title generation, and UI error delivery. This makes it the coupling point for all lower layers and makes failure policy harder to change safely. It is still only 40 executable lines, but it has too many reasons to change.

There is configuration and construction duplication. Both controllers repeat the fallback `ConversationStore` factory (`app/controllers/conversations_controller.rb:9-11`; `app/controllers/messages_controller.rb:25-27`), while the Claude model default is repeated in the initializer, `ChatClient`, and `TitleGenerator` (`config/initializers/ruby_llm.rb:5`; `app/services/chat_app/chat_client.rb:16`; `app/services/chat_app/title_generator.rb:17`). The generated empty helpers and unused `app/javascript/controllers/hello_controller.js` are dead scaffolding. `Conversation#bound_messages` drops individual messages (`app/services/chat_app/conversation.rb:97-103`), which can leave a retained assistant message without its user prompt.

Top three refactors with more time:

1. Split `ChatTurn` into a preflight/locking coordinator, a streaming executor, and a post-success title step. This would reduce cross-layer coupling and make each error contract independently testable.
2. Introduce a single application-level Redis/store factory with connection pooling, and make conversation trimming remove complete user/assistant exchanges. The current per-request construction and individual-message eviction are fragile under load.
3. Centralize chat configuration (model, budget, limits) and remove generated dead files. This eliminates default-value drift and makes the actual application surface smaller.

## Test coverage assessment

The final `bundle exec rails test` run completed with 26 runs, 88 assertions, 0 failures, 0 errors, and 0 skips. SimpleCov reported 95.33% line coverage (327/343) and 70.88% branch coverage (56/79); its JSON has the same counts with unrounded percentages of 95.34% and 70.89%.

The weakest line-covered component is `app/services/chat_app/turn_dispatcher.rb` at 87.50% (7/8); its thread-level rescue/logging branch is not exercised. More broadly, the least credible area is the external integration path: `ResponseBroadcaster` is 88.00% line covered, `ChatClient` is 88.46% line/66.67% branch covered, but both are tested without a real WebSocket or provider.

No test covers a real OpenRouter stream, tool call, or structured-title response; live Redis expiration/WATCH retry behavior; two actual Puma workers across a restart; Action Cable ordering, reconnection, or browser DOM updates; Redis unavailability/corrupt JSON; lock expiry during a slow provider call; or the Stimulus form behavior. The RubyLLM method names used by doubles were checked against ruby_llm 1.16.0, but that is not an end-to-end provider contract test.

## Known defects and risks

- `TurnDispatcher#dispatch` creates an unbounded native thread per accepted message (`app/services/chat_app/turn_dispatcher.rb:11-16`). A caller can consume worker threads, memory, and provider quota; there is no queue, rate limit, or admission control.
- The Redis turn lock has a fixed 300-second TTL and is not renewed (`app/services/chat_app/conversation_store.rb:7-8,55-62`). A turn that exceeds it can overlap a later turn; a crashed process can also block a conversation until TTL expiry.
- The token budget is checked before a new call but does not reserve estimated prompt/output tokens (`app/services/chat_app/chat_turn.rb:37-52`). One expensive response can overshoot the configured budget substantially before the following turn is rejected.
- History trimming removes one message at a time (`app/services/chat_app/conversation.rb:102`), so a byte-cap eviction can begin a replayed history with an assistant message or otherwise split an exchange.
- `ConversationStore.new` creates a Redis client whenever a controller/service falls back to the default (`app/services/chat_app/conversation_store.rb:21`; both controllers noted above). There is no explicit shared connection pool or close lifecycle, which risks connection churn at higher request rates.
- A disconnected or failed Action Cable subscription has no HTTP-stream fallback. The request response now intentionally contains only form housekeeping (`app/views/messages/create.turbo_stream.erb:1-3`), so transient stream UI updates are missed until reload even if the turn later persists.
- This is intentionally unauthenticated. Combined with no rate limit, any reachable user can create conversations and incur OpenRouter cost. The production configuration also leaves `force_ssl` commented out (`config/environments/production.rb:24-31`); TLS and ingress restrictions must be supplied by deployment infrastructure.
- The current review did not make a billable real-provider request. The Docker/Compose smoke used a placeholder key and verified boot/root rendering, not an end-to-end answer.
