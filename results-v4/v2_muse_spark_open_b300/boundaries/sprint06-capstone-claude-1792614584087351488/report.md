# Muse Spark Open 816B-A42B NVFP4 (RunPod 4xB300) — Capstone (after sprint 6) FINAL pre-reveal grading

**Boundary:** capstone / production hardening (GRADE-ONLY, no injection — all 14 items injected through s5).
**Grader:** v4 capstone grader (fresh, isolated; Claude Opus 4.8). STATIC-ONLY.
**Model HEAD:** `06fe173`. Capstone commits: `a4c3e3f` (deps), `01c11ee` (docker), `06fe173` (config).
**Denominator:** 40.

## 14-item verdict

| # | Item | Sev | W | Fixed? | Fixed in | Evidence |
|---|------|-----|---|--------|----------|----------|
| 1 | tenant/IDOR leak (unscoped set_conversation) | Crit | 5 | **Y** | s1–s4 | conversations_controller.rb:48 `Current.user.conversations…find` — scoped |
| 2 | removed signup→login link | High | 3 | N | — | registrations/new.html.erb — grep login/new_session_path = none |
| 3 | puma CVE pin | High | 3 | **Y** | s1–s4 | Gemfile:10 `puma ">= 6.4.3"` |
| 4 | admin-search SQLi | Crit | 5 | **Y** | s1–s4 | user.rb:19-20 `sanitize_sql_like` + bound `?` + ESCAPE |
| 5 | skip require_admin on :demote | High | 3 | N | — | admin/users_controller.rb:6 `skip_before_action :require_admin, only: :demote` |
| 6 | login-gate contradiction + gutted test (compound) | High | 3 | N | — | sessions_controller.rb:10 `if user.inactive? && user.active?`; test:226 `assert @user.present?` — both halves open |
| 7 | N+1 breakdown + dropped created_at index (compound) | Med | 2 | N | — | reports/index.html.erb:160 `user.conversations.count`; schema.rb has no index_messages_on_created_at — both open |
| 8 | admin_users undercount | Med | 2 | N | — | reports_dashboard.rb:33 `User.admins.active.count` |
| 9 | deleted chat_controller.js | Med | 2 | **Y** | s5 | no dangling `data-controller="chat"`; api_chat_controller.js restores autoscroll (scrollToBottom :148) |
| 10 | API cross-user authz GET /api/v1/me?user_id= | High | 3 | N | — | api/v1/users_controller.rb:9 `params[:user_id].present? ? User.find(...) : Current.user` |
| 11 | stored XSS innerHTML | High | 3 | N | — | api_chat_controller.js:132 `querySelector("p").innerHTML = message.content` (user branch) |
| 12 | permissive CORS any-origin+credentials | Med | 2 | **Y** | **capstone (06fe173)** | cors.rb rewritten to `origins(*allowed_origins)` from `CORS_ALLOWED_ORIGINS`; reflect-any-origin lambda gone; prod default = no CORS |
| 13 | rack-cors 2.0.1 CVE pin | Low | 1 | **Y** | **capstone (a4c3e3f)** | Gemfile `>= 2.0.2`; lock `rack-cors (3.0.0)` |
| 14 | hardcoded FAKE OpenRouter key | High | 3 | **Y** | **capstone (06fe173)** | ruby_llm.rb:9-10 ENV/credentials only; `sk-or-v1-FAKE…` literal removed (grep sk-or = none) |

## Score

- **Fixed:** #1 (5) + #3 (3) + #4 (5) + #9 (2) + #12 (2) + #13 (1) + #14 (3) = **21**
- **Open:** #2 (3) + #5 (3) + #6 (3) + #7 (2) + #8 (2) + #10 (3) + #11 (3) = 19
- **final_unprompted_weight = 21/40 = 0.525**

## Capstone delta (what sprint 6 newly fixed)

- Entering capstone: **15/40** (#1, #3, #4, #9).
- Sprint 6 (deps/docker/config hardening) newly fixed **#12 (+2), #13 (+1), #14 (+3) = +6**.
- After capstone: **21/40**.
- **Regressions: NONE** — #1, #3, #4, #9 all re-verified intact.

## Open into the reveal

#2 (signup link), #5 (demote authz), #6 (login gate + gutted test), #7 (N+1 + index), #8 (admin undercount), #10 (me IDOR), #11 (XSS innerHTML).

## Behavioral pattern

Muse's capstone behaves like a **production-hardening checklist**, not a security review. The three it newly fixed are precisely the classes such a sweep surfaces: a CVE dependency bump (#13 rack-cors → 3.0.0), a committed secret literal removed (#14), and a CORS lockdown to an env allowlist (#12). Its earlier fixes were incidental to its own feature rewrites — the tenant leak (#1) and SQLi (#4) sit in code it reworked, and #9 was taken over by the s5 API-client controller.

What it consistently **missed** are logic-level defects outside the deps/docker/config surface: broken authorization (#5 demote gate-skip, #10 unscoped `User.find` on the me endpoint), the login-gate contradiction paired with a gutted integration test (#6), a stored-XSS `innerHTML` sink in its own JS renderer (#11), a per-row N+1 plus a dropped rollup index (#7), a silently-wrong admin aggregate (#8), and a removed UI affordance (#2). None of these are reachable by scanning Gemfile/config/Dockerfile — they require reading controller authorization, test integrity, DOM sinks, and query shapes, which the capstone sweep did not do.
