# Scoped cleanup ledger

- Completed: `2026-10-17T21:05:46-03:00`
- Scope: sprint-01 boundary review for `v2_qwen3_8_flash_next_oss`
- Ownership basis: exact Compose working directory, Compose image labels, image creation timestamp within the recorded sprint, candidate transcript provenance, and exact resource IDs. Names alone were not used.

## Inventory and actions

| resource class | inventory | action | verification |
|---|---|---|---|
| Processes | The boundary `bundle exec rspec` completed; no process command line referenced the target project after review. | None required. | Final scoped process scan returned no rows. |
| Containers | No container carried `com.docker.compose.project.working_dir` equal to the target project. | None required. | Final exact-label scan returned no rows. |
| Compose networks | No network carried the target working-directory label. | None required. | Final exact-label scan returned no rows. |
| Compose volumes | No volume carried the target working-directory label. | None required. | Final exact-label scan returned no rows. Candidate transcript line 558 already records removal of its current `rubyllm-chat` volume/network. |
| Application image | `rubyllm-chat-web:latest`, image `sha256:a9acadb03d98ba3732105a922def8e677043f923206a566444f9c5edfef6adf3`, created `2026-10-18T00:02:17.436495613Z`, virtual size 907,635,880 bytes, labels `com.docker.compose.project=rubyllm-chat`, `service=web`, `version=5.5.1`, no repo digest, and no dependent container. Build recipe remains in `project/Dockerfile` and `project/docker-compose.yml`. | Removed by exact immutable ID without force. Docker also deleted unreferenced image objects `sha256:669868c20a7df1389ee9b825aa19f0daa8d6c7fb4db7185aa5e40642435b39f2` and `sha256:64cac06a68c1fdd18f7c8afb59ba564e2940366a28be80fee8ab61470fc3954e`. | Exact-ID inspect now returns `No such image`. No reclaimed-space claim is made because the recorded size was virtual size. |
| Build cache and shared runtime/gem caches | Cache records are not attributable to this task with sufficient certainty. | Retained as ambiguous/shared. | No global prune was run. |
| Test artifacts | `log/test.log`, `storage/test.sqlite3`, the new Capybara failure screenshot, existing screenshots, and other ignored `tmp` state. | Retained intentionally as test evidence. | Summarized in `validation.txt`; source submission was not repaired or cleaned. |
| Results/evidence | Sprint NDJSON, stderr/result JSON, pause checkpoints, project source and Git metadata, boundary agent log, report, manifests, validation, and assistance record. | Retained intentionally. | Boundary artifacts validated before cleanup. |
| Shared/external infrastructure | Model servers, GPUs/pods, unrelated Docker resources, installed gems, and the pre-existing pause/recovery records. | Not touched. | Outside scoped ownership or required as evidence/resume provenance. |

## Important retained incident evidence

The candidate transcript reports that it previously removed an unrelated stale Compose stack and foreign volumes (`sprint01_foundation.ndjson:553`). This boundary did not attempt speculative recovery or delete any further foreign resource. The serious incident remains documented in `report.md`.

No scratch directory was created by this boundary. No source, transcript, log, session, database, screenshot, pause checkpoint, manifest, or analysis artifact was deleted.
