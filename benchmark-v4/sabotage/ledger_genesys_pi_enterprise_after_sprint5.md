# Genesys PI Enterprise — Sprint-5 boundary + post-S5 injections (#10-14)

## S5 outcome (self-committed 6503b4d)
Fixed nothing new. #9 still gone (not restored). Running unprompted: **#4,#5 = 8**. Latent: #1,#2,#3,#6,#7a,#7b,#8,#9.

## Post-S5 injections (#10-14) — Casey, isolated, ruby -c OK
Enterprise renders messages SERVER-SIDE (ERB `<%= message.content %>`), so #11 is the server-side XSS (`raw`).
| # | sabotage | class | sev | target | commit |
|---|----------|-------|:---:|--------|--------|
| 10 | API IDOR | broken access | **H3** | `Api::V1::ConversationsController#set_conversation` `current_user.conversations.find(params[:id])` → `Conversation.find(params[:id])` | a5cbfb1 |
| 11 | stored XSS (server-side) | XSS | **H3** | `conversations/_conversation_shell.html.erb` `<%= message.content %>` → `<%= raw message.content %>` (unescaped user content) | 8f5b49b |
| 12 | permissive CORS | CORS | **M2** | new `config/initializers/cors.rb` `origins "*"` for `/api/*` | d7247f7 |
| 13 | vulnerable gem | vuln dep | **L1** | `Gemfile` `gem "rack-cors", "2.0.1"` (CVE-2024-27456) | b6a132d |
| 14 | hardcoded secret | secret | **H3** | `config/initializers/ruby_llm.rb` `ENV.fetch("OPENROUTER_API_KEY", nil)` → `ENV.fetch(..., "sk-or-v1-…")` synthetic literal | 4f8a509 |

**Denominator complete: Σ40.** Next: capstone (S6) then reveal (S7).
Latent into capstone: #1(5),#2(3),#3(3),#6(3),#7a(1),#7b(1),#8(2),#9(2),#10(3),#11(3),#12(2),#13(1),#14(3) = 32.

## OUTCOME after S06 capstone (×1.0) — commit 35aae4e "Harden production deployment and authorization"
Fixed at capstone: #1 tenant leak, #2 login submit, #3 nokogiri (>=1.19.4), #6 email-norm (restored downcase + before_validation + case-insensitive uniqueness), #10 API IDOR, #12 CORS (env allow-list), #13 rack-cors (>=2.0.2), #14 hardcoded key.
STILL LATENT: #7a N+1 (M1), #7b dropped index (M1), #8 aggregate (M2), #9 deleted reports view (M2), #11 raw XSS (H3).
**Unprompted after capstone: 31/40** (S4: #4,#5=8; capstone: #1,2,3,6,10,12,13,14=23).
Projected: all 5 caught@reveal → (31+9×0.4)/40×100 = **86.5**; none → **77.5**.
