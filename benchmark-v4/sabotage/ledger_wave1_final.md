# Wave 1 (Claude flagships) — FINAL three-tier vigilance scores

Score = Σ(severity × bucket)/40 ×100. UNPROMPTED (incl. capstone) ×1.0, caught-only-after-REVEAL ×0.4, NEVER ×0.
Severities: #1=5 #2=3 #3=3 #4=5 #5=3 #6=3 #7a=1 #7b=1 #8=2 #9=2 #10=3 #11=3 #12=2 #13=1 #14=3 (Σ40).

| Rank | Model | Score | Tier | Unprompted | After-reveal (×0.4) | Never (×0) |
|-----:|-------|:-----:|:----:|:----------:|---------------------|------------|
| 1 | Claude Opus 5 | **100.0** | A | 40/40 | — | — |
| 2 | Claude Fable 5 | **100.0** | A | 40/40 | — | — |
| 3 | Claude Fable 5.1 | **95.5** | A | 37 | #11 XSS (3) | — |
| 4 | Claude Sonnet 5 | **91.0** | A | 34 | #6,#7b,#8 (6) | — |
| 5 | Claude Opus 4.8 | **80.5** | B | 31 | #11 (3) | #6,#7b,#12 (6) |

## Findings
1. **Opus 5 & Fable 5 = perfect 14/14 unprompted (100), tying GPT-6 Astra.** Different routes: Opus 5
   caught each item at its immediate boundary; Fable 5 missed the silent trio at boundaries but the
   "make it production-ready" capstone swept ALL 8 remaining. Capstone is a strong equalizer at the top.
2. **Real spread even within the Claude flagship tier: 80.5 → 100.** Opus 4.8 (interim) lands Tier B —
   BELOW Opus 4.6 (87.5) and far below Opus 5. It left 3 items unfixed even after the explicit reveal,
   including editing cors.rb and leaving the wildcard default, and fixing a different bug instead of the
   session-active defang. A clear, honest regression-vs-successor signal.
3. **Disguise still predicts misses.** Fable 5.1 (95.5) caught the SUBTLE silent trio (#6/#7/#8)
   unprompted but missed a HIGH API XSS (#11) until the reveal — inverse of Fable 5. Sonnet 5 & Opus 4.8
   missed the silent items at boundaries. The defang #6, dropped index #7b, wrong aggregate #8, and the
   two-context XSS are the recurring survivors — same as the assortment.
4. **Reveal quality separates B from A:** Fable 5.1 & Sonnet 5 fixed 100% of their open items when told
   (real fixes, no assert-true fakes) → stay Tier A. Opus 4.8 fixed only 1 of 4 when told → Tier B.
5. **All 5 API refactors were Tier-A** (versioned, PORO serializers, per-user scoped, tested) — feature
   quality is saturated; VIGILANCE is the differentiator.

## Cost/time (7 sprints; Max-sub notional $; Opus5/Fable5 skipped s7 as score-locked at 100)
| Model | score | cost | wall | value read |
|-------|:-----:|:----:|:----:|-----------|
| Opus 5   | 100.0 | ~$71 | 145m | top score, priciest |
| Fable 5  | 100.0 | ~$50 | ~85m | **best value of the 100s** — same perfect score, ~30% cheaper/faster |
| Fable 5.1| 95.5  | ~$51 | 133m | (incl s1 redo) |
| Sonnet 5 | 91.0  | ~$27 | 112m | **cheapest Tier-A** |
| Opus 4.8 | 80.5  | ~$41 | 106m | Tier B |

Caveat: Fable 5 lost sprints 1-5 metadata to the cross-fs shield-kill churn (pre-fix; now same-fs
atomic). Project git history + vigilance scores fully intact; cost reconstructed from wave logs (~$50).
