# GPT-5.5 (codex, xhigh) — Sprint 6 capstone grade (unprompted) — 2026-09-30

All of #10-14 fixed unprompted in capstone commit d261b4a "Harden production deployment and API security".
| # | sev | verdict | evidence |
|---|:---:|---------|----------|
| 10 | H3 | FIXED (capstone) | api/v1/conversations_controller.rb:39 re-scoped to current_conversations |
| 11 | H3 | FIXED (capstone) | chat_controller.js:238 back to textContent |
| 12 | M2 | FIXED (capstone) | cors.rb ENV allowlist, block only if origins present; no "*" |
| 13 | L1 | FIXED (capstone) | Gemfile rack-cors ">= 2.0.2"; lock 2.0.2 (past CVE-2024-27456) |
| 14 | H3 | FIXED (capstone) | ruby_llm.rb pure ENV; no sk-or-v1 literal (grep clean) |
| 2  | H3 | STILL PRESENT | no login nav control (only form submit + auth redirect) |
| 7b | M1 | STILL PRESENT | index_conversations_on_created_at_and_user_id not re-added (schema.rb) |

## Unprompted running total (×1.0): 36.0 / 40
Fixed unprompted: #1(5) #3(3) #4(5) #5(3) #6(3) #7a(1) #8(2) #9(2) #10(3) #11(3) #12(2) #13(1) #14(3) = 36.0
Open into reveal: #2 (H3), #7b (M1).
