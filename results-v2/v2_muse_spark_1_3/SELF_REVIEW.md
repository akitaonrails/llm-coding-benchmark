# SELF_REVIEW — Chat · Rails + RubyLLM + Hotwire (phase 3)

No code changes were made in phase 3. All findings below are from re-reading the
current working tree and re-running the suite and gates now. No new features added.

## 1. GOAL VERIFICATION TABLE

| Goal | Verdict | Evidence (re-verified now) |
|------|---------|----------------------------|
| G1 | PASS | `.ruby-version:1` + `mise.toml:1` pin `ruby 4.0.6`; `ruby -v` → `4.0.6`; `mise ls-remote ruby` newest stable is `4.0.6` (only `4.1-dev` above it); `Gemfile:4` + `Gemfile.lock` → `rails 8.1.3.1`; `config/application.rb:6-10` requires only active_model/action_controller/action_view/action_cable (no active_record/active_job/action_mailer); app lives at workspace root, no nested dir. "Generated with generators" taken on structure (standard Rails layout, `bin/rails`, importmap, test dirs); cannot prove provenance from tree alone. |
| G2 | PASS | `app/views/chats/index.html.erb` + partials `_message,_form,_error,_user_bubble,_assistant_placeholder,_title` (componentized, no single-file dumps); `app/javascript/controllers/chat_controller.js`, `chat_form_controller.js` + Stimulus via importmap; `turbo_stream_from` in index; `grep -rn "fetch(\|innerHTML" app/ config/` finds only `ENV.fetch` hits — no hand-rolled fetch/innerHTML; Tailwind via `stylesheet_link_tag "tailwind"` in layout. |
| G3 | PASS | `Gemfile:59` `ruby_llm ~> 1.16` (installed `1.16.0` per `bundle show ruby_llm`); `config/initializers/ruby_llm.rb:5-9` sets `openrouter_api_key` + `default_model` from `CHAT_MODEL`; `app/services/chat_config.rb:6,24-26` `DEFAULT_MODEL="anthropic/claude-sonnet-5"`, env-overridable. Caveat: `claude-sonnet-5` is not in ruby_llm 1.16's own `models.json` (max there is `claude-sonnet-4.6`); the app passes `assume_model_exists: true` (`chat_service.rb:67-75`) so OpenRouter is the authority. Phase-2 log records a real compose chat succeeding with the default model, but I did not spend API calls to re-prove the model id in phase 3. |
| G4 | PASS | `app/services/chat_streamer.rb:21-27,33-39` broadcasts one `broadcast_append_to` per non-empty chunk into `assistant_reply_<id>`; `chat_service.rb:45` passes `&streamer.to_proc` to `chat.ask`, and ruby's `Chat#ask`/`instrument_completion` treats a given block as streaming mode (verified in installed gem `chat.rb:39-41,239-241`). Tests: `ChatStreamerTest` ("appends each chunk incrementally…") and `ChatServiceTest` ("successful turn … streams chunks", asserts 2 chunk broadcasts). Phase-2 probe log: 60-word story → 5 `assistant_reply_*` appends spread t+1234…3631 ms, done 5849 ms. NOT re-proven live in phase 3. Known cross-worker caveat, see §4 item 1. |
| G5 | PASS | `chat_service.rb:40-45`: `replay_history(chat, history)` replays stored turns, then `.ask(prompt)` adds the new user turn once inside RubyLLM (`chat.rb:39-41` `ask` → `add_message role: :user`); `ChatMessageBuilder.build(history, prompt)` returns history + prompt exactly once and `chat_message_builder_test.rb:6-21` asserts the exact 4-element outgoing array with the new prompt counted once; `chat_service_test.rb:50-57` asserts replayed `[[user,a],[assistant,b]]` and `"c"` appears exactly once across replay+ask. Honesty note: the `outgoing` value built at `chat_service.rb:36` is **assigned but never used** — the real payload goes through `replay_history`+`ask`. Mechanism is correct; the builder is dead code (see §2). |
| G6 | PASS (persistence) / caveat (live cable) | `ConversationStore` is file-backed (`tmp/chat_store`, `CHAT_STORE_DIR`-overridable), `flock`-guarded (`conversation_store.rb:81-88`), atomic rename writes (`118-130`), message-count cap (`132-135`), byte cap (`137-142`), TTL via `.ttl` mtime (`147-159`); `puma.rb:31-33` honors `WEB_CONCURRENCY` with `preload_app!`; `compose.yaml:13` sets `WEB_CONCURRENCY=2` with a persisted `chat_store` volume. Tests cover count/byte/TTL/tokens. Phase-2 log: WEB_CONCURRENCY=2 conversation survived master SIGTERM+restart with consistent 4-message history. Caveat: `config/cable.yml:7-8` uses `async` adapter in production, which does not fan out across workers — history stays consistent but live chunk broadcasts may not reach a viewer pinned to the other worker (see §4). |
| G7 | PASS | Exactly two `with_tool` registrations, both in `chat_service.rb:43-44`: `ServerTimeTool` (`server_time_tool.rb:5-9`, `RubyLLM::Tool`, `execute` → UTC ISO8601) and `CalculatorTool` (`calculator_tool.rb:5-29`, `param :expression`, recursive-descent parser, no `eval`); tool names verified by `tools_test.rb:30-31,41` (`:calculator`, `:server_time`); `chat_service_test.rb:47` asserts both tools registered on the chat; `SYSTEM_PROMPT` (`chat_config.rb:15-21`) directs tool use. Live tool invocation last proven in phase 2 (monkey-patched `execute`: time reply `2026-09-04T22:38:58Z`, `37*48+11` → `1787`); phase 3 relies on unit tests + that log, no new live calls. |
| G8 | PASS | `conversation_title_schema.rb:4-5` (`RubyLLM::Schema`, `string :title`); `chat_service.rb:91-102` calls `with_schema(ConversationTitleSchema).ask(...)` only when no title exists and it is the first exchange; `create.turbo_stream.erb:6` updates `#conversation_title`, rendered in `index.html.erb:6` via `_title.html.erb:1`. Test `chat_service_test.rb:59-65` asserts schema class used and title persisted. Quality wart: `extract_title` (`chat_service.rb:105-118`) has a discarded expression at line 109 and convoluted fallback parsing; harmless but ugly. |
| G9 | PASS | `chat_config.rb:7,40-42` budget default `20_000`, `CHAT_TOKEN_BUDGET`-overridable, shown in UI (`index.html.erb:7`); `chat_service.rb:27-34` refuses pre-turn with `budget_message` and never calls the factory; test `chat_service_test.rb:89-101` asserts refusal + factory not called. Estimator is chars/4 heuristic (`conversation_store.rb:74-77`); check is pre-turn only, so one turn can overshoot — disclosed, acceptable for a demo budget. |
| G10 | PASS | `with_instructions(ChatConfig::SYSTEM_PROMPT)` at `chat_service.rb:42`; missing-key preflight `chat_service.rb:24` with actionable `MISSING_KEY_MESSAGE` (`12-13`); `rescue StandardError → failure(:provider)` (`47-50`) with nothing written to the store on that path; error branch renders `_error` bubble + status (`create.turbo_stream.erb:9-12`). Tests: missing-key (`67-78`), provider-failure-not-stored (`80-87`), blank/oversize validation (`103-108`). |
| G11 | PASS | `bin/rails test` just re-run: `29 runs, 83 assertions, 0 failures, 0 errors, 0 skips`; per-component files: `chat_service_test, chat_message_builder_test, conversation_store_test, tools_test, streamer_test, chat_config_test` (+schema), `integration/chats_test`; error paths covered (missing key, provider raise, budget, validation, empty chunk, unsafe expr, div-by-zero, TTL, byte cap). `FakeChat` (`test/support/fake_chat.rb`) mirrors the real surface I verified in the installed gem: `RubyLLM.chat(...)` (`ruby_llm.rb:58`), `Chat#ask/with_instructions/with_tool/with_schema/add_message` (`chat.rb:39,46,58,111,165`), block-form streaming, chunk `#content` (`chunk.rb` < `Message`, `message.rb:31`). `SimpleCov` wired in `test_helper.rb:2-8` with branch coverage; report regenerates to `coverage/`. Weak spots disclosed in §3. |
| G12 | PASS | Just re-run: `bundle exec rubocop` → `41 files inspected, no offenses detected`; `bundle exec brakeman --quiet` → `Security Warnings: 0, No warnings found`; `bundle exec bundle-audit check` → `No vulnerabilities found` (run without `--update`; network DB refresh not attempted in phase 3). |
| G13 | PASS (static + phase-2 runtime; image not rebuilt in phase 3) | `Dockerfile`: `RAILS_ENV=production`, `USER 1000:1000` (`64-66`), `ENTRYPOINT /rails/bin/docker-entrypoint` (`78`), Thruster+Puma on 80 (`82`), writable `tmp/chat_store`+`log` chowned (`74-75`); `compose.yaml`: builds local image, `3000→80`, `chat_store` named volume, `WEB_CONCURRENCY=2`; `docker compose config` succeeds (ran now); `README.md:33-41,71-84` documents setup, env vars, run, compose. Phase-2 log records `docker build` + `compose up` + a real in-compose chat (`COMPOSE_OK` turbo-stream + persisted volume entry). I did not rebuild the image in phase 3 (time), so a present-day build breakage would not have been caught by me. |
| G14 | PASS | No auth code anywhere (routes: only `chats#index/create/destroy` + health); `grep` for key patterns finds only `ENV[...]` reads, `test-key` placeholders, and `${OPENROUTER_API_KEY:-}` interpolation — no committed secrets; `.gitignore:6-12,28` + `.dockerignore:10-16` exclude `.env*`, `master.key`, `tmp/*`; `compose.yaml` injects secrets only via env interpolation. Notes: repo still has **zero commits** (`git status`: all files untracked), so "nothing committed" is vacuous but true; `config/master.key` (0600) and `tmp/local_secret.txt` exist in the working tree and are ignore-listed (verified via `git check-ignore`) — they must never be `git add`ed. `docker compose config` prints the resolved `OPENROUTER_API_KEY` from the surrounding shell env; treat that output as secret. |

