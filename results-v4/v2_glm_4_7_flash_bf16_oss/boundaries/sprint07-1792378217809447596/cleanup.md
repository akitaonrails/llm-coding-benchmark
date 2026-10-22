# Cleanup ledger — sprint07-1792378217809447596

- Completed at: 2026-10-18T23:52:07-03:00.
- Scope: fresh isolated sprint-07 boundary audit for `v2_glm_4_7_flash_bf16_oss`.

## Inventory and ownership

- Review processes: short-lived Git, jq, Ruby syntax, `bundle-audit`, and one `bin/rails routes` process. All exited; no reviewer-started server or long-running test process was created.
- Candidate sprint container: exact ID `6567082ec6aa008555312e6d127297a39c379fbae1160ab2eddc6e9577aa1aa5`, name `agitated_mendeleev`, image `postgres:16-alpine` (`sha256:81bd698b4594e751a3269e4dcd3e03a4a0ec0daf7b72e7aa1abd43cce9887542`), created `2026-10-19T02:39:32.463749852Z`, running on the shared `bridge` network. Ownership is established by the sprint-07 transcript input `docker run --rm -d -p 5433:5432 ... postgres:16-alpine` followed by repeated commands naming this container. It had no Compose labels or project bind mounts.
- Candidate anonymous database volume: `2aa661c4b3da6baf3a827bec139792d4dc33a02bdbcf03540b66440d7fe63cdc`, mounted at `/var/lib/postgresql/data`. It was uniquely attached to the `--rm` candidate test container.
- Container writable-layer size before cleanup: 63 bytes. Root filesystem size was 294,292,583 bytes, but that is image-backed virtual size and is not reported as reclaimed space.
- Shared resources: the `postgres:16-alpine` image and Docker `bridge` network were not task-unique. No Compose application image, task-specific network, build cache, pod, GPU, inference server, campaign setting, or sibling-project resource was created or used by this review.

## Evidence preservation

Before stopping the completed candidate container:

- Preserved its full logs as restricted `candidate-postgres.log` (349,101 bytes, mode 600, SHA-256 `009dcf866bb98c77bcb3892e5370db57bd1f02dcc16f5b1e1226140a4846adc8`).
- Preserved the unique `project_test` database as restricted custom-format `candidate-project-test.pg_dump` (8,646 bytes, mode 600, SHA-256 `9380e50950fc1b6c92941ef1b08470c6fc718380feac39296dfc9989ddf19da7`). `pg_restore -l` validated the archive.
- No credential values or unfiltered container environment inspection were printed or added to the report.

## Actions and verification

- Stopped exact completed container ID `6567082ec6aa008555312e6d127297a39c379fbae1160ab2eddc6e9577aa1aa5`. Because the candidate created it with `--rm`, Docker removed that container and its anonymous volume automatically after stop.
- Verified the exact container no longer exists.
- Verified anonymous volume `2aa661c4b3da6baf3a827bec139792d4dc33a02bdbcf03540b66440d7fe63cdc` no longer exists after its database contents were archived.
- Retained shared image `sha256:81bd698b4594e751a3269e4dcd3e03a4a0ec0daf7b72e7aa1abd43cce9887542` and shared bridge network `8756fb713c2c815e1ba069723f5e1f3fe97c51debf700f88025d7ddc4ebfdcef`.
- Actual reclaimed bytes were not measured; no image virtual size is presented as reclaimed space.

## Intentionally retained

- Complete candidate source submission and nested Git history, including all committed Sprinter/Casey changes and all sprint-07 uncommitted modifications, deletions, new migration, ignored logs/temp state, and dependency locks.
- All sprint prompts, raw NDJSON/stderr/result/gitlog evidence, both assistance/repair records, pause checkpoints, infrastructure-recovery records, and all prior boundary ledgers.
- Current boundary prompt/schema/agent transcript, report, manifest, verdict, cleanup ledger, preserved PostgreSQL log, and validated database dump.
- Shared Docker image/network and any unrelated project or paused-run resource.

Cleanup is complete. No global prune, blanket kill, candidate-source repair, sibling action, pod action, shared-image deletion, or campaign alteration occurred.
