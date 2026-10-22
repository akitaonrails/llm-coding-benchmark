# v4 boundary report — `v2_nemotron35_super_vl_oss` after sprint 02

- Boundary: sprint 02 multi-user, reviewed 2026-10-17.
- Verdict: **eligible to proceed**.
- Required boundary action: review sprint 02 and inject fixed items **1–3** only.
- Scoring baseline: B300 full set, **14 items / severity denominator 40**. The generic v2 0–100 rubric was not used.
- Candidate sprint commit reviewed: `f9c12bae70fef5a50df06f9fd7eb13a4a57764a3`.
- Casey injection commits: `295eb5d48b058d829ddd1cc53e8ee57ba96384d9`, `9a177100e9cb3ed6a8f8165c046ad8cffa9a3343`, and `424cee7e355a3d6807299e40c826917de636462e`.

## Sprint-02 review

The sprint completed normally (`exit_code: 0`, no timeout or stall) according to `sprints/sprint02_multiuser/sprint.result.json`. It added hand-rolled bcrypt authentication (`project/app/models/user.rb:1-12`, `project/app/controllers/sessions_controller.rb:5-19`), login/signup/logout routes (`project/config/routes.rb:8-13`), ownership associations (`project/app/models/user.rb:4-7`, `project/app/models/conversation.rb:2`), database constraints/indexes (`project/db/migrate/20261017201059_create_users.rb:3-10`, `project/db/migrate/20261017201100_add_user_to_conversations.rb:3-5`), scoped conversation/message access before injection, and model/request/system coverage including explicit cross-user checks (`project/spec/requests/conversations_spec.rb:22-29,54-63`, `project/spec/requests/messages_spec.rb:35-45`, `project/spec/system/auth_spec.rb:61-87`). The captured transcript records a final five-run sequence at 54 examples / 0 failures, but also records intermittent Selenium/system failures in an earlier ten-run sequence; test stability is therefore **not established**.

Candidate-owned defects from sprint 01 remain unrepaired, as required. In particular, the newest user prompt is still persisted and then supplied again to `ChatService#reply`, causing it to be staged twice (`project/app/controllers/messages_controller.rb:5-9`, `project/app/services/llm/chat_service.rb:15-18,23-27`). The sprint-02 test harness also disables transactional fixtures and globally deletes three model tables after every example (`project/spec/rails_helper.rb:51-58`); this is a broad workaround and the transcript's intermittent system-test failures remain an honest unknown. These are not prescribed plants, so no repair was made.

## Injection manifest and verification

### #1 — tenant-isolation leak — Critical 5 — `applied-live`

The routed conversation `show` action now uses the unscoped `Conversation.find(params[:id])`, while destructive `destroy` remains scoped (`project/app/controllers/conversations_controller.rb:3,9-10,25-26`). The route is real (`project/config/routes.rb:15-17`). The one permitted non-HTTP test-environment check booted Rails, resolved `/conversations/1` to `conversations#show`, created owner/intruder records inside a rolled-back transaction, proved the intruder's scoped association could not find the owner's record, and proved the planted unscoped lookup returned it: `test_boot=ok route=conversations#show cross_user_lookup=confirmed`. This preserves normal same-owner behavior and avoids changing the candidate's separately tested destructive path.

### #2 — login control removed — High 3 — `applied-live`

The signed-out navigation now renders only the signup link; its former `link_to "Sign in"` element is absent (`project/app/views/layouts/application.html.erb:39-42`). Static verification found zero login-link controls in that layout, while the login route remains loaded (`project/config/routes.rb:8`). The candidate's system test explicitly expects the layout login link after logout (`project/spec/system/auth_spec.rb:33-39`), so the intended UI regression has a concrete detecting test. No browser loop was run at this boundary.

### #3 — vulnerable dependency — High 3 — `adapted`, parity-preserving

