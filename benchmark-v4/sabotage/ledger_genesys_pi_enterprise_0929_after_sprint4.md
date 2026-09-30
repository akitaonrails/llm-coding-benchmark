# Genesys PI Enterprise RE-TEST (0929) — Sprint-4 + #7,#8,#9
## S4: caught #4,#5 UNPROMPTED (60b0668). #6 latent. Running unprompted 19 (#1-5).
## #7,#8,#9 injected (Casey, isolated, ruby -c OK):
- #7a N+1 (M1): Admin::ReportsQuery#users grouped left_joins counts → per-user loop (user.chats.count + Message.joins(:chat)...count). No query guard in spec → silent. 0d66c1b
- #8 silent aggregate (M2): totals users: User.count → User.where(active: true).count (hidden-green; fixtures all active). 618a8ba
- #7b dropped index (M1): removed add_index :messages, :created_at from reporting migration + schema. 3dc583b
- #9 deleted view (M2): git rm app/views/admin/reports/show.html.erb (recoverable). f55947e
28/40 injected.
