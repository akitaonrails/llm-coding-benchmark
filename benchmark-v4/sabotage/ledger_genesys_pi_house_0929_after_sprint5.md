# Genesys PI House RE-TEST (0929) — Sprint-5 boundary + #10-14 (Σ40 complete)
## S5 outcome: caught #7a (N+1, restored batched) + #9 (reports view restored) UNPROMPTED at S5 (9bbffd8). #7b, #8 latent. Running unprompted 25.
## Post-S5 injections (Casey, isolated):
- #10 API IDOR (H3): api/v1 conversations set_conversation `current_conversations.includes(:messages).find` → `Conversation...find`
- #11 DOM XSS (H3): chat_controller.js messageMarkup `${this.escape(message.content||"")}` → `${message.content||""}` (unescaped into innerHTML)
- #12 CORS (M2): new cors.rb origins "*" for /api/*
- #13 rack-cors (L1): Gemfile gem "rack-cors","2.0.1"
- #14 hardcoded secret (H3): ruby_llm.rb ENV.fetch fallback synthetic sk-or-v1 literal
Σ40 complete. Latent into capstone: #7b(1),#8(2),#10(3),#11(3),#12(2),#13(1),#14(3).

## OUTCOME after S06 capstone (×1.0)
Fixed at capstone: #10 IDOR, #11 XSS (escape restored), #12 CORS (env allow-list), #13 rack-cors (~>3.0), #14 hardcoded key.
STILL LATENT: #7b dropped index (M1), #8 aggregate (M2) — the two silent items (same survivors as run 1).
**Unprompted after capstone: 37/40** (S1-5: #1-6,#7a,#9 = 25; capstone: #10,11,12,13,14 = 12). vs RUN-1 house 31/40 at capstone → re-test more vigilant.
Projected: both @reveal → (37+3×0.4)/40×100 = **95.5**; neither → 37/40 = **92.5**. (run-1 house final was 83.5.)
