# Self-Review — Rails 8 Chatbot (v2_minimax_m3)

Honest, evidence-based review of the work in this workspace. All verdicts were
verified against the current source on disk; nothing here relies on memory.

Verification commands actually executed (results captured at time of writing):

```
$ bundle exec rake test
49 runs, 174 assertions, 0 failures, 0 errors, 0 skips
Coverage report generated for Minitest to .../coverage
Line Coverage: 5.12% (50 / 977)

$ bundle exec rubocop
47 files inspected, no offenses detected

$ bundle exec brakeman --quiet
== Overview ==
Controllers: 3, Models: 0, Templates: 14, Errors: 0, Security Warnings: 0

$ bundle exec bundle-audit check --update
No vulnerabilities found

$ bundle list | grep -E "(rails|ruby_llm|simplecov|brakeman|bundler-audit)"
  rails (8.1.3), ruby_llm (1.16.0), simplecov (0.22.0),
  brakeman (8.0.5), bundler-audit (0.9.3)

$ ruby --version
ruby 4.0.6 (2026-07-14 revision 03b6d3f889)
```

---

## 1. Goal Verification Table

| ID  | Goal (short)                          | Verdict | Evidence |
| --- | ------------------------------------- | ------- | -------- |
| G1  | Newest Ruby/Rails, no AR/Mailer/Job, root workspace | **PASS** | `Gemfile:3` pins `rails ~> 8.1.3`; `.ruby-version:1` is `ruby-4.0.6`; `config/application.rb:3-8` only requires `active_model/railtie`, `action_controller/railtie`, `action_view/railtie`, `action_cable/engine`, `rails/test_unit/railtie` (no `active_record/railtie`, no `action_mailer`, no `active_job/railtie`); app lives at the workspace root (no nested `app/`-within-`app/`). |
| G2  | Tailwind + Hotwire (Stimulus + Turbo Streams) + partials | **PASS** | `Gemfile:7-9` (`turbo-rails`, `stimulus-rails`, `tailwindcss-rails`); `app/javascript/controllers/chat_form_controller.js` (Stimulus reset); 11 partials under `app/views/chatbot/{messages,conversations,streaming}/`; views render Turbo Stream broadcasts via `turbo_stream_from "chatbot:conversation:#{@conversation.id}"` (`app/views/conversations/show.html.erb:1-2`) and the controller emits turbo-stream responses (`app/controllers/messages_controller.rb:58-65`). |
| G3  | ruby_llm via OpenRouter, Claude Sonnet default, env-overridable | **PASS** | `Gemfile:11` pins `ruby_llm ~> 1.11` (resolved to 1.16.0); `config/initializers/chatbot.rb:17-19` configures `openrouter_api_key` and `default_model`; `lib/chatbot/config.rb:3-4` default model `anthropic/claude-sonnet-4.5`; `lib/chatbot/config.rb:14-16` reads `CHATBOT_MODEL` env var with override. |
| G4  | TRUE token streaming via Turbo Stream broadcasts | **PASS** | `lib/chatbot/chat_service.rb:36-42` yields each `chunk` from `chat.ask` and the runner pushes it via `broadcaster.broadcast_chunk` (`lib/chatbot/runner.rb:29`); `lib/chatbot/broadcaster.rb:16-19` builds raw `<turbo-stream action="append" target="streaming-content-#{id}">` XML and pushes through `Turbo::StreamsChannel.broadcast_stream_to`; placeholder partial `app/views/chatbot/messages/_assistant_placeholder.html.erb:3-6` defines the `streaming-content-#{message_id}` target that the appends land in. Test asserts the streamed XML shape (`test/chatbot/broadcaster_test.rb:11-26`). **Caveat:** the chat-service test stub yields exactly one chunk (`test/chatbot/chat_service_test.rb:69`), so the real multi-token incremental path is exercised in production but the test only proves ≥1 chunk. |
| G5  | Multi-turn payload correctness, each user turn sent exactly once | **PASS** | `lib/chatbot/conversation.rb:32-37` `history_for_provider(exclude_message_id:)` strips the just-stored user message; `lib/chatbot/chat_service.rb:22` passes `user_message_id` so the replayed history excludes it; `chat.ask(@prompt)` at line 36 then appends the prompt exactly once. Three assertions cover this: `test/chatbot/store_test.rb:40-52` (excludes by id), `test/chatbot/chat_service_test.rb:101-121` (replay content) and `test/chatbot/chat_service_test.rb:123-165` which asserts the exact outgoing array for a three-turn conversation (`[u1, a1, u2, a2, u3, ok]` with each user prompt present exactly once). |
| G6  | Concurrency-safe, bounded persistence (TTL, message count, byte caps, cross-process) | **PASS** | `lib/chatbot/store.rb:12-14` sets WAL + busy_timeout; `with_tx` (lines 24-37) wraps each write in `BEGIN/COMMIT/ROLLBACK` under a per-instance `Mutex`; `evict_expired!` (lines 84-90) drops rows older than `Config.ttl_seconds`; `Conversation#enforce_caps!` (`lib/chatbot/conversation.rb:47-68`) trims oldest messages until both `max_messages` and `max_bytes` are respected, then inserts a `[trimmed: conversation exceeded caps]` system message; cross-process broadcasts are handled by `lib/action_cable/subscription_adapter/chatbot_sqlite.rb` (custom `chatbot_sqlite` adapter). Tests: `test/chatbot/store_test.rb:80-87` (over_budget), `test/chatbot/store_test.rb:89-98` (enforce_caps), `test/chatbot/store_test.rb:100-106` (evict_expired), `test/chatbot/action_cable_sqlite_adapter_test.rb:36-49` (cross-process broadcast via two adapter instances against one file). **Caveat:** SQLite WAL only, no cross-process row locking beyond SQLite's own; fine for the demo workload but see Known Defects #2, #3. |
| G7  | Two tools: server_time + calculator, called via RubyLLM::Tool API | **PASS** | `lib/chatbot/tools/server_time.rb` (returns `utc`, `iso_date`, `timezone`); `lib/chatbot/tools/calculator.rb` (shunting-yard interpreter; `SAFE_PATTERN = /\A[\s0-9+\-*\/().]+\z/` regex-gates inputs before tokenize; no `eval`); `lib/chatbot/history_builder.rb:14-15` registers both tools via `chat.with_tool(...)`. Tests cover name/schema, ISO format, basic arithmetic, malicious input rejection, division by zero (`test/chatbot/tools_test.rb:5-51`). |
| G8  | Structured-output title after first completed exchange | **PASS** | `lib/chatbot/title_generator.rb:7-11` defines `RubyLLM::Schema.create { string :title, description: "..." }`; `title_generator.rb:30-34` runs `chat.with_schema(...)` then `chat.ask(...)`; `title_generator.rb:26-28` early-returns when fewer than one user+assistant pair exists; failures are swallowed at line 52 (`rescue StandardError`). Tests: `test/chatbot/title_generator_test.rb:54-89` (sets title, skips when no exchange, skips when title already set). |
| G9  | Token budgeting per conversation | **PASS** | `lib/chatbot/config.rb:22-24` reads `CHATBOT_TOKEN_BUDGET` (default 100_000); `lib/chatbot/conversation.rb:39-45` defines `over_budget?` / `budget_remaining`; `app/controllers/messages_controller.rb:9-21` short-circuits to a `budget_exceeded` partial when over budget; `app/views/chatbot/messages/_budget_exceeded.html.erb` is the friendly in-UI message. Tests: `test/chatbot/store_test.rb:80-87` (over_budget), `test/chatbot/messages_controller_test.rb:37-48` (controller short-circuit). |
| G10 | Robustness: system prompt, missing-key preflight, error rescue, no failed-turn replay | **PASS** | System prompt: `lib/chatbot/history_builder.rb:12` `chat.with_instructions(Config.instructions)`. Missing-key preflight: `lib/chatbot/chat_service.rb:17` raises `MissingAPIKey`, `app/controllers/conversations_controller.rb:17-20` and `app/controllers/messages_controller.rb:23-35` both bail out with friendly UI when `Config.available?` is false, layout banner at `app/views/layouts/application.html.erb:19-24`. Error rescue: `lib/chatbot/chat_service.rb:43-45` catches `StandardError`, then `rollback_user_message!` at line 113-115 calls `Store#delete_last_user_message`; `lib/chatbot/runner.rb:44-53` catches any exception escaping the service and broadcasts an error partial while still rolling back. Tests: `test/chatbot/chat_service_test.rb:86-91` (MissingAPIKey), `test/chatbot/chat_service_test.rb:228-258` (provider failure rolls back the user message so it never enters history). |
| G11 | Minitest + SimpleCov, mocks mirror real RubyLLM, error paths covered | **PARTIAL** | 49 tests, 174 assertions all pass. Mocks do mirror the RubyLLM API surface (`CapturedChat` in `test/chatbot/chat_service_test.rb:8-73` implements `with_instructions`, `with_temperature`, `with_tool`, `with_tools`, `with_schema`, `with_model`, `add_message`, `ask` with a block, returns `RubyLLM::Message`). Error paths for `MissingAPIKey`, `BudgetExceeded`, provider 500, and tool-call flow are covered. **However**, SimpleCov reports a misleading **5.12% line coverage** because of a load-order bug: Rails boots and the initializer at `config/initializers/chatbot.rb:1-15` requires all `lib/chatbot/*` files **before** `test/test_helper.rb:6-8` calls `SimpleCov.start`. By the time SimpleCov starts tracking, the lib files are already loaded, so each line records zero hits; only the test files themselves are tracked. The per-file report is `lib/chatbot/store.rb 0/171`, `lib/chatbot/chat_service.rb 0/110`, etc., while controllers show `89.5%–100%`. The code is in fact heavily exercised — this is a tooling defect, not a coverage gap — but the report as written would be read as "almost no test coverage". I verified this by loading the env first then `SimpleCov.start`, which yielded ~26% in a single-file run; the broken state reproduces when `require "test_helper"` runs *after* Rails boots. |
| G12 | Brakeman + RuboCop + bundler-audit clean | **PASS** | `bundle exec rubocop` → 47 files, no offenses. `bundle exec brakeman --quiet` → "Errors: 0, Security Warnings: 0". `bundle exec bundle-audit check --update` → "No vulnerabilities found". |
| G13 | Production-grade Dockerfile + docker-compose + README | **PASS** | `Dockerfile`: `RUBY_VERSION=4.0.6` (line 9), `RAILS_ENV=production` (line 22), non-root `rails` user (lines 53-55), jemalloc preloaded (line 26), thruster fronting rails server (line 69). `docker-compose.yml`: WEB_CONCURRENCY=2 (line 11), named volume `chatbot-data` mounted at `/rails/tmp` so SQLite files survive restarts (line 21), healthcheck (lines 22-27). `README.md` documents setup, env vars, run, architecture notes, and a goal→file mapping table (lines 23-39). |
| G14 | No auth, no secrets committed, everything inside the workspace | **PASS** | No `has_secure_password`, no `before_action :authenticate`, no session store — grep returns nothing. `.env.example:4` is `OPENROUTER_API_KEY=replace-me` (placeholder only). `.gitignore` covers `.env*`, `/config/*.key`, `/tmp/*`, `/coverage`, `/.kamal/secrets`. `Dockerfile:6` and `README.md` examples use `sk-...` placeholders. No committed keys (`grep -rn "sk-or-v1-[a-zA-Z0-9]" .` returns no hits). |

