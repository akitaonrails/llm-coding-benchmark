# SELF_REVIEW — phase 3 of 3

Date: 2026-08-22
Scope: `./project` (Rails 8.1.3.1, Ruby 4.0.6) — builds on phases 1 and 2.

## 0. Fixes applied during this review

One genuine defect was found while re-verifying the goals and was fixed (small,
surgical; no new features):

**G4 defect — the live assistant bubble was never rendered into the page.**
`app/views/messages/_assistant_streaming.html.erb` (the only partial that
renders the streaming targets `content-*` and `message-assistant-*`) was dead
code — nothing referenced it (verified with ripgrep). `ChatEngine` emitted
Turbo Stream `append` events targeting `content-<random>` and a final `update`
targeting `message-assistant-<random>` (`app/services/chat_engine.rb:79,102`),
but those elements never existed in the DOM. Turbo silently no-ops on missing
targets (`targetElementsById` returns `[]`, see turbo-rails 2.0.23
`turbo.min.js`, `StreamActions.append/update` forEach over an empty list), so
**no assistant reply ever appeared in the page until a hard reload**. Phase 2
only inspected the SSE byte stream with curl and timestamped events on the
wire, which is why this was missed.

Fix: `ChatEngine#run_exchange` now appends the streaming bubble before calling
the provider, and `handle_failure` now removes the correctly-prefixed element
ids (`message-*`) instead of bare ids that never existed.
`app/services/chat_engine.rb:63-65,106-112`. The G4 test was strengthened to
assert exactly one streaming bubble is appended and the final update targets
it (`test/services/chat_engine_test.rb:130-141`).

Live re-verification (fresh server, real OpenRouter key): with my fix the first
two SSE events are `append target="messages"` for `_user_message` then
`_assistant_streaming` (containing `id="message-assistant-…"` and `<span
id="content-…">`), followed by incremental `append target="content-…"` token
events, followed by `update target="message-assistant-…"`. Targets now exist,
so Turbo renders tokens incrementally in the page (the goal's client-side
requirement).

## 1. GOAL VERIFICATION TABLE

Re-verified against the code and by running the suite and quality gates on this
machine (2026-08-22). All file:line references are to the current workspace
root `project/`.

