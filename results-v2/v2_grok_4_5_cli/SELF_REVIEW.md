# SELF_REVIEW — Phase 3

Evidence gathered 2026-07-30 against the live tree at workspace root. Commands re-run in this phase; phase-2 runtime proofs cited where re-running live LLM calls was unnecessary.

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence |
|------|---------|----------|
| G1 | **PASS** | `ruby -v` → `ruby 4.0.6`; `bundle exec rails -v` → `Rails 8.1.3.1`; `.ruby-version` = `ruby-4.0.6`; `config/application.rb` loads only `active_model`, `action_controller`, `action_view`, `action_cable`, `rails/test_unit` (no Active Record / Active Job / Action Mailer railties); app lives at workspace root (no nested app dir); no `config/database.yml`. |
| G2 | **PASS** | Tailwind via `tailwindcss-rails` + `app/assets/builds/tailwind.css`; Hotwire: `turbo-rails`/`stimulus-rails`, `turbo_stream_from` in `app/views/chats/show.html.erb:3`, Stimulus controllers under `app/javascript/controllers/{chat,composer,scroll}_controller.js`; UI split into partials `_composer`, `_message`, `_title`, `_token_usage`, `_empty_state`, `_error` — no fetch/innerHTML chat path. |
| G3 | **PASS** | `Gemfile`/`Gemfile.lock`: `ruby_llm (1.16.0)`; `config/initializers/ruby_llm.rb` sets `config.openrouter_api_key` + default model `anthropic/claude-sonnet-4.6`; `ChatService#build_chat` uses `RubyLLM.chat(model:, provider: :openrouter, assume_model_exists: true)`; model overridable via `CHAT_MODEL` (`config/application.rb:25`). |
| G4 | **PASS** | Implementation: `ChatService#broadcast_token` → `Turbo::StreamsChannel.broadcast_append_to(..., target: "#{assistant_id}-content", html: ...)` (`app/services/chat_service.rb:224-230`); unit test `call streams chunks via turbo and stores final assistant message` asserts ≥3 HTML token appends. Phase-2 proof: ActionCable Redis pub/sub showed distinct APPEND events at ~0ms (user+placeholder), ~3050ms (`alpha`), ~3130ms (` beta gamma…`), then replace-complete — not one post-completion append. |
| G5 | **PASS** | History captured before persist (`chat_service.rb:57-62`); seed excludes new user; `ask` sends it once (`stream_completion!` lines 111-121). Tests: `build_outgoing_messages excludes the new prompt from history and appends it once`, `outgoing_messages_for uses conversation history without the pending user turn`, `multi-turn exact outgoing message array assertion` in `test/services/chat_service_test.rb`. |
| G6 | **PASS** | `Conversation` Redis keys `chat:conversation:<id>:{meta,messages}` with `expire` TTL, `lpop` message-count + byte caps (`app/models/conversation.rb:170-186`); `ConnectionPool::Wrapper` in `config/initializers/redis.rb`. Tests: message/byte bounds, restart simulation across instances. Phase-2: `WEB_CONCURRENCY=2`, marker `UNIQUE_MARKER_G6_1887cc52` survived kill/restart; page + multi-turn recall intact. |
| G7 | **PASS** | Exactly two tools: `ServerTimeTool` (`name` → `server_time`), `CalculatorTool` (`name` → `calculator`); registered in `ChatService#build_chat` via `with_tools(ServerTimeTool, CalculatorTool)`. Unit tests for both tools + RubyLLM `#call` API. Phase-2: time answer matched server ISO window; `(123+456)*7-89` → 3964; `2**10 + 5**4` → 1649. |
| G8 | **PASS** | `ConversationTitleSchema < RubyLLM::Schema` with `string :title`; `maybe_generate_title!` after first exchange (`message_count >= 2`, title blank) uses `chat.with_schema(ConversationTitleSchema)`; UI `render "chats/title"` + `broadcast_title`. Test: `generates title after first exchange using schema API`. Phase-2 stored clean title e.g. `"Code Word Acknowledgment"`. |
| G9 | **PASS** | `TOKEN_BUDGET` default 100000 (`config/application.rb:24`); `Conversation#budget_exceeded?`; `ChatService#call` raises `BudgetExceededError` before provider; controller renders friendly turbo error + disables composer (`messages_controller.rb:39-48`, `_composer` placeholder when disabled). Tests: service + controller budget paths. |
| G10 | **PASS** | System prompt via `chat.with_instructions(SYSTEM_PROMPT.call)` (`chat_service.rb:149`); `preflight!` on empty `OPENROUTER_API_KEY` → `MissingApiKeyError` with actionable text; provider errors → `broadcast_error` + `ProviderError`; persist only after successful stream (`append_message!` after `stream_completion!`). Tests: missing key (0 messages stored), `failed provider call does not store assistant message`. |
| G11 | **PARTIAL** | 43 runs / 98 assertions / 0 failures (`bundle exec rails test`). Coverage: SimpleCov line **92.62%** (364/393); **branch coverage not enabled** (`coverage.json` meta `branch_coverage: false`). Components under test: Conversation, ChatService, TokenEstimator, both tools, schema, both controllers. Gaps: `MessagesController` `ProviderError` + `NotFoundError` paths untested (missed lines 61–73); several `ChatService#parse_title` / title-failure branches untested; no view/JS/system tests; calculator error/edge branches partially uncovered. Mocks use real surface (`chat`, `with_instructions`, `with_tools`, `add_message`, `ask`, `with_schema`). |
| G12 | **PASS** | Re-run this phase: `bundle exec rubocop` → 38 files, 0 offenses; `bundle exec brakeman -q -w2` → 0 warnings; `bundle exec bundler-audit check` → no vulnerabilities. |
| G13 | **PASS** | `Dockerfile`: multi-stage, `RAILS_ENV=production`, `USER 1000:1000`, `ENTRYPOINT bin/docker-entrypoint`, bootsnap + assets precompile. `docker-compose.yml`: redis + web, `WEB_CONCURRENCY=2`, healthchecks. `README.md` documents purpose, setup, env vars, tests, security tooling. Phase-2: `docker build` exit 0; `docker compose up --build` healthy and answered a real chat (`compose-e2e-ok`). Compose still healthy at review time (`docker compose ps`). |
| G14 | **PASS** | No auth layer in controllers/routes. Secrets not hardcoded: `OPENROUTER_API_KEY` from ENV only; `.gitignore` includes `.env*`, `config/master.key`, `coverage/`. `config/master.key` present on disk but ignored by git. Compose uses `${OPENROUTER_API_KEY:-}` and a clearly non-production `SECRET_KEY_BASE` default placeholder (not a live credential). Everything under workspace root. |

