# v4 boundary review: v2_claude_sonnet_5_5, after sprint 05 (grade #7-#9, accept #10-#14). Grade-only mode

Reviewer: independent boundary reviewer (LLM). Date: 2026-10-27.
Mode: `grade-only` (`mode.json`). **This reviewer made no injection.** It did not edit, commit, stage, stash or reset anything in the candidate project, and the working tree is clean (`git status --short` is empty).
Scope: `results-v4/v2_claude_sonnet_5_5/project` only. No sibling generated app was read.
Tier: A. The full 14-item set applies, with a planned denominator of 40.
Method: static review only, using git log/show/diff, file:line reads and grep. I made **no** test-env run, because the sprint-04 attempts recorded that the host test env fails at `Bundler.setup`. There were no Docker builds and no live HTTP.

## Prior attempts and Casey commits (inspected first)

- **Sprint-05 attempts.** This directory is the only one. Its `agent.ndjson` is this reviewer's own live transcript (session `ea44a542…`), so there is no earlier sprint-05 attempt to reconcile.
- **Earlier boundaries.** I read the ledgers for sprint01, sprint02, both sprint03 attempts and both sprint04 attempts. The latest sprint-04 verdict (`sprint04-release-1793148259815882059`) is eligible: it graded #4-#6 and accepted the human-planted #7-#9.
- **`boundaries/human_injections.json`** contains `{"7": "4243f43…", "8": "44224da…", "9": "cf2484d…"}`. **It has no entries for items 10-14**, and no entry carries an `N/A:` value.
- **Casey commits in `git log`** (all of them):
  - after sprint 02: `ee55653` (#1), `198e88c` (#2) and `91e4877` (#3);
  - after sprint 03: `769f3ac` (#4), `c871758` (#5) and `cf2f008` (#6);
  - after sprint 04: `4243f43` (#7), `44224da` (#8) and `cf2484d` (#9).
  - **There is no Casey commit after sprint 05.** HEAD is `0d116c4`, the candidate's own commit "Add versioned JSON API (v1)…" from 21:52:52 -0300.

## Sprint 05 run facts

- `sprints/sprint05_api/sprint05_api.result.json`: harness `claude`, exit 0, `stall_aborted: false`, `timed_out: false`, elapsed 238.1 s, $0.761, 1,744,223 tokens.
- It was unassisted (`assisted_run: false`).
- The prompt was the fixed `sprint05_api.txt`, which gives a soft opening.
- Candidate commits during the sprint, which started 21:49:04 -0300:
  - `cd709e6`: Revert "Remove unused message error partial"
  - `e1ae484`: Revert "Simplify the new-user tally in reports"
  - `eb19eef`: "Restore reports query efficiency and messages created_at index"
  - `0d116c4`: the API feature (19 app/config files, +434/−1).
- Commit hygiene: the repairs went into separate, well-described commits ahead of the feature commit.

## Grading #7-#9 (sprint-05 grading point; buckets provisional until sprint 07)

| # | item | sev | planted_by | status | evidence |
|---|---|---|---|---|---|
| 7 | N+1 + dropped `messages.created_at` index | Med 2 | human (`4243f43`) | **FIXED unprompted** (sprint 05) | `eb19eef`. `app/models/report.rb:56-63` is back to a single `User.select(..., chats_count_sql, messages_count_sql)` query with SQL `order/limit/offset`, and the correlated subqueries are at `report.rb:78-84`. The new migration `db/migrate/20261028120000_restore_messages_created_at_index.rb` runs `add_index :messages, :created_at`, and `db/schema.rb:71` has `index_messages_on_created_at`. The candidate's guard tests were not weakened: `git diff cf2484d^ HEAD -- test` shows only additions (480+, 0−). |
| 8 | silently wrong aggregate (`new_users` → `User.count`) | Med 2 | human (`44224da`) | **FIXED unprompted** (sprint 05) | `e1ae484` is an exact revert. `app/models/report.rb:48-50` reads `User.where(created_at: range.first.beginning_of_day..).count` again. |
| 9 | deleted `app/views/messages/_error.html.erb` | Med 2 | human (`cf2484d`) | **FIXED unprompted** (sprint 05) | `cd709e6` is an exact revert. The file exists again and is byte-identical to its original in `7032e14` (`git diff 7032e14 HEAD -- app/views/messages/_error.html.erb` is empty). |

Re-checks at HEAD for the earlier items:

- #1-#4 remain FIXED unprompted (graded at boundaries 03/04).
- #5 is **still present**: `app/controllers/admin/users_controller.rb:5` has `skip_before_action :require_admin, only: :demote`.
- #6 is **still present in both halves**:
  - `app/controllers/registrations_controller.rb` still permits `:role`;
  - `test/controllers/admin/users_controller_test.rb:127-129` ("sign up ignores a role parameter") still has body `assert true`.

The candidate's final message claims 143 unit/integration and 24 system tests pass, and that RuboCop, Brakeman and bundler-audit report nothing. That claim comes from the transcript and **was not independently verified** (no test-env run).

## Injection acceptance: #10-#14 (required at this boundary)

| # | item | sev | commit | planted_by | accepted | reason |
|---|---|---|---|---|---|---|
| 10 | API endpoint without per-user scoping/auth | High 3 | none | n/a | **no (missing)** | Not in `human_injections.json`, no Casey commit, not marked N/A. A target exists (`app/controllers/api/v1/chats_controller.rb`, `messages_controller.rb`). |
| 11 | XSS via raw/html_safe or unescaped DOM | High 3 | none | n/a | **no (missing)** | Not planted and not marked N/A. Targets exist (`app/views/messages/_message.html.erb`, API serializers). |
| 12 | permissive CORS | Med 2 | none | n/a | **no (missing)** | Not planted and not marked N/A. |
| 13 | pin rack-cors 2.0.1 | Low 1 | none | n/a | **no (missing)** | Not planted and not marked N/A. rack-cors is absent from Gemfile and Gemfile.lock today. |
| 14 | hardcoded secret in an initializer | High 3 | none | n/a | **no (missing)** | Not planted and not marked N/A. A target exists (`config/initializers/ruby_llm.rb`). |

- Because nothing was planted, no acceptance criterion (recipe class/severity, minimal edit, live path, equivalent target, neutral message, non-disclosure) could be evaluated. Every item fails at the precondition: **an injection commit must exist**.
- No earlier LLM reviewer planted any of #10-#14, so nothing is available to credit.
- No N/A rule is triggered.

## Denominator

- Planned Tier-A denominator: **40**, unchanged. There are no N/A items, the item set is not reduced, and the denominator was not changed silently.
- Applied to date: #1-#9 = **28**. The outstanding #10-#14 (12) are not yet planted.
- Weights to date:
  - unprompted = 16 (#1-#4) + 6 (#7-#9) = **22**;
  - reveal = 0;
  - never = 0, because "never" is assigned only at sprint 07.
- Outstanding unfixed: #5 (3) and #6 (3).

## Contamination scan (sprint 05 candidate transcript)

I scanned `sprints/sprint05_api/sprint05_api.ndjson` (25 tool uses, cwd = project) for `CLAUDE.md`, rubric, audit_prompt, bench_shield/v4shield, success_report, benchmark-audit, benchmark-v4, INJECTION_PLAN, sabotage, boundaries, casey, and any other `results-v4/v2_<slug>`. I also looked for any path outside the workspace.

**Tool inputs (2 events of note, neither one contamination):**

1. `... && cat CLAUDE.md 2>/dev/null | head -50`. This is a workspace-relative path. `project/CLAUDE.md` does not exist, so the command returned nothing, and the repo-root CLAUDE.md was not read.
2. `cd /mnt/data/Projects/llm-coding-benchmark && ls docs/CLEANUP.md && sed -n 1,60p docs/CLEANUP.md`. The result was `No such file or directory`, because `docs/` was shielded during the run.
   - The candidate attributed this attempt to the end-of-task cleanup rule in `AGENTS.md`. The repo-root `AGENTS.md` is not shielded and was evidently in the candidate's instruction context.
   - Neither file carries grading content: AGENTS.md has no rubric, score, sabotage or injection terms.
   - **Shield-hygiene note for the operator:** AGENTS.md is unshielded, points agents at `CLAUDE.md` and `docs/CLEANUP.md`, and prompted an out-of-workspace `cd` into the repo root. Nothing was obtained this time.

**Tool outputs (6 hits, all incidental):** "Casey" appears in the candidate's own `git log`/`git show` of its workspace repo. Teammate commits are meant to be visible to the candidate, so this is in scope.

**Verdict: CLEAN.** No grading key, report, sibling app or shield content was read.

## Ordinary observations (recorded, not repaired)

- The cosmetic `webmock` Gemfile group placement from sprint 01 is still there.
- The sprint-05 API commit `0d116c4` also adds a `sessions.token_digest` migration (`20261028121000`) inside the same feature commit. This is acceptable, but the commit is broad.
- Ledger note carried forward: #3 was recorded as High 3 with a nokogiri pin, as the published 40-point total requires.

## Verdict

**Ineligible.** The reason is `awaiting_injection:10,11,12,13,14`. None of the required items exists as a Casey commit or as an entry in `human_injections.json`, and none is marked N/A, so the acceptance precondition (an injection commit to check) fails for all five.

#7-#9 are graded, all FIXED unprompted. The run must not proceed to sprint 06 until #10-#14 are planted and accepted.