| Goal | Verdict | Evidence |
| --- | --- | --- |
| G1 — Rails 8.x/Ruby newest from mise, no AR/Mailer/Job, at workspace root, generated | PASS | Ruby 4.0.6 (`mise.toml:2`, `.ruby-version`), Rails 8.1.3.1 (`Gemfile.lock:276`). `app/models/conversation.rb:3` / `app/models/chat_message.rb:3` are plain-Ruby POROs. `config/application.rb:5-15` requires only active_model, action_controller, action_view, test_unit; active_record/action_mailer/active_job/active_storage are commented out. `bin/`, `app/`, `config/` all live directly at the workspace root. |
| G2 — Tailwind + Hotwire SPA, partials, no single-file CSS/JS dump | PASS | `tailwindcss-rails` native binary (no Node), `turbo-rails` + `stimulus-rails` in `Gemfile:10-11`; 7 view partials under `app/views/messages/` and `app/views/conversations/`; streaming JS is a 84-line Stimulus controller that hands every SSE fragment to `Turbo.renderStreamMessage` (`app/javascript/controllers/chat_controller.js:67-68`) — no `fetch`+`innerHTML` hand-rolling for rendering. |
| G3 — `ruby_llm` latest, OpenRouter, Claude Sonnet default, model via env | PASS | `ruby_llm (1.16.0)` (`Gemfile.lock:276`, latest on rubygems at build time). `config/initializers/ruby_llm.rb:5-9` sets OpenRouter key + base + timeout; `AppConfig::DEFAULT_MODEL = "anthropic/claude-sonnet-5"` with `LLM_MODEL` override (`app/services/app_config.rb:8,19-21`). |
| G4 — TRUE token streaming rendered incrementally in the page | PASS | Fixed this phase (see §0). SSE emits multiple `append target="content-…"` events (timestamped 1.734s, 2.464s, … before the single final `update` in the live capture) and the target elements now exist in the DOM. `app/services/chat_engine.rb:63-65,79,102`. Test `streams into a live assistant bubble then finalizes it in place (G4)` `test/services/chat_engine_test.rb:130`. |
| G5 — multi-turn payload exact, prompt sent exactly once | PASS | `ChatEngine.build_replay` (`app/services/chat_engine.rb:26-28`) appends the new prompt once: unit test asserts the exact 4-element array and exactly-one occurrence for `third question` (`test/services/chat_engine_test.rb:141-159`) plus an end-to-end store→replay test (`:161-177`). Fakes mirror the real RubyLLM `Chat#add_message(role:, content:)` (verified against ruby_llm 1.16.0 `chat.rb:165-168`). |
| G6 — concurrency-safe, bounded, TTL'd persistence that survives restart and WEB_CONCURRENCY=2 | PASS | Shared SQLite file (no process-local store), WAL + `busy_timeout=5000` (`app/services/conversation_store.rb:257-278`). Bounds: msg-count, per-msg bytes, per-conversation bytes (`:190-220`), TTL prune (`:105-110`). Tests cover caps, TTL, restart-new-connection (`test/services/conversation_store_test.rb:11,56,76,88`). Phase 2 runtime: `WEB_CONCURRENCY=2` booted 2 Puma workers against one SQLite file; a 2-turn conversation survived master kill + restart and the model recalled pre-restart turns (phase2.ndjson). |
| G7 — exactly two tools via RubyLLM Tool API | PASS | `build_chat` registers exactly `ServerTime` + `Calculator` (`app/services/chat_engine.rb:117-118`); both subclass `RubyLLM::Tool`. Live this phase: `"What time is it on the server?"` → answered with `2026-08-22T15:38:46Z (UTC)`; `"Compute 123 * 456 using the calculator tool."` → `123 × 456 = **56,088**` (correct tool result 56088). Tool metadata tests `test/tools/server_time_calculator_test.rb`. |
| G8 — structured-output title after first exchange, shown in UI | PASS | `TitleGenerator` uses `with_schema(...).ask(...)` (`app/services/title_generator.rb:19-22`); engine invokes it only when `conversation.title.nil?` (`app/services/chat_engine.rb:122-128`), updates `#conversation-title` and the sidebar; title renders in `app/views/conversations/show.html.erb:7-8`. Tests: `test/services/title_generator_test.rb`, `chat_engine_test.rb:212-230`. Live capture showed `update conversation-title → "Server Time Check"`. |
| G9 — token budgeting, env-configurable, friendly refusal | PASS | `TokenBudget` (`app/services/token_budget.rb`), `TOKEN_BUDGET` default 50_000 (`app/services/app_config.rb:28-32`); refusal before any provider call (`chat_engine.rb:52-54`), budget partial + disabled input (`app/views/messages/_budget.html.erb`, `_form.html.erb:1,11-19`). Tests `test/services/token_budget_test.rb` and `chat_engine_test.rb:191-200`. |
| G10 — system prompt via instructions API, key preflight, rescued provider errors, no failed-turn persistence | PASS | `chat.with_instructions(AppConfig.system_prompt)` (`chat_engine.rb:116`); missing-key preflight returns `missing_key_message` without calling the provider (`chat_engine.rb:48-50`, `app/services/app_config.rb:74-80`); provider errors rescued into a visible error fragment (`chat_engine.rb:106-112`); persistence happens only after a successful response (`chat_engine.rb:94-97`). Tests: failed turns leave the store empty and surface "Something went wrong" (`chat_engine_test.rb:179-210`), title failure falls back (`title_generator_test.rb:45-49`). |
| G11 — Minitest per component, real-API mocks, error paths, SimpleCov | PASS | Ran `bin/rails test` → **56 runs, 155 assertions, 0 failures, 0 errors**; SimpleCov (line) **96.88% (404/417)** `coverage/index.html`. Fakes model the real ruby_llm 1.16.0 surface (`with_instructions`/`with_tool`/`add_message`/`complete` verified in gem source; `Response`/`Message` shape matches `message.rb:31,51-55`). Error paths tested (provider raise, missing key, budget refusal, divide-by-zero, malformed input). Branch coverage: **not available** — `Coverage.supported?(:branch)` returns `false` on this Ruby 4.0.6 build, and SimpleCov 1.1.1 raises `SimpleCov::ConfigurationError` on `enable_coverage "branch"`. |
| G12 — Brakeman, RuboCop, bundle-audit clean | PASS | Ran now: `bin/rubocop` → `43 files inspected, no offenses detected`; `bin/brakeman -q` → `Security Warnings: 0`; `bundle exec bundler-audit check --update` → `No vulnerabilities found` (1234 advisories). |
| G13 — production Dockerfile + compose + README | PASS | `Dockerfile:1-40` (`RAILS_ENV=production`, non-root `appuser`, `bin/docker-entrypoint`, asset precompile); `docker-compose.yml` non-root, named volume `chat_storage`, all env passthrough; `README.md` covers setup, config table, Docker, tests. Phase 2: `docker build` succeeded and `docker compose up --build` answered a real chat message via SSE. My phase-3 changes are Ruby-only (no Docker-affecting changes). |
| G14 — no auth, no secrets committed, everything in workspace | PASS | No auth gem/middleware; no `before_action` authentication anywhere. `config/master.key` is gitignored (`.gitignore:4`); no `.env*` files exist; `rg "sk-or-"` matches only the README placeholder `sk-or-...` (`README.md:50,82`). All sources live inside `project/`. |

