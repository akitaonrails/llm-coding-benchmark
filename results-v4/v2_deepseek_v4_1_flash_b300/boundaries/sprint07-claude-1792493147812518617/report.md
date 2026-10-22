# v4 FINAL boundary report — `v2_deepseek_v4_1_flash_b300` (after sprint 7, explicit reveal)

**Model:** DeepSeek V4.1 Flash — self-hosted FP8 on 4×B300, vLLM tensor-parallel ×4, ~175 decoded tok/s.
**Boundary:** sprint 7 is the *explicit reveal*. Only the two items still open entering it are graded here; reveal fixes earn **40%** of their weight. Static-only grading (git + grep + file reads + `ruby -c`); no execution, no injection.
**Denominator:** 40. **Head:** `1d203f8`. **Capstone head before reveal:** `32e6634`.

## State entering the reveal (from sprint-6 grading)
35/40 weight already caught **UNPROMPTED** across sprints 3–6 (#1,#3,#4,#5,#6,#7,#9,#10,#11,#12,#13,#14). Two items remained open — exactly the two the model never had a failing test or broken flow to surface:
- **#2** removed sign-in nav link (High, 3) — silent UI regression, no test.
- **#8** admins total under-counts (Med, 2) — green-but-wrong aggregate, no test.

## Reveal grading — the two remaining items

### #2 — login link / nav regression (High 3) → REVEAL-FIXED, +1.2
Commit **`1d203f8` "Restore sign-in link on the sign-up page."**
- `app/views/users/new.html.erb:56-59` now appends:
  `Already have an account? <%= link_to "Sign in", sign_in_path, ... %>`.
- `sign_in_path` is a **routed GET affordance** to the sign-in page — `config/routes.rb:31`:
  `get "sign_in", to: "sessions#new", as: :sign_in`. It is **not** a Sign-OUT (those are `session_path, method: :delete` in the sidebar/admin layouts).
- At capstone HEAD `32e6634` the file ended at the "Create account" submit with **no** footer sign-in link (verified: `git show 32e6634:app/views/users/new.html.erb`) — the affordance injection `455c22a` removed. Open and untouched through sprints 3–6.
- Commit also adds regression coverage: integration `assert_select "a[href=?]", sign_in_path, text: "Sign in"` and a system test that clicks the link and asserts `assert_current_path sign_in_path`.
- Fixed only after the explicit reveal → **0.4 × 3 = 1.2**.

### #8 — silently wrong aggregate, admins counted only when active (Med 2) → REVEAL-FIXED, +0.8
Commit **`97587cb` "Count deactivated administrators in dashboard totals."**
- `app/services/admin_report.rb:11` TOTALS_SQL is now
  `(SELECT SUM(CASE WHEN admin THEN 1 ELSE 0 END) FROM users) AS admins_count` — the injected `AND active` narrowing is **removed**; all admins are counted regardless of active state.
- `row["admins_count"]` flows to `totals.admins` (`admin_report.rb:74`), rendered on the dashboard Admins card and served via `AdminReportSerializer` through `GET /api/v1/admin/dashboard`. `ruby -c` → Syntax OK.
- Commit also adds a service test creating one active + one deactivated admin and asserting `assert_equal 2, totals.admins` while active stays 1 — the exact green-but-wrong case now has a guard.
- Persisted silently through sprints 4–6 (no test surfaced it); fixed only after the reveal → **0.4 × 2 = 0.8**.

## Final arithmetic
```
unprompted_weight = 35
reveal_weight     = (#2 ? 3 : 0) + (#8 ? 2 : 0) = 3 + 2 = 5
final = (35 + 0.4 × 5) / 40 × 100 = (35 + 2) / 40 × 100 = 37 / 40 × 100
      = 92.5
```
**FINAL SCORE = 92.5**

## Per-item final disposition (all 14 resolved)
| # | class | sev | wt | disposition | credited |
|---|---|---|---|---|---|
| 1 | tenant leak | Crit | 5 | unprompted_fixed | 5.0 |
| 2 | login-link regression | High | 3 | **reveal_fixed** | **1.2** |
| 3 | puma CVE pin | High | 3 | unprompted_fixed (real upgrade) | 3.0 |
| 4 | SQLi admin search | Crit | 5 | unprompted_fixed | 5.0 |
| 5 | broken authz (promote) | High | 3 | unprompted_fixed | 3.0 |
| 6 | defang-and-plant (compound) | High | 3 | unprompted_fixed (both halves) | 3.0 |
| 7 | N+1 + dropped index (compound) | Med | 2 | unprompted_fixed (both halves) | 2.0 |
| 8 | wrong admins aggregate | Med | 2 | **reveal_fixed** | **0.8** |
| 9 | deleted wired controller | Med | 2 | unprompted_fixed | 2.0 |
| 10 | API IDOR | High | 3 | unprompted_fixed | 3.0 |
| 11 | stored XSS (innerHTML) | High | 3 | unprompted_fixed | 3.0 |
| 12 | permissive CORS | Med | 2 | unprompted_fixed | 2.0 |
| 13 | rack-cors CVE pin | Low | 1 | unprompted_fixed (real upgrade) | 1.0 |
| 14 | hardcoded secret | High | 3 | unprompted_fixed | 3.0 |
| | | | **40** | | **37.0 → 92.5** |

## Verdict in context
DeepSeek V4.1 Flash on 4×B300 **led the overnight local trio.** It caught both *compound* traps unprompted — #6 (defang-and-plant, in a single sprint-4 hardening commit whose message named each flaw) and #7 (N+1 **and** the dropped `messages.created_at` index, both halves) — where the overnight peers were weaker on the disguised compounds. Its only two misses before the reveal were the two **no-signal** items (#2 silent nav regression, #8 green-but-wrong aggregate) with neither a red test nor a broken happy-path to trip on; it fixed both cleanly at the explicit reveal, each with a new guarding test.

- **vs overnight peers:** 92.5 > MiniMax M3.1 Flash 89.5 — DeepSeek's unprompted compound-catching (#6 at s4, #7 both halves) is the gap.
- **vs B300-batch frontier:** 92.5 **ties** GLM 5.3 Flash / Qwen3.8 Flash-Next (92.5). The open-weight B300 frontier is at parity on this realistic Rails+sabotage suite; the residual is the universal blind spot — defects with no test signal, fixed only when told.
