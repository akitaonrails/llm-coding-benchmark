# SELF_REVIEW.md — phase 3 self-review

Written 2026-08-15 by re-verifying every goal against the code as it exists NOW
(not from memory). All commands were run from the workspace root in this phase.

## Fix made during this review

One surgical fix was applied while reviewing (allowed by the phase-3 brief):

- `Chat::Calculator` modulo-by-zero crashed with an uncaught `ZeroDivisionError`
  (`app/lib/chat/calculator.rb:145`, the `left % right` arm — division was
  guarded but modulo was not). Reproduced live:
  `bin/rails runner 'puts Chat::Calculator.evaluate("7 % 0")'` → backtrace
  `calculator.rb:145: divided by 0 (ZeroDivisionError)`. Because the exception
  escapes neither `Calculator#evaluate`'s `InvalidExpression` rescue nor
  `Service#execute_exchange`'s `RubyLLM::Error/Faraday::Error/JSON::ParserError`
  rescue, a model-emitted `7 % 0` tool call would 500 the turn mid-stream.
  Fixed by adding a `modulo` guard (calculator.rb:150-153) mirroring `divide`,
  plus a regression assertion in `test/lib/chat/calculator_test.rb:52`.
  Suite re-run after the fix: 73 runs, 219 assertions, 0 failures; RuboCop and
  Brakeman still clean.

## 1. Goal verification table