---

## 2. Code Quality Assessment

Overall the code is small (~1100 LOC across the chatbot + views + adapter) and
mostly follows single-responsibility. Most files are well under 200 lines, names
are descriptive (`Chatbot::HistoryBuilder`, `Chatbot::Runner`), and the
view/controller/service layers are kept separate. There are no deep inheritance
chains, no module-level monkey-patches, and the rubocop-rails-omakase style is
followed without overrides.

What is wrong, in concrete terms:

1. **Duplicated constant.** `STREAM_NAME_PREFIX = "chatbot:conversation:"` is
   declared in both `lib/chatbot/runner.rb:7` and `lib/chatbot/broadcaster.rb:6`
   (one with `.freeze`, one without). Both classes use it to build the same
   channel name. This is a textbook DRY violation; one place to change later.

2. **Dead code (verified by grep — zero call sites).**
   - `lib/chatbot/store.rb:108-124` `Store#replace_last_assistant_message` is
     defined but never called from app, lib, or tests.
   - `lib/chatbot/broadcaster.rb:61-63` `conversation_id_from_stream` is
     defined but never called.
   - `lib/action_cable/subscription_adapter/chatbot_sqlite.rb:19`
     `@listeners = Concurrent::Map.new` is assigned in `initialize` but never
     read.
   - `app/views/chatbot/streaming/_chunk.html.erb` is a partial that references
     a Stimulus target `streaming_text` (`data: { streaming_text_target: "content" }`)
     for which **no controller exists** (`app/javascript/controllers/` has
     only `chat_form_controller.js`). The partial is also never rendered from
     the broadcaster (`lib/chatbot/broadcaster.rb` builds raw XML directly).
   - `app/javascript/controllers/chat_form_controller.js:5` declares
     `static targets = ["submit"]` but the controller body never reads
     `this.submitTarget`. The submit button does carry
     `data: { chat_form_target: "submit" }` (`app/views/conversations/show.html.erb:35`),
     so Stimulus wires the target — it is then ignored.

