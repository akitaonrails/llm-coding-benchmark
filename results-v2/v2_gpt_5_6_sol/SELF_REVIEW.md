# Self-review

Review date: 2026-07-26.

The current source was inspected directly and the test/quality commands below were rerun in this phase. The positive browser, streaming, tool, restart, and Docker runtime proofs cited from phase 2 were produced against the same application source: no application file is newer than `../phase2.result.json`. No application code was changed in phase 3; the Rails-managed local development secret finding is documented below.

## 1. Goal verification table

| Goal | Verdict | Concrete evidence |
| --- | --- | --- |
| G1 | PASS | `mise latest ruby`, `mise current ruby`, `ruby --version`, and `bundle exec rails --version` returned Ruby 4.0.6 and Rails 8.1.3; `gem search --remote --exact rails` returned 8.1.3. `mise.toml:2` pins Ruby 4.0.6, while `config/application.rb:6-11` does not load Active Job, Active Record, or Action Mailer and `config/application.rb:41` disables ORM generators. Phase 1 ran `mise exec -- rails _8.1.3_ new . ... --skip-active-record --skip-active-job --skip-action-mailer` at `.` with exit 0. |
| G2 | PASS | `app/views/chats/show.html.erb:2-26` is one Turbo-enabled chat screen assembled from partials; `app/views/chats/_form.html.erb:2-18` uses `form_with` plus Stimulus; `app/javascript/controllers/chat_form_controller.js:15-37` contains focused form behavior and no fetch/`innerHTML`; `app/assets/tailwind/application.css:1-4` splits Tailwind styles into base, layout, and chat component files. `ChatsControllerTest#test_renders_the_componentized_single-page_chat` passed in the current suite. |
| G3 | PASS | `Gemfile:21` and `Gemfile.lock:277` resolve current `ruby_llm` 1.16.0; `gem search --remote --exact ruby_llm` also returned 1.16.0. `app/models/chat/settings.rb:5-16` defaults to env-overridable `anthropic/claude-sonnet-5`; `app/services/chat/llm_client.rb:23-25` constructs an OpenRouter chat. A current OpenRouter model-list query returned `Anthropic: Claude Sonnet 5`, created 2026-06-30, and listed both Sonnet 5 and the older Sonnet 4.6. |
| G4 | PASS | `app/services/chat/llm_client.rb:33-35` yields each non-empty provider chunk and `app/services/chat/turn_runner.rb:62-67` broadcasts each accumulated update through `app/services/chat/broadcaster.rb:28-29`. The phase-2 browser observer recorded four separate assistant Turbo replacements growing through 130, 224, 365, and 476 characters before the final completion; current `Chat::TurnRunnerTest#test_streams_incrementally_commits_both_messages_and_generates_the_first_title` and `Chat::BroadcasterTest#test_broadcasts_every_accumulated_streaming_update` passed. |
| G5 | PASS | `app/services/chat/turn_runner.rb:23-30` snapshots committed history before the new prompt, and `app/services/chat/llm_client.rb:31-33` replays that history before calling `ask(prompt)` once. `Chat::LlmClientTest#test_sends_each_multi-turn_message_exactly_once` asserts the exact three-message provider array at `test/services/chat/llm_client_test.rb:16-35` and passed. |
| G6 | PASS | `app/models/chat/conversation_store.rb:34-42,45-68` uses cross-process `flock`, atomic disk writes, and per-conversation transactions rather than process memory; `app/models/chat/conversation_store.rb:117-126` enforces message/byte limits and `app/models/chat/conversation_store.rb:111-115` writes a TTL. Current tests passed for restart via a new store, two forked writers (24 messages without loss), TTL, message/byte caps, and conversation count (`test/models/chat/conversation_store_test.rb:18-115`). Phase 2 also reloaded an unchanged four-message conversation after replacing a two-worker Puma master; current `docker top project-web-1` still shows two non-root workers. The separate store-wide pruning defect disclosed below does not defeat the required per-conversation message/byte caps. |
| G7 | PASS | `app/services/chat/llm_client.rb:63-70` replaces the tool set with exactly `ServerTime` and `Calculator`; their implementations are at `app/tools/server_time.rb:3-13` and `app/tools/calculator.rb:3-16`, with arithmetic parsed without `eval` in `app/services/chat/arithmetic_evaluator.rb:13-26`. Phase-2 RubyLLM logs recorded `Tool server_time called` with `2026-07-26T19:43:42Z` and `Tool calculator called` with `(17 * 23) + 19 / 2`, returning 400.5; the UI answers matched. Current tool, evaluator, and exact-tool-set tests passed. |
| G8 | PASS | `app/services/chat/turn_runner.rb:42,70-80` calls the title generator only after the first successful exchange; `app/services/chat/title_generator.rb:25-33` uses `with_schema(ConversationTitleSchema)`, whose schema is defined at `app/schemas/conversation_title_schema.rb:5-7`; `app/views/chats/_title.html.erb:1-3` renders the title. Current title/turn-runner tests passed, and the phase-2 Compose E2E displayed the generated title `Respond With Compose-runtime-ok Marker`. |
| G9 | PASS | `app/services/chat/turn_runner.rb:26-30,57-60` checks projected usage before invoking the client; `app/services/chat/turn_runner.rb:37` persists approximate usage and `app/services/chat/broadcaster.rb:60-63` emits the friendly in-UI refusal. `Chat::TurnRunnerTest#test_refuses_an_over-budget_turn_without_calling_the_provider` asserts no client call and no persistence at `test/services/chat/turn_runner_test.rb:83-96`; it passed. The admission-only/approximate nature of the budget is disclosed below. |
| G10 | PASS | `app/services/chat/llm_client.rb:8-15,60-70` sets the system prompt through `with_instructions`; `app/services/chat/llm_client.rb:53-57` provides the missing-key preflight; `app/services/chat/turn_runner.rb:43-50` converts provider/unexpected failures to degraded results. The exchange is added only after `stream_reply` succeeds (`app/services/chat/turn_runner.rb:29-38`). Current missing-key, provider-error, unexpected-client-error, no-partial-persistence, and title-degradation tests passed; `app/views/chats/_status.html.erb:1-3` and `app/views/chats/_streaming_message.html.erb:14-19` render the visible state. |
| G11 | PARTIAL | Current `bin/rails test` passed 47 runs / 160 assertions with 0 failures, errors, or skips; `test/test_helper.rb:3-10` starts SimpleCov with branch coverage and `test/services/chat/llm_client_test.rb:6-13` checks fake/real RubyLLM method signatures. However, coverage is 97.08% line and only 78.81% branch, the Stimulus controllers have no JS/system tests, and several failure paths listed in section 3 have no automated test. This does not satisfy the literal “every component” and “error paths covered” wording completely. |
| G12 | PASS | Current commands all exited 0: `bin/rubocop` inspected 52 files with no offenses; `bin/brakeman --quiet --no-pager --exit-on-warn --exit-on-error` reported 0 warnings/0 errors; `bin/bundler-audit` reported no vulnerabilities. `bin/importmap audit` also found no vulnerable packages. |
| G13 | PASS | `Dockerfile:20-24` sets production/Bundler runtime state, `Dockerfile:59-69` creates and runs as UID/GID 1000 with an explicit entrypoint, and `Dockerfile:73-75` supplies a health check and server command. `compose.yml:1-35` supplies the production web service, two Puma workers, Redis, health dependency, and a named conversation volume. Phase-2 `docker build` and `docker compose up --build` succeeded; current `curl` calls to the Compose app at port 3101 return 200 for `/` and `/up`, both containers are healthy, and `docker compose config --quiet` passes. Setup and run instructions are at `README.md:17-70`. |
| G14 | PASS | Routes contain only chat/message/health endpoints (`config/routes.rb:1-10`), and a current auth-marker scan of `app`, `config`, and `Gemfile` returned `auth_markers=none`. `.gitignore:2-16` excludes env, coverage, runtime conversations, temporary files, master keys, and credentials. Current scans found no `.env` files and no OpenRouter-key/private-key patterns in source or logs. Rails's ignored, untracked `tmp/local_secret.txt` is the framework-generated local session secret described below, not a committed provider credential. App artifacts are under the workspace root. |

