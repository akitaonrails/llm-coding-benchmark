# Ledger — v2_glm_5_3_full_b300 — after SPRINT 7 (explicit REVEAL) — FINAL

- Model: GLM 5.3 full FP8 (self-hosted 4×B300), opencode harness
- Boundary graded: after-sprint-7 explicit reveal (find/fix ALL planted). Reveal fixes @ 40% weight.
- Graded by: fresh isolated v4 boundary reviewer (Claude Opus 4.8), STATIC-ONLY.
- Project HEAD: 87dab11 (unchanged, tree clean; no writes inside project/).
- Denominator: 40.

## Entering reveal
- Unprompted weight-caught = 24/40 (fixed: #1,#3,#4,#9,#10,#12,#13,#14).
- Open (6): #2(3), #5(3), #6(3), #7(2), #8(2), #11(3) = 16.

## Reveal outcome — ALL 6 genuinely fixed
| item | wt | status | both-halves | commit |
|---|---|---|---|---|
| #2 login link | 3 | FIXED_AT_REVEAL | n/a | 87dab11 |
| #5 deactivate authz | 3 | FIXED_AT_REVEAL | n/a | 7412439 |
| #6 guard + gutted test | 3 | FIXED_AT_REVEAL | yes | 41c5f7f |
| #7 N+1 + created_at index | 2 | FIXED_AT_REVEAL | yes | 8368c69 / f3c778d |
| #8 avg denominator | 2 | FIXED_AT_REVEAL | n/a | dca3eea |
| #11 innerHTML + CSP | 3 | FIXED_AT_REVEAL | yes | 2567f83 / 5716cfc |

reveal_fixed_weight = 16. reveal_items_still_open = [].

## 8 unprompted fixes — re-checked, NO regression at HEAD.
Incidental commit 9780168 (drop dead HTML messages route) is routes-only, not a sabotage item, no regression.

## Final score
final_score = (24 + 0.4×16)/40×100 = 30.4/40×100 = **76.0** → **Tier B** (73–82).

Artifacts: results-v4/v2_glm_5_3_full_b300/boundaries/sprint07-claude-1792513959789363127/ (grading.json, report.md, final-score.json).
