# Self-review

Phase 3. Every claim below was re-checked against the code in this workspace on
2026-07-26, not against memory of what was intended.

Environment used for verification: Ruby 4.0.6, Rails 8.1.3, `ruby_llm` 1.16.0.
Live checks ran against the Docker Compose stack (`sonnet-chat-app-1`,
`RAILS_ENV=production`, `WEB_CONCURRENCY=2`) with a real `OPENROUTER_API_KEY`.

## Fixes made during this review

Two defects were found in `Assistant::Arithmetic` (the `calculator` tool) and
fixed. Nothing else was changed except the test count in `README.md:145`.

1. **Operator precedence was wrong for a signed base.**
   `-2 ** 2` evaluated to `4`. Ruby and standard notation both give `-4`: the
   sign applies to the power, not the base. The parser called `unary` from
   `power`, so the sign was absorbed into the base. Restructured to
   `term → unary → power → primary`, with the exponent going back through
   `unary` so `2 ** -3` still parses
   (`app/services/assistant/arithmetic.rb:103-127`). This was handing the model
   silently wrong arithmetic — the exact failure the tool exists to prevent.
   Covered by `ArithmeticTest#test_a_leading_sign_binds_looser_than_exponentiation`.
2. **A fractional power of a negative base returned a `Complex`.**
   `(0 - 8) ** 0.5` returned `(0.0+2.8284271247461903i)`, which was then
   serialised into the tool result. Now rejected as
   `"result is not a real number"` (`app/services/assistant/arithmetic.rb:54-56`).
   Covered by `ArithmeticTest#test_rejects_a_complex_result_from_a_fractional_power_of_a_negative_base`.

Post-fix: `bin/rails test` → 168 runs, 438 assertions, 0 failures, 0 errors,
0 skips. `bin/rubocop` → 63 files, no offenses. `bin/brakeman` → 0 warnings.
`bundle-audit check` → no vulnerabilities.

---

## 1. Goal verification table

