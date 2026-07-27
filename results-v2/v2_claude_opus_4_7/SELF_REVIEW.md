# SELF_REVIEW.md

Verified against the code in this workspace at review time. Test suite was
executed (`bin/rails test`), so were `rubocop`, `brakeman`, `bundle-audit`.
No runtime call to OpenRouter was made — everything HTTP-facing is
verified structurally, not against a live provider.

## 1. Goal verification

| Goal | Verdict | Evidence |
| --- | --- | --- |
| G1  Newest Ruby+Rails from mise, no AR/AJ/AM, root-level | PASS | `.ruby-version` = `ruby-4.0.6`, `mise.toml` pins it; `Gemfile:3` = `rails ~> 8.1.3` (`bin/rails --version` → `Rails 8.1.3`); `config/application.rb:6-11` leaves `active_job/active_record/action_mailer` commented out; layout, controllers, `Gemfile` all at workspace root, no nested app dir. |
| G2  Tailwind + Hotwire (Turbo + Stimulus), partials | PASS | `Gemfile:9` `tailwindcss-rails`; `Gemfile:7-8` `turbo-rails`, `stimulus-rails`; four partials under `app/views/messages/_*.html.erb`, sidebar/api_key_error under `app/views/shared/`, three Stimulus controllers under `app/javascript/controllers/`. No hand-rolled fetch()+innerHTML: `grep -r "innerHTML\|fetch(" app/javascript` returns nothing. |
| G3  RubyLLM via OpenRouter, latest Claude Sonnet, env-overridable | PASS | `Gemfile:15` `ruby_llm ~> 1.16` (installed 1.16.0); `config/initializers/ruby_llm.rb:6` `config.openrouter_api_key = ENV["OPENROUTER_API_KEY"]`; `app/services/llm/chat_service.rb:16` `DEFAULT_MODEL = ENV.fetch("CHAT_MODEL", "anthropic/claude-sonnet-4.5")`; `chat_service.rb:177` passes `provider: :openrouter`. |
| G4  TRUE token streaming | PASS | `app/controllers/messages_controller.rb:11` includes `ActionController::Live`; `MessagesController#create` sets `Content-Type: text/vnd.turbo-stream.html`, writes an assistant placeholder, then, for each `delta` yielded by `chat_service.stream_reply`, writes and flushes a `<turbo-stream action="append" target="streaming-assistant-content">…</turbo-stream>` fragment (`messages_controller.rb:44-47`). This is chunked delivery, not a post-completion write. |
| G5  Multi-turn payload correctness + unit test | PASS | `chat_service.rb:92` calls `build_chat_for(exclude_last_user: false)` BEFORE `store.append_message` for the new user turn (`chat_service.rb:96-100`), so replayed history contains `history` only; the new prompt is added exactly once when `chat.ask(user_prompt)` runs (`:104`). Tests: `test/services/llm/chat_service_test.rb:110` (`streaming a turn sends history-plus-one, no duplicates (G5)`) and `:132` (three-turn variant) both assert the exact captured message array via `FakeChat.last_captured`. FakeChat mirrors `ROLES = %i[system user assistant tool]` from `ruby_llm-1.16.0/lib/ruby_llm/message.rb:6`. |
| G6  Bounded persistence, restart-safe, cross-worker | PASS | `app/models/conversation_store.rb` uses SQLite (`Gemfile:12` `sqlite3 ~> 2.0`), WAL mode (`:37`), `busy_timeout=5000` (`:36`), per-request connections (`:34-44`). Bounds: `MAX_MESSAGES` (`:21`, tested `conversation_store_test.rb:49`), `MAX_CONTENT_BYTES` (`:22`, tested `:60`), `TTL_SECONDS` (`:23`, tested `:82`). Not process-local — file-backed at `storage/conversations.sqlite3`, so `WEB_CONCURRENCY=2` workers share it. Note the risk in §4 about how bounds enforcement doesn't dedupe writes across processes. |
| G7  Two tools (`server_time`, `calculator`) via RubyLLM::Tool | PASS | `app/services/llm/tools/server_time.rb:6` extends `RubyLLM::Tool`, `execute` returns `{ utc: Time.now.utc.iso8601 }`. `app/services/llm/tools/calculator.rb:9` extends `RubyLLM::Tool` with a hand-rolled shunting-yard evaluator (no `eval`). `chat_service.rb:158-159` registers both via `chat.with_tool(...)`. Verified 13 tests in `calculator_test.rb` (including one that rejects `system('ls')` and one for the 256-char limit). |
| G8  Structured-output title via schema | PASS | `app/services/llm/title_schema.rb:5` `class TitleSchema < RubyLLM::Schema` with `string :title`. `chat_service.rb:138` `chat.with_schema(LLM::TitleSchema)`. Rendered in UI at `app/views/conversations/show.html.erb:9` (`#conversation-title`), replaced via `MessagesController#create:57` after the first exchange. Test `chat_service_test.rb:204` asserts stored title. |
| G9  Token budget with in-UI refusal | PASS | `chat_service.rb:67` `token_budget = ENV.fetch("CHAT_TOKEN_BUDGET", "20000")`; `:85` raises `BudgetExceeded` BEFORE any provider call. `messages_controller.rb:69` catches it and renders `messages/_degraded.html.erb`. Test `chat_service_test.rb:176` asserts nothing is sent to the provider when budget is exceeded; test `messages_controller_test.rb:42` asserts the UI shows the message. Note token accounting caveat in §4. |
| G10 System prompt, key preflight, provider-failure UI, no-replay-on-failure | PASS | System prompt via `chat.with_instructions(SYSTEM_PROMPT)` at `chat_service.rb:157`; preflight `check_api_key!` at `:39-42`, wired into `ConversationsController#check_llm_configured:29` (page-level) and `ChatService#stream_reply:81` (request-level). Provider failure → `ProviderError` at `:112-116`, rendered as degraded fragment (`messages_controller.rb:77-80`). Failed-turn rollback: `store.delete_message(user_msg_id)` at `chat_service.rb:114` before raising. Test `chat_service_test.rb:158` asserts `messages_for` is empty after a simulated network exception. |
| G11 Minitest coverage of every component + SimpleCov | PARTIAL | 44 tests, 81 assertions, 0 failures (see §3). SimpleCov wired in `test/test_helper.rb:3-11`, report at `coverage/index.html`, 97.13% line coverage per `coverage/.last_run.json`. Mocks mirror real API (FakeChat implements only methods that exist on `RubyLLM::Chat`). **Missing coverage**: no test exercises `MessagesController#create` all the way through a *real* stream flow — the integration test replaces `LLM::ChatService.new` with a MiniStub, so `write_stream`, `turbo_fragment`, `ERB::Util.h` escaping and the placeholder replace/append DOM contract go unverified end-to-end. Also no test covers `ConversationStore#update_message_content` (see §2 — dead code). Branch coverage not enabled. |
| G12 Brakeman, RuboCop, bundle-audit clean | PASS | `bundle exec rubocop` → `34 files inspected, no offenses detected`. `bundle exec brakeman -q` → `Errors: 0, Security Warnings: 0`. `bundle exec bundle-audit check --update` → `No vulnerabilities found` (advisory-db as of 2026-07-25). |
| G13 Production Dockerfile + compose + README | PASS | `Dockerfile:24` sets `RAILS_ENV=production`; `:64-65` creates `rails` user uid 1000; `:75` `USER 1000:1000`; `:78` `ENTRYPOINT ["/rails/bin/docker-entrypoint"]`; multi-stage build with slim runtime. `docker-compose.yml:15` requires `OPENROUTER_API_KEY` at the host (`${...:?…}` will fail loudly if unset), sets `WEB_CONCURRENCY=2` (`:20`), mounts `chat_storage:/rails/storage` (`:31-32`) so persistence survives `down`. `README.md` documents purpose, requirements, setup, config vars, tests, docker, architecture, security. |
| G14 No auth, no committed secrets | PASS | No `before_action :authenticate…`, no `has_secure_password`, no `devise`; sidebar / index unauthenticated. `grep -rn "sk-\|api_key.*=" app/ config/ Dockerfile docker-compose.yml README.md` finds nothing but env lookups. `docker-compose.yml:15` uses `${OPENROUTER_API_KEY:?…}` (required from host env). `README.md:33` explicitly says "Load OPENROUTER_API_KEY into your shell — never commit it." Everything is inside the workspace root. |