## 2. CODE QUALITY ASSESSMENT

Overall: small, readable, well-factored codebase; good naming and separation
between persistence (no AR), orchestration, tools, and views. Service layer is
clean and the store.rb is the right kind of boundary. Below is a frank list of
sore spots.

**What is good**
- `SafeArithmetic` is a tight, correct recursive-descent parser with clear
  `Parser`/`Tokenizer` split, no `eval`, unit-tested edge cases.
- `ConversationStore` keeps all SQL in one file with a single write path
  (`add_message` → `enforce_bounds!`), WAL/fk pragmas set in one place.
- Views are consistent partials; escaping is applied everywhere (ERB in views,
  `CGI.escapeHTML` for streamed tokens).
- `ChatEngine` injects `sse`/`ts`, which keeps the unit tests honest about the
  emitted stream without network.

**Weaknesses:**
1. **God-method + mixed responsibilities** — `ChatEngine#run_exchange`
   (`chat_engine.rb:61-104`) does: rendering user bubble, building replay,
   calling the provider, buffering, computing tokens, persisting, final
   replacement, and title generation. It has to be read top-to-bottom to
   understand, and the token-count `if/else` at `:87-91` is mis-indented.
2. **`SELECT *` positional column mapping** — `conversation_store.rb:229-254`
   maps `row[0]..row[6]` positionally in 3 places; a schema edit silently
   corrupts fields.
3. **Class-level mutable state** — `@connection`, `@schema_ready`, `@mutex`
   as class ivars with `reload!`/`reset!` hooks used by tests; subtle
   cross-construction coupling and a classic test-isolation footgun.
4. **Dead / almost-dead code** — `ConversationStore.reset!`
   (`conversation_store.rb:142`) is never called; `ChatMessage::ROLES/STATUSES`
   (`chat_message.rb:5-6`) and the `status` DB column default `'complete'` are
   never exercised by the app; `_assistant_streaming.html.erb` was dead until
   this review. Small, but present.
5. **Duplicated env-default pattern** — `AppConfig` rescues `ArgumentError`
   five times for nearly identical numeric env reads (`app_config.rb:28-56`).
6. **`conversation.rb:14`** — `def to_param` is misindented (column 0). Valid
   Ruby, passes RuboCop, but sloppy.

**Top 3 things I would refactor with more time:**
1. **Split `ChatEngine#run_exchange`** into a small state object
   (`ExchangeResult` holding buffer, tokens, content) + separate methods for
   build-chat, stream, persist, finalize — removing the 3-phase god-method and
   the `final.respond_to?` duck-typing.
2. **Extract a typed settings loader** shared by `AppConfig`/`TokenBudget`
   (e.g., `EnvSetting.int("MAX_MESSAGES", default: 40)`) to kill the five
   copy-pasted `Integer(...) rescue` blocks.
3. **Replace positional `row[i]` mapping** with column-name-indexed lookups or
   a `RowMapper` so the store doesn't silently mis-attribute columns.

## 3. TEST COVERAGE ASSESSMENT

Command run: `bin/rails test` → **56 runs, 155 assertions, 0 failures, 0 errors.**

| Metric | Value |
| --- | --- |
| SimpleCov line coverage | **96.88% (404 / 417)** `coverage/index.html` |
| SimpleCov branch coverage | not obtainable — this toolchain's Ruby 4.0.6 build reports `Coverage.supported?(:branch) == false`; `enable_coverage "branch"` raises `SimpleCov::ConfigurationError` (SimpleCov 1.1.1). Only line data exists in `coverage/coverage.json`. |
| Files the shortest tests | controllers: `messages_controller_test.rb` (2 tests, `ChatEngine.run` fully stubbed), `conversations_controller_test.rb` (5 tests). |