| Goal | Verdict | Evidence |
| --- | --- | --- |
| G1 — newest Ruby/Rails from mise; no AR/AM/AJ; generators; no nested app dir | PASS | `mise latest ruby` → `4.0.6` = `mise.toml:2` = `.ruby-version`; `gem list -r -e rails` → `8.1.3` = `Gemfile:4`; `config/application.rb:6,7,10` leave `active_job`, `active_record`, `action_mailer` commented out (`bin/rails runner 'p defined?(ActiveRecord)'` → nil); `Gemfile`/`config.ru` are at the workspace root, no nested directory. Generator provenance is inferred from untouched generator output (`config/environments/*.rb`, `app/views/pwa/`, `public/icon.*`), not directly provable after the fact. |
| G2 — Tailwind, Hotwire/Stimulus/Turbo Streams, partials, no hand-rolled DOM | PASS | 17 partials under `app/views/conversations/`; Tailwind v4 via `app/assets/tailwind/application.css` (live page serves `/assets/tailwind-7d53458d.css`); two Stimulus controllers (`composer_controller.js`, `autoscroll_controller.js`) registered through `config/importmap.rb:7`; live page contains `<turbo-cable-stream-source …>` and `data-controller="composer autoscroll"`. `grep -rn "fetch(\|innerHTML" app/javascript/` → no matches. |
| G3 — `ruby_llm` latest, OpenRouter, latest Claude Sonnet, env-overridable | PASS | `Gemfile:23` `ruby_llm ~> 1.16`, lockfile `1.16.0`, which is the newest published version (`gem list -r -e ruby_llm --all`). `chat_factory.rb:28` passes `provider: :openrouter`; `chat_factory.rb:38-45` sets `openrouter_api_key`/`openrouter_api_base`. `settings.rb:8` `DEFAULT_MODEL = "anthropic/claude-sonnet-5"`, confirmed present and the highest Sonnet in the live OpenRouter catalogue (`curl https://openrouter.ai/api/v1/models`). Overridable via `ASSISTANT_MODEL` (`settings.rb:30-32`), asserted in `MultiTurnPayloadTest#test_the_payload_names_the_configured_model_and_both_tools`. |
| G4 — true token streaming over Turbo Stream broadcasts | PASS | `turn_runner.rb:42-48` passes a block to `chat.ask` and calls `broadcaster.token` per delta; `broadcaster.rb:57-63` issues one `broadcast_append_to` per delta. **Live proof:** subscribed to the Action Cable Redis channel while posting "Write a 300-word explanation of how Hotwire works" — 20 separate `append` frames targeting `pending_<id>_body` arriving between t=4.59 s and t=10.12 s, then one `replace` at t=10.27 s. A direct chunk probe through `ChatFactory` showed 30 chunks spread over 9.76 s, first content chunk at 1.53 s. Not a single end-of-turn append. |
| G5 — each user turn sent exactly once; unit test asserts the outgoing array | PASS | `conversation.rb:37-42` `replayable_history_before` slices `messages[0...index]`. `test/services/assistant/multi_turn_payload_test.rb` asserts the **literal JSON HTTP body** captured by WebMock, not a stand-in: `:25` asserts the exact 6-element `messages` array for a third turn; `:47` asserts `%w[one two three]` with no duplicates; `:100` asserts the post-tool-call follow-up still carries one user message. `ChatFlowTest#test_a_second_exchange_replays_the_first_without_duplicating_it` repeats it over real HTTP. |
| G6 — survives restart, correct under `WEB_CONCURRENCY=2`, bounded, TTL | PASS (one caveat) | Store is Redis-only outside test (`conversation_repository.rb:34-36`); atomic RMW via `WATCH`/`MULTI`/`EXEC` with retry and `ConflictError` (`redis_adapter.rb:64-77`). Compose runs `WEB_CONCURRENCY: "2"` — container log shows `* Workers: 2`, `Worker 0 (PID: 21)`, `Worker 1 (PID: 25)`. **Live proof:** a conversation with 4 messages / 5,973 tokens survived both `docker restart sonnet-chat-app-1` and a full `docker compose build && up -d` image rebuild. Bounds and TTL applied on every write (`conversation_repository.rb:114-121`, `conversation.rb:69-79`). *Caveat:* the byte cap loop stops at `kept.size > 1`, so a single message larger than `ASSISTANT_MAX_BYTES` is never dropped — see Defect 6. |
| G7 — exactly two tools via RubyLLM's tool API | PASS | `chat_factory.rb:11` `TOOLS = [Tools::ServerTime, Tools::Calculator]`, wired with `chat.with_tools(*tools)` (`chat_factory.rb:21`). Both subclass `RubyLLM::Tool` with `description`/`param`/`execute`. `MultiTurnPayloadTest` asserts the wire payload advertises exactly `%w[server_time calculator]`. **Live proof:** asked the deployed app "What time is it right now, and what is (1240 * 3) / 8?" → "Right now it's Sunday, 26 July 2026, 18:58:28 UTC. And (1240 × 3) / 8 = 465." Both tools actually invoked; 465 is correct. |
| G8 — structured-output title after the first exchange, shown in the UI | PASS | `titler.rb:26-31` uses `chat.with_schema(TitleSchema.instance)`; `title_schema.rb:9` subclasses `RubyLLM::Schema`. `TitlerTest#test_sends_a_strict_json_schema_and_returns_the_parsed_title` asserts the wire body carries `response_format.type == "json_schema"`, `name == "conversation_title"`, `strict == true`. Triggered only after `completed_exchange?` (`turn_runner.rb:76`). **Live proof:** the deployed app titled a conversation "Explain Turbo Streams", rendered in `#conversation_title` and in the sidebar. |
| G9 — token budget, env-configurable, refuses in-UI without calling provider | PASS | `settings.rb:11,50-52` (`ASSISTANT_TOKEN_BUDGET`, default 60 000); usage accumulated in `token_usage.rb` with a chars/4 fallback; refusal in `messages_controller.rb:55-61` runs **before** `start_turn`, returning `422` with a composer message. `MessagesControllerTest#test_a_conversation_over_its_token_budget_is_refused_in_the_ui` asserts `assert_not_requested` against OpenRouter. Meter live at `_token_budget.html.erb`; deployed app showed `5,973 / 60,000 tokens`. *Limits:* the check is pre-turn only — see Defects 3 and 4. |
| G10 — instructions API, key preflight, failures rescued, failed turns not replayed | PASS | Instructions: `chat_factory.rb:20` `chat.with_instructions(...)` with `Settings::SYSTEM_PROMPT`; asserted as a `system` role message in the wire body (`multi_turn_payload_test.rb:19`). Preflight: `chat_factory.rb:33-35` raises `MissingApiKeyError`, plus the pre-typing banner in `_api_key_banner.html.erb:2`. Rescue: `turn_runner.rb:30-33` catches `StandardError` → `ProviderFailure.message_for` → `broadcaster.failed`; 12 statuses and 4 exception classes mapped in `provider_failure.rb:13-33`. Failed turns: `chat_message.rb:52` marks `FAILED`, `conversation.rb:41` filters with `select(&:ok?)`; asserted end-to-end by `ChatFlowTest#test_a_failed_exchange_is_not_replayed_on_the_next_attempt`. |
| G11 — Minitest for every component, faithful mocks, error paths, SimpleCov | **PARTIAL** | Ruby side is strong: 168 tests / 438 assertions across 18 files; SimpleCov 100.00% line, 92.00% branch (`coverage/.last_run.json`), with `minimum_coverage line: 98, branch: 90` enforced at `test/test_helper.rb:14`. Mock fidelity is real, not nominal: tests stub OpenRouter at the HTTP layer with WebMock and assert the literal request body (`test/support/openrouter_stubs.rb`), so a hallucinated RubyLLM method would not compile a passing test. Error paths covered (`turn_runner_test.rb:138-208`, `provider_failure_test.rb`). **Why not PASS:** the two Stimulus controllers (~100 lines in `app/javascript/controllers/`) have **zero** tests — no JS test runner and no `test/system/` directory, despite `capybara` and `selenium-webdriver` sitting unused in `Gemfile:55-56`. "Tests for every component" is not true of the client-side components. |
| G12 — Brakeman, RuboCop, bundle-audit clean | PASS | `bin/rubocop` → "63 files inspected, no offenses detected". `bin/brakeman -q --no-pager` → "Security Warnings: 0", "No warnings found". `bundle exec bundle-audit check --update` → "No vulnerabilities found" (advisory DB at commit `6abafa3`, 2026-07-25). All three re-run after the arithmetic fix. |
| G13 — production Dockerfile, compose, README | PASS | `Dockerfile:21` `RAILS_ENV="production"`; `:58-62` creates `rails` uid/gid 1000 and `USER 1000:1000` (verified live: `docker exec … id -u` → `1000`, `id -un` → `rails`); `:64` `ENTRYPOINT ["/rails/bin/docker-entrypoint"]`; multi-stage so build tooling is dropped; `HEALTHCHECK` at `:69`. `compose.yaml` brings up Redis + app; **verified live**: `docker compose build && up -d` → container `healthy`, `GET /up` → 200, `GET /` → 200 with a fully rendered SPA. `README.md` covers what it does, setup, both run paths, and the full env table. *Caveat:* the compose `SECRET_KEY_BASE` default is a weak literal — see Defect 8. |
| G14 — no auth, no committed secrets, everything in-workspace | PASS (with a scoping caveat) | No authentication anywhere (`ApplicationController` has no auth filter; `config/routes.rb` has no auth routes). `git check-ignore -v` confirms `config/master.key` is ignored by `.gitignore:28` and `.env` by `.gitignore:11`; `git add -An` stages no key/env file. `.env.example:6,9` ship empty values. No literal key in `Dockerfile`, `compose.yaml`, `README.md`, or any source file — all read from ENV. Everything lives under the workspace root. *Note:* the repository has **zero commits** (`git log` → "does not have any commits yet"), so "not committed" is currently vacuous; the `.gitignore` is nonetheless correct for the first commit. *Caveat:* "no auth" is honoured, but the conversation sidebar is a global unscoped list — see Defect 1. |

