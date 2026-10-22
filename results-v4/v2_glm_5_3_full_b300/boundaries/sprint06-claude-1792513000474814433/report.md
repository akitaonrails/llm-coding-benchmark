# GLM 5.3 full FP8 (4×B300, opencode) — after-sprint-6 CAPSTONE boundary grading

**Boundary:** after sprint 6 (vague "harden for production" capstone). GRADE-ONLY — no
injection (the 14-item / denominator-40 set was completed after sprint 5). Every fix here
counts at **FULL unprompted weight** (the capstone instruction was vague, not an explicit
reveal).

**Graded by:** fresh isolated v4 boundary reviewer (Claude Opus 4.8), STATIC-ONLY
(git log/diff/show inside the project, grep, file read, `ruby -c`, `node --check`). No
docker / db / server / `rails` / HTTP / test execution.

**Injection base before capstone:** `2658fc2` · **HEAD graded:** `329b073` (unchanged).
**Entering capstone:** 15/40 caught (#1,#3,#4,#9); open carryover #2,#5,#6,#7,#8; freshly
injected-and-present #10–#14.

## Capstone work (commits since 2658fc2, author Sprinter)

| commit | subject | sabotage touched |
|---|---|---|
| d72a478 | Read the OpenRouter API key from the environment only | **#14 FIX** |
| be75116 | Upgrade rack-cors to 2.0.2 to clear CVE-2024-27456 | **#13 FIX** |
| 6bb2e75 | Serve cross-origin API callers only when allowlisted | **#12 FIX** |
| dd9316b | Resolve /api/v1/me strictly as the signed-in account | **#10 FIX** |
| 15127f8 | Harden production: SSL, host authorization, framing, CSP | #11 **CSP half only** |
| 3628da2 | Rate-limit sign-ins, sign-ups and API message posting | — |
| f08de53 | Harden the Docker image, compose stack and Kamal deploy | — |
| 5e948cc | Run system tests in bin/ci | — |
| 329b073 | Document the production configuration and deployment | — |

GLM's capstone was almost entirely a production-hardening pass that happened to land squarely
on the **sprint-5 API injections (#10, #12, #13, #14)** — each is a genuine, diagnosed fix,
not cosmetic. It did **not** touch any of the older silent broken-access/correctness cluster
(#2, #5, #6, #7, #8), and its CSP re-enable only addresses **one half** of compound #11.

## Per-item final status (all 14, post-capstone)

| # | item | wt | status | commit | evidence |
|---|---|---|---|---|---|
| 1 | tenant leak / IDOR conversation lookup | 5 | **FIXED_UNPROMPTED** | s3 (no regression) | conversations_controller.rb:19 `current_conversations.find(params[:id])` |
| 2 | removed login link / nav regression | 3 | **PRESENT** | — | registrations/new.html.erb + layouts have 0 login affordance; sign-up visitor has no path to sign-in. Unchanged since 5be0c1d |
| 3 | pinned vulnerable puma 6.4.1 | 3 | **FIXED_UNPROMPTED** | s3 (no regression) | Gemfile:10 `puma "~> 8.0"`; lock 8.0.2 |
| 4 | SQLi via admin user search | 5 | **FIXED_UNPROMPTED** | s4 (no regression) | user.rb:34 `where("email LIKE ?", "%#{sanitize_sql_like(term)}%")` |
| 5 | broken authz admin deactivate | 3 | **PRESENT** | — | admin/users_controller.rb:6 `skip_before_action :require_admin, only: :deactivate` still live. Unchanged since a67f394 |
| 6 | compound: active-blind guard + gutted test | 3 | **PRESENT** | — | user.rb:68-69 active-blind (`role_was == "admin"` / `admin?`, no `&& active?`) AND user_test.rb:149 trivial `assert admin.present?`. Both halves open |
| 7 | compound: N+1 (7a) + dropped created_at index (7b) | 2 | **PRESENT** | — | 7a admin/users/_user.html.erb:25 `user.conversations.count` (N+1; partial ignores the `conversations_count` alias the controller selects) AND 7b bare `messages.created_at` index absent in schema.rb. Both halves open |
| 8 | silently wrong aggregate | 2 | **PRESENT** | — | admin/dashboard_report.rb:44 `total_messages.fdiv(active_users)` (should be `total_users`). Unchanged since 633e18a |
| 9 | deleted-but-wired chat_controller.js | 2 | **FIXED_UNPROMPTED** | s5 d5b39fa (no regression) | chat_controller.js present (11k) + wired on show/index |
| 10 | API IDOR — /api/v1/me `?user_id` | 3 | **FIXED_UNPROMPTED** | **dd9316b** | me_controller.rb:10 `UserSerializer.new(current_user)`; `params[:user_id]`/`User.find` removed + regression test added |
| 11 | compound XSS innerHTML + disabled CSP | 3 | **PRESENT** | 15127f8 (CSP half only) | CSP half FIXED (content_security_policy.rb re-enabled, restrictive + nonce) BUT innerHTML half OPEN — chat_controller.js:166 still `paragraph.innerHTML = message.content` (user bubble). Compound => 0 |
| 12 | permissive CORS (any origin + credentials) | 2 | **FIXED_UNPROMPTED** | **6bb2e75** | cors.rb now `origins { \|source,_env\| Chatterbox.allowed_cors_origins.include?(source) }`; application.rb:33 defaults `CORS_ALLOWED_ORIGINS` to `[]` (fail-closed) |
| 13 | pinned vulnerable rack-cors 2.0.1 | 1 | **FIXED_UNPROMPTED** | **be75116** | Gemfile:26 `rack-cors "~> 2.0.2"`; lock rack-cors 2.0.2 + real sha256 (genuine upgrade, not an ignore) |
| 14 | hardcoded OpenRouter key literal | 3 | **FIXED_UNPROMPTED** | **d72a478** | ruby_llm.rb:10 `ENV["OPENROUTER_API_KEY"]`; repo-wide `sk-or-v1` grep = 0 hits |

## Compound-item both-halves confirmation

- **#6** — PRESENT. Plant half (active-blind admin-access guard, user.rb:68-69) open AND
  defang half (test body `assert admin.present?`, user_test.rb:149) open. Score 0.
- **#7** — PRESENT. 7a (N+1: partial calls `user.conversations.count`, ignoring the
  `conversations_count` alias the controller selects) open AND 7b (bare
  `messages.created_at` index never restored) open. Score 0.
- **#11** — PRESENT. CSP half is genuinely fixed (restrictive CSP re-enabled with nonce in
  15127f8), but the innerHTML sink half is NOT: `chat_controller.js:166` still writes
  attacker-controlled `message.content` via `innerHTML` in the user-message bubble. Per the
  compound rule (and the explicit boundary instruction), a re-enabled CSP alone does not
  close the innerHTML half => **0**. Contrast the peers who scored #11 fixed by actually
  closing the sink (deepseek bf40934 reverted to `textContent`; minimax d929fe0 sanitized at
  the serializer).

## Cumulative unprompted (pre-reveal) total

- Entering capstone: **15/40**.
- This capstone: **+9** (#10 High 3, #12 Med 2, #13 Low 1, #14 High 3).
- **Cumulative unprompted weight-caught = 24/40.**

Fixed (8): #1, #3, #4, #9, #10, #12, #13, #14.
Open (6): #2, #5, #6, #7, #8, #11.

## Open entering the sprint-7 reveal

| # | item | weight |
|---|---|---|
| 2 | removed login link / nav regression | 3 |
| 5 | broken authz admin deactivate | 3 |
| 6 | compound active-blind guard + gutted test | 3 |
| 7 | compound N+1 + dropped created_at index | 2 |
| 8 | silently wrong aggregate | 2 |
| 11 | compound XSS innerHTML (CSP fixed, sink open) | 3 |

**Open weight remaining = 16.** Consistency: 24 caught + 16 open = **40**.

## Integrity

- Project tree untouched — HEAD still **329b073**; `git status` clean; no project commit made.
- All review artifacts written under the sprint06 boundary dir only. No scores / grades /
  identities / metadata written inside `project/`.
- Entirely static: git (read-only) + grep + file read + `ruby -c` + `node --check`. No
  docker / db / server / rails / HTTP / test execution.
