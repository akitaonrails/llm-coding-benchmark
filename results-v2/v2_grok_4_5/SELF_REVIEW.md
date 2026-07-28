# SELF_REVIEW — Phase 3

Evidence gathered 2026-07-27 against the code and commands in this workspace. No new features were added in this phase. No surgical fixes were required.

Commands re-run:

- `bin/rails test` → 69 runs, 201 assertions, 0 failures, 0 errors, 0 skips
- SimpleCov → Line **97.54%** (437/448), Branch **80.70%** (92/114)
- `bin/rubocop` → 53 files, no offenses
- `bin/brakeman -q` → 0 warnings (Rails 8.1.3)
- `bundle exec bundle-audit check` → no vulnerabilities
- `bin/rails runner '…'` → boots; `RUBY_VERSION=4.0.6`, `Rails=8.1.3`, ActiveRecord/ActiveJob/ActionMailer undefined
- Secret scan (`sk-or-…` / committed `SECRET_KEY_BASE=…`) → none in source

---

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | **PASS** | Ruby 4.0.6 (`.ruby-version`, `ruby -v`); Rails 8.1.3 (`Gemfile:3`, `Gemfile.lock`); AR/AJ/AM railties commented out (`config/application.rb:6-10`); app at workspace root (not nested). `bin/rails runner` prints `ar=`/`aj=`/`am=` empty. |
| G2 | **PASS** | Tailwind via `tailwindcss-rails` (`Gemfile:9`, `app/assets/tailwind/application.css`); Turbo + Stimulus (`Gemfile:7-8`, `app/javascript/controllers/{composer,auto_scroll}_controller.js`); SPA shell + partials (`app/views/conversations/show.html.erb`, `app/views/messages/_*.erb`); form posts Turbo Stream (`messages/create.turbo_stream.erb`), not fetch/innerHTML. |
| G3 | **PASS** | `ruby_llm` 1.16.0 (`Gemfile.lock`); OpenRouter key + default model in `config/initializers/ruby_llm.rb:9-12` and `AppConfig.chat_model` default `anthropic/claude-sonnet-4.6` (`app_config.rb:12-14`); overridable via `CHAT_MODEL`. Responder uses `provider: :openrouter` (`conversation_responder.rb:102-105`). |
| G4 | **PASS** | Incremental path: `chat.ask` yields chunks → `accumulated += text` → `TurboBroadcaster#stream_chunk` → `broadcast_update_to` on `assistant_body_#{turn_id}` (`conversation_responder.rb:86-94`, `turbo_broadcaster.rb:14-20`). Unit test asserts progressive snapshots `["Hel","Hello","Hello world"]` (`conversation_responder_test.rb` “streams the reply incrementally as tokens arrive (G4)”). HTTP response only appends empty placeholder (`create.turbo_stream.erb:9-10`). |
| G5 | **PASS** | Responder loads `@conversation.messages` then `ask(@prompt)` so the new prompt is not in replayed history (`conversation_responder.rb:54,109`). Unit tests: `MessageBuilderTest` “builds the exact outgoing message array for a multi-turn conversation”; `ConversationResponderTest` “replays history that excludes the prompt being sent (G5)” asserts `chat.messages == MessageBuilder.outgoing(...)`. **Caveat:** production path never calls `MessageBuilder` (only tests do) — see Code Quality. |
| G6 | **PASS** | SQLite file store, WAL + `busy_timeout` + `BEGIN IMMEDIATE` (`conversation_store.rb:144-151,236-243`); message/byte caps + TTL (`trim`/`expired?`, `AppConfig` max_messages/max_bytes/ttl); restart test “state survives an application restart”; cross-instance test “shared across processes”; thread stress “concurrent writers… 40 messages”. Compose sets `WEB_CONCURRENCY=2` + Redis cable + volume (`docker-compose.yml:43-55`). **Caveat:** multi-worker correctness is designed/tested via two store objects, not a real forked Puma pair; see Known Defects (preload/fork pool). |
| G7 | **PASS** | Exactly two tools: `ServerTimeTool` / `CalculatorTool` (`app/tools/*`); registered `chat.with_tools(ServerTimeTool, CalculatorTool)` (`conversation_responder.rb:108`); FakeChat records tools as `:server_time`/`:calculator` (`conversation_responder_test.rb` “sets the system prompt and exposes both tools”). Calculator uses `SafeCalculator` (no `eval`) (`calculator_tool.rb:17`, `safe_calculator.rb`). Live model compliance is model-dependent; wiring is correct. |
| G8 | **PASS** | `TitleSchema < RubyLLM::Schema` with `string :title` (`title_schema.rb`); `TitleGenerator` calls `chat.with_schema(TitleSchema)` (`title_generator.rb:18-22`); first-exchange only (`conversation_responder.rb:126-135`); UI partial + broadcast (`_title.html.erb`, `TurboBroadcaster#title`). Tests: “generates and broadcasts a title after the first exchange” / “does not regenerate… on later exchanges”. |
| G9 | **PASS** | `AppConfig.token_budget` env `CONVERSATION_TOKEN_BUDGET` default 20000 (`app_config.rb:27-29`); usage bumped on success (`append_exchange` + `TokenEstimator`); refuse before provider when `token_usage >= budget` (`messages_controller.rb:14,32-34`); `over_budget.turbo_stream.erb`. Test: “an over-budget conversation is refused without calling the provider (G9)”. |
| G10 | **PASS** | System prompt via `with_instructions` (`conversation_responder.rb:107`); missing-key preflight (`messages_controller.rb:13`, banner in `show.html.erb:23-28`); provider errors → `handle_failure` + friendly copy (`conversation_responder.rb:140-159`); failed turns not persisted (tests “rescues a provider failure…” and “failed turn never enters the history…”). |
| G11 | **PASS** | 17 test files covering controllers, models, services, tools; FakeChat mirrors real API (`test/support/test_doubles.rb:3-9`); error paths in controller + responder tests; SimpleCov started before app load (`test_helper.rb:3-15`). Suite green: 69 runs / 201 assertions. **Gaps:** no Stimulus/JS tests; some responder branches unhit (see §3). |
| G12 | **PASS** | Re-run: RuboCop 0 offenses; Brakeman 0 warnings; bundle-audit no vulnerabilities. |
| G13 | **PASS** | `Dockerfile`: `RAILS_ENV=production`, non-root `USER 1000:1000`, multi-stage, `ENTRYPOINT bin/docker-entrypoint`, thruster CMD (`Dockerfile:20-24,47-61`). `docker-compose.yml` app+Redis, healthchecks, volume. `README.md` documents purpose, local run, compose, env vars. (Docker build/compose not re-executed in phase 3; files present and coherent.) |
| G14 | **PASS** | No auth layer (session UUID only, `application_controller.rb:24-31`). Secrets from env only; `.env` gitignored (`.gitignore`); `.env.example` has empty key; no real `sk-or-…` / `SECRET_KEY_BASE=` values in tree. Workspace-contained. |

