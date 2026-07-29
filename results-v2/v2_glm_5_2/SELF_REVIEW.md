# Self-Review (Phase 3)

Honest, evidence-based review of the work in this workspace. Every claim below was
re-verified against the actual code or by running a command during this phase (Ruby
4.0.6, Rails 8.1.3.1, ruby_llm 1.16.0). No new features were implemented. No files
were changed.

Verification commands actually run this phase:
- `bin/rails test` → 46 runs, 154 assertions, **0 failures, 0 errors**; SimpleCov
  **Line 392/404 = 97.02%, Branch 75/102 = 73.52%**.
- `bin/rubocop` → 43 files, **no offenses**.
- `bin/brakeman --no-pager` → **0 warnings, 0 errors**.
- `bundle exec bundle-audit check --update` → **No vulnerabilities found**.
- `bundle exec rails test:system` → **LoadError** (no `test/system`) — see defects.
- The RubyLLM API surface used by the app was cross-checked against the installed gem
  source (`RubyLLM.chat`, `with_instructions`, `with_tools`, `with_schema`, `ask`,
  `add_message`, `RubyLLM::Tool` + `param`/`Parameter`, `RubyLLM::Schema` + `string`,
  `Message#content/input_tokens/output_tokens`). **All are real**, none hallucinated.

## 1. Goal Verification Table

