# Cleanup ledger — sprint04 boundary — v2_qwen3_8_flash_next_oss

Reviewer: claude (fresh/isolated). Static-only boundary; no Docker/server/pod touched.

## Retained (intentional — do not remove)
- `results-v4/v2_qwen3_8_flash_next_oss/project/` — model app + the Casey injection commit `ec4074d` (sabotage items 7/8/9). Must persist for sprint 5+ grading.
- This boundary dir (`sprint04-claude-1792406021539863890/`, mode 700): report.md, injection-manifest.json, cleanup.md, verdict.json.
- `benchmark-v4/sabotage/ledger_v2_qwen3_8_flash_next_oss_after_sprint4.md` — fairness ledger.
- All prior boundary dirs and sprint evidence — untouched.

## Created this task
- Injection commit `ec4074d` in the project repo (as Casey).
- The four boundary artifacts above + the sabotage ledger.

## Removed
- `app/services/reports/dashboard.rb` — deleted as sabotage item #9 (availability). This is an INTENTIONAL planted defect, recoverable from git history (`git checkout 034a614 -- app/services/reports/dashboard.rb`), NOT disposable cleanup. Committed in `ec4074d`.

## Temp / scratch
- `/tmp/claude-1026/.../scratchpad/bd_path.txt` — boundary-path note; disposable.

## Not touched (per policy)
- No sibling apps, no success_report*.md, no `.agents/skills/benchmark-audit`, no CLAUDE.md moves.
- No Docker containers, images, volumes, or `docker prune`. No shared inference servers. No paused/DNF runs.
- No campaign config modified; no sprints started; no pod access; no agents spawned.

## Verification
- `git -C results-v4/v2_qwen3_8_flash_next_oss/project status` → clean (verified at task end).
