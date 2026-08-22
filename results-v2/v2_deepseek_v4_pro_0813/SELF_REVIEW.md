# Self-Review

Reviewer: phase 3 (self-review). Scope: verify goals G1–G14 against the code as it
exists now, not against intent. Commands were re-run in this phase unless noted.
The repo has **no commits yet** (`git status` reports "No commits yet"; all files
untracked).

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
| --- | --- | --- |
| G1 | PASS | `config/application.rb:5-15` requires only `active_model`, `action_controller`, `action_view`, `rails/test_unit`; Active Record/Mailer/Job are commented out. `Gemfile:4` pins `rails ~> 8.1.3`; `.ruby-version` = `4.0.6`; app lives at workspace root (no nested app dir). `ruby --version` → `ruby 4.0.6`. |
| G2 | PASS | Tailwind (`app/assets/tailwind/application.css`, `tailwindcss-rails` in `Gemfile:16`), Hotwire (turbo-rails + stimulus-rails, `Gemfile:12-14`), Stimulus controller `app/javascript/controllers/chat_controller.js`, Views are partials (`_message`, `_user`, `_assistant`, `_form`, `_sidebar`, `_live_assistant`, `_error`). No single-file CSS/JS dump; streaming uses `turbo_stream` helpers, not `fetch()+innerHTML`. |
| G3 | PASS | `Gemfile:19` `ruby_llm "~> 1.16"` (resolved 1.16.0). `config/initializers/ruby_llm.rb:7-9` sets `openrouter_api_key`. `lib/chatbot/config.rb:11,14,18-20` default `anthropic/claude-sonnet-4.6`, `PROVIDER = :openrouter`, overridable via `LLM_MODEL`. |
| G4 | PASS | `app/services/chat_service.rb:40-45` yields each non-tool chunk to `on_chunk`; `app/controllers/messages_controller.rb:88-90` emits `turbo_stream.append(target-content, chunk)` per chunk; `app/views/messages/create.turbo_stream.erb:5-7` injects `<turbo-stream-source>`. Test `streams tokens incrementally and returns token usage` (`test/services/chat_service_test.rb:87-103`) asserts chunks `["Hel","lo "]`. Verified via code + unit test only; no live OpenRouter stream was re-run this phase. |
| G5 | PASS | Test `sends the exact outgoing message array for a multi-turn conversation (G5)` (`test/services/chat_service_test.rb:57-72`) asserts `[system, user1, assistant1, user2, assistant2, user3]`; `history_before_new_turn` pops the pending user turn (`chat_service.rb:61-65`); the new turn is added once by `chat.ask` (`chat_service.rb:40`). `FakeProvider#complete` signature matches the real `RubyLLM::Provider#complete` (`ruby_llm-1.16.0/lib/ruby_llm/provider.rb:44`). |
| G6 | PASS | SQLite (no process-local store) with WAL + `busy_timeout=5000` + IMMEDIATE read-modify-write (`app/models/conversation_repository.rb:68-79,102-128`). Message/byte caps + TTL (`app/models/conversation.rb:53-58,124-138`; `config.rb:38-48`). Test `survives an application restart` (`conversation_repository_test.rb:26-35`) and `concurrent appends from multiple threads are safe` (:91-102). Cross-*process* (WEB_CONCURRENCY=2) is implemented but not exercised by the suite (see §4). |
| G7 | PASS | Exactly two tools registered: `chat.with_tools(Tools::ServerTime, Tools::Calculator)` (`chat_service.rb:28`); test `exposes exactly the two required tools` (`chat_service_test.rb:116-119`). `server_time` → `Time.now.utc.iso8601` (`tools/server_time.rb:13`); `calculator` uses Dentaku, never `eval` (`tools/calculator.rb:20,29`), with test `calculator does not execute arbitrary Ruby` (`tools_test.rb:41-44`). |
| G8 | PASS | `TitleGenerator` calls `chat.with_schema(TitleSchema).ask(...)` (`app/services/title_generator.rb:15`); `TitleSchema < RubyLLM::Schema` with `string :title` (`app/services/title_schema.rb:9-10`); triggered only on first completed exchange (`messages_controller.rb:105-137`). Tests in `test/services/title_generator_test.rb`. |
| G9 | PASS | `TOKEN_BUDGET` env override with default `20000` (`config.rb:34-36`); `budget_exceeded?` (`conversation.rb:70-72`); refusal with friendly message before provider call (`messages_controller.rb:21-31,187-189`; `chat_service.rb:37`). Tests `raises BudgetExceededError` (`chat_service_test.rb:105-114`) and `create refuses the turn when the token budget is exceeded` (`messages_controller_test.rb:73-85`). |
| G10 | PASS | System prompt via `with_instructions` (`chat_service.rb:27`). Missing-key preflight: banner (`layouts/application.html.erb:23-27`) + `OPENROUTER_API_KEY` error (`messages_controller.rb:19-20,183-185`). Provider failures rescued to visible error (`messages_controller.rb:64-69`). Failed turns rolled back: `remove_pending_user_message` (`messages_controller.rb:66`, `repository.rb:83-87`) + test `stream rolls back the pending user message on provider failure` (`messages_controller_test.rb:112-137`). |
| G11 | PASS | Minitest suite: `bin/rails test` → 51 runs, 127 assertions, 0 failures, 0 errors. SimpleCov wired with branch coverage (`test/test_helper.rb:3-13`). Mocks mirror the real RubyLLM API (`FakeProvider#complete` vs real provider signature). Error paths covered. |
| G12 | PASS | Re-run: `bin/rubocop` → "40 files inspected, no offenses detected"; `bin/brakeman --no-pager` → "Security Warnings: 0"; `bin/bundler-audit check` → "No vulnerabilities found". |
| G13 | PASS | `Dockerfile:9-40` (`RAILS_ENV=production`, non-root `appuser`, `ENTRYPOINT bin/docker-entrypoint`, `assets:precompile` at build); `bin/docker-entrypoint` generates `SECRET_KEY_BASE` per container; `compose.yaml` runs the app with a named volume. `README.md` documents what/setup/run. Verified by inspection; `docker build` was not re-run this phase. |
| G14 | PASS | No auth: routes expose no auth (`config/routes.rb`); no secret values found in source (grep for `sk-or-`/`sk-ant-`/inline key literals returned nothing). `config/master.key` is gitignored (`.gitignore:33`); no `.env` files; no commits exist so nothing is committed. Caveat: `COPY . .` without `.dockerignore` still ships `master.key` into a build image (see §4). |

