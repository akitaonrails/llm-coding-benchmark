# Ledger — v2_glm_5_3_full_b300 — after sprint 6 (CAPSTONE, grade-only)

- **Boundary:** after-sprint-6 capstone (vague "harden for production"). GRADE-ONLY — no new
  injection; the 14-item / denominator-40 set was completed after sprint 5.
- **Scoring:** capstone is pre-reveal + vague, so every fix counts at FULL unprompted weight.
- **Graded by:** fresh isolated v4 boundary reviewer (Claude Opus 4.8), STATIC-ONLY.
- **Injection base before capstone:** 2658fc2 · **HEAD graded:** 329b073 (unchanged).

## Capstone remediations (this boundary, +9)

| # | item | wt | fix commit |
|---|---|---|---|
| 10 | API IDOR /api/v1/me ?user_id | 3 | dd9316b (me_controller.rb:10 -> current_user only + regression test) |
| 12 | permissive CORS (any origin + creds) | 2 | 6bb2e75 (cors.rb allowlist via Chatterbox.allowed_cors_origins; default empty/fail-closed) |
| 13 | pinned rack-cors 2.0.1 (CVE-2024-27456) | 1 | be75116 (Gemfile + lock -> rack-cors 2.0.2, real checksum) |
| 14 | hardcoded OpenRouter key | 3 | d72a478 (ruby_llm.rb:10 ENV only; 0 sk-or-v1 literals repo-wide) |

## Still OPEN entering sprint-7 reveal (16)

| # | item | wt | why open |
|---|---|---|---|
| 2 | removed login link / nav | 3 | registrations/new + layouts: no login affordance; unchanged since 5be0c1d |
| 5 | broken authz admin deactivate | 3 | admin/users_controller.rb:6 skip_before_action :require_admin, only: :deactivate |
| 6 | compound active-blind guard + gutted test | 3 | user.rb:68-69 active-blind AND user_test.rb:149 trivial assert — both halves open |
| 7 | compound N+1 + dropped created_at index | 2 | 7a _user.html.erb:25 user.conversations.count (alias ignored) AND 7b created_at index absent — both open |
| 8 | silently wrong aggregate | 2 | dashboard_report.rb:44 total_messages.fdiv(active_users) |
| 11 | compound XSS innerHTML + disabled CSP | 3 | CSP half FIXED (15127f8) but innerHTML sink OPEN (chat_controller.js:166) — compound => 0 |

## Compound both-halves status

- #6 PRESENT (both halves open). #7 PRESENT (both halves open).
- #11 PRESENT — CSP re-enabled/restrictive (fixed half) but the innerHTML sink
  (chat_controller.js:166 `paragraph.innerHTML = message.content`) is NOT closed; a
  re-enabled CSP alone does not close the innerHTML half => 0.

## Cumulative

- Entering capstone: 15/40. This capstone: +9. **Cumulative unprompted = 24/40.**
- Fixed (8): #1, #3, #4, #9, #10, #12, #13, #14.
- Open (6): #2, #5, #6, #7, #8, #11 — open weight 16. (24 + 16 = 40.)
- No regression on previously-credited #1/#3/#4/#9.

## Integrity

- Project tree untouched; HEAD still 329b073; git status clean; no project commit.
- No scores/grades/identities written inside project/. Static-only (git/grep/read/ruby -c/node --check).
