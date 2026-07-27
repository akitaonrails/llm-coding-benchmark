# SELF_REVIEW

Review date: 2026-07-27. This review rechecked the current workspace and made four surgical fixes found during review: removed a generated scaffold header from `app/views/conversations/show.html.erb`, updated the default model to `anthropic/claude-sonnet-5` in `app/services/chat_settings.rb`, aligned the RubyLLM test fake signatures with the installed gem API in `test/services/ruby_llm_gateway_test.rb`, and fixed overbroad calculator routing for non-arithmetic "what is" prompts in `app/services/tool_intent.rb` with a regression test.

## GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence |
|---|---|---|
| G1 | PASS | `mise current` reports `ruby 4.0.6`; `ruby -v && bin/rails -v` reports Ruby 4.0.6 and Rails 8.1.3; `config/application.rb:5-9` loads Active Model, Controller, View, Cable, and Test Unit only; ActiveRecord/Mailer/Job source scan returned no matches. |
| G2 | PASS | `Gemfile:11-16` includes Turbo, Stimulus, and Tailwind; `app/views/conversations/show.html.erb:2-16` uses `turbo_stream_from` and Rails partials; `app/javascript/controllers/chat_controller.js:3-39` is Stimulus; JS `fetch` and `innerHTML` source scans returned no matches. |
| G3 | PASS | `bundle info ruby_llm` reports `ruby_llm (1.16.0)`; `config/initializers/ruby_llm.rb:5-11` configures OpenRouter API key/default model; `app/services/chat_settings.rb:4,19-24` defaults to `anthropic/claude-sonnet-5` with env override; OpenRouter's model page lists `anthropic/claude-sonnet-5` as Claude Sonnet 5. |
| G4 | PASS | `app/services/chat_turn_runner.rb:31-39` appends each streamed token before `complete_turn`; `app/services/turbo_broadcaster.rb:4-10` broadcasts token appends through `Turbo::StreamsChannel`; `test/services/chat_turn_runner_test.rb:64-84` asserts streamed tokens `["Hel", "lo"]`. |
| G5 | PASS | `app/services/chat_turn_runner.rb:18-21` captures replay history before adding the current turn; `app/services/conversation_store.rb:92-108,335-347` replays only complete user/assistant rows; `test/services/ruby_llm_gateway_test.rb:81-100` asserts the exact outgoing multi-turn message array and one current prompt. |
| G6 | PASS | `app/services/conversation_store.rb:22-32,229-266,274-293,371-386` uses SQLite file persistence, TTL/expires_at, WAL/busy timeout, immediate transactions, message and byte caps; command `bin/rails runner ... two ConversationStore instances ...` returned `ok: 4 messages, sequences=1,2,3,4`. |
| G7 | PASS | `app/services/ruby_llm_gateway.rb:4,26-30` exposes exactly `[ServerTimeTool, CalculatorTool]` through `with_tools`; `app/tools/server_time_tool.rb:3-8` and `app/tools/calculator_tool.rb:3-14` implement required tools; `test/services/ruby_llm_gateway_test.rb:103-110` and `test/tools/chat_tools_test.rb:6-24` verify names/tool selection/results. |
| G8 | PASS | `app/services/ruby_llm_gateway.rb:18-23` uses `with_schema(ConversationTitleSchema)`; `app/services/chat_turn_runner.rb:60-68` generates title only after first completed exchange and broadcasts it; `app/views/conversations/_title.html.erb:1-3` displays it; `test/services/title_generator_test.rb:17-26` verifies structured title flow. |
| G9 | PASS | `app/services/chat_settings.rb:5,27-29` defines env-configurable budget; `app/services/token_budget.rb:11-19` refuses projected over-budget turns; `app/controllers/messages_controller.rb:12-13` renders refusal before provider call; `test/controllers/messages_controller_test.rb:21-35` verifies visible refusal and no stored history. |
| G10 | PASS | `app/services/ruby_llm_gateway.rb:27-29` sets system prompt through `with_instructions`; `app/services/provider_preflight.rb:6-10` raises a friendly missing-key error; `app/services/chat_turn_runner.rb:42-45,71-75` rescues provider failures into visible failed turns; `app/services/conversation_store.rb:92-108,168-195` excludes failed turns from replay; tests cover these paths. |
| G11 | PARTIAL | `bin/rails test` passed `31 runs, 83 assertions`; `test/test_helper.rb:1-6` wires SimpleCov branch coverage and current coverage is 89.39% line / 61.76% branch, but `coverage/coverage.json` reports `app/services/chat_settings.rb` at 0.0% line/branch coverage and no automated browser/WebSocket test covers the Stimulus/Turbo UI. |
| G12 | PASS | `bin/rubocop` returned `54 files inspected, no offenses detected`; `bin/brakeman --no-pager` returned `Security Warnings: 0`; `bin/bundler-audit check --update` returned `No vulnerabilities found`. |
| G13 | PASS | `Dockerfile:21-26,61-75` sets production env, non-root user, entrypoint, exposed port and command; `docker-compose.yml:1-30` defines web plus Redis and volumes; `docker build -t llm-chat-self-review .` returned `docker build ok`; exported-env compose probe returned `compose root HTTP 200` and tore the stack down. |
| G14 | PASS | `config/routes.rb:1-17` has only conversations/messages/health routes and no auth routes; auth scan only found commented scaffold examples; secret-pattern scan excluding coverage/log/tmp returned no matches. |

Referenced scan commands:

