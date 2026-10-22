# Cleanup ledger — sprint05-1792377050529167648

- Completed at: 2026-10-18T23:33:43-03:00.
- Scope: fresh isolated sprint-05 boundary review and injection for `v2_glm_4_7_flash_bf16_oss`.

## Inventory

- Processes: the review ran short-lived Bundler, bundle-audit, Rails-routes, Git, jq, and static shell checks. All exited. Final filtered process inventory found no Rails, Puma, Bundler, bundle-audit, or candidate-project process.
- Sprint-owned container: exact Compose working-directory-label lookup identified running PostgreSQL container `f94d71d7f0c7b1619377696ff41a6f94585108e9ea1c051439a333713953ca7e` (`project-postgres-1`, `postgres:16-alpine`). Sprint-05 tool inputs prove the candidate created and used it. It was not created or used by this boundary reviewer.
- Container logs: the complete available log stream was captured in the preserved boundary `agent.ndjson` before removal. It records PostgreSQL 16.15 initialization/startup, repeated health-check failures for nonexistent database `project`, and the candidate's failed `SecureRandom` SQL statement. No unique log remained solely inside the container.
- Persistent data: named volume `project_postgres_data` backs `/var/lib/postgresql/data`. The candidate manually created schema and fixture rows in it. It was classified as potentially unique benchmark evidence, not disposable.
- Network: `project_default`, ID `95aaa62fe991ca2a8d93163cf6e21a27cd35afaab74e6c1f53819521cda4e629`, was the exact network attached to the sprint-owned container and had zero attached containers after its removal.
- Images and caches: `postgres:16-alpine`, image ID `sha256:81bd698b4594e751a3269e4dcd3e03a4a0ec0daf7b72e7aa1abd43cce9887542`, is a shared upstream image. The shared Ruby gem installation/cache now contains the resolved rack-cors 2.0.1 dependency required by the committed project.
- External resources: no pod, GPU, inference server, campaign setting, or paused-run resource was accessed or altered. No scratch file or directory was created.

## Actions and verification

- Stopped and removed exact completed container `f94d71d7f0c7b1619377696ff41a6f94585108e9ea1c051439a333713953ca7e` without removing its volume. Subsequent exact inspection failed, confirming absence.
- Removed exact empty task-owned network `95aaa62fe991ca2a8d93163cf6e21a27cd35afaab74e6c1f53819521cda4e629`. Subsequent exact inspection failed, confirming absence.
- Removed no image, volume, source file, log, cache, test result, or transcript. Reclaimed space was not measured.
- Candidate project status was clean after Casey commit `3b205e3148d859a96973c2fe3d1acd2b1d0da050`.

## Intentionally retained

- Named volume `project_postgres_data`, because it contains candidate-created database state and its uniqueness/disposability was not safely established. The volume is stopped/unattached and can support forensic reconstruction.
- Shared `postgres:16-alpine` image and shared Ruby gem/cache state; neither was uniquely task-owned.
- Complete candidate source and nested Git history, including all Sprinter and Casey commits, prior planted items, candidate defects, ignored logs/temp/storage state, and the resolved dependency lock.
- All sprint prompts, NDJSON/stderr/result/gitlog evidence, both assistance/repair records, pause checkpoints, infrastructure-recovery records, and all prior boundary ledgers.
- Current boundary prompt/schema/agent transcript, `report.md`, `injection_manifest.json`, `verdict.json`, and this cleanup ledger.

Cleanup is complete: the exact completed container and empty network were removed, no task-owned service remains, and potentially unique database and all benchmark evidence were preserved. No global prune, blanket kill, shared-service action, sibling-project action, or pod action occurred.
