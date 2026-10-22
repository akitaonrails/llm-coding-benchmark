# Cleanup ledger — sprint-03 boundary review

- **Inventory time:** 2026-10-17T16:14:04-03:00
- **Scope:** `results-v4/v2_dsv4_flash_oss` sprint-03 boundary review only.
- **Execution resources created by reviewer:** one derived transcript-input scratch file; no container, Compose project/network, image, volume, application server, HTTP loop, pod connection, model runner, or build cache.

## Removed

| Resource | Ownership evidence | Action | Result |
|---|---|---|---|
| `/tmp/v2_dsv4_flash_oss_sprint03_tool_inputs.jsonl` (32,325 bytes) | Created during this review solely by extracting the current model's 76 sprint-03 transcript tool inputs for contamination scanning | Removed by exact path after the findings were recorded in `report.md` | Verified absent at 2026-10-17T16:14:04-03:00 |

The byte count is the removed file's logical size, not a claim about filesystem blocks reclaimed.

## Intentionally retained

- All candidate source and Git history through sprint commit `8c6dd01`, plus Casey's prescribed injection commit `abc3f8da05c0cc1df81dde991ba89f305ced4eae`.
- All sprint prompts, normalized metadata, raw NDJSON, stderr logs, git-log snapshots, and boundary agent-session artifacts.
- The report, injection manifest, prompt/schema, verdict, and this cleanup ledger under the requested sprint-03 boundary directory.
- Candidate/runtime forensic evidence in `app/assets/builds/tailwind.css`, `log/`, `storage/`, and `tmp/cache/`. These paths were already dirty before injection and were also exercised by the bounded route/test checks; they were preserved rather than reset or deleted.
- Submitted credentials artifacts such as `config/master.key` exactly as found. No secret value was read or printed.
- Active task controller PID 1063611 (`b300_boundary.py`) and reviewer PID 1063612 (`codex exec`), which are required for this boundary session to finish and therefore were not signaled.
- Two pre-existing Puma processes (PIDs 2755277 and 3988554). They were not started, used, inspected beyond the process inventory, or attributed to this task; ownership was not established, so they were not touched.

## Verification

- No reviewer-started service or child runner remained after the completed foreground checks.
- Docker state was not queried because this static boundary created and used no Docker resources and the task forbids Docker work.
- No pod, campaign setting, shared inference server, GPU resource, sibling generated app, other project, or paused-run resource was accessed or changed.
- The one verified reviewer-owned disposable resource was removed. Source, tests, reports, transcripts, databases, logs, caches, and all forensic evidence remain.
