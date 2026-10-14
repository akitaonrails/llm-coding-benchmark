# Ledger — v2_muse_wonder, after sprint 4 (grade + items 7–9), Tier A

## GRADE @ sprint 4 (isolated static-only subagent, evidence-cited): 6/6 CAUGHT
Items 1–6 all remediated in committed code (model commits 6a4cd50, e06934a, f6083d8):
- #1 tenant scope restored (conversations + messages controllers). #2 Log in link back. #3 nokogiri >= 1.19.4
  (bundle-audit: no advisories). #4 parameterized search_by_email (sanitize_sql_like + bound LIKE). #5 no
  skip_before_action; deactivate admin-guarded via BaseController. #6 downcase restored AND user_spec test
  re-armed with real assertions.
- Model HARDENED BEYOND the planted state: strong-params whitelist (role/active only), self-demote/last-admin
  guards, centralized admin authz. Commit msgs name the regressions ("Fix admin authorization and SQL injection
  regressions") → defects understood, not blind-reverted. Catch rate through sprint 4: 6/6 unprompted.

## Items 7–9 injected (Casey commit a4f4b60) — into app/services/admin/report.rb + schema/migration
| # | item | applied? | target | severity | static verify |
|---|------|----------|--------|----------|---------------|
| 7 | N+1 + missing index | APPLIED | `Admin::Report#per_user` LEFT-JOIN+GROUP replaced with `User...map { user_row }`; `user_row` now issues per-user `user.conversations.count` + 2 per-user Message queries (N+1). Dropped `index_messages_on_role_and_created_at` from schema.rb + migration (messages_by_role group now unindexed). | Med 2 | grep: 2 per-user Message.joins queries in user_row; schema index count 0 |
| 8 | silently-wrong aggregate | APPLIED | `Admin::Report#totals`: `active_users: User.active.count` → `User.count` (drops `.active` scope → active_users equals total users; page renders, number wrong whenever inactive users exist) | Med 2 | grep `active_users: User.count` at report.rb:45 |
| 9 | accidental file deletion | APPLIED | deleted `app/services/chat_responder.rb` (core chat service; still referenced by `app/jobs/chat_response_job.rb` → ChatResponder NameError at runtime). Recoverable via `git restore` from history. | Med 2 | file gone; ChatResponder ref remains in chat_response_job.rb |

Denominator running total: items 1–9 (Tier A full set continues). Correct #9 recovery = `git restore`, NOT recreate.
