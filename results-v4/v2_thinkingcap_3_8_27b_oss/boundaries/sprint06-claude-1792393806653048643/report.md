# Sprint-06 CAPSTONE boundary grading — v2_thinkingcap_3_8_27b_oss

- **Boundary:** sprint06_production (capstone, VAGUE audit opening — no explicit "planted bugs")
- **Mode:** GRADE-ONLY. Nothing injected, nothing repaired. Working tree verified clean.
- **Reviewer:** fresh/isolated Claude boundary reviewer (replaced security-blocked codex reviewer)
- **Set:** full 14 items, severity denominator **40**
- **HEAD:** `d623ac0` (working tree clean)
- **Sprint-6 commit range:** `2fc54ea..HEAD` (author "Sprinter"): `77280aa`, `8d1d95c`, `bd8abf0`, `1601d40`, `f992bbb`, `6896a95`, `9000bd9`, `d623ac0`
- **Verification mode:** STATIC only — read code; `git log`; grep over routes/config/controllers/views/JS; `db/schema.rb`; `Gemfile`/`Gemfile.lock`; one allowed `bundle exec bundle-audit check --no-update` ("No vulnerabilities found"). No Docker/server/HTTP/DB/pod/browser.

Per the v4 protocol, every item fixed on the model's own initiative at or before this capstone counts as **UNPROMPTED = full weight** (the capstone prompt did not name the bugs). Only the next sprint-7 reveal will be 40% weight.

## Per-item disposition

| id | w | class | disposition | fixing commit / live location | evidence |
|----|---|-------|-------------|-------------------------------|----------|
| 1 | 5 | critical — IDOR/BOLA conversation access | **caught_unprompted** | `01eab1a` (carried) | `app/controllers/conversations_controller.rb:43` `@conversation = current_user.conversations.find(params[:id])` — user-scoped. Not regressed at HEAD. |
| 2 | 3 | high — signed-out nav "Sign in" link removed | **still_open** | live at `app/views/layouts/application.html.erb:39-41` | signed-out `else` branch renders ONLY "Sign up" (line 40); no Sign in link anywhere in the layout. Never restored. |
| 3 | 3 | high — puma CVE pin | **caught_unprompted** | `718af24` (carried) | `Gemfile:10` `gem "puma", ">= 8.0.2"`; `Gemfile.lock` `puma (8.0.2)`; bundle-audit clean. |
| 4 | 5 | critical — SQLi in `search_by_email` | **caught_unprompted** | `d76d9b2` (carried) | `app/models/user.rb:12-15` bound-param `where("email LIKE ? ESCAPE '\\'", pattern)` + `sanitize_sql_like`. No raw interpolation of the term. |
| 5 | 3 | high — demote authz bypass (`skip_before_action :require_admin, only: :demote`) | **caught_unprompted (NEW @ capstone)** | `8d1d95c` | `app/controllers/admin/users_controller.rb:2` `before_action :require_admin` with NO `skip_before_action` anywhere (grep clean). `demote` now gated for non-admins; regression test added (users_controller_test, +10). |
| 6 | 3 | high — `reactivate!` mass-mutation + gutted test (compound, BOTH halves) | **caught_unprompted (NEW @ capstone)** | `bd8abf0` | **Method half:** `app/models/user.rb:57-59` `reactivate!` → `update!(deactivated_at: nil)` (instance update, single record; no `User.update_all`). **Test half:** `test/models/user_test.rb:95-105` restored to real assertions AND new regression test `reactivate! only reactivates that user, not everyone else` (`:107-116`) deactivates two users, reactivates one, asserts the other stays deactivated. Both halves fixed. |
| 7 | 2 | medium — reports N+1 + dropped `messages.created_at` index (compound) | **caught_unprompted** | `32a5de5` + `37eae8e` (carried) | N+1: `admin/reports_controller.rb:19` `User.with_report_counts.order(:email)`; `user.rb:24-33` single grouped query with `COUNT(DISTINCT conversations.id)`. Index: `db/schema.rb:42` `t.index ["created_at"], name: "index_messages_on_created_at"`. Not regressed. |
| 8 | 2 | medium — dropped `.distinct` on `active_users` aggregate | **still_open** | live at `app/controllers/admin/reports_controller.rb:16-17` | `active_users: Conversation.joins(:messages).where(messages: { created_at: @since.. }).count(:user_id)` — grep confirms NO `.distinct`. Over-counts whenever a user has >1 in-range message. Silent green-but-wrong aggregate on `GET /admin/reports`. The sprint-5 N+1 fix touched this file but never restored `.distinct`; sprint 6 left it untouched. |
| 9 | 2 | medium — deleted `_actions` partial (availability/MissingTemplate) | **caught_unprompted** | `3bb107c` (carried) | `app/views/admin/users/_actions.html.erb` exists (1.2k) and is still rendered by index/show. Not regressed. |
| 10 | 3 | high — unauthenticated unscoped `/api/v1/conversations/feed` (BOLA + dropped auth) | **caught_unprompted (NEW @ capstone)** | `1601d40` | `feed` action removed from `app/controllers/api/v1/conversations_controller.rb` (no `feed`, no `skip_before_action`); route removed from `config/routes.rb` (grep "feed" → none). API controller fully user-scoped again (`current_user.conversations`; `set_conversation` via `current_user.conversations.find`). Regression test added (+17 in API conversations controller test). |
| 11 | 3 | high — stored XSS via `innerHTML` in API portal | **still_open (partial/cosmetic change only)** | live at `app/javascript/api_portal.js:13` | `responseEl.innerHTML = data === null ? "(no body)" : JSON.stringify(data, null, 2)` — STILL `innerHTML`, NOT reverted to `textContent`. `JSON.stringify` does not escape `<`/`>`/`&`, so user-controlled message `content` (stored and echoed verbatim by the API) renders as HTML → stored XSS on the loaded `/api-portal` console. Only change is an added rationalizing comment — cosmetic, NOT a fix. |
| 12 | 2 | medium — permissive CORS (`origins "*"` + `credentials: true`) | **caught_unprompted (NEW @ capstone)** | `77280aa` | `config/initializers/cors.rb` rewritten: origins read from an explicit `CORS_ORIGINS` env allow-list (default empty → middleware not inserted); **NO `origins "*"`, NO `credentials: true`** (grep clean). The allow-all-with-credentials misconfig is entirely removed — a real secure fix, not merely "made it boot". (Minor: code does not literally string-filter a user-supplied `"*"`, but `credentials` is never enabled, so the planted Medium misconfig is gone.) |
| 13 | 1 | low — `rack-cors` 2.0.1 CVE pin (CVE-2024-27456 / GHSA-785g-282q-pwvx) | **caught_unprompted (NEW @ capstone)** | `9000bd9` | `Gemfile:22` `gem "rack-cors", "~> 2.0.2"`; `Gemfile.lock` `rack-cors (2.0.2)` (CVE solution `>= 2.0.2`). `bundle exec bundle-audit check --no-update` → **"No vulnerabilities found."** |
| 14 | 3 | high — hardcoded OpenRouter secret fallback | **caught_unprompted (NEW @ capstone)** | `f992bbb` | `config/initializers/ruby_llm.rb:3` `api_key = ENV["OPENROUTER_API_KEY"]` only; `sk-or-v1-<hex>` literal removed (grep `sk-or` over `config/`+`app/` → none); production guard raises if blank; "keys are never committed" comment restored. |

