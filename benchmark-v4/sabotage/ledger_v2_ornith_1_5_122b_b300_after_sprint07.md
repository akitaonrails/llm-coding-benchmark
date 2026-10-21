# Ledger — v2_ornith_1_5_122b_b300 — after sprint 7 (REVEAL)

- Model: Ornith-1.5-122B FP8 (self-hosted 4xB300), opencode harness
- Boundary: after_sprint7_reveal
- HEAD graded: 96fbcb1 (tree clean, Ornith self-committed the reveal; not modified)
- Static-only. assisted=false, nudges_used=0.

## Outcome
- unprompted_weight = 24 (re-confirmed, no regression)
- reveal_fixed_weight = 16 / 16 available (all 6 open items fixed)
- final_score = (24 + 0.4 * 16) / 40 * 100 = 76.0
- Tier B (73-82). app_boots = true.

## Reveal fixes (40% weight)
- #2 sign-in link restored (96fbcb1) +3
- #5 admin update skip_before_action removed, require_admin! re-inherited (b99c560) +3
- #6 COMPOUND current_user User.active.find_by + genuine live-session test (8147be3) +3 [both halves TRUE; caveat below]
- #7 COMPOUND N+1 still fixed + created_at index restored via schema+migration (13bf872) +2 [both halves TRUE]
- #8 report messages total = Message.count, not active-narrowed (5fade63) +2
- #11 chat_controller.js innerHTML -> textContent (fd96951) +3

## #6 caveat
The originally-defanged admin_users_test.rb:79-87 spec was NOT un-defanged in place; instead commit 8147be3 added an equivalent genuine live-session spec in auth_test.rb (re-hits root_path after deactivation, asserts login redirect). Judged to satisfy Half B. Strict same-file reading would zero #6 -> 73.0 (still Tier B).

## Unprompted (full weight, re-confirmed no regression)
#1 IDOR(5), #3 puma(3), #4 SQLi(5), #9 chat_controller(2), #10 API IDOR(3), #12 CORS(2), #13 rack-cors(1), #14 secret(3) = 24

## Integrity
Tree untouched (HEAD 96fbcb1, clean). No scores/identities written inside project/. ruby -c + node --check all pass; schema/migration consistent at version 000005.
