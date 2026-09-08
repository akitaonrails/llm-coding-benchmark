# Wave 2 (GPT/Gemini/Grok top) — injections after sprint 2 (items 1-3), parity

6 models (4 codex GPT + 2 opencode). All built multi-user w/ per-user isolation. Items 1-3 applied
identically + live-verified. Denominator (1-3): 11 (Crit 5 + High 3 + High 3). Matches Wave 1 / assortment.

| # | item | sev | GPT5.6 sol | GPT5.6 terra | GPT5.6 luna | GPT5.5 | Gemini3.7F | Grok4.5 |
|---|------|-----|-----------|--------------|-------------|--------|-----------|---------|
| 1 | tenant leak | Crit5 | f456ceb | e15e8d5 | d4ebc87 | d528f35 | 4541148 | b42110b |
| 2 | login submit removed | High3 | 1f25d97 | 44a7a10 | 6d277e6 | 236f924 | af764de | 56206a3 |
| 3 | nokogiri 1.15.7 pin | High3 | 6b7066c | cff98c7 | 9f9b0ba | 81082d4 | ad8c933 | 7fe3812 |

Naming: sol/terra/luna/GPT5.5 = Conversation (sol uses UUID public_id); Gemini3.7F/Grok4.5 = Chat.
All live-verified: #1 user B loads user A's conversation (each model's own isolation test goes red);
#2 login submit gone (system test red); #3 bundle-audit flags nokogiri 1.15.7 CVE. All boot; Casey commits.

CLEANUP PENDING (end-of-run): `bench-pg-terra` Postgres container (port 55432) — terra spun it up for
live DB tests; docker rm denied by permission sandbox. Isolated, not gaming/ruby-llm-chat/relay. Remove
at batch cleanup: `docker rm -f bench-pg-terra`. Also the earlier `.v4_lost_fable_5_1` stub in /mnt/data/Projects.
