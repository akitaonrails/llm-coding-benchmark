# Self review (phase 3)

Date: 2026-09-02. Everything below was re-verified against the working tree as
it stands now, not from memory. Commands were run from the workspace root with
`OPENROUTER_API_KEY` unset (the test suite never contacts the network).

## Fixes made during this review

Two things were found broken while re-reading the code. Both are small,
covered by new tests, and recorded here as required.

1. **Title generation ran inside the per-conversation turn lock.** After the
   reply had finished streaming, `TurnRunner` still held the lock while it made
   the (non-streamed) title request, so sending the next prompt within that
   1–3 s window was refused with "A reply is still being generated". Moved
   `ensure_title` outside `with_turn_lock` (`app/services/turn_runner.rb:26-40`);
   this is safe because `ConversationStore#update` is an atomic WATCH/MULTI
   read-modify-write. Regression test
   `test/services/turn_runner_test.rb:69` ("releases the turn lock before
   generating the title") fails against the old code (`Expected: false`) and
   passes now.
2. **`calculator` bounded the exponent but not the result size.**
   `(9^1000)^1000` produced a 954,243-digit integer in 0.05 s (which would then
   be JSON-serialised into the tool result sent to OpenRouter), and
   `((9^1000)^1000)^100` did not finish within a 90 s timeout — a CPU/memory
   exhaustion path reachable by asking the assistant to "calculate …". Added
   `MAX_RESULT_BITS = 8_192` (`app/lib/arithmetic_evaluator.rb:13,107`);
   the pathological expression now raises `ArithmeticEvaluator::Error: result
   too large` instantly. Test: `test/lib/arithmetic_evaluator_test.rb:46`.

Also carried over, uncommitted, from phase 2: `Gemfile` pins `redis < 6`
(Action Cable 8.1's Redis adapter cannot activate redis 6.x, which broke every
WebSocket connection) plus the regression test
`test/integration/cable_redis_adapter_test.rb`.

## 1. Goal verification table

| Goal | Verdict | Evidence |
| --- | --- | --- |
| G1 Newest Ruby/Rails, no AR/AM/AJ, generated at root | PASS | `mise ls-remote ruby` newest = 4.0.6 = `.ruby-version`/`mise.toml`; `gem list rails --remote` newest = 8.1.3.1 = `Gemfile.lock`. `config/application.rb:5-14` requires only active_model, action_controller, action_view, action_cable, test_unit (AR/AJ/AM commented out); no `config/database.yml`; no db gems in `Gemfile`. Standard `rails new` layout at workspace root (`bin/`, `config/initializers/*`, `app/views/pwa`, `public/icon.svg`, `.github/workflows/ci.yml`, `config/ci.rb`). Note: the repo has a single commit, so the generator run itself is not visible in git history — the evidence is the untouched generator boilerplate. |
| G2 Tailwind + Hotwire SPA, partials, no hand-rolled fetch/innerHTML | PASS | `tailwindcss-rails 4.6.0`, `app/assets/tailwind/application.css`; `turbo_stream_from` at `app/views/conversations/show.html.erb:2`; server-rendered `app/views/messages/create.turbo_stream.erb` and `notice.turbo_stream.erb`; 3 Stimulus controllers (`composer`, `scroll`, `flash`); 17 partials under `app/views`. `grep -rn "fetch(\|innerHTML" app/javascript` → 0 hits. |
| G3 RubyLLM latest, OpenRouter, latest Claude Sonnet, env-overridable | PASS | `gem list ruby_llm --remote` = 1.16.0 = locked version. Provider `:openrouter` at `app/services/chat_completion.rb:18,32`; `config/initializers/ruby_llm.rb:8` sets `openrouter_api_key` from ENV. Default model `anthropic/claude-sonnet-5` (`app/models/chat_settings.rb:5`), overridable via `CHAT_MODEL` (`chat_settings.rb:25`; test `chat_completion_test.rb:61`). |
| G4 True token streaming via Turbo Stream broadcasts | PASS | Each SSE delta → `on_chunk` (`chat_completion.rb:55-57`) → `Turbo::StreamsChannel.broadcast_append_to` on the pending bubble's `_body` span (`app/services/conversation_broadcaster.rb:19-21,55-57`); completion is a separate `replace`. Test `turn_runner_test.rb:25-52` asserts two `append` frames ("Hel", "lo!") *before* the `replace`. Live measurement was done in phase 2 over the real `/cable` WebSocket (12 `append` frames from t=1.23 s to 7.19 s, then `replace` at 7.24 s; 39 frames ~50 ms apart with sonnet-4.5). Not re-measured live in this phase. |
| G5 Each user turn sent exactly once; unit test of exact payload | PASS | History replayed with `chat.add_message` and only the new prompt goes through `ask` (`chat_completion.rb:35,55`). Exact outgoing `messages` array asserted in `test/services/chat_completion_test.rb:8-29` (4-turn history + new prompt) and `:31-48` (payload growth across two turns); also `turn_runner_test.rb:188-203` and `chat_flow_test.rb:44-46`. |
| G6 Restart-safe, multi-process, bounded (count+bytes), TTL | PASS | Redis JSON documents with `SET … EX ttl` (`app/stores/conversation_store/redis_adapter.rb:20-37`), optimistic WATCH/MULTI updates, per-conversation lock; `config/puma.rb:36-39` drops inherited Redis client/thread pool on worker boot; nothing conversation-related is process-local. Caps: `Conversation#prune!` (`app/models/conversation.rb:84-88`) on `max_messages` (40) and `max_bytes` (64 KiB), TTL 7 days (`chat_settings.rb:7-9`). Tests: `conversation_test.rb:27-53`, `conversation_store_test.rb:42,61`, `redis_adapter_test.rb` (runs against real Redis: 8 threads × 10 conflicting updates lose nothing). Phase 2 verified live with `WEB_CONCURRENCY=2` (10 WebSocket subscribers split across two worker PIDs all received identical frames; Redis document byte-identical across a server restart). Caveats in §4: a single message larger than `max_bytes` is kept, byte pruning can leave an orphan assistant turn at the head, and restart survival depends on Redis persistence (compose enables AOF; a local dev Redis may not). |
| G7 Exactly two tools via RubyLLM tool API | PASS | `ChatCompletion::TOOLS = [ServerTimeTool, CalculatorTool]` (`chat_completion.rb:17`), both `RubyLLM::Tool` subclasses; RubyLLM derives names `server_time`/`calculator` (`server_time_tool_test.rb:4`, `calculator_tool_test.rb:4`); outgoing payload has exactly those two function tools (`chat_completion_test.rb:57`). Tool round trips exercised through the real provider code with stubbed SSE (`chat_completion_test.rb:90-128`). Calculator uses a recursive-descent parser, no `eval`. Phase 2 confirmed live that "What time is it on the server?" and an arithmetic prompt were answered via the tools (tool names persisted on the message). |
| G8 Structured-output title after first exchange, shown in UI | PASS | `TitleGenerator#call` uses `chat.with_schema(ConversationTitleSchema)` (`app/services/title_generator.rb:17`, schema at `app/schemas/conversation_title_schema.rb`); invoked from `TurnRunner#ensure_title` once `exchanges_count >= 1` and untitled (`turn_runner.rb:78-90`); broadcast into `#conversation_title` and the sidebar item. `title_generator_test.rb:6-20` asserts the request carries `response_format.type == "json_schema"` with `required: ["title"]`; `chat_flow_test.rb:29-36` asserts the title appears in `h1#conversation_title` and the sidebar after reload. |
| G9 Token budget, env-configurable, friendly refusal | PASS | `CHAT_TOKEN_BUDGET` default 20 000 (`chat_settings.rb:6,26`); usage accumulated from provider `usage` (fallback estimator when absent, `chat_completion.rb:64-72`); `MessagesController#create` refuses with a warning notice before enqueuing (`messages_controller.rb:14`) and `TurnRunner` re-checks under the lock (`turn_runner.rb:29`); usage shown in `_usage.html.erb`. Tests: `messages_controller_test.rb:80-89`, `turn_runner_test.rb:158-167` (`assert_not_requested`). |
| G10 Instructions API, missing-key preflight, provider failures rescued, failed turns never stored | PASS | `chat.with_instructions(SYSTEM_PROMPT)` (`chat_completion.rb:33`; test `chat_completion_test.rb:140`). Preflight in `messages_controller.rb:13` and `turn_runner.rb:28` with an actionable message naming `OPENROUTER_API_KEY`. `TurnRunner#call` rescues `StandardError` into a `data-state="failed"` bubble (`turn_runner.rb:41-43,98-102`). Persistence happens only after `generate_reply` returns (`turn_runner.rb:31-32`), so failed turns are never written; tests `turn_runner_test.rb:108-146` (429, connection failure, timeout, failure after a tool call) and `chat_flow_test.rb:50-58`. |
| G11 Minitest for every component, realistic mocks, error paths, SimpleCov | PASS | 137 runs / 556 assertions / 0 failures (with `TEST_REDIS_URL`), one test file per class in `app/` (see `test/` tree). No RubyLLM method is mocked at all: OpenRouter is stubbed at the HTTP layer with WebMock in OpenAI-compatible SSE/JSON wire format (`test/support/openrouter_stubs.rb`), so RubyLLM's real payload rendering, SSE parsing, tool-call accumulation and usage extraction run in every test. I also verified every RubyLLM method the app calls exists in the installed gem (`with_instructions`, `with_tools`, `with_schema`, `add_message`, `after_message`, `before_tool_call`, `assume_model_exists:`, `Tool#name` derivation). SimpleCov with branch coverage (`test/coverage.rb`), report at `coverage/index.html`. Gap: no browser/system tests for the Stimulus controllers. |
| G12 Brakeman, RuboCop, bundle-audit clean | PASS | Run today after the fixes: `bin/rubocop` → "64 files inspected, no offenses detected"; `bin/brakeman --quiet --no-pager --exit-on-warn --exit-on-error` → exit 0, "Security Warnings: 0"; `bin/bundler-audit check --update` → "No vulnerabilities found" (advisory DB 2026-08-31); `bin/importmap audit` → "No vulnerable packages found". |
| G13 Production Dockerfile, compose, README | PASS | `docker build -t selfreview-chat .` today → exit 0; `docker image inspect` → `User=1000:1000`, `Entrypoint=[/rails/bin/docker-entrypoint]`, `Cmd=[./bin/rails server]`, `RAILS_ENV=production` (`Dockerfile:25`), 0 `OPENROUTER` entries in image env. `docker compose config --quiet` → valid. `docker compose up --build` with a real end-to-end chat (both tools used, restart survival) was verified in phase 2, not re-run in this phase. `README.md` documents purpose, setup, configuration table, local/compose runs, tests. |
| G14 No auth, no secrets, everything in workspace | PASS | No auth code anywhere. Scans for key patterns (`sk-or-v1`, `sk-ant-`, `OPENROUTER_API_KEY=<value>`) over all tracked+untracked files, `git log -p`, `log/*.log` and `tmp/validation/*` → 0 hits; `.env*` git-ignored (`.gitignore:5-6`), no `config/master.key`/credentials; compose forwards the key from the host shell only (`compose.yaml:25`). RubyLLM's Faraday logger is configured with `headers: false`, so the bearer token never reaches logs. Phase-2 helper scripts live in `tmp/validation/` (inside the workspace, git-ignored). |

## 2. Code quality assessment

The app is small (≈1,600 lines across `app/` + `lib/`; largest file
`app/lib/arithmetic_evaluator.rb` at 153 lines) and the layering is mostly
clean: controllers → `TurnRunner` → (`ChatCompletion`, `TitleGenerator`,
`ConversationBroadcaster`, `ConversationStore`) → adapters. Every class has a
header comment explaining its role and the tests read well. Frank findings:

**Duplication**
- The turn preflight is implemented twice with diverging copy:
  `MessagesController#api_key_present?`/`#budget_message`
  (`app/controllers/messages_controller.rb:34-41`) and
  `TurnRunner#api_key_present?`/`#budget_message`
  (`app/services/turn_runner.rb:51-53,93-96`). The two budget messages are
  worded differently; the busy/lock check is a third variant
  (`messages_controller.rb:15` vs `conversation_store.rb:102`).
- The `"conversation:#{id}"` string is derived independently in three places
  (`Conversation#stream_name` `app/models/conversation.rb:40`,
  `ConversationBroadcaster#stream_name` `:15`, `ConversationStore#key_for`
  `:121`). The Turbo stream name and the Redis key happen to share a format
  purely by coincidence.
- The assistant bubble DOM id `chat_message_<uuid>` (and the `_body`/`_status`
  suffixes) are hand-built in `_pending.html.erb`, `_failed.html.erb` and
  `ConversationBroadcaster#dom_id_for`, while `_message.html.erb` uses
  `dom_id(message)`. Two mechanisms produce the same id; a rename in one
  partial silently breaks streaming (tests would catch it, but the coupling is
  string-based).

**Dead / test-only code**
- `ConversationStore#exists?` and `Conversation#remaining_tokens` are not used
  by any app code (only their tests).
- `ChatCompletion::Result#total_tokens` and `#estimated_tokens` are only read
  by tests.
- `ConversationStore.new(settings:)` injection is never used outside tests.
- `app/helpers/application_helper.rb` is the empty generator stub.

**Coupling / hidden dependencies**
- Views reach into global config: `_sidebar.html.erb:14` and
  `_usage.html.erb:1` call `ChatSettings.current` directly; so does
  `ProviderErrorPresenter.model_hint`. Three process-wide singletons
  (`ChatSettings.current`, `ConversationStore.current`, `AsyncExecutor`) are
  the main seams; tests cope via `ChatSettings.with`, but it is
  service-locator style rather than injection.
- `ConversationStore::Busy` is raised by the store but its user-facing text
  lives in `ProviderErrorPresenter` (`app/lib/provider_error_presenter.rb:43`),
  which is otherwise about provider errors — the presenter's name no longer
  matches its responsibility.
- `ConversationBroadcaster` knows the internal DOM layout of the message
  partials (presentation knowledge in a service).

**Single responsibility / size**
- `TurnRunner` (108 lines) coordinates preflight, generation, persistence,
  three kinds of broadcast and title generation, with five injected
  collaborators. It is readable but is the class that will grow.
- `MessagesController#create` is five guard clauses with early returns; fine,
  but the guards belong to the domain, not the controller.
- `ConversationStore#all` does one `GET` per conversation on every page render
  (N+1 against Redis, no pipelining) and lazily repairs the index.
- `test/integration/chat_flow_test.rb:45-46` packs the payload assertion into a
  one-line `map … .then { … }` that is hard to read.

**Top 3 refactors with more time**
1. Extract a `TurnPolicy` (or `TurnPreflight`) object used by both the
   controller and `TurnRunner`: one place for the missing-key, budget and busy
   checks and their messages. Removes the diverging copy and lets the
   controller respond 422 with the same object the runner uses under the lock.
2. Centralise DOM-id and stream-name derivation (e.g. `MessageDom.id(id, :body)`
   used by partials and broadcaster; have the broadcaster take a
   `Conversation` and call its `stream_name`) and delete the unused methods
   listed above. Cheap, and it eliminates the string-coupling class of bug.
3. Split title generation out of `TurnRunner` into its own follow-up step
   (`TitleTurn`) now that it runs outside the lock, and pass settings into
   views/presenters explicitly instead of reading `ChatSettings.current` from
   ERB. This shrinks `TurnRunner` to "one provider turn" and makes the views
   pure functions of their locals.

## 3. Test coverage assessment

Command: `TEST_REDIS_URL=redis://localhost:6399/1 bin/rails test` (throwaway
`redis:7-alpine` container), run after the fixes above.

| Run | Runs / assertions | Line | Branch |
| --- | --- | --- | --- |
| With `TEST_REDIS_URL` (Redis adapter tests run) | 137 / 556, 0 failures, 0 skips | **660 / 660 = 100.00 %** | **147 / 158 = 93.03 %** |
| Plain `bin/rails test` (5 Redis tests skipped) | 137 / 540, 0 failures, 5 skips | 617 / 660 = 93.48 % | 145 / 158 = 91.77 % |

The 100 % line figure is real but should not be over-read: it is the
`app/` + `config/` Ruby files SimpleCov tracks; JavaScript, ERB, `bin/`, and
`config/puma.rb`'s fork hooks are not measured.

**Uncovered branches** (from `coverage/.resultset.json`): the defensive `else`
arms of the `case` statements in `ArithmeticEvaluator` (unreachable via the
tokenizer), `AsyncExecutor`'s nil-backtrace guards, `ProviderErrorPresenter`
when a response object has no `status`, `TitleGenerator#extract_title` when
content is neither Hash nor String, the `title.blank?` early return in
`TurnRunner#ensure_title`, `ConversationStore.default_adapter`'s Redis arm
(never taken in the test env), and the index-repair arm in
`ConversationStore#all` when a document has vanished.

**Weakest-tested area:** the browser side. The three Stimulus controllers
(Enter-to-send, autosize, scroll pinning, flash dismissal) and the actual
Turbo DOM mutations have no automated tests at all (no system tests, no JS
tests). Second: real Action Cable delivery — tests use the `test` cable
adapter, and the only Redis-adapter test asserts the gem loads. Both were
exercised only by hand in phase 2.

**Failure modes not covered by any test:**
- A worker dying (SIGKILL/OOM/`docker stop` past the 10 s grace) mid-turn,
  leaving the Redis turn lock behind for up to 300 s.
- Redis being unreachable at request time (page renders and turns would 500;
  no rescue exists to test).
- `AsyncExecutor` queue saturation and the `:caller_runs` fallback running an
  LLM round-trip on a Puma request thread.
- Broadcast failure (cable Redis down) while a reply is streaming.
- Corrupt or unknown-schema-version JSON in Redis (`Conversation.from_json`
  raises `KeyError`; nothing catches it).
- A conversation being deleted or expiring *during* a turn (the existing test
  deletes it before the turn starts).
- Two POSTs racing the `locked?` check in `MessagesController` (both render a
  pending bubble; the second turn fails with Busy).
- The budget being exceeded mid-turn during a multi-round tool loop (checked
  only before the provider call).
- The model calling an unknown tool or sending malformed tool arguments;
  SSE `event: error` frames arriving mid-stream (only HTTP-status errors and
  network errors are tested).
- Multi-worker fan-out (`WEB_CONCURRENCY=2`) and the `on_worker_boot` reset
  hooks — live-verified in phase 2 only.
- `bin/docker-entrypoint` (SECRET_KEY_BASE generation) — exercised only by
  the phase-2 compose run.

## 4. Known defects and risks

1. **Stale turn lock after an unclean stop.** The lock is only released in an
   `ensure` (`app/stores/conversation_store.rb:100-109`) with
   `TURN_LOCK_TTL = 300`. `AsyncExecutor.shutdown` waits at most 10 s
   (`app/lib/async_executor.rb:23`), so even a normal restart during a long
   reply — or any kill — leaves the conversation refusing prompts ("A reply is
   still being generated") for up to five minutes.
2. **Lock TTL can expire under a still-running turn.** RubyLLM's
   `complete_once` recurses on every tool-call response with no round limit by
   default (`calls: nil`), and each round may take up to
   `CHAT_REQUEST_TIMEOUT` (120 s) × `max_retries` (1). A pathological turn can
   exceed 300 s; the lock then lapses, a second turn can start concurrently,
   and the first turn's `unlock` deletes the second's lock. The optimistic
   `update` still prevents lost writes, but the "one turn at a time" guarantee
   is not absolute. No `max_tokens` is set either, so a single reply's length is
   bounded only by the model.
3. **Byte cap is approximate.** `Conversation#prune!` keeps at least one message
   (`app/models/conversation.rb:86`), so a single message larger than
   `max_bytes` is stored anyway. Byte-pruning also shifts one message at a
   time, so the retained history can start with an assistant turn (the test at
   `test/models/conversation_test.rb:49-52` codifies this). I have not
   verified whether OpenRouter/Anthropic accept a history beginning with an
   assistant message; if not, a heavily pruned conversation would fail every
   subsequent turn until it is abandoned.
4. **`:caller_runs` fallback blocks request threads.** With 8 pool threads and
   a 64-deep queue per process (`async_executor.rb:37-40`), the 73rd concurrent
   turn runs synchronously inside the Puma request, holding one of only 3
   request threads for the whole provider round-trip. Total outbound
   concurrency is `workers × 8` with no global cap.
5. **Check-then-enqueue race in `MessagesController#create`.** `locked?` is
   read at `messages_controller.rb:15`, the lock is only acquired later on the
   background thread. Two rapid submissions both get a pending bubble; the
   second becomes a failed bubble and its text is dropped from the transcript
   (the user must resend). Harmless to stored history, confusing in the UI.
6. **No isolation between clients (by design, but operationally risky).** There
   is no auth, the conversation list is global (`conversations_controller.rb:5`),
   and anyone who can reach the port can read, delete, and create conversations
   and spend the operator's OpenRouter credits. The per-conversation token
   budget does not limit spend across conversations, and there is no rate
   limit on `POST /conversations` or `/messages`. The number of conversations
   (and Redis memory) is bounded only by the 7-day TTL. Do not expose beyond a
   local demo.
7. **Redis is a hard dependency with no graceful degradation.** Every page
   render calls the store; if Redis is down, `index`/`show` return 500 instead
   of a friendly page. In development, `bin/dev` boots fine without Redis and
   only fails on first request.
8. **Corrupt documents are fatal for that conversation.** `Conversation.from_json`
   uses `fetch` on `id`/timestamps; a hand-edited or future-schema document
   raises on read, and `ConversationStore#all` would raise for the whole
   sidebar (the `SCHEMA_VERSION` field is written but never checked).
9. **Token accounting is approximate when the provider omits `usage`.** The
   fallback estimator counts only system prompt + new prompt + reply
   (`chat_completion.rb:68-71`), ignoring replayed history, so it
   underestimates and the budget is reached later than intended in that case.
10. **Title race after the phase-3 fix.** `ensure_title` now runs outside the
    lock, so its `store.update` can interleave with the next turn's
    `append_exchange`. WATCH/MULTI retries make this safe (up to
    `MAX_ATTEMPTS = 10`), but on a very hot conversation the title write can
    give up with `ConcurrentUpdateError`, which is logged and the conversation
    stays untitled until the next successful exchange.
11. **Content Security Policy is not enabled** (`config/initializers/content_security_policy.rb`
    is the commented generator default). XSS is mitigated by ERB escaping and
    `ERB::Util.html_escape` on streamed chunks (`conversation_broadcaster.rb:20`),
    but there is no CSP backstop.
12. **Configuration is read once per process.** `ChatSettings.current` and
    `RubyLLM.config.default_model` are fixed at boot; changing `CHAT_MODEL`
    etc. requires a restart (documented behaviour, but easy to trip over).
13. **Development Redis persistence is not guaranteed.** Restart survival is
    real under compose (AOF + named volume, `compose.yaml:42-44`); with a local
    `redis-server` using default snapshotting, a crash could lose the last
    minutes of conversations.
14. **`allow_browser versions: :modern`** (`application_controller.rb:3`)
    returns 406 to older browsers; acceptable for a demo but not obvious from
    the UI.