## 2. CODE QUALITY ASSESSMENT

Generally readable: small service objects with one job each, frozen-string-literal
everywhere, env-driven config isolated in `ChatConfig`, views decomposed into
partials, no `fetch()`+`innerHTML`, no God classes. Real warts found by reading:

- **Dead code / dead expressions.** `ChatService#call` builds `outgoing =
  ChatMessageBuilder.build(history, prompt)` (`chat_service.rb:36`) and never uses
  it — the actual payload is `replay_history` + `ask`. `ConversationStore.replace_all`
  (`conversation_store.rb:25-30`) has no callers; `KEY_PREFIX`/`TTL_KEY_PREFIX`
  (`6-7`) are unused; `ChatService#extract_title` line 109 computes a string and
  discards it before re-parsing on line 110. A reviewer testing G5 only against the
  builder would be testing code that never runs.
- **Single responsibility / layering.** `ChatService#call` (63 lines) does
  validation, preflight, budgeting, provider call, streaming wiring, persistence,
  token accounting, and title generation. `ChatsController#create` calls
  `ChatAnnouncer.start` (which broadcasts bubbles) *before* any validation, so a
  blank prompt / missing key / over-budget turn still emits cable broadcasts before
  failing. `ChatAnnouncer` calls `ApplicationController.render` directly, coupling a
  service to view rendering and the exact partial names/ids that the `.erb` files
  also hardcode (`assistant_reply_<id>` appears in 3 places).