| Goal | Verdict | Concrete evidence |
|---|---|---|
| **G1** Rails, newest Ruby/Rails, no AR/AM/AJ, generators, at root | **PASS** | `.ruby-version`=`4.0.6`; `Gemfile` `rails "~> 8.1.3.1"`; `config/application.rb:6-14` comments out `active_record`, `active_job`, `action_mailer`, `active_storage`, `action_mailbox`, `action_text` railties. App lives at workspace root (no nested app dir). |
| **G2** Tailwind + Hotwire (Stimulus + Turbo Streams), componentized partials, no single-file dumps | **PASS** | Tailwind via `tailwindcss-rails` (`app/assets/tailwind/`, built `app/assets/builds/tailwind.css`); Stimulus controller `app/javascript/controllers/composer_controller.js`; Turbo Streams emitted in `app/controllers/replies_controller.rb` via `TurboStreamSse`. Partials split per concern: `messages/_message`, `_assistant_bubble`, `_composer`, `_error_bubble`, `_stream_source`; `conversations/_sidebar`, `_title`, `_budget`. No `fetch()+innerHTML`. |
| **G3** RubyLLM latest, OpenRouter, latest Claude Sonnet, env-overridable | **PASS** | `Gemfile` `ruby_llm "~> 1.16"` (1.16.0 installed); `config/initializers/ruby_llm.rb:11` `openrouter_api_key`; `chat_service.rb:71-73` `RubyLLM.chat(model: ChatConfig.chat_model, provider: ChatConfig.provider, ...)`; `chat_config.rb:13-20` default `anthropic/claude-sonnet-4.5` (verified present in ruby_llm 1.16.0 `models.json`), `CHAT_MODEL` env override. |
| **G4** TRUE incremental token streaming via Turbo Stream broadcasts | **PASS** | `chat_service.rb:43-49` yields accumulated content per token; `replies_controller.rb:35-37` emits a Turbo `update` per token over SSE; `app/views/messages/_stream_source.html.erb` is a `<turbo-stream-source>` wired to the SSE URL. `chat_service_test.rb:41-50` asserts the block receives `["Hello", "Hello there", "Hello there friend"]` — incremental, not a post-completion append. |
| **G5** Each user turn sent exactly once; replay excludes the pending prompt; unit test asserts exact outgoing array | **PASS** | `chat_service.rb:38-43` (`prior = replayable_messages[0...-1]`; pending sent once via `chat.ask`); `chat_service_test.rb:19-39` uses WebMock to assert the real outgoing payload is `[u1,a1,u2,a2,u3]` and that `u3` appears exactly once. Mock goes through the **real** RubyLLM provider code (HTTP intercepted, no method stubs). |
| **G6** Concurrency-safe, bounded (msg+byte), TTL persistence; survives restart; correct under WEB_CONCURRENCY=2 | **PARTIAL** | File-locked, no process-local store: `conversation_store.rb:110-124` `flock(LOCK_EX/LOCK_SH)`. Restart survival + message-cap **tested** (`conversation_store_test.rb:17-25`, `:34-45`); `WEB_CONCURRENCY=2` wired in `config/puma.rb:39-40` and `docker-compose.yml:24`. **Gap:** byte-cap eviction (`conversation_store.rb:157-165`), TTL eviction (`purge_expired!` rejection branch, `:152-155`), and corrupt-file recovery (`:137` `rescue JSON::ParserError`) are implemented but **never executed by any test** (SimpleCov shows lines 161-163 and 137 uncovered). No test runs two real Puma workers; the restart test only resets the memoized instance. |
| **G7** Exactly two tools via RubyLLM tool API — `server_time` (UTC) + `calculator` (safe arithmetic); assistant answers via the tool | **PASS** | `app/tools/server_time.rb` (`< RubyLLM::Tool`, `execute` returns UTC ISO8601) and `app/tools/calculator.rb` (`< RubyLLM::Tool`, hand-written recursive-descent `SafeEvaluator`, no `eval`); registered in `chat_service.rb:74` `.with_tools(ServerTime, Calculator)`. API verified real against gem source. `calculator_test.rb:28-34` proves injection attempts (`system('ls')`, `File.read(...)`, backticks) are rejected, not evaluated. **Caveat (not a fail):** there is no test that mocks a provider *tool-call* response to prove the tool result is incorporated into the reply — that path relies on the model and is exercised only at runtime. |
| **G8** Structured title via RubyLLM schema API after the first exchange, shown in UI | **PASS** | `app/schemas/title_schema.rb` (`< RubyLLM::Schema`, `string :title`); `chat_service.rb:98-101` `.with_schema(TitleSchema).ask(...)`; first-exchange-only guard at `:91-92`; rendered by `app/views/conversations/_title.html.erb` + `show.html.erb:2`. `chat_service_test.rb:64-78` asserts `result.title == "Greetings"`; `replies_controller_test.rb:45-46` asserts the title is stored and broadcast. `RubyLLM::Schema`/`string` verified real in the `ruby_llm-schema` gem. |
| **G9** Per-conversation token budget (env, sane default); refuse when exceeded without calling provider | **PASS** | `chat_config.rb:29-31` `MAX_CONVERSATION_TOKENS` default `100_000`, env-overridable; `chat_service.rb:36,84-86` raises `BudgetExceeded` **before** `build_chat`/`ask`; tokens accumulated in `conversation_store.rb:61`. `chat_service_test.rb:91-103` asserts `result.budget_exceeded?` and `assert_not_requested(:post, OPENROUTER_URL)` — provider never called. |
| **G10** System prompt via instructions API; missing-key preflight; every provider failure rescued to degraded UI; failed turns never replayed | **PASS** | Instructions API at `chat_service.rb:73` `.with_instructions`; missing-key banner at `show.html.erb:10-14` + `chat_config.rb:67-75`; all provider failures rescued at `chat_service.rb:64-65`; failed turns stored error-marked and excluded from replay (`message.rb:34-36` `replayable?`, `replies_controller.rb:61-63`). `replies_controller_test.rb:58-76` asserts `failed.error?` and `refute failed.replayable?`. |
| **G11** Minitest for every component; mocks mirror real API; error paths covered; SimpleCov report | **PASS** (with caveats in §3) | Tests exist for service, store, all models, both tools, all three controllers (46 runs, 0 failures). `test_helper.rb:46-66` stubs the **real OpenRouter wire format** and runs the real RubyLLM provider code (no internal-method mocking) — the hard part, done correctly. SimpleCov wired (`test_helper.rb:7-13`) with branch coverage. Caveat: branch coverage is 73.52%; several defensive/boundary error paths are uncovered — listed in §3. |
| **G12** Brakeman, RuboCop, bundle-audit all clean | **PASS** | Re-run this phase: RuboCop `43 files inspected, no offenses detected`; Brakeman `Security Warnings: 0`; `bundle-audit check --update` `No vulnerabilities found`. |
| **G13** Production-grade Dockerfile (RAILS_ENV=production, non-root, entrypoint) + compose + README | **PASS** | `Dockerfile` is multi-stage, sets `RAILS_ENV=production` (`:21`), runs as non-root `USER 1001:1001` (`:58`), `ENTRYPOINT ["/rails/bin/docker-entrypoint"]` (`:63`). `docker-compose.yml` builds + runs with `WEB_CONCURRENCY=2` and a named volume for persistence. `README.md` documents setup/run. **Caveat:** the actual `docker build` was **not** re-run in this phase (daemon 29.6.2 is available; skipped to keep this review non-mutating). Structure fully satisfies the goal. |
| **G14** No auth; no secrets committed; everything in workspace | **PASS** | No auth anywhere (no Devise, no auth `before_action`). Grep for keys found only placeholders/fakes: `README.md` `sk-or-v1-...` and `test/models/chat_config_test.rb:35` fake `"sk-or-v1-" + "x"*40`. `.gitignore` ignores `/storage/*`, `/coverage/`, `/config/master.key`, `/.env*`. Everything is inside the workspace. |

