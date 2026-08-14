# SELF_REVIEW — LLM Chat (v2_qwen3_8_max)

Phase 3 self-review. Every verdict below was re-verified against the actual code
and by re-running commands on 2026-08-14, not recalled from build time.
No code changes were made during this review: the test suite, all three quality
gates, a fresh local boot, and a fresh live provider call were all green, so
nothing qualified as "broken" under the surgical-fix allowance. Suspected
weaknesses are recorded in section 4 instead.

Verification commands run for this review:

- `bin/rails test` → 62 runs, 226 assertions, 0 failures, 0 errors, 0 skips
- `bundle exec brakeman -q --no-pager` → 0 warnings (exit 0)
- `bundle exec rubocop` → 43 files inspected, no offenses (exit 0)
- `bundle exec bundle-audit check` → "No vulnerabilities found" (exit 0)
- `bin/rails server -p 3210` + `curl /up` → 200; `/` renders the composer
- Live `rails runner` smoke test through OpenRouter → correct reply, tool result,
  schema title, and token counts (details in G3/G7/G8 rows)
- `docker ps` / `curl` against the still-running compose stack → `project-web-1`
  healthy, `/up` → 200, running as user `1000:1000` with `WEB_CONCURRENCY=2`

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 — Newest Ruby/Rails from mise; no AR/AM/AJ; generators; workspace root | PASS | `.ruby-version` = `ruby-4.0.6` and `mise latest ruby` = 4.0.6; `Gemfile.lock:225` = rails 8.1.3.1, which `gem search "^rails$" --remote` confirms is the current release. `config/application.rb:6-12` requires only active_model/action_controller/action_view/action_cable/test_unit (AR, AJ, AM, AS, AMailer commented out); no ORM gems in `Gemfile`. Standard generated skeleton present (`bin/`, `Procfile.dev`, `.kamal/`, `config/deploy.yml`, PWA views, `.github/workflows/ci.yml`). App lives at workspace root, no nested app dir. |
| G2 — Tailwind + Hotwire/Stimulus/Turbo Streams, componentized partials, no JS/CSS dumps | PASS | Tailwind v4 via tailwindcss-rails (`app/assets/tailwind/application.css` = `@import "tailwindcss"`; build log shows `tailwindcss v4.3.3`). 5 single-purpose Stimulus controllers in `app/javascript/controllers/` (chat_form, messages, reply_signal, pending_watchdog, application); 14 view templates split into partials (`app/views/conversations/_*.erb`, `app/views/messages/_*.erb`). All dynamic updates are Turbo Stream broadcasts/render (`reply_streaming.rb:90-136`, `messages_controller.rb:29-34`); `grep "fetch(\|innerHTML" app/javascript/` finds nothing. `app/assets/stylesheets/application.css` is the empty Propshaft manifest comment, not a CSS dump. |
| G3 — ruby_llm latest, OpenRouter, latest Claude Sonnet, env-overridable | PASS | `Gemfile:22` `gem "ruby_llm", "~> 1.16"` → installed 1.16.0 (current). `config/initializers/ruby_llm.rb:10-14` sets `openrouter_api_key`; `lib/chat_service.rb:74` passes `provider: :openrouter`. Default model `anthropic/claude-sonnet-4.6` (`lib/llm_config.rb:7`), overridable via `CHAT_MODEL` (`llm_config.rb:14-16`, tested in `test/lib/llm_config_test.rb`). Re-verified live today: `rails runner` ChatService call returned the correct answer via OpenRouter. |
| G4 — True token streaming via Turbo Stream broadcasts | PASS | `chat_service.rb:58-64` uses RubyLLM's block form of `Chat#complete`, accumulating chunks and calling `on_chunk`; `reply_streaming.rb:85-96` broadcasts each progress snapshot as a `turbo_stream.replace` of `pending-content`. Live evidence: `log/validation-dev.log:119-128` shows successive incremental broadcasts (`"#"` → growing text); phase-2 WebSocket capture recorded 16 monotonic progress frames before the final frame; `test/controllers/messages_controller_test.rb:40-42` asserts progress + final broadcasts. Not a completion-time append. |
| G5 — Multi-turn payload sends each user turn exactly once, with unit test | PASS | `reply_streaming.rb:33-34` replays stored history minus the prompt; `chat_service.rb:73-80` appends the prompt exactly once. Exact-payload unit test: `test/lib/chat_service_test.rb:14-35` asserts the full outgoing `[system, user, assistant, user]` array and one-occurrence-per-user-turn; controller-level test `messages_controller_test.rb:45-57`. Live proof: in `storage/conversations/87e28764-*.json` turn 3 asked "what was the earlier result" and the model answered `97408247365` — the exact value from turn 2 (independently recomputed correct: 123456*789012 − 54321/3). |
| G6 — Concurrency-safe, bounded persistence with TTL, survives restart | PASS | `lib/conversation_repository.rb`: exclusive `flock` (123-133), atomic tmp+rename writes (116-121), message-count/byte caps trimming oldest first (110-114), TTL purge (101-108). Multi-process test forks 2 processes × 10 updates and asserts all 20 survive (`conversation_repository_test.rb:94-112`) — passes. Bounds/TTL tests at lines 60-92. Files on disk in `storage/conversations/` survived server restarts across phases 1→2→3. Phase 2 ran Puma cluster mode `WEB_CONCURRENCY=2` (`log/validation-mw.log`) and compose with 2 workers, end-to-end. |
| G7 — Exactly two tools via RubyLLM tool API; safe arithmetic | PASS | `chat_service.rb:77` `chat.with_tools(ServerTimeTool, CalculatorTool)`; test asserts `chat.tools.keys == [:server_time, :calculator]` (`chat_service_test.rb:44-47`). Tools subclass `RubyLLM::Tool` with real `description`/`param`/`execute` API (verified against installed gem source). Calculator uses a hand-rolled recursive-descent parser, no `Kernel#eval` anywhere (`lib/arithmetic_evaluator.rb`; grep for `eval` in lib/app finds none). Live: server_time returned `2026-08-14T19:05:10Z`; calculator returned `97408247365` and (today) `56` for 7*8 — all numerically correct; tool loop test `chat_service_test.rb:73-101` exercises the real RubyLLM tool loop. |
| G8 — Structured-output title after first exchange, shown in UI | PASS | `chat_service.rb:106-110` builds the title chat with `chat.with_schema(ConversationTitleSchema)` (`lib/conversation_title_schema.rb` subclasses `RubyLLM::Schema`); trigger logic in `reply_streaming.rb:64-73`; title rendered in `app/views/conversations/_header.html.erb`. Live: stored titles "History of Lighthouses Essay" and "Server Time Timestamp Request" in `storage/conversations/*.json`; today's smoke test produced "Simple Multiplication Question" (207 tokens). Failure isolation tested (`messages_controller_test.rb:128-140`). |
| G9 — Token budget per conversation, env-configurable, friendly refusal | PASS | Usage metered from `chat.ruby_llm` instrumentation events (`chat_service.rb:51-65`; railtie sets the instrumenter to ActiveSupport::Notifications — verified in gem source). Budget gate before any provider call at `messages_controller.rb:20-23` with message at 58-62; default 100_000 via `CHAT_TOKEN_BUDGET` (`llm_config.rb:8,18-20`). Test `messages_controller_test.rb:84-95` asserts refusal without provider call; live conversations show real counts (2181, 4872). UI shows `tokens / budget` in `_header.html.erb`. |
| G10 — Instructions API, missing-key preflight, rescued failures, failed turns never stored | PASS | System prompt via `chat.with_instructions` (`chat_service.rb:75`, asserted in `chat_service_test.rb:49-53`). Missing-key preflight in both controllers (`conversations_controller.rb:19-22`, `messages_controller.rb:14-17`) plus `ChatService::MissingApiKey` raise (`chat_service.rb:44,114-116`); tested. `reply_streaming.rb:52-59` rescues StandardError, rolls back the stored user turn (76-83) and broadcasts a degraded bubble (`messages/_error_message.html.erb`); per-error-class friendly messages tested (`messages_controller_test.rb:117-126`); rollback + empty-history assertion at 97-110. |
| G11 — Minitest for every component, real-API mocks, error paths, SimpleCov | PASS | 62 tests / 226 assertions / 0 failures across 9 test files covering every lib class and every controller. Mocks mirror the real API: `chat_service_test.rb:157-162` stubs only `Chat#provider_completion` on genuine `RubyLLM::Chat` objects — I verified each method used (`with_instructions`, `add_message`, `with_tools`, `with_schema`, `complete`, `ask`, `Chunk`, `ToolCall`, error classes, `chat.ruby_llm` event with `input_tokens`/`output_tokens`) exists in the installed ruby_llm-1.16.0 source. Error paths covered (missing key, provider errors, corrupt JSON, TTL, failed title, failed broadcast excluded — see §3). SimpleCov wired in `test/test_helper.rb:3-10`, HTML report in `coverage/`. Caveat: no system/browser tests exist (see §3). |
| G12 — Brakeman, RuboCop, bundle-audit clean | PASS | Re-run today: `brakeman -q --no-pager` → "Security Warnings: 0" (exit 0); `rubocop` → "43 files inspected, no offenses detected" (exit 0); `bundle-audit check` → "No vulnerabilities found" (exit 0). CI workflow wires all three plus `importmap audit` (`.github/workflows/ci.yml`). |
| G13 — Production-grade Dockerfile + compose + README | PASS | `Dockerfile`: multi-stage, `RAILS_ENV=production` (line 24), non-root `USER 1000:1000` (72), `bin/docker-entrypoint` generates a persistent `SECRET_KEY_BASE` on first boot. `docker-compose.yml`: web + redis, `WEB_CONCURRENCY=2`, `REDIS_URL` for cross-worker Action Cable, persistent `conversation-data` volume, healthcheck on `/up`. Re-verified today: `project-web-1` still Up/healthy, `/up` → 200, user 1000:1000. Phase-2 record: `docker build` exit 0, compose end-to-end chat (calculator 27*43 → "1161" + title persisted in the volume), WebSocket capture of 16 streaming frames through the compose stack. `README.md` documents purpose, env vars, local run, tests, Docker. |
| G14 — No auth, no secrets committed, everything in workspace | PASS | No authentication code anywhere (no devise/http-basic/`has_secure_password`; `Gemfile:25` bcrypt commented out). `grep -rnE "sk-or-…-ant-…" .` finds no hardcoded keys; compose passes `OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:-}` from host env only; README examples use `<your secrets file>` placeholders. `config/master.key` exists on disk (Rails-generated) but is ignored by both `.gitignore` and `.dockerignore`; `credentials.yml.enc` is docker-ignored and the entrypoint supplies `SECRET_KEY_BASE` at runtime instead. All files inside the workspace root. |

