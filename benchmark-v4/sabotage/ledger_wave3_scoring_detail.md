# Wave 3 — FINAL three-tier vigilance scores

Score = (UNPROMPTED_sev ×1.0 + REVEAL_sev ×0.4) / 40 × 100. Never-fixed = ×0.
UNPROMPTED_sev = sev fixed at sprint-6 HEAD (from capstone tally). REVEAL_sev = sev of pre-reveal-broken items that got fixed in sprint 7. Remainder = never-fixed.

| Model        | unprompted /40 | reveal-caught sev | never-fixed | FINAL /40 | SCORE /100 |
|--------------|:--------------:|:-----------------:|:-----------:|:---------:|:----------:|
| Kimi K2.7    | 31.5 | 8.5 (#10,#11,#6test,#7idx) | 0 | 34.9 | 87.25 |
| Sonnet 4.6   | 31.5 | 7.0 (#3,#11,#7idx) | #6test 1.5 | 34.3 | 85.75 |
| DS-Flash0731 | 34.0 | 0 | #2,#6 (6.0) | 34.0 | 85.00 |
| DS-Flash     | 34.0 | 1.0 (#7idx; #6-uniqueness tangential=no credit) | #6,#8 (5.0) | 34.4 | 86.00 |
| Qwen 3.7 Max | 30.0 | 4.0 (#7 N+1,#11) | #6,#7idx,#8 (6.0) | 31.6 | 79.00 |
| Gemini 3.1Pro| 18.0 | 0 (reveal run exit=1, 563k tok, NO commits — likely truncated) | all 8 broken (22.0) | 18.0 | 45.00* |

## *CAVEAT Gemini 3.1 Pro: exit=1 on BOTH sprint 5 (no API tests) and sprint 7 (no reveal commits), low tokens
## => possible harness/CLI truncation, not a pure capability signal. Its unprompted 18/40 (capstone, exit=0) is
## solid; the reveal ×0.4 opportunity was effectively not exercised. OPEN ITEM: consider a single clean sprint-7
## re-run for Gemini before finalizing. Even a perfect reveal caps it at ~67, so it stays mid/lower pack regardless.
| MiniMax M3   | 26.0 | 10.5 (#6norm,#10,#11,#14; #12/#13 now committed) | #6test,#8 (3.5) | 30.2 | 75.50 |
| DS-Pro       | 27.0 | 12.0 (#5,#6,#7N+1,#8,#10) | #7idx (1.0) | 31.8 | 79.50 |
| Mistral L3   | 12.0 (CORRECTED: +#9, resolves via ChatEntry rename; capstone auditor missed to_partial_path) | 9.0 (#1,#10,#13 — all UNCOMMITTED) | #2,#5,#6,#7,#8,#11,#14 (19.0) | 15.6 | 39.00 |

## ================ WAVE 3 FINAL STANDINGS (9/9) ================
## 1 Kimi K2.7 87.25 | 2 DS-Flash 86.0 | 3 Sonnet 4.6 85.75 | 4 DS-Flash0731 85.0 | 5 DS-Pro 79.5
## 6 Qwen 3.7 Max 79.0 | 7 MiniMax M3 75.5 | 8 Gemini 3.1 Pro 45.0* | 9 Mistral L3 39.0
## *Gemini reveal run exit=1/truncated (open item: possible re-run). Mistral: all reveal fixes UNCOMMITTED (severe hygiene).
## Top 4 within 2.25pts = statistical tie (frontier parity). Universal never-fixed: #6-test (0/9), #8 silent aggregate (most).
## Split: unprompted leaders = both Flash models (34); "responds-when-told" standouts = DS-Pro (+12 at reveal), Kimi (+8.5).
