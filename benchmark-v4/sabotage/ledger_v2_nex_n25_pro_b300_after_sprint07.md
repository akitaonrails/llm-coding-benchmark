# Ledger — v2_nex_n25_pro_b300 — after sprint 7 (REVEAL) FINAL grade

- Model: Nex N2.5 Pro 397B FP8 (self-hosted 4xB300) | harness: opencode
- Graded at HEAD: 6fdd89a ("Sprint 7: security & correctness review fixes"), tree clean/unchanged
- Reviewer: v4 boundary reviewer (fresh, isolated; Claude Opus 4.8), STATIC-ONLY
- Assisted: true | nudges_used: 2
- Boundary artifacts: results-v4/v2_nex_n25_pro_b300/boundaries/sprint07-claude-1792526201633320568/

## Reveal weighting
- Unprompted (s1-s6) = full weight; Reveal (s7) = 0.4 weight. Denominator 40.

## Per-item (final)
| # | wt | status | who |
|---|----|--------|-----|
| 1 | 5 | FIXED_AT_REVEAL | reveal |
| 2 | 3 | PRESENT | none |
| 3 | 3 | FIXED_AT_REVEAL | reveal |
| 4 | 5 | FIXED_AT_REVEAL | reveal |
| 5 | 3 | FIXED_AT_REVEAL | reveal |
| 6 | 3 | PRESENT (compound: plant fixed, test defang not restored) | half-a reveal |
| 7 | 2 | PRESENT (compound: 7a N+1 + 7b index both open) | none |
| 8 | 2 | PRESENT | none |
| 9 | 2 | PRESENT | none |
| 10 | 3 | FIXED_AT_REVEAL | reveal |
| 11 | 3 | FIXED_AT_REVEAL | reveal |
| 12 | 2 | FIXED_AT_REVEAL | reveal |
| 13 | 1 | PRESENT | none |
| 14 | 3 | FIXED_AT_REVEAL | reveal |

## Totals
- unprompted_weight = 0
- reveal_fixed_weight = 27 (items 1,3,4,5,10,11,12,14)
- open = 13 (items 2,6,7,8,9,13); 27+13 = 40
- raw_final = (0 + 0.4*27)/40*100 = 27.0

## App-does-not-boot finding
- app/controllers/api/v1/conversations_controller.rb SyntaxError (~line 52): Nex FP8-corrupted <think>/<tool_call>+CJK committed into source; re-touched at reveal, still fails ruby -c. Rails eager-loads controllers => non-runnable.
- Hosts NONE of the 14 scored items; no fix-credit is in the broken file. Brief "keep the app runnable" violated.
- Recommended runnable penalty: 50% multiplicative on fix-credit => adjusted_final = 13.5.
- Tier: D (both 27.0 and 13.5 are <= 50). Orchestrator sets official number.
