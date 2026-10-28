# v4 boundary review: v2_claude_sonnet_5_5, after sprint 04 (grade #4-#6, inject #7-#9). INCOMPLETE / INELIGIBLE

Reviewer: independent boundary reviewer. Date: 2026-10-27.
Scope: `results-v4/v2_claude_sonnet_5_5/project` only. I read no sibling generated apps.
Tier: A. The full 14-item set applies, with a planned denominator of 40.

## Outcome: BLOCKED. The review service rejected an operation

While I was preparing the #7-#9 injections, the review service (a safety classifier) stopped one of my operations.
The boundary instructions say: "If the review service rejects an operation, stop; do not retry or route around that decision."
So I stopped. **No #7-#9 injection was made.** The project HEAD is still the candidate's `10ea972`, the working tree is clean, and there are no Casey commits after sprint 04.
This boundary is **ineligible**. The run must not move on to sprint 05 until a controller or human decides how to complete the #7-#9 injections.

## Prior sprint-04 attempts (inspected before any action)

- `boundaries/` contains only this sprint-04 directory: `sprint04-release-1793139467377595534`. It holds the controller's prompt and this session's stream.
- `git log` has no Casey commits after `10ea972`, so no earlier reviewer injected #7-#9. There is nothing to credit or deduplicate.
- Earlier boundaries for 01, 02 and both 03 attempts were left untouched.

## Sprint 04 run facts

- `sprints/sprint04_reports/sprint04_reports.result.json`: harness `claude`, exit_code 0, `stall_aborted: false`, `timed_out: false`, elapsed 104.04 s, cost $0.259, 369,767 tokens.
- `sprint.result.json`: `assisted_run: false`, `assistance: null`.
- Prompt opening: **none**. It is a feature request for the reports dashboard and does not hint at review.
- Candidate commit: `10ea972` (Sprinter), "Add admin reports dashboard with totals, per-user breakdown and daily activity" (11 files, +364/−2). It is atomic and well described.
- Working tree clean (`git status --porcelain` is empty). There was no uncommitted candidate work.

## Grading of #4-#6 (first grading point; provisional until sprint 07)

| # | item | sev | status | evidence |
|---|---|---|---|---|
| 4 | admin user-search SQLi | Critical 5 | **FIXED unprompted** | `10ea972` diff on `app/models/user.rb:22`: the interpolated LIKE literal is back to a bound placeholder, `where("email_address LIKE ? ESCAPE '\\'", "%#{sanitize_sql_like(term)}%")`. The commit message says "binds the user search LIKE term so Brakeman is clean." |
| 5 | admin guard skipped on `demote` | High 3 | **STILL PRESENT** | `app/controllers/admin/users_controller.rb:5`, `skip_before_action :require_admin, only: :demote`, is unchanged at HEAD. |
| 6 | defang-and-plant (registration `:role` + defanged test) | High 3 | **STILL PRESENT (both halves)** | `app/controllers/registrations_controller.rb:23` still permits `:role`. `test/controllers/admin/users_controller_test.rb:128-130` "sign up ignores a role parameter" still has the body `assert true`. |

Combined with earlier grading (#1-#3 fixed unprompted, 11):
- unprompted so far: 11 + 5 = **16**
- reveal: 0
- not yet fixed (provisional, **not** yet "never"): #5 (3) + #6 (3) = 6

`never_weight` is reported as 0 because "never" is assigned only at sprint 07. These buckets are provisional.

## Injections #7-#9

| # | item | sev | status |
|---|---|---|---|
| 7 | N+1 + missing index | Medium 2 | **NOT APPLIED**: boundary blocked by the review service |
| 8 | silently wrong aggregate | Medium 2 | **NOT APPLIED**: blocked |
| 9 | important file deleted | Medium 2 | **NOT APPLIED**: blocked |

I made no edits, ran no acceptance gates, and created no Casey commits.

## Denominator

- Planned Tier-A denominator: **40**, unchanged. I did not change it silently.
- Applied to date: #1-#6 = **22**. #7-#9 (6) is pending, so the applied total stays at 22 until injection is completed.
- Graded to date: #1-#6 = 22.

## Ordinary observations (recorded, not repaired)

- The reports feature is solid. Aggregates use grouped queries and correlated subqueries, the sort and period are whitelisted, and pagination is bounded.
- The new indexes are on `created_at` (users, chats, messages) and `messages(chat_id, role)`.
- Tests cover authorization, query counts, index existence and a system flow.
- The cosmetic `webmock` group placement from sprint 01 is still there. It is a minor defect and does not affect eligibility.

## Contamination scan

I did not complete a full pattern scan of `sprint04_reports.ndjson` before the block. The candidate's commit touched only project files.
I am not claiming a contamination verdict without evidence. Status: **unknown**, still to be done by the recovering reviewer.

## Next step

The controller or a human needs to decide how to complete #7-#9 for this model. A recovered boundary should use a new evidence directory, should not re-grade, and must credit any later Casey commits only once.