**Summary: 14 PASS, 0 PARTIAL, 0 FAIL** — with the caveats in sections 3 and 4,
which do not contradict any goal as written but matter for production use.

## 2. CODE QUALITY ASSESSMENT

Overall the codebase is small (~1,100 lines of Ruby + ~200 lines of JS), consistently
styled (RuboCop omakase clean), and well-commented where intent is non-obvious
(frozen_string_literal everywhere, goal references in comments).

**Naming.** Good. Classes/methods read as their purpose (`ConversationRepository`,
`rollback_failed_turn`, `broadcast_progress`, `enforce_bounds`). Constants for magic
values (`PROGRESS_INTERVAL`, `TITLE_TRUNCATION`, `ID_PATTERN`). No meaningful offenders.

**Single responsibility.** Mostly good. Controllers are thin (all ≤ 63 lines); domain
logic lives in `lib/`. The two soft spots:
- `app/controllers/concerns/reply_streaming.rb` (158 lines) is the largest coupling
  point: it mixes thread orchestration, provider invocation, persistence, title
  triggering, three kinds of broadcasts, and error-class-to-message mapping. It works,
  but it is a concern doing five jobs, and it is only testable through controller seams
  (`async_runner`/`cattr_accessor` injection — workable, but a smell).
- `lib/chat_service.rb` duplicates its token-metering lambda verbatim in
  `stream_reply` (lines 51-55) and `generate_title` (lines 91-95).