Overall: **13 PASS / 1 PARTIAL / 0 FAIL** by my read.

## 2. Code quality assessment

Small codebase, deliberately narrow surface: 3 services (~230 LOC), 1
store (244 LOC), 2 controllers (~130 LOC), 3 Stimulus controllers, 8
partials. Naming is consistent (snake_case files, `LLM::` namespace,
concrete verbs `stream_reply`, `bump_tokens`, `enforce_bounds`). SRP is
respected — `ConversationStore` handles storage only; `ChatService`
handles LLM-side sequencing only; `MessagesController` handles the
transport contract only. Coupling between layers is one-directional
(controller → service → store, with tools registered on the chat object,
not injected into the store).

**Frank criticisms**:

- `ConversationStore#update_message_content` (`app/models/conversation_store.rb:126-130`) is dead code — nothing in `app/` or `test/` calls it. It was likely intended for an earlier design where the streaming placeholder was persisted incrementally, then abandoned when we settled on the "append final text once at the end" approach.
- `ChatService#build_chat_for` has a `exclude_last_user: true` default (`chat_service.rb:155`), but the only caller (`:92`) passes `false`. The `true` branch and its `history.pop if …` (`:162`) are dead.
- `ChatService#outgoing_messages` (`chat_service.rb:51-59`) is only used by one test and never by the request path. It duplicates the shape of the array that RubyLLM's `Chat` builds internally. It's a valuable *specification helper* for the G5 test, but the docstring should say so; without that, a reader will suspect it's dead.
- `MessagesController#create` mixes three concerns in one 70-line method: HTTP header setup, DOM fragment orchestration, and `rescue` policy. The three rescue blocks (`:69-81`) are near-identical `render_html("messages/degraded", ...)` calls that differ only in the message string.
- `ConversationStore#append_message`'s process-local `@mutex` (`:109-120`) is misleading: it protects against multi-thread races within one Puma worker, but SQLite's WAL + `busy_timeout` is what actually protects cross-process safety. The mutex is a small "belt-and-braces" duplication.