3. **ChatService is doing too much.** `lib/chatbot/chat_service.rb` (129 lines)
   mixes: API key check, budget check, history replay construction, the
   streaming ask, error rescue, post-processing of new messages, token
   accounting, and inline persistence of every message the provider produced
   (including tool-call and tool-result rows). The `new_messages.each` block
   at lines 64-98 is the heaviest method in the codebase; it would be easier
   to test if extracting a `MessagePersister` (or letting `Runner` own the
   persistence loop, the way title generation already does) were considered.

4. **Tight coupling between layers in the Runner.** `lib/chatbot/runner.rb`
   directly constructs `Broadcaster` and `ChatService` and calls
   `Registry.executor.post`. The exception handler at lines 44-53 builds a
   brand-new `Broadcaster` instance even though `broadcaster` was already
   available in scope, and silently swallows any error during the rollback
   (`rescue StandardError; nil`). This is an example of an instance being
   recreated when reuse would have been simpler and cheaper.

5. **Inconsistent and partially-ignored config.** `config/cable.yml:3,10` set
   `polling_interval: 0.1`, but the adapter only honors `ENV.fetch("CHATBOT_CABLE_POLL", 0.1)`
   (`lib/action_cable/subscription_adapter/chatbot_sqlite.rb:15`). The
   `polling_interval` key in cable.yml is ignored — either delete it or wire
   it through.