---

## 2. CODE QUALITY ASSESSMENT

**What works**

- Clear layering: controllers thin (`MessagesController` ~47 lines), orchestration in `ConversationResponder`, persistence in `ConversationStore`, presentation broadcasts in `TurboBroadcaster`.
- Naming is mostly intention-revealing (`append_exchange`, `stream_chunk`, `over_budget?`, `SafeCalculator`).
- Value objects (`Conversation`, `ChatMessage`) stay free of I/O; store owns SQLite.
- Tools are small and single-purpose; calculator safety is isolated from the tool wrapper.
- Config centralized in `AppConfig` with env overrides and sane defaults.

**Friction / smells**

1. **`MessageBuilder` is dead production code.** Only referenced from tests (`rg MessageBuilder app/` → definition only). Comments claim it is the “source of truth” for the outgoing payload (`message_builder.rb:10-12`), but `ConversationResponder#build_chat` reimplements the same rules via `with_instructions` + `add_message` + `ask`. Drift risk if one path changes.
2. **`ConversationResponder` is the god-object for a turn** (~161 lines): streaming, persistence, title generation, error mapping, async dispatch. Still readable, but several responsibilities.
3. **Unused dependency:** `jbuilder` in `Gemfile:10` — no app usage.
4. **Leftover Rails scaffold noise:** PWA stubs (`app/views/pwa/*`), empty `concerns/.keep`, `allow_browser versions: :modern` may surprise non-“modern” clients without being documented as a product choice.
5. **Duplication of “friendly error” surfaces:** missing-key banner in show + turbo_stream partial + controller preflight; acceptable but slightly scattered.
6. **Method size:** `SafeCalculator` is long but cohesive (tokenizer/RPN/eval). Fine for the domain; not a SRP violation.

**Top 3 refactors with more time**

1. **Wire `MessageBuilder` into `ConversationResponder` (or delete it).** Either build the outgoing list once and feed the chat from that array, or drop the module and keep assertions only on FakeChat’s recorded messages. Removes the dual-source lie.
2. **Puma worker boot: reset `ConversationStore` pool after fork.** With `preload_app!` + `WEB_CONCURRENCY=2` (`config/puma.rb`), the memoized `@instance` and SQLite handles can be inherited across fork. Add `on_worker_boot { ConversationStore.reset_instance! }` (and ensure connections are not shared).
3. **Split `ConversationResponder`:** e.g. `ProviderChatFactory` (instructions/tools/history), `TurnPersister`, `TitleAfterFirstExchange` — keeps streaming orchestration thin and eases testing empty-response / generic-error branches that are currently cold.

---

## 3. TEST COVERAGE ASSESSMENT

| Metric | Value |
|--------|-------|
| Line | **97.54%** (437 / 448) |
| Branch | **80.70%** (92 / 114) |
| Suite | 69 runs, 201 assertions, 0 failures |

Source: `bin/rails test` + `coverage/.last_run.json` after that run.

**Weakest-tested area**

