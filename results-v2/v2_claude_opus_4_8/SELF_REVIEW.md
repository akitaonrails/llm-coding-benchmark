# Self-Review

Evidence-based review of this workspace. All commands below were run against the
code as it stands now (Ruby 4.0.6, Rails 8.1.3, ruby_llm 1.16.0).

Verification commands used:
- `bin/rails test` → **69 runs, 201 assertions, 0 failures, 0 errors, 0 skips**
- SimpleCov → **Line 97.54% (437/448), Branch 80.70% (92/114)**
- `bundle exec rubocop` → **53 files, no offenses**
- `bundle exec brakeman` → **0 security warnings**
- `bundle exec bundle-audit check --update` → **No vulnerabilities found**

---

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
|------|---------|----------|
| **G1** Rails, newest Ruby/Rails, no AR/AM/AJ, generators, root | **PASS** | `.ruby-version` = ruby-4.0.6; `Gemfile.lock` rails (8.1.3). `config/application.rb:6-14` comments out `active_record`, `active_job`, `action_mailer` railties; loads `active_model`, `action_controller`, `action_view`, `action_cable`. No `config/database.yml`. App files (`app/`, `config/`) are at workspace root — no nested app dir. |
| **G2** Tailwind + Hotwire (Stimulus + Turbo Streams) + partials | **PASS** | `tailwindcss-rails`, `turbo-rails`, `stimulus-rails` in Gemfile. Stimulus controllers `app/javascript/controllers/{auto_scroll,composer}_controller.js`. Turbo Streams: `app/views/messages/create.turbo_stream.erb`, `turbo_stream_from` at `show.html.erb:6`. 10 partials under `app/views/{messages,conversations}`. No single-file CSS/JS dump; no `fetch()+innerHTML`. |
| **G3** RubyLLM (`ruby_llm`) via OpenRouter, latest Claude Sonnet, env-overridable | **PASS** | `Gemfile` `gem "ruby_llm"` → 1.16.0. `config/initializers/ruby_llm.rb:11` `config.openrouter_api_key`. `config/initializers/app_config.rb:13` `ENV.fetch("CHAT_MODEL", "anthropic/claude-sonnet-4.6")`. `RubyLLM.chat(provider: :openrouter)` in responder/title_generator. |
| **G4** True token streaming via Turbo Stream broadcasts | **PASS (unit-verified)** | `conversation_responder.rb:86-94` streams inside `chat.ask(&block)`, reassigning an accumulator and calling `broadcaster.stream_chunk` per chunk. `turbo_broadcaster.rb:14` `broadcast_update_to`. Test `conversation_responder_test.rb:36-45` asserts broadcasts carry `["Hel","Hello","Hello world"]` (incremental, not one final blob). Caveat: incremental delivery is proven only against a fake; no live-provider streaming test exists. |
| **G5** Multi-turn: each user turn sent exactly once; unit test asserts exact array | **PASS** | Responder replays `@conversation.messages` (history excludes the new prompt) then `chat.ask(@prompt)` appends it once (`:54,:86,:109`). Test `conversation_responder_test.rb:66-83` asserts `chat.messages == MessageBuilder.outgoing(...)` and counts the new user turn exactly once (`:82`). See Known Defect #4 re: MessageBuilder not being the real production path. |
| **G6** Concurrency-safe, bounded, TTL persistence; survives restart; WEB_CONCURRENCY=2 | **PASS** | `conversation_store.rb`: on-disk SQLite (survives restart), WAL + `busy_timeout=5000` + `BEGIN IMMEDIATE` transactions (`:144-152,:236-244`), `ConnectionPool`. Count cap + byte cap trimming (`:183-204`), TTL expiry (`:52,:252`). Tests: cross-process share `store_test.rb:43-52`, count cap `:54-62`, byte cap `:64-74`, TTL `:76-87`, 8-thread concurrent writers `:103-113`. No process-local store. |
| **G7** Exactly two tools (`server_time`, `calculator`) via RubyLLM tool API | **PASS (registration)** | `app/tools/{server_time_tool,calculator_tool}.rb` subclass `RubyLLM::Tool`. `responder.rb:108` `chat.with_tools(ServerTimeTool, CalculatorTool)`. Test `conversation_responder_test.rb:63` asserts `chat.tools.keys == %i[server_time calculator]`. Tool unit tests exist. Caveat: end-to-end "assistant actually invokes the tool" needs a live provider and is not tested. See Defects #1/#2 for calculator edge cases. |
| **G8** Structured-output title after first exchange, shown in UI | **PASS** | `title_schema.rb` `class TitleSchema < RubyLLM::Schema` (ruby_llm-schema 0.4.0). `title_generator.rb:20` `chat.with_schema(TitleSchema)`. Generated only on first exchange (`responder.rb:126-136`), broadcast to `conversation_title` target, rendered `conversations/_title`. Tests `conversation_responder_test.rb:85-104` (generates once, not on later turns). |
| **G9** Token budgeting, refuse in-UI when exceeded, no provider call | **PASS** | `messages_controller.rb:14,:32-34` `return render_over_budget if over_budget?` before `dispatch`. Budget `AppConfig.token_budget` (env `CONVERSATION_TOKEN_BUDGET`, default 20_000). `over_budget.turbo_stream.erb` renders the refusal. Test `messages_controller_test.rb:23` asserts refusal without provider call. Approximate accounting via `TokenEstimator` (~4 chars/token). |
| **G10** System prompt, missing-key preflight, rescue every failure, never persist failed turn | **PASS** | System prompt `responder.rb:107` `with_instructions(AppConfig.system_prompt)`. Preflight `messages_controller.rb:13` + `application_controller.rb:16`. `rescue StandardError` `responder.rb:76,140-160` maps errors to friendly messages and broadcasts a degraded state. Persistence happens only after a successful stream (`:57-66`), so failures store nothing — tested `conversation_responder_test.rb:106-128`. |
| **G11** Minitest per component, real-API mocks, error paths, SimpleCov | **PASS** | 20 test files under `test/`. `test/support/test_doubles.rb` `FakeChat` mirrors real `Chat#with_instructions/with_tools/with_schema/add_message/ask(&block)` (verified against gem source — see Notes). Error paths covered (unauthorized/rate-limit/overloaded/payment). SimpleCov wired in `test/test_helper.rb`; report at `coverage/`. |
| **G12** Brakeman, RuboCop, bundle-audit clean | **PASS** | RuboCop: 53 files, no offenses. Brakeman: 0 warnings. bundle-audit: no vulnerabilities (advisory-db updated 2026-07-25). |
| **G13** Production Dockerfile (non-root, entrypoint), docker compose, README | **PASS** | `Dockerfile:24` `RAILS_ENV="production"`, `:65-66` `useradd rails` + `USER 1000:1000`, `:73` `ENTRYPOINT bin/docker-entrypoint`. `docker-compose.yml`: web + redis, `WEB_CONCURRENCY=2`, named volume for SQLite, healthchecks. `README.md` (6.9 KB) documents purpose/setup/run. Not executed here (no Docker build run in phase 3). |
| **G14** No auth, no committed secrets, everything in workspace | **PASS** | No authentication (session id only, `application_controller.rb:24-32`). `.env.example` holds placeholders only; `.gitignore`/`.dockerignore` exclude `.env`. Compose injects `OPENROUTER_API_KEY` from host env (`docker-compose.yml:48`). bundle-audit/brakeman clean; grep found no literal keys in source. |

