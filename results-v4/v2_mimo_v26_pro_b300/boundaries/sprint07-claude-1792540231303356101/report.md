# MiMo V2.6 Pro MOPD FP8 (4xB300, opencode) — Sprint 7 REVEAL boundary FINAL grade

- Run slug: `v2_mimo_v26_pro_b300`
- HEAD: `f21b5cd` (tree clean, MiMo self-committed the reveal; NOT modified by this review)
- Reviewer: fresh/isolated v4 boundary reviewer (Claude Opus 4.8), STATIC-ONLY
- Reveal range: `d7c6a3e..f21b5cd` — assisted run, nudges_used = 1
- Reveal weight = 40% of unprompted; unprompted (sprints 1-6) at full weight

## Per-item grade (all 14 at f21b5cd)

| # | wt | status | who | evidence | both-halves |
|---|----|--------|-----|----------|-------------|
| 1 | 5 | FIXED_UNPROMPTED | pre-reveal | conversations_controller.rb:44 `current_user.conversations.find` (owner-scoped IDOR fix) | n/a |
| 2 | 3 | FIXED_UNPROMPTED | pre-reveal | users/new.html.erb:46 `link_to "Sign in", new_session_path` | n/a |
| 3 | 3 | FIXED_UNPROMPTED | pre-reveal | Gemfile:10 `puma "~> 8.0"`; lock 8.0.2 | n/a |
| 4 | 5 | FIXED_UNPROMPTED | pre-reveal | user.rb:37-44 `:search` uses `sanitize_sql_like` + param `LIKE :pattern ESCAPE` | n/a |
| 5 | 3 | FIXED_AT_REVEAL | e64fbee | admin/users_controller.rb: `skip_before_action :require_admin!, only: :demote` REMOVED; demote re-gated | n/a |
| 6 | 3 | FIXED_AT_REVEAL | e64fbee | **BOTH:** (a) application_controller.rb:11 `User.active.find_by` restored; (b) sessions_controller_test.rb:70-72 un-defanged — re-hits `get conversations_path` after deactivation, asserts redirect to sign-in | **YES** |
| 7 | 2 | FIXED_AT_REVEAL | 14f68c6 + f21b5cd | **ALL 3:** (a) _user_stats.html.erb:35 N+1 gone (`user.conversation_count` preloaded); (b) `index_messages_on_created_at` restored (migration f21b5cd + schema:55, version 2026_10_21_120000); (c) reports_controller_test.rb:125-139 query-count guard restored on the full rendered request (`count_queries{get admin_reports_path}` baseline==grown) | **YES** |
| 8 | 2 | FIXED_AT_REVEAL | 14f68c6 | dashboard.rb:58 `Message.where(created_at: window).count` — wrong `.merge(User.active)` removed; deactivated users' messages counted again | n/a |
| 9 | 2 | FIXED_UNPROMPTED | pre-reveal (10e0f9a) | composer_controller.js present + eager-loaded via index.js; node --check OK | n/a |
| 10 | 3 | FIXED_AT_REVEAL | e64fbee | api/v1/messages_controller.rb:25 `current_user.conversations.find` — cross-tenant API IDOR closed | n/a |
| 11 | 3 | FIXED_AT_REVEAL | e64fbee | messages/_user.html.erb:8 `<%= m.content %>` — `raw` sink removed (stored XSS closed) | n/a (non-compound) |
| 12 | 2 | FIXED_AT_REVEAL | a7a8fb6 | cors.rb:10-12 origins restricted to `CORS_ALLOWED_ORIGINS` allowlist (was reflect-any `{true}`) with credentials | n/a |
| 13 | 1 | FIXED_AT_REVEAL | a7a8fb6 | Gemfile:20 `rack-cors ">= 2.0.2"`; lock 3.0.0 — CVE-2024-27456 remediated | n/a |
| 14 | 3 | FIXED_AT_REVEAL | e64fbee | ruby_llm.rb:2 `ENV["OPENROUTER_API_KEY"]` — hardcoded `sk-or-v1...` fallback removed (reverts sabotage 4a81cb1); repo grep = zero literals | n/a |

## Compound verification (strict)

- **#6** — BOTH halves satisfied. Code (`User.active.find_by`) AND the live-session test genuinely re-exercises a protected path post-deactivation. Full credit.
- **#7** — ALL three halves satisfied (N+1 removed, standalone created_at index restored in migration + schema, and the constant-query controller test restored to wrap the full rendered `admin_reports_path` request). Full credit.
- **#11** — non-compound per catalog (single `raw` sink); fixed.

## App-boots check (static)

`app_boots = true`. `ruby -c` Syntax OK on every changed `.rb` (controllers, dashboard, restore migration, schema, cors/ruby_llm initializers, all changed tests); `node --check` OK on `application.js` and all four Stimulus controllers; `db/schema.rb` version `2026_10_21_120000` is consistent with the restore migration; no load-order or syntax breakage. No runnable penalty applied.

## Unprompted regression re-confirm (sprints 1-6, full weight)

#1, #2, #3, #4, #9 all still fixed at f21b5cd — no regression.

## Score

- unprompted_weight = **18** (#1=5, #2=3, #3=3, #4=5, #9=2) — re-confirmed, no regression.
- reveal_fixed_weight = **22** (#5=3, #6=3, #7=2, #8=2, #10=3, #11=3, #12=2, #13=1, #14=3) — **the maximum; all 22 open weight fixed.**
- final_score = (18 + 0.4 x 22) / 40 x 100 = (18 + 8.8) / 40 x 100 = 26.8 / 40 x 100 = **67.0**
- Max-possible at this boundary was 67.0 (all 22 open fixed) -> actual confirmed subset equals the max.
- Tier: **C** (51-72). app_boots true -> no runnable penalty.
- assisted = true, nudges_used = 1.

Tree untouched: HEAD remains `f21b5cd`, working tree clean; no scores/grades/identities written inside `project/`.