## 2. Code quality assessment

### Naming and responsibilities

Most names communicate intent: `TurnRunner`, `ConversationStore`, `TokenEstimator`, `Broadcaster`, and `ArithmeticEvaluator` have predictable public APIs. Names such as `start_turn`, `stream_reply`, `over_budget?`, and `provider_attributes` describe the work being done without requiring comments.

Responsibility boundaries are uneven. `Chat::ConversationStore` is 208 lines and owns path validation, lock striping, JSON decoding, expiry, size trimming, atomic writes, and global pruning (`app/models/chat/conversation_store.rb:8-207`). That is too much policy and infrastructure in one class. `TurnRunner#call` is a reasonable orchestration method, but it keeps a persistence transaction open while performing a potentially 120-second provider request (`app/services/chat/turn_runner.rb:22-40`), coupling LLM latency directly to the storage lock.

`Broadcaster` is focused on presentation delivery, but it is tightly coupled to view partial names and DOM IDs (`app/services/chat/broadcaster.rb:12-24,34-50,67-84`). Both controllers duplicate session-ID validation and concrete store construction (`app/controllers/chats_controller.rb:14-22`, `app/controllers/messages_controller.rb:42-54`). `Conversation#stream_name` also places a presentation/channel concern in the domain object (`app/models/chat/conversation.rb:32-34`).