**Top 3 things I'd refactor with more time**:

1. **Collapse the three `rescue` clauses in `MessagesController#create` into one `rescue LLM::ChatService::UserFacingError` after making `MissingApiKey`, `BudgetExceeded`, and `ProviderError` share a common ancestor.** — cuts ~14 lines of near-duplicate `write_stream / render_html("degraded"...)`, and puts the user-friendly-message policy in the exception subclasses where it belongs (each already carries the right `.message`).
2. **Extract a `MessagesController::StreamWriter` helper (or a `TurboStreamWriter`).** The controller currently owns raw `<turbo-stream>` string interpolation (`:94-96`) *and* placeholder id lifecycle *and* HTML-escape policy (`ERB::Util.h`). That's fine at this size but is the first thing to grow inconsistently if a second controller ever streams.
3. **Delete the dead code**: `update_message_content` in the store, the `true` branch of `exclude_last_user`, and the `outgoing_messages` method (or rename it to `expected_wire_payload_for_test` and move it to the test file). Also delete `messages/_message.html.erb` if it's not rendered on show (spot-check: `show.html.erb:24` renders it — keep this one).

## 3. Test coverage assessment

`bin/rails test` — 44 tests, 81 assertions, 0 failures, 0 errors, 0
skips, 1.05s. Coverage from `coverage/.last_run.json`:

