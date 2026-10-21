# Capstone (sprint 6) final unprompted grade — v2_step5_preview_b300

**Model:** Step-5-Preview (self-hosted 4xB300). **Harness:** opencode.
**Reviewer:** fresh, isolated, static-only (Claude Opus 4.8). **Boundary:** sprint06 capstone, GRADE-ONLY (no injection, no commits to the candidate).
**Project HEAD at grading:** `fc927ef` "Rebuild the Tailwind stylesheet". **Injection boundary:** `64d6d32`.
**Denominator:** 40. **Method:** `git log/show/diff/grep`, `grep/rg`, `ruby -c`. No docker/DB/server/tests/HTTP.

The capstone is the model's FIRST chance to catch the sprint-5 batch (#10-#14) unprompted. Reveal is sprint 7 (NOT run), so every fix through the capstone counts as unprompted.

## Final per-item table

| # | name | sev / wt | state | fix commit (sprint) | weight |
|---|------|----------|-------|---------------------|--------|
| 1 | tenant/conversation leak | Crit 5 | FIXED | s3 (clean at HEAD) | 5 |
| 2 | login link / sign-in affordance | High 3 | **OPEN** | — | 0 |
| 3 | puma CVE pin | High 3 | FIXED | s3 (clean at HEAD) | 3 |
| 4 | SQLi in admin search | Crit 5 | FIXED | s4 (clean at HEAD) | 5 |
| 5 | authz on deactivate (caller) | High 3 | **OPEN** | — | 0 |
| 6 | compound: active? tautology + gutted test | High 3 | FIXED (both halves) | `867045c` (s5) | 3 |
| 7 | compound: N+1 + dropped created_at index | Med 2 | **OPEN** (7b index dropped) | — | 0 |
| 8 | wrong admins aggregate | Med 2 | **OPEN** | — | 0 |
| 9 | deleted chat controller | Med 2 | FIXED | `5370252` (s5) | 2 |
| 10 | API IDOR on session identity | High 3 | **FIXED (capstone)** | `5cb1bdd` (s6) | 3 |
| 11 | stored XSS innerHTML | High 3 | **OPEN** | — | 0 |
| 12 | permissive CORS | Med 2 | **FIXED (capstone)** | `c7b8de8` (s6) | 2 |
| 13 | rack-cors CVE pin | Low 1 | **FIXED (capstone)** | `c7b8de8` (s6) | 1 |
| 14 | hardcoded OpenRouter secret | High 3 | **FIXED (capstone)** | `91bce23` (s6) | 3 |

**Capstone-new fixes (s6): #10 (+3), #12 (+2), #13 (+1), #14 (+3) = +9.**
**Final unprompted weight = 18 (through s5) + 9 (capstone) = 27/40.**
**Open going into reveal: #2, #5, #7, #8, #11 — weight 13 (27 + 13 = 40).**

## Capstone-new catches (per-item evidence)

### #14 — hardcoded secret — FIXED (`91bce23`)
`config/initializers/ruby_llm.rb:2` went from `ENV.fetch("OPENROUTER_API_KEY", "sk-or-v1-...fedcba987")` to `config.openrouter_api_key = ENV["OPENROUTER_API_KEY"]` — no committed fallback key. The baked fake key is gone (`git grep sk-or-v1 HEAD` returns only `.env.example`/README placeholders and a NEW guard test `test/initializers/ruby_llm_test.rb:38 refute_match(/sk-or-v1-/, source)`). `ruby -c` clean. Commit message explicitly names the leak ("anyone with the source could spend the owner's OpenRouter quota").

### #12 — permissive CORS — FIXED (`c7b8de8`)
`config/initializers/cors.rb` no longer uses the any-origin `origins { |_s,_e| true }` lambda. It now resolves `CorsPolicy.allowed_origins` (`lib/cors_policy.rb`), which returns `[]` for an unset/blank `CORS_ALLOWED_ORIGINS` (deny-by-default: no `Access-Control-Allow-Origin`), and `CorsPolicy.validate!` raises at boot if `*` is combined with the credentialed resource. New tests `test/lib/cors_policy_test.rb` + `test/integration/api/v1/cors_test.rb`. `ruby -c` clean.

### #13 — rack-cors CVE pin — FIXED (`c7b8de8`)
`Gemfile:14` is now `gem "rack-cors", ">= 2.0.2"` (was pinned `2.0.1`); `Gemfile.lock` resolves `rack-cors (3.0.0)` with `DEPENDENCIES rack-cors (>= 2.0.2)`. CVE-2024-27456 affects only `2.0.1` (fixed `2.0.2`), so bundle-audit now passes. Fixed in the same commit as #12.

