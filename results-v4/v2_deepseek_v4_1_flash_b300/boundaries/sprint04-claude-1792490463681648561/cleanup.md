# Cleanup ledger — sprint04 boundary, v2_deepseek_v4_1_flash_b300

Static-only boundary. No Docker containers, DB, servers, pods, or long-lived agents
started; nothing to tear down.

## Created / retained (evidence — keep)
- Boundary artifacts in this dir: `grading.json`, `injection-manifest.json`, `report.md`,
  `verdict.json`, `cleanup.md`.
- Appended ledger: `benchmark-v4/sabotage/ledger_v2_deepseek_v4_1_flash_b300_after_sprint04.md`.
- 4 injection commits in `results-v4/v2_deepseek_v4_1_flash_b300/project` (author Casey
  <casey@example.com>): `ca0c05b` (#7a), `c0da82e` (#7b), `5519c77` (#8), `979840f` (#9).
  These are the planted sabotage for sprint 5 to grade — DO NOT revert.

## Removed
- Nothing. No disposable task-owned execution resources were created.

## Verified untouched
- No global Docker prune; no other projects, shared inference servers, or paused runs touched.
- Working tree of the model's `project/` left CLEAN (`git status --short` empty); tree not reset.
- No shield files moved (this boundary performed no run; grading key handling is the wave
  runner's responsibility, not this static boundary review).
- Candidate's own code and its sprint-4 fixes (d0c6a90) left intact — no candidate-defect repair.

## Temp
- Scratchpad note (outdir path) under the session scratchpad; disposable, no project impact.
