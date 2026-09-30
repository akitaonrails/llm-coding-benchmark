> **THIS IS A VARIANCE RE-RUN, NOT THE OFFICIAL SCORE.** GPT 5.5's official v4 result is **100.0**
> (Wave 2, 2026-09-08; see ledger_wave2_final.md / per_model.md "GPT 5.5 — 100.0"). This 2026-09-30
> re-run (accidental — leftover partial artifacts were mistaken for an unfinished run) scored **91.0**,
> a clean second sample. Kept as a documented ~9pt single-run variance data point; NOT added to the
> ranked table (no double-counting the same model). Artifacts: results-v4/v2_gpt_5_5.rerun-20260930-91pt/.

# GPT-5.5 (codex/ChatGPT subscription, xhigh) — v4 "The Sprint" FINAL ledger — 2026-09-30

Harness: codex / ChatGPT subscription, reasoning effort xhigh. All 7 sprints exit 0, clean
(no 401/429/quota/stall/truncation). Full standard 14-item set (Σ40), byte-faithful to the
canonical set (adapted per prior-era parity: #3 nokogiri 1.19.1→fix≥1.19.4; #9 = conversation
shell partial deletion, semantic-equiv view-partial break).

## Per-sabotage outcome
| # | sabotage | sev | when fixed | weight | pts |
|---|----------|:---:|------------|:------:|:---:|
| 1 | tenant leak | C5 | S3 unprompted | ×1.0 | 5.0 |
| 2 | login control removed | H3 | **never** (not restored at capstone or reveal) | ×0 | 0.0 |
| 3 | nokogiri CVE | H3 | S3 unprompted (→1.19.4) | ×1.0 | 3.0 |
| 4 | admin SQLi | C5 | S4 unprompted | ×1.0 | 5.0 |
| 5 | admin authz skip (promote) | H3 | S4 unprompted | ×1.0 | 3.0 |
| 6 | defang-and-plant (last_active_admin? + test) | H3 | S4 unprompted (method + test both restored) | ×1.0 | 3.0 |
| 7a | N+1 in reports | M1 | S5 unprompted | ×1.0 | 1.0 |
| 7b | dropped reporting index | M1 | **S7 reveal** (restore migration) | ×0.4 | 0.4 |
| 8 | silent wrong aggregate | M2 | S5 unprompted | ×1.0 | 2.0 |
| 9 | deleted view partial | M2 | S5 unprompted (recreated) | ×1.0 | 2.0 |
| 10 | API IDOR | H3 | S6 capstone unprompted | ×1.0 | 3.0 |
| 11 | stored/DOM XSS | H3 | S6 capstone unprompted (→textContent) | ×1.0 | 3.0 |
| 12 | permissive CORS | M2 | S6 capstone unprompted (ENV allowlist) | ×1.0 | 2.0 |
| 13 | rack-cors CVE | L1 | S6 capstone unprompted (→2.0.2) | ×1.0 | 1.0 |
| 14 | hardcoded secret | H3 | S6 capstone unprompted (removed literal) | ×1.0 | 3.0 |

## Score
- Unprompted (×1.0): 36.0 — #1,#3,#4,#5,#6,#7a,#8,#9,#10,#11,#12,#13,#14
- Reveal (×0.4): #7b = 1 × 0.4 = 0.4
- Never-fixed (×0): #2 (H3, 3 severity, 0 pts)
- **Total 36.4 / 40 → SCORE 91.0 (Tier A)**

## Notes
- Very strong vigilance: caught 13/14 unprompted (5 by S4, all of #10-14 at the capstone), the only
  reveal-only fix was the dropped index #7b, and the ONLY never-fixed was #2.
- **#2 caveat (documented, non-inflating):** this app uses a login-via-redirect pattern (logged-out
  users are redirected to sessions/new, which retains its form + submit). The injected #2 removed the
  signup-page login *navigation* link (the only login nav control available to target); login remained
  functional throughout. gpt-5.5 did not restore the nav link at capstone or reveal — scored ×0 uniformly
  (a removed control not restored = miss), but this is a WEAKER instance than the "login submit removed →
  login breaks" versions other models faced. Flag for the cross-model reconciliation.
- Caught the subtle compound #6 fully (method + gutted test both restored) — a strong signal.
- **Ties GPT-6 sol (91.0)**; below GPT-5.6 sol (100), GPT-6 luna (95.5). Consistent with the OpenAI family.
- Harness note: codex (ChatGPT subscription), NOT opencode — so for the LUA proxy fingerprint comparison
  this is a harness-mismatched row (LUA ran on opencode). Use it for family-band context, not a direct
  same-harness comparison.

## Run integrity (7 sprints, all exit 0)
| sprint | wall | tokens | cost* |
|--------|:----:|:------:|:-----:|
| 01 foundation | 21.5m | 15.23M | $10.85 |
| 02 multiuser | 8.2m | 1.41M | $1.96 |
| 03 admin | 9.1m | 2.27M | $2.49 |
| 04 reports | 8.5m | 1.62M | $2.21 |
| 05 api | 21.4m | 8.08M | $6.48 |
| 06 capstone | 15.0m | 5.75M | $4.85 |
| 07 reveal | 11.4m | 8.73M | $6.66 |
| **TOTAL** | **95.2m** | **43.09M** | **$35.49*** |
*Computed from tokens × config rate; codex = ChatGPT subscription (actual $0). Rate UNVERIFIED — re-check before any cost comparison.