**Summary: 13 PASS, 1 PARTIAL, 0 FAIL.**

---

## 2. Code quality assessment

### What holds up

**Naming.** Names describe intent, not mechanism: `replayable_history_before`,
`budget_exceeded?`, `completed_exchange?`, `ProviderFailure.message_for`,
`Storage::Adapter`. Nothing is called `Manager`, `Handler`, or `Util`.

**Single responsibility, mostly honoured.** The turn pipeline is genuinely
decomposed: `MessagesController` (accept/refuse) → `TurnDispatcher` (threading)
→ `TurnRunner` (orchestration) → `ChatFactory` (provider wiring) /
`Broadcaster` (transport) / `ConversationRepository` (persistence). Sizes are
small and measured: the largest file under `app/` is `arithmetic.rb` at 168
lines (a module wrapping a nested parser class), then
`conversation_repository.rb` at 129 and `conversation.rb` at 115; the single
longest method in the whole app is `MessagesController#start_turn` at 17 lines,
and it is the only method at or above 15.

**Layer coupling is clean in one important place.** `Conversation` and
`ChatMessage` are plain frozen value objects with no knowledge of Redis, RubyLLM
or Rails view concerns. The whole replay/bounding rule set is therefore testable
without any adapter. `Storage::Adapter` is a six-method port with two
implementations that share a contract test (`test/support/storage_adapter_contract.rb`),
which is the right shape.

