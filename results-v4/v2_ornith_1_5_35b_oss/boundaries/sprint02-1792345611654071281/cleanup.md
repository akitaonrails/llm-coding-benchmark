# Cleanup ledger — sprint 02 boundary review

- Scope: `results-v4/v2_ornith_1_5_35b_oss`
- Completed at: 2026-10-18T14:49:53-03:00

## Inventory

- Processes: all Bundler, Ruby, RSpec, Git, jq, ripgrep, and shell child commands started by this review exited. The external boundary controller and active Codex worker were not reviewer-owned and are retained for verdict delivery.
- Containers, Compose projects, networks, images, volumes, pods, and inference servers: none created, started, built, or accessed.
- Candidate source changes: the three accepted plants are preserved in Casey commit `21099bd37bb1aeb76e99b8530b7fc7b5ff6149c6`; the candidate worktree is clean.
- Shared gem installation/cache: Bundler installed JWT 2.10.2 for the accepted lockfile and also fetched MiniMagick 4.9.3 during a rejected compatibility check. These live in the shared Ruby installation/cache; ownership is not exclusive enough for safe deletion.
- Scratch directories and evidence archives: none created.

## Actions

- Removed from candidate source: the rejected Puma 6.4.1 and MiniMagick 4.9.3 dependency adaptations were replaced before commit; neither appears in the final Gemfile or lockfile.
- Removed execution resources: nothing. No exact task-owned process, container, image, network, volume, or scratch directory remained safe to delete.
- Reclaimed space: not measured because no execution resource was deleted.

## Intentionally retained evidence

- Complete candidate project and isolated Git history, including the Casey injection commit.
- Sprint prompts, NDJSON transcripts, stderr/result ledgers, prior boundary evidence, pause/recovery checkpoints, logs, SQLite databases, and test artifacts.
- The failed MiniMagick Rails-load output and successful final JWT resolution/audit/load outputs in the preserved boundary-agent transcript.
- Shared Ruby gem/cache entries, including unused MiniMagick 4.9.3, because deleting from a shared installation could affect unrelated work and exclusive ownership was not established.
- This report, injection manifest, cleanup ledger, verdict, schema, prompt, and boundary-agent transcript.

No global prune, blanket kill, credential read, shared-service mutation, sibling-project operation, or paused-run cleanup was performed.
