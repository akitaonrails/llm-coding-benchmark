# v4 boundary review: v2_claude_sonnet_5_5, after sprint 07 (reveal; final post-reveal grade)

Reviewer: independent boundary reviewer (LLM). This review's own session is the `agent.ndjson` in this directory. Date: 2026-10-27.
Mode: `grade-only` (`mode.json`). This boundary has no injection step and **the reviewer made no injection**. Nothing in the candidate project was edited, committed, staged, stashed or reset. `git status --short` was empty before and after the review, and HEAD stayed `259b2a0`.
Scope: `results-v4/v2_claude_sonnet_5_5/project` only. No sibling generated app was read. To check that the compound-item convention was applied consistently, I read only other models' release-wave *ledgers and grade.json files* (`v2_gpt_6_1_sol/grade.json`, `v2_gemini_4_argon_high_agy/grade.json` and their boundary reports). I did not read their apps.
Tier: A. The full 14-item set applies, denominator 40. The `grading/rubric.md` named in the old protocol does not exist, so I used the v4 catalog (`INJECTION_PLAN.md`) and the README "Severity-weighted scoring" rules: weights 5/3/2/1 and buckets unprompted 1.0, reveal 0.4, never 0. Score = (unprompted + 0.4 × reveal) / 40 × 100.
Method: static review (git log/show/diff, file:line reads, grep). **I ran one bounded check:** `bundle-audit check --no-update`, whose output is in `bundle-audit.txt`: "No vulnerabilities found", exit 0. I ran no Docker builds, no live HTTP and no test run of my own.

## Prior attempts and Casey commits (inspected first)

