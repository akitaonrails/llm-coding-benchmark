# Ornith-1.5-122B FP8 (4xB300, opencode) — v4 REVEAL boundary (after sprint 7)

- Slug: `v2_ornith_1_5_122b_b300`
- HEAD graded: `96fbcb1` (tree clean; Ornith self-committed the reveal). Not modified.
- Mode: STATIC-ONLY (file reads, grep, git in project, `ruby -c`, `node --check`). No docker/db/server/test execution.
- Reveal commits (bbefbe1..96fbcb1): b99c560 (#5), 8147be3 (#6), fd96951 (#11), 13bf872 (#7), 5fade63 (#8), 96fbcb1 (#2).
- assisted = false, nudges_used = 0 (Ornith never needed a nudge).

## Per-item grade (all 14 at HEAD 96fbcb1)

| # | wt | status | who | evidence | both-halves |
|---|----|--------|-----|----------|-------------|
| 1 | 5 | FIXED_UNPROMPTED | unprompted | conversations_controller.rb:9,25 current_user.conversations.find — tenant-scoped | n/a |
| 2 | 3 | FIXED_AT_REVEAL | 96fbcb1 | layouts/application.html.erb:30 link_to "Sign in", login_path + users/new.html.erb:35 "Already have an account?"; route get "login" present; login_flow_test added | n/a |
| 3 | 3 | FIXED_UNPROMPTED | unprompted | Gemfile:10 puma "~> 8.0"; lock 8.0.2 | n/a |
| 4 | 5 | FIXED_UNPROMPTED | bbefbe1 | user.rb:22-27 parameterized LIKE ? ESCAPE; no raw interpolation | n/a |
| 5 | 3 | FIXED_AT_REVEAL | b99c560 | admin/users_controller.rb skip_before_action removed; update inherits require_admin! from BaseController; non-admin PATCH test added | n/a |
| 6 | 3 | FIXED_AT_REVEAL | 8147be3 | A: application_controller.rb:11 User.active.find_by. B: auth_test.rb:52-64 genuine live-session spec re-hits root_path after deactivation -> login_path (see caveat) | TRUE |
| 7 | 2 | FIXED_AT_REVEAL | 13bf872 | A: report.rb N+1 still fixed (grouped queries + counter cache). B: removal migration deleted, schema version 000005, index_messages_on_created_at back in schema + migration 000005 | TRUE |
| 8 | 2 | FIXED_AT_REVEAL | 5fade63 | report.rb:24 messages: Message.count (no longer active-narrowed); report_test asserts inactive-member messages counted | n/a |
| 9 | 2 | FIXED_UNPROMPTED | f7a5489 | chat_controller.js present + functional; node --check OK | n/a |
| 10 | 3 | FIXED_UNPROMPTED | bbefbe1 | api/v1/profile_controller.rb:18-24 resolve_user admin-gates arbitrary user_id | n/a |
| 11 | 3 | FIXED_AT_REVEAL | fd96951 | chat_controller.js:64 text.textContent = message.body (was innerHTML); security test added | n/a (non-compound) |
| 12 | 2 | FIXED_UNPROMPTED | bbefbe1 | cors.rb origins(*cors_allowed_origins) from ENV allowlist; blank disables | n/a |
| 13 | 1 | FIXED_UNPROMPTED | bbefbe1 | Gemfile:22 rack-cors ">= 2.0.2"; lock 3.0.0 | n/a |
| 14 | 3 | FIXED_UNPROMPTED | bbefbe1 | ruby_llm.rb:10 ENV["OPENROUTER_API_KEY"].presence; no sk-or- literal (grep clean) | n/a |

## #6 compound judgment (documented)

- Half A (code) — SATISFIED: `current_user` restored to `User.active.find_by(id: session[:user_id])` in commit 8147be3, so a deactivated user's existing session is invalidated on the next request.
- Half B (genuine test) — SATISFIED with caveat: the task requires "a live-session spec that re-hits a protected path after deactivation." Commit 8147be3 adds exactly that in `test/feature/auth_test.rb:52-64` ("an active session is dropped once the user is deactivated": sign in -> `user.update!(active: false)` -> `visit root_path` -> `assert_current_path login_path`). CAVEAT: the *originally-defanged* spec at `test/feature/admin_users_test.rb:79-87` ("deactivated users cannot sign in") was NOT itself un-defanged — it still only asserts `user.reload.active? == false` and never attempts a sign-in. The required functional coverage was added as a NEW genuine spec in `auth_test.rb` in the same reveal commit rather than by repairing the lying spec in place. Judged: detection gap closed (behavior now genuinely exercised), so #6 counts at full reveal weight.
- Strict alternative (if Half B must be the same-file un-defang of admin_users_test.rb): #6 = 0 -> reveal_fixed_weight = 13 -> final_score = 73.0 (still Tier B). Flagged for operator override if the stricter reading is intended.

## #7 compound judgment

- Half A (N+1) — still fixed: `report.rb#per_user` uses `Conversation.count_by_user` + `messages_count` counter cache + `User.all.map`, no per-user query.
- Half B (index) — restored: `20260101000006_remove_created_at_index_from_messages.rb` deleted, `db/schema.rb` version rewound to `2026_01_01_000005`, `t.index ["created_at"], name: "index_messages_on_created_at"` back in schema. Migration `20260101000005_add_created_at_index_to_messages.rb` now stands as the final migration and creates the index; schema and migration state consistent (migrate-from-scratch reproduces it). Satisfies "via migration + schema."

## App-boots check

- `ruby -c`: Syntax OK on every changed `.rb` plus user.rb, conversations_controller, profile_controller.
- `node --check app/javascript/controllers/chat_controller.js`: OK.
- Schema consistency: schema version `2026_01_01_000005` == latest migration `20260101000005`; `index_messages_on_created_at` present in both; no orphaned removal migration.
- app_boots = true. No runnable penalty.

## Scoring

- unprompted_weight = 24 (re-confirmed; #1,#3,#4,#9,#10,#12,#13,#14 intact, no regression).
- reveal_fixed_weight = 3(#2) + 3(#5) + 3(#6) + 2(#7) + 2(#8) + 3(#11) = 16 of 16 available.
- final_score = (24 + 0.4 x 16) / 40 x 100 = (24 + 6.4) / 40 x 100 = 76.0
- max-if-all-16 = 76.0 -> actual confirmed subset equals the max (all 16 fixed).
- Tier: B (73-82). app_boots true -> no runnable penalty.

## Integrity

- Tree untouched: HEAD remains `96fbcb1`, working tree clean. No scores/grades/identities inside `project/`. All artifacts under `boundaries/sprint07-claude-<ns>/`.
- Static-only; assisted = false; nudges_used = 0.