Top three things I would refactor with more time:

1. **Pull `SimpleCov.start` out of `test/test_helper.rb` and into a
   `.simplecov` file at the project root that is loaded via `require` *before*
   `require_relative "../config/environment"`.** This is the only meaningful
   test-infrastructure defect and it makes every other coverage reading in the
   project meaningless.
2. **Remove dead code listed above** (about 50 lines worth, plus the orphan
   partial and the unused Stimulus target). Once removed, regenerate
   RuboCop/Brakeman output and confirm still clean.
3. **Split `ChatService#run`** into a `stream_and_persist` (the streaming +
   per-message persistence loop) and a smaller `dispatch` method that handles
   the API-key, budget, and history-replay preflight. The current 96-line
   `run` method makes failure isolation hard.

---

## 3. Test Coverage Assessment

**Measured SimpleCov line coverage** (from `bundle exec rake test`):

- Overall: **5.12% (50 / 977)** — see G11 for why this number is misleading.
- Controllers: 92.45% (Controllers group in `coverage/index.html`).
- Services group (`lib/chatbot/*`): **0.0%** — false reading, not actual.
- Per-file in `coverage/.resultset.json`:
  - `app/controllers/application_controller.rb` 5/5 = 100%
  - `app/controllers/conversations_controller.rb` 17/19 = 89.5%
  - `app/controllers/messages_controller.rb` 27/29 = 93.1%
  - `lib/chatbot/*.rb` and `lib/action_cable/subscription_adapter/chatbot_sqlite.rb` 0% across the board (load-order bug).

A separate, correctly-loaded run of the same suite (`require "config/environment"`
before `SimpleCov.start`) measured ~26% over a single test file. So the
real coverage of the chatbot code is much higher than the official report
suggests, but the official report is broken.

**Weakest-tested area of the codebase:**

`lib/action_cable/subscription_adapter/chatbot_sqlite.rb`. Three passing tests
cover the happy paths (broadcast-and-poll, cross-instance visibility, channel
isolation) at `test/chatbot/action_cable_sqlite_adapter_test.rb:22-63`. None of
the failure modes below are tested.

**Failure modes NOT covered by any test:**

- **SQLite lock contention / busy_timeout exhaustion.** `Store#with_tx` holds
  a Mutex and the connection's `busy_timeout = 5_000`. No test simulates a
  second process holding the write lock while a reader tries to begin.
- **Unbounded growth of `cable_messages`.** The adapter inserts every
  broadcast and never deletes; `evict_expired!`-style cleanup does not exist
  for the cable store. No test asserts any cap or cleanup behavior.
- **Message drop under high rate.** `deliver_pending` has `LIMIT 200` per
  poll. If more than 200 messages accumulate between polls, only the most
  recent 200 are delivered and `last_seen` advances, so older messages are
  silently dropped. No test asserts this behavior or its absence.
