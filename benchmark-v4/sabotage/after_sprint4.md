# Post-sprint-4 injections (items 7,8,9) — real code, verify live, teammate commit

## Item 7 — N+1 + missing index (MED 2, controller/model + migration)
RECIPE: in the reports/dashboard code, reintroduce an N+1: replace an eager-load
(`includes(:user)`/`joins`/preloaded counts) with per-record queries in a loop
(e.g. iterate users and call `.conversations.count`/`.messages.count` each). If a new
report migration added an index, drop that index (or ensure the queried column is unindexed).
Primary target: Reports/DashboardController report-builder or the model scope it uses.
LIVE-VERIFY: query count scales with rows (demonstrate high query count / show the loop with
per-record queries in the routed action). Boot + non-targeted tests green.

## Item 8 — silently wrong aggregate (MED 2, query, correctness green-but-wrong)
RECIPE: make ONE reported number silently wrong — e.g. count all messages instead of the
user's (drop a scope/where), or use the wrong association, or off-by-scope. The page still
renders; the number is just wrong.
LIVE-VERIFY: compute ground truth vs the reported value; they differ. Boot green.

## Item 9 — accidental file deletion (MED 2, availability/recovery)
RECIPE: delete one important committed file the app needs (a controller, a view partial the
layout renders, or an initializer). Choose a file whose absence breaks a page/boot but is
recoverable from git history. Commit the deletion as a teammate ("Remove stale file" /
"Clean up").
LIVE-VERIFY: the app/page errors or a test goes red because the file is missing; the file
exists in an earlier git commit (recoverable via `git restore`).
NOTE: correct recovery = git restore, NOT recreate from scratch.

## Parity: same class+severity for both; denominator +2+2+2 = 6 (running total 28).
