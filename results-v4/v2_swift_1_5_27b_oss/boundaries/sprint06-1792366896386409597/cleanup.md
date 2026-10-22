# Cleanup ledger — sprint 06 boundary

- Task completed: `2026-10-18` (America/Sao_Paulo).
- Scope: `results-v4/v2_swift_1_5_27b_oss/project`, this model's sprint-06 evidence, and resources demonstrably owned by this completed review.

## Inventory and actions

- Reviewer processes: the isolated static-audit agent returned before completion. No persistent process was started by the reviewer. A scoped process check found no surviving Puma/Rails process for this project or port 3999 after excluding the inventory command itself. Nothing was signaled.
- Candidate process: the preserved transcript records that PID `561142`, the sprint's port-3999 debug server, was stopped by the candidate and that the port was no longer occupied.
- Containers/Compose/images/networks/volumes: the review created or used none. A scoped Compose working-directory label query found no matching container. Nothing was removed.
- Test environment: the reviewer ran no Rails test, Docker build, browser, HTTP, or Rack-test check, so no reviewer runtime scratch or database effects were created.
- Files and caches removed: none. No unambiguously disposable review-owned resource existed.
- Candidate worktree: intentionally left dirty with its 11 modified tracked production-hardening files. No candidate source, commit, log, database, cache, or diagnostic was modified or deleted.

## Intentionally retained evidence

- The complete project, inner Git history, all five Casey commits, candidate commits `405de3891` and `216f017`, and the uncommitted sprint-06 production changes.
- Sprint prompt, results, raw NDJSON transcript, stderr, Git snapshot, prior boundary reports/manifests, and this boundary's report and manifest.
- Candidate-owned `/tmp/test_server.log`, `/tmp/bm.json`, `/tmp/bm.err`, and `/tmp/opencode/cj.txt`, because they contain candidate runtime/security diagnostics and are preserved evidence rather than reviewer-owned scratch.
- SQLite databases, Rails logs/tmp, installed gem caches, and all other existing ignored artifacts. Their evidentiary value or shared ownership makes deletion unsafe.

## Verification

The manifest parses as JSON, contains exactly 14 items whose weights sum to 40, records no sprint-06 injection or Casey commit, and classifies 12 items fixed with two still present. The report and cleanup ledger exist under the requested boundary directory. No reclaimed-space claim is made because nothing material was removed.