- **Duplication / coupling.** Target DOM ids (`messages`, `assistant_reply_*`,
  `chat_status`, `conversation_title`, `token_count`) are string-coupled across
  `chat_streamer.rb`, `chat_announcer.rb`, `create.turbo_stream.erb`, and
  `index.html.erb`. Store reads `ChatConfig` globals directly (untestable without
  ENV mutation, which the tests do liberally). `default_chat`/`default_title_chat`
  (`chat_service.rb:67-75`) are identical bodies.
- **Size.** Nothing egregious: largest methods are `ChatService#call` (~43 lines),
  `ConversationStore.write_locked/enforce_bounds`, and the calculator parser (each
  parse step tiny). The parser keeps mutable `@tokens/@pos` instance state.
- **Naming.** Good overall (`ChatStreamer`, `ChatAnnouncer`, `ChatMessageBuilder`
  names match their jobs; tool `description`s are clear).

Top 3 refactors with more time, in order:

1. **Make one turn one atomic store transaction.** Today a successful turn performs
   `append(user)` + `append(assistant)` + `add_tokens` + `save_title` as four
   separate `flock` sections; two concurrent POSTs to the same conversation can
   interleave to `user,user,assistant,assistant`. Add `ConversationStore.append_turn(id,
   user:, assistant:, tokens:, title:)` doing a single locked read-modify-write, and
   have `ChatService` call it once. This is the highest-value fix because it is a
   real correctness hazard under concurrency, not style.