**Weakest-tested area:** the JS/Stimulus layer and the live
controller↔engine↔provider path. `messages_controller_test.rb:8-14` stubs
`ChatEngine.run` entirely, so the controller's SSE contract is only tested
with a fake fragment. `chat_controller.js` has **zero test coverage**
(no JS/system test harness) — the SSE framing/close/drop paths are verified by
hand only.

**Failure modes NOT covered by any test:**
- Real provider network behavior (timeouts, mid-stream disconnect, retries) —
  mocks only; no stub-server benchmark.
- Client-side: dropped/disconnected SSE mid-stream, non-2xx HTTP, a `chunk`
  that splits a multi-byte UTF-8 char across reads, empty `data:` lines — none
  of it automated.
- Concurrent interventions on the same conversation (threads/turns) — the store
  tests are strictly single-threaded.
- `ConversationStore.reset!` / the `ChatMessage` `:streaming`/`failed` status
  flows (all dead now, so un-covered by definition).
- Budget boundary equality (`total_tokens == budget`, covered for `>=` only
  with values far from the edge).
- Malformed `params` edge cases (e.g. missing `message`, huge bodies) in the
  controllers.

## 4. KNOWN DEFECTS AND RISKS

**Concurrency / consistency:**
1. **Non-atomic budget check-and-increment** — two concurrent turns
   (separate server workers or threads on the same conversation) can both pass
   the budget-refusal gate before their tokens are added
   (`conversation_store.rb:72-81`) → a conversation can exceed its budget and
   run two provider calls.
2. **Read-then-write replay race** — history is read outside the write
   transaction (`chat_engine.rb:64` then `92-97`); two simultaneous turns for
   the same conversation can persist as interleaved user/assistant pairs and
   one replay may omit the other's reply.
3. **`ClientDisconnected` escapes** — a client that closes mid-stream makes
   `SSE.write` raise (`actionpack live.rb`) inside the stream callback; the
   rescue in `run_exchange` then calls `emit_error` / `handle_failure` which
   attempts another `write` → raises again, escapes the controller, and is
   logged as an unhandled error. The failed turn's removals do run, but it is
   noisily an error.
4. **SSE thread holding** — each streaming request holds a Puma thread for the
   whole provider call (up to `request_timeout` = 120s,
   `config/initializers/ruby_llm.rb:8`); no keep-alive and no auth → a handful
   of stalled SSE connections can exhaust the default 3-thread pool
   (demo-grade; see G14).

**Data / correctness:**
5. **Provider payload vs stored divergence on truncation** — the replay to the
   provider uses the raw `@user_text` while the store truncates it at the
   per-message byte cap (`conversation_store.rb:178-188`,
   `app/services/chat_engine.rb:92`); history replayed to the provider next
   turn can then differ from what was stored this turn.
6. **Synchronous title generation** — the title call runs after the reply,
   inside the same SSE connection → first-turn latency tails noticeably (an
   extra provider call), and a very slow title call can outlive the reply's
   last event.
7. **Rough token estimate** — `bytesize / 4` (`token_budget.rb:12`)
   over/under-counts tokens for non-Latin text — acceptable for a hard budget
   guard, but approximate.
8. `SELECT *` positional reads — see §2.2.

**Operational / security:**
9. **No authentication, no rate limiting** — by design (G14), but anyone with
   network access can burn the OpenRouter API budget indefinitely; consider
   a token on the demo route.
10. **`docker-entrypoint` generates a fresh `SECRET_KEY_BASE` when unset**
    (`bin/docker-entrypoint:6-8`) — fine for a local demo, but any restart
    invalidates sessions; a real deployment should set it statically.
11. **No resource limits / restart policies** in `docker-compose.yml`; logs go
    to stdout (good) but the compose app has no `mem_limit`/`pids_limit`.
12. Compose sets `FORCE_SSL: "false"` for local use; a production deployment
    should keep SSL enforcement on.
13. The streaming HTML is escaped, but no CSP is configured
    (`config/initializers/content_security_policy.rb` is commented out) — a
    defense-in-depth gap worth closing before public deployment.

No secrets were found in the workspace, and none of the above blocks goal
completion; items 1-5 are the ones most worth hardening before production.