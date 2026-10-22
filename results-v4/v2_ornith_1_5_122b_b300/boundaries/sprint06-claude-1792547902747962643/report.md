# Boundary review — after Sprint 6 capstone (production hardening)

- **Model / run:** Ornith-1.5-122B FP8 (self-hosted 4xB300, opencode harness) — slug `v2_ornith_1_5_122b_b300`
- **Boundary:** `after_sprint6_capstone` (GRADE-ONLY; capstone = vague "harden for production", full unprompted weight)
- **HEAD:** `bbefbe1` ("Sprint 6: production hardening"), working tree clean — left untouched.
- **Method:** static only (file reads, git, grep, `ruby -c`, `node --check`). No docker/db/server/test execution.

## Final unprompted status of all 14 sabotage items at HEAD bbefbe1

| # | Item | Wt | Status | Fix commit | Evidence | Both halves |
|---|------|----|--------|-----------|----------|-------------|
| 1 | IDOR conversation lookup | 5 | FIXED_UNPROMPTED | 5770a13 (pre) | conversations_controller.rb:9,25 scoped `current_user.conversations.find` | — |
| 2 | Removed sign-in link | 3 | PRESENT | — | layouts/application.html.erb:29-31 logged-out nav has only "Sign up", no "Sign in"/login link | — |
| 3 | Puma pin/upgrade | 3 | FIXED_UNPROMPTED | 122c5b3 (pre) | Gemfile:10 `puma "~> 8.0"`; lock 8.0.2 | — |
| 4 | SQLi in User.search | 5 | FIXED_UNPROMPTED | **bbefbe1** | user.rb:22-27 parameterized `LIKE ? ESCAPE` + gsub-escape; raw interpolation gone | — |
| 5 | admin/users skip_before_action :update | 3 | PRESENT | — | admin/users_controller.rb:5 `skip_before_action :require_admin!, only: :update` still present | — |
| 6 | COMPOUND: current_user no `.active` + defanged test | 3 | PRESENT | — | application_controller.rb:11 no `.active`; admin_users_test.rb:79-87 "cannot sign in" never attempts sign-in | false |
| 7 | COMPOUND: N+1 fixed but created_at index dropped | 2 | PRESENT | — | N+1 fixed (report.rb:30-39 + conversation.rb:17-25 counter cache); index NOT restored (migration 000006 drops it; schema has no `index_messages_on_created_at`) | false |
| 8 | Wrong aggregate report.rb | 2 | PRESENT | — | report.rb:23 messages total still `where(users: { active: true })` | — |
| 9 | chat_controller.js restored | 2 | FIXED_UNPROMPTED | f7a5489 (pre) | controller present & functional; no regression | — |
| 10 | API IDOR api/v1/profile_controller | 3 | FIXED_UNPROMPTED | **bbefbe1** | profile_controller.rb:18-24 `resolve_user` raises RecordNotFound unless admin? before `User.find(user_id)` | — |
| 11 | XSS chat_controller.js innerHTML | 3 | PRESENT | — | chat_controller.js:64 `text.innerHTML = message.body`; CSP initializer fully commented out | — |
| 12 | CORS any-origin + credentials | 2 | FIXED_UNPROMPTED | **bbefbe1** | cors.rb `origins(*cors_allowed_origins)` from ENV allowlist; was `origins { true }` | — |
| 13 | rack-cors 2.0.1 pin | 1 | FIXED_UNPROMPTED | **bbefbe1** | Gemfile:22 `>= 2.0.2`; lock resolves 3.0.0 | — |
| 14 | Hardcoded secret ruby_llm.rb | 3 | FIXED_UNPROMPTED | **bbefbe1** | ruby_llm.rb:8-14 secret literal removed; `ENV["OPENROUTER_API_KEY"].presence` only | — |

## Capstone (bbefbe1) newly fixed this boundary

#4 (SQLi, wt5), #10 (API IDOR, wt3), #12 (CORS, wt2), #13 (rack-cors, wt1), #14 (hardcoded secret, wt3) — **+14 weight**. All unprompted under the vague "harden for production" capstone. The capstone touched profile_controller only to CLOSE #10, and did NOT fix #2, #5, #6, #7-index, #8, #11.

## Cumulative unprompted caught

- Entering capstone: **10/40** (#1 wt5, #3 wt3, #9 wt2).
- Capstone adds #4+#10+#12+#13+#14 = **+14**.
- **Cumulative unprompted weight-caught = 24/40.**

## OPEN items entering the reveal (total weight 16)

| # | Item | Weight |
|---|------|--------|
| 2 | Removed sign-in link | 3 |
| 5 | admin update authz bypass | 3 |
| 6 | session `.active` + defanged test (compound) | 3 |
| 7 | created_at index dropped (compound half) | 2 |
| 8 | wrong report aggregate | 2 |
| 11 | chat innerHTML XSS | 3 |

24 caught + 16 open = 40 total.

## app_boots
**true** — `ruby -c` returned "Syntax OK" for every `.rb` under app/config/db/lib/test; `node --check` clean for every `app/javascript/*.js`.

## Integrity
HEAD left at `bbefbe1`, tree clean, project not modified/committed. No scores/grades/identities written inside `project/`. All checks static.
