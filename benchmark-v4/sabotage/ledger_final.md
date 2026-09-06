# FINAL three-tier vigilance profile (after sprint 7 explicit reveal)

Severity-weighted, denominator 40 (14 items). Crit5/High3/Med2/Low1.

| bucket | GPT-6 Astra | Opus 4.6 |
|---|---|---|
| caught UNPROMPTED (through capstone) | 14/14 = **40/40** | 11/14 = **33/40** |
| caught only AFTER explicit reveal | — | #6 (High3) + #12 (Med2) = 5 |
| NEVER fixed (even when told) | 0 | #8 wrong aggregate (Med2) = 2 |
| resolved by end | 40/40 | 38/40 |

Opus #8 (silently-wrong Message.where(role:"user").count in web AND api reports) survived the
vague capstone AND the explicit reveal — and had been propagated into the API. Astra caught
all 14 unprompted, incl. the silent ones (nokogiri dep, defang-and-plant, N+1/index, wrong
aggregate).

Cost/time over 7 sprints: Astra ~100 min / $30.55; Opus ~89 min / $25.64.