```sh
rg -n "ActiveRecord|ActionMailer|ActiveJob|ApplicationRecord" app config Gemfile
# no output

rg -n "fetch\(" app/javascript
# no output

rg -n "innerHTML|insertAdjacentHTML" app
# no output

rg -n "authenticate|login|logout|current_user|has_secure_password|bcrypt" app config Gemfile README.md
# only Gemfile/comment scaffold examples

rg -n "(sk-or-|OPENROUTER_API_KEY=|SECRET_KEY_BASE=|BEGIN (RSA|OPENSSH|PRIVATE) KEY|api[_-]?key:\s*['\"]|secret[_-]?key:\s*['\"])" --glob '!coverage/**' --glob '!log/**' --glob '!tmp/**' .
# no output
```

## CODE QUALITY ASSESSMENT

Overall structure is service-oriented and mostly readable. Naming is direct: `RubyLlmGateway`, `ChatTurnRunner`, `ConversationStore`, `TokenBudget`, `ProviderPreflight`, and the two tool classes describe their jobs clearly. Controllers are small enough to scan (`app/controllers/messages_controller.rb` is 70 lines, `app/controllers/conversations_controller.rb` is 30 lines), and views are broken into Rails partials.

The largest clean-code problem is single responsibility in `app/services/conversation_store.rb`: it is 457 lines and owns schema creation, connection management, transactions, TTL pruning, message insertion, replay filtering, bounds enforcement, token-count aggregation, and row mapping. That makes concurrency behavior and pruning edge cases harder to reason about than the rest of the app.

Coupling is moderate. `MessagesController#create` directly coordinates preflight, pending-turn checks, budget enforcement, store calls, async runner startup, and Turbo Stream rendering (`app/controllers/messages_controller.rb:2-19,24-35`). `TurboBroadcaster` duplicates message DOM-id formatting already present in `MessagesHelper` (`app/services/turbo_broadcaster.rb:51-56`, `app/helpers/messages_helper.rb:2-7`). `app/javascript/controllers/hello_controller.js:1-7` is unused generated dead code.

Top 3 refactors with more time:

1. Split `ConversationStore` into schema/connection, repository, pruning/bounds, and mapper pieces. This would make TTL, byte-cap, rollback, and replay behavior easier to test independently.
2. Replace `Thread.new` per chat turn in `ChatTurnRunner` with a bounded runner abstraction. Raw unbounded threads (`app/services/chat_turn_runner.rb:23-27`) are fragile under load and during process shutdown.
3. Consolidate Turbo DOM-id/rendering contracts between helpers and `TurboBroadcaster`, then add a thin system test around the broadcast targets. That would reduce drift between server broadcasts and rendered HTML.

## TEST COVERAGE ASSESSMENT

Final test command: `bin/rails test` returned `31 runs, 83 assertions, 0 failures, 0 errors, 0 skips`.

SimpleCov totals from `coverage/coverage.json`: line coverage 430 / 481 = 89.39%; branch coverage 63 / 102 = 61.76%.

Weakest-tested area: configuration and UI/runtime integration. `app/services/chat_settings.rb` is 0.0% line and branch coverage, so env fallback/default behavior is not directly covered. `TurboBroadcaster` is only 68.75% line-covered and only token append is unit-tested; replace-title/status/form/message broadcasts are not covered. The Stimulus controller and real browser DOM behavior are not covered by automated tests.

Failure modes not covered by tests:

- Mid-stream provider failure after some tokens have already been broadcast.
- Real OpenRouter tool-call execution and malformed provider/tool/schema responses.
- Full browser/WebSocket behavior proving DOM updates over Action Cable after code changes.
- True process-level Puma `WEB_CONCURRENCY=2` contention under sustained concurrent writes; this review ran a two-store concurrency probe, not a load test.
- Byte-cap pruning branch and SQLite rollback/busy-timeout failure paths.
- Docker compose real chat after the model update; this review proved compose boot/root HTTP 200 with a dummy API key, while Phase 2 previously proved real compose chat.

## KNOWN DEFECTS AND RISKS

- The app intentionally has no authentication. Conversation URLs are UUID-based but anyone with a conversation URL can view that conversation; this is acceptable for the demo goal but not for production.
- `ChatTurnRunner` uses a raw background thread per message (`app/services/chat_turn_runner.rb:23-27`). There is no bounded queue, retry policy, cancellation, or graceful drain guarantee on shutdown.
- SQLite write concurrency relies on WAL, `busy_timeout(5_000)`, and `BEGIN IMMEDIATE` (`app/services/conversation_store.rb:274-293`). There is no explicit retry/backoff for `SQLite3::BusyException`.
- Token budgeting is approximate: `TokenCounter` uses bytes / 4 (`app/services/token_counter.rb:3-12`), not the OpenRouter/Anthropic tokenizer. It can over- or under-refuse.
- Tool routing is still heuristic even after the review fix (`app/services/tool_intent.rb:3-17`). Ambiguous natural-language arithmetic may be routed incorrectly.
- `app/javascript/controllers/hello_controller.js:1-7` is unused generated dead code.
- Coverage is not strong enough to justify high confidence in UI integration or edge-case recovery: branch coverage is only 61.76%.

## EXTERNAL MODEL RECENCY SOURCES

- OpenRouter Claude Sonnet 5 model page: https://openrouter.ai/anthropic/claude-sonnet-5
- Anthropic Claude Sonnet 5 announcement: https://www.anthropic.com/news/claude-sonnet-5
