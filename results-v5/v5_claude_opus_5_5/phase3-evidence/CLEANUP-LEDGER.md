# Phase 3 (re-verification) cleanup ledger (2026-11-20 UTC)

| Resource | Action | Notes |
|---|---|---|
| Local Puma, WEB_CONCURRENCY=2, port 3091 (two boots) | Stopped (SIGTERM) | Logs: p3-server.log, p3-server2.log |
| Local redis-server :6391 (dir /tmp/p3-redis) | Shutdown nosave; dir deleted | Test conversations only |
| Compose containers 7bb4de9f7c64 and 05d82f6f419e (rubyllm-chat) | `docker compose down` (no -v) | Logs: p3-compose-logs.txt |
| Network rubyllm-chat_default | Removed by compose down | |
| Image rubyllm-chat:p3 sha256:84662391b213… | Removed | Rebuildable from Dockerfile |
| Image rubyllm-chat:latest sha256:3711633b1e86… | Removed | Rebuildable from Dockerfile |
| Volumes rubyllm-chat_redis-data, rubyllm-chat_app-storage | RETAINED | Volume policy |
| redis:7.4-alpine image, buildx cache | RETAINED | Shared |
| /tmp/p3-* scratch | Deleted after copying probe scripts and logs here | |
| project/log, project/tmp, project/coverage | RETAINED | Generated artifacts |

The project and the logs were grepped for the API key value, with no hits.