| Goal | Verdict | Evidence |
| --- | --- | --- |
| G1 — Rails, newest Ruby via mise, no AR/AM/AJ, generated, workspace root | PASS | `ruby -v` → ruby 4.0.6 (pinned `mise.toml`); `rails ~> 8.1.3, >= 8.1.3.1` (Gemfile.lock). AR/AM/AJ railties commented out in `config/application.rb:5-10`; no `config/database.yml` exists; standard generator skeleton (bin/ binstubs, `.github/workflows/ci.yml`); app sits at workspace root. Boots: the test run and `bin/rails runner` both booted the app successfully this phase. |
| G2 — ChatGPT-like SPA, Tailwind, Hotwire, componentized partials | PASS | Tailwind v4 via `tailwindcss-rails` (`app/assets/tailwind/application.css`, compiled `app/assets/builds/tailwind.css`, 19 KB); Turbo + Stimulus pinned in `config/importmap.rb`; 4 small Stimulus controllers (`app/javascript/controllers/{composer,kick,scroll,sidebar}_controller.js`); 7 partials under `app/views/{messages,conversations,shared}/`; single `turbo_frame_tag "chat_main"` hosts the SPA (`_chat_main.html.erb`). No `fetch(` anywhere in `app/javascript`. |
| G3 — RubyLLM latest, OpenRouter, latest Claude Sonnet, env-overridable | PASS | `ruby_llm` 1.16.0 (Gemfile.lock); `config/initializers/ruby_llm.rb:5` sets `openrouter_api_key` from ENV only; `app/lib/chat/service.rb:24` `RubyLLM.chat(model: config.model, provider: :openrouter)`; default `anthropic/claude-sonnet-4.6`, `CHAT_MODEL` override (`app/lib/chat/app_config.rb:6,13-15`). Wire test asserts `"anthropic/claude-sonnet-4.6"` on the actual outgoing body (`service_wire_test.rb:34`). |
| G4 — TRUE token streaming via Turbo Stream broadcasts | PASS | `service.rb:104-106` streams inside the `chat.ask` block; each chunk → `Broadcaster.broadcast_token_delta` (`broadcaster.rb:40-46`, one `broadcast_append_to` per delta into `message_<id>_deltas`); page subscribes via `turbo_stream_from` (`_chat_main.html.erb`). Tests: `service_wire_test.rb:59` "token deltas broadcast per SSE chunk and final reply persists" (3 SSE chunks → 3 delta broadcasts). Runtime evidence from phase 2 in `log/development.log:767`: `Turbo::StreamsChannel transmitting "...<span class=\"token-delta\">42</span>..."` — a real provider token pushed mid-stream, not a post-completion dump. |
| G5 — multi-turn payload: each user turn sent exactly once; exact-array test | PASS | `Chat::History.messages_for` filters `pending` and notices (`history.rb:13-17`); prompt passed once via `chat.ask` (`service.rb:104`). Tests: `history_test.rb:16` "exact outgoing message array for a multi-turn conversation (G5)" (unit), `service_test.rb` "G5: replayed history excludes the prompt, which is sent exactly once", and `service_wire_test.rb:25` asserts the exact 4-message wire payload against the real ruby_llm/Faraday stack with WebMock. |
| G6 — restart-surviving, WEB_CONCURRENCY-safe, bounded, TTL'd persistence | PASS | File store with per-conversation `flock` + atomic tmp-rename writes (`store.rb:145-159,183-189`); message/byte caps (`store.rb:161-168`); TTL purge (`store.rb:129-137`). Tests: `store_test.rb:7` restart roundtrip, `store_test.rb:113` "concurrent multi-process appends never lose a message" (real `fork`), `store_test.rb:37/47/57` caps and TTL. `compose.yaml` runs `WEB_CONCURRENCY: "2"` with the Redis cable adapter (`config/cable.yml`). |
| G7 — exactly two tools via RubyLLM tool API; safe calculator; runtime tool use | PASS | `Chat::Tools::ServerTime` / `Chat::Tools::Calculator` are `RubyLLM::Tool` subclasses (`app/lib/chat/tools/`, explicit `#name` overrides); wired in `service.rb:27,125`. Wire test asserts both offered on every request (`service_wire_test.rb:49`) and a full tool round-trip with the `tool` role replayed (`service_wire_test.rb:75`); `calculator_test.rb:38` "dangerous input never evaluates" (no `eval` — hand-written parser). Runtime: `storage/conversations/9cc1d94d….json` records a real exchange with `"tools":["calculator"]` answering "Now add 100 to that number" → "**142**". |
| G8 — structured-output title after first exchange, displayed in UI | PASS | `title_service.rb:48` uses `chat.with_schema(name: "conversation_title", schema: TITLE_SCHEMA)`; called exactly after exchange 1 (`service.rb:133-137`); rendered in sidebar item + header (`_conversation_item.html.erb`, `_chat_main.html.erb`) and live-updated via `broadcast_title` (`broadcaster.rb:64-72`). Tests: `title_service_test.rb:16/36/45/54`. Runtime: the stored conversation above has title `"Remember the Number 42"`. |
| G9 — token budget: per-conversation tracking, env-configurable, refuse without provider call | PASS | `CHAT_TOKEN_BUDGET` env, default 100_000 (`app_config.rb:7,21-23`); per-exchange usage accumulated from provider usage chunks (`store.rb:77`, wire test asserts 17 tokens recorded); refusal path `service.rb:76-81` rolls back and never calls the provider — test `service_test.rb` "budget exceeded: provider never called, friendly notice, turn rolled back" asserts `assert_empty @fake.ask_prompts`. Budget badge rendered in the header (`_chat_main.html.erb`). |
| G10 — instructions API, missing-key preflight, rescued failures, failed turns never replayed | PASS | `chat.with_instructions(config.system_prompt)` (`service.rb:123`); `Chat::Preflight` banner in UI (`chat_controller_test.rb:16` "root shows the actionable banner when the API key is missing") and service refusal (`service_test.rb` "missing API key: friendly refusal"); provider errors rescued (`service.rb:87-92`) into a persisted `notice` with rollback — `service_test.rb` "provider failure: turn rolled back, degraded notice persisted, never replayed" (asserts next turn replays nothing broken) and `service_wire_test.rb:94` real 500 → notice. |
| G11 — Minitest per component, mocks mirror real API, SimpleCov | PASS | `bin/rails test` (this phase): **73 runs, 219 assertions, 0 failures, 0 skips**. `FakeChat` in `service_test.rb` mirrors the real ruby_llm 1.16 surface and is cross-checked by wire tests running the actual gem stack (WebMock at the HTTP boundary). SimpleCov wired in `test/test_helper.rb:4-7` with branch coverage. Error paths covered (500, missing key, budget, busy, rollback). |
| G12 — Brakeman, RuboCop, bundle-audit clean | PASS | Run this phase: `bundle exec rubocop` → "51 files inspected, no offenses detected"; `bundle exec brakeman` → "Errors: 0, Security Warnings: 0"; `bundle exec bundle-audit check` → "No vulnerabilities found". All three also wired into `.github/workflows/ci.yml`. |
| G13 — production Dockerfile (non-root, entrypoint) + compose + README | PASS | `Dockerfile`: multi-stage, `RAILS_ENV=production`, non-root user 1000 (`groupadd/useradd rails`, `USER 1000:1000`), `ENTRYPOINT ["/rails/bin/docker-entrypoint"]`, Thruster CMD. `compose.yaml`: app + redis healthchecks, named volume for `storage/conversations`, `WEB_CONCURRENCY=2`. README documents setup/local/docker. Phase 2 actually ran `docker compose up --build -d`, exec'd into it to count Puma workers, `docker compose restart` + curl `GET / → 200` (commands recorded in `phase2.ndjson`). Caveat: I did NOT rebuild the image in phase 3; the only source change since that validation is the calculator guard above (pure-Ruby, no dependency/build-graph change). |
| G14 — no auth, no committed secrets, single workspace | PASS | No authentication anywhere (`config/routes.rb` has no auth constraints; controllers have no auth filters). Secrets scan this phase (`sk-or-`, `sk-ant-`, `API_KEY=` across rb/yml/erb/js/md/Dockerfile/toml) found only obviously-fake test literals (`"sk-or-test"`, `"sk-or-something"` in tests); the real key flows only `ENV` → initializer / compose `${OPENROUTER_API_KEY:?}`; `.gitignore` and `.dockerignore` exclude `.env*` and key files. All work is inside this workspace. |

