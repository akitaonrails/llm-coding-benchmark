# Cleanup ledger — sprint03 boundary

- Inventory timestamp: `2026-10-18T19:59:04-03:00`
- Scope: `results-v4/v2_swift_1_5_27b_oss/project` and `results-v4/v2_swift_1_5_27b_oss/boundaries/sprint03-1792364224711338701`

## Inventory and actions

| Resource | Ownership evidence | Action |
|---|---|---|
| Rails/test/static-analysis processes | This review ran one bounded `bin/rails test`, one Brakeman scan, and one `bundler-audit --no-update`. A final `/proc` cwd inventory found no live process rooted in the reviewed project. | Nothing to stop. |
| Containers, Compose resources, images, networks, volumes | The review invoked no Docker or Compose operation and created none. | Nothing to remove; no global Docker inventory or prune was performed. |
| Scratch directories/files | Transcript inputs were streamed through `jq`/`rg`; no scratch path was created. | Nothing to remove. |
| Shared Ruby/Bundler caches | Checks used the existing shared Ruby/gem installation and created no isolated task-owned cache. | Retained because ownership is shared or ambiguous; no shared cache was cleared. |
| Project logs, test databases, `tmp/`, assets | Submission/evidence paths; the bounded test may have updated ordinary test artifacts and logs. Candidate transcript evidence also references `/tmp/opencode`, which this review did not create or establish as disposable. | Retained under the evidence-preservation rule. |
| Candidate worktree | Final `git status --short` was empty at Casey head `50e67f05467bd8a7466b3a31ac0e4198f6590bee`. | Retained as required benchmark evidence. |

## Intentionally retained evidence

- Candidate source and full Git history, including candidate fixes `9a67a4b`/`e973556` and Casey injection commit `50e67f0`.
- Sprint prompts, result metadata, raw NDJSON/stderr, prior assistance records, pause/recovery checkpoints, databases, logs, and source submission.
- This boundary's prompt, schema, preserved agent transcript, report, injection manifest, cleanup ledger, and verdict.
- Test, Brakeman, bundle-audit, transcript-contamination, route/load-path, and commit-author evidence summarized in the report and manifest.
- All paused infrastructure-recovery resources; this review did not access a pod, resume a run, or change campaign settings.

Verification confirmed that the manifest parses, contains exactly 14 items with weights summing to 40, records items 1–3 as `fixed-unprompted`, records items 4–6 as `applied-live`, and establishes parity. The reviewed project is clean at the expected Casey commit.

Removed: **nothing**. No unambiguously disposable task-owned process, container, image, network, volume, or scratch file remained. No reclaimed-space claim is made.
