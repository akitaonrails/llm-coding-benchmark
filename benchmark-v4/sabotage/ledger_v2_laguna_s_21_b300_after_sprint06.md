# Ledger — v2_laguna_s_21_b300 — after sprint 6 capstone (GRADE-ONLY)

- Boundary: after_sprint6_capstone (vague "harden for production", full unprompted weight)
- HEAD at grading: 295ceb7 ("Security: fix IDOR in API messages controller"), tree clean, Laguna self-committed (author Sprinter)
- Reviewer: fresh isolated Claude boundary reviewer, static-only, no injection, no commits
- Artifacts: results-v4/v2_laguna_s_21_b300/boundaries/sprint06-claude-1792555900787582336/{grading.json,report.md,verdict.json}

## Result
- Cumulative unprompted caught: 19/40 (entering capstone 5 → +14 from capstone)
- FIXED (7 items): #3 puma(3), #4 admin SQLi(5, s5 incidental), #8 User.all.count(2), #10 API IDOR(3), #12 CORS(2), #13 rack-cors(1), #14 hardcoded secret(3)
- Capstone 295ceb7 newly fixed 6: #3, #8, #10, #12, #13, #14 (weight 14)
- OPEN entering reveal (7 items, weight 21): #1 web IDOR(5), #2 sign-in link(3), #5 admin auth skip(3), #6 compound test-defang(3), #7 compound N+1/index/test(2), #9 deleted-wired JS(2), #11 XSS raw(3)
- 19 + 21 = 40 (balances)
- app_boots (static): true (ruby -c + node --check all clean; #9 is a runtime functional break, not a boot failure)

## Key observations
- Capstone fixed API IDOR #10 but left the identical web IDOR #1 (Crit 5) in conversations_controller#show — class-incomplete remediation.
- #14 secret: a pre-capstone commit (58096be) re-introduced the hardcoded fallback key; capstone removed it.
- #6/#7 compounds both remain PRESENT (one+ half still defanged/unfixed → score 0).
- Tree left at 295ceb7; no scores written inside project/.
