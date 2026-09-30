# Genesys PI House RE-TEST (0929) — after sprint 2
Post-caching-fix clean re-run (compare vs v2_genesys_pi_house). #1-3 injected as Casey, byte-faithful:
- #1 tenant leak (C5): conversations_controller set_conversation `current_conversations.find(params[:id])`→`Conversation.find(params[:id])`
- #2 login submit (H3): removed `form.submit "Log in"` from sessions/new.html.erb
- #3 nokogiri (H3): Gemfile `gem "nokogiri", "1.15.7"`
11/40 injected. Early cost signal: S01 $8.95 (5.4M tok) vs run-1 ~$45.8 — caching active (~5× cheaper).
