# Self-Review — MiniChat (phase 3)

Re-verified against the live tree on 2026-07-29. Commands run in this session:
`bin/rails test` → 45 tests, 82 assertions, 0 failures; SimpleCov line **97.12%**.
`bundle exec rubocop` → 34 files, 0 offenses.
`bundle exec brakeman -q` → 0 warnings.
`bundle exec bundle-audit check --update` → 0 vulnerabilities.
Phase 2 runtime proofs (boot, streaming, tools, WEB_CONCURRENCY=2 restart, docker) were already recorded; this review does not re-run provider E2E.

No code fixes were made in this phase.

---

## 1. Goal verification table

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | PASS | Ruby 4.0.6 (`.ruby-version`), Rails 8.1.3 (`Gemfile:3`, `Gemfile.lock`). `config/application.rb:3-8` loads only active_model, action_controller, action_view, action_cable, test_unit — no Active Record / Action Mailer / Active Job. App lives at workspace root (no nested app dir); no `db/`. |
| G2 | PASS | Tailwind via `tailwindcss-rails` (`Gemfile:9`); Hotwire gems turbo/stimulus; layout `app/views/layouts/application.html.erb` + partials under `app/views/{conversations,messages,shared}/`; Stimulus controllers in `app/javascript/controllers/` (`chat`, `composer`, `chat_cursor`). Composer uses `form_with` + `turbo_stream: true` (`_composer.html.erb:1-7`), not fetch/innerHTML. |
| G3 | PASS | `ruby_llm` 1.16.0 (`Gemfile:15` / lockfile). `config/initializers/ruby_llm.rb:5-6` sets `openrouter_api_key`. Default model `anthropic/claude-sonnet-4.5` (`chat_service.rb:8`); override via `CHAT_MODEL`. `RubyLLM.chat(..., provider: :openrouter, ...)` at `chat_service.rb:143`. |
| G4 | PASS | True incremental streaming via chunked HTTP turbo-stream body, not a single post-completion append: `MessagesController` includes `ActionController::Live` (`messages_controller.rb:6`), sets `text/vnd.turbo-stream.html` (`:23`), writes per-token appends in the `stream_reply` block (`:38-39`). Phase 2 proof: raw socket POST observed **105** `<turbo-stream action="append" target="streaming-assistant-content">` fragments spanning ~5.5s, then final `replace`. Note: delivery is response-streamed Turbo fragments, not ActionCable `broadcast` / `turbo_stream_from` (no `app/channels`). |
| G5 | PASS | `stream_reply` builds chat from store **before** appending the new user message (`chat_service.rb:64-71`) then `chat.ask(user_prompt)`, so the new turn is not double-presented from history. Unit tests assert exact arrays: `outgoing_messages returns exactly history + new user turn`, `streaming a turn sends history-plus-one, no duplicates (G5)`, `streaming for a third turn still sends exactly one copy of the latest user prompt` in `test/services/llm/chat_service_test.rb`. |
| G6 | PASS | SQLite store `app/models/conversation_store.rb` — path `CHAT_DB_PATH`/`storage/conversations.sqlite3`, WAL + busy_timeout (`:32-42`), message/byte caps + TTL (`:21-23`, `enforce_bounds` `:177-202`, `expired?` `:173-175`). Not process-local: shared DB file. Phase 2: `WEB_CONCURRENCY=2`, codeword retained across kill/restart. Tests: `ConversationStoreTest` max messages, byte cap, TTL expiry. |
| G7 | PASS | Exactly two tools: `LLM::Tools::ServerTime` (`name` → `server_time`) and `LLM::Tools::Calculator` (`name` → `calculator`), both `RubyLLM::Tool` subclasses; registered in `build_chat_for` (`chat_service.rb:124-125`). Calculator is hand-rolled RPN, never `eval` (`calculator.rb`). System prompt directs tool use (`chat_service.rb:17-18`). Phase 2: wall-clock server time answer; `(123 * 456) + 789` → 56877 with tool log. Unit tests under `test/services/llm/tools/`. |
| G8 | PASS | `LLM::TitleSchema < RubyLLM::Schema` with `string :title` (`title_schema.rb`). After stream, if `conversation[:title]` empty, `generate_title` runs (`messages_controller.rb:46-52`) using `chat.with_schema(LLM::TitleSchema)` (`chat_service.rb:106-107`). UI target `conversation-title` (`show.html.erb:9-10`). Tests: `generate_title stores the returned title`, `generate_title accepts string JSON content`. |
| G9 | PASS | Approx tokens via `estimate_tokens` + `bump_tokens` (`chat_service.rb:47-53,58-62,93`; store `:136-149`). Budget `CHAT_TOKEN_BUDGET` default 20000. Over budget raises `BudgetExceeded` before provider call; controller renders degraded partial (`messages_controller.rb:59-62`). Meter partial `conversations/_token_meter`. Test: `budget exceeded raises before touching the provider and persists nothing`. |
| G10 | PASS | System prompt via `chat.with_instructions(SYSTEM_PROMPT)` (`chat_service.rb:123`, prompt `:14-20`). Missing key: `check_api_key!` + index/show preflight (`conversations_controller.rb:29-34`) and actionable partial `shared/_api_key_error.html.erb`. Provider failures → `ProviderError`, UI degraded (`messages_controller.rb:67-70`); failed user turn deleted (`chat_service.rb:84`). Tests: provider rollback, missing key (controller + service), degraded controller response. |
| G11 | PARTIAL | Controllers, store, `ChatService`, and both tools covered (45 tests). Mock `FakeChat` mirrors `with_instructions` / `with_tool` / `with_schema` / `add_message` / block `ask`. SimpleCov wired (`test/test_helper.rb:3-11`), report `coverage/index.html`, **97.12%** line. Gaps: no tests for Stimulus JS; `MissingApiKey` rescue in `MessagesController` unhit (`messages_controller.rb:63-66`); real RubyLLM streaming/tool integration not tested (only fakes); branch coverage not enabled. |
| G12 | PASS | This session: RuboCop 0 offenses; Brakeman 0 warnings; bundle-audit 0 CVEs. |
| G13 | PASS | `Dockerfile`: `RAILS_ENV=production`, non-root `USER 1000:1000`, `ENTRYPOINT` `bin/docker-entrypoint`, Thrust+Rails CMD. `docker-compose.yml` builds, maps 3000:80, volume for storage, `WEB_CONCURRENCY=2`. `README.md` documents purpose, setup, env vars, tests, Docker. Phase 2: `docker build` + `docker compose` E2E chat answered. |
| G14 | PASS | No auth routes/controllers. No real API keys in source/Dockerfile/compose (key from env only). `config/*.key` gitignored (`.gitignore:27`). README uses `sk-...` placeholder only. Entire app under workspace `project/`. |