**Views are genuinely componentised.** 17 partials averaging 13 lines; no partial
does more than render one thing. `_role_label`, `_title`, `_composer_error` are
three lines each, which is the correct size for a broadcastable Turbo target.

**Duplication is low.** The only real repetition is the `Settings` accessor
block (`settings.rb:30-80`), which is 15 near-identical two-line methods. That
is boilerplate-by-design and I would leave it — a metaprogrammed
`define_method` loop would be shorter and worse to read.

### What does not hold up

**Dead code.**
- `Storage::MemoryAdapter#index_add` writes `@index_expiry` (`memory_adapter.rb:46-47`)
  and nothing ever reads it. The index TTL is silently not implemented in the
  memory adapter, unlike the Redis one. It is either a missing feature or a
  leftover; as written it is a lie in the code.
- `capybara` and `selenium-webdriver` (`Gemfile:55-56`) are unused — no
  `test/system/` exists.
- `config/initializers/content_security_policy.rb` is 100% commented-out
  generator boilerplate, while `layouts/application.html.erb:10` renders a
  `csp_meta_tag` that emits nothing.

**A tautological assertion.** `test/services/assistant/turn_dispatcher_test.rb:29`
reads `assert_equal 1, calls.size + 1` after the queue has been drained by
`pop`. `calls.size` is always 0, so this passes unconditionally and asserts
nothing. The test above it (that the runner ran on a different thread) is the
one doing the work; this line should be deleted or replaced with a real
thread-identity assertion.

**Two hidden global singletons.** `ConversationRepository.instance`
(`conversation_repository.rb:15`) and `TurnDispatcher.pool`
(`turn_dispatcher.rb:25`) are both unsynchronised `||=` memoisations with public
writers. The test suite depends on `ConversationRepository.instance=` to swap in
the memory adapter, so production code carries a seam that exists only for
tests.

**One layer leak.** `Conversations::MessagesController` reaches into view helpers
for formatting (`messages_controller.rb:74-80` wrap `helpers.number_to_human_size`
and `helpers.number_with_delimiter`) to build user-facing refusal strings. Those
strings are presentation and belong in a partial or a locale file, not in a
controller private method.

