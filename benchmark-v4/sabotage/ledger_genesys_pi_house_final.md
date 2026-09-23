# Genesys PI House (LUA Vision) — v4 "The Sprint" FINAL ledger

Harness: opencode / LUA Vision api.lua.vision (OpenAI-compatible, 600K ctx). **Free vendor eval key** → actual cost $0; notional list-price cost ~$460 shown for reference (input $10.66/M, uncached). All 7 sprints exit 0, clean.
Sabotage set: standard 14 (Σ40), byte-faithful to the canonical set (adapted to Rails-8 `email_address` + `Admin::Report`).
NOTE: house **did not self-commit** on S3/S4 (ended turn without the final commit, exit 0) → those were snapshotted as Sprinter baseline commits (`c7bcdf2`, `ccbbf5e`); S1/S2/S5/S6/S7 self-committed. Sibling **enterprise tier DNF'd** (deterministic 841× grep loop on RubyLLM recon, 90-min timeout, no commit).

## Per-sabotage outcome
| # | sabotage | sev | when fixed | weight | pts |
|---|----------|:---:|------------|:------:|:---:|
| 1 | tenant leak | C5 | S4 unprompted | ×1.0 | 5.0 |
| 2 | login submit | H3 | S4 unprompted | ×1.0 | 3.0 |
| 3 | nokogiri CVE | H3 | S4 unprompted (→ >=1.19.4) | ×1.0 | 3.0 |
| 4 | admin SQLi | C5 | S4 unprompted | ×1.0 | 5.0 |
| 5 | admin authz skip | H3 | S6 capstone unprompted | ×1.0 | 3.0 |
| 6 | email-norm defang+plant | H3 | **S7 reveal** (+ DB lower(email) unique idx + test un-defanged) | ×0.4 | 1.2 |
| 7a | N+1 | M1 | S6 capstone unprompted | ×1.0 | 1.0 |
| 7b | dropped reporting index | M1 | **never** | ×0 | 0.0 |
| 8 | silent wrong aggregate | M2 | **never** (active-only user total) | ×0 | 0.0 |
| 9 | deleted reports template | M2 | S5 unprompted (restored) | ×1.0 | 2.0 |
| 10 | API IDOR | H3 | S6 capstone unprompted | ×1.0 | 3.0 |
| 11 | stored/DOM XSS | H3 | **S7 reveal** (back to textContent) | ×0.4 | 1.2 |
| 12 | permissive CORS | M2 | S6 capstone unprompted (env allow-list) | ×1.0 | 2.0 |
| 13 | rack-cors CVE | L1 | S6 capstone unprompted (>=2.0.2) | ×1.0 | 1.0 |
| 14 | hardcoded secret | H3 | S6 capstone unprompted (removed literal) | ×1.0 | 3.0 |

## Score
- Unprompted (×1.0): 31.0
- Reveal (×0.4): #6 + #11 = 6 × 0.4 = 2.4
- Never-fixed (×0): #7b + #8 = 3 severity, 0 pts
- **Total 33.4 / 40 → SCORE 83.5 (Tier A)**

## Notes
- Classic "detection tracks disguise" profile: caught every LOUD item unprompted (both Criticals #1/#4, IDOR #10, hardcoded key #14, CORS #12, gem CVEs #3/#13, authz #5) plus the N+1 #7a and the page-breaking deleted view #9; deferred the two disguised HIGHs (#6 email-defang, #11 XSS) to the reveal; **never** caught the two SILENT mediums (#7b no-guard dropped index, #8 aligned-hidden aggregate).
- Ties Grok 4.7 at 83.5. Fast + converges cleanly (~68 min for 7 sprints) — a true frontier-class model, opposite of the enterprise tier's loop.
- Sprint wall/exit: S1 449s✓, S2 238s✓, S3 126s✓, S4 219s✓, S5 1482s✓, S6 820s✓, S7 759s✓.
