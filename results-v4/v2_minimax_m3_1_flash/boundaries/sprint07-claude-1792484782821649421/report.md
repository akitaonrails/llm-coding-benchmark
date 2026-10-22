# v4 FINAL grading — `v2_minimax_m3_1_flash` after Sprint 7 (explicit reveal)

**Model:** MiniMax M3.1 Flash — a 428B cloud MoE successor to MiniMax M3 (whose v4 score was **75.5**).
**Boundary:** after-sprint-7, the EXPLICIT security reveal. GRADE-ONLY, no injection.
**Method:** static-only (git show/log, grep, file reads, `ruby -c`); no docker/db/server/bundle/tests run. `GIT_CEILING_DIRECTORIES` pinned to `results-v4`.
**Capstone (s6) HEAD:** `a524ff5` → **grading HEAD:** `1c3c778`. Reveal range `a524ff5..HEAD` = 10 commits (e4d28e5, b984569, 263f5be, 0dac1eb, 227cb84, c682063, c74dd84, 026618b, a494ba6, 1c3c778).

## State entering the reveal
33/40 weight already caught UNPROMPTED through sprint 6 (#1,#3,#4,#5,#6,#9 + the five s6 capstone fixes #10–#14). Only three items were OPEN: **#2 (High 3)**, **#7 (Med 2 compound)**, **#8 (Med 2)**. Fixes landing only now earn 40% of their weight.

## The three remaining items — final dispositions

### #2 login-link (High 3) — FIXED AT REVEAL → 40% = **1.2**
Commit **`0dac1eb`** ("let a visitor with an account go back to the sign in form") appends to the routed view `app/views/registrations/new.html.erb:40`:
`<%= link_to "Sign in", sign_in_path, class: "font-medium text-slate-900 underline" %>` inside an "Already have an account?" paragraph after the Sign up button. The sign-up page is no longer a dead end. A guarding system test was added (`test/system/authentication_test.rb`: visit sign_up_path → click_link "Sign in" → assert_current_path sign_in_path). Landed in the reveal range ⇒ reveal-weight only.

### #8 wrong aggregate (Med 2) — FIXED AT REVEAL → 40% = **0.8**
Commit **`263f5be`** ("count every admin in the totals") changes `app/models/reports/dashboard.rb:107` from `admins: User.admin.active.count` to **`admins: User.admin.count`**. The Admins card now counts ALL admins, open or closed. A regression test was added (`dashboard_test.rb`: deactivate carol, assert `admins == 1`, `closed_accounts == 2`). Reveal range ⇒ reveal-weight only.

### #7 COMPOUND N+1 + index (Med 2) — BOTH HALVES NOW HOLD → 40% = **0.8**
- **Half A (N+1): RESOLVED** (unchanged this boundary). `dashboard.rb` builds everything with grouped SQL aggregates — `conversation_counts` (GROUP BY user_id), `message_counts` (JOIN messages … GROUP BY user_id), and `build_activity` (:182) runs three grouped `.group(DAY).count` queries. No per-row iteration.
- **Half B (dropped `messages.created_at` index): RESTORED AT REVEAL.** Commit **`b984569`** ("give the activity … an index it can use") adds migration `20261020000010_restore_message_timestamp_index.rb` doing `add_index :messages, :created_at, algorithm: :concurrently` **and** `remove_index :messages, [:role, :created_at]`. At HEAD `db/schema.rb:60` carries `t.index ["created_at"], name: "index_messages_on_created_at"` and the bogus `index_messages_on_role_and_created_at` is **GONE** (grep: absent). This is a REAL bare `created_at` index backing `build_activity`'s filter+group on `created_at` alone — the bogus composite (which could not serve it) was correctly discarded, not kept as a substitute. A guarding test asserts the index exists AND (via `EXPLAIN` with `enable_seqscan=off`) that the activity query uses an index whose first column is `created_at`.

Compound rule satisfied (A healed + B restored). The credit-bearing half (B) landed only in the reveal range, so the whole item scores at reveal-weight. (The later `a494ba6` only re-cosmeticizes the users `role` check_constraint; `1c3c778` is a system-test retry tweak — neither touches the index.)

## Arithmetic
- unprompted_weight = **33**
- reveal_weight = #2(3) + #8(2) + #7(2) = **7**
- final = (33 + 0.4 × 7) / 40 × 100 = (33 + 2.8) / 40 × 100 = 35.8 / 40 × 100 = **89.5**

## FINAL SCORE: **89.5 / 100**

## The model's pattern
MiniMax M3.1 Flash catches the **loud / signal-bearing** sabotage on its own, under no explicit prompt:
- Everything with a **test, scanner, or runtime signal** fell unprompted — the Critical tenant-leak and SQLi, the authz/IDOR items, the compound test-defang+vuln (#6), the deleted-file availability break (#9), and the entire sprint-6 capstone batch under only a vague "harden for production" steer: API IDOR re-scoping, stored-XSS killed at the source with a server-side `SafeListSanitizer`, wildcard+credentials CORS replaced by an ENV allow-list, a REAL rack-cors 2.0.1→2.0.2 upgrade (no bundle-audit ignore), and the hardcoded OpenRouter key moved to ENV.
- The three it needed the **explicit reveal** for are exactly the **no-signal** ones: a missing UI link that no existing test exercised (#2), a green-but-wrong aggregate that no fixture made wrong (#8), and a silently dropped index masked by a plausible-looking bogus composite (#7 half-B). With no red test and no scanner finger, it never looked — until told. Once told, it fixed all three correctly AND added a guarding test to each, which is the mature response.

Net: strong unprompted security instincts, weaker unprompted correctness/perf vigilance without a failing signal — but complete and test-backed remediation at the reveal.

## Verdict vs the field
**89.5** — a clear generational lift over its predecessor **MiniMax M3 (75.5)**, +14. It sits in Tier A (≥83), comfortably above the mid-pack open-weight MoEs and in the neighborhood of the strong cloud models, though short of the 92–100 frontier tier. The whole gap to a perfect 40/40 is the 60% withheld on three no-signal items it caught only after the explicit reveal.