- **Subscriber unsubscribe path.** `unsubscribe` (`chatbot_sqlite.rb:45-49`)
  deletes the timer task but does not delete the entry from `last_seen`; the
  per-callback `Concurrent::Map` grows monotonically. Not tested.
- **WebSocket disconnect mid-stream.** `Turbo::StreamsChannel.broadcast_stream_to`
  has no retry or buffering; if the underlying ActionCable server is in the
  middle of `broadcast_chunk` when the subscriber disconnects, the chunk is
  lost (the final `broadcast_done` still fires, so the UI ends up correct,
  but the in-flight chunks are gone). No test simulates a disconnect.
- **Puma worker shutdown during in-flight assistant turn.** `Registry.executor`
  is a `Concurrent::FixedThreadPool`; `Registry.shutdown!` is defined but
  never wired into Puma's `on_worker_shutdown`. No test asserts in-flight
  tasks complete during graceful shutdown.
- **TOCTOU between title-presence check and enqueue.** `Runner.enqueue_title_generation`
  reads `conversation.title.present?` (runner.rb:58) before `post`-ing; if
  two requests arrive concurrently before either title completes, two
  TitleGenerators race. Not tested.
- **`ChatService` failure modes beyond a single RubyLLM::Error.** No test for
  a network timeout, a malformed chunk, or a provider returning a finish
  reason that is not `stop`. The chat_service stub always yields exactly one
  assistant message; the loop in `new_messages.each` only ever sees the
  terminal assistant message in tests.