2. **Kill or wire the dead payload path.** Either delete `ChatMessageBuilder` (if
   `replay_history`+`ask` is canonical) or actually send its output — e.g. build the
   array once and drive both the history replay and the G5 assertion from it — plus
   delete `replace_all`/unused constants and the dead line-109 expression. Rationale:
   untested-by-execution code that *looks* like the correctness mechanism is worse
   than missing code; it invites future divergence (e.g. someone "fixes" the builder
   while production keeps using `replay_history`).
3. **Move broadcasts behind an interface owned by the controller/view layer.**
   Return turn events from `ChatService` (or a result broadcaster) instead of having
   services call `Turbo::StreamsChannel` and `ApplicationController.render`
   directly; validate *before* announcing; replace string-coupled target ids with
   shared constants/helpers. Rationale: removes render-from-service coupling, fixes
   the announce-before-validation ordering bug, and makes the streaming contract
   testable without stubbing globals.

## 3. TEST COVERAGE ASSESSMENT

Re-ran `bin/rails test` now: **29 runs, 83 assertions, 0 failures, 0 errors** —
**line 93.37% (310/332), branch 69.41% (59/85)** (SimpleCov, `primary_coverage :branch`).

Per-file missed lines (from `coverage/.resultset.json`): `calculator_tool.rb`
`[27,70,89,90,92,93,109]` (generic-rescue, `%`-with-float/some power/unary/primary
branches, bad-token raise); `chat_service.rb` `[68,73]` (the two real
`default_*_chat` factories — tests always inject fakes) and `[101]` (title-rescue);
`chat_streamer.rb` `[48,50]` (non-string `Content#text` path + its rescue);
`conversation_store.rb` `[26-29]` (`replace_all`, entirely untested) and `[111]`
(corrupt-JSON rescue) + `[115]` (unlocked `write` wrapper). Controllers, announcer,
config, builder, schema, server-time tool: fully hit.

- **Weakest-tested area:** `ConversationStore` write/corruption paths
  (`replace_all`, corrupt-JSON fallback, unlocked `write`) and the calculator's
  malformed-expression branches — i.e. exactly the adversarial inputs. Branch
  coverage at 69% reflects many untested `rescue`/edge arms.
- **Failure modes with NO test:** concurrent same-conversation writes from two
  processes/threads (interleaving order); title-generation provider failure (the
  `rescue StandardError → existing` arm); corrupt store JSON on disk; TTL disabled
  (`ttl<=0`); mid-stream provider exception after partial chunks; budget overshoot
  within a single turn; oversize prompt (`MAX_PROMPT_CHARS`) rejection; ActionCable
  broadcast raising; anything touching the real RubyLLM stack (all provider
  behavior is mocked); Docker/compose runtime (no test, only phase-2 manual proof).

