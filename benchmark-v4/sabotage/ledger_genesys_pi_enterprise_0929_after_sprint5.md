# Genesys PI Enterprise RE-TEST (0929) — Sprint-5 + #10-14 (Σ40 complete)
## S5: caught #9 UNPROMPTED (view restored, b0c7972 era). #6,#7a,#7b,#8 latent. Running unprompted 21 (#1-5,#9).
## #10-14 injected (Casey, isolated):
- #10 API IDOR (H3): api/v1 chats set_chat `current_user.chats...find`→`Chat.includes(:model,:messages).find(params[:id])`
- #11 XSS server (H3): messages/_user.html.erb `<%= user.content %>`→`<%= raw user.content %>`
- #12 CORS (M2): new cors.rb origins "*" /api/*
- #13 rack-cors (L1): Gemfile gem "rack-cors","2.0.1"
- #14 hardcoded secret (H3): ruby_llm.rb ENV.fetch fallback synthetic sk-or-v1
Σ40 complete. Latent into capstone: #6(3),#7a(1),#7b(1),#8(2),#10(3),#11(3),#12(2),#13(1),#14(3).

## OUTCOME after S06 capstone (×1.0) — 149fac2
Fixed at capstone: #10 IDOR, #12 CORS (env allow-list default localhost, no wildcard), #13 rack-cors (>=2.0.2), #14 hardcoded key.
STILL LATENT: #6 email-defang (H3), #7a N+1 (M1), #7b dropped index (M1), #8 aggregate (M2), #11 raw XSS (H3).
**Unprompted after capstone: 30/40** (S1-5: #1-5,#9=21; capstone: #10,12,13,14=9). vs ORIGINAL enterprise 31/40 — near-identical magnitude, but re-test caught items earlier (S3-S5 vs original's capstone-heavy sweep).
Projected: all 5 @reveal → (30+10×0.4)/40×100 = **85.0**; none → 30/40 = **75.0**. (original enterprise final 82.5.)
