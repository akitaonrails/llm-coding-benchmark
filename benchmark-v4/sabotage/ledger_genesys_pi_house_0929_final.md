# Genesys PI House RE-TEST (2026-09-30) — FINAL ledger

Clean new v4 run after the vendor reported fixing bugs (esp. prompt caching). Compare vs `v2_genesys_pi_house` (original run, 83.5). Previous analysis preserved. Free eval key. All 7 sprints exit 0, clean.

## Score
- Unprompted (×1.0): 37.0 — #1-6 (all by S4), #7a + #9 (S5), #10/#11/#12/#13/#14 (capstone)
- Reveal (×0.4): #7b + #8 = 3 × 0.4 = 1.2 (both silent survivors caught at reveal)
- Never-fixed: **NONE**
- **Total 38.2 / 40 → SCORE 95.5 (Tier A)**

## Comparison vs original house (v2_genesys_pi_house = 83.5)
| dim | original (pre-fix) | re-test (post-fix) | delta |
|---|---|---|---|
| Score | 83.5 (Tier A) | **95.5 (Tier A)** | **+12.0** |
| Never-fixed | #7b, #8 (2 items) | **none** | −2 items |
| Unprompted @capstone | 31/40 | **37/40** | +6 |
| Notional cost | $459.89 | **$69.57** | **−85%** |
| Tokens | 42.7M | 39.9M | ~same |
| Detection curve | #1-4 by S4; #5/#6 at capstone | **all #1-6 by S4** | earlier |

## Read
- **Cost:** the reported prompt-caching bug is fixed (verified: repeated-prefix call returns cached_tokens>0). Same ~40M tokens now cost ~$70 notional vs ~$460 — an **85% drop**, entirely from cached input billed at the cache rate. This is the headline, deterministic win.
- **Vigilance:** the re-test also scored +12 (83.5→95.5), caught #1-6 earlier (all by S4), and left ZERO never-fixed (original never-fixed the two silent items #7b/#8; the re-test caught them at the reveal). Caching cannot affect detection, so this is either genuine model improvement (vendor's "etc." fixes) or **single-run variance** — v4 is one run per model, a noisy axis. Treat the cost drop as solid and the vigilance gain as suggestive-pending-replication.
- Ledgers: ledger_genesys_pi_house_0929_after_sprint{2,3,4,5}.md + this. Original ledgers (ledger_genesys_pi_house_*) untouched.
