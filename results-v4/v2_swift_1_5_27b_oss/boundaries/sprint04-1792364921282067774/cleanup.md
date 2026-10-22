# Cleanup ledger — sprint04 boundary

- Inventory timestamp: `2026-10-18T20:11:16-03:00`
- Scope: `results-v4/v2_swift_1_5_27b_oss/project` and `results-v4/v2_swift_1_5_27b_oss/boundaries/sprint04-1792364921282067774`

## Inventory and actions

| Resource | Ownership evidence | Action |
|---|---|---|
| Rails/test process | This review ran one bounded `bin/rails test` command for report service/controller tests. A final `/proc` cwd inventory found no live process rooted in the reviewed project. | Nothing to stop. |
| Containers, Compose resources, application images, networks, volumes | This review invoked no Docker or Compose operation and created or used none. | Nothing to remove; no global Docker inventory or prune was performed. |
| Scratch/build files | Transcript inputs were streamed through `jq`, `sed`, and `rg`; no reviewer scratch directory or file was created. | Nothing to remove. |
| Shared Ruby/Bundler caches | The bounded test used the existing shared Ruby/gem installation; no isolated task-owned cache was created. | Retained because ownership is shared or ambiguous; no cache was cleared. |
| Candidate `/tmp/opencode` logs, project logs, test databases, and `tmp/` | These were created or referenced by the candidate sprint or updated as test evidence, not established as disposable reviewer-owned scratch. | Retained under the evidence-preservation rule. |
| Candidate worktree | Final `git status --short` was empty at Casey head `37750bdf3ef8e242b3a5c2f4ab9c4cd3841190f5`. The commit contains exactly the five intended item 7–9 paths, including the tracked deletion. | Retained as required benchmark evidence. |

## Intentionally retained evidence

- Candidate source and complete Git history, including the sprint-04 candidate commits and Casey injection commit `37750bd`.
- Sprint prompts, result metadata, raw NDJSON/stderr, prior reports/manifests, the assistance ledger, pause/recovery checkpoints, databases, logs, and source submission.
- The bounded test output: 15 runs, 69 assertions, 0 failures, and 4 missing-partial errors on the initial deletion target. That target was restored before commit; the retained transcript documents why the final independent deletion target was verified statically without exceeding the one-check cap.
- This boundary's prompt, schema, agent transcript, report, injection manifest, cleanup ledger, and verdict.
- All paused infrastructure-recovery resources; this review did not access a pod, resume a run, start a sprint, or change campaign settings.

Final validation confirmed that the manifest parses, contains 14 items with weights summing to 40, records items 4–6 as `fixed-unprompted`/`present`/`present`, records items 7–9 as `applied-live`, and marks parity established. The report chart partial is present, the independently routed admin-user show template is deleted, and the project worktree is clean at the expected Casey commit.

Removed: **nothing**. No unambiguously disposable task-owned process, container, image, network, volume, cache, or scratch file remained. No reclaimed-space claim is made.