### Duplication, dead code, and size

Configuration defaults are repeated across `Chat::Settings`, the RubyLLM initializer, Compose, and README. In particular, timeout parsing is implemented in `config/initializers/ruby_llm.rb:3-12` while `Chat::Settings.request_timeout` at `app/models/chat/settings.rb:44-46` is unused. `Conversation#first_exchange?` is referenced only by its model test, not production code (`app/models/chat/conversation.rb:28-30`). The generated PWA views remain while their routes and layout link are commented out (`config/routes.rb:12-14`, `app/views/layouts/application.html.erb:14-15`).

The 128-line arithmetic parser is long but cohesive and avoids dangerous evaluation. The CSS is sensibly divided into base, layout, and chat component files. Controller methods and the smaller service/model classes are generally short.

### Top three refactors with more time

1. Split `ConversationStore` into a file repository/codec, a per-conversation transaction lock, and a pruner. This would isolate failure handling, make the proven pruning race easier to fix, and reduce the 208-line class's reason count.

2. Remove provider I/O from the file-lock critical section. A versioned reservation/commit protocol or per-conversation queue could preserve exact ordering while avoiding 120-second lock occupancy and unrelated head-of-line blocking from the 64 lock stripes.

3. Introduce one request-level conversation context and central configuration source. This would remove duplicated `conversation_id`/`store` controller methods, reduce concrete layer coupling, and prevent the model/timeout/default values from drifting across Ruby code, Compose, tests, and documentation.

## 3. Test coverage assessment

Current command:

```text
bin/rails test
47 runs, 160 assertions, 0 failures, 0 errors, 0 skips
Line coverage: 500 / 515 (97.08%)
Branch coverage: 93 / 118 (78.81%)
```

The weakest-tested request-path area is `MessagesController`: 29/32 lines (90.62%) and 6/9 branches (66.67%). Its successful streaming callback and completed/budget result branches at `app/controllers/messages_controller.rb:13,25,31` are not executed by controller integration tests. The two Stimulus controllers are outside SimpleCov and have no JS or system tests, so the complete request-to-WebSocket-to-DOM path is not automated even though its positive path was manually validated in phase 2.

Failure modes not covered by an automated test include:

- an empty provider response taking `LlmClient`'s own `Error` re-raise path (`app/services/chat/llm_client.rb:38,43-44`);
- an unexpected non-`LlmClient` failure in the main turn runner (`app/services/chat/turn_runner.rb:48-50`);
- disk full, permission failure, interrupted `fsync`/rename, and concurrent delete/prune races in `ConversationStore`;
- invalid expiry data during `expired?` and corrupt/invalid data encountered specifically by the pruning pass (`app/models/chat/conversation_store.rb:105-109,166-173`);
- unary arithmetic, modulo-by-zero, and several malformed-parenthesis/parser branches (`app/services/chat/arithmetic_evaluator.rb:63-81,84-90`);
- Redis/Action Cable disconnect during a stream, browser disconnect mid-turn, provider timeout after partial chunks, and reconnect/reload behavior;
- combined time-and-calculation requests proving that both tools, rather than merely one required tool, are called;
- malformed or unavailable env-selected model IDs when `assume_model_exists: true` bypasses the local registry.

## 4. Known defects and risks

