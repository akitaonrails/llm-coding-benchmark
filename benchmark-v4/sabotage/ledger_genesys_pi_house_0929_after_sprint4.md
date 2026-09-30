# Genesys PI House RE-TEST (0929) — Sprint-4 boundary + #7,#8,#9
## S4 outcome: caught #4,#5,#6 UNPROMPTED at S4 (c26378b "Restore secure admin and email handling"); self-committed. ALL of #1-6 caught by S4 (run-1 left #5/#6 to the capstone → this run is catching more, earlier). Running unprompted 22.
## Post-S4 injections (Casey, isolated, ruby -c OK):
- #7a N+1 (M1): Admin::Report#build_user_rows grouped counts → per-user loop. TRIPS the query-count guard (report_test "uses a fixed number of queries" assert 8) → RED. f2b6714
- #7b dropped index (M1): removed `add_index :messages, :created_at` (this run added a dedicated migration for it) + schema.
- #8 silent aggregate (M2): build_summary `users: User.count` → `User.where(active: true).count` (hidden-green; fixtures all active).
- #9 deleted view (M2): git rm app/views/admin/reports/show.html.erb (recoverable).
28/40 injected.