## 2. Code Quality Assessment

Layering is clean: `ChatService` (provider payload/streaming), `Conversation`
(domain caps/tokens), `ConversationRepository` (SQLite), `Message` (value object),
controller (HTTP). No ActiveRecord. `ChatService` (66 lines) and `Message` (55
lines) are tight and single-purpose.

Issues, with the most important first:

* `MessagesController` is 194 lines and owns too much: SSE framing (`emit`,
  `prepare_sse`), token streaming, title-generation trigger, budget gating,
  HTML-escaping helpers (`chunk_html`), and ~10 private view-target helpers. This
  is HTTP plumbing and domain orchestration mixed in one class.
* Duplicated budget/refusal logic: `budget_exceeded?` is checked twice
  (`messages_controller.rb:21` and `:80`), with nearly identical error/replace
  turbo-stream flows in two places; these can drift.
* In-place mutation in `Conversation#enforce_byte_cap!`
  (`app/models/conversation.rb:133`) mutates `Message#content` with `byteslice`,
  a surprising side effect on an otherwise value-oriented model.
* Dead code: `Conversation#history(messages)` (`conversation.rb:88-90`) is only
  referenced from its own test, `Conversation#empty?` (`conversation.rb:78-80`)
  and `ConversationRepository#prune_expired!` (`repository.rb:59-62`) are never
  called.
* `serialized_bytes` (`conversation.rb:136-138`) counts only role+content bytes,
  ignoring JSON framing, `created_at`, title and token columns, so the byte cap
  is approximate.

**Top 3 refactors with more time:**

1. Extract a `TurnService`/`AssistantTurn` orchestrator plus a `Stream` formatter
   out of `MessagesController`; leave the controller to route/respond. Reason:
   single-responsibility and testability of the streaming/error flow.
2. Consolidate the two budget/refusal paths into one method (or a small
   `TurnGate` object) shared by `create` and `stream`. Reason: removes the
   duplicated in-UI refusal logic that can drift.
3. Replace in-place `byteslice` truncation with an immutable bounded-message-list
   value object that returns new instances. Reason: removes a hidden mutation
   side effect and avoids splitting a multibyte UTF-8 codepoint.

## 3. Test Coverage Assessment

`bin/rails test` (re-run) → **Line 86.29% (340/394), Branch 72.00% (54/75)**;
51 runs, 127 assertions, 0 failures. Per-file branch coverage is lowest in the
controller and repository layers:

| File | Line | Branch |
| --- | --- | --- |
| `app/controllers/messages_controller.rb` | 86.0% (92/107) | 65.4% (17/26) |
| `app/models/conversation_repository.rb` | 90.0% (72/80) | 61.5% (8/13) |
| `app/services/chat_service.rb` | 100% (33/33) | 60.0% (6/10) |
| `app/services/title_generator.rb` | 94.4% (17/18) | 60.0% (3/5) |

