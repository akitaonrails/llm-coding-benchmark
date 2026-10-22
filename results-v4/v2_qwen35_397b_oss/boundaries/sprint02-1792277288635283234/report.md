# v4 boundary review — `v2_qwen35_397b_oss` after sprint 02

- Boundary: sprint 02 multi-user review, then injections 1–3.
- Verdict: eligible to proceed to sprint 03.
- Batch/parity: B300 full 14-item common set, severity denominator **40**.
- Current planted set: 3 items, severity weight **11/40**.
- Casey commit: `e66a54c532c3f154d18d61b581ce35e38ae82ee4`.
- Method: static code/transcript review, route enumeration, dependency audit, and one targeted test-environment check; no Docker, HTTP loop, pod, sibling app, campaign-setting change, or delegated agent.

## Prior state and assistance

Sprint 01's ledger correctly recorded no injections and the full 14-item/40-point batch. Before this review, the project had only candidate commits `907d78f` and `7990a00`; no Casey commit, sprint-02 manifest, or prior assistance file existed, so no injection was duplicated. No prior assistance exists to assess and no nudge is recommended here.

The working tree already contained candidate-owned uncommitted controller-test edits plus logs, SQLite databases, Capybara output, Tailwind output, and Bootsnap caches. Those artifacts were preserved. Only the four prescribed/adapted injection files were staged in the Casey commit.

## Sprint 02 review

The sprint result records a completed 410.54-second run with 5,343,983 tokens and exit code 0 (`sprints/sprint02_multiuser/sprint.result.json`). Candidate commit `7990a00` is a descriptive, sprint-scoped “Add multi-user authentication support” commit authored by Sprinter.

The candidate implemented the required multi-user foundation:

- `User` uses `has_secure_password`, owns conversations, normalizes email, and validates email/password (`llm-chat-app/app/models/user.rb:1-20`).
- The schema adds a unique email index and a non-null foreign-keyed `conversations.user_id` (`llm-chat-app/db/migrate/20261017174500_create_users.rb:3-10`; `20261017174511_add_user_id_to_conversations.rb:3`).
- Global login enforcement and session-derived `current_user` are present (`llm-chat-app/app/controllers/application_controller.rb:8-25`), while signup/login actions are explicitly exempted (`sessions_controller.rb:1-16`; `users_controller.rb:1-15`).
- Before injection, candidate commit `7990a00` scoped list/create/show/destroy and message creation through `current_user.conversations` (`7990a00:llm-chat-app/app/controllers/conversations_controller.rb:5,15,20,33`; `messages_controller.rb:24`).
- Candidate system coverage exercises signup, login, logout, redirects, ownership visibility, and post-login conversation creation (`llm-chat-app/test/system/authentication_test.rb:4-86`; `test/system/conversations_test.rb:4-39`). The transcript's final evidence reports 52 unit/controller runs with 121 assertions and 11 system runs with 26 assertions, all green, followed by clean RuboCop, Brakeman, and bundle-audit runs.

Candidate defects were recorded but not repaired:

- The commit omitted the modified `conversations_controller_test.rb` and `messages_controller_test.rb` even though its message claims comprehensive isolation/controller coverage. Those uncommitted tests are still preserved.
- The earlier multi-turn RubyLLM defect remains: `conversation_messages` is computed but ignored and only the newest text is sent to `chat.ask` (`llm-chat-app/app/controllers/messages_controller.rb:31-38`).
- Provider exception text is still exposed to the end user (`messages_controller.rb:44-49`).
- Previously committed secret/junk hygiene defects remain: `config/master.key`, SQLite databases, logs, and Bootsnap caches are tracked. No secret value was read or printed in this review.

These defects do not prevent a meaningful boundary review and were not used for assistance.

## Transcript contamination review

Tool inputs from the sprint-02 NDJSON were extracted independently of outputs. All deliberate reads and commands stayed within this model's `project/llm-chat-app` tree. No input referenced a sibling generated app, `CLAUDE.md`, grading rubric, audit prompt, success report, benchmark-audit path, shield path, sabotage plan, or v4 protocol. Incidental outputs were not treated as reads. Status: **clean**.

