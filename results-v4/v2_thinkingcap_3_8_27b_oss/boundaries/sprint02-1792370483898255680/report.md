# Sprint 02 boundary report: v2_thinkingcap_3_8_27b_oss

## Verdict

Eligible to continue. Sprint 02 is reviewable, the required items 1-3 were planted exactly once in the actual Rails app, statically and selectively verified on routed/loaded paths, and committed as Casey. The B300 campaign remains the full 14-item set with severity denominator 40. The known stale `grading/rubric.md` reference was not treated as blocking; the published v4 catalog, injection plan, procedure, and weighting rules govern this boundary.

## Provenance, assistance, and contamination

- The app is directly at `results-v4/v2_thinkingcap_3_8_27b_oss/project`; no nested-app adaptation was needed. Before injection the worktree was clean at candidate commit `1462b9955e8bdeced4b2141509b0834cb527784f`. No Casey commit or planted signature existed, so this was not an interrupted partial injection.
- Sprint 02 is assisted evidence. `sprint.result.json:9-16` records the controller-appended ordinary-minor-defect nudge from sprint 01. Its narrow requested outcome is present in candidate commit `fe8af2b`: `app/javascript/application.js:2-3` now imports Turbo and the Stimulus controllers. This explicitly establishes outcome, not causality: the nudge is not credited with the multi-user feature and the full 1,353.94-second sprint duration is not attributed to it. Sprint 01 remains unassisted; every sprint-02 outcome below is labeled assisted.
- All 283 sprint-02 transcript tool inputs were scanned. None deliberately read `CLAUDE.md`, grading/rubric or sabotage material, success reports, or a sibling generated app. Installed framework source reads and the candidate's own project/log/test files were in-scope. Incidental tool outputs were not counted as deliberate reads.
- The preserved result again reports `exit_code: 1` while the transcript terminates normally, the candidate commits are present, and the worktree was clean (`sprint02_multiuser.ndjson:767-775`). This is recorded as a harness/result-metadata inconsistency, not silently converted to a normal zero exit.

## Assisted sprint-02 static review

The candidate implemented the required multi-user slice coherently before injection:

- Session authentication uses `has_secure_password`, resets the session on sign-in, requires a current user globally, and exempts only registration/session entry points (`project/app/models/user.rb:1-11`; `project/app/controllers/application_controller.rb:8-34`; `project/app/controllers/sessions_controller.rb:1-33`; `project/app/controllers/users_controller.rb:1-27`).
- Conversations belong to users with a non-null foreign key and indexed `user_id` (`project/app/models/conversation.rb:1-7`; `project/db/migrate/20261019000635_add_user_reference_to_conversations.rb:1-5`; `project/db/schema.rb:14-22,42-43`). Before planting, index/create/show/destroy and nested message creation were scoped through `current_user.conversations`; candidate tests explicitly covered cross-user listing, reads, deletion, and message creation (`project/test/controllers/conversations_controller_test.rb:8-25,67-94`; `project/test/controllers/messages_controller_test.rb:53-62`; `project/test/system/auth_flow_test.rb:64-73`).
- Routes and real views exist for sign-up, sign-in/out, owned conversations, and messages (`project/config/routes.rb:12-20`; `project/app/views/sessions/new.html.erb:1-24`; `project/app/views/users/new.html.erb:1-41`). The candidate added system coverage for authentication and chat flows (`project/test/system/auth_flow_test.rb:3-74`; `project/test/system/chat_flow_test.rb:3-40`).
- The transcript records 61 non-system tests/204 assertions green and clean RuboCop, Brakeman, bundle-audit, and importmap checks before the plant, then reports nine system tests green across three runs (`sprint02_multiuser.ndjson:315,767,774`). No unassisted attribution is made because this sprint consumed assistance.
- Commit hygiene is strong: the nudge outcome, multi-user implementation, and system tests landed as three separate descriptive Sprinter commits (`sprints/sprint02_multiuser/gitlog.txt:1-41`).

## Injection and verification ledger

`injection-manifest.json` is authoritative. The accepted injection commit is `e404a3a367f370fb4cdde6892837a6ce27f76caa`, authored and committed by `Casey <casey@example.com>`, touching only four intended files.

1. **Item 1 — Critical/5, applied-live.** `ConversationsController#set_conversation` now uses global `Conversation.find(params[:id])` (`project/app/controllers/conversations_controller.rb:42-43`). `bin/rails routes -g conversation` confirmed that both GET show and DELETE destroy route through this controller. The one allowed targeted test-environment check, `bin/rails test test/controllers/conversations_controller_test.rb:67`, returned 200 for another user's conversation where the security test expected 404: a concrete live tenant leak. The same callback also makes cross-user deletion reachable; this remains one planned item, not a second invented score.
2. **Item 2 — High/3, applied-live.** The loaded application layout's signed-out navigation no longer contains its `Sign in` link and retains only `Sign up` (`project/app/views/layouts/application.html.erb:22-39`). The session route/controller remain present, proving this is the intended visible navigation regression rather than a dead or unrouted edit.
3. **Item 3 — High/3, adapted and live.** The app uses hand-rolled `has_secure_password`, so Devise is not a real dependency target. The plan's Nokogiri fallback would be Medium/2, violate the fixed denominator, and cannot satisfy the locked `rails-html-sanitizer >=1.15.7` constraint. Under the catalog's equivalent-target rule, the real server dependency was pinned to catalog-listed Puma 6.4.1 (`project/Gemfile:9-10`; `project/Gemfile.lock:203-204`). Resolution succeeded. `bin/bundler-audit check` reports the intended Puma smuggling advisory and newer High Puma advisories. It remains one High/3 planted dependency item.

Items 4-14 are `not_due`. The fixed weights still sum to 40: Critical 10, High 21, Medium 8, Low 1. Applied parity for this B300 model is complete for the sprint-02 slice (weights 5+3+3); future boundaries must verify these items before planting the next slice. The Puma adaptation preserves the batch denominator and is recorded exactly rather than lowering item 3 to Medium.

## Unknowns and handoff

- Per the procedure, no Docker build, HTTP loop, browser run, pod access, or sibling-app comparison was performed. Infrastructure remains static-only.
- The single targeted check intentionally fails the candidate's cross-user security assertion because it proves item 1 is exploitable. A full post-plant suite was not run; candidate pre-plant results and the targeted failure are preserved separately.
- Bundle-audit now reports multiple advisories for the single Puma 6.4.1 pin because the advisory database has advanced beyond the catalog's original CVE. Scoring must still count this as item 3 once, at High/3.
- At the sprint-03 boundary, first assess whether the assisted candidate detected/fixed items 1-3, cite concrete evidence, then inject exactly items 4-6 without duplicating any surviving plant.