**Summary: 14/14 PASS.** Two goals (G4, G7) carry honest caveats about live-provider behavior being unit-verified rather than integration-verified — see caveats and Known Defects.

---

## 2. Code Quality Assessment

Overall the codebase is clean, small, and well-factored. Services are single-purpose
(`SafeCalculator`, `TokenEstimator`, `TitleGenerator`, `TurboBroadcaster`,
`ConversationStore`, `ConversationResponder`). Naming is descriptive and consistent.
`frozen_string_literal` everywhere; RuboCop-clean. Layer coupling is reasonable: the
responder depends on injected collaborators (`store`, `chat`, `broadcaster`,
`title_generator`), which is what makes it testable without a live provider.

Weaknesses:

- **`ConversationResponder#call` mixes several concerns** (streaming, token math,
  persistence, meter broadcast, title generation). It is readable but is the largest
  behavioral surface in the app; the orchestration and the "what to persist" policy
  live in the same method.
- **Duplicated chat-construction knowledge.** `RubyLLM.chat(model:, provider: :openrouter,
  assume_model_exists: true)` appears in both `conversation_responder.rb:102` and
  `title_generator.rb:18`. If the provider wiring changes, two call sites must change.
- **`MessageBuilder` is dead in production** (grep: referenced only by the G5 test, never
  by `app/`). Its docstring claims "the ConversationResponder feeds the provider from this
  same source of truth" — that is inaccurate; the responder builds the outgoing array via
  `add_message`/`with_instructions`/`ask`, a parallel path. See Known Defect #4.
