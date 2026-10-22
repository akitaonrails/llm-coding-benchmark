# Cleanup ledger — boundary sprint02 (v2_glm_5_3_full_b300)

Per docs/CLEANUP.md. STATIC-ONLY boundary task; nothing to prune.

## Removed
- (none) — no Docker containers/images, no DB/server processes, no temp build artifacts were
  created. No `rm` performed.

## Intentionally retained (evidence — preserve)
- `results-v4/v2_glm_5_3_full_b300/project/` — the model's app with injections #1-#3 committed
  (Casey), base `63e32d7`. Working tree clean.
- This boundary dir: `injection-manifest.json`, `report.md`, `verdict.json`, `cleanup.md`.
- Appended ledger `benchmark-v4/sabotage/ledger_v2_glm_5_3_full_b300_after_sprint02.md`.

## Not touched (out of scope)
- No sibling apps inspected. No shared inference server / pod touched. No sprint started.
- No global Docker prune; no unrelated containers touched.
- Gemfile.lock on-disk state preserved (the one `bundle lock --local --print` was non-mutating;
  md5 verified unchanged before+after).
