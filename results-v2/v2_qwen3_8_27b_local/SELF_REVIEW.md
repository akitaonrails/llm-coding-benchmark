# SELF_REVIEW — `v2_qwen3_8_27b_local/project` (phase 3)

Scope: honest, evidence-based verification of the Rails app in this workspace
against goals G1–G14 in `prompts/benchmark_prompt_v2.txt`. Every verdict below
was re-checked against the actual code (and the installed `ruby_llm 1.16.0` gem
source) as of this review. Commands were run in the project root with `ruby 4.0.6` / `Rails 8.1.3.1`.

Summary: 4 PASS, 4 PARTIAL, 6 FAIL. The most serious finding is that the
streamed assistant reply is **not rendered live in the DOM at all** (G4), on top
of **zero tests** (G11) and **no** token budget / title schema / Docker / README
(G8, G9, G13).

---

## 1. GOAL VERIFICATION TABLE

| ID | Verdict | Evidence |
|----|---------|----------|
| G1 | **PARTIAL** | Newest Ruby `4.0.6` (`.ruby-version:1`) and Rails `8.1.3.1` (Gemfile.lock). `action_mailer`, `active_job`, `active_storage` are commented out (`config/application.rb:7,9,12`). **But** `active_record/railtie` is required (`config/application.rb:7`) and loaded the persistence layer (SQLite + AR models `Conversation`, `Message`) — a direct violation of the explicit "No Active Record" clause. |
| G2 | **PASS** | Tailwind v4 build present (`app/assets/builds/tailwind.css:1`), componentized with Rails partials (`app/views/messages/_*.erb`), one Stimulus controller (`app/javascript/controllers/chat_controller.js`) + separate Stimulus/Turbo imports (`app/javascript/application.js:1-2`, `config/importmap.rb`). No single-file CSS/JS dump (`app/assets/stylesheets/application.css` is the 10-line Propshaft manifest only). |
| G3 | **PASS** | `ruby_llm (1.16.0)` latest (Gemfile:24, Gemfile.lock). OpenRouter + `anthropic/claude-sonnet-4.6` as default, overridable by `RUBYLLM_MODEL` (`config/initializers/ruby_llm.rb:4-8`). Verified via `bin/rails runner`: `model=anthropic/claude-sonnet-4.6, key_set`. |
| G4 | **FAIL** | Per-token deltas *are* broadcast (`app/services/llm/session.rb:73-81` → `render_append` → `turbo_stream.append "message_#{id}_content"`), **but the assistant bubble is never inserted into `#messages`.** Only the *user* bubble is appended (`session.rb:66` → `_message.turbo_stream.erb:3` `append :messages`). The assistant uses `replace` on `message_#{assistant_id}` (`session.rb:67,86` → `_clear`/`_message_replace`), and Turbo's `append`/`replace` no-op when the target `getElementById` is null (confirmed in `turbo-rails` `StreamElement#targetElementsById` + `StreamActions`). Net effect: the assistant answer does **not** appear incrementally; it only shows after a full page reload (initial render `_bubble.html.erb`). |
| G5 | **PARTIAL** | Payload logic is correct: `conversation.history` is captured *before* the user row is created (`session.rb:60`), `build_chat` replays only those prior turns (`session.rb:138-144,62`), and `chat.ask(user_text)` adds the new prompt exactly once (`session.rb:73`). **But** the required "unit test that asserts the exact outgoing message array for a multi-turn conversation" does not exist — there are no tests at all (see G11). |
| G6 | **PARTIAL** | Restart survival + multi-worker share are satisfied: persistence is DB-backed, not process-local (`app/models/conversation.rb`, `config/database.yml` with WAL + `busy_timeout: 30000`); no in-process store. **But** no bounding — grep for `budget|ttl|cap|prune|limit` found nothing in `app/models`, `app/services`, `app/controllers`. No message-count cap, no byte cap, no TTL, no pruning. |
| G7 | **PASS** | Exactly two RubyLLM tools registered: `chat.with_tools(CalculatorTool.new, ServerTimeTool.new)` (`session.rb:141`). Both inherit `RubyLLM::Tool` with `description`/`param`/`execute` (`app/tools/server_time_tool.rb:2-8`, `app/tools/calculator_tool.rb:19-41`). Verified against gem source that `with_tools`, `before_tool_call`, `after_tool_result`, `ToolCall#name/#arguments` all exist. Live "assistant answers via tool" behavior was **not** runtime-verified (no LLM round-trip executed). |
| G8 | **FAIL** | No structured-output/schema usage anywhere: `grep -rn "with_schema\|as_schema\|schema" app/services/llm/session.rb` → empty. The title is set by plain truncation of the first user message (`Conversation#rename_from_first_message!`, `app/models/conversation.rb:32-39`), not the RubyLLM schema API, and only when the title is still `"New chat"`. |
| G9 | **FAIL** | No token budgeting exists: no env var, no token accumulation, no per-conversation budget check, no "refuse further turns" path. `grep -rn budget app config` → no app hits. |
| G10 | **PARTIAL** | ✓ system prompt via `with_instructions` (`session.rb:140`). ✓ every provider `StandardError` is rescued and a friendly message is written/broadcast (`session.rb:88-94`; controller thread also rescues, `chat_controller.rb:34-36`). ✗ **No missing-API-key preflight** — a missing key surfaces only as the generic "model provider returned an error" after the first send, not as an actionable "set `OPENROUTER_API_KEY`" state. ✗ a failed turn's assistant row is updated to the error string (role `assistant`) and **is replayed to the provider next turn** (`conversation.history`), so "failed turns are never stored into replayed history" is violated. Also the degraded state is only visible after reload (same DOM gap as G4). |
| G11 | **FAIL** | `bin/rails test` → `0 runs, 0 assertions, 0 failures, 0 errors, 0 skips`. `find test -name "*_test.rb"` → 0 files (only `test/test_helper.rb`). SimpleCov is **not wired**, not required in `test_helper.rb`, and no `coverage/` output exists (`grep -rn simplecov test Rakefile` → empty). |
| G12 | **FAIL** | Brakeman clean (0 warnings, `bin/brakeman`). bundler-audit clean (`No vulnerabilities found`, exit 0). **RuboCop fails**: `bin/rubocop` exits 1 with **22 offenses** (11× `Layout/SpaceInsideArrayLiteralBrackets` autocorrectable + related), e.g. `app/tools/calculator_tool.rb:92,107,109`. "All pass clean" is false. |
| G13 | **FAIL** | No `Dockerfile`, no `docker-compose.yml`/`compose*.yml` anywhere in the workspace (`find` → empty). `README.md` is the untouched Rails template boilerplate (no setup / env vars / run instructions). Production config *presumes* a compose/Redis setup it does not ship (`config/cable.yml` prod → redis; `production.rb` comments reference compose). |
| G14 | **PASS** | No authentication routes/controllers. No secret is committed: the whole `results-v2/v2_qwen3_8_27b_local/project` dir is gitignored by the parent repo (`git add -n config/master.key` → "The following paths are ignored…"), no `.env` present (`find . -name ".env*"` → empty), no key/paste of the key in source, README, or logs. Caveat in §4: `config/master.key` (32 bytes) exists on disk and is protected only by that ignore rule. |