- **`ChatMessage` / `Conversation` carry helper methods that aren't all used** (e.g.
  `Conversation#first_exchange_complete?`, `#user_turn_count`, `#display_title` — only some
  are exercised). Minor dead-ish surface.

Top 3 refactors I'd do with more time:
1. **Extract a `ChatFactory`** so the `RubyLLM.chat(...)` construction lives in one place
   (removes the duplication between responder and title generator).
2. **Make `MessageBuilder` the real production source of truth** — have the responder build
   its outgoing array from `MessageBuilder.outgoing` and feed the chat from it, so the G5
   test guards the actual payload instead of a parallel reconstruction. Otherwise delete
   `MessageBuilder` and assert directly on `FakeChat`.
3. **Split `ConversationResponder#call`** into a thin orchestrator + a `Persistence`/policy
   collaborator, so "stream", "persist exchange", and "generate title" are independently
   readable and independently testable.

---

## 3. Test Coverage Assessment

- **SimpleCov line coverage: 97.54% (437/448).**
- **SimpleCov branch coverage: 80.70% (92/114).** Branch coverage is the real weak spot.

Per-file lowest line coverage:
- `conversation_responder.rb` — 93.4% (71/76)
- `title_generator.rb` — 95.8% (23/24)
- `conversation_store.rb` — 97.4% (112/115)
- `safe_calculator.rb` — 97.9% (92/94)

**Weakest-tested area: `ConversationResponder` error/finalize branches and
`TitleGenerator#extract_title`.** The `finalize_content`/`response_text` fallback paths
(empty stream → fall back to `response.content`; nil response) and `TitleGenerator`'s
Hash-vs-String/`nil` branches drive most of the 22 uncovered branches.

Failure modes NOT covered by any test:
- **Live tool invocation (G7).** No test proves the model actually calls `server_time` or
  `calculator` through RubyLLM — only tool registration and the tool classes in isolation.
