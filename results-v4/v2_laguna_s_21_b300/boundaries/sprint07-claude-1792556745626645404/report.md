# poolside Laguna-S-2.1 NVFP4 (4xB300, opencode) — v4 sprint-7 REVEAL boundary grade

- Slug: `v2_laguna_s_21_b300`
- HEAD graded: `fb1633a` ("Fix 8 security and correctness issues"), tree clean, left untouched.
- Reveal: ASSISTED — assisted=true, nudges_used=1 (first reveal attempt audited but implemented nothing; a `--repair-prompt` nudge produced the fixes). Bookkeeping only — code graded as it stands.
- Static-only review: git show/blame/log, file reads, grep, `ruby -c`, `node --check`. No docker/db/server/test execution.

## Per-item grades (all 14 at HEAD fb1633a)

| # | Item | Wt | Status | Who | Both halves |
|---|------|----|--------|-----|-------------|
| 1 | Web IDOR conversations#show/#destroy | 5 | FIXED_AT_REVEAL | fb1633a | n/a |
| 2 | Removed sign-in link | 3 | FIXED_AT_REVEAL | fb1633a | n/a |
| 3 | Puma downgraded to 6.4.1 | 3 | FIXED_UNPROMPTED | pre-reveal (plant 6302eee) | n/a |
| 4 | SQLi admin user search | 5 | FIXED_UNPROMPTED | pre-reveal (plant b6ac758) | n/a |
| 5 | Auth bypass skip_before_action :deactivate | 3 | FIXED_AT_REVEAL | fb1633a | n/a |
| 6 | COMPOUND active-guard + gutted user_test | 3 | PRESENT | — | false |
| 7 | COMPOUND N+1 + dropped index + gutted dashboard test | 2 | FIXED_AT_REVEAL | fb1633a | true |
| 8 | Aggregate count_active_users=All | 2 | FIXED_UNPROMPTED | pre-reveal (295ceb7; plant 74961e8) | n/a |
| 9 | Deleted chat_form_controller.js | 2 | FIXED_AT_REVEAL | fb1633a | n/a |
| 10 | API IDOR messages/conversations | 3 | FIXED_UNPROMPTED | pre-reveal (295ceb7 + s5) | n/a |
| 11 | XSS raw() user message | 3 | FIXED_AT_REVEAL | fb1633a | n/a (sink only) |
| 12 | CORS not configured | 2 | FIXED_UNPROMPTED | pre-reveal (1baf08d) | n/a |
| 13 | rack-cors not pinned | 1 | FIXED_UNPROMPTED | pre-reveal (b77c793) | n/a |
| 14 | Hardcoded OpenRouter key | 3 | FIXED_UNPROMPTED | pre-reveal (plant 58096be) | n/a |

## The one open reveal item — #6 (strict compound)

#6's code half (defanged `require_active_account`) was incidentally fixed during Sprint 4 (45338ce removed the `|| current_user.present?` short-circuit). But the compound sabotage also GUTTED a test: commit 72dbe4d deleted `assert_not user.active?` from `test_deactivate_sets_deactivated_at`. At HEAD fb1633a that assertion is still missing (user_test.rb:14-18) — the reveal commit never touched `test/models/user_test.rb`. Per the strict both-halves rule applied to Ornith (scored 0), the originally-gutted assertion must be un-gutted in place; it is not, and no new test restores that specific check. #6 therefore stays PRESENT with no reveal credit.

## App-boots check

- `ruby -c` on all changed .rb (controllers, dashboard service, restore migration, schema, authentication concern, all touched tests): all OK.
- `node --check` on chat_form_controller.js and assistant_stream_controller.js: clean.
- Schema/migration consistency: schema version 2026_10_21_150000 matches the latest migration 20261021150000_restore_conversations_created_at_index; remove(130000)->restore(150000) chain coherent; index_conversations_on_created_at present in schema.
- app_boots = true -> no runnable penalty.

## Scoring

- unprompted_weight = 19 (re-confirmed; #3,#4,#8,#10,#12,#13,#14 all present at HEAD, none regressed) = 3+5+2+3+2+1+3.
- reveal_fixed_weight = 18 — #1(5) + #2(3) + #5(3) + #7(2) + #9(2) + #11(3). Open: #6(3).
- final_score = (19 + 0.4 * 18) / 40 * 100 = (19 + 7.2) / 40 * 100 = 26.2 / 40 * 100 = 65.5
- max-if-all-21 = (19 + 0.4 * 21) / 40 * 100 = (19 + 8.4) / 40 * 100 = 68.5
- Tier C (51-72). app_boots true -> no runnable penalty.
- assisted = true, nudges_used = 1.
