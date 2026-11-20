# Phase 2 cleanup ledger (2026-11-19/20)

| Resource | Action | Notes |
|---|---|---|
| Local Puma (WEB_CONCURRENCY=2), masters 2821440 and 2823905 | Stopped (SIGTERM) | Logs preserved: p2-server.log, p2-server2.log |
| Local redis-server :6390 (pid 2820174, dir /tmp/p2-redis) | Shutdown nosave; dir deleted | Contained only test conversations |
| Compose containers 07f38099e91a (redis), 4e1821f0c8e7 (web) | Removed via `docker compose down` (no -v) | Logs preserved: p2-compose-logs.txt |
| Network 2ce54ada1c06 rubyllm-chat_default | Removed | |
| Image rubyllm-chat:latest sha256:3711633b1e86… | Removed | Rebuildable from Dockerfile |
| Image sha256:84662391b213… (untagged, previous build) | Removed | Rebuildable from Dockerfile |
| Volumes rubyllm-chat_redis-data, rubyllm-chat_app-storage | RETAINED | Volumes are kept by policy |
| Image redis:7.4-alpine, buildx cache | RETAINED | Shared, not owned by this task |
| /tmp/p2-scripts, /tmp/p2-*.log, /tmp/p2-env.sh | Deleted after copying into this directory | p2-env.sh contained no secret values |
| project/log, project/tmp, project/coverage | RETAINED | Generated artifacts kept as evidence |

The logs were checked for the API key prefix, and none was found.
