# Cleanup ledger — sprint02 boundary

- Timestamp: `2026-10-17T19:38:03-03:00`
- Scope: boundary review for `v2_swift_1_5_27b_oss` only.

## Inventory and actions

| Resource | Ownership evidence | Action |
|---|---|---|
| `/tmp/v4_swift_s02_tool_inputs.tsv` (10,182 bytes) | Created by this review solely to scan the 35 candidate tool inputs | Removed by exact path; absence verified. The byte count is file size, not a claim of measured filesystem reclamation. |
| Rails/Bundler test processes | Process inventory found no leftover `bundle install`, `bundle lock`, or Rails test process. | Nothing to stop. |
| PIDs 2592762/2592763 | Active B300 boundary controller and this Codex review process; command lines point to this boundary directory. | Intentionally retained as active orchestration, not leftover execution resources; not signaled. They terminate with the boundary controller workflow. |
| Docker containers, images, networks, volumes | This review invoked no Docker or Compose command and created none. | Nothing to remove; no global Docker inventory or prune was performed. |
| Devise 4.7.0 in the shared mise Ruby gem store | Installed by the boundary's `bundle install` while testing the prescribed pin; path is under the shared Ruby installation rather than a task-owned isolated bundle. | Retained because the shared gem store may serve other projects; ownership/disposability is ambiguous. It is not selected by this project's restored lockfile. |
| Project `tmp/`, logs, SQLite files, Bundler/Ruby caches | Existing submission/evidence paths or shared caches; the failed boot check may have touched ordinary cache/log metadata. | Retained under the evidence-preservation rule; no speculative cache deletion. |

## Preserved evidence

- Candidate source, commits, sprint results, prompts, raw NDJSON transcripts, stderr logs, session metadata, and assistance records.
- Casey partial injection commit `b8e4b3cb74622a790b5c9ba761dec8460f4259b4` containing accepted items 1–2.
- `report.md` and `injection-manifest.json`, including the rejected item-3 boot failure and bundle-audit result.
- The clean candidate/Casey project history and all database/log/test artifacts.

No paused run resources, shared model servers, GPUs, other projects, sibling generated applications, containers, images, networks, or volumes were altered.
