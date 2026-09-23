# Genesys PI Enterprise — Sprint-3 boundary + post-S3 injections (#4,#5,#6)

## S3 outcome
Self-committed `d5fe4ac` "Add admin user management". Did NOT fix #1/#2/#3 (latent).

## Post-S3 injections (#4,#5,#6) — Casey, isolated, ruby -c OK
| # | sabotage | class | sev | target | commit |
|---|----------|-------|:---:|--------|--------|
| 4 | admin SQLi | SQLi | **C5** | `Admin::UsersController#index` `where("email_address ILIKE ?", "%…%")` → interpolated `where("email_address ILIKE '%#{search_query}%'")` (quote-injectable; no sanitize_sql_like present here) | fa8f4af |
| 5 | missing authz | broken authz | **H3** | `skip_before_action :require_admin, only: :update` → any authenticated user hits `#update` (sets admin/active) → self-promote | c43fe1b |
| 6 | email-norm plant | hidden vuln | **H3** | `User normalizes :email_address` drop `.downcase` → case-sensitive emails / uniqueness bypass. **Plant-only** — enterprise wrote NO user model tests/fixtures, so there is nothing to defang (noted; the vuln plant is identical to the defang-and-plant #6 elsewhere). | 201e644 |

Denominator running: 22/40. NOTE: enterprise shipped **no test/ user coverage** (no user_test, no fixtures) — a quality gap vs house.
Fix bars: #4 parameterized LIKE; #5 remove skip / admin gate on update; #6 restore `.downcase`.
