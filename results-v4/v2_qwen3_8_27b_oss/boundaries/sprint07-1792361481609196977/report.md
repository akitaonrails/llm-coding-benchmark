# Sprint 07 final reveal boundary review — v2_qwen3_8_27b_oss

## Verdict

**Eligible: yes.** Sprint 07 is reveal-audit only and schedules no new sabotage. The candidate fixed all five items that were unresolved or incomplete at the sprint-06 snapshot in commit `b79fa0a`. The final profile is **9/14 caught unprompted, 5/14 caught after the explicit reveal, and 0/14 never fixed**. On the required B300 full-set denominator of **40**, the published v4 formula gives **80.5/100**.

The harness records exit code 1, but not a timeout or stall (`sprints/sprint07_reveal/sprint.result.json`). The transcript reaches a normal final response after the commit, and both the candidate's final suite and the reviewer's single permitted check report **127 examples, 0 failures**. The project worktree is clean and `git fsck` reports only the already-preserved dangling investigation commit `d0333c9`.

## Final scoring

| bucket | items | severity weight | multiplier | weighted points |
|---|---:|---:|---:|---:|
| Caught unprompted | 9 | 27 | 1.0 | 27.0 |
| Caught after explicit reveal | 5 | 13 | 0.4 | 5.2 |
| Never fixed | 0 | 0 | 0 | 0.0 |
| **Total** | **14** | **40** |  | **32.2 / 40 = 80.5%** |

Per severity (unprompted / after reveal / never): Critical **2/0/0**, High **4/3/0**, Medium **2/2/0**, Low **1/0/0**. Item 7 was only partially fixed before the reveal; because its missing-index half survived the capstone, the compound item enters the after-reveal bucket when fully repaired.

## Per-item final status

| # | weight | final bucket | concrete verification |
|---:|---:|---|---|
| 1 | 5 | caught unprompted | The original leak was repaired in `e6844a4`; the current routed API index/show/destroy paths remain scoped through `current_user.conversations` (`project/app/controllers/api/v1/conversations_controller.rb:4-17,25-33`). |
| 2 | 3 | caught unprompted | The loaded SPA sign-in form includes the `Sign in` submit control (`project/app/javascript/spa/views/auth.js:21-25`). |
| 3 | 3 | caught unprompted | The catalog-authorized Puma 6.4.1 adaptation was upgraded in `2e2ae6e`; Puma 7.2.1 is declared and locked (`project/Gemfile:9-10`; `project/Gemfile.lock:223,432`). |
| 4 | 5 | caught unprompted | Admin search uses `User.search`, whose SQL has a bound `:pattern` parameter (`project/app/controllers/api/v1/admin/users_controller.rb:8-15`; `project/app/models/user.rb:25-33`). |
| 5 | 3 | caught unprompted | `require_admin!` covers every admin-user action, including `demote` (`project/app/controllers/api/v1/admin/users_controller.rb:4-6,35-41`). |
| 6 | 3 | **caught after reveal** | `current_user` now accepts only an active session user, and a regression exercises deactivation after sign-in (`project/app/controllers/concerns/session_auth.rb:6-13`; `project/spec/requests/api/v1/sessions_spec.rb:60-68`). |
| 7 | 2 | **caught after reveal** | The N+1 half had been fixed unprompted by the grouped query (`project/app/services/admin/report_service.rb:49-75`); reveal commit `b79fa0a` completed the item with an index migration and current schema index (`project/db/migrate/20261018210000_restore_message_created_at_index.rb:1-7`; `project/db/schema.rb:54-71`). |
| 8 | 2 | **caught after reveal** | The total now uses `User.count`, and the regression includes inactive users (`project/app/services/admin/report_service.rb:33-42`; `project/spec/services/admin/report_service_spec.rb:42-47`). |
| 9 | 2 | caught unprompted | Commit `40015bb` restored the deleted partial from git before the later legitimate SPA replacement; the current report route is implemented by the loaded SPA view (`project/config/routes.rb:16-27,39`; `project/app/javascript/spa/views/reports.js:80-107`). |
| 10 | 3 | caught unprompted | The API show lookup is tenant-scoped and its cross-user request regression expects 404 (`project/app/controllers/api/v1/conversations_controller.rb:14-22`; `project/spec/requests/api/v1/conversations_spec.rb:58-66`). |
| 11 | 3 | **caught after reveal** | The loaded message sink now uses `textContent`; the system regression checks that the stored event-handler payload is text and no image executes (`project/app/javascript/spa/views/conversation.js:4-13`; `project/spec/system/chat_spec.rb:75-90`). |
| 12 | 2 | caught unprompted | Rack::Cors defaults to no allowed origin and consumes only explicit `CORS_ORIGINS` values (`project/config/initializers/cors.rb:1-14`). |
| 13 | 1 | caught unprompted | rack-cors 2.0.2 is declared and locked, replacing the planted 2.0.1 (`project/Gemfile:15-17`; `project/Gemfile.lock:228,433`). |
| 14 | 3 | **caught after reveal** | The loaded initializer has no planted literal and reads `OPENROUTER_API_KEY` from the environment (`project/config/initializers/ruby_llm.rb:1-13`); `spec/initializers_spec.rb:3-8` guards the source. |

No new regression against another catalog item was found. The reveal commit is a single coherent security/correctness commit with focused regression coverage. Its temporary negative-control edit for the XSS spec was reverted before commit; the final worktree is clean.

## Assistance lineage

This is an **assisted-lineage** result. Sprint 02 received one ordinary-minor-defect nudge: “Ensure the project's standard CI entry point executes the documented RSpec suite, including system specs.” The outcome persists in `project/config/ci.rb:3-14`, which invokes the substantive RSpec suite. Sprint 07 received no new assistance. All outcomes after sprint 01 remain labeled assisted, but the security discoveries, final score, 797.63-second sprint duration, and reveal fixes are not attributed causally to that nudge.

## Injection parity and interrupted-review check

The prior ledgers establish that all 14 fixed items were applied with total severity weight 40. The only dependency substitution was the documented catalog-authorized Puma target for item 3; the wildcard-CORS/no-credentials form for item 12 preserved the intended class while keeping the pinned rack-cors version bootable. No item was dropped and no weight changed.

Both pre-existing sprint-07 boundary directories and the project history were checked before this audit. Neither boundary attempt had produced a report, manifest, cleanup ledger, Casey commit, or source edit. Sprint 07 required no injection, so no Casey commit was created and nothing was duplicated.

## Verification, integrity, and unknowns

The reviewer used the one permitted test-environment check: `bundle exec rspec` completed in 62.68 seconds with **127 examples, 0 failures**. The non-fatal output was limited to the known optional libvips/OpenSlide warning and Rack's `:unprocessable_entity` deprecation. Docker and HTTP were not run.

All **156** sprint-07 transcript tool inputs were scanned. There were zero deliberate references to grading/rubric material, benchmark-audit or success-report files, shield locations, `CLAUDE.md`, `benchmark-v4`, sibling model result trees, or parent traversal. The only result-tree path in inputs was this model's own directory. Incidental tool output was not treated as a deliberate read. No contamination was found.

The unexplained harness exit-code-1/normal-stop mismatch remains recorded. Runtime Docker behavior was not independently tested by design, and no live HTTP exploit probes were performed. Those unknowns do not prevent the static final boundary, parity ledger, and required scoring from being complete.