**Summary:** 13 PASS, 1 PARTIAL (G6). The PARTIAL is honest: persistence survives
restart and is message-bounded with passing tests, but the byte-cap, TTL, and
corrupt-file-recovery branches are unexercised, and no test proves the 2-worker
claim under real contention.

## 2. Code Quality Assessment

Frankly: this is a clean, small, well-factored codebase. Naming is descriptive and
consistent (`replayable_messages`, `answer_trailing`, `maybe_generate_title`,
`budget_exhausted?`). Methods and classes are small — the largest unit is
`Calculator::SafeEvaluator` (~115 lines), justified for a hand-written parser.
Layering is sensible: thin controllers → `ChatService` (orchestration) →
`ConversationStore` (persistence) + `ChatConfig` (env) + `RubyLLM`.

Issues, with specifics:

- **Duplication.** `ConversationsController#new` and `#create`
  (`app/controllers/conversations_controller.rb:12-22`) are byte-for-byte identical
  (both `create_conversation` + redirect). Worse, `create` is **dead** — no test and
  no view POSTs to it (new conversations come from `GET /conversations/new`), and
  SimpleCov confirms lines 19 & 21 are never executed. The `with_env` test helper is
  copy-pasted across `chat_service_test.rb`, `conversation_store_test.rb`, and
  `chat_config_test.rb` (the openrouter/SSE helpers are correctly centralized in
  `test_helper.rb`, so this is minor).
- **Dead code.** `Message::USER_ROLES` (`app/models/message.rb:11`) is referenced
  nowhere. `Conversation#completed_exchanges` (`conversation.rb:35`) is used only by
  its own unit test — the real title-gating logic uses a different check
  (`prior.none?(&:assistant?)` in `chat_service.rb:92`).
- **Coupling to a global singleton.** `ConversationStore.instance`
  (`conversation_store.rb:22-31`) is a process-local memoized singleton over a shared
  file; every layer (`ChatService`, controllers, views) reaches for it directly.
  Testability currently depends on `reset!` + an ENV swap. Acceptable at this size,
  but it is the main coupling smell.
- **SRP.** `ChatService` is the "heart" and holds streaming, replay, budget, tools,
  title-generation, and error-mapping. It is well-decomposed into private methods, so
  this is a soft concern, not a violation.