- `app/services/conversation_responder.rb` — **93.4%** lines, **12/23** branches. Missed lines include thread-crash logger (`:42`), `response_text` nil/non-string paths (`:120-123`), and the generic `else` friendly error (`:158`).
- Closely followed by cold branches in `SafeCalculator` (unknown-token / unsupported-operator arms that are structurally unreachable if tokenize is correct) and `TitleGenerator` non-Hash content path.
- **No automated coverage** of Stimulus controllers (`composer_controller.js`, `auto_scroll_controller.js`) or full-browser Turbo Stream + Action Cable integration.

**Failure modes NOT covered by any test**

- Empty provider response / chunks that are all blank → placeholder text path (`finalize_content` empty branch).
- Generic `StandardError` (non-RubyLLM) from the provider call → default friendly message branch.
- Background `Thread` crash inside `dispatch` when `stream_async` is true (rescue only logs; no user-visible error if crash is outside `call`’s rescue — actually `call` is wrapped; crash in executor.wrap setup is untested).
- `TitleGenerator` returning nil/blank after first exchange (broadcast skipped) — only success path with `FakeTitleGenerator`.
- `ConversationStore#purge_expired` and `#add_tokens` (lines never hit in suite).
- Real multi-process Puma (`WEB_CONCURRENCY=2`) + Redis Action Cable end-to-end (unit tests approximate with two store instances / RecordingBroadcaster).
- SQLite `busy_timeout` exhaustion under extreme write contention.
- Double-submit / concurrent turns on the same conversation racing budget check + append.
- Stimulus behavior (Enter-to-send, reset after submit, auto-scroll).
- Docker image build/run (not re-validated in this phase).
- Model refusing to call tools (G7 behavioral dependency on the LLM).

---

## 4. KNOWN DEFECTS AND RISKS

1. **Puma preload + SQLite pool fork hazard.** `config/puma.rb` enables `preload_app!` when `WEB_CONCURRENCY > 1`. `ConversationStore.instance` memoizes a `ConnectionPool` of live `SQLite3::Database` objects with no `on_worker_boot` reset. Forked workers can share or inherit bad connection state. Mitigated somewhat by WAL/busy_timeout, but this is a real production footgun.

2. **In-flight turns are fire-and-forget threads.** `ConversationResponder.dispatch` uses `Thread.new` (not a job queue). Process restart, deploy, or Puma worker kill drops active streams; user sees a stuck empty assistant bubble with no finalize/error. No timeout UI.

3. **TTL is lazy-only.** Expiry runs on `load` / `find_or_create`; `purge_expired` exists but is never scheduled. Disk can accumulate expired rows until touched.

4. **Token budget is approximate and checked only pre-turn.** `TokenEstimator` is ~4 chars/token; a single huge completion can blow past the budget after the check. Concurrent requests can both pass `over_budget?` before either persists usage.

5. **No per-conversation turn lock.** Two parallel POSTs can interleave streams and `append_exchange` order; history order may not match what the user saw.

6. **Streaming replaces full body every chunk.** Each token triggers a Turbo Stream partial re-render of the entire accumulated text (`broadcast_update_to`). Fine for demos; costly/chatty under long answers or slow clients.

7. **Session-only tenancy, no auth (by design).** Anyone with the session cookie owns the conversation; UUID is unguessable in practice but there is no CSRF-exempt API abuse story beyond Rails defaults. Demo-appropriate, not multi-tenant safe.

8. **`allow_browser versions: :modern`** (`application_controller.rb:6`) can 403 older browsers without a product-facing explanation.

9. **Composer UX vs preflight.** Missing API key shows a banner and server-side refusal, but the submit control is not actually `disabled` in `_composer.html.erb` — copy says sending is disabled; it is not client-side.

10. **Tool calling is best-effort.** Tools are registered and described; nothing forces the model to invoke them. G7 “must answer via the tool” depends on provider/model behavior and the system prompt nudge.

11. **Title generation is a second paid LLM call** on the first exchange, sequential after the main completion, with failures swallowed. Extra latency/cost; title may silently never appear.

12. **Redis required in production cable config.** `config/cable.yml` production adapter is Redis; without Redis, multi-worker streaming breaks even if the web process is up. Compose wires this; bare `RAILS_ENV=production` local runs will not stream across workers without Redis.

13. **Foreign keys + delete:** schema uses `ON DELETE CASCADE` with `PRAGMA foreign_keys = ON` — good. `delete_within` only deletes the conversation row (cascade cleans messages). No automated test specifically for cascade orphans.

14. **Branch coverage 80.7%** leaves several degraded paths unproven (empty assistant content, generic errors). Those paths exist in code but are not regression-locked.

---

## Summary

The implementation matches the G1–G14 contract in structure and in the automated suite. Quality gates are clean. The main credibility risks for external reviewers are: (a) G4/G6/G7 live multi-worker and tool behavior were not re-proven in this phase (code + unit evidence only), (b) `MessageBuilder` is not on the production path despite G5 tests leaning on it, and (c) fork-safe store lifecycle under `preload_app!` is unaddressed. None of these warranted a silent PASS-without-caveat; where design intent is solid but operational proof is thin, caveats are listed above rather than downgraded to FAIL.