- **`SafeCalculator` complex-number path** (`(-4) ** 0.5`) — no test; it raises an
  unhandled `RangeError` (Defect #1).
- **Unary-minus-vs-exponent precedence** — `-2 ** 2` returns `4`, no test pins the intended
  semantics (Defect #2).
- **Real streaming over Action Cable / Redis.** No integration test boots Puma with
  `WEB_CONCURRENCY=2` and asserts a browser receives incremental broadcasts; the guarantee
  is architectural + unit-level only.
- **Background-thread crash path** (`dispatch`'s `rescue` on `Thread.new`) — logged, not
  asserted; a mid-turn thread crash leaves the assistant placeholder spinning forever with
  no error bubble (Defect #3).
- **Store trim under a byte cap smaller than one message** — the "keep at least one message"
  guard (`store.rb:198-200`) means a single oversized message can exceed `max_bytes`; no
  test covers that boundary.

---

## 4. Known Defects and Risks

1. **`SafeCalculator` leaks `RangeError` on complex results (`calculator` tool).**
   `SafeCalculator.evaluate("(-4) ** 0.5")` raises `RangeError: can't convert 0.0+2.0i into
   Integer` from `normalize` (`safe_calculator.rb:166`). `CalculatorTool#execute` only
   rescues `SafeCalculator::Error` (`calculator_tool.rb:19`), so this propagates out of the
   tool. Net effect: not a crash of the app (the responder's `rescue StandardError` catches
   it and shows the generic degraded message) but the user gets "something went wrong"
   instead of the friendly "could not evaluate expression". Fix: rescue `StandardError` in
   the tool, or guard `Complex`/non-real results in `SafeCalculator`.

2. **Non-standard operator precedence: `-2 ** 2` evaluates to `4`, not `-4`.**
   Unary minus is given `NEG_PRECEDENCE = 4`, higher than `**` (3), so it binds as
   `(-2) ** 2`. Standard math/most languages (e.g. Python) treat `-2 ** 2` as `-(2**2) =
   -4`. This is a silent correctness deviation for any expression with a leading/negated
   base under exponentiation. Low impact (demo calculator) but real and untested.

3. **Unbounded background threads + silent failure on thread crash.**
   `ConversationResponder.dispatch` spawns a raw `Thread.new` per turn in async mode
   (`conversation_responder.rb:38-47`) with no pool/cap. Under concurrent load this creates
   unbounded threads (each briefly holding a SQLite pool connection of size 5 → contention).
   If the thread raises before broadcasting (the top-level `rescue` at `:41` only logs), the
   assistant placeholder bubble streams nothing and never resolves to an error state — the
   UI shows a permanent "typing" indicator. Consider a bounded executor and a
   broadcast-error in the thread's rescue.

4. **G5's test does not guard the actual production payload.**
   The responder builds the outgoing message array via `with_instructions` + `add_message` +
   `ask`; `MessageBuilder.outgoing` (the thing the G5 test compares against) is never called
   in `app/`. The test relies on `FakeChat` faithfully mirroring real RubyLLM ordering. It
   does today (verified `add_message`/`ask`/`with_instructions` against ruby_llm 1.16.0
   source), but a future RubyLLM change to message ordering/dedup would not be caught by
   this test — the fake would drift with the assertion, not with the real gem.

5. **Token budget is checked before an async turn commits — a race window (G9).**
   `over_budget?` reads `token_usage` at request time and the debit happens later on the
   background thread. Two near-simultaneous turns can both pass the check and jointly exceed
   the budget by roughly one turn. Bounded and low-severity, but not strictly enforced.

6. **Approximate token accounting can under/over-count vs. the provider.**
   `TokenEstimator` uses a ~4-chars/token heuristic and ignores tool-call tokens and the
   system prompt in the per-turn delta (`responder.rb:58` counts only prompt + assistant
   content). The budget is therefore an estimate, not a hard provider-accurate ceiling.

7. **Operational: SQLite is single-writer.** Correct under `WEB_CONCURRENCY=2` via WAL +
   `BEGIN IMMEDIATE` + `busy_timeout`, but it does not scale horizontally across machines
   (shared file only). Acceptable for the demo scope (G6 asks for WEB_CONCURRENCY=2
   correctness, which is met), noted as a scaling ceiling.

8. **Demo secret handling in compose.** `SECRET_KEY_BASE` is auto-generated by the
   entrypoint if unset and `RAILS_FORCE_SSL=false` in the compose file (documented, plain
   HTTP for local use). Fine for a demo; a real deployment must set a stable secret and
   enable SSL. No secret is committed (G14 holds).

No other defects known at review time. This list is deliberately complete; an empty list
would have been a false claim.
