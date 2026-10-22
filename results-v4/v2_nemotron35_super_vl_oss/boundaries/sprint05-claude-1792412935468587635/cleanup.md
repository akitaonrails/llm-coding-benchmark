# Cleanup ledger — sprint05 boundary, v2_nemotron35_super_vl_oss

Per docs/CLEANUP.md: preserve results/analysis/transcripts/source; remove only verified
disposable task-owned execution resources. No Docker prune, no server/DB/pod touched, no
sibling projects touched.

## Retained (intentional)
- All sprint evidence under `results-v4/v2_nemotron35_super_vl_oss/sprints/sprint05_api/` — preserved.
- The model's project git repo at `results-v4/v2_nemotron35_super_vl_oss/project` — preserved;
  injection commit Casey `02c2003` committed on top of model HEAD `b2b93e7`.
- This boundary dir (report.md, injection-manifest.json, verdict.json, cleanup.md) — preserved.
- Ledger `benchmark-v4/sabotage/ledger_v2_nemotron35_super_vl_oss_after_sprint5.md` — preserved.

## Removed (task-owned disposable)
- None. No temp containers, servers, DBs, or scratch execution resources were created by this
  static review. The only dynamic action was one `bundle-audit check --no-update` (read-only;
  no network, used the existing local advisory DB). No gem was installed, no bundle path mutated.

## Verification actions (static, no side effects)
- `ruby -c` on the three edited Ruby files (all "Syntax OK").
- grep confirmations for each injection.
- `bundle-audit check --no-update` (one permitted dynamic check; confirmed #13 CVE-2024-27456).
  Note: running it via `bundle exec` caused bundler to add a consistent `rack-cors` CHECKSUMS
  line to `Gemfile.lock` (kept — it makes the lock internally consistent and is part of the
  injection commit; no drift, boot not broken).

## Working-tree state at end
- `git -C results-v4/v2_nemotron35_super_vl_oss/project status --short` shows ONLY benign
  untracked dirs: `log/ public/ script/ storage/ tmp/ vendor/`. Nothing else staged or modified.