---

## 2. Code quality assessment

**What works**
- Clear layering: thin controllers → `LLM::ChatService` → `ConversationStore` + RubyLLM tools.
- Naming is straightforward (`stream_reply`, `enforce_bounds`, `BudgetExceeded`).
- Calculator is self-contained and well corresponding to tests.
- Env-driven config avoids hard-coding.

**Friction**
- `ConversationStore` is a Singleton + manual SQL. Acceptable without AR, but mixes connection lifecycle, schema, bounds, and domain API in one ~230-line class (`conversation_store.rb`).
- `MessagesController#create` owns streaming protocol, rendering, title side-effect, token meter, and error mapping (~65 lines). High responsibility for one action.
- Dead / vestigial paths: `update_message_content` (`conversation_store.rb:118-122`) never called; `role == "failed"` store/filter/UI (`messages_for`, `_message.html.erb`) while failures use `delete_message` instead.
- `outgoing_messages` is only used by tests as a specification helper — production path is `build_chat_for` + `ask`, so two parallel “history assembly” paths exist (`chat_service.rb:37-45` vs `:121-135`).
- Process-local `@mutex` around append does not coordinate across Puma workers (relies on SQLite busy handling alone).
- Empty `ApplicationHelper`; Action Cable railtie loaded but unused (no channels).
- Assistant content is plain-escaped text (`<%= content %>`), not Markdown — system prompt claims Markdown fences but UI will not render them.

**Top 3 refactors with more time**
1. **Persist tool-call / tool-result turns (or strip tools from replay entirely)** — today only final assistant text is stored (`chat_service.rb:88-92`). Multi-turn after tools depend on the model re-deriving facts; provider history can be inconsistent with Code describing tools.
2. **Split `MessagesController#create`** into stream writer + result handlers (title/meter/errors), and/or extract a `TurboStreamWriter` so Live I/O is testable without full integration stubs.
3. **Unify history assembly** — delete tempo `outgoing_messages` or make `stream_reply` assert/produce from one shared builder so G5 cannot drift between helper and real path.

---

## 3. Test coverage assessment

| Metric | Value |
|--------|-------|
| Line coverage | **97.12%** (338 / 348 lines) — `bin/rails test` / SimpleCov `.last_run.json` |
| Branch coverage | **Not enabled** (`SimpleCov.start` without `enable_coverage :branch`) — no branch % reported |

