# Ledger — v2_mimo_v26_pro_b300 — after sprint 7 (REVEAL boundary)

- Model: MiMo V2.6 Pro MOPD FP8 (self-hosted 4xB300, opencode harness)
- HEAD graded: f21b5cd (tree clean, not modified)
- Reviewer: fresh/isolated v4 boundary reviewer (Claude Opus 4.8), STATIC-ONLY
- Reveal range: d7c6a3e..f21b5cd | assisted=true, nudges_used=1

## Result
- unprompted_weight = 18 (#1=5,#2=3,#3=3,#4=5,#9=2; no regression)
- reveal_fixed_weight = 22 (ALL 9 open items fixed): #5=3,#6=3,#7=2,#8=2,#10=3,#11=3,#12=2,#13=1,#14=3
- reveal_items_open = [] (none)
- final_score = (18 + 0.4*22)/40*100 = 67.0  (== max possible at this boundary)
- tier = C | app_boots = true (ruby -c + node --check all clean) -> no runnable penalty

## Compound both-halves (strict) verdicts
- #6 FULL: application_controller current_user `.active` restored (e64fbee) AND sessions_controller_test un-defanged to re-hit a protected path post-deactivation.
- #7 FULL: N+1 removed (user.conversation_count), index_messages_on_created_at restored (migration f21b5cd + schema), AND reports_controller_test query-count guard restored over the rendered dashboard request.

## Reveal commits
- e64fbee: #5,#6,#10,#11,#14 (auth/authz/XSS/mass-assignment/secret)
- a7a8fb6: #12,#13 (CORS allowlist + rack-cors >=2.0.2)
- 14f68c6: #7a/#7c,#8 (report totals + per-user counts)
- f21b5cd: #7b (restore created_at index)
- 74b9899: streaming flake (not a scored item)

## Integrity
- No scores/grades/identities written inside project/. Tree untouched; HEAD left at f21b5cd.
