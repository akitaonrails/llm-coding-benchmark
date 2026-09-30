# Genesys PI Enterprise RE-TEST (0929) — after sprint 2
Clean re-run post-fix (compare vs v2_genesys_pi_enterprise=82.5). No S01 loop this time. This build uses "chats" naming + wrote 167 files S01 (vs original's sparse/no-test build).
#1-3 injected as Casey:
- #1 tenant leak (C5): chats_controller set_chat `current_user.chats...find(params[:id])`→`Chat.includes(:model,:messages).find(params[:id])`
- #2 login submit (H3): removed form.submit from sessions/new
- #3 nokogiri (H3): Gemfile gem "nokogiri","1.15.7"
11/40 injected.