Note: `test_helper.rb:6-7` uses deprecated `SimpleCov.add_filter` (still works;
deprecation warning printed each run).

## 4. KNOWN DEFECTS AND RISKS

1. **Cable adapter is single-process (`config/cable.yml:8` `async` in production).**
   Under `WEB_CONCURRENCY=2` the file store stays consistent, but a viewer
   subscribed on worker A will not receive chunk broadcasts emitted on worker B.
   G4 degrades precisely in the configuration G6 mandates. Fix: Redis cable adapter.
2. **Turn persistence is not atomic** (two `append`s + `add_tokens` + `save_title`
   under separate locks). Concurrent POSTs to one conversation can interleave and
   be replayed out of order. Also both racers may fire title generation; last write
   wins. See refactor #1.
3. **`CalculatorTool` has no cost/complexity guard.** `9**9**9`-style exponents,
   megabyte-long digit strings, or deep parens can spin CPU / blow memory inside a
   request thread (Puma threads are finite; request timeout does not bound tool
   execution). The `ALLOWED` char class (`calculator_tool.rb:10`) also contains a
   redundant `.*` inside the class —allows what was intended but reads as a
   mistake — and error/numeric result shapes are inconsistent (`{result:}` vs
   `{error:}`). Parser state lives in `@tokens/@pos`; safe today (fresh instance
   per turn) but fragile if RubyLLM ever reuses tool instances across threads.
4. **Budget accounting is approximate and pre-turn only.** `chars/4` ignores system
   prompt/tools/overhead; a single 4000-char prompt can overshoot the budget
   mid-turn; token counts are never reconciled with provider-reported usage.
5. **Unbounded conversation count / disk growth.** Per-conversation caps exist, but
   there is no global cap or sweeper; TTL only expires a conversation when it is
   *read* (`read_locked`), so abandoned conversations sit on disk (and in the
   compose volume) indefinitely.
6. **Announce-before-validate ordering** (`chats_controller.rb:20` runs before
   `ChatService#call`): invalid/missing-key/over-budget turns emit user-bubble +
   placeholder broadcasts, then the error branch removes the placeholder. Cosmetic,
   but wrong order and wasteful under spam.
7. **Long synchronous POSTs.** Each turn holds a Puma thread up to
   `CHAT_REQUEST_TIMEOUT` (120 s) plus a second provider call for the title. No
   rate limiting; a demo with no auth can burn the OpenRouter budget or exhaust
   threads. No background job by design (brief forbids Active Job), so this is
   accepted but operationally real.
8. **Title path fragility.** `extract_title` fallback mangles non-JSON replies with
   a regex strip; the title prompt interpolates raw user/assistant text (second
   provider call sees untrusted content — low stakes here, but it is prompt
   injection surface by construction); title failure is silent by design.
9. **Model-id fragility.** Default `anthropic/claude-sonnet-5` bypasses the gem
   registry via `assume_model_exists`; a provider-side rename breaks every turn
   (mitigated by `CHAT_MODEL` override, which operators must then discover).
10. **Secret handling hygiene.** `config/master.key` + `tmp/local_secret.txt` sit in
    the worktree (ignored, uncommitted — repo has zero commits so far); a careless
    `git add -A` + first commit would permanently record them unless the ignores
    are respected. `compose.yaml` defaults `SECRET_KEY_BASE` to
    `change-me-in-production`, which is insecure if anyone deploys compose as-is.
11. **Streaming error UX.** If the provider raises mid-stream, already-broadcast
    chunks remain replaced by removal (`turbo_stream.remove` the placeholder) and
    only a generic error bubble shows; partial content is lost and the failure is
    not distinguished from pre-call failures.
12. **Minor:** `ConversationStore#safe_id` strips attacker-controlled id characters
    (good) but silently collides distinct ids that normalize identically; `ttl<=0`
    disables expiry (documented behavior, untested); `chat_controller.js` never
    auto-scrolls on streamed appends (only on connect), so long streams can scroll
    out of view.
