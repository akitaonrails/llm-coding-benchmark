# Genesys PI Enterprise (LUA Vision) — v4 "The Sprint" FINAL ledger

Harness: opencode / api.lua.vision (OpenAI-compatible, 384K ctx). **Free vendor eval key** → actual cost $0; notional list-price ~$18 (input $0.74/M). 
**Viability note:** first S01 attempt DNF'd (stochastic 841× `grep "LUA"` loop on RubyLLM recon, 90-min timeout, no commit — preserved as `results-v4/v2_genesys_pi_enterprise.dnf-90min-loop-*`). Clean re-run S01 committed in 7 min; all 7 sprints then completed clean. The loop was a one-off, NOT deterministic. Scored on the clean run.
Enterprise shipped **no user model tests/fixtures** (quality gap vs house).

## Per-sabotage outcome
| # | sabotage | sev | when fixed | weight | pts |
|---|----------|:---:|------------|:------:|:---:|
| 1 | tenant leak | C5 | S6 capstone | ×1.0 | 5.0 |
| 2 | login submit | H3 | S6 capstone | ×1.0 | 3.0 |
| 3 | nokogiri CVE | H3 | S6 capstone (→ >=1.19.4) | ×1.0 | 3.0 |
| 4 | admin SQLi | C5 | S4 unprompted | ×1.0 | 5.0 |
| 5 | admin authz skip | H3 | S4 unprompted | ×1.0 | 3.0 |
| 6 | email-norm plant | H3 | S6 capstone (restored downcase + before_validation + CI uniqueness) | ×1.0 | 3.0 |
| 7a | N+1 | M1 | **never** | ×0 | 0.0 |
| 7b | dropped reporting index | M1 | **never** | ×0 | 0.0 |
| 8 | silent wrong aggregate | M2 | **S7 reveal** (restored messages_scope.count) | ×0.4 | 0.8 |
| 9 | deleted reports template | M2 | **never** (view stayed deleted; no report tests to flag it) | ×0 | 0.0 |
| 10 | API IDOR | H3 | S6 capstone | ×1.0 | 3.0 |
| 11 | stored XSS (server `raw`) | H3 | **S7 reveal** (back to escaped `<%= %>`) | ×0.4 | 1.2 |
| 12 | permissive CORS | M2 | S6 capstone (env allow-list) | ×1.0 | 2.0 |
| 13 | rack-cors CVE | L1 | S6 capstone (>=2.0.2) | ×1.0 | 1.0 |
| 14 | hardcoded secret | H3 | S6 capstone (removed literal) | ×1.0 | 3.0 |

## Score
- Unprompted (×1.0): 31.0
- Reveal (×0.4): #8 + #11 = 5 × 0.4 = 2.0
- Never-fixed (×0): #7a + #7b + #9 = 4 severity, 0 pts
- **Total 33.0 / 40 → SCORE 82.5 (Tier B)**

## Notes
- Same "detection tracks disguise" shape as house but weaker: caught fewer items mid-sprint (only #4/#5 at S4 vs house's #1–4), leaned heavily on the capstone (8 items) to reach 31/40 unprompted, and left **three never-fixed** — the two silent perf items (#7a N+1, #7b index) AND the deleted reports view #9 (house restored #9 at S5; enterprise never did — it wrote no report tests to flag the MissingTemplate).
- **82.5 (Tier B) vs house 83.5 (Tier A)** — the flagship edges the workhorse by 1 pt and clears the A line; enterprise sits just under it. Fast (~39 min for 7 sprints) once past the one-off S01 loop.
- Sprint wall/exit (scored run): S1 432s✓ S2 402s✓ S3 130s✓ S4 147s✓ S5 170s✓ S6 375s✓ S7 660s✓.
