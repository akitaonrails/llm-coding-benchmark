# Ledger — CAUGHT-UNPROMPTED snapshot (through sprint 6 vague capstone), all 14 items

Status of every planted item by end of the vague "make production-ready" capstone (sprint 6),
BEFORE the explicit reveal (sprint 7). Severity weights: Crit5/High3/Med2/Low1. Total = 40.

| # | item | sev | Opus 4.6 | Astra |
|---|---|---|---|---|
| 1 | tenant leak (web) | Crit 5 | FIXED | FIXED |
| 2 | login button | High 3 | FIXED | FIXED |
| 3 | nokogiri gem | High 3 | FIXED (→1.19.4) | FIXED (→1.19.4) |
| 4 | admin SQLi | Crit 5 | FIXED | FIXED |
| 5 | admin authz | High 3 | FIXED | FIXED |
| 6 | defang-and-plant | High 3 | **PRESENT** (test still assert true; .downcase dropped) | FIXED (test+guard restored) |
| 7 | N+1 + index | Med 2 | FIXED | FIXED |
| 8 | wrong aggregate | Med 2 | **PRESENT** (+propagated into API) | FIXED |
| 9 | deleted file | Med 2 | FIXED (restored, sanitize) | FIXED (obsoleted via JSON refactor) |
| 10 | API authz leak | High 3 | FIXED | FIXED |
| 11 | XSS | High 3 | FIXED (sanitize) | FIXED (escape) |
| 12 | permissive CORS | Med 2 | **PRESENT** (defaults to "*") | FIXED (removed CORS/rack-cors) |
| 13 | rack-cors 2.0.1 | Low 1 | FIXED (→3.0.0) | FIXED (removed) |
| 14 | hardcoded secret | High 3 | FIXED (→ENV) | FIXED (→ENV) |

## CAUGHT-UNPROMPTED (severity-weighted, denominator 40)
- **Astra: 40/40 (100%)** — every planted issue caught without ever being told.
- **Opus 4.6: 33/40 (82.5%)** — 3 survived to the reveal: #6 (High 3), #8 (Med 2), #12 (Med 2) = 7 pts.

The vague capstone lifted Opus a lot (it had missed the silent ones through sprint 5, then
audited and fixed most at "make production-ready"). What remained are the SUBTLEST: a defanged
test hiding a real bug (#6), a silently-wrong number it even copied into the API (#8), and a
CORS default it left permissive (#12). Sprint 7 (explicit reveal) tests whether Opus fixes
these once told.
