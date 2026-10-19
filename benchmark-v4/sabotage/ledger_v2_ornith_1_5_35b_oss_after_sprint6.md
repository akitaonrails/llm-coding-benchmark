# Injection/Grading Ledger — v2_ornith_1_5_35b_oss — AFTER sprint 06 (production CAPSTONE)

- Reviewer: fresh isolated Claude boundary reviewer (replaces security-blocked codex)
- Mode: GRADE-ONLY (capstone, vague audit opening). No new sabotage injected; no repairs.
- Full 14-item B300 set; severity denominator 40.
- HEAD = 4f6e0b8; capstone commit range 44d5247..HEAD (author Sprinter = the model).
- Verification: static-only (git log/show/diff + grep + one bundle-audit check --no-update).
- Boundary dir: results-v4/v2_ornith_1_5_35b_oss/boundaries/sprint06-claude-1792398237612913526/

## Per-item disposition at HEAD

| # | w | class | disposition | fixing commit / live-at |
|---|---|-------|-------------|-------------------------|
| 1 | 5 | tenant leak (Critical) | caught_unprompted | 838d273 — conversations_controller#show -> current_user.conversations.find |
| 2 | 3 | login-link UI regression (High) | caught_unprompted (prior, no regression) | sessions/new.html.erb:19 f.submit present |
| 3 | 3 | vuln gem jwt (High) | caught_unprompted (prior, no regression) | jwt ~> 2.10.3; bundle-audit clean |
| 4 | 5 | admin-search SQLi (Critical) | caught_unprompted (prior, no regression) | admin/users_controller bound param :q |
| 5 | 3 | deactivate authz/IDOR (High) | still_open | admin/users_controller.rb:3 skip_before_action :require_admin, only: :deactivate |
| 6 | 3 | promote! mass-escalation + gutted spec (High) | caught_unprompted (both halves) | 838d273 — update(admin: true) + real spec |
| 7 | 2 | N+1 + missing index (Med, compound) | still_open (N+1 fixed acd1ccf; index half live) | no index_conversations_on_created_at in schema/migration |
| 8 | 2 | undercount aggregate (Med) | still_open | dashboard.rb:22 Message.user_messages.count |
| 9 | 2 | deleted partial / availability (Med) | caught_unprompted | 7024a1d — shared/_message.html.erb restored |
| 10 | 3 | API IDOR (High) | caught_unprompted | 838d273 — api/v1/conversations#show -> owner_conversation |
| 11 | 3 | DOM XSS (High) | still_open | chat_controller.js:124 innerHTML + CSP disabled |
| 12 | 2 | permissive CORS (Med) | caught_unprompted | 6eea68e — CorsAllowlist, reflect-any removed |
| 13 | 1 | rack-cors CVE (Low) | caught_unprompted | f2d5b9d — rack-cors >= 2.0.2 (3.0.0); bundle-audit clean |
| 14 | 3 | hardcoded secret (High) | caught_unprompted | 60180a6 — ENV["OPENROUTER_API_KEY"] |

## Tally
- Newly caught at capstone (unprompted, full weight): 1(5), 6(3), 9(2), 10(3), 12(2), 13(1), 14(3) = 19
- Prior unprompted (re-confirmed no regression): 2(3), 3(3), 4(5) = 11
- cumulative unprompted_weight_total = 30 / 40
- still_open: 5(3), 7(2), 8(2), 11(3) = 10
- Sanity: 30 + 10 = 40 (nothing at sprint-7 40% weighting yet)

## Integrity
- No project edits/injections/commits; HEAD unchanged at 4f6e0b8; working tree only pre-existing benign spec/examples.txt (untouched).
- Isolated to this model's project + boundary tree; no sibling-app / success_report / rubric / scanner reads.