1. **Proven soft-cap defect under concurrent pruning.** `remove_if_available` silently skips a locked conversation (`app/models/chat/conversation_store.rb:181-187`) and there is no retry. A review-time reproduction configured `max_conversations: 1`, locked the oldest file in another process, and wrote a second conversation. Exact result: `configured_max=1 during_lock=2 after_release_without_new_write=2`. The store-wide cap can therefore remain exceeded until a later mutating transaction happens to prune it. Per-conversation message and byte caps still passed.

2. **Long external calls occur while holding a striped file lock.** `TurnRunner` invokes streaming inside `store.transact` (`app/services/chat/turn_runner.rb:22-40`), and the transaction acquires one of only 64 exclusive locks (`app/models/chat/conversation_store.rb:87-94,203-205`). A slow provider blocks the same conversation and any unrelated conversation that hashes to the same stripe for up to the configured request timeout. Correctness is favored over throughput, but latency and saturation risk rise under load.

3. **Streaming payload work grows quadratically with answer length.** Each chunk is appended to an accumulated string (`app/services/chat/turn_runner.rb:62-67`), then the entire accumulated answer is rendered and broadcast as a replacement (`app/services/chat/broadcaster.rb:28-29,79-85`). There is no coalescing or rate limit. Long/high-frequency streams can create excessive rendering, Redis, WebSocket, and browser work.

4. **The token budget is approximate and admission-only.** It is checked before a turn (`app/services/chat/turn_runner.rb:57-60`), but no output-token limit or mid-stream cutoff is applied. A single long reply or the title call can take usage beyond the configured budget before the following turn is refused. Starting a new chat resets the per-conversation limit.

5. **Persistence has single-host filesystem assumptions.** File `flock` and atomic rename are suitable for the tested two Puma workers sharing one local volume, but multi-host deployment would require a shared filesystem with compatible lock/rename semantics or a different store. Expired files are removed only when fetched or when another mutation triggers pruning (`app/models/chat/conversation_store.rb:31-42,156-179`), so TTL expiry is not proactive disk cleanup. The file is `fsync`ed, but the parent directory is not, leaving a power-loss durability gap around rename.

6. **Tool enforcement relies partly on a lexical heuristic and model compliance.** `tool_choice` recognizes selected words/operators (`app/services/chat/llm_client.rb:73-82`). Phrases such as “what is seven plus nine?” do not force `calculator`; they fall back to `:auto`. A request containing both time and arithmetic uses generic `:required`, which requires a tool but does not by itself guarantee both tools. The system instructions reduce this risk but do not make it deterministic.

7. **The unauthenticated demo is exposed to cost and privacy abuse if internet-facing.** This is intentionally a no-auth app, but there is no rate limiting, global spend cap, or user quota, and Compose binds the web port on all host interfaces (`compose.yml:15-16`). Development RubyLLM logs contain complete prompts, responses, and tool payloads; those logs should be treated as conversation data. Conversation JSON is plaintext at rest, though individual files are created mode `0600`.

8. **Redis failure can leave the current page stale.** Conversation data is committed on disk, but incremental/final UI delivery depends on Action Cable through Redis in production (`config/cable.yml:9-12`). There is no application-level replay/acknowledgment of missed broadcasts. A reload recovers committed history, but an in-flight browser may miss the final replacement if Redis or the cable connection drops.

9. **Rails writes the local development session secret mode `0644`.** Rails 8.1.3 automatically generates the 128-byte `tmp/local_secret.txt` when development/test boots without `SECRET_KEY_BASE` (railties `lib/rails/application/configuration.rb:653-662`). The workspace ignores all of `tmp` (`.gitignore:9-13`), and production Compose requires `SECRET_KEY_BASE`, so this is not a committed or production provider secret. On a multi-user development host, however, the default world-readable mode exposes the local cookie-signing secret to other local users.

### Review-time finding and attempted cleanup

The review initially treated `tmp/local_secret.txt` as leftover validation output and deleted it without reading or printing its value. A later `bin/rails runner` invocation regenerated it. Gem-source inspection then confirmed that this is Rails 8.1.3's documented local `secret_key_base` behavior, so no recurring deletion or application change was made. The file is ignored and untracked. Follow-up scans reported `env_files=none`, `secret_pattern_matches=none` in source, and `secret_log_pattern_matches=none`. No surgical application-code fix was made in phase 3.