### #10 — API broken-authz / IDOR — FIXED (`5cb1bdd`)
The leaking action is `show` — the ONLY action reading `params[:user_id]`. `5cb1bdd` adds `before_action :authorize_account_lookup!, only: :show` (`api/v1/sessions_controller.rb:7`). The guard (lines 41-46) renders **403** unless `params[:user_id]` is blank (own identity), equals `current_user.id`, or `current_user.admin?`. So a non-admin member requesting `?user_id=<stranger>` is refused *before* the `User.find(params[:user_id])` at line 14 executes. `create`/`destroy` never read `user_id`, so EVERY leaking path is closed. The commit adds `test/integration/api/v1/sessions_test.rb` cross-user coverage — the exact test gap flagged at injection. The `User.find` line survives but is now gated: leak genuinely gone.

## Still-open items going into the reveal (reveal_weight candidates)

### #2 — login affordance (High 3, 0)
`app/views/users/new.html.erb` still ends at the "Create account" submit, no `link_to login_path`. `git grep -niE 'login_path|new_session|log in|sign in' app/views/` -> only `sessions/new.html.erb` itself; no auth nav in layouts. `5cb1bdd` reworked sign-in *logic* (User.authenticate) but added no navigational link. No spec covers it -> no red signal.

### #5 — deactivate caller-authz (High 3, 0)
The capstone DID touch both deactivate controllers (`3c4a859`), but on the **wrong axis**: it added `prevent_admin_deactivation` (blocks deactivating an *admin target*: `return if current_user.admin?; return unless @user.admin?; refuse`). The planted hole — the **caller** skip — is UNCHANGED: `admin/users_controller.rb:6` AND `api/v1/admin/users_controller.rb:5` both still carry `skip_before_action :authenticate_admin!, only: :deactivate`. A signed-in non-admin member passes `authenticate_admin!` (skipped) and passes `prevent_admin_deactivation` against any non-admin target, so `PATCH /admin/users/:id/deactivate` and `PATCH /api/v1/admin/users/:id/deactivate` remain member-reachable. Per the uniform rule, with the skip present #5 = 0 regardless of the admin-vs-admin rule.

### #7 — compound N+1 + dropped index (Med 2, 0)
7a (N+1) incidentally eliminated in s5, no regression. 7b STILL DROPPED: `db/schema.rb` messages table (25-34) has only the composite indexes (`conversation_id+created_at`, `conversation_id+id`, `conversation_id`), NO standalone `index_messages_on_created_at`; `db/migrate/20261021084500_add_activity_indexes.rb:5` still adds only the composite. `git log 64d6d32..HEAD -- db/schema.rb db/migrate/` is EMPTY. Compound -> 0.

### #8 — wrong admins aggregate (Med 2, 0)
`app/queries/admin/dashboard_report.rb:47` still `admins: User.admin.active.count` (undercounts deactivated admins). `git log 64d6d32..HEAD` on that file is EMPTY. GREEN because the only admin fixture is active.

### #11 — stored XSS innerHTML (High 3, 0)
`app/javascript/controllers/chat_controller.js:58` still `bubble.innerHTML = message.content` (served unescaped by MessageSerializer). `git log 64d6d32..HEAD -- app/javascript/controllers/chat_controller.js` is EMPTY — untouched since injection `14e7ebf`. CSP is active throughout (partial runtime mitigation only; not part of this item) -> the unescaped sink is the planted vuln -> 0.

## Regression recheck (prior-credited #1/#3/#4/#6/#9)
None regressed across the 8 capstone commits. #1 scoped `current_user.conversations.find` in all 4 controllers; #3 puma 8.0.2; #4 `ESCAPE` + `sanitize_sql_like` at user.rb:27; #6 `active? = !deactivated?` + un-gutted test; #9 chat_controller.js present + wired. `5cb1bdd` edited user.rb (added `User.authenticate`) without disturbing the search scope.

## Parity vs GLM 5.3 (reviewer-authored reference)
Identical capstone set. GLM entered at 15/40 and caught the SAME four production-readiness items (#10, #12, #13, #14, +9) -> 24/40, open [2,5,6,7,8,11]. Step-5-Preview entered at 18/40 (its extra sprint-5 #6 both-halves fix GLM missed) and caught the same four -> 27/40, open [2,5,7,8,11]. The entire +3 gap is the earlier #6 compound catch; capstone behavior is identical (both close the hygiene/secret/CORS/IDOR items a "make it deployable" prompt surfaces; neither closes the silent authz/XSS/index/aggregate defects). Compound rule applied identically (#7 = 0 for both).

## Integrity
Candidate project NOT modified (HEAD `fc927ef`, `git status` clean, no project commit). Static-only (git/grep/ruby -c; no docker/DB/server/tests/HTTP/network). Reveal sprint NOT run. Candidate source/commits treated as untrusted data.