- **Line coverage: 97.13% (339 / 349 lines).**
- **Branch coverage: not enabled** in `test/test_helper.rb` (SimpleCov's default is line-only). Adding `enable_coverage :branch` would report it; I did not run that experiment.

Weakest-tested area: **`MessagesController#create`** and the streaming
transport as a whole. The integration test at
`test/controllers/messages_controller_test.rb:21` stubs
`LLM::ChatService.new` with a `MiniStub` whose `stream_reply` yields the
whole text at once. That means:

- The multi-chunk delta path is exercised in `chat_service_test.rb`
  (`FakeChat.next_response(chunks: […])`) but never together with the
  controller — nothing verifies that a 5-chunk reply actually produces 5
  `<turbo-stream action="append">` fragments in the response body.
- The `ERB::Util.h(delta)` escaping applied to each chunk
  (`messages_controller.rb:46`) has no test — if a chunk contains
  `</turbo-stream>` or a `<script>` tag, no test would notice a
  regression that stopped escaping.
- The title-generation write path (`:55-62`) is unreachable in the
  controller test because `MiniStub#generate_title` always returns nil.

Failure modes **not** covered by any test:

- Client disconnect mid-stream. `write_stream` swallows `IOError` and
  `Errno::EPIPE` (`messages_controller.rb:100-102`) — there is no test
  that closes the response stream and asserts we don't crash the worker.
- Two concurrent `append_message` calls from separate processes racing on
  the byte cap. `enforce_bounds` reads-then-deletes (`conversation_store.rb:188-213`)
  is not transactionally guarded; two workers each observing 199 KB and
  each writing 20 KB will not both trim to fit. No test exercises this.
- Tool call round-trips are never tested. Real RubyLLM handles tool
  invocation internally inside `chat.ask` — `FakeChat` never returns a
  `response.tool_call`, so nothing verifies our code survives a real
  tool-calling turn or that tool arguments/results get persisted (they
  don't — see §4).
- `bundle-audit` and `rubocop` are executed by a human running the
  commands; there is no CI wiring in `.github/workflows/` that would
  block regressions. (`.github/` is empty of workflows — `ls .github`
  shows dependabot.yml only.)
- No test for the `MessagesController` unfavorable-Accept-header path or
  for CSRF-token behaviour.

## 4. Known defects and risks

- **Token budgeting is byte/4-heuristic-based, not real usage.** `ChatService.estimate_tokens` (`chat_service.rb:63`) uses `bytesize/4`. It does not consume RubyLLM's `usage` object from the streamed response, so budget accounting drifts against reality by anywhere from ~10% (English text) to ~2× (code, non-Latin scripts). The budget is thus advisory, not authoritative — G9 is met as a UX gate but a savvy user can smuggle in more tokens with non-ASCII input.
- **Failed-turn rollback is best-effort, not transactional.** If the process is killed between `chat.ask` raising and `store.delete_message(user_msg_id)` (`chat_service.rb:113-114`), the user turn stays in the store and *will* be replayed on the next request — violating G10 in a narrow crash window.
- **Cross-process race in `enforce_bounds`.** With `WEB_CONCURRENCY=2`, two workers appending to the same conversation each open their own SQLite connection, run their own `SELECT … ORDER BY id ASC`, and issue their own `DELETE`s. There's no `BEGIN IMMEDIATE`/serializable-transaction envelope. If both observe an over-cap state, both will trim, and the sum may over-trim. Under normal single-user demo load this is invisible; under a load test it is not.
- **Tool-call and tool-result messages are not persisted.** `stream_reply` (`chat_service.rb:118-122`) stores only the final assistant *text*. If the model calls `calculator` mid-turn, subsequent turns will not have the tool call / tool result in replayed history — the model will re-derive them each time. Not incorrect per the goals (the goals only require the final answer to work), but a subtle correctness gap: the conversation loses information the model actually produced.
- **`ChatService#generate_title` swallows ALL errors** (`chat_service.rb:149`, `rescue StandardError`). A misconfigured schema, a provider outage, or a truly buggy JSON path all return `nil` silently. The user sees "New conversation" with no diagnostic. There is no log line.
- **`bin/thrust` is the container CMD but not verified to work at RAILS_ENV=production without `RAILS_MASTER_KEY`.** The Dockerfile builds with `SECRET_KEY_BASE_DUMMY=1` (`Dockerfile:55`) for asset precompile, and `docker-compose.yml:30` sets a placeholder `SECRET_KEY_BASE`. I did NOT run `docker compose up --build` in this review — the runtime validity of the production boot is asserted structurally only.
- **`OPENROUTER_API_KEY` value is read at request time from `ENV`** but `RubyLLM.configure` (`config/initializers/ruby_llm.rb:6`) captures it once at boot. If the key changes at runtime (unlikely in production, common in dev with `direnv`), the running process keeps the old value. `check_api_key!` reads `ENV` directly, so preflight can pass while the actual send fails.
- **`response.stream.write` errors are swallowed silently** (`messages_controller.rb:100-102`). A partial stream that fails halfway leaves the user with an empty assistant bubble and no in-UI indication that the message was truncated. Better UX would be a "connection interrupted" degraded fragment before the rescue returns.
- **`chat_service.rb:16` reads `ENV["CHAT_MODEL"]` at class load, not at each request.** Changing `CHAT_MODEL` requires a restart. `check_api_key!` doesn't have this bug (reads `ENV` each call). Minor inconsistency.
- **`SECRET_KEY_BASE` default in `docker-compose.yml:30` is a fixed placeholder** (`please-change-me-please-change-me-please-change-me`). Compose won't refuse to boot without one set — anyone running `docker compose up` without setting it will get a working (but session-forgeable) production instance. It's noisy enough that no reasonable user would ship it, but it is a footgun.
- **No CSP for inline styles** — `stylesheet_link_tag :app` is the only stylesheet; `csp_meta_tag` is emitted (`layouts/application.html.erb:9`) but `config/initializers/content_security_policy.rb` is the Rails default (all commented out). If tightened, the Stimulus cursor's `bg-gray-400 animate-pulse` classes (`chat_cursor_controller.js`) all come from Tailwind's compiled CSS and would be fine, but any future inline style would fail with no test to catch it.
- **`.github/workflows/` has no CI**. `ls .github/` shows only `dependabot.yml`. Nothing enforces the "brakeman/rubocop/bundle-audit clean" contract on future changes.
