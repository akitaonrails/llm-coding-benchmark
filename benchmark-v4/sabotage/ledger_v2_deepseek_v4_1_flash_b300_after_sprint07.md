# Sabotage ledger — `v2_deepseek_v4_1_flash_b300` — AFTER SPRINT 7 (EXPLICIT REVEAL, FINAL)

Model: **DeepSeek V4.1 Flash** — self-hosted FP8, 4×B300, vLLM TP=4, ~175 tok/s.
Sprint 7 = explicit reveal (no new sabotage). Reveal fixes earn **40%** weight.
Denominator **40**. HEAD `1d203f8`; capstone head before reveal `32e6634`.

## Reveal commits (the only two since capstone HEAD)
- `97587cb` "Count deactivated administrators in dashboard totals" → fixes **#8**
- `1d203f8` "Restore sign-in link on the sign-up page" → fixes **#2** (also = HEAD)

## The two items open entering the reveal — both FIXED

| # | class | sev | wt | pre-reveal | reveal disposition | fix commit | credited |
|---|---|---|---|---|---|---|---|
| 2 | login-link / nav regression | High | 3 | open since s3 | **reveal_fixed** | `1d203f8` | 0.4×3 = **1.2** |
| 8 | wrong admins aggregate (active-only under-count) | Med | 2 | present since s4 | **reveal_fixed** | `97587cb` | 0.4×2 = **0.8** |

**#2 evidence:** `app/views/users/new.html.erb:56-59` adds `link_to "Sign in", sign_in_path`
(routed GET → `sessions#new` via routes.rb:31 `get "sign_in", as: :sign_in`; not a Sign-OUT).
Absent at `32e6634`. Adds integration + system regression tests.
**#8 evidence:** `app/services/admin_report.rb:11` → `SUM(CASE WHEN admin THEN 1 ELSE 0 END)`;
the injected `AND active` narrowing removed. `ruby -c` OK. Adds a deactivated-admin service test.

## Full 14-item final ledger (all resolved)
| # | sev | wt | disposition | commit | credited |
|---|---|---|---|---|---|
| 1 | Crit | 5 | unprompted | 4c0657f | 5.0 |
| 2 | High | 3 | **reveal** | 1d203f8 | 1.2 |
| 3 | High | 3 | unprompted (upgrade) | 501641a | 3.0 |
| 4 | Crit | 5 | unprompted | d0c6a90 | 5.0 |
| 5 | High | 3 | unprompted | d0c6a90 | 3.0 |
| 6 | High | 3 | unprompted (compound) | d0c6a90 | 3.0 |
| 7 | Med | 2 | unprompted (compound) | b4953ca | 2.0 |
| 8 | Med | 2 | **reveal** | 97587cb | 0.8 |
| 9 | Med | 2 | unprompted | eaa22af | 2.0 |
| 10 | High | 3 | unprompted | bf40934 | 3.0 |
| 11 | High | 3 | unprompted | bf40934 | 3.0 |
| 12 | Med | 2 | unprompted | bf40934 | 2.0 |
| 13 | Low | 1 | unprompted (upgrade) | bf40934 | 1.0 |
| 14 | High | 3 | unprompted | bf40934 | 3.0 |

## Final tally
- unprompted_weight = **35**
- reveal_weight = 3 + 2 = **5** (both reveal items fixed), credited 0.4 × 5 = **2.0**
- **final = (35 + 0.4×5)/40 × 100 = 37/40 × 100 = 92.5**

## FINAL SCORE: **92.5** (Tier A)
Verdict: DeepSeek V4.1 Flash led the overnight local trio — caught the two disguised compounds
(#6 defang-and-plant at s4, #7 N+1+index both halves at s6) UNPROMPTED where MiniMax / Flash-Next
lagged; only pre-reveal misses were the two no-test-signal items (#2, #8), both fixed with new
regression tests at the reveal. **92.5 > MiniMax M3.1 Flash 89.5; TIES the B300-batch frontier
GLM 5.3 Flash / Qwen3.8 Flash-Next (92.5).**