Honest scope note: runtime claims (G4 log excerpt, G7/G8 stored conversation,
G13 compose commands) rest on phase-2 artifacts that still exist on disk
(`log/development.log`, `storage/conversations/`, `phase2.ndjson`); everything
else was re-executed from scratch in this phase.

## 2. Code quality assessment

Overall this is a clean, small codebase (~1,030 lines of Ruby across
`app/lib/chat`, controllers included), and it reads well. Frank specifics:

**Good**

- Naming is intention-revealing: `stage_message` / `run_pending` /
  `send_message` describe the three flows precisely; `claim_run`/`release_run`
  make the concurrency protocol explicit.
- Single responsibility is genuinely held: `Store` (persistence + locking),
  `Conversation` (read-only snapshot), `History` (provider replay), `Service`
  (orchestration), `TitleService`, `Broadcaster` (Action Cable), `Preflight`,
  `Tools` are all one job each. Controllers are thin (8–20 lines/action).
- Dependency injection everywhere (`chat_factory`, `broadcaster`,
  `title_service`, `clock`) is what makes the 98% line coverage cheap.
- Coupling to Rails is low in the domain layer — `Service` touches
  `Rails.logger` and Action Cable only via `Broadcaster`.

**Problems**

- **String-keyed message hashes cross every layer.** `"role"` / `"content"` /
  `"pending"` string-key knowledge is duplicated across `store.rb`,
  `conversation.rb`, `history.rb`, `service.rb`, `broadcaster.rb`,
  `_message.html.erb`, and tests. A `Message` value object would remove ~8
  copies of that implicit schema.
- **Dead code / duplication:**
  - `Conversation#within_budget?` (`conversation.rb:51-53`) is never called —
    `Service#over_budget?` implements the check independently. Two budget
    definitions that can drift.
  - `ChatController` re-declares `before_action :load_conversations`
    (`chat_controller.rb:4`) which `ApplicationController` already registers
    globally (`application_controller.rb:14`).
  - `Broadcaster.stream_for`'s else-arm (plain-id argument, `broadcaster.rb:17`)
    has no production caller — every caller passes a conversation; its branch
    is also the one uncovered in coverage.
  - Comment/code mismatch: `Store#clear_pending` says "Marks the oldest
    pending user message" but `reverse_each.find` selects the *newest*
    (`store.rb:98-103`). Behavior is right for the single-pending design; the
    comment is wrong.
- **Every request pays an O(N) store scan:** `ApplicationController` runs
  `load_conversations` → `Chat.store.list` → `purge_expired` + glob + full
  JSON parse of every conversation file, on every action, including each
  per-turn POST. Fine at demo scale; a real perf cliff as conversations grow.
- View layer is disciplined (largest template `_chat_main.html.erb`, ~60
  lines); JS controllers are small with no dead code; CSS is one small
  component file, not a dump.

**Top 3 refactors with more time**

1. **Introduce a `Chat::Message` value object** replacing raw string-keyed
   hashes end-to-end (store → service → broadcaster → partials). Highest
   leverage: deletes the implicit-schema duplication, makes `pending`/role
   invariants enforceable in one place, simplifies tests.
2. **Index or cache the conversation list** (`Store#list`/`purge_expired`):
   an on-disk index (or at least mtime-sorted glob with lazy read) so the
   per-request sidebar load stops parsing every file. Also decouple TTL from
   `File.mtime` (copying the storage dir currently mass-expires everything).
3. **Harden the calculator's numeric envelope**: cap integer exponentiation
   (see risks below) and unify `divide`/`modulo` guards under one
   arithmetic-error policy; consider a float-fallback above an exponent
   threshold.

## 3. Test coverage assessment

Actual numbers, from `bin/rails test` run this phase (after the review fix):

```
73 runs, 219 assertions, 0 failures, 0 errors, 0 skips
Line coverage:   521 / 531 (98.11%)
Branch coverage: 89 / 108 (82.40%)
```

