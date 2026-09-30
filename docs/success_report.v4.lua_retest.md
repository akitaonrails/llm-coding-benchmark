# LUA Vision Genesys PI — post-fix re-test (2026-09-30) vs original (2026-09-23)

The vendor (LUA Vision) reported fixing bugs from the first test — notably the **lack of prompt caching**.
This is a clean, independent v4 re-run of both models to measure the effect. **The original runs are preserved
unchanged** (`v2_genesys_pi_house` / `v2_genesys_pi_enterprise`, still the ranked entries); the re-runs are
`v2_genesys_pi_house_0929` / `v2_genesys_pi_enterprise_0929`. Same 14-sabotage protocol, byte-faithful,
one run per model (v4 is a single-run benchmark — a noisy axis). Free vendor eval key ($0 actual; costs below
are notional list-price at the vendor's BRL rates ÷ 5.16, for weighting).

## Pre-flight: the caching fix is real
Repeated-prefix probe on `/v1/chat/completions` returned `cached_tokens: 4121 / 4124` on the 2nd call
(1st call: 0). In the original test it was **always 0**. Confirmed active before any run.

## Results

| Model | Score (orig → re-test) | Never-fixed (orig → re-test) | Notional cost (orig → re-test) | Wall |
|-------|:---:|---|:---:|:---:|
| **Genesys PI House** | 83.5 → **95.5**  (+12.0) | #7b, #8 → **none** | $459.89 → **$69.57**  (−85%) | 68m → 94m |
| **Genesys PI Enterprise** | 82.5 → **82.0**  (−0.5) | #7a,#7b,#9 → #7b,#8 | $18.80 → **$2.42**  (−87%) | 39m → 33m |

Both: A ≥ 83, B 75–82. House stays Tier A; enterprise stays Tier B.

## What clearly improved (replicated, deterministic)
- **Cost: −85% to −87%.** The prompt-caching fix is the headline. Same ~40M (house) / ~19–24M (enterprise)
  token volume now bills repeated context at the cache rate instead of full input price. House's original
  ~$460 (the single most expensive run in the whole field, purely from uncached context) collapses to ~$70.
- **Reliability:** enterprise's original run needed a re-try after a one-off S1 grep loop; the re-test S1
  converged first-try. No loops in either re-test.
- **Test discipline:** the enterprise re-test wrote a real RSpec suite (models/requests/system); the original
  enterprise wrote **no tests at all**.
- **Earlier detection:** both re-tests caught the loud early sabotages (#1–3) by S3, and house caught all of
  #1–6 by S4 (original house left #5/#6 to the capstone; original enterprise caught #1–3 only at the capstone).

## What is NOT established (noise-limited)
- **Vigilance score.** House +12 but enterprise −0.5. Since prompt caching **cannot affect detection**, an
  opposite-direction move across the two tiers means the vigilance deltas are **within single-run variance**.
  House's +12 is large enough to *hint* at a real model improvement in the vendor's other ("etc.") fixes, but
  one run per model cannot confirm it. Treat the cost/reliability wins as solid and the vigilance gain as
  suggestive-pending-replication (would need N≥3 runs per model to separate signal from noise).
- **The two silent survivors persist.** Both re-tests still never-fixed the no-test-guard dropped index (#7b)
  and the aligned-hidden aggregate (#8) — the same disguise-class blind spot as the originals and most models.

## Bottom line
The reported caching bug is **fixed and verified** — an ~85% cost reduction, turning house from the field's
priciest run into a mid-cost one. Vigilance is unchanged within noise (enterprise flat; house up but not
confirmable on one run). Ledgers: `ledger_genesys_pi_{house,enterprise}_0929_*`. Originals untouched for
side-by-side.