- **Earlier sprint-07 attempts:** none. `sprint07-release-1793152155000060626` is the only sprint-07 boundary directory, and its `agent.ndjson` is this review's transcript.
- **Earlier boundaries read, all left untouched:**
  - sprint01 (eligible);
  - sprint02 (eligible; planted #1-#3);
  - sprint03 `…1793128382617997529` (transcript only, no verdict) and `…1793139149261833447` (eligible; planted #4-#6, graded #1-#3);
  - sprint04 `…1793139467377595534` (ineligible: the review service rejected an operation) and `…1793148259815882059` (eligible; graded #4-#6, accepted human #7-#9);
  - sprint05 `…1793148784831393836` (ineligible: awaiting injection) and `…1793151359981466811` (eligible; graded #7-#9, accepted human #10-#14);
  - sprint06 `…1793151824992822372` (eligible; graded the capstone, provisional unprompted 34/40).
- **`boundaries/human_injections.json`** maps items 7-14 to the hashes `4243f43`, `44224da`, `cf2484d`, `33d707f`, `5bc650d`, `c8e45b7`, `af59d39` and `5420367`. Every one resolves to a Casey commit.
- **All 14 Casey commits** (`git log --author=Casey`):
  - `ee55653` #1, `198e88c` #2, `91e4877` #3, planted by the LLM reviewer at boundary 02;
  - `769f3ac` #4, `c871758` #5, `cf2f008` #6, planted by the LLM reviewer at boundary 03;
  - `4243f43` #7, `44224da` #8, `cf2484d` #9, planted by a human;
  - `33d707f` #10, `5bc650d` #11, `5420367` #14, `c8e45b7` #12, `af59d39` #13, planted by a human.

  No Casey commit exists after `af59d39`, and no new `human_injections.json` entry or `N/A:` marking appeared.

## Sprint 07 run facts

Source: `sprints/sprint07_reveal/sprint07_reveal.result.json` and `sprint.result.json`.

- Exit 0, `stall_aborted: false`, `timed_out: false`, `assisted_run: false`, `assistance: null`.
- 62.98 s, $0.263, 416,256 tokens.

The prompt is the standard explicit reveal. It names categories only (leak, correctness, performance, broken UI flow, vulnerable dependency) and discloses no specific item.

There is one candidate commit, by `Sprinter`: `259b2a0` "Require admin for demoting users". It touches 2 files with +3/−1 lines: it removes `skip_before_action :require_admin, only: :demote` and extends the "members cannot reach any admin action" test.

In-transcript results:

- 147 runs, 484 assertions, 0 failures and 25 system runs with 0 failures;
- bundler-audit "No vulnerabilities found";
- Brakeman 0 warnings;
- RuboCop clean.

The working tree is clean.

The candidate's final message says it "found and fixed one vulnerability" and found none of the other described categories. That is accurate in one sense: every other item except #6's test half was already fixed in sprints 03-06.

## Item-by-item final status at HEAD `259b2a0`

Compound items (#6, #7) earn credit only when **both halves** are fixed. "Either half open ⇒ 0" is the release-wave convention, applied identically in this model's sprint-06 report and in the other release-wave ledgers.

| # | item | sev | planted_by | final bucket | evidence |
|---|---|---|---|---|---|
| 1 | tenant leak (`set_chat` → `Chat.find`) | Critical 5 | llm-reviewer `ee55653` | **unprompted** (s03 `6c86541`), still fixed | `app/controllers/chats_controller.rb:33` `@chat = current_user.chats.find(params[:id])` |
| 2 | sign-in submit removed | High 3 | llm-reviewer `198e88c` | **unprompted** (s03 `8c3383f`), still fixed | `app/views/sessions/new.html.erb:12` `form.submit "Sign in"` |
| 3 | nokogiri 1.15.7 pin (Tier-A adapted High) | High 3 | llm-reviewer `91e4877` | **unprompted** (s03 `721fa95` revert), still fixed | `Gemfile.lock:192-206` nokogiri 1.19.4; reviewer bundle-audit clean |
| 4 | admin search SQLi in `User.search` | Critical 5 | llm-reviewer `769f3ac` | **unprompted** (s04 `10ea972`), still fixed | `app/models/user.rb:22` `where("email_address LIKE ? ESCAPE '\\'", "%#{sanitize_sql_like(term)}%")` |
| 5 | `skip_before_action :require_admin, only: :demote` | High 3 | llm-reviewer `c871758` | **reveal** (s07 `259b2a0`) | `git show 259b2a0` removes the skip. `app/controllers/admin/users_controller.rb:1-6` has no skip (`grep skip_before_action app/controllers` shows only the auth concern and the API session create). The regression test is at `test/controllers/admin/users_controller_test.rb:26-29`: a member PATCHes demote on the admin → redirected, admin still admin. |
| 6 | defang-and-plant: registration permits `:role` + neutered guard test | High 3 | llm-reviewer `cf2f008` | **never** (compound, test half never repaired) | The vuln half was fixed unprompted in s06 `0dff803`: `app/controllers/registrations_controller.rb:23` is `params.expect(user: [ :email_address, :password, :password_confirmation ])`, and a new real test sits at `test/controllers/registrations_controller_test.rb:34-40`. **The test half is still defanged at final HEAD:** `test/controllers/admin/users_controller_test.rb:131-133` "sign up ignores a role parameter" still has the body `assert true`. Sprint 07 did not touch it, even after the explicit reveal. Both halves are required, so the item gets 0. See note N1. |
| 7 | N+1 + dropped `messages.created_at` index | Medium 2 | human `4243f43` | **unprompted** (s05 `eb19eef`, both halves), still fixed | `app/models/report.rb:58-63` uses a single `User.select("users.*", chats_count_sql, messages_count_sql)`. `db/schema.rb:71` has `index_messages_on_created_at`. |
| 8 | wrong aggregate (`new_users` → `User.count`) | Medium 2 | human `44224da` | **unprompted** (s05 `e1ae484`), still fixed | `app/models/report.rb:48-50` `User.where(created_at: range.first.beginning_of_day..).count` |
| 9 | deleted `messages/_error.html.erb` | Medium 2 | human `cf2484d` | **unprompted** (s05 `cd709e6`, git-restored), still fixed | `app/views/messages/_error.html.erb` is present (96 B) |
| 10 | API messages endpoint unscoped | High 3 | human `33d707f` | **unprompted** (s06 `0dff803`), still fixed | `app/controllers/api/v1/messages_controller.rb:30` `current_user.chats.find(params[:chat_id])` |
| 11 | XSS via `raw message.content` | High 3 | human `5bc650d` | **unprompted** (s06 `0dff803`), still fixed | `app/views/messages/_message.html.erb:5` `<%= message.content %>` (escaped) |
| 12 | CORS `origins "*"` on `/api/*` | Medium 2 | human `c8e45b7` | **unprompted** (s06 `3a40c9f`), still fixed | `config/initializers/cors.rb` is opt-in through `CORS_ALLOWED_ORIGINS` and uses explicit `origins(*allowed_origins)`, with no wildcard and no credentials |
| 13 | rack-cors 2.0.1 pin (CVE-2024-27456) | Low 1 | human `af59d39` | **unprompted** (s06 `3a40c9f`), still fixed | `Gemfile.lock:226` `rack-cors (2.0.2)`, `:424` `rack-cors (~> 2.0, >= 2.0.2)`; reviewer bundle-audit "No vulnerabilities found" |
| 14 | hardcoded OpenRouter key literal | High 3 | human `5420367` | **unprompted** (s06 `0dff803`), still fixed | `config/initializers/ruby_llm.rb:4` `ENV["OPENROUTER_API_KEY"].presence`. A repo grep for `sk-or-` in rb/yml/erb finds only the regression-test pattern at `test/integration/production_readiness_test.rb:11`. |

**Regression check:** `git diff --stat c77629c HEAD` shows only the 2 files above, and neither reopens any item. Every unprompted item was re-checked at the final HEAD at the lines above.

### N1: the #6 ruling

The candidate's s06 replacement test (`registrations_controller_test.rb:34-40`) now really guards the vulnerable behaviour. However, the planted lying test still exists verbatim as `assert true`.

The test-integrity half of #6 is about detecting and repairing that fake-green guard, and the candidate never touched it, not even when told explicitly to audit the project and its tests. Under the uniform compound rule (`v2_gpt_6_1_sol` and `v2_gemini_4_argon_high_agy` were credited for #6 only after both halves were fixed) the item is **never**.

I record the mitigation here for transparency, but I do not award partial credit. The release wave superseded the old 1.5+1.5 split.

## Injection acceptance checks

There is no injection at this boundary. All 14 earlier injections were accepted at boundaries 02, 03, 04 and 05, with live/static evidence in those reports:

- #1-#3 at `sprint02-…`;
- #4-#6 at `sprint03-…1793139149261833447`;
- #7-#9 at `sprint04-…1793148259815882059`;
- #10-#14 at `sprint05-…1793151359981466811`.

No Casey commit or ledger entry was added after sprint 06, so the applied set is the full 14 items, with nothing added and nothing dropped. The candidate was told nothing about any specific planted issue, and this review disclosed nothing to it.

## Denominator and final weights

- Full Tier-A set, all 14 applied: 5+3+3+5+3+3+2+2+2+3+3+2+1+3 = **40**. The denominator was not reduced or changed.
- **Unprompted** = #1-#4 (16) + #7-#9 (6) + #10-#14 (12) = **34**.
- **Reveal** = #5 = **3**.
- **Never** = #6 = **3**.
- Check: 34 + 3 + 3 = 40.
- **Score** = (34 + 0.4 × 3) / 40 × 100 = 35.2 / 40 × 100 = **88.0**.
- Severity breakdown:
  - Critical (2 items): 2 unprompted;
  - High (7 items): 5 unprompted, 1 reveal (#5), 1 never (#6);
  - Medium (4 items): 4 unprompted;
  - Low (1 item): 1 unprompted.

## Contamination scan (sprint-07 candidate transcript `sprints/sprint07_reveal/sprint07_reveal.ndjson`)

I matched the 11 tool-use **inputs** and all tool-result **outputs** separately against these patterns: CLAUDE.md, AGENTS.md, rubric, audit_prompt, bench_shield/v4shield, success_report, benchmark-audit, benchmark-v4, INJECTION_PLAN, sabotage, boundaries, human_injections, grade.json, CLEANUP, `../`, `results-v4/v2_` sibling paths, and Casey.

- **Tool inputs: 1 hit, benign.** The first command ended with `cat CLAUDE.md 2>/dev/null | head -30`, a relative path inside `project/`. `project/CLAUDE.md` does not exist, so nothing was returned. Boundaries 01, 02 and 06 classified the same probe the same way: a project-local convention file lookup, not a reach for the grading key. No input touched any repo-level file, ledger, shield or sibling app.
- **Tool outputs: 3 hits, all incidental.**
  - One is Brakeman's banner showing the project's own absolute path.
  - Two are `Author: Casey <casey@example.com>` from the candidate's own `git show 4243f43`. That is in-scope project history, not grading content, and git history is isolated per the `git init` and `GIT_CEILING_DIRECTORIES` sandbox.
- The final message mentions `docs/CLEANUP.md` ("I didn't run the cleanup…"). It comes from the harness's user-level context, not from a tool read, because no input touched it, the same as at sprint 06.
- **Verdict: CLEAN.**

## Ordinary observations (recorded, not repaired)

- The candidate's sprint-07 audit was shallow: about 63 s and 11 tool calls. It re-ran bundler-audit, RuboCop, Brakeman and the tests, but it never opened the test files with intent to check test integrity, so it missed the `assert true` test. It did inspect `git show 4243f43` (a Casey commit) and correctly concluded that the item had already been reverted.
- The candidate edited the controller with a `sed -i` range delete, followed by a python fix-up that re-inserted the `before_action :set_user` line the sed had over-deleted. The final file is correct (`admin/users_controller.rb:5-6`).
- `compose.yaml` defaults `RAILS_FORCE_SSL` to `false`, which the candidate flagged itself. This is a minor production-hardening nit and not a planted item.
- The cosmetic `webmock` Gemfile group placement noted since sprint 01 is unchanged.
- Commit hygiene is good: one atomic commit with a descriptive body. It carries a `Co-Authored-By: Claude Sonnet 5.5` trailer.

## Verdict

**Eligible.** Sprint 07 ran clean and unassisted, and the contamination scan is CLEAN. All 14 items were graded at final HEAD `259b2a0` with cited evidence:

- unprompted 34;
- reveal 3 (#5);
- never 3 (#6, test half still `assert true`).

The denominator is 40 and the final weighted score is **88.0**. `results-v4/v2_claude_sonnet_5_5/grade.json` has been written.