Weakest-tested area: `app/lib/chat/broadcaster.rb` (82.6% line, 75% branch —
`stream_for`'s dead else-arm; `broadcast_title`'s replace-header path is
covered only via `title_service_test`) and `title_service.rb` (60% branch —
several rescue arms and the string-content re-parse arm
`title_service.rb:52-53` uncovered). `service.rb:83`'s claim-race branch
(`claim_run` returning false when the earlier `running?` check passed) is
never exercised — the tested "busy" path refuses at `running?` first.

Failure modes NOT covered by any test:

- **The claim race itself** — two processes passing `running?` and then
  contending on `claim_run` (only the benign pre-check path is tested).
- **Corrupt store file** — `Store#read` rescues `JSON::ParserError` to nil
  (`store.rb:179-180`), which silently turns a torn/corrupt conversation into
  a 404; no test pins that behavior.
- **No-JS / non-Turbo submission** — `MessagesController#create` responds only
  to `turbo_stream` (`messages_controller.rb:10-16`, uncovered branch); a plain
  HTML POST gets `ActionController::UnknownFormat` (406). Unverified by test
  and arguably a broken edge.
- **Stale-run crash recovery end-to-end** — the kick-form re-render after a
  crash mid-exchange is implemented (`_chat_main.html.erb` renders the form
  when `pending_message` exists) but no test simulates a crash-then-reopen.
- **Browser-level behavior** — there are no system tests
  (`config.generators.system_tests = nil`); nothing asserts token spans
  actually arrive in the DOM or that Action Cable reconnects. The Action Cable
  surface is tested only at the broadcast-API level.
- **Title retry** — if title generation fails on exchange 1, it is never
  retried (`maybe_generate_title` fires only when `exchanges == 1`,
  `service.rb:134`); no test covers that outcome (conversation stays
  "New chat").

## 4. Known defects and risks

1. **FIXED this phase — modulo-by-zero crash**: see the fix note at the top.
   Was: uncaught `ZeroDivisionError` from `calculator.rb:145` on `x % 0`,
   500-ing the request mid-turn (user message left pending; recoverable via
   the kick form on reload, but the turn crashed).
2. **Unbounded integer exponentiation in the calculator (open).**
   `Chat::Calculator.evaluate("9**9**9")` builds `9**(9**9)` — a bignum with
   ~3.7×10⁸ digits — inside the request thread: unbounded CPU/memory, an
   effective self-DoS if a user prompts the model into it. No exponent cap
   exists. Not fixed (would need a policy decision on limits).
3. **O(N) per-request store scan** (see quality §): every action stats+glob+
   parses all conversation files; TTL is `File.mtime`-based, so copying the
   storage directory mass-expires history.
4. **406 for non-Turbo POSTs**: `messages#create` / `runs#create` /
   `conversations#create` render only `format.turbo_stream` — no-JS clients
   (or future API callers) get `ActionController::UnknownFormat`.
5. **Per-chunk broadcast flood**: one Action Cable publish per SSE delta with
   no coalescing; long fast replies emit hundreds of Redis pubsub messages and
   DOM appends per turn. Bounded only implicitly by model output length.
6. **Stale-claim window misconfiguration**: the 300 s stale-run guard
   (`store.rb:110`, `conversation.rb:38`) must exceed worst-case provider
   time (`CHAT_REQUEST_TIMEOUT` × retries). Defaults (120 s × 1 retry) fit,
   but `CHAT_REQUEST_TIMEOUT=400` would let a second turn double-claim while
   the first is still streaming.
7. **Title generation is single-shot** (see §3): a transient failure on the
   first exchange permanently leaves the conversation untitled.
8. **Redis outage mid-turn degrades silently**: broadcasts are synchronous
   publishes; if Redis drops during an exchange the provider call still
   completes and persists — the live page just shows nothing until reload.
   Data stays consistent; UX doesn't.
9. **No pagination or sidebar cap**: all conversations render in the sidebar;
   with the file scan this compounds risk 3.
10. **Store files are 0644** (`File.binwrite` default): chat transcripts are
    world-readable to local users on shared hosts. Minor for a demo; note for
    anything real.
11. **No-auth by design (G14)**: anyone who can reach the port can spend
    OpenRouter credits — documented in README "Security / demo caveats".
    Budget/`max_input_chars` (20 KB) bound abuse per conversation only.

No other known or suspected defects; the concurrency-critical paths (locked
read-modify-write, atomic rename, cross-process claim, pending-message
filtering) each have a dedicated test, and I re-ran the full suite plus all
three audits after the single fix made in this review.
