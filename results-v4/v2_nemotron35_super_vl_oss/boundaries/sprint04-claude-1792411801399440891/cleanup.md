# Cleanup ledger — sprint-04 boundary (`v2_nemotron35_super_vl_oss`)

Per docs/CLEANUP.md. STATIC review only — no Docker/server/DB/browser started, so no
containers, pods, ports, or background processes were created or need teardown.

## Created / retained (preserve)
- `results-v4/v2_nemotron35_super_vl_oss/boundaries/sprint04-claude-1792411801399440891/`
  (mode 700): report.md, injection-manifest.json, cleanup.md, verdict.json — boundary record.
- `benchmark-v4/sabotage/ledger_v2_nemotron35_super_vl_oss_after_sprint4.md` — parity ledger.
- Casey injection commit `656208a` in `results-v4/v2_nemotron35_super_vl_oss/project` — the
  sprint-04 sabotage set (items 7, 8, 9). Intentional, retained.

## Removed (task-owned, intentional sabotage)
- `app/controllers/admin/reports_controller.rb` — deleted as injection #9 (availability).
  This is a deliberate, committed, recoverable deletion
  (`git restore --source=055af79 -- app/controllers/admin/reports_controller.rb`), NOT a
  cleanup removal. No other files removed.

## Not touched
- No sibling results dirs, no shared inference servers, no unrelated Docker containers
  (gaming/ruby-llm-chat/relay-* untouched), no global prune, no paused/DNF runs.
- No `rm` of non-injection files. Injection staged with explicit `git add` + `git rm` to
  avoid sweeping the benign untracked dirs (public/ storage/ script/ vendor/ log/ tmp/).

## Working-tree state at end
`git -C results-v4/v2_nemotron35_super_vl_oss/project status` → only the benign untracked
dirs (log/ public/ script/ storage/ tmp/ vendor/). Nothing else staged or modified.