## 2. CODE QUALITY ASSESSMENT

**What works**

- Clear layering: controllers stay thin; `ChatService` owns provider/streaming/broadcasts; `Conversation` owns Redis persistence; tools/schema are isolated.
- Naming is mostly intention-revealing (`history_for_provider`, `build_outgoing_messages`, `budget_exceeded?`, `enforce_bounds!`).
- Calculator avoids `Kernel#eval` with a hand-rolled parser + Ripper guard — appropriate for a demo tool.
- Frozen string literals and small, focused files for tools/schema/token estimator.

**Problems**

- **`ChatService` is a god object** (`app/services/chat_service.rb`, ~280 lines): streaming, Turbo broadcasts, title generation/parsing, preflight, error mapping, and token accounting live in one class. Broadcast helpers alone are ~70 lines of private methods.
- **Duplicated mock chat construction** across `test/services/chat_service_test.rb` and `test/controllers/messages_controller_test.rb` (ad-hoc `Object.new` + `define_singleton_method` instead of a shared test double).
- **Dead / unused API**: `Conversation.find_or_create` (`conversation.rb:39-45`) has no callers in `app/` or `test/`; `Conversation#to_h` untested/unused; empty junk file `=7` at repo root.
- **RMW races on meta** (`token_usage=`, `add_tokens`, `title=`): each does get→mutate→set without `MULTI`/`WATCH`/`INCR`. Safe enough for single-tab demos; wrong under concurrent turns on the same conversation id.
- **`enforce_bounds!` byte path** loads the full list with `LRANGE 0 -1` on every append — O(n) memory/CPU per message.
- **Controller duplication**: four near-identical `respond_to` turbo_stream/html blocks in `MessagesController#create`.
- **Coupling**: `ChatService` hard-depends on `Turbo::StreamsChannel`, ERB escape, concrete tool classes, and `Conversation` — hard to reuse outside Rails/request cycle (and streaming holds the Puma thread for the full LLM call).

**Top 3 refactors with more time**

1. **Split `ChatService`** into `CompletionStreamer` (provider + chunk callbacks), `ChatBroadcaster` (Turbo), and `TitleGenerator` — single responsibility and thinner tests per unit.
2. **Atomic Redis updates** for meta (`INCRBY` for tokens; Lua or `WATCH` for title/bounds) and a per-conversation lock (or queue) so two in-flight turns cannot interleave history.
3. **Extract a test `FakeRubyLLMChat`** supporting scripted chunks/errors/tools/schema, shared by service and controller tests — reduces brittle singleton redefinitions and better documents the real API surface.

## 3. TEST COVERAGE ASSESSMENT

**SimpleCov (re-run: `bundle exec rails test`)**

| Metric | Value |
|--------|--------|
| Line coverage | **92.62%** (364 covered / 393 relevant lines) |
| Branch coverage | **Not enabled** (`meta.branch_coverage: false` in `coverage/coverage.json`; no branch % available) |
| Suite | 43 runs, 98 assertions, 0 failures, 0 errors |

**By group (line %)**

| Group | Line % |
|-------|--------|
| Schemas | 100% |
| Helpers | 100% |
| Models | 95.0% |
| Services | 93.4% |
| Tools | 90.9% |
| Controllers | 88.4% |

**Weakest-tested area**

- `app/controllers/messages_controller.rb` (~82.8% lines): `ProviderError` rescue (lines 61–69) and `Conversation::NotFoundError` (line 73) never exercised.
- Secondary: `ChatService#parse_title` Hash / Hash#inspect fallbacks and title-generation failure warn path; calculator branches for `%`, unary `+`/`-`, generic rescue, and reject-call AST paths.

**Failure modes NOT covered by any test**

- Provider failure **after** partial token broadcasts (orphaned streaming placeholder + error toast).
- Mid-stream client disconnect / Puma timeout while `service.call` still blocks.
- Concurrent double-submit on the same conversation (interleaved `append_message!` / lost `token_usage` updates).
- Redis down / connection errors on read or write.
- ActionCable/WebSocket subscriber absent (broadcasts succeed server-side; UI stays empty until full page reload — reload does show persisted history only after success).
- Calculator: division by zero (`Infinity`), huge `**` exponents, malformed floats.
- Title generation returning empty/invalid schema payload (UI keeps “New chat”).
- HTML/`turbo_stream` format fallbacks on several controller branches.
- End-to-end tool-call path through `ChatService` with a mocked provider tool round-trip (tools tested in isolation only).
- Docker/compose and multi-worker behavior (validated manually in phase 2, not in Minitest).
- JavaScript Stimulus controllers (composer enter-to-send, scroll pinning).

## 4. KNOWN DEFECTS AND RISKS

1. **Orphaned streaming assistant bubble on provider error** — `broadcast_assistant_placeholder` runs before `stream_completion!`; on raise, code `broadcast_error` but never removes/replaces the placeholder (`chat_service.rb:67-91`). User sees an empty pulsing assistant message plus a separate error partial. Failed content is correctly omitted from Redis history.

2. **Optimistic user bubble vs history** — user message is broadcast before provider success but only persisted after success. On failure the UI shows a user message that will disappear on refresh and is not replayed — consistent with G10, confusing UX.

3. **Request-thread blocking stream** — entire LLM stream runs inside the `messages#create` request (`MessagesController` → `service.call`). With compose defaults `WEB_CONCURRENCY=2`, `RAILS_MAX_THREADS=3`, ~6 concurrent chats saturate workers; long OpenRouter latency ties up Puma threads. No job/queue offload (Active Job intentionally absent).

4. **Non-atomic conversation meta** — `add_tokens` / `title=` / `token_usage=` are read-modify-write without Redis transactions; concurrent turns on one id can lose increments or titles. `append_message!` + `enforce_bounds!` is similarly racy (two writers can briefly exceed caps).

5. **Byte-cap enforcement cost** — each append may `LRANGE` the full message list to sum bytes (`conversation.rb:180-185`); large caps → CPU/memory spikes.

6. **Calculator resource risk** — expressions like `9**9**9` (right-assoc power) can allocate huge Bignums or hang the worker; no timeout/complexity limit beyond character class checks.

7. **Action Cable CSRF disabled** — `config.action_cable.disable_request_forgery_protection = true` in development and production; `allowed_request_origins` is a wide `http(s)://*` regex in production. Acceptable for a no-auth demo; unsafe if exposed on a shared network without a reverse-proxy origin lock.

8. **No authentication / open write** — any client who learns (or guesses) a conversation UUID can read/append that thread. UUIDs are 122-bit random — fine for demo, not multi-tenant safe. No rate limiting on `messages#create` → cost amplification against OpenRouter.

9. **Compose `SECRET_KEY_BASE` default** — hardcoded placeholder in `docker-compose.yml` if env unset. Fine for local demo; must be overridden for any shared deployment.

10. **Token budget is approximate and post-hoc** — `TokenEstimator` uses ~4 chars/token and counts only user+assistant text after the turn (not system prompt, tools, or provider usage). Budget can be exceeded mid-turn; check is only at turn start. Tool-heavy turns under-counted.

11. **Title path extra LLM call** — failure is swallowed (`maybe_generate_title!` rescue log); success depends on schema/JSON parsing heuristics. Phase-2 needed a parse fix for Hash-shaped structured output — residual risk if provider returns a new shape.

12. **Repo hygiene** — empty stray file `=7` at root; `log/*.log` and local puma validation logs present on disk (gitignored via `/log/*` but noisy in workspace); `Conversation.find_or_create` dead code.

13. **Branch coverage dark** — SimpleCov started without `enable_coverage :branch`, so untested conditionals are invisible in the headline 92.62% figure.

14. **Redis DB assumptions** — test forces DB 15; cable uses DB 1 by default URL path; app data DB 0. Mis-set `REDIS_URL` without a DB path can collate concerns; initializer rewrites test URL only when not `REDIS_TEST_URL`.

### Fixes made during this review

None. No surgical code changes in phase 3; defects above are documented only.

### Commands re-run (this phase)

```text
redis-cli ping                          → PONG
ruby -v                                 → ruby 4.0.6
bundle exec rails -v                    → Rails 8.1.3.1
bundle exec rails test                  → 43 runs, 98 assertions, 0 failures; line 92.62%
bundle exec rubocop                     → 0 offenses
bundle exec brakeman -q -w2             → 0 warnings
bundle exec bundler-audit check         → No vulnerabilities found
docker compose ps                       → web + redis healthy on :3000
```
