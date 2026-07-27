# Self-Review — Phase 3

Date: 2026-07-26. Every verdict below was re-verified against the actual code and
a live running instance during this review — not from memory of phases 1–2.

How live evidence was obtained: the phase-2 compose stack (`chat-demo-web-1`,
`WEB_CONCURRENCY=2`, exposed on `http://localhost:3102`) was still running. I
wrote `tmp/stream_check.py` (validation tooling only, in gitignored `tmp/`) that
subscribes to the page's `Turbo::StreamsChannel` over the Action Cable
websocket, POSTs a message, and counts incremental append broadcasts vs. the
final replace. No application code was modified during this review.

## 1. Goal verification table

| Goal | Verdict | Evidence |
| --- | --- | --- |
| G1 | PASS | `config/application.rb:5-15` requires only active_model, action_controller, action_view, action_cable, test_unit railties — no Active Record / Action Mailer / Active Job. `mise.toml` pins Ruby 4.0.6 (`ruby -v` confirms). `Gemfile.lock` has `rails (8.1.3)`; `curl https://rubygems.org/api/v1/versions/rails/latest.json` returns `8.1.3`, i.e. newest. App lives at workspace root (no nested directory). |
| G2 | PASS | Tailwind via `tailwindcss-rails` (Gemfile), Hotwire via `turbo-rails` + `stimulus-rails` + importmap. Views are componentized partials: `app/views/conversations/_{sidebar,sidebar_item,header,title,composer,empty_state}.html.erb`, `app/views/messages/_{message,assistant_placeholder,error,budget_notice,setup_error}.html.erb`. JS is two small Stimulus controllers (`chat_scroll_controller.js` 23 lines, `composer_controller.js` 25 lines). `grep -rn 'fetch(\|innerHTML' app/javascript app/views` → no matches. |
| G3 | PARTIAL | `ruby_llm (1.16.0)` in `Gemfile.lock` — matches the latest release on the project's GitHub releases page. OpenRouter configured in `config/initializers/ruby_llm.rb:6-9`; model overridable via `CHAT_MODEL` (`lib/chat_config.rb:8-10`). **But** the default `anthropic/claude-sonnet-4.5` is no longer the latest Claude Sonnet: Sonnet 4.6 exists and Sonnet 5 shipped 2026-06-30 (per public Anthropic line-up trackers as of July 2026). The goal's "latest Claude Sonnet" is stale; the plumbing is correct and the override works. |
| G4 | PASS | Server side: `app/services/chat_service.rb:37-43` broadcasts each chunk via `Turbo::StreamsChannel.broadcast_append_to` as it arrives (`broadcast_chunk`, line 110). Live proof: `tmp/venv/bin/python tmp/stream_check.py http://localhost:3102 "…three-sentence story…"` → **30 incremental `action="append"` broadcasts between t=2.77s and t=4.3s, then the final `action="replace"` at t=4.36s**. Not a post-completion append. Test: `chat_service_test.rb:81` ("streams every chunk over Turbo Stream…"). |
| G5 | PASS | `chat_service.rb:33-37` replays only stored history (`@store.messages`) via `add_message`, then sends the current prompt once via `chat.ask`. Exact-array test: `chat_service_test.rb:29-52` asserts seeded history `[[:user,"first question"],[:assistant,"first answer"]]`, `asked_messages == ["second question"]`, and the full outgoing array. Suite: 0 failures. |
| G6 | PASS | Redis-backed store with atomic Lua append (`app/services/conversation_store.rb:18-41`) doing RPUSH + count trim + byte trim + EXPIRE in one call. Caps/TTL tests: `conversation_store_test.rb:22` (count cap), `:32` (byte cap), `:43` (sliding TTL). Live proof: compose container runs `WEB_CONCURRENCY=2` (verified via `docker inspect`); after 3 turns I ran `docker restart chat-demo-web-1` and the full history rendered intact from Redis afterwards. |
| G7 | PASS | Exactly two tools: `ChatService::TOOLS = [ServerTimeTool, CalculatorTool]` (`chat_service.rb:16`); test `chat_service_test.rb:66` asserts both and `TOOLS.length == 2`. Live proof: asked "what time is it on the server?" → reply "21:07:06 UTC on July 26, 2026" (matched `date -u` seconds later); asked to compute `(12.5 * 4) / 2 + 7` → "The result is 32.0" (correct). `docker logs chat-demo-web-1` shows `[Tool] server_time called` and `[Tool] calculator called with expression="(12.5 * 4) / 2 + 7"`. Calculator is a hand-rolled parser (`app/services/arithmetic_evaluator.rb`), no `eval`. |
| G8 | PASS | Schema: `app/schemas/conversation_title_schema.rb` (`RubyLLM::Schema`); titler uses `.with_schema(...)` (`app/services/conversation_titler.rb:13`); triggered only when `history.empty?` (`chat_service.rb:54`). Live proof: after the first exchange the page's `conversation_title` element and the sidebar both rendered the generated title "Lighthouse Keeper Retires After Forty Years". Test: `chat_service_test.rb:97` and `:104`. |
| G9 | PASS | `app/services/token_budget.rb` keeps a Redis counter per conversation (uses real provider token counts, chars/4 + 500/turn estimate fallback). Refusal path: `messages_controller.rb:16-21` renders `messages/_budget_notice` and never instantiates `ChatService`. Test: `messages_controller_test.rb:28` asserts the notice, that the service was not called, and that nothing was stored. Budget configurable via `CHAT_TOKEN_BUDGET`, default 8000 (`lib/chat_config.rb:17-19`). |
| G10 | PASS | System prompt via `with_instructions` (`chat_service.rb:67`; test `chat_service_test.rb:74`). Missing-key preflight: `application_controller.rb:15-17` + `messages/_setup_error.html.erb` naming `OPENROUTER_API_KEY`; test `messages_controller_test.rb:14`. Provider failures rescued into a broadcast error partial (`chat_service.rb:56-61`, `messages/_error.html.erb`); tests cover `RubyLLM::ServerError`, `RateLimitError`, and generic `StandardError`, each asserting the store stays empty (`chat_service_test.rb:116-146`). |
| G11 | PASS | 53 tests / 145 assertions, 0 failures, 0 errors (`bin/rails test`). Test files exist for every component: 5 service tests, 2 tool tests, 2 controller tests. Error paths covered (see G10 + evaluator error tests). SimpleCov wired with branch coverage in `test/test_helper.rb:3-7`. Doubles use real `RubyLLM::Chunk`/`RubyLLM::Message` value objects and mirror the 1.16 API (`with_instructions`, `with_tools`, `with_schema`, `add_message`, streaming `ask`) — `test/test_helper.rb:34-101`. |
| G12 | PASS | `bin/rubocop` → "42 files inspected, no offenses detected". `bin/brakeman -q` → "Security Warnings: 0". `bin/bundler-audit check` → "No vulnerabilities found". All run during this review. |
| G13 | PASS | `Dockerfile`: multi-stage, `RAILS_ENV=production`, jemalloc, non-root `USER 1000:1000`, `ENTRYPOINT ["/rails/bin/docker-entrypoint"]`, dummy-secret asset precompile. `docker-compose.yml`: redis with healthcheck + persistent volume, web with healthcheck, secrets injected from env only. Live proof: the compose stack built in phase 2 (`chat-demo-web:latest`, 407MB) is running and answered real chat messages end-to-end during this review. `README.md` documents features, setup, env vars, tests, Docker. |
| G14 | PASS | No authentication code anywhere (per the brief's intent). No secrets in any source file: `config/master.key` exists on disk but is git- and docker-ignored; compose reads `OPENROUTER_API_KEY`/`SECRET_KEY_BASE` from the environment with `:?` guards; README shows placeholders only. Everything is inside the workspace. Caveat: the git repo has **zero commits** (`git ls-files` is empty), so "nothing committed" is trivially true — see Risks. |

Score: 13 PASS, 1 PARTIAL (G3), 0 FAIL.

## 2. Code quality assessment

Overall the code is in good shape: classes are small (largest is `ChatService`
at 136 lines), names are accurate, comments explain *why* (e.g. the Lua script,
the token-estimate constants), and layering is clean — controllers are thin,
all provider interaction is in services, all Redis access is in
`ConversationStore`/`TokenBudget`/`RedisConnection`.

Specific observations:

- **Naming**: consistently good (`exceeded?`, `record_turn`, `spawn_turn`,
  `fail_turn`). No misleading names found.
- **Single responsibility**: mostly respected. `ChatService` mixes turn
  orchestration with four different Turbo broadcast methods
  (`chat_service.rb:110-135`); extracting a small `TurnBroadcaster` would make
  the service read linearly, but at this size it is defensible.
- **Duplication**: minimal. The only repetition is
  `self.class.stream_name(@conversation_id)` in five broadcast calls — trivial.
- **Dead code**: `RedisConnection.reset!` (`app/services/redis_connection.rb:14`)
  is never called anywhere (grep confirms; `test_helper.rb` uses
  `RedisConnection.current.flushdb` instead). `ChatService::Result` is consumed
  only by tests, not by the controller.
- **Method/class size**: all methods short; the Lua script embedded in a
  heredoc is the longest single block and is appropriately self-contained.
- **Coupling**: controllers depend on service classes directly (fine at this
  scale). `MessagesController` ignores the `:conversation_id` route parameter
  and uses the session instead (see Risks) — a latent coupling bug rather than
  a style issue. Views reach into `ChatConfig` (`_budget_notice`) and
  `ChatService.stream_name` (`conversations/index.html.erb:9`) directly;
  acceptable, though helpers would be tidier.

Top 3 refactors, given more time:

1. **Serialize turns per conversation and fix thread management.** Replace the
   fire-and-forget `Thread.new` (`messages_controller.rb:53`) with a small
   runner that holds a per-conversation lock (e.g. a Redis `SET NX PX` lock or
   a serialized queue). This fixes the concurrent-turn history interleaving
   (Risk R1) and gives in-flight turns a lifecycle.
2. **Make the controller honor `params[:conversation_id]`** (or drop the
   nested route). Today the URL says one conversation while the session decides
   another — a real multi-tab correctness bug (Risk R2).
3. **Tell the truth in coverage and clean up the edges**: remove dead
   `reset!`, and decouple the tailwind pre-build from `bin/rails test` (or
   load `test_helper`/SimpleCov first) so `lib/chat_config.rb` doesn't report
   a bogus 0%. Update the default model to the current Sonnet while at it.

## 3. Test coverage assessment

Measured during this review with `bin/rails test` (53 runs, 145 assertions,
0 failures):

- **Line coverage: 92.85% (247/266)** — `coverage/.last_run.json`
- **Branch coverage: 88.00% (44/50)**

Important caveat on the line number: 16 of the 19 "missed" lines are the whole
of `lib/chat_config.rb`, reported at 0% purely as a **measurement artifact** —
`bin/rails test` runs the tailwindcss build first, which boots the Rails
environment (loading `chat_config.rb` via the initializer) *before*
`test_helper.rb` starts SimpleCov. I verified this by probing
`$LOADED_FEATURES` inside `test_helper`: the file is already loaded. Running a
single test file (no tailwind pre-build) reports `chat_config.rb` as covered,
and `chat_service_test.rb:78` does assert `ChatConfig.system_prompt`. Excluding
this artifact, real coverage is ~98.8% of lines.

Genuinely uncovered lines (3):

- `app/services/arithmetic_evaluator.rb:85` — "unexpected closing parenthesis"
  raise (input like `1+)`).
- `app/services/chat_service.rb:78` — `""` fallback when the response object
  has no `content` (defensive path).
- `app/services/redis_connection.rb:15` — body of the dead `reset!`.

**Weakest-tested area**: the edge/error paths above plus everything outside the
Ruby process — the two Stimulus controllers (autoscroll, composer) have **zero
automated tests**, and there are no system/browser tests at all.

Failure modes NOT covered by any test:

- Redis being unreachable mid-turn or at boot (`Redis::CannotConnectError` —
  it would be rescued by the `StandardError` handler, but that is untested).
- A stream that aborts part-way (partial assistant text broadcast, nothing
  persisted; the placeholder-cursor UI state afterwards is untested).
- Concurrent turns in one conversation (G6 is validated by Lua atomicity and a
  live multi-worker run, but no test exercises two simultaneous turns).
- Provider tool-call round trips (`ask` with tool invocations) — the tools
  are unit-tested in isolation, the integration is only proven live.
- Action Cable broadcast failures inside the streaming block.
- The multi-tab/route-param mismatch (controller uses session id, not the URL).

## 4. Known defects and risks

- **R1 — Concurrent-turn interleaving (racy).** `ChatService#call` reads
  history (`chat_service.rb:33`) and appends the user+assistant pair later
  (`:46`). Two rapid messages in one conversation both replay the same
  history; the persisted order of the two pairs can invert, and each turn's
  replayed history misses the other in-flight turn. No per-conversation lock.
  The Lua append is atomic, which prevents corruption but not mis-ordering.
- **R2 — Controller ignores the route's conversation id.** All of
  `MessagesController#create` uses `current_conversation_id` (session), never
  `params[:conversation_id]`. With two tabs on different conversations, the
  tab that loaded last wins the session; a message typed in the other tab is
  persisted to the wrong conversation while its echo renders in the tab the
  user typed it in. Latent correctness bug.
- **R3 — Unbounded, unmanaged threads.** Every accepted message spawns a raw
  `Thread.new` (`messages_controller.rb:53`) — no cap, no registry, no
  graceful shutdown. In-flight turns die silently on restart (the placeholder
  with its pulsing cursor stays in the UI forever; the user message is visible
  but never persisted until reload).
- **R4 — Check-then-act on the token budget.** The budget check
  (`messages_controller.rb:16`) and the usage recording
  (`token_budget.rb:39-45`) are not atomic; two concurrent turns can both pass
  the check. Acceptable for approximate budgeting, noted for completeness.
- **R5 — Test-suite hazard: `flushdb` honors `REDIS_URL`.**
  `test/test_helper.rb:12` uses `||=`, so if a developer runs the suite with
  `REDIS_URL` exported (e.g. pointing at their dev Redis), every test run
  flushes that database. It should hard-require a dedicated test DB or at
  least assert the URL is the scratch one.
- **R6 — Byte cap is soft for a single oversized message.** The Lua trim loop
  (`conversation_store.rb:34`) keeps at least one message, so one message
  larger than `CHAT_MAX_BYTES` (default 64KB) stays in full. Bounded in
  practice by the count cap, but the byte guarantee has this exception.
- **R7 — No conversation access control (accepted, but real).**
  `ConversationsController#show` assigns any `params[:id]` into the session.
  No auth is an explicit goal (G14), but anyone with a conversation UUID can
  read and append to that conversation. Fine for a local demo; must not be
  exposed publicly as-is.
- **R8 — Stale default model.** `anthropic/claude-sonnet-4.5` is two
  generations behind (Sonnet 4.6, then Sonnet 5 on 2026-06-30). Overridable
  via `CHAT_MODEL`; the default should be bumped. (This is the G3 PARTIAL.)
- **R9 — Version control unused.** The git repository has **no commits** —
  every file is untracked. Nothing is lost to secrets (nothing is committed),
  but there is also no history, no rollback point, and no reviewable diff of
  phases 1–2.
- **R10 — SimpleCov blind spot.** Full-suite coverage silently under-reports
  `lib/chat_config.rb` (0%) due to the tailwind pre-build boot order described
  in §3. Anyone trusting the HTML report will misread the gap.
- **R11 — Workspace clutter.** `tmp/` contains phase-2 validation leftovers
  (`convo_client.py`, `stream_check.py`, `g6_jar.txt`,
  `secret_key_base.txt`, `venv/`) and `log/` has validation server logs. All
  gitignored, so harmless to the repo, but `tmp/secret_key_base.txt` is a
  secret sitting in plaintext on disk (locally generated, not committed
  anywhere).

## Fixes applied during this review

None to application code. The only addition is `tmp/stream_check.py`
(gitignored validation tooling) used to produce the G4/G7/G8/G6 live evidence
above. The `chat-demo-web-1` container was restarted once as part of the G6
restart-survival proof and is healthy.