Score: 4 PASS / 5 PARTIAL / 5 FAIL.

---

## 2. CODE QUALITY ASSESSMENT

Strong points: small, readable files (largest `session.rb` 176 lines, others ≤139);
good domain naming (`Conversation`, `Message`, `Llm::Session`, `Calculator::SecurityError`
vs `ArithmeticError` in `app/tools/calculator_errors.rb:7-11`); a clean
`Transport` seam (`session.rb:35-49`) that lets tests capture broadcasts without a
live Action Cable server; the calculator uses a hand-written parser instead of
`eval` (`app/tools/calculator_tool.rb:9-18,61-111`), which is the correct call.

Weaknesses (with citations):

- **Single responsibility — `Llm::Session#send_and_stream!`** (`session.rb:59-94`)
  does six jobs in one method: row creation, renaming, first broadcast, chat
  construction, tool-event tracking, the streaming loop, finalization, and error
  handling. It is the natural home for a bug (and contains the G4 gap).
- **Duplication — view rendering.** Five near-identical wrappers
  (`render_append_message`, `render_final`, `render_clear`, `render_append`,
  `record_tool_event`, `session.rb:105-174`) all repeat
  `ApplicationController.render(partial: …, formats: [:turbo_stream])`. The wire
  name `"conversation-#{id}"` is also constructed in three places
  (`session.rb:101,167`) and re-derived in `ConversationChannel#conversation_wire_name`
  (`app/channels/conversation_channel.rb:26-28`). One helper would remove the spread.
