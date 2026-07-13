# Grok CLI Integration

This document covers the **Grok Build CLI** (`grok` / `agent` on PATH) as a third benchmark runner alongside `opencode run` and `codex exec`. It is used for models that are only available through xAI's Grok CLI (e.g. `grok-composer-2.5-fast`), not via OpenRouter.

## Why Grok CLI?

Some Grok coding models are exposed exclusively through the Grok Build headless runner (`grok -p` / `grok --prompt-file`). They cannot be benchmarked through opencode's OpenRouter provider path. The harness mirrors the Codex integration pattern: opt-in via `"runner_type": "grok"` in `config/models.json`, dispatch from `run_model()` in `scripts/benchmark/runner.py`.

## Installation

The `grok` binary must be on PATH (also resolves `agent`, which is the same CLI on some installs). Auth via `grok login` (grok.com session) or `XAI_API_KEY`.

```bash
grok models   # verify target model is listed
```

## How It's Wired

```json
{
  "slug": "grok_composer_2_5_fast",
  "id": "grok-composer-2.5-fast",
  "label": "Grok Composer 2.5 Fast",
  "provider": "grok",
  "runner_type": "grok",
  "skip_by_default": true,
  "enable_followup": true,
  "grok_max_turns": 200,
  "grok_followup_max_turns": 100,
  "grok_followup_no_progress_minutes": 30,
  "grok_followup_resume": false
}
```

Run:

```bash
python scripts/run_benchmark.py --model grok_composer_2_5_fast
python scripts/run_benchmark.py --model grok_composer_2_5_fast --phase2-only
```

Phase 2 re-run requires `results/<slug>/phase1-result.json` from a prior full run.

## Hurdles and Fixes

### 1. `--resume` hangs silently on phase 2

`grok --resume <sessionId>` with `--output-format streaming-json` can run for many minutes with **zero stdout/stderr** while loading a large session context. The default 6-minute no-progress timeout kills the run before Docker validation starts.

**Fix:** Set `"grok_followup_resume": false` on the model entry. Phase 2 starts a fresh Grok session; `build_followup_prompt()` appends the standard fallback paragraph instructing the agent to inspect the existing project in the workspace.

### 2. Docker/build runs exceed the default no-progress window

Phase 2 validation (`docker build`, `docker compose up`) may produce no streaming-json events for 10+ minutes while shell children are active.

**Fixes:**
- Per-model `"grok_followup_no_progress_minutes": 30` extends the stall detector for phase 2 only.
- `stream_grok_process()` treats active child processes (`pgrep -P <grok-pid>`) as progress during phase 2.

### 3. Thought-token logging fills disk

Grok's `streaming-json` format emits **one JSON line per thought token**. Persisting those lines to `followup-opencode-output.ndjson` can grow logs to gigabytes on long validation runs.

**Fix:** The runner writes only `text`, `end`, and `error` events to the ndjson log. Thought events still reset the activity clock but are not persisted.

### 4. Same artifact paths as opencode/codex

Grok runs reuse the existing per-slug layout (`opencode-output.ndjson`, `phase1-result.json`, `phase2-result.json`, `result.json`) so `load_results()` / `build_report()` work unchanged. Session IDs are stored in `opencode_session_id` for cross-runner compatibility.

## Model config fields

| Field | Purpose |
|---|---|
| `grok_max_turns` | `--max-turns` for phase 1 |
| `grok_followup_max_turns` | `--max-turns` for phase 2 |
| `grok_followup_no_progress_minutes` | Phase-2-only stall timeout override |
| `grok_followup_resume` | When `false`, phase 2 omits `--resume` and uses a fresh session |

## Files

```
scripts/benchmark/grok_runner.py   build_grok_command, stream_grok_process, run_grok_phase
scripts/benchmark/runner.py        runner_type=grok dispatch; --phase2-only support
scripts/run_benchmark.py           grok binary preflight; --phase2-only CLI flag
config/models.json                 grok_composer_2_5_fast entry
```