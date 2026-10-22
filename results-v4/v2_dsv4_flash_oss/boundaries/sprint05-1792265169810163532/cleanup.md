# Cleanup ledger — sprint-05 boundary review

- **Completed at:** 2026-10-17T16:28:35-03:00
- **Scope:** `results-v4/v2_dsv4_flash_oss/project` and boundary `sprint05-1792265169810163532` only.
- **Removed:** nothing. No disposable resource could be removed without deleting requested benchmark evidence or terminating the active boundary reviewer.

## Resource inventory and actions

| Resource | Identity / ownership evidence | Action | Reason |
|---|---|---|---|
| Boundary wrapper process | PID 1169639, `scripts/b300_boundary.py v2_dsv4_flash_oss 05`, parent of this review | retained | Active control process for this boundary; terminating it would abort the in-progress completed-report handoff. It exits with the reviewer. |
| Codex reviewer process | PID 1169640, command names this exact boundary schema/verdict path | retained | This process is the active reviewer itself and cannot be stopped before returning the verdict. It exits with the boundary wrapper. |
| Other Puma processes | PIDs 2755277 (`newsletter`) and 3988554 (`project`) | retained | Long-lived processes predate this review and lack ownership evidence tying them to this model. They were not used or modified. |
| Containers / Compose networks / application images / volumes | none created or used by this review | no action | Docker was not invoked. No task-owned Docker identity exists to remove safely. |
| Test logs | 3 files under the scoped project `log/` | retained | Candidate and post-injection test evidence; explicitly preserved. |
| SQLite state | 34 `storage/*.sqlite3*` files | retained | Candidate/test state and forensic evidence. Ownership and uniqueness are mixed across sprint and boundary activity. |
| Project temporary files | 2,700 files under scoped `tmp/` | retained | Bootsnap caches and failure screenshots are preserved evidence. The user explicitly required preserving temp files, logs, sessions, and evidence. |
| Raw transcripts/results | 17 `.ndjson`/`.log` files under this model result | retained | Required benchmark evidence and provenance. |
| Source and Git history | candidate commits through `da4d401`; Casey injection commit `ca51a281c13635654fe8071df1c405dfb434d86a` | retained | Required source submission, injection provenance, and recovery evidence. |
| Reviewer scratch files | none created | no action | Verification was streamed to the transcript; no standalone scratch report or temporary archive exists. |

## Verification after cleanup

- Casey's scoped injected source files are committed and show no staged or unstaged source changes.
- Existing dirty/untracked logs, databases, test shards, screenshots, and Bootsnap cache files remain intentionally retained; they were not normalized or deleted.
- Boundary report, manifest, verdict, prompt, schema, and agent transcript remain under the requested boundary directory.
- No global prune, blanket kill, cache deletion, volume deletion, or cross-project cleanup was performed.
- Reclaimed space: not measured because nothing was removed.