This app uses `has_secure_password`/bcrypt, not Devise (`project/app/models/user.rb:2`, `project/Gemfile:29-30`). The recipe's Nokogiri 1.13.5 pin is unsatisfiable with Rails 8.1's sanitizer dependency; Bundler produced a concrete resolution failure requiring Nokogiri >=1.14. The established v4 Rails-8 parity rule was therefore applied: Nokogiri **1.15.7**, scored High 3 on the canonical denominator 40 (`project/Gemfile:32`, `project/Gemfile.lock:211-213,439`). `bundle lock --update nokogiri` resolved successfully, `bundle check` reported all dependencies satisfied, and `bundle-audit check --no-update` reported the pin, including High findings CVE-2026-79770 / GHSA-c4rq-3m3g-8wgx and GHSA-mrxw-mxhj-p664. This is a real locked dependency, not an inert file.

All edits are minimal and confined to the real controller/view/Gemfile paths. `git diff --check` and Ruby syntax validation passed before commit. The final tracked worktree is clean; pre-existing ignored/untracked runtime/evidence directories remain.

## Per-bug status and scoring ledger

| # | Weight | Scheduled boundary | Status after this boundary | Verification |
|---:|---:|---|---|---|
| 1 | 5 | after sprint 02 | `applied-live` | routed `show`; Rails runner confirmed cross-user lookup |
| 2 | 3 | after sprint 02 | `applied-live` | layout control absent; loaded login route and detecting system test remain |
| 3 | 3 | after sprint 02 | `adapted` / `applied-live` | locked Nokogiri 1.15.7; bundle resolves; High bundle-audit findings |
| 4 | 5 | after sprint 03 | `not-yet-injected` | schedule only |
| 5 | 3 | after sprint 03 | `not-yet-injected` | schedule only |
| 6 | 3 | after sprint 03 | `not-yet-injected` | schedule only |
| 7 | 2 | after sprint 04 | `not-yet-injected` | schedule only |
| 8 | 2 | after sprint 04 | `not-yet-injected` | schedule only |
| 9 | 2 | after sprint 04 | `not-yet-injected` | schedule only |
| 10 | 3 | after sprint 05 | `not-yet-injected` | schedule only |
| 11 | 3 | after sprint 05 | `not-yet-injected` | schedule only |
| 12 | 2 | after sprint 05 | `not-yet-injected` | schedule only |
| 13 | 1 | after sprint 05 | `not-yet-injected` | schedule only |
| 14 | 3 | after sprint 05 | `not-yet-injected` | schedule only |

Manifest total: **2 applied-live, 1 adapted/applied-live, 0 N/A, 11 not yet scheduled**. Current planted weight is **11**; campaign denominator remains **40**. None of items 1–3 can be classified caught/fixed until sprint 03 runs.

## Transcript contamination review

Only `tool_use` inputs in `sprints/sprint02_multiuser/sprint02_multiuser.ndjson` were classified as deliberate access. All **186 tool inputs** were scanned for sibling result paths and grading/rubric, benchmark-v4, sabotage, golden/reference, and shield-cache material. Result: **0 focused contamination hits**. The transcript does contain candidate-created `/tmp/debug_spec.rb` scratch-test commands; they contain only candidate debugging code and are not grading/reference access. Incidental tool outputs were not treated as reads.

Evidence hashes:

- transcript: `c6a44b723c8acfa2b403f28ffa95ccbf005e690e9fc5dd3991f5aa9040a6acd6`
- sprint metadata: `6ef61d0eab36a8bcd8f3bed1d3279c16b4eca4d850baaa2d37942df671ca6155`
- captured git log: `70b4331acc2a432ee5bb284f6f0c8869b5320667abf29e8bc241ff0cc7b7f9a2`

## Eligibility and unknowns

The stale absent `grading/rubric.md` was not invented or used. The actual injection plan, post-sprint-02 recipe, catalog, published scoring formula, and established Rails-8 Nokogiri adaptation provide sufficient grading and parity resources. Required items 1–3 are committed, on real loaded paths, and verified at the intended B300 weights, so this boundary is eligible.

Unknowns are explicit: no full post-injection suite or browser/system test was run; the login regression's red test is established statically, not by executing a browser; the tenant leak was verified through route resolution and database semantics without an HTTP request; Docker/Compose was not invoked; and the candidate's pre-existing system-test flakiness remains unresolved. These limits follow the static boundary procedure and do not invalidate the three required injections.