### Top 3 refactors I would do with more time

1. **Serialise turns per conversation.** Today two rapid submissions to the same
   conversation start two independent `TurnRunner`s that each read history, each
   call the provider, and each append when they finish. The store cannot be
   corrupted (the RMW is atomic) but the *conversation* can be: replies can
   interleave, both turns can see the same pre-turn history, and both can pass a
   budget check that only one should. The fix is a short-lived Redis lock
   (`SET key NX PX`) keyed on the conversation id, taken in the controller and
   released by the runner, with a "still thinking" refusal when it is held. This
   is the single highest-value change in the list because it converts a
   correctness hazard into a UX message.

2. **Replace the `caller_runs` thread pool with a real queue, or bound its
   damage.** `turn_dispatcher.rb:30` uses `fallback_policy: :caller_runs`, so
   once 4 threads and 16 queue slots are full the 21st request runs the whole
   provider call *on the Puma request thread* — up to `ASSISTANT_REQUEST_TIMEOUT`
   (120 s) of a blocked worker out of only 3. Under load this is how the app
   stops responding. Failing fast with the existing `QUEUE_FULL_MESSAGE`
   constant (which is currently defined at `turn_dispatcher.rb:11` and **never
   used**) would be strictly better; a real job backend would be better still.

3. **Move the refusal/limit policy out of the controller into a
   `TurnPolicy` object.** `refusal_for` / `budget_refusal` / the two helper
   wrappers are 35 of the controller's 81 lines and mix three concerns (input
   validation, budget policy, message formatting). Extracting them would let the
   policy be unit-tested directly instead of through `ActionDispatch`, would
   remove the `helpers.` leak, and would give the per-conversation lock from (1)
   an obvious home.

---

## 3. Test coverage assessment

Command: `bin/rails test`

```
168 runs, 438 assertions, 0 failures, 0 errors, 0 skips
Line coverage:   667 / 667  (100.00%)
Branch coverage: 138 / 150  (92.00%)
```

Thresholds are enforced, not just reported (`test/test_helper.rb:14`:
`minimum_coverage line: 98, branch: 90`). Report at `coverage/index.html`.

Note on the 0 skips: `test/services/storage/redis_adapter_test.rb:18` skips its
three tests when no Redis is reachable at `REDIS_URL`. On this machine a Redis
was reachable, so they ran. **On a machine without Redis the entire production
storage path — `WATCH`/`MULTI`/`EXEC`, TTL, cross-instance visibility — is
silently untested and the run still reports green.** A reviewer running the
suite on a bare laptop will see "165 runs, 3 skips", not a failure.

### Weakest-tested area

**The JavaScript layer — it has no tests at all.** `composer_controller.js` (63
lines) and `autoscroll_controller.js` (37 lines) are 100 lines of behaviour with
zero coverage and zero tooling to cover them. SimpleCov reports 100% line
coverage because SimpleCov only sees Ruby. Concretely untested: Enter-to-send vs
Shift+Enter, IME composition guarding (`event.isComposing`), textarea auto-grow,
the suggestion-chip path, `history.replaceState` URL pinning after the first
message, the submit-button disabled toggle, the `MutationObserver` autoscroll and
its 120 px "don't fight the user" threshold. `capybara` and `selenium-webdriver`
are installed and unused, so the gap is a decision that was not carried out.

Second-weakest: `Storage::RedisAdapter` (see the skip caveat above) and
`TurnDispatcher` under real concurrency — the pool is tested for "runs off the
request thread" and "swallows exceptions", but never for saturation.

### Failure modes not covered by any test

- **Redis unavailable.** Verified by hand: pointing `REDIS_URL` at a dead port and
  calling `ConversationRepository#recent` raises `Redis::CannotConnectError`.
  Nothing rescues it, so the index page 500s. No test asserts any behaviour here.