Uncovered / near-miss application lines from coverage data:
- `conversation_store.rb:119-120` (`update_message_content`)
- `conversation_store.rb:193-195` (byte-trim loop edge when message-count overflow already queued deletes)
- `chat_service.rb:82,118,143` (re-raise path, `generate_title` rescue nil, real `RubyLLM.chat` builder)
- `messages_controller.rb:49,64` (title turbo replace when title generated; MissingApiKey rescue)

**Weakest-tested area:** Live streaming / browser layer — Stimulus (`composer_controller.js`, `chat_controller.js`, `chat_cursor_controller.js`) has **zero** tests; controller streaming tests buffer the full body with a stub that yields one chunk, so multi-chunk flush, client disconnect (`write_stream` IOError), and mid-stream provider failure are not exercised.

**Failure modes not covered by any test**
- Mid-stream provider exception after some tokens already written (UI partial content + rollback interaction).
- Client disconnect during `ActionController::Live` stream.
- Concurrent appends under true multi-process (`WEB_CONCURRENCY=2`) race on bounds/tokens.
- Tool-using multi-turn history replay after a prior tool call.
- `generate_title` provider failure during the happy-path stream (only returns nil; controller silent).
- `MessagesController` `MissingApiKey` path after a POST (only ConversationsController GET preflight).
- Calculator pathological inputs (`2**999999` CPU/time, stack overflows).
- Real OpenRouter API contract changes / schema response shapes beyond Hash and JSON string.
- Docker/production SECRET_KEY_BASE weakness and thruster proxy buffering (streaming under reverse proxy).

---

## 4. Known defects and risks

1. **Tool turns not persisted.** Only user + final assistant text are written. After a tool-backed answer, subsequent provider payloads lack tool_call/tool_result messages; model may hallucinate prior numbers/times. Schema has columns for tool metadata but `stream_reply` never fills them.

2. **Streaming ≠ ActionCable broadcast.** Goal wording says “Turbo Stream broadcasts”; implementation uses current-request chunked turbo-stream HTML. Works (phase 2), but multi-tab sync and classic `broadcasts_to` patterns are absent. Proxies that buffer (without `X-Accel-Buffering: no` honored end-to-end) can collapse “true” streaming.

3. **Cross-worker mutex is cosmetic.** `@mutex` in `ConversationStore` is per-process. Two workers can interleave append + `enforce_bounds`; last writer wins. SQLite busy_timeout helps but bounds enforcement is not transactional with the insert (`append_message` insert then separate connection in `ensure enforce_bounds`).

4. **Token budget is approximate and one-sided.** `bytesize/4` estimator; budget check uses current_tokens + prompt only, not expected completion. Assistant output can push stored tokens past budget after the call. No ballasting of system prompt / tools / titles against the meter.

5. **Title generation is synchronous on the stream request.** Blocks closing the stream until a second full LLM round-trip finishes (`messages_controller.rb:46-52`). Failures are swallowed (`generate_title` rescues to nil).

6. **Calculator resource risk.** `**` with huge exponents can CPU-spin or allocate large integers; only length cap 256 chars. Sufficient for demo, not a sandbox.

7. **No authentication / tenancy (by design).** Any client who can reach the port can read/create all conversations (UUID security-through-obscurity only). List endpoint exposes recent conversations.

8. **Compose default `SECRET_KEY_BASE`.** `docker-compose.yml:18` ships a fixed fallback string if unset — weak for any shared deploy.

9. **Expired conversations are filtered on read, not purged.** SQLite grows until manual cleanup; TTL only hides rows in `find`/`list`.

10. **`role: "failed"` path is dead.** Rollbacks delete messages; UI branch and store blog for `failed` are unused leftover, increasing reader confusion.

11. **Puma + Live + threads.** Long-lived LLM streams occupy a Puma thread for the whole generation; with default thread pool and multi-worker this can stall other requests under load. No queue/async job path (Active Job intentionally omitted).

12. **Markdown/XSS surface is OK-by-escape, not rich.** Content is ERB-escaped (safe), so any “```” / HTML in model output shows as raw text; streaming uses `h(delta)`. No extra CSP beyond Rails default.

13. **No automated regression for phase-2 E2E proofs.** Streaming timing, tool invocation via real model, multi-worker restart, and compose chat are manual-only; suite cannot catch regressions there.

14. **Git history empty.** `git log` has no commits yet; reproducibility of “what shipped” is filesystem-only for this benchmark run.