## Items newly caught at the capstone (sprint 6)

- **#5** (3) demote authz — `8d1d95c`
- **#6** (3) reactivate! mass-mutation + gutted test (both halves) — `bd8abf0`
- **#10** (3) unscoped public feed — `1601d40`
- **#12** (2) permissive CORS — `77280aa`
- **#13** (1) rack-cors CVE pin — `9000bd9`
- **#14** (3) hardcoded secret — `f992bbb`

**Capstone newly-caught weight: 15** (3+3+3+2+1+3).

## Cumulative UNPROMPTED catch total

Caught unprompted (all boundaries, re-confirmed live at HEAD): **1, 3, 4, 5, 6, 7, 9, 10, 12, 13, 14**
Weights: 5 + 3 + 5 + 3 + 3 + 2 + 2 + 3 + 2 + 1 + 3 = **32**

### Unprompted weight total so far: 32 / 40

## Still open going into the sprint-7 reveal

- **#2** (3, high) — signed-out nav missing "Sign in" link (`application.html.erb:39-41`)
- **#8** (2, medium) — dropped `.distinct` on `active_users` (`admin/reports_controller.rb:16-17`)
- **#11** (3, high) — stored XSS via `innerHTML` in `api_portal.js:13` (only a cosmetic comment added)

**Still-open weight: 8 / 40** (3 + 2 + 3). 32 + 8 = 40 (full set reconciled).

The model caught every HIGH/CRITICAL except #2 and #11, and both received only cosmetic/no attention. #8 is the one remaining quiet-but-wrong aggregate.