- **`Storage::Adapter::ConflictError` escaping into a request.** The adapter is
  tested for raising it after 8 lost races (`redis_adapter_test.rb:44`), but no
  test covers what the *controller* does when `append_user_message` raises it —
  which is: nothing, it 500s.
- **Two concurrent turns in one conversation.** No test drives overlapping
  `TurnRunner`s. Interleaved token broadcasts, double budget passes, and
  out-of-order appends are all unexercised.
- **Thread-pool saturation / `caller_runs`.** No test posts more than
  `max_threads * 4` turns, so the request-thread-blocking path never executes.
- **Action Cable delivery.** Tests assert what was *broadcast* (via the test
  adapter), never that a browser subscribed to the signed stream *receives* it.
  The `turbo_stream_from` → `Turbo::StreamsChannel` link is only covered by the
  manual live probe recorded in this document.
- **A provider reply larger than `ASSISTANT_MAX_BYTES`.** No `max_tokens` is set
  anywhere, and no test feeds a multi-megabyte stream.
- **TTL expiry of the Redis index key** (the `zset` at `chat:conversations`)
  versus expiry of individual conversation keys — the two expire independently
  and no test covers the window where the index names keys that are gone.
  (`recent` uses `filter_map`, so this degrades quietly rather than crashing,
  but that is untested too.)
- **The 12 uncovered branches** (all defensive nil/empty guards):
  `arithmetic.rb:55`, `broadcaster.rb:58,72`, `chat_factory.rb:20`,
  `token_usage.rb:34`, `turn_dispatcher.rb:35,36`,
  `turn_runner.rb:59,71,79,92`, `conversation_repository.rb:125`.

---

## 4. Known defects and risks

Ordered roughly by how likely they are to bite.

1. **Every visitor sees every other visitor's conversations.** The sidebar is
   built from one global sorted set (`conversation_repository.rb:11`
   `INDEX_KEY = "chat:conversations"`, read by `#recent` at `:50-51`) with no
   per-session scoping. Verified live: a request from a brand-new cookie jar to
   `GET /` on the deployed stack returned links to three conversations created
   in earlier sessions, with their titles. The brief says "no authentication",
   but that is not the same as "publish everyone's chats to everyone". If this
   were ever exposed beyond localhost it is a data-disclosure bug. A
   session-scoped index (`chat:conversations:<session_id>`) would fix it without
   adding auth.

