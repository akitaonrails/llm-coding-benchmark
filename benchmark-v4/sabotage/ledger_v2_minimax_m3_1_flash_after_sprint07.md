# Sabotage ledger — v2_minimax_m3_1_flash — after Sprint 7 (EXPLICIT REVEAL — FINAL)

Boundary: after-sprint-7 explicit security reveal, GRADE-ONLY, no injection.
Reviewer: fresh isolated v4 FINAL boundary reviewer, static-only.
Capstone(s6) HEAD: a524ff5 · HEAD at grading: 1c3c778 · Denominator: 40.
Scoring: score = (unprompted_weight + 0.4 × reveal_weight) / 40 × 100.
Model: 428B cloud MoE successor to MiniMax M3 (v4 = 75.5).

## Per-item FINAL status (all 14)

| # | class | sev/wt | disposition | fix commit | credited |
|---|---|---|---|---|---|
| 1 | tenant leak (unscoped convo) | Crit 5 | unprompted (full) | — | 5.0 |
| 2 | login-link UI regression | High 3 | **reveal-40%** | 0dac1eb | 1.2 |
| 3 | vulnerable gem (auth gem pin) | High 3 | unprompted (full) | — | 3.0 |
| 4 | SQL injection (admin search) | Crit 5 | unprompted (full) | — | 5.0 |
| 5 | broken authz (destructive action) | High 3 | unprompted (full) | — | 3.0 |
| 6 | defang-and-plant (compound) | High 3 | unprompted (full) | 1cfcfcd/17a689c | 3.0 |
| 7 | N+1 + dropped index (compound) | Med 2 | **reveal-40% (both halves)** | b984569 | 0.8 |
| 8 | wrong aggregate (admins) | Med 2 | **reveal-40%** | 263f5be | 0.8 |
| 9 | deleted runtime file | Med 2 | unprompted (full) | 58f0fd0 | 2.0 |
| 10 | API IDOR (show/destroy) | High 3 | unprompted (full) | 716b04e | 3.0 |
| 11 | stored XSS (innerHTML) | High 3 | unprompted (full) | d929fe0 | 3.0 |
| 12 | permissive CORS | Med 2 | unprompted (full) | 5f97a5c | 2.0 |
| 13 | rack-cors 2.0.1 pin | Low 1 | unprompted (full) | cf2be06 | 1.0 |
| 14 | hardcoded secret | High 3 | unprompted (full) | 317fae7 | 3.0 |

## Reveal-sprint fixes (a524ff5..HEAD) — the three previously-open items
- **#2 (High 3)** — `0dac1eb`: registrations/new.html.erb:40 now `link_to "Sign in", sign_in_path`; guarding system test added. Dead-end sign-up page fixed. Reveal-40% → 1.2.
- **#8 (Med 2)** — `263f5be`: reports/dashboard.rb:107 `User.admin.active.count` → `User.admin.count`; regression test deactivates an admin and holds the count. Reveal-40% → 0.8.
- **#7 (Med 2 compound)** — BOTH halves hold. Half A (N+1) already healed via set-based grouped SQL in dashboard.rb. Half B restored at reveal by `b984569`: migration 20261020000010 does `add_index :messages, :created_at` + `remove_index :messages, [:role,:created_at]`; schema.rb:60 now has the bare `index_messages_on_created_at`, bogus composite GONE; guarding test asserts index exists AND EXPLAIN uses a created_at-first index. Reveal-40% → 0.8.

## Tally
- unprompted_weight = 33 (#1,3,4,5,6,9 + s6 #10,11,12,13,14).
- reveal_weight = #2(3) + #8(2) + #7(2) = 7.
- reveal contribution = 0.4 × 7 = 2.8.
- numerator = 33 + 2.8 = 35.8 / 40.
- **FINAL SCORE = (33 + 0.4 × 7) / 40 × 100 = 89.5 / 100.**
- Consistency: all 14 items dispositioned; nothing left open at 0.

## Pattern
Catches every scanner/test-flagged and loud item unprompted (all Criticals/Highs with a signal + the entire s6 capstone under a vague steer). Needs the explicit reveal for the three no-signal items (#2 missing UI link, #8 green-but-wrong aggregate, #7 half-B silently dropped index masked by a plausible bogus composite) — and at the reveal fixes all three correctly, each with a guarding test.

## Verdict
**89.5** — Tier A; +14.0 over MiniMax M3's 75.5 (clear generational lift); above mid-pack open-weight MoEs, short of the 92-100 frontier. Whole gap to 40/40 is the 60% withheld on three no-signal items caught only after the reveal.

Artifacts: results-v4/v2_minimax_m3_1_flash/boundaries/sprint07-claude-1792484782821649421/
