# Scoped cleanup ledger

- Model: `v2_qwen35_122b_oss`
- Boundary: `sprint02-1792278461694503538`
- Completed at: `2026-10-17T20:10:21-03:00`
- Procedure: `docs/CLEANUP.md`

## Inventory

- One local quick test-environment command was run in `project/rubyllm-chat`: a `RAILS_ENV=test bin/rails runner` verification. Its database writes were enclosed in a transaction and explicitly rolled back.
- One Bundler dependency-resolution attempt and one bundle-audit check were run. Bundler consulted the shared RubyGems metadata cache; no task-owned cache boundary could be established.
- The verifier created no Docker image, container, Compose stack, volume, or network and issued no Docker command.
- No pod, remote inference server, GPU resource, campaign setting, sprint runner, or sibling model resource was accessed.
- No scratch directory or temporary evidence file was created. The current boundary controller/Codex processes are active orchestration resources required to deliver this verdict, not abandoned execution resources.
- Post-check process inventory found no remaining Rails runner, Puma, Chrome, or chromedriver process for this model.

## Actions

- Removed during injection validation: the uncommitted, non-resolving `nokogiri 1.13.5` Gemfile line. It was not a valid planted change; the resolver failure is preserved in `verification.log` and the boundary transcript. `Gemfile.lock` was never changed by the failed resolution.
- Removed during scoped cleanup: **nothing**. No verified task-owned disposable process, container, image, network, volume, or scratch path remained.
- Shared Ruby/Bundler caches were retained because their ownership is not exclusive to this task.
- Reclaimed space: not measured; no resource deletion was performed.

## Evidence intentionally retained

- All candidate source, both candidate commits, the nested candidate repository, sprint prompts, raw transcripts, stderr/result JSON, timing/token metadata, pause checkpoints, test database, logs, screenshots, and project-local caches.
- Casey injection commit `a6fbb2e304330db1badd756058503935e5a0d93e`, containing only accepted items 1 and 2.
- The single-check verification result, dependency-resolution diagnosis, clean post-rollback bundle-audit result, injection manifest, report, and this cleanup ledger.
- The outer `project/.git` remains commitless with `rubyllm-chat/` untracked; this pre-existing nested-repository condition was not altered.

## Verification

- The nested app working tree is clean on `master` after the Casey commit.
- `injection_manifest.json` parses as valid JSON and lists all 14 fixed items.
- No `assistance.json` was written because no prior assistance existed and the blocker is a campaign recipe/parity conflict, not an ordinary candidate defect suitable for a nudge.
- No evidence or resumable run resource was deleted.