Top 3 things I would refactor with more time:
1. **Add an "answering" guard to fix the SSE re-entrancy race** (see §4 defect #3) —
   mark a conversation as streaming so a reconnect cannot re-answer the same pending
   message. This is the highest-value change because it closes a correctness hole,
   not a style nit.
2. **Delete the dead/duplicate code** (`USER_ROLES`, `ConversationsController#create`
  and collapse `new`/`create`, `completed_exchanges`) — removes ~30 lines and two
  confusing "why are there two identical actions?" questions.
3. **Split `ChatService`'s title-generation into its own object** (`TitleGenerator`)
   and inject the store into `ChatService` by default but make it overridable, so the
   service has a single reason to change and is unit-testable without the global
   singleton.

## 3. Test Coverage Assessment

Actual numbers from `bin/rails test` this phase:
- **Line coverage: 392 / 404 = 97.02%**
- **Branch coverage: 75 / 102 = 73.52%**

The strong points: the provider-facing contract (G4/G5/G8/G9/G10) is tested through
the **real** RubyLLM provider code with WebMock on the real OpenRouter SSE/JSON wire
format — these mocks are faithful to the real API surface, which is exactly where
this kind of app usually lies. The calculator's safety property (no code execution)
is explicitly tested with injection payloads.

**Weakest-tested area: `ConversationStore` boundary/enforcement.** SimpleCov
pinpoints the never-run lines:
- `conversation_store.rb:137` — `rescue JSON::ParserError` (corrupt/half-written
  store file recovery).
- `conversation_store.rb:161-163` — the `shrink_to_byte_limit!` eviction loop (the
  whole-store byte cap actually evicting a conversation).
- The `purge_expired!` **rejection** branch (`:154`) — TTL eviction of a stale
  conversation (the method runs on every write, but nothing is ever old enough to be
  evicted in a test).
- `chat_service.rb:63` (`NoPendingMessage` path), `:115` (`when String` title path),
  `:127` (empty-error-message fallback) — all defensive branches.

**Failure modes NOT covered by any test:**
- A **corrupt or partially-written** store file on disk (process killed mid-`fsync`).
- **Byte-cap eviction** and **TTL eviction** actually evicting anything (G6's
  bounding claims are unproven by the suite).
- **Concurrent / reconnecting SSE** — no test simulates a second `GET .../reply` while
  a stream is in flight, nor a dropped client mid-stream
  (`replies_controller.rb:40` `rescue ActionController::Live::ClientDisconnected` is
  never exercised).
- **Real two-process `WEB_CONCURRENCY=2` flock contention** — the restart test only
  resets the in-process memo; no fork/spawn test contends on the lock.
- A **provider tool-call round-trip** (G7) — no mocked tool-call response proves the
  tool result reaches the final reply.

## 4. Known Defects and Risks

1. **CI `system-test` job is broken (and the workflow is gitignored).**
   `.github/workflows/ci.yml:93-116` runs `bin/rails test:system`, but `test/system`
   does not exist — re-running it raises `LoadError: cannot load such file --
   .../test/system`. That CI job would fail. Additionally `.gitignore:37` ignores
   `/.github`, so in a standalone repo the workflow would not be committed at all.
   (Note: this does not violate G12 — Brakeman/RuboCop/bundle-audit, the three named
   gates, all pass clean.)
2. **SSE re-entrancy / double-answer race (correctness).** `replies_controller#show`
   has no idempotency guard. A `<turbo-stream-source>` reconnect (common with Turbo)
   while a stream is already in flight issues a second `GET .../reply`; both see the
   same pending user message, so the provider is called twice and two assistant
   messages get persisted. The `flock` serializes store access but does **not** mark a
   conversation as "currently being answered." No test covers this.
3. **Unbounded external blast / cost abuse surface.** With no auth (explicitly a demo
   per G14), any unauthenticated `GET /conversations/:id/reply?token=anything` that
   finds a pending user message triggers a real, billable provider call. Acceptable
   for the stated "no-auth demo," but it is an operational/cost risk.
4. **Byte-cap / TTL / corrupt-recovery are unverified (G6).** Implemented
   (`conversation_store.rb:137,152-165`) but never executed by tests (see §3). The
   logic reads correctly, but a future change there could silently regress with no
   signal.
5. **Weak `SECRET_KEY_BASE` default under `RAILS_ENV=production`.**
   `docker-compose.yml:19` falls back to `please-change-this-secret-key-base-value`
   while `RAILS_ENV: production`. For a local demo this is fine, but it is a weak
   cookie-signing key if anyone runs the compose stack as-is publicly (cookie forgery
   risk). Not a committed secret, so it does not violate G14.
6. **Store grows unbounded on disk between writes.** TTL/byte eviction run **only
   inside a `write` transaction** (`conversation_store.rb:100-101`). A store that is
   only ever read (or never written to again) is never trimmed, so stale
   conversations can persist past their TTL until the next append. Minor at this
   scale, but worth knowing.
7. **Minor dead/duplicate code** (quality, not correctness): `Message::USER_ROLES`
   unused; `ConversationsController#create` duplicates `#new` and is never called
   (uncovered lines 19, 21); `Conversation#completed_exchanges` is app-dead (test
   only).
