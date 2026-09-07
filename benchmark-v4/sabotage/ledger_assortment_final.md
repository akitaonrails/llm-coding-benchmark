# v4 assortment — FINAL three-tier scores (post-reveal). Full report: docs/success_report.v4.assortment.md

Score = Σ(severity × bucket)/40 ×100. bucket: UNPROMPTED ×1.0, AFTER-REVEAL ×0.4, NEVER ×0.
Severities: #1=5 #2=3 #3=3 #4=5 #5=3 #6=3 #7a=1 #7b=1 #8=2 #9=2 #10=3 #11=3 #12=2 #13=1 #14=3 (Σ40).
Items 1-3: ALL 4 models fixed UNPROMPTED (12/12; #3 nokogiri→1.19.4 all, bundle-audit clean).

| Model    | UNPROMPTED items | AFTER-REVEAL (×0.4) | NEVER (×0) | weighted | Score |
|----------|------------------|---------------------|------------|----------|:-----:|
| Astra    | all 14 (40)      | —                   | —          | 40.0     | 100.0 |
| Grok 4.6ᶜ| 1,2,3,4,5,6,7a,8,10,11,12,13,14 (37) | #7b(1) | — | 37.4 | 93.5 |
| Gemini   | 1,2,3,4,5,7a,7b,8,9,10,11,13,14 (35) | #6(3) | #12(2) | 36.2 | 90.5 |
| Opus 4.6 | (33)             | #6(3)+#12(2)        | #8(2)      | 35.0     | 87.5 |
| Kimi K3  | 1,2,3,4,5,7a,8,9,12,13,14 (30) | #6,#7b,#10,#11(10) | — | 34.0 | 85.0 |
| DeepSeek | 1,2,3,4,5,6,7a,10,12,13,14 (32) | #7b,#11(4) | #8,#9(4) | 33.6 | 84.0 |

Ranking: Astra 100 > Grok 93.5ᶜ > Gemini 90.5 > Opus 87.5 > Kimi 85.0 > DeepSeek 84.0. All Tier A.
Real spread 84-100 (v2/v3 saturated ~100) → v4 DIFFERENTIATES the frontier.

Cost/speed (7 sprints): DeepSeek $4.49/151.6min (cheapest,slowest); Grok $13.00/66.6min (fastest,
best value); Kimi $13.79/147.6min; Gemini $15.98/96.8min (138M tok); Opus $25.64/89min; Astra $30.55/99.9min.

Key finding: detection tracks DISGUISE not severity. Never-fixed ×0 (silent, disguised bugs) is the
sharpest separator. Arithmetic verified per model. ᶜ = Grok stale-#4 caveat (self-healed, minor).
