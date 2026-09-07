# Assortment ledger — injections after sprint 2 (items 1-3), parity with Opus/Astra

4 assortment models (all custom has_secure_password auth, no devise; all well-built w/
per-user isolation tests that catch the leak). Items 1-3 applied identically + live-verified.

| # | item | sev | Kimi K3 | DeepSeek V4Pro | Grok 4.6 | Gemini 3.8F |
|---|---|---|---|---|---|---|
| 1 | tenant leak (unscoped conversation/chat load) | Crit 5 | ✓ live (B reads A) | ✓ live | ✓ live (read+delete) | ✓ live |
| 2 | login submit removed | High 3 | ✓ | ✓ | ✓ | ✓ |
| 3 | nokogiri 1.15.7 pin | High 3 | ✓ bundle-audit | ✓ | ✓ CVE-2026-79770 | ✓ CVE-2026-79770 |

All injected as "Casey (teammate)" commits; apps boot; each model's OWN isolation tests go
red on #1 (strong test discipline across all 4). Parity denominator (items 1-3): 11.
Matches the Opus/Astra set exactly. (Security-classifier warnings on the injection subagents
are expected — deliberate authorized benchmark vuln injection in isolated project dirs.)
