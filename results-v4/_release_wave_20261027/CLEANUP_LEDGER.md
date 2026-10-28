# Cleanup ledger — v4 Tier-A release wave (2026-10-27/28)

Procedure: docs/CLEANUP.md. Inventory first; preserve all results/evidence; stop only
verified task-owned leftovers; no global prune, no git clean, no touching other projects.

## Processes
| Resource | PID(s) | State at cleanup | Action |
|----------|--------|------------------|--------|
| gates driver (`v4_release_gates.py`) | 128049, 1305565, 1356836 (successive) | all exited (last: exit 0, wave complete) | none needed — exited on their own |
| wave passes (`run_v4_release_wave.py`) | transient per pass | none alive | none |
| sprint/boundary children | transient | none alive | none |
| gate watchers (`gate_watch.py`, session scratchpad) | background tasks | all exited on driver death / marker change | none |

Verified quiescent: `pgrep` for run_v4_release_wave / run_v4_sprint / v4_release_boundary /
v4_release_gates / gate_watch all empty.

## Containers / networks / images
Read-only `docker ps -a` inventory. **No container, network, image, or Compose stack was
created by or is tied to this wave** (grading is static-only — no docker/DB/server; candidate
sprints produced no running stacks tied to `_release_wave_20261027`, `v2_kimi_k3_1_pro`, or
`v2_gpt_6_1_terra`). Nothing removed. Pre-existing unrelated/protected containers left
untouched: `gaming`, `rea`, ruby-llm-chat Postgres (`rubyllm_chat_pg`, `rubyllm-chat-pg`,
`chat-db`, `chat_app-postgres-1`), buildx builders, and the 6-week-old `bench-pg-terra` (prior
work, not this wave). No prune of any kind.

## Evidence retained (NOT deleted)
- Final grades: `results-v4/{v2_gemini_4_argon_high_agy,v2_claude_sonnet_5_5,v2_gpt_6_1_terra,v2_kimi_k3_1_pro}/grade.json`
- Wave summary: `results-v4/_release_wave_20261027/SUMMARY.md`
- Wave state/logs: `/tmp/v4-release-wave-20261027/{status.json,gates.log,boundary-modes.json,logs/}`
- Failed-attempt evidence (infra, not charged):
  - `results-v4/v2_kimi_k3_1_pro/_failed_sprints/sprint05_api.failed-auth-1793157373`
  - `results-v4/v2_gpt_6_1_terra/_failed_sprints/sprint07_reveal.failed-capacity-1793160216`
- Lifted false/infra pauses archived in-place as `PAUSED.release-wave.{resolved,archived}-*` markers
  with evidence JSON (auth / lingering-process / glob-bug / capacity).
- Injection boundary reports + `boundaries/human_injections.json` per model.

## Nothing safe to delete
After inventory, there were no disposable task-owned resources to remove: all task processes
had already exited cleanly, and every on-disk artifact is a result, transcript, grade, or
infra-failure evidence that must be preserved. Reclaimed space: 0 bytes (nothing deleted).