**Duplication.** The metering lambda above is the only real copy-paste. The
`respond_to` turbo_stream/html blocks in the three controllers are similar but differ
enough in payloads that extracting them would likely hurt clarity.

**Dead code.** One genuine item: `Conversation#first_exchange_complete?`
(`lib/conversation.rb:54-56`) is referenced only by its own unit test. The production
title trigger (`reply_streaming.rb:64-67`) re-implements a slightly different version
of the same condition (checks "any assistant message" rather than message count ≥ 2).
Two divergent definitions of "first exchange complete" existing side by side is a
latent-bug hazard. `script/` and several `.keep`-only test dirs are empty scaffolding
(normal Rails output, harmless).

**Method/class size.** All methods are short (longest is `deliver_reply` at ~34 lines
including rescue). No class exceeds 160 lines. Fine.

**Coupling between layers.** Clean direction: controllers → ChatService /
ConversationRepository → plain domain objects; views never touch the provider.
`LlmConfig` centralizes env access (good). The one structural coupling: controllers
reach into `ReplyStreaming` internals via class-level mutable seams
(`chat_service=`, `async_runner=`) — pragmatic for tests, but global mutable state
shared across all controller classes that include the concern.

**Top 3 refactors with more time:**
1. **Extract a `ReplyRunner` service object** out of `ReplyStreaming` (thread spawn,
   history prep, stream call, title trigger, persist, broadcasts, rollback). The
   concern would shrink to a 10-line controller adapter, the runner would be directly
   unit-testable without controller seams, and the biggest SRP violation disappears.
