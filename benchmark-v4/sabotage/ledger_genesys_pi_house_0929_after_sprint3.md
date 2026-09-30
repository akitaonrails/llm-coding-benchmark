# Genesys PI House RE-TEST (0929) — Sprint-3 boundary + #4,#5,#6
## S3 outcome: caught #1,#2,#3 UNPROMPTED at S3 (897dfde "Fix merged authentication and security regressions"); self-committed. Running unprompted 11. (run-1 caught #1-3 across S3-S4; this run caught all 3 by S3 — earlier.)
## Post-S3 injections (Casey, isolated, ruby -c OK):
- #4 SQLi (C5): User.scope :search_by_email `LOWER(email_address) LIKE ?` → interpolated `LIKE '%#{sanitize_sql_like(query.downcase)}%'` (quote-injectable). f1881a4
- #5 authz (H3): Admin::UsersController `skip_before_action :require_admin, only: :update` (self-promote hole).
- #6 defang+plant (H3): User normalizes drop `.downcase` (login case-mismatch vuln; uniqueness stays case-insensitive); defanged normalization test input `" PERSON@EXAMPLE.COM "`→`" person@example.com "` (line16 .upcase dup test stays green via case_sensitive:false).
22/40 injected.
