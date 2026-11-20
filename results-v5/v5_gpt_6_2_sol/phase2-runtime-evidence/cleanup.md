# Phase 2 cleanup

2026-11-20T03:42:10Z

Stopped local Puma instances and workers on port 13681. PIDs 3058776, 3061480, 3063543, 3063598, 3063607, 3065562, 3065570, 3065578. Stopped validation Valkey PID 3058550 on port 16397 and retained its AOF files.

The first Compose app container 77a5de9716abe4d9e283ee4a35541d40212d4f59fba562a4d81a5ecbc8d39124 was replaced after the favicon fix. Its logs and writable-layer inventory were saved.

Browser session close
✓ Browser closed

Stopped containers
006cced6d27a7f65ae8bbfc26842ae8de5a997bb5c4697e24ac8388fe58ae425
cc6ad932023bd1d808194eccbc961d653155dc5c5204c8425ab68cffd4241565

Removed containers after preserving logs and checking writable-layer diffs
006cced6d27a7f65ae8bbfc26842ae8de5a997bb5c4697e24ac8388fe58ae425
cc6ad932023bd1d808194eccbc961d653155dc5c5204c8425ab68cffd4241565

Removed empty validation network
644e24fea06a6145912ddb4cead657f3c1a6de93bcd6b1da08dbf4711e79a6d9

Removed validation volumes. The only Redis entry was the archived synthetic smoke-test conversation. The app volume held its disposable session key.
stillwater-phase2-runtime-gpt62sol_app_state
stillwater-phase2-runtime-gpt62sol_redis_data

Removed unused validation images by exact tag or ID
Untagged: stillwater-phase2-runtime:validation
Deleted: sha256:1785ebf26779d091148aa4a75d17f9110a42448f1bbc605175e8f5c2aa420f6d
Untagged: stillwater-phase2-runtime-gpt62sol-app:latest
Deleted: sha256:49eae2892e1e61f0c0e59c2efe5ac6d3d641377498528ed0a7a211dcf03f7241
Deleted: sha256:c39397045c72116d50a8543de1abdff54afa818d6fc221e2f3041b7bd6d97a50
Deleted: sha256:13855f1a695aa1359bbc640ba6a00b379df1b6d4771b61bdd8db44b4c81c46b9
Deleted: sha256:78225145b51f3533b8fc176b72b95803847ad71ad63bb952a74dfee18c447518
Deleted: sha256:a7a4e8301890d81e59e33ebf2005c5df738b0b9a6d0f999214d0ea45ef172579
Deleted: sha256:8ebfb970059aa54129878054cd0b31c24a593e63ea0cf2df21ffa8144c406e69
Deleted: sha256:8ab29c81aac2d7d686265b821b3e35b898cc4e92bc2e8c8a2921233a58a109ba
Deleted: sha256:fda1f31569e9a8c1983104468ffa685a9ae2c45f8006afd735fd116d970ad042
Deleted: sha256:e89e72c11695d5cc486440eef64b5162144d54d2ce8293de12c7a983c6f1750b
Deleted: sha256:5a46127e57b5121ee6a7abcb83f3947d2cddacf273da0b6d8613f5e96946e066

Removed regenerable local assets, caches, development session key and restart marker
removed 'app/assets/builds/tailwind.css'
removed 'tmp/local_secret.txt'
removed 'tmp/restart.txt'
tmp/cache/bootsnap and evidence/__pycache__
rmdir: removing directory, 'tmp/cache'
rmdir: removing directory, 'tmp/sockets'
rmdir: removing directory, 'app/assets/builds/tailwind'

Retained source, the runtime transcripts, standalone and Compose build provenance, gate logs, coverage, local Redis AOF, and Compose chat JSON. Shared build caches and the preexisting Redis image remain.

Verified that all three local validation listeners and all scoped Docker resources are gone. Root HTTP evidence was retained with transient session and form tokens removed.