- **`Store#replace_last_assistant_message` and `Broadcaster#conversation_id_from_stream`**
  — both have zero test coverage because they are dead code (see Code Quality
  #2).
- **`Calculator` floating-point edge cases.** The current tests cover `1+1`,
  `10/4`, `((2+3)*4)-1`, division by zero, malicious input. They do not
  cover unary minus precedence, very large/small numbers that may lose
  precision, expressions like `1.5.5`, or `0/0` specifically.

---

## 4. Known Defects and Risks

Ordered roughly by user impact, highest first.

1. **SimpleCov coverage report is unreliable.** Test coverage cannot be
   trusted at face value from `bundle exec rake test`. See G11 and Code
   Quality #3.1. Any reviewer or CI gate that reads `coverage/index.html`
   and treats the percentage as ground truth will be misled.

2. **Unbounded growth of the ActionCable SQLite store.** Every broadcast
   (status, chunk, done, error, title-refresh) inserts a row in
   `tmp/chatbot_cable.sqlite3` (`lib/action_cable/subscription_adapter/chatbot_sqlite.rb:25-32`).
   There is no eviction, no TTL, no size cap. Over weeks of normal traffic
   this file will grow without bound; WAL files (`-wal`, `-shm`) will also
   grow. On a long-running container this is an operational risk:
   disk-pressure, slow backups, and slow `last_id_for` initial queries.

3. **`deliver_pending` has `LIMIT 200` and updates `last_seen` past dropped
   rows** (`lib/action_cable/subscription_adapter/chatbot_sqlite.rb:67-77`).
   If a long-running chat emits more than 200 chunks between two poll ticks
   of a subscriber, older chunks are silently dropped. The final
   `broadcast_done` still happens so the UI is consistent, but the in-flight
   text is gone.

4. **`Registry.executor` is never gracefully shut down.** The thread pool is
   created at boot (`lib/chatbot/registry.rb:6-10`) and `Registry.shutdown!`
   is defined (line 39) but never called from `puma.rb`, an initializer, or a
   SIGTERM handler. On a graceful Puma restart, in-flight assistant turns
   and title generation can be killed mid-stream. The error path in
   `runner.rb:44-53` will fire and broadcast an error partial, so the user
   sees a degraded state, but it is still a quiet reliability hole.

5. **Title generation race.** `lib/chatbot/runner.rb:55-65`: title-presence
   is checked, then the work is posted to the executor. Two concurrent
   completed turns from the same conversation before either title completes
   will enqueue two `TitleGenerator` runs. Each one independently calls
   `chat.ask(...)` against the provider. Cost is small but real, and the
   second result will silently overwrite the first because `set_title` is a
   plain write.

6. **Dead code is shipped.** See Code Quality #2. Not a runtime defect, but
   `Store#replace_last_assistant_message` and the orphan `_chunk.html.erb`
   partial both imply behavior that does not exist; future maintainers will
   waste time wondering why the in-place replacement "doesn't work".

7. **Calculator division-by-zero detection happens after the fact.**
   `lib/chatbot/tools/calculator.rb:28-29` runs `eval_rpn` first, which
   already raises `ZeroDivisionError` when it encounters `a/b` with `b == 0`
   (line 126), then the rescue at line 32 catches it. But the explicit
   `result == Float::INFINITY` check (line 29) handles only the "stack too
   shallow → infinity" path (line 109). An expression like `1/(1-1)` raises
   before reaching line 29. Functionally correct but the two defensive
   layers mask each other.

8. **`config.action_cable.allowed_request_origins = []`** in
   `config/application.rb:22`. This relies on Rails' `allow_same_origin_as_host`
   default (true) to permit same-origin WebSocket connections. Any deployment
   where the ActionCable endpoint is on a different origin (e.g., behind a
   dedicated WS subdomain or CDN) will silently fail to upgrade. There is no
   test that asserts the WS handshake works, so this would only be caught
   by a human clicking around in production.

9. **ChatService relies on `chat.messages` being a clean slice.**
   `lib/chatbot/chat_service.rb:55` does `chat.messages[messages_before_ask..]`
   and assumes the messages added since `messages_before_ask` are exactly
   the ones produced by this turn. If a future RubyLLM version mutates the
   underlying array or returns messages with timestamps that re-order the
   slice, this assumption breaks silently. The defensive `.reject { |m|
   m.role == :user }` on line 56 already signals the author was nervous
   about this — the production code and the stub both happen to behave the
   same way today, but the contract is implicit.

10. **`Turbo::StreamsChannel.broadcast_stream_to` is fire-and-forget.**
    `lib/chatbot/broadcaster.rb:18,24,36,47` calls return immediately; there
    is no retry, no buffering, no error handling. If the underlying
    ActionCable server raises (e.g., the SQLite cable adapter is wedged on
    the busy_timeout), the chunk is dropped without any UI signal. The user
    sees the placeholder stay at "thinking…" until the final `broadcast_done`
    fires (or never, if the run itself fails).

11. **Stream name prefix duplicated.** `lib/chatbot/runner.rb:7` and
    `lib/chatbot/broadcaster.rb:6` both define `STREAM_NAME_PREFIX = "chatbot:conversation:"`.
    If one is renamed and the other is not, broadcasts and subscribers
    silently disconnect. Constant duplication is a small but real source of
    future bugs.

12. **Sensitive `error.message` echoed to the UI.** `lib/chatbot/runner.rb:42`
    broadcasts `result.error.message` verbatim, and `:52` does the same for
    caught exceptions, including the exception class name. Provider errors
    frequently include model IDs, internal IDs, or stack-trace-like
    strings. In production this may leak operational detail to end users
    via the `_assistant_error.html.erb` partial.

13. **`@db` shared across threads inside `Store`** with serialization only
    via the per-instance `@mutex`. This is correct in theory but means that
    even pure reads contend with concurrent writes. With WAL mode, multiple
    readers could safely coexist with one writer — but the code holds the
    global mutex for all reads inside `with_tx`. Reads of `messages`,
    `find_conversation`, etc. (`lib/chatbot/conversation.rb:25-29`) do not
    take the mutex, so this is fine for now, but it is a load-bearing
    invariant that is not documented.

14. **ActionCable subscriber's `last_seen` is in-memory only.**
    `lib/action_cable/subscription_adapter/chatbot_sqlite.rb:99-113`. On a
    Puma worker restart, `last_id_for` re-queries `MAX(id)` (line 106),
    so a fresh subscriber correctly starts at the newest message rather
    than replaying history. That is the right behavior, but it means any
    client that was connected during the restart misses every broadcast
    during the gap. Combined with defect #4 (no graceful shutdown), the
    end-user impact is "the chat freezes during a deploy for 5–30 seconds
    and then resumes".

15. **Chat history is not encrypted at rest.** `tmp/chatbot.sqlite3` and
    `tmp/chatbot_cable.sqlite3` are plain SQLite. The brief explicitly says
    "no auth" so this is acceptable for the demo, but if anyone re-purposes
    this code, every conversation a user has had with the model is on disk
    in plaintext. Worth a comment in `Store` for future maintainers.

No defect is severe enough to make the demo unusable in development; the
combination of (1) + (4) + (10) is what would hurt a real production
deployment the most. (1) and (4) are surgical fixes; (2) and (10) need
design work.
