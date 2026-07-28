# Self-Review — RubyLLM Chat

Phase 3 self-review of the workspace. Each goal was re-verified against the
actual code on 2026-07-27, not from memory. The commands actually run during
this review:

```
bundle exec rails test                       # 77 runs, 211 assertions, 0 failures, 0 errors; Line 96.27% (413/429)
bundle exec rubocop                          # 43 files, 0 offenses
bundle exec brakeman -q                      # 0 errors, 0 security warnings
bundle exec bundle-audit check --config config/bundler-audit.yml   # No vulnerabilities
```

Ruby 4.0.6 / Rails 8.1.3 (mise). `ruby_llm` 1.16.0. The RubyLLM API surface
used by this app was verified against the installed gem source (see G3/G11) —
the config setters, `Chat` methods, `Tool`/`Schema`/`Message`/`Chunk` and the
error classes are all real.

No code changes were made in this phase. The defects found are design-level
concurrency/operational risks (section 4); none is a clear-cut breakage in
normal use, and a concurrency change without a paired test would be riskier
than documenting it. They are recorded below for the next pass.

---

## 1. Goal Verification Table

| Goal | Verdict | Evidence |
|------|---------|----------|
| **G1** Rails app, newest Ruby/Rails from mise; no AR/Mailer/Job; at workspace root | **PASS** | `.ruby-version` = `ruby-4.0.6`; `Gemfile:5` `rails "~> 8.1.3"`; `config/application.rb:5-15` comments out `active_record`/`active_job`/`active_storage`/`action_mailer`/`action_mailbox`/`action_text` railties and keeps only `action_controller`/`action_view`/`action_cable`/`test_unit`. App sits at the workspace root (no nested `app/` dir). |
| **G2** ChatGPT-like SPA: Tailwind + Hotwire (Stimulus + Turbo Streams), partials, no fetch/innerHTML dumps | **PASS** | `Gemfile` pins `tailwindcss-rails`, `turbo-rails`, `stimulus-rails`. Views are componentized into partials (`messages/_message`, `messages/_form`, `messages/_error`, `conversations/_title`, `conversations/_conversation`). `show.html.erb:16` uses `turbo_stream_from`; `app/javascript/controllers/chat_controller.js` is a Stimulus controller that only uses a `MutationObserver` for auto-scroll — no `fetch()`/`innerHTML`. Tailwind is split into an input (`app/assets/tailwind/application.css`) and a build output (`app/assets/builds/tailwind.css`), not a single dump. |
| **G3** RubyLLM (`ruby_llm`, latest) for OpenRouter, latest Claude Sonnet, model env-overridable | **PASS** | `Gemfile` `gem "ruby_llm"` → `Gemfile.lock` resolves `ruby_llm 1.16.0`. `config/initializers/ruby_llm.rb:10-15` calls the **real** config setters `config.openrouter_api_key=` and `config.openai_use_system_role=` (verified: `ruby_llm-1.16.0/lib/ruby_llm/providers/openrouter.rb:18,53,57` reads `@config.openrouter_api_key`; `providers/openai.rb:44` registers `openai_use_system_role`; both setters accepted at runtime). `app/models/chat_config.rb:17` defaults to `anthropic/claude-sonnet-4.6`, overridable via `CHAT_MODEL`. |
| **G4** TRUE token streaming via Turbo Stream broadcasts (not a post-completion append) | **PASS** | `messages_controller.rb:52-59` calls `service.ask(...) do |accumulated, chunk|` and broadcasts each token *as it arrives* via `broadcast_streaming_update` (`:152-160`, `Turbo::StreamsChannel.broadcast_replace_to`) during the synchronous request — a transient streaming bubble is swapped in first (`:142-150`) and replaced by the final message only at the end (`:162-169`). `chat_service.rb:50-62` yields the accumulated text per chunk. `chat_service_test.rb:65-74` asserts the block receives `["Hel","Hello","Hello world"]` incrementally; `messages_controller_test.rb:66-88` asserts the fragments were streamed through the block. |
| **G5** Each user turn sent exactly once; replayed history excludes the prompt about to be sent; unit test asserts the exact outgoing array | **PASS** | `chat_service.rb:21-33` `build_chat` replays only prior messages via `add_message`, then `complete`/`ask` (`:50-62`) adds the new prompt — so it is sent once. `chat_service_test.rb:37-63` "the outgoing payload sends each user turn exactly once" asserts the exact role sequence `[system, user, assistant, user, assistant, user]` and that `"What is 2+2?"`, `"Hello"` and `"Do you know Ruby?"` each appear exactly once. The mock sits at the real `Chat#provider_completion` boundary (`test_helper.rb:102-111`), capturing `chat.messages.dup` as the real outgoing array. |
| **G6** Concurrency-safe, bounded persistence; restart survival; correct under WEB_CONCURRENCY=2 (no process-local store); message/byte caps + TTL | **PASS** (with a disclosed race — see Known Defects #1) | `ConversationStore` is file-backed JSON with no process-local cache (`conversation_store.rb`). Atomic writes via temp-file + `FileUtils.mv` (`:66-77`); per-conversation `flock` in `with_lock` (`:102-112`); TTL sweep (`:115-126`). Bounds enforced in `conversation.rb:141-166` (count + bytes); `expired?` at `:109-113`. Restart-survival test: `conversation_store_test.rb:16-25`; TTL test `:67-77`; lock-serialization test `:79-97`; atomic-read test `:99-119`. Cross-worker Cable broadcasting is wired with Redis: `config/cable.yml` (redis when `REDIS_URL` set) + `docker-compose.yml:48-49` `REDIS_URL`/`WEB_CONCURRENCY=2`. **Caveat:** the lock serializes critical sections but the conversation is read in a `before_action` *before* the lock is acquired, so two simultaneous POSTs to the *same* conversation can lose a message — see #1. |
| **G7** Exactly two tools via RubyLLM tool API: `server_time` (UTC) and `calculator` (safe arithmetic) | **PASS** | `app/models/server_time.rb` and `app/models/calculator.rb` both subclass `RubyLLM::Tool` using the real `description`/`param` DSL. `chat_service.rb:28` `chat.with_tools(ServerTime, Calculator)`. `tools_test.rb:62-66` asserts exactly `%i[server_time calculator]`; `:9-33` exercises `Calculator#call` and `:24-33` asserts the param schema via the real `Tool` API; `:35-60` covers `server_time` (UTC, IANA tz, unknown-tz fallback). Calculator never `eval`s — `safe_arithmetic.rb` is a hand-written recursive-descent parser with DoS guards (`MAX_EXPRESSION_LENGTH`, `MAX_EXPONENT`). |
| **G8** Structured-output title via RubyLLM schema API after the first completed exchange; shown in UI | **PASS** | `app/models/conversation_title_schema.rb` subclasses `RubyLLM::Schema`. `chat_service.rb:66-87` builds a chat with `.with_schema(ConversationTitleSchema)` and extracts the title. `messages_controller.rb:98-112` calls it after `needs_title?` (first completed exchange, `conversation.rb:101-103`) and broadcasts a `replace` of `#conversation_title`. `_title.html.erb` renders it; `show.html.erb:5-7` wraps the target. Tests: `chat_service_test.rb:89-128` (success + error-swallow), `conversation_title_schema_test.rb`, `messages_controller_test.rb:86` asserts the title is persisted. |
| **G9** Per-conversation token budgeting; configurable (env, sane default); refuse further turns with a friendly in-UI message instead of calling the provider | **PASS** | `chat_config.rb:41` `token_budget` default `50000` (`TOKEN_BUDGET`). `conversation.rb:84-99` tracks `tokens_used`/`budget_exceeded?`/`record_tokens`. `messages_controller.rb:116-129` refuses with a broadcast when exceeded *before* `service.ask`. `messages_controller_test.rb:48-62` asserts the provider is never called and a `/token budget/i` broadcast is emitted. **Caveat:** accounting depends on the provider returning `input_tokens`/`output_tokens` on a streamed final message — see #3. |
| **G10** System prompt via instructions API; missing-key preflight (friendly, actionable); every provider failure rescued into a visible degraded UI; failed turns never replayed | **PASS** | System prompt via `with_instructions` (`chat_service.rb:27`). Missing-key preflight broadcast (`messages_controller.rb:116-121`). Provider failures rescued (`:62-70`): `RubyLLM::ConfigurationError`/`RubyLLM::Error`, `Timeout::Error`/`Faraday::Error`, and a catch-all `StandardError`, each routing to `finalize_failure` (`:89-94`) which `rollback_last_turn!`s and broadcasts a degraded error bubble. Failed turns excluded from replay by `replayable_messages` (`conversation.rb:45-47`). Tests: missing key (`messages_controller_test.rb:28-44`), provider failure rollback (`:92-112`). |
| **G11** Minitest tests for every component; mocks mirror the real RubyLLM API; error paths covered; SimpleCov wired with a report | **PASS** | `test_helper.rb:6-18` starts SimpleCov (Rails profile, 80% floor). Mocks stub the real `Chat#provider_completion` private boundary and return real `RubyLLM::Message`/`RubyLLM::Chunk` objects (`test_helper.rb:81-111`) — not a fake API. 77 tests, 0 failures. Error paths covered: missing key, budget exceeded, provider failure, blank message, corrupt store file, division by zero, malicious calculator input, unknown timezone. **Caveat:** branch coverage is not enabled and several rescue arms are unexercised — see section 3. |
| **G12** Brakeman, RuboCop, bundle-audit all pass clean | **PASS** | Re-run this phase: `rubocop` → "43 files inspected, no offenses detected"; `brakeman` → "Errors: 0, Security Warnings: 0"; `bundle-audit check --config config/bundler-audit.yml` → "No vulnerabilities found". |
| **G13** Production-grade Dockerfile (RAILS_ENV=production, non-root, entrypoint) + docker compose that runs locally; README | **PASS** | `Dockerfile`: multi-stage, `ENV RAILS_ENV="production"` (`:24`), non-root user uid 1000 (`:64-66`), `ENTRYPOINT ["/rails/bin/docker-entrypoint"]` (`:73`), jemalloc, `BUNDLE_WITHOUT="development"`. `bin/docker-entrypoint` generates `SECRET_KEY_BASE` at runtime (never baked). `docker-compose.yml`: `redis` + `web` (`RAILS_ENV=production`, `WEB_CONCURRENCY=2`, `REDIS_URL`, requires `OPENROUTER_API_KEY`). `README.md` documents features, env vars, local + Docker run. (Phase 2 logged `docker build succeeds` and `docker compose up --build runs end-to-end chat`; not re-run in phase 3.) |
| **G14** No auth (demo); no secrets committed; everything inside the workspace | **PASS** | No auth code/routes (`routes.rb` has only `conversations`/`messages`). `.gitignore` ignores `/config/master.key` and `/.env*` (keeps `!.env.example`); `.dockerignore` mirrors this. A repo-wide scan for `OPENROUTER_API_KEY` found only the empty placeholder in `.env.example`, the `${OPENROUTER_API_KEY}` compose reference, a `"sk-or-..."` README example, and a `"sk-or-test"` test fixture — never a real key value. `credentials.yml.enc` is the encrypted blob (not a secret). |

**Summary: 14/14 PASS**, with three disclosed caveats attached to G6, G9 and G11.
The caveats are expanded in section 4; they are real but do not violate the
letter of the stated goals under normal (single-user, sequential) operation.

---

## 2. Code Quality Assessment

Overall the code is clean, consistently styled (omakase RuboCop, 0 offenses),
well-commented with intent, and tightly scoped. A few honest observations:

**Naming / readability — good.** Method names are intention-revealing
(`replayable_messages`, `rollback_last_turn!`, `needs_title?`,
`broadcast_streaming_update`). The `ChatConfig` module centralizes every tunable
behind a single source of truth read by controllers, services and tests alike
(`app/models/chat_config.rb`).

**Single responsibility — mostly good, one outlier.** `app/models/conversation.rb`
(171 lines) and `conversation_store.rb` (141 lines) are well-factored. The
weakness is `app/controllers/messages_controller.rb` (**225 lines**) which owns
loading, preflight, four distinct Turbo broadcast shapes, the streaming loop,
success/finalize, failure/rollback, and title generation. It is doing both HTTP
concerns *and* exchange orchestration. Logic that belongs in a service object
lives in the controller, which is why it is only tested through integration tests
with a `FakeChatService` rather than in isolation.

**Duplication — minor.** The streaming placeholder/swap/error broadcasts in
`messages_controller.rb` (`broadcast_append_streaming_placeholder`,
`broadcast_streaming_update`, `broadcast_swap`, `broadcast_error`) each
re-construct a throwaway `Message.new(...)` and call
`Turbo::StreamsChannel.broadcast_replace_to`/`_append_to` with near-identical
arguments. `bubble_classes` (`messages_helper.rb`) and the streaming/error flags
in `_message.html.erb` overlap conceptually. Acceptable for a demo; a small
`TurboBroadcaster` helper would remove the repetition.

**Dead code — essentially none.** `app/javascript/controllers/hello_controller.rb`
is the Stimulus scaffold default and is unused (no `data-controller="hello"` in
any view). `app/views/pwa/*` are PWA scaffold defaults. Cosmetic only.

**Method/class size — acceptable.** Longest methods: `SafeArithmetic#parse_base`
(~16 lines) and `Conversation#enforce_bounds!` callers are fine. No god-methods.
`MessagesController` is the only oversized class.

**Coupling — reasonable, one leak.** `Conversation` (a plain ActiveModel
aggregate) reaches into `ChatConfig` for bounds/TTL/budget
(`conversation.rb:88,93,112,147,158`). That makes `Conversation` non-reusable
outside this app's config and means unit tests must stub `ChatConfig`. A cleaner
design passes bounds in at construction. `ChatService` is otherwise cleanly
decoupled (it depends on `ChatConfig` and the two tool classes only).

**Top 3 things I would refactor with more time:**

1. **Extract exchange orchestration out of `MessagesController` into a
   `ChatExchangeService`** (preflight → stream → finalize/rollback → title).
   The controller should stay an HTTP adapter. This also makes the
   same-conversation race (#1) fixable in one place and testable without HTTP.
2. **Close the `Conversation` ↔ `ChatConfig` coupling** by injecting bounds/TTL
   at construction (or via a small `Limits` value object), so `Conversation` is a
   pure aggregate and its tests need no config stubs. Passes the dependency
   inward instead of reaching outward.
3. **Consolidate the four Turbo-broadcast helpers** in `messages_controller.rb`
   behind one `TurboBroadcaster` that takes `(conversation, target, message,
   state:)`, removing the duplicated `Message.new(...)` scaffolding and the
   repeated `broadcast_*_to` calls.

---

## 3. Test Coverage Assessment

Actual numbers from a fresh suite run this phase:

- **Line coverage: 96.27%** (`413 / 429` lines), reported by SimpleCov to
  `coverage/.last_run.json` and `coverage/index.html`.
- **Branch coverage: not measured.** `test_helper.rb:6-18` starts SimpleCov with
  the Rails profile and `minimum_coverage 80` (line) plus a per-file line floor,
  but **does not enable branch coverage** (`enable_for_branch_coverage` /
  `coverage(:branch) { … }` is absent). So the headline 96% is line-only; no
  branch percentage exists. This is itself a gap — several conditional branches
  are unexercised and invisible to the gate.

77 runs, 211 assertions, 0 failures, 0 errors, 0 skips. Parallelized across 32
processes.

**Weakest-tested area:** `MessagesController#perform_exchange`'s rescue ladder
(`messages_controller.rb:62-70`). Only the `RubyLLM::Error` arm is hit (via the
`RubyLLM::RateLimitError` provider-failure test). The `Timeout::Error` /
`Faraday::Error` arm and the catch-all `StandardError` arm are **not exercised by
any test**. Likewise the "unexpected" log path (`:67-69`) is unreached.

**Failure modes NOT covered by any test:**

- Network/timeout failure (`Faraday::Error`, `Timeout::Error`) rescue arm — no
  test injects a Faraday/timeout error.
- The catch-all `StandardError` rescue and its `Rails.logger.error` branch.
- **The RubyLLM tool-execution loop at runtime.** `tools_test.rb` calls
  `Tool#call` directly, but no test stubs a provider response containing a
  `tool_call` to prove the model→tool→model round-trip works end-to-end through
  `ChatService`. The tools are wired and individually correct, but the loop that
  invokes them is untested.
- **The same-conversation concurrency race** (#1) — no test posts to one
  conversation concurrently.
- `ChatService#extract_title`'s `String` branch (`chat_service.rb:94`) — only the
  `Hash` path is covered; a provider that returns a bare string title is not
  tested.
- Token accounting when a provider omits usage on a streamed response (#3) — no
  test for the `tokens_used`-stays-zero path.
- No **system/browser test** asserts the Turbo Stream actually renders
  incrementally in the DOM. Tests assert that *broadcasts* were emitted to the
  Action Cable channel (`assert broadcasts_for(...).any?(/…/)`), not that a
  browser would paint them. `capybara`/`selenium-webdriver` are in the Gemfile
  test group but no system test exists under `test/`.
- Branch coverage generally (unmeasured).

---

## 4. Known Defects and Risks

1. **Lost-update race on concurrent posts to the *same* conversation (G6).**
   `MessagesController#load_conversation` (a `before_action`,
   `messages_controller.rb:209-214`) reads `@conversation` from the store
   *before* `ConversationStore.with_lock(@conversation.id)` is acquired in
   `create` (`:21-24`). The `flock` serializes the critical sections, but it does
   **not** reload the conversation inside the lock. Two workers posting to the
   same conversation simultaneously each hold a snapshot taken before locking;
   the second worker's `save` overwrites the first's, dropping the first user
   message. Narrow in practice (a single-user chat doesn't post concurrently to
   one conversation) but a genuine correctness hole under WEB_CONCURRENCY>1.
   **Fix:** reload `@conversation` inside `with_lock` (or move the read inside
   the lock). Not patched this phase — a concurrency change belongs with a
   concurrent test, which is out of scope for review-only.

2. **Streaming blocks a Puma thread for the entire LLM reply (operational).**
   `MessagesController#create` runs `service.ask` to completion *within* the HTTP
   request, broadcasting tokens as they arrive. A long or stalled reply holds the
   worker/thread for up to `request_timeout` (ruby_llm default 300s). With
   `WEB_CONCURRENCY=2` and modest thread counts, a few slow/simultaneous chats
   can starve the server. There is deliberately no Active Job (G1 forbids it), so
   a proper async background streamer is non-trivial. This is the main
   scalability ceiling.

3. **Token accounting depends on the provider returning usage on streamed
   responses (G9).** `finalize_success` reads `response.input_tokens` /
   `response.output_tokens` (`messages_controller.rb:72-80`). Some OpenRouter
   upstreams omit usage on stream chunks; in that case `tokens_used` stays 0 and
   the budget never trips, silently disabling the G9 guard. No fallback
   tokenizer. Claude/OpenRouter currently returns usage, so it works today, but
   it is model-dependent and unverified for arbitrary `CHAT_MODEL` values.

4. **`ConversationStore.sweep_expired!` is O(n) per request and parses every
   file.** It runs on every `find`, `save`, `recent` and on `index`
   (`conversation_store.rb:44,74,89,115-126`), iterating all `.json` files and
   `JSON.parse`-ing each to test the TTL. `recent` (`:86-96`) likewise parses
   every file. Fine for a demo; a busy store would make every request scan and
   parse the whole directory. No mtime pre-filter, no index, and no background
   sweep (Active Job is disallowed by G1).

5. **`generate_title_if_needed` makes a second synchronous provider call inside
   the user's first-exchange request** (`messages_controller.rb:98-112`). It is
   rescued (returns `nil` on failure), but it adds wall-clock latency and another
   failure/timeout surface to the user's turn. A user posting the first message
   waits for both the reply and the title generation.

6. **No size cap on the inbound `message[:content]` param.** Only the
   per-conversation byte cap (`MAX_CONVERSATION_BYTES`) bounds total storage, and
   it is enforced *after* the message is read into memory and appended
   (`conversation.rb:57-63` → `enforce_bounds!`). A single very large POST is
   fully materialized first. Minor DoS surface; a `maxlength`/server-side length
   guard would close it.

7. **Conversation streams are subscribable by id-guessing.** `turbo_stream_from`
   uses a plain string channel derived from the conversation id
   (`application_controller.rb:9-11`). Anyone who guesses/discovers a uuid can
   subscribe to its live token stream and read replies. Acceptable for an
   explicit no-auth demo (G14), but worth stating plainly: conversations are not
   private.

8. **`completed_exchanges` counting is slice-fragile** (`conversation.rb:51-55`).
   It counts non-error user/assistant messages in strict pairs. If history ever
   becomes unbalanced (e.g. two user messages in a row after a rollback that left
   a dangling assistant gap, or trimming that split a pair via `enforce_bounds!`
   dropping the oldest), `needs_title?` could fire at the wrong time or not at
   all. Not observed failing, but the invariant ("messages always alternate
   user/assistant") is not enforced or asserted.

9. **Branch coverage is not enabled** (see section 3) — the 96.27% figure is
   line-only, so the rescue-ladder and several conditional branches are
   effectively unguarded by the coverage gate.

10. **Unused scaffold:** `app/javascript/controllers/hello_controller.js` and
    `app/views/pwa/*` are Rails/Stimulus defaults with no references. Dead weight
    only.

No security findings: Brakeman reports 0 warnings, bundle-audit 0 CVEs, and no
secrets are committed (verified by scan).