2. **Deduplicate token metering in `ChatService`** into one private
   `meter_tokens { ... }` helper wrapping `ActiveSupport::Notifications.subscribed`;
   removes the only copy-paste and makes the instrumentation seam single-sourced.
3. **Reconcile or delete `Conversation#first_exchange_complete?`** — either make
   `maybe_generate_title` use it (single definition of the invariant) or delete it and
   its test. Leaving two divergent definitions invites future regression.

## 3. TEST COVERAGE ASSESSMENT

SimpleCov (re-run today, `bin/rails test`):

- **Line coverage: 92.25% (417/452 lines)** — reported by SimpleCov, HTML at `coverage/index.html`.
- **Branch coverage: not measured.** `test_helper.rb` does not call
  `enable_coverage :branch`, so there is no branch percentage to report. This is a gap,
  not a number.
- Per-file: everything is at 100% except `app/controllers/concerns/reply_streaming.rb`
  (96.8%, 61/63 — lines 58 and 82) and `lib/conversation_repository.rb` (98.7%, 76/77
  — line 75). Note: one forked-subprocess coverage result from the multi-process test
  was excluded from the merge (`merge_timeout`), so the reported number is the
  in-process suite alone; the forked paths exercise the same repository code that the
  in-process tests already cover.

**Weakest-tested area:** `app/controllers/concerns/reply_streaming.rb`. Its two
uncovered lines are both failure-of-failure paths: line 58 (the failure broadcast
itself raising — double-fault logging path) and line 82 (rollback when the
conversation vanished mid-failure). More importantly, the concern's *concurrency*
behavior (real threads, interleaved turns) is never exercised — controller tests force
the synchronous runner.

**Failure modes with NO test coverage:**
- Concurrent turns on one conversation (double-send / rapid second message while a
  reply is in flight) — the race described in §4.1.
- The lost-broadcast race of §4.2 (reply completes before the browser subscribes;
  stuck pending bubble, no-op retry).
- Multi-worker Action Cable delivery via the Redis adapter (only the in-process
  `async`/`test` adapters are exercised; the compose Redis path was verified manually
  in phase 2, not by a test).
- All Stimulus controllers / browser behavior — there are **zero system tests**;
  `capybara` and `selenium-webdriver` are in the Gemfile and `ci.yml` declares a
  `system-test` job, but no `test/system/` directory exists. The JS is untested.
- `bin/docker-entrypoint` secret generation and the production container environment.
- A single message larger than `CHAT_MAX_BYTES` (bounds loop empties the conversation —
  see §4.7).
- Provider failure *after* partial streaming (chunks already broadcast, then the
  connection dies) — the rollback path is tested with a service that raises before any
  chunk, not mid-stream.

## 4. KNOWN DEFECTS AND RISKS

