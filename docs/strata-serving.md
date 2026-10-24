# Strata Serving (RTX 5090 — Qwen3.8 Flash-Next)

Field notes on **Strata**, the native expert-offload inference engine we use to run Qwen3.8 Flash-Next locally on the RTX 5090. Everything here was learned hands-on (2026-10-22). Companion: [`docs/hardware-serving-playbook.md`](hardware-serving-playbook.md) (cross-hardware), [`docs/llama-swap.md`](llama-swap.md) (the other 5090 path).

> TL;DR: Strata runs a big MoE on a consumer GPU by keeping only the **hot experts** in VRAM and **streaming the cold ones from system RAM/SSD**. It serves an OpenAI/Anthropic API on `:8080`. We run **Qwen3.8 Flash-Next IQ3_S** (benchmark score 91.0 / Tier A) at **~176 tok/s** (full cache) / **~147 tok/s** (with a 2.5 GB desktop VRAM reserve), **256K context**. Those throughput figures are historical; the current desktop reserve is **4096 MiB** (see the validation below). Serving uses an on-demand systemd service that lazy-loads and idle-unloads.

---

## What Strata is
- A **native install** (NOT a container): the engine binary + a Python terminal/serve wrapper + a GUI app, under `~/.local/share/strata`. It's an expert-offload MoE engine — dense weights + hot experts live in VRAM, cold experts stream from pinned host RAM (and SSD via mmap).
- It serves OpenAI-compatible (`/v1/chat/completions`) + Anthropic (`/v1/messages`) on a port.

## Paths
| What | Path |
|---|---|
| CLI | `~/.local/bin/strata` (subcommands: `serve, launch, presets, profile, tune, runtime, status, models, …`) |
| Engine binary | `~/.local/share/strata/components/engine/<ver>/strata` (ours: `0.1.45.3-linux-x86_64-cuda-cuda13`) |
| Serve wrapper | `~/.local/share/strata/terminal/<ver>/strata.py serve …` |
| Data dir (weights/packs) | `/mnt/data/strata-models` (set in `~/.config/strata/settings.json`) |
| Config/presets/profiles | `~/.config/strata/` (`presets/<hash>.json`, `profiles/*.json`) |
| Qwen model (IQ3_S GGUF, 2 shards) | `/mnt/data/strata-models/models/IQ3_S/Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-0000{1,2}-of-00002.gguf` |
| Expert-offload pack | `/mnt/data/strata-models/packs/iq3_s/` (`dense.bin`, `native_experts.txt`, tokenizer, …) |

