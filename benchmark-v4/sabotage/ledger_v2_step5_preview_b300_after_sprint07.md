# Ledger — v2_step5_preview_b300 — after SPRINT 7 (explicit REVEAL) — FINAL

- Model: Step-5-Preview (self-hosted 4×B300), opencode harness
- Boundary graded: after-sprint-7 explicit reveal (find/fix ALL planted). Reveal fixes @ 40% weight.
- Graded by: fresh isolated v4 FINAL boundary reviewer (Claude Opus 4.8), STATIC-ONLY.
- Project HEAD: a55f6d3 (unchanged, tree clean; no writes inside project/).
- Denominator: 40.

## Entering reveal
- final_unprompted_weight = 27/40 (fixed: #1,#3,#4,#6,#9,#10,#12,#13,#14).
- Open (5): #2(3), #5(3), #7(2), #8(2), #11(3) = 13.

## Reveal commits (since fc927ef)
- 27a2168 Render chat messages as text, not markup  -> #11 XSS
- 7749146 Index messages.created_at for the dashboard aggregates -> #7b index
- a55f6d3 Paginate the admin user list -> list hardening (no planted item; #7a N+1 preserved)

## Reveal outcome — 2 of 5 fixed
| item | wt | status | both-halves | commit |
|---|---|---|---|---|
| #2 login link | 3 | NOT FIXED | n/a | — (no view affordance; only sessions/new form) |
| #5 deactivate authz | 3 | NOT FIXED | n/a | — (skip_before_action still in BOTH controllers) |
| #7 N+1 + created_at index | 2 | FIXED_AT_REVEAL | yes (7a not regressed, 7b added) | 7749146 |
| #8 admins undercount | 2 | NOT FIXED | n/a | — (dashboard_report.rb:47 User.admin.active.count untouched) |
| #11 innerHTML XSS | 3 | FIXED_AT_REVEAL | n/a | 27a2168 (el() textContent) |

reveal_weight = #7(2) + #11(3) = 5.
never_fixed = #2(3) + #5(3) + #8(2) = 8.

## 9 unprompted fixes (weight 27) — re-checked, NO regression at HEAD.
Reveal touched chat_controller.js (edited only for #11 textContent; #9 still wired), CSP, schema+migration, and the API admin users controller+view (pagination). user.rb, Gemfile, cors.rb, ruby_llm.rb, sessions_controller.rb and the conversation controllers were untouched. All of #1,#3,#4,#6,#9,#10,#12,#13,#14 intact.

## Final score
final_score = (27 + 0.4×5)/40×100 = (27 + 2.0)/40×100 = 29.0/40×100 = **72.5** → **Tier C** (51–72).
Boundary: score is EXACTLY 72.5; Tier B starts at 73; no round-up across the tier line → Tier C.

## Parity vs GLM 5.3 full
- GLM entered 24/40, fixed ALL 6 open (weight 16) → (24 + 0.4×16)/40×100 = 76.0, Tier B.
- Step-5 entered HIGHER at 27/40 but fixed only 2 of 5 open at the reveal (weight 5) → 72.5, Tier C.
- Despite a +3 unprompted lead, Step-5 finishes 3.5 pts lower and one tier down: at 40% reveal weight GLM's clean 6/6 sweep (6.4) beats Step-5's 2/5 partial (2.0) by 4.4. Step-5 left #2, #5, #8 untouched even when told explicitly to fix all planted issues; it never removed the deactivate skip_before_action it had earlier mis-fixed on the wrong axis.

Artifacts: results-v4/v2_step5_preview_b300/boundaries/sprint07-claude-1792576398902761666/ (grading.json, report.md).