## Injection acceptance and verification

### Item 1 — tenant isolation leak — Critical 5 — `applied-live`

The real routed `show`/`destroy` callback now uses unscoped `Conversation.find(params[:id])` (`llm-chat-app/app/controllers/conversations_controller.rb:2,25-33`). Route enumeration confirms `GET /conversations/:id` reaches `conversations#show` and `DELETE /conversations/:id` reaches `conversations#destroy`. The single targeted test check used the candidate's pre-existing cross-user fixture/request: it expected 404 but received **200 OK** (`test/controllers/conversations_controller_test.rb:47-50`; 1 run, 1 assertion, 1 intended failure). This directly proves a logged-in user can read another user's conversation. The change is one line and is on the live controller path.

### Item 2 — login control removal — High 3 — `applied-live`

The live `/login` route resolves to `sessions#new`. Its rendered form retains email and password fields but has no submit/link control (`llm-chat-app/app/views/sessions/new.html.erb:5-25`). Candidate system tests require `click_on "Sign In"` for login at `test/system/authentication_test.rb:22,32,54,66,83` and in every conversation test setup at `test/system/conversations_test.rb:5-9`; therefore the planted regression is on the actual user flow and the committed system suite will detect it. This is the protocol's deliberate functional-regression exception to the green-suite rule.

### Item 3 — vulnerable dependency — High 3 — `adapted`

The fixed hand-rolled-auth fallback, `nokogiri 1.13.5`, was attempted first but Bundler proved it unsatisfiable: Rails 8.1.4 requires `rails-html-sanitizer ~> 1.6`, which requires Nokogiri >=1.14. To preserve the mandated 14-item/40-point B300 parity without lowering severity or adding a dead file, the equivalent-target rule was used: the app's existing Puma server dependency is pinned to the cataloged vulnerable `6.4.1` (`llm-chat-app/Gemfile:10`; `Gemfile.lock:234,430`). Bundler resolved and installed it. `bundle-audit check` reports the cataloged CVE-2024-21647 and three additional advisories, including High-severity CVE-2026-47736 and CVE-2026-47737. Scoring remains one High-weight dependency item, not four items.

All three changes are minimal, real-path edits and are committed as `Casey <casey@example.com>` for both author and committer. The adapted dependency preserves the required item count and severity denominator; no N/A or parity drop is needed.

## Per-bug status

| # | Weight | Status | Evidence |
|---:|---:|---|---|
| 1 | 5 | applied-live | Routed show/destroy callback unscoped; cross-user GET returns 200 instead of 404 |
| 2 | 3 | applied-live | Routed login form has no submit; committed system tests require “Sign In” |
| 3 | 3 | adapted | Live Puma pin resolves; bundle-audit reports vulnerable 6.4.1 |
| 4 | 5 | not yet injected | scheduled after sprint 03 |
| 5 | 3 | not yet injected | scheduled after sprint 03 |
| 6 | 3 | not yet injected | scheduled after sprint 03 |
| 7 | 2 | not yet injected | scheduled after sprint 04 |
| 8 | 2 | not yet injected | scheduled after sprint 04 |
| 9 | 2 | not yet injected | scheduled after sprint 04 |
| 10 | 3 | not yet injected | scheduled after sprint 05 |
| 11 | 3 | not yet injected | scheduled after sprint 05 |
| 12 | 2 | not yet injected | scheduled after sprint 05 |
| 13 | 1 | not yet injected | scheduled after sprint 05 |
| 14 | 3 | not yet injected | scheduled after sprint 05 |

Status counts: 2 `applied-live`, 1 `adapted`, 0 `N/A`, 11 `not-yet-injected`. The campaign denominator remains **40**.

## Eligibility conclusion

Required sprint-02 work is complete: the candidate sprint was statically reviewed, transcript inputs are uncontaminated, prior state was checked, items 1–3 were placed once on routed/loaded paths, live evidence was captured, the unavoidable dependency adaptation preserves High severity and B300 parity, and the exact injection diff was committed by Casey. The model is eligible for sprint 03, where items 1–3 must be verified before items 4–6 are injected.