- **Dead code.** `Message.scope :history` (`app/models/message.rb:21`) is unused —
  `Conversation#history` builds its own `where(role: …)` query (`conversation.rb:28`).
  `Conversation#newest_position` (`conversation.rb:41-43`) and
  `Message#streaming_target` (`message.rb:41-43`) are defined but never called
  (`grep` for both across `app/` → only their definitions).
- **Coupling.** A *service* layer reaches into `ApplicationController.render` to
  produce view HTML (`session.rb:105-174`), and renders partials directly (`record_tool_event`
  also `transport.broadcast`s inline). The session is coupled to the view layer and
  to view markup IDs (`message_#{id}`, `message_#{id}_content`, `_tools`).
- **Inconsistent data shapes.** Tool events are stored as both symbol-keyed hashes
  written by `record_tool_event` (`session.rb:164-174`) and read back by
  `ApplicationHelper#tool_event_label` (`app/helpers/application_helper.rb:5-10`);
  `tool_event_list` does `Array(tool_events)` to normalize (`message.rb:31-33`) —
  a JSON round-trip boundary that is easy to break.

**Top 3 refactors, if there were more time:**

1. **Fix and isolate the streaming lifecycle (G4).** Split `send_and_stream!` into
   discrete steps (persist-user, open-assistant-shell, stream, finalize, degrade)
   and make the assistant bubble *append*ed to `#messages` before any fragment
   streams (mirroring the user bubble). This both fixes the live-render defect and
   shrinks the method.
2. **Deduplicate render + wire-name construction.** One `render_stream(partial:, **locals)`
   and one `wire_name` shared by the session and the channel; removes ~40 lines of
   duplicated `ApplicationController.render`/id-building and the three-way id drift
   (including the `conversation-list` vs `conversation_list` mismatch, §4).
3. **Extract view rendering out of the service.** Move the Turbo Stream HTML
   production into a small presenter/view object (or let the controller render),
   keeping `Llm::Session` focused on model + provider orchestration; then delete
   the dead `Message.history` scope, `newest_position`, and `streaming_target`.

---

## 3. TEST COVERAGE ASSESSMENT

- **SimpleCov line / branch %: not available — SimpleCov is not wired.**
  It is in the `:test` group (Gemfile:52) but is never `require`d
  (`test/test_helper.rb` has no SimpleCov setup, no `.simplecov` file, no
  `coverage/` directory produced). So **no coverage report can be reported**.
- **Actual test results:** `bin/rails test` → `0 runs, 0 assertions, 0 failures,
  0 errors, 0 skips`. There are **zero** `*_test.rb` files.
- **Weakest-tested area:** the entire codebase, but the two with the most logic and
  the least testing are (a) `CalculatorTool` (`app/tools/calculator_tool.rb`) — a
  139-line recursive-descent parser handling precedence, parentheses, negative
  factors, div/mod-by-zero, and numeric formatting, all untested; and (b)
  `Llm::Session#send_and_stream!` + `build_chat` — the exact multi-turn
  "sent exactly once" contract (G5) that the brief explicitly asked to assert.
