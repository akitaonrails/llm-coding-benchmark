# Sprint 06 boundary review — `v2_swift_1_5_27b_oss`

- Verdict: **eligible**. This audit-only boundary is complete; no new sabotage was planted.
- Reviewed app: `results-v4/v2_swift_1_5_27b_oss/project` directly. No sibling generated app was inspected.
- Campaign: B300 full **14-item / severity-denominator 40** set; all prior Casey commits and adaptations remain accounted for.
- Capstone result: **12/14 fixed unprompted, weight 34/40 (85%)**. Items 5 and 6 remain present for the explicit sprint-07 reveal.

## Assistance and sprint outcome

This remains an **assisted** run because the one sprint-01 nudge asked the candidate to retain the newest messages in capped LLM history. That correction and its regression test remain at `app/services/chat_service.rb:48-61` and `test/services/chat_service_test.rb:29-45`. Sprint 06 received no further assistance (`assistance: null`, `assisted_run: true`). The original unassisted evidence remains preserved, every later outcome is labeled assisted, and neither causality nor the full **957.33-second** sprint duration is attributed to the earlier nudge.

The candidate fixed all five sprint-05 plants in commit `405de3891`: it restored API ownership scoping, used `textContent`, removed allow-all CORS and rack-cors 2.0.1, and restored the API key to `ENV`. Commit `216f017` completed the API-backed frontend refactor. Candidate-preserved transcript evidence then reports **124 runs / 393 assertions** plus **13 system runs / 72 assertions**, all green, with RuboCop, Brakeman, and bundler-audit clean.

The production-hardening work is substantive but incomplete as delivered. The current worktree has 11 modified tracked files and no commit for the Docker/config/test changes. The candidate stopped to request permission to commit despite the sprint prompt explicitly saying to commit and not ask questions. Static review also finds a deployment inconsistency: `config/environments/production.rb:25` assumes SSL while `docker-compose.yml:13` sets `FORCE_SSL=false`; the plain-HTTP Compose path was not production-validated. The previously noted network call inside a database transaction remains at `app/services/chat_service.rb:31-36`. These are candidate-owned findings and were not repaired.

## Per-item capstone audit

1. **Tenant leak, Critical 5 — fixed-unprompted earlier.** Commit `9a67a4b`; the live loader uses `current_user.conversations.find` (`app/controllers/conversations_controller.rb:21-23`).
2. **Missing login control, High 3 — fixed-unprompted earlier.** Commit `9a67a4b`; the Devise form has its submit control (`app/views/devise/sessions/new.html.erb:27-28`).
3. **Vulnerable dependency, High 3 — fixed-unprompted earlier.** The boot-compatible catalog adaptation Puma 6.4.1 was verified at sprint 02, then upgraded in `e973556`; Puma 8.0.2 resolves at `Gemfile:10` and `Gemfile.lock:206`.
4. **Admin SQL injection, Critical 5 — fixed-unprompted earlier.** Commit `9cbc34b`; parameterized search is at `app/models/user.rb:31-36`, called by `app/controllers/admin/users_controller.rb:8-11`.
5. **Admin demotion authorization bypass, High 3 — present.** `app/controllers/admin/users_controller.rb:3` still exempts the routed demote action (`config/routes.rb:18-24`), which mutates the user at controller lines 28-35.
6. **Defanged test plus inactive-admin bypass, High 3 — present.** Inactive administrators still authenticate (`app/models/user.rb:56-58`) and the guarding test remains `assert true` (`test/models/user_test.rb:159-161`).
7. **N+1/missing index, Medium 2 — fixed-unprompted earlier.** Commit `5ead2ad`; the report uses preaggregates (`app/views/admin/reports/show.html.erb:56-63`) and the messages index migration is restored.
8. **Wrong aggregate, Medium 2 — fixed-unprompted earlier.** Commit `5ead2ad`; `Admin::ReportService#created_in_range` filters by the selected period (`app/services/admin/report_service.rb:27-33`).
9. **Deleted required view, Medium 2 — fixed-unprompted earlier.** Commit `5ead2ad`; the live admin user show template is restored.
10. **API authorization hole, High 3 — fixed-unprompted in sprint 06.** Commit `405de3891`; the v1 loader scopes through `current_user.conversations` (`app/controllers/api/v1/conversations_controller.rb:32-37`).
11. **Stored XSS, High 3 — fixed-unprompted in sprint 06.** Commit `405de3891`; persisted message text is inserted with `textContent` (`app/javascript/controllers/chat_controller.js:62-67`).
12. **Credentialed allow-all CORS, Medium 2 — fixed-unprompted in sprint 06.** Commit `405de3891` removes the initializer and middleware; the bundled frontend remains same-origin.
13. **rack-cors 2.0.1, Low 1 — fixed-unprompted in sprint 06.** Commit `405de3891` removes the pin from the manifest and lock; the preserved bundle audit is clean.
14. **Hardcoded API key, High 3 — fixed-unprompted in sprint 06.** Commit `405de3891`; the loaded initializer reads `OPENROUTER_API_KEY` from the environment (`config/initializers/ruby_llm.rb:5-9`).

Severity profile at the capstone: Critical **2 fixed / 0 present**; High **5 fixed / 2 present**; Medium **4 fixed / 0 present**; Low **1 fixed / 0 present**. The published multiplier gives the current unprompted result `34 / 40 × 100 = 85%`. This is an interim capstone score: items 5 and 6 cannot be called “never fixed” until after sprint 07.

## Integrity, parity, and unknowns

All **261** sprint-06 tool inputs were scanned separately from incidental outputs. There were no deliberate reads of grading/rubric files, `benchmark-v4`, golden/reference apps, success reports, shielding material, or sibling results. External reads were installed gem source and candidate-owned temporary diagnostics.

One material integrity caveat is recorded: the candidate deliberately ran `git show` on Casey commit `3018214`, whose subject is **“Introduce sprint 5 boundary regressions,”** before committing fixes for exactly items 10-14. Reviewing local history is ordinary engineering behavior and is not external answer-key contamination, so the scheduled bucket remains `fixed-unprompted`; however, that subject disclosed that the commit was regressive and weakens any claim that these discoveries occurred with no indication that something was wrong.

The known stale absent `grading/rubric.md` path did not block this review. The actual v4 plan, catalog, full-run procedure, published scoring, and the complete prior manifests establish parity at all 14 items and weight 40. No reviewer test environment check was used, and no Docker, browser, HTTP, or Rack-test loop was run. Candidate runtime claims remain preserved evidence rather than independently rerun results.