## Serving: the run-config, not the overrides profile ⚠️
Strata serves from a **run-config JSON** (`exe` + `args[]` array):
```
strata serve --config /home/akitaonrails/.local/state/strata/launch/iq3_s-128k.json --host 127.0.0.1 --port 8080
```
**Gotcha:** `~/.config/strata/profiles/launch-iq3_s-128k.json` is a *serving-overrides* profile (`{host,parallel,port}`), **NOT** a run-config — passing it to `serve --config` fails with `run config needs an args array of strings`. The real run-config is the `source_config` it points at: `~/.local/state/strata/launch/iq3_s-128k.json`. (The preset file is still *named* `iq3_s-128k` even though we now serve 256K — cosmetic; don't rename, the profile references it by path.)

The Qwen run-config `args` (the expert-offload invocation):
```
--pack  /mnt/data/strata-models/packs/iq3_s
--native   …/Qwen3.8-Flash-Next-…-IQ3_S-00001-of-00002.gguf
--ple-gguf …/Qwen3.8-Flash-Next-…-IQ3_S-00002-of-00002.gguf
--expert-profile ~/.local/share/strata/terminal/<ver>/data/expert-profile.bin
--expert-cache auto          # fills the GPU with hot experts (see VRAM section)
--prefill auto               # prompt chunking up to 8192 (auto:16384/32768 raise it)
--spec 4 --spec-min-p 0.5    # MTP speculative decode (draft 4 tokens/verify)
--mtp /mnt/data/strata-models/mtp/rt
--max-context 262144         # 256K (native max; see below)
--kv int8 --kv-resident 32768  # int8 KV, keep 32K cells/layer resident, stream the rest from RAM
--vram-elastic               # opt-in: lets us hand VRAM back to the desktop (see below)
```
`strata launch` is the guided/TUI alternative (`--preset`, `--set KEY=VALUE`, `--save-preset`, `--no-tui`). Our saved presets live as `~/.config/strata/presets/<hash>.json` + `active.json`.

## Context window
- Native max per the GGUF (`qwen4exp.context_length`) = **262144 (256K)**; Qwen's vLLM recipe + Unsloth agree.
- We run the full **262144**. Bumping 128K→256K cost **zero** speed (196→196 tok/s synthetic): the window past the 32K-resident KV is **streamed**, so VRAM is unchanged. Set `--max-context 262144` and the opencode `limit.context` to match.

## Sampling & anti-loop (thinking-confusion)
- The GGUF ships **non-greedy defaults** — `general.sampling.temp=1.0, top_p=0.95, top_k=20` (= Unsloth's Flash-Next preset). **Non-greedy is the #1 loop-avoider** (greedy → endless repetition on Qwen3-family).
- Strata separates `<think>` into a `reasoning_content` field (no bleed into `content` or tool-calls); `finish_reason=stop` is reliable. Tool-calls parse clean (qwen3_coder-style). This is why it ran 7 clean v4 sprints without looping.
- **Client-side knobs** (opencode doesn't expose sampling in provider config — these are agent-level, only needed *if* a loop ever appears): `min_p=0` (Qwen rec; llama.cpp-family wrongly defaults 0.1), `presence_penalty` 0 for coding (1.0–1.5 to break loops, but higher risks language-mixing).

## Expert cache & VRAM — the important part
- The IQ3_S expert set is **46.84 GiB total**; `--expert-cache auto` keeps the **hottest ~11,560 experts (~22 GiB) resident in VRAM** and streams the rest from RAM. Measured **98.3% cache hit** (only ~0.1% of routed experts go over PCIe) → ~176 tok/s.
- **VRAM footprint when loaded: ~29.5 GB** (≈97% of the 32 GB card): ~22 GB expert cache + ~7.6 GB fixed floor (dense weights + KV + MTP head + CUDA context + prompt buffers). **System RAM: ~52 GB** held for the streamed experts (of 91 GB).
- Strata **fills the card by design** → only ~0.3 GB free → **the desktop (Hyprland) chokes** while the model is loaded.

### `--expert-cache N` is a FLOOR, not a cap ⚠️
Setting `--expert-cache 10240` did **not** reduce VRAM — the serve layer still auto-filled to ~22 GiB, and it *dropped* hit rate (98%→94%) and speed (176→141 tok/s). Don't use it to reserve VRAM.

### `--vram-elastic` — reserving VRAM for the desktop (the right way)
Opt-in flag (NVIDIA-only; upstream Strata issue #533 — "hot VRAM resize for a shared desktop GPU"). Allocates the expert cache in **512 MiB segments** so it can give VRAM back:
```
POST http://127.0.0.1:8781/v1/vram   {"reserve_mib": 2560}   # no auth needed
# -> {"status":"ok","reserve_mib":2560,"expert_slots":10278,"expert_cache_mib":19968,"vram_free_mib":2726,...}
```
- `reserve_mib` = **free VRAM to keep on the card** (across all programs). `null` restores the startup size, `0` keeps nothing free. Freed memory comes in whole 512 MiB segments, so actual-free can land a segment short of the request.
- **Only the expert cache moves** (weights/KV/MTP/context/buffers stay) — it can't give back "everything".
- **Measured on our box:** `reserve_mib=2560` → cache 22→~20 GB (10278 vs 11514 experts) → **~2.3–2.7 GB free**, and **the reserve HOLDS steadily — before, during, AND after generation** (free stayed 2727 MiB through a full response; it does *not* reclaim mid-generation here, despite the docs' "between requests" wording). Cost: **~147 tok/s / 94% hit** (vs ~176 / 98%) — roughly **15–20% slower** for ~2.5 GB of steady desktop headroom.
- **Must be re-applied after every (re)load** (a fresh cold-start comes up at full cache). Our on-demand proxy POSTs it automatically — see below.
- Upstream caveat (open issue #1034): failure/partial-free/re-acquire semantics *while another process holds the VRAM* aren't fully nailed down. A newer Strata also adds a **static `--vram-reserve-mib`** flag (not in our 0.1.45.3).

### Alternative: offload the desktop to the iGPU
This box has an **AMD Radeon 610M** iGPU (`card0`, from the 7950X3D), unused for display; the 5090 is `card1` and drives all 3 monitors. Rendering Hyprland on the iGPU (reverse-PRIME: `env = AQ_DRM_DEVICES,/dev/dri/by-path/pci-0000:18:00.0-card:/dev/dri/by-path/pci-0000:01:00.0-card`) frees the whole 5090 — no VRAM cap, no speed cost. Trade-offs: weak 610M, NVIDIA-Wayland multi-GPU quirks, a display restart to apply. We chose the `--vram-elastic` reserve instead (less hassle, games unaffected since the model idle-unloads).

## On-demand service (lazy-load + idle-unload + auto-reserve)
Strata has **no native idle-unload**, so a small proxy wraps it:
- `~/.local/bin/qwen-strata-ondemand` — stdlib Python proxy on **:8080** (public, always up, ~no VRAM). Answers `GET /v1/models` locally *without* loading the model; on the first **chat** request it starts Strata on **:8781** (cold-start ~35 s), proxies (streaming), and after `QWEN_IDLE_TTL` idle **unloads** it (frees the whole GPU + ~52 GB RAM). After load it auto-POSTs the `QWEN_VRAM_RESERVE_MIB` reserve.
- `~/.config/systemd/user/qwen-strata.service` — runs the proxy; `enabled` + `loginctl enable-linger` (survives reboot). Env: `QWEN_IDLE_TTL=600`, `QWEN_VRAM_RESERVE_MIB=4096` in the current controller (verify the service environment separately before switching launch methods), `QWEN_UP_PORT=8781`, `QWEN_PROXY_PORT=8080`.
- `~/.local/bin/qwen-strata` — manual shim (`start|stop|restart|status`) that serves Strata **directly** on :8080 (bypasses the proxy; stop the service first — only one can own :8080).
- opencode uses it unchanged: provider `strata-5090` → `http://127.0.0.1:8080/v1`, model `qwen3.8-flash-next-iq3_s`.

**Concurrency:** both opencode instances share the one Strata (single proxy + lock; no double-load). We don't set `--parallel`, so the engine runs at its default slot count — two *simultaneous* generations may serialize; add `--parallel 2` to the run-config for true concurrent decode (splits the ~176 tok/s between them).

## Performance (Qwen3.8 Flash-Next IQ3_S, RTX 5090)
| Metric | Value |
|---|---|
| Single-stream decode (synthetic burst) | ~196 tok/s |
| Real-world decode, full cache | ~165–176 tok/s |
| Real-world decode, 2.5 GB reserve | ~140–147 tok/s |
| Expert-cache hit (full / reserved) | 98.3% / 94% |
| Cold-start (load) | ~30–35 s |
| VRAM loaded (full / reserved) | ~29.5 GB / ~27 GB |
| System RAM held | ~52 GB |
| Context | 256K (262144) |

## Gotchas (all hit this session)
- `serve --config` wants the **run-config** (`~/.local/state/strata/launch/*.json`), not the overrides **profile** (`~/.config/strata/profiles/*.json`).
- `--expert-cache N` is a **floor, not a cap** (doesn't reserve VRAM; hurts speed).
- The on-demand proxy must call `shutdown()` **off** the `serve_forever` thread or SIGTERM deadlocks (leaves `:8080` bound) — spawn a thread in the signal handler.
- When *scripting* `pkill -f <pattern>` for Strata, keep the pattern literals **out of your own command's argv** or you SIGTERM your own shell. Prefer stopping via `systemctl` or by the `:8080`/`:8781` listener PID (`ss -ltnp`).
- The shell's `ls` is aliased to `eza` (prints a header) — reading a path via `ls … | head -1` yields garbage; use a glob/`find`/explicit path.
- `--vram-elastic` reserve is **not persistent across reloads** — re-apply after each cold-start.

## See also
- [`docs/hardware-serving-playbook.md`](hardware-serving-playbook.md) · [`docs/llama-swap.md`](llama-swap.md) · [`docs/v4.2-concurrency-report.md`](v4.2-concurrency-report.md)
- Upstream: Strata issue #533 (hot VRAM resize), #1034 (vram elastic semantics), #3140 (`--vram-reserve-mib`).

## VRAM reserve for the desktop (Hyprland) — 2026-10-22 incident + fix

**Incident**: hard reset required — Strata engine (Qwen3.8-Flash-Next IQ3_S) used 32,085 of
32,607 MiB (98.4%) on the 5090, leaving Hyprland + terminal ~500 MiB. Desktop allocations
failed; even the TUI was unusable.

**Root cause (two layers)**:
1. The on-demand proxy's `set_reserve()` was fire-once with all exceptions swallowed — on cold
   start it fired before the engine's `/v1/vram` endpoint was live, silently never applied, and
   nothing retried. (Measured: 1,760 MiB free with a nominal 2,560 reserve.)
2. 2,560 MiB was too small anyway for Hyprland + browser + terminal.

**Fix (validated empirically)**:
- `QWEN_VRAM_RESERVE_MIB` raised to **4096**; `set_reserve()` now retries (~3 min backoff),
  verifies the engine's response, and logs `[vram] reserve ... confirmed` to the engine log.
- `idle_watch` re-asserts the reserve every 30 s while the engine is up (idempotent, attempt-1
  confirms) — closes any drift/rebalance gap.
- Load test at 99% GPU utilization: free VRAM held 3,629–3,888 MiB for the whole generation.
  Cost: ~150 tok/s vs ~200 (expert cache capped at ~9.7K slots vs 11.7K full; more experts
  stream over PCIe). Fair trade for a desktop that stays alive.

**Levers, in order**:
1. Raise `QWEN_VRAM_RESERVE_MIB` (ctl script env) if the desktop needs more headroom.
2. Structural: the workstation has an **AMD Raphael Radeon 610M iGPU** (18:00.0) — moving
   Hyprland to the iGPU frees the entire 5090 for compute (BIOS/display routing + Hyprland env;
   610M is fine for terminal/browsing, weak for gaming).
3. Smaller quant / lower `--kv-resident` if the model itself must shrink.
4. NVIDIA Linux has NO hard driver-level reservation for display clients — the engine-side
   elastic reserve (above) or a VRAM-holder daemon are the community-standard answers.

Engine facts: `/v1/vram` POST `{"reserve_mib": N}` → engine evicts expert-cache slots until
~N MiB free; response reports `expert_slots`, `vram_free_mib`. `--vram-elastic` is required in
the launch profile (present in `~/.local/state/strata/launch/iq3_s-128k.json`).

### Follow-up load test and retained running state

The final OpenCode load test on 2026-10-22 used the 4096 MiB reserve. Its captured
session output reported:

| Workload | Wall time | Minimum free VRAM | Peak GPU utilization | Engine-reported decode |
|---|---:|---:|---:|---:|
| One generation, up to 3,000 output tokens | 18.2 s | 4,247 MiB | 100% | 225.3 tok/s |
| Three concurrent requests, up to 2,000 tokens each | 40.4 s | 3,949 MiB | 100% | 172.8–178.5 tok/s |

All four requests succeeded. A separate 1 GiB CUDA allocation probe also succeeded.
These figures come from OpenCode session `799c4886-967f-507b-a575-6e4c6cd7e21c`,
observations at 18:45 UTC; they were not regenerated during the documentation follow-up.
Concurrent requests do not prove simultaneous engine decoding, and these short prompts
do not exercise the full 256K context. Timing differences from earlier measurements are
not a controlled performance comparison.

Reproduce the generation test with
`python3 scripts/strata_vram_loadtest.py` against the already configured local proxy.
The script samples GPU memory every two seconds and requires at least **3400 MiB** free
and successful responses. This is an empirical acceptance threshold, not a hard VRAM
reservation or proof that the desktop cannot freeze. Sampling can miss brief allocation
spikes; additional desktop applications or longer contexts can consume more memory.
The script sends inference requests and **does not unload the engine afterward**.

During the follow-up, a read-only inspection of the running proxy's environment confirmed
`QWEN_VRAM_RESERVE_MIB=4096`. A live GPU snapshot showed **4232 MiB free at 99% utilization**.
The user explicitly requested leaving the loaded engine running with these settings, so
no stop, restart, reserve mutation or additional stress request was issued. Automatic idle
unloading remains governed by the existing proxy configuration.

The uncommitted `park` addition in `strata_proxy_ctl.py` is not part of this documented
release: it uses broad process-name matching and needs exact process-ownership validation
before it can safely be recommended. Do not use blanket `pkill` commands to reclaim VRAM.

Cleanup for this documentation task: no temporary files, containers or services were
created; nothing was removed. The active engine, proxy, model files, existing test evidence
and unfinished controller edit were intentionally retained. Python source syntax and the
local documentation link were checked without loading or stopping the model.

### Local archive of uncensored Flash-Next variants

The five variants discussed on 2026-10-22 are archived under
`/mnt/gigachad/huggingface/archives/uncensored-qwen-flash-next/`. Use these local
files for future Strata trials instead of downloading the same weights again. The
archive's `manifest.json` records exact Hugging Face revisions, included files,
expected sizes and verification status. Run `python3 download.py` from that
directory to resume an incomplete download. A `verified` entry means the pinned
files are present at their published sizes; it does not mean the model has passed
an inference or coding benchmark.

| Directory | Variant archived |
|---|---|
| `alesha-iq3_s-vector/` | Original GSQ-RCO IQ3_S weights, refusal-direction control vector and vision projector |
| `sc117-iq3_s/` | SC117 abliterated GSQ-RCO IQ3_S, vision projector and draft weights |
| `rvn-iq3_s/` | RVN abliterated/uncensored Strata IQ3_S merged GGUF |
| `orcarouter-iq3_xxs/` | OrcaRouter uncensored IQ3_XXS, vision projector and draft weights |
| `coder-iq1_m/` | DatKurai uncensored Coder IQ1_M |

These are the quantizations discussed as Strata options, not every quantization
published in each upstream repository. The Alesha vector can be turned off to
recover the original model's behavior. The other four are separate checkpoints
or quants. Keep the current running vanilla Qwen setup as the measured baseline
until a variant is tested in a separate configuration.
The broader [Hugging Face archive index](HF_MODEL_ARCHIVE.md) also lists the
official Flash checkpoints and completed local-model quants.

## TeksEdge-style optimization review — 2026-10-24 (verdict: already optimized)

Prompted by the Qwen3.8-27B 82→381 tok/s report (see
`docs/qwen38-27b-inference-optimizations.md`), each technique was checked against this
setup (Qwen3.8 Flash-Next IQ3_S on the 5090):

| Technique | Status here |
|---|---|
| Speculative decoding / MTP | **Already on and tuned**: `--spec 4 --spec-min-p 0.5 --mtp`. Tuner NEVER-list shows spec ≥6 is 4–16% slower and ≤2 is 4–11% slower for flash-next — 4 is the measured sweet spot |
| Context lookup (`--lookup-chain`) | **Tested and rejected by the tuner on this machine**: 3–8.5% slower. Matches the report's own caveat (their +176 tok/s came from a 25k-token document-copy workload; chat sees little) |
| Prefix caching | **Already inherent**: measured 17k-token repeat prompt prefill 4004 ms → ~130 ms (30×) with zero config; growing-history (agentic) prompts also only pay the delta (~140–200 ms). Test: `scripts/strata_convcache_test.py` |
| `--conversation-cache-mib` (opt-in) | **Left off deliberately**: it parks whole conversations across eviction/idle — a scenario our workload doesn't hit, and it would spend VRAM against the 4096 MiB desktop reserve |

Decode speed here (~165–225 tok/s) already exceeds the report's ~133 tok/s chat figure
on the 3090 — expected, 5090 vs 3090. Nothing to change.

## Vision encoder — enabled 2026-10-24

The install was text-only ("this server was started without the vision encoder" when a
client sent an image). Enabled by hand:

- **mmproj**: reused from the NAS archive
  (`uncensored-qwen-flash-next/alesha-iq3_s-vector/mmproj-Qwen3.8-Flash-Next-BF16.gguf`) —
  sha256 `b1a82259…` matches both the archive's SHA256SUMS and Strata's pinned hash for
  ISTA-DASLab's BF16 encoder. Staged copy (archive copy preserved):
  `/mnt/data/strata-models/models/IQ3_S/mmproj-Qwen3.8-Flash-Next-BF16.gguf`.
- **Config**: `~/.local/state/strata/launch/iq3_s-128k.json` gained `--vision` in `args`
  and a `vision` section (`exe` → the component's `strata-vision`, `mmproj`, `model` →
  dense shard 1 vocab-only, `gpu: true`, `max_tokens: 1024`). Backup beside it:
  `iq3_s-128k.json.bak-pre-vision`.
- **Verified end-to-end**: encoder loads in 0.5 s, warms at 1024 image tokens in 1.7 s;
  a red-square test image was correctly answered ("Red"). VRAM with encoder resident:
  ~3.65 GB free — the 4096 MiB desktop reserve still effectively holds.
- Note: `runconfig.py` refuses `lazy_load` together with a vision section (text-only
  lazy path) — keep lazy loading off for this config.

