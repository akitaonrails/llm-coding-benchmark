# Cleanup ledger — sprint-01 boundary review

- **Inventory time:** 2026-10-17T15:59:33-03:00
- **Scope:** `results-v4/v2_dsv4_flash_oss` boundary review only.
- **Execution resources created by reviewer:** one derived transcript-input scratch file; no container, Compose project/network, image, volume, application server, HTTP loop, pod connection, model runner, or build cache.

## Removed

| Resource | Ownership evidence | Action | Result |
|---|---|---|---|
| `/tmp/v2_dsv4_flash_oss_tool_inputs.tsv` (65,365 bytes) | Created during this review solely by extracting the current model's transcript tool inputs for contamination scanning | Removed by exact path after the scan was summarized in `report.md` | Verified absent |

The file was fully regenerable from the preserved sprint NDJSON. The byte count is the removed file size, not a claim of filesystem blocks reclaimed.

## Intentionally retained

- All candidate source and Git history, including commit `5d55ac0dd484694ee46e9ef4abca9d16d13f22e1`; the project worktree remained clean and unmodified by the reviewer.
- All sprint prompts, normalized result metadata, raw NDJSON, stderr log, git-log snapshot, and boundary agent session artifacts.
- Candidate-generated runtime and forensic evidence: `log/development.log`, `log/test.log`, both SQLite databases, five failure screenshots, compiled assets, and all committed `tmp/cache` files. Some are poor candidate repository hygiene, but they are preserved evidence and were not treated as reviewer-owned scratch.
- `config/master.key` and encrypted credentials exactly as submitted. The key was neither read nor printed; it remains because deleting or rewriting candidate evidence is forbidden.
- Boundary outputs: `report.md`, `injection_manifest.json`, this ledger, prompt/schema, and `agent.ndjson`.
- PID 1014202, the active boundary-review Codex process that owns this session.
- PID 1682473, a pre-existing shared `opencode ... serve --service` process. It was not started, used, signaled, or claimed by this task.

## Verification

- No task-owned service or child runner was found to stop.
- Docker state was not queried because this static boundary created and used no Docker resources and the task explicitly forbids Docker work.
- No shared inference server, GPU resource, other project, sibling generated app, campaign setting, or paused-run resource was touched.
- The only reviewer-owned disposable file was removed; all result and evidence artifacts remain.
