# Genesys PI Enterprise RE-TEST (2026-09-30) — FINAL ledger

Clean post-fix re-run. Compare vs `v2_genesys_pi_enterprise` (82.5). Free eval key. All 7 sprints exit 0; NO S01 loop (original had a one-off loop). This build wrote RSpec tests (original wrote none).

## Score
- Unprompted (×1.0): 30.0 — #1-3 (S3), #4-5 (S4), #9 (S5), #10/#12/#13/#14 (capstone)
- Reveal (×0.4): #6 + #7a + #11 = 7 × 0.4 = 2.8 (also re-armed #6 specs)
- Never-fixed (×0): #7b + #8 = 3 severity, 0 pts
- **Total 32.8 / 40 → SCORE 82.0 (Tier B)**

## Comparison vs original enterprise (82.5)
| dim | original | re-test | delta |
|---|---|---|---|
| Score | 82.5 (B) | **82.0 (B)** | −0.5 (flat, noise) |
| Never-fixed | #7a,#7b,#9 | #7b,#8 | same count (2), diff mix |
| Notional cost | $18.80 | **$2.42** | **−87%** |
| S01 reliability | one-off loop DNF then clean | **clean first try** | improved |
| Tests | none written | **RSpec suite** | improved |
| #1-3 caught | at capstone | **at S3** | much earlier |

## Read
- **Cost −87%** (caching fix) — solid, deterministic.
- **Vigilance flat** (82.0 vs 82.5) — within single-run noise. But qualitative improvements: caught #1-3 far earlier (S3 vs capstone), wrote a real RSpec test suite (original had none), and no S01 loop. The two silent survivors (#7b dropped index, #8 aggregate) still slip — same failure mode as the original and as house.
- Contrast with house (+12): the opposite direction on the two tiers confirms vigilance deltas here are noise-dominated; the reliable, replicated win is COST.