2. **Concurrency hazard: no per-conversation serialisation.** Two submissions to
   the same conversation race. `MessagesController#start_turn` appends the
   prompt and dispatches immediately; nothing prevents a second turn from
   starting while the first is streaming. Consequences: both turns replay the
   same pre-turn history (the second never sees the first's answer), token
   deltas from two turns append into two different pending bubbles in
   nondeterministic order, and both can pass the budget check. The Redis RMW
   keeps the *store* consistent; it does not keep the *conversation* coherent.
   Not tested. This is refactor (1) in section 2.

3. **The token budget is a pre-turn gate, not a cap.** `budget_exceeded?`
   (`conversation_repository.rb:85-87`) is checked before the turn only, and no
   `max_tokens` is configured on the chat anywhere in `app/`. A conversation at
   59,999 / 60,000 tokens will happily run one more full-length turn. Combined
   with (2), N concurrent submissions can all pass the same check. The budget
   bounds cost to roughly `budget + one turn`, per conversation.

4. **Unbounded cost across conversations.** The budget is per-conversation and
   conversation ids are client-chosen UUIDs. There is no rate limiting (no
   `Rack::Attack`, no throttling anywhere), so an unauthenticated client can
   create unlimited conversations and spend unlimited provider credit. This is
   the largest real-money risk in the app.

5. **Redis being unavailable takes the whole app down with a 500.** Reproduced:
   `Redis::CannotConnectError` from `ConversationRepository#recent` propagates
   out of `ApplicationController#sidebar_conversations` unrescued. Same for a
   `Storage::Adapter::ConflictError` from `append_user_message` in
   `MessagesController#create`. Provider failures degrade beautifully; storage
   failures do not degrade at all.

6. **The byte cap does not bind for a single oversized message.**
   `Conversation#bounded` (`conversation.rb:73`) stops dropping at
   `kept.size > 1`, so one message larger than `ASSISTANT_MAX_BYTES` (128 KiB
   default) is retained in full. User input is capped at 8 KiB
   (`messages_controller.rb:48`), but assistant replies are not capped at all —
   no `max_tokens` is set — so the stored blob is bounded only by whatever the
   model chose to emit.

7. **A crashed or restarted worker leaves an orphaned "…" bubble.** If the
   process dies between `broadcaster.pending` and `broadcaster.completed`, the
   pending bubble is never replaced; the user watches a spinner forever until
   they reload. There is no timeout, no client-side watchdog, and no recovery
   sweep. The same happens if `TurnRunner#call` returns early because the prompt
   was evicted by the message cap between the controller's write and the
   runner's read (`turn_runner.rb:27`).

8. **`compose.yaml` ships a weak default `SECRET_KEY_BASE`.**
   `compose.yaml:42` falls back to the literal
   `please-generate-me-with-bin-rails-secret`. `bin/docker-entrypoint:10` only
   fails when the variable is *empty*, so the fallback defeats it. Anyone
   running `docker compose up` without exporting a secret gets a published,
   publicly-known key base — which signs the session cookie *and* the Turbo
   Stream `signed-stream-name`, so a third party could forge a subscription to
   any conversation's stream. It should be `${SECRET_KEY_BASE:?...}` like the
   API key on the line above.

9. **No Content-Security-Policy.** `config/initializers/content_security_policy.rb`
   is entirely commented out, so `csp_meta_tag` in the layout emits nothing and
   no CSP header is sent (confirmed: `curl -D -` against the deployed app
   returns no `content-security-policy` header). Assistant output is escaped
   (`broadcaster.rb:61` `ERB::Util.html_escape`, `_message.html.erb:10` `<%= %>`)
   and Brakeman is clean, so I know of no live injection path — but there is no
   second line of defence for a demo that renders untrusted model output.

10. **`fallback_policy: :caller_runs` blocks Puma under load.** Described in
    refactor (2). Note also that `QUEUE_FULL_MESSAGE` (`turn_dispatcher.rb:11`)
    is defined and never referenced — the friendly overflow message that
    constant implies does not exist.

11. **Unsynchronised singleton initialisation.** `ConversationRepository.instance`
    (`:15`) and `TurnDispatcher.pool` (`:25`) use bare `@x ||= …`. Two threads
    hitting either on a cold worker can build two instances; for the pool that
    means two thread pools and a leaked one. Low probability, real.

12. **Token accounting is an estimate presented as a number.** `TokenUsage`
    falls back to `characters / 4` when the provider omits usage
    (`token_usage.rb:22`), and tool round-trips report usage per assistant
    message so the totals are approximate. The UI says "(approx.)", which is
    honest, but the budget gate is enforced against this approximation.

13. **`Storage::MemoryAdapter` index TTL is not implemented.** `@index_expiry` is
    written and never read (`memory_adapter.rb:46-47`), so the memory adapter's
    index never expires while the Redis one does. Since the shared contract test
    does not cover index expiry, the two adapters can drift here without any
    test noticing — which undermines the "the contract keeps them honest" claim
    the README makes.

14. **`allow_browser versions: :modern`** (`application_controller.rb:5`) returns
    406 to older browsers. Intentional Rails default, listed because it is a
    real user-visible failure mode with no UI explaining it.

15. **`config/master.key` and `config/credentials.yml.enc` exist in the
    workspace.** Both are correctly git-ignored (`.gitignore:28`) and nothing in
    the app reads the credentials, but the key file is present on disk. It
    should be deleted along with the unused credentials file.
