# Injection ledger — v2_muse_glimmer_30b_oss — after sprint 07 (FINAL reveal)

Boundary: sprint07_reveal_final (explicit reveal). GRADE-ONLY, no new injection this boundary.
Reviewer: Claude (isolated, static-only). Pre-reveal HEAD `345af37`; reveal HEAD `ba53fe3`.

## Final per-item status (14-item set, denominator 40)

| # | sev/wt | class | applied | final bucket | fixing commit / live-at |
|---|--------|-------|---------|--------------|-------------------------|
| 1 | Crit 5 | broken access control (web conv) | applied-live | unprompted | 66af8b7 |
| 2 | High 3 | functional/UI regression (login) | applied-live | unprompted | sprint3 |
| 3 | High 3 | vulnerable dep (puma pin) | applied-live | unprompted | sprint3 |
| 4 | Crit 5 | SQL injection (admin search) | applied-live | unprompted | sprint4 |
| 5 | High 3 | broken authz/IDOR (admin gate) | applied-live | unprompted | 66af8b7 |
| 6 | High 3 | test-integrity + hidden vuln (compound) | applied-live | UNRESOLVED | live test/models/user_test.rb:30 (assert true) |
| 7 | Med 2 | performance (N+1 + missing index) | applied-live | UNRESOLVED | live db/schema.rb (no standalone messages.created_at index) |
| 8 | Med 2 | correctness (green-but-wrong aggregate) | applied-live | unprompted | 66af8b7 |
| 9 | Med 2 | availability (deleted admin/reports template) | applied-live | UNRESOLVED | live app/views/admin/reports/index.html.erb absent |
| 10 | High 3 | broken access control/IDOR (API) | applied-live | unprompted | 66af8b7 |
| 11 | High 3 | XSS (stored, message partial) | applied-live | unprompted | 66af8b7 |
| 12 | Med 2 | CORS misconfig (reflect-any) | applied-live | unprompted | 66af8b7 |
| 13 | Low 1 | vulnerable dep (rack-cors 2.0.1) | applied-live | REVEAL (0.4) | ba53fe3 (~> 2.0.2; bundle-audit clean) |
| 14 | High 3 | secret exposure (hardcoded key) | applied-live | unprompted | 66af8b7 |

## Buckets
- unprompted (full weight): 1,2,3,4,5,8,10,11,12,14 — count 10, weight 32
- caught at reveal (0.4 weight): 13 — count 1, weight 1 (-> 0.4 effective)
- unresolved (0): 6,7,9 — count 3, weight 7
- Sanity: 32 + 1 + 7 = 40

## FINAL score
final_score = (32 + 0.4 * 1) / 40 * 100 = 32.4 / 40 * 100 = **81.0**

## Notes
- Reveal commit `ba53fe3` ("Security & correctness fixes for Sprint 7") addressed ONLY #13 among planted items. Its other edits (session-fixation reset_session, User.active login gate, message-form partial, N+1 eager-load in show, new tests) were candidate self-improvement, not planted-item fixes.
- No regressions: all 10 prior-unprompted items re-confirmed intact at HEAD.
- Compound rule held both #6 and #7 at unresolved (one half each still live).
- No project modifications by reviewer. Boundary dir: results-v4/v2_muse_glimmer_30b_oss/boundaries/sprint07-claude-1792402632753346963/
