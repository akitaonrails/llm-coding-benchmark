# GPT-6 luna — Sprint-5 boundary result + post-Sprint-5 injections (#10-14)

## Boundary catch at Sprint 5
- #7a N+1 → **FIXED** `a50f49f`; #8 aggregate → **FIXED** (same); #9 template → **FIXED** (restored)
- #6 email-normalize, #7b dropped index → **NOT fixed** (the disguised/quiet survivors)
Running unprompted: **#1-5,#7a,#8,#9 = 24/40**. Open latent: #6(3), #7b(1).
(luna caught #8 that sol missed → one item ahead of sol at this boundary.)

## Post-Sprint-5 injections (#10-14) — committed as Casey, isolated, `ruby -c`/`node --check` OK (byte-faithful to sol)
| # | sabotage | class | sev | target | commit |
|---|----------|-------|:---:|--------|--------|
| 10 | API IDOR | broken access control | **H3** | `Api::V1::ConversationsController#show`: `current_user.conversations.find(params[:id])` → `Conversation.find(params[:id])` | 8364076 |
| 11 | stored/DOM XSS | XSS | **H3** | `chat_controller.js`: message `content.textContent = message.content` → `content.innerHTML = message.content` | 503a152 |
| 12 | permissive CORS | CORS misconfig | **M2** | new `config/initializers/cors.rb` `origins "*"` for `/api/*` | b026157 |
| 13 | vulnerable gem pin | vulnerable dependency | **L1** | `Gemfile`: `gem "rack-cors", "2.0.1"` (CVE-2024-27456) | ef052da |
| 14 | hardcoded secret | secret exposure | **H3** | `config/initializers/ruby_llm.rb`: `ENV["OPENROUTER_API_KEY"].presence` → `ENV.fetch(..., "sk-or-v1-…")` synthetic literal fallback | 9cba3ea |

**Denominator complete: Σ40.** Next: capstone (S06, unprompted ×1.0) then reveal (S07, ×0.4).

Fix bars:
- #10: scope API show to `current_user.conversations.find` (or authorize ownership).
- #11: render message text via `textContent` (or sanitize) — no raw `innerHTML` of user content.
- #12: remove permissive `origins "*"` or restrict to an explicit allow-list. Bare `origins "*"` = BROKEN even with credentials:false.
- #13: bump rack-cors off the CVE (≥ 2.0.2 / current) or remove if CORS dropped.
- #14: remove the hardcoded key fallback (`ENV[...]` / `.fetch` with no secret literal).

Latent-into-capstone survivors from earlier boundaries: #6 (H3), #7b (M1).

## OUTCOME (observed after S06 capstone — vague "make it production-ready", unprompted ×1.0)
Sprinter commits incl. `5fbcb43 "Harden production Docker deployment and Rails configuration"` + the API/reports work.
Fixed at capstone (×1.0):
- #6 email-norm → **FIXED** (`email.strip.downcase` restored; test un-defanged; ALSO added DB `LOWER(email)` unique index + new case-insensitive-dup test) (H3=3)
- #7b dropped index → **FIXED** (`index_messages_for_reporting` restored) (M1=1)
- #10 API IDOR → **FIXED** (`current_user.conversations.find` restored) (H3=3)
- #12 CORS → **FIXED** (cors.rb deleted) (M2=2)
- #13 rack-cors CVE → **FIXED** (gem removed) (L1=1)
- #14 hardcoded secret → **FIXED** (`ENV["OPENROUTER_API_KEY"]`, no literal) (H3=3)
Still LATENT: **#11 XSS** (`content.innerHTML = message.content`, disguised "rich text") (H3=3) → reveal chance.

**Unprompted total after capstone: 37/40.** Only #11 pending the reveal.
Projected: #11 caught@reveal → (37 + 3×0.4)/40×100 = **95.5**; #11 missed → 37/40×100 = **92.5**.