1. **No per-conversation turn serialization (race).** `MessagesController#create`
   stores the user message and spawns a reply thread; nothing prevents a second turn
   starting while the first is in flight. The history-pop guard
   (`reply_streaming.rb:34`) only removes the prompt if it is still the *last* stored
   message, so a rapid second send makes the first reply thread replay the second
   user message inside its history (that prompt is then sent twice overall), and the
   two assistant replies persist in completion order, not request order. Single-user
   demo scale makes this unlikely; it is a real correctness hazard under any
   concurrent use of one conversation.
2. **Lost-broadcast race → stuck "Thinking…" bubble.** If the reply completes between
   the server rendering `show` (which renders the pending bubble because
   `pending_turn?` is true) and the browser's cable subscription activating, the
   completion broadcast is missed. The bubble then stays pending; the 45 s watchdog
   offers Retry, but `RepliesController` sees `pending_turn? == false` (the assistant
   message is already stored) and redirects — the retry is a no-op. Only a manual
   reload fixes the view. Window is small (async adapter, same process) but non-zero,
   and larger with Redis latency.
3. **Silent degradation without Redis under multiple workers.** `config/cable.yml`
   falls back to the `async` adapter when `REDIS_URL` is unset; with
   `WEB_CONCURRENCY>1` each Puma worker then has its own cable hub, so a worker that
   did not serve the page's WebSocket never delivers the broadcasts. Compose always
   sets `REDIS_URL`, but a bare multi-worker `rails server` without Redis degrades
   with no warning logged.
4. **Lock files accumulate.** `with_lock` creates `<id>.lock` files that are never
   removed; TTL purging deletes the `.json` but leaves the `.lock` (visible in
   `storage/conversations/`). Unbounded slow leak of zero-byte files over the
   lifetime of a volume.
5. **Token accounting undercounts failed turns.** Tokens are recorded only after a
   successful completion (`reply_streaming.rb:45-49`). A turn that consumes provider
   tokens and then fails (network drop mid-stream, rate limit after partial work) is
   rolled back and its usage never counted, so the G9 budget can be exceeded in real
   spend. Counts are also approximate by design (instrumentation payloads only).
6. **Provider error text surfaced to the UI.** `friendly_error` for generic
   `RubyLLM::Error` echoes up to 200 chars of the upstream message
   (`reply_streaming.rb:153`). Provider error bodies can include request details;
   minor information-disclosure surface for a no-auth demo, unacceptable as-is for
   anything public.
7. **Bounds trimming can produce assistant-first history or empty conversations.**
   `enforce_bounds` (`conversation_repository.rb:110-114`) shifts oldest messages
   regardless of role: after trimming, replayed history may start with an assistant
   message (some providers reject or misbehave on assistant-first conversations), and
   a single user message larger than `CHAT_MAX_BYTES` trims the conversation to empty.
8. **TTL is lazy.** Expiry only happens on `find`/`list`; expired conversations stay
   on disk (and count against nothing, but occupy the volume) until accessed. No
   background reaper.
9. **`docker exec` operational gotcha.** The entrypoint exports `SECRET_KEY_BASE`
   only for the container's main process tree; `docker exec ... bin/rails runner`
   fails with "Missing secret_key_base" unless the operator re-exports it manually
   (confirmed in phase 2). Not a code bug, but a real foot-gun for debugging.
10. **No authentication and no rate limiting (by design, G14).** Anyone who can reach
    the port can spend OpenRouter credits without bound beyond the per-conversation
    token budget; there is no per-IP throttle on conversation creation. Acceptable for
    the demo brief, must be called out for any real deployment.
11. **Single-host persistence.** flock protects across processes on one host; the
    file store gives no cross-host consistency. Fine for the single-node compose
    setup, but scaling out with a shared network volume would be racy (flock over NFS
    is unreliable).
12. **Test-infra gaps as risks.** Zero browser/system tests for a streaming SPA means
    regressions in the Stimulus controllers, autoscroll, or cable wiring ship green.
    Branch coverage being disabled hides untested conditionals (e.g. the
    `content["title"] || content[:title]` fallbacks).

No secrets are known or suspected to be committed (verified by grep in §G14), and no
data-loss path was found for the happy single-user flow.