- **Failure modes covered by no test (all of them):** missing/invalid API key;
  provider error mid-stream and the error-path persistence (G10); tool
  call → result round-trip and `tool_events` recording; streaming chunk
  handling; calculator edge cases (division by zero, malformed expression,
  unbalanced parentheses, empty, non-numeric); multi-turn replay; the
  `reply_in_progress?` lock; `find_or_create_by_client!` idempotency; and the
  turbo-stream DOM behavior (G4) which has no test of any kind.

---

## 4. KNOWN DEFECTS AND RISKS

1. **[HIGH] Assistant reply never renders live (G4).** Only the user bubble is
   `append`ed into `#messages` (`session.rb:66`); the assistant bubble is only
   referenced by `replace` on a nonexistent id, so every streamed fragment and the
   final replace are no-ops in the DOM. The answer appears only after a full reload.
   Same root cause makes the "degraded" error state (G10) invisible until reload.
2. **[HIGH] Enter-to-send is broken.** `submitKeypress` calls
   `this.inputTarget.form.requestSubmit()` (`app/javascript/controllers/chat_controller.js:42-47`)
   but there is no Stimulus `submit` action — it triggers a *native* local-form
   POST (`form_with …, local: true`, `app/views/chat/index.html.erb:28-29`), navigating
   the browser to the empty 202 response and discarding the page. Only the button
   `click → sendMessage` (fetch) path works.
3. **[HIGH] Unbounded persistence (G6).** No message/byte cap, no TTL, no pruning;
   SQLite grows indefinitely. No retention at all.
4. **[MED] No missing-key preflight (G10).** A cold start without
   `OPENROUTER_API_KEY` gives the generic provider-error message only after the
   first send; the key-absent case is not detected or surfaced actionably.
5. **[MED] Failed assistant turns are replayed.** On provider error the empty
   assistant row is set to an error string and persisted with role `assistant`
   (`session.rb:90-93`), so the next turn replays that error text to the provider.
6. **[MED] Concurrency race on `position` and on the in-progress lock.**
   `position: history.size + 1/+2` is computed non-atomically
   (`session.rb:62-63`); two near-simultaneous `create` requests for the same
   conversation both pass `reply_in_progress?` (`chat_controller.rb:22`) before
   either inserts, then collide on the unique `(conversation_id, position)` index —
   surfacing as an `ActiveRecord` exception logged in the worker thread, not a clean
   UI state. `reply_in_progress?` is a 5-minute age heuristic on empty assistant
   rows (`conversation.rb:49-57`); a dead worker mid-stream can therefore block
   fresh turns for up to ~5 minutes.
7. **[MED] No Docker / no README (G13).** Production config assumes a Redis-backed
   Action Cable plus a compose flow that is not shipped; there is no documented way
   to run the app as written.
8. **[MED] CI is not actually running.** `bin/ci`, Brakeman, RuboCop, bundler-audit,
   and the `bundler-audit.yml` config exist, but there are **no** `.github/workflows`
   or any CI yml in the workspace — nothing is wired to run them, and RuboCop is
   currently red (G12).
9. **[MED] `master.key` on disk.** `config/master.key` exists (32 bytes) and relies
   solely on the parent repo's directory-level ignore. If that ignore rule is
   relaxed or the project is snapshotted, the credential and encrypted credentials
   would leak. It is not committed today.
10. **[LOW] `final_text` fallback ordering.** `final_text = chat.messages.last&.content`
    with a `buffer` fallback (`session.rb:83-84`): after a tool round-trip,
    `chat.messages.last` is not guaranteed to be the assistant text; the empty-string
    guard covers the common case but not every shape.
11. **[LOW] No CSS/JS asset versioning for the Tailwind build.**
    `app/assets/builds/tailwind.css` is checked in; `Procfile.dev` runs the watch task,
    but a stale build would silently ship in production with no guard.
12. **[LOW] `client_id` user-controlled with no format/length validation beyond the
    DB column** (`app/controllers/conversations_controller.rb:24-26`). Fine for a
    demo (UUID default, `SecureRandom.uuid` at `conversations/index.html.erb:24`),
    but no sanitization.

No test exercises any of the above, so none of these defects would currently be
caught by the suite.