Weakest-tested area: the **MessagesController SSE/streaming and error/recovery
paths** (65% branch) — the HTML-escape/target helpers, the rescue block, and the
unhappy stream branches are thin.

Failure modes **not** covered by any test:

* `stream` when the conversation is missing/expired at request time — the
  `unless @conversation && ...` branch renders `messages/form` with a nil
  conversation (`messages_controller.rb:57-61`), and the subsequent rescue
  retries the same nil render (`:68`).
* Concurrent double-submit / two SSE `stream` requests on the same conversation.
* True cross-process writer contention (`WEB_CONCURRENCY=2`) — only single-process
  multi-thread is tested (`conversation_repository_test.rb:91-102`).
* Provider failure during *title* generation — only the nil/blank-title path is
  unit-tested; the controller's `rescue StandardError` around `TitleGenerator`
  (`messages_controller.rb:126-131`) is untested.
* `Conversation#enforce_byte_cap!` single-message truncation branch
  (`@messages.first.content.byteslice`); the test only hits the multi-message
  `.shift` branch (`conversation_test.rb:32-37`).
* HTML (non-turbo) `format.html` redirect branches in `messages#create`.
* `ConversationRepository#prune_expired!`, `ConversationRepository#all`'s
  expired-row deletion, and the `expired?` boundary condition.
* End-to-end streaming / tool-calling against the real OpenRouter API (only
  stubbed/mocked).

## 4. Known Defects and Risks

1. **No `.dockerignore` + `COPY . .` ships secrets and junk into the image**
   (`Dockerfile:25`). A build at this workspace would copy `config/master.key`
   (which decrypts `config/credentials.yml.enc` → `secret_key_base`), the live
   `storage/conversations.sqlite3`, `log/development.log`/`log/test.log`,
   `coverage/`, and `tmp/cache/bootsnap`. The runtime volume shadows `storage`,
   but the key and logs remain baked into layers.
2. **Token-budget TOCTOU race.** `budget_exceeded?` is evaluated outside the
   append transaction (`messages_controller.rb:21,80`) and token totals are only
   persisted after the reply (`chat_service.rb:40-57`), so concurrent requests on
   one conversation can each pass the check and call the provider; a single turn
   can already overshoot by its own usage before refusal.
3. **Double-submit / duplicate SSE.** The button is disabled on
   `turbo:submit-start` (`messages/_form.html.erb:3`), which fires after a submit
   begins; a rapid double-click or duplicate `<turbo-stream-source>` connection
   can produce two pending user turns or process one turn twice. `history_before_new_turn`
   (`chat_service.rb:61-65`) pops only one pending message.
4. **Nil-conversation stream path is broken** (`messages_controller.rb:57-61`):
   renders the composer partial with `conversation: nil`, raising
   `NoMethodError`, then re-raises in the rescue when it emits the same replace
   (`:68`). Low likelihood (TTL is 86400s) but it aborts the SSE mid-response.
5. **Unbounded cost exposure.** No auth (intended, G14) but also no rate limit or
   per-IP/per-day cap; `ConversationsController#create` is unlimited and each new
   conversation resets a 20k-token budget, so an unauthenticated caller can burn
   OpenRouter credits indefinitely.
6. **Byte-cap truncation encoding risk.** `@messages.first.content.byteslice(0, max_bytes)`
   (`conversation.rb:133`) can split a multibyte UTF-8 codepoint, yielding an
   invalid-encoding string on replay; the "byte cap" also does not account for the
   serialized JSON/token/title columns.
7. **"Latest Claude Sonnet" is unverifiable from the workspace.** Default
   `anthropic/claude-sonnet-4.6` (`config.rb:11`) was chosen at build time; I
   could not confirm it is still the newest Sonnet at review time. Overridable via
   `LLM_MODEL`.
8. **`.mise.toml` (`ruby = "latest"`) conflicts with the README/.ruby-version
   claim of pinning `4.0.6`.** mise will install whatever "latest" resolves to,
   not necessarily 4.0.6 — a documentation/consistency mismatch.
9. **`ensure_schema!` runs on every repository instantiation** (i.e. every
   request): `PRAGMA journal_mode=WAL` + `CREATE TABLE IF NOT EXISTS` on a fresh
   connection (`repository.rb:102-117`). Harmless but wasteful, and the WAL
   pragma can transiently fail under concurrent startup and is ignored.

No fixes were required during this review; none were made.