# Local llama-swap Setup (NVIDIA RTX 5090)

This document covers the **NVIDIA RTX 5090 / Blackwell** llama-swap setup that runs the local model subset of this benchmark on a single workstation. The companion AMD Strix Halo (gfx1151) server setup is documented in [the main README](../README.md).

The Docker stack lives at [`~/Projects/llama-swap-docker`](../../llama-swap-docker) (separate repo). This document explains:

1. Why a custom Docker build is needed for Blackwell
2. How models are sourced (Ollama symlinks vs HuggingFace GGUFs)
3. The VRAM budget and per-model context overrides
4. The `--reasoning-format none` workaround for tool calling
5. How to run the benchmark against the local stack
6. Common pitfalls (env var leaks, broken symlinks, parser bugs)

---

## Why a custom Docker build

The official `ghcr.io/mostlygeek/llama-swap:cuda` image targets older CUDA architectures and may not include `sm_120` (Blackwell). On a 5090 you'll get either PTX JIT fallback (slow first inference) or hard `no kernel image available for execution on the device` failures.

The local Dockerfile builds llama.cpp from source against `nvidia/cuda:12.8.0-devel-ubuntu24.04` with:

```cmake
-DGGML_CUDA=ON
-DCMAKE_CUDA_ARCHITECTURES=120
```

This produces `llama-server` plus the dynamic libraries (`libggml-cuda.so`, `libggml-cpu-*.so`, `libllama.so`, `libmtmd.so`) targeted directly at sm_120. The final image then drops in the official `llama-swap` Go binary release on top of the runtime CUDA layer.

Key points if you replicate this:

- **Build with CUDA 12.8 or newer.** Earlier toolkits don't ship `sm_120` codegen support.
- **NVIDIA driver ≥ 570.** The 5090 minimum.
- **Set `LD_LIBRARY_PATH=/app` and `PATH=/app:$PATH`** in the final image. llama-swap launches `llama-server` via `exec()` which respects PATH.
- **Copy the entire `build/bin/` dir** in one go. Recent llama.cpp builds put `llama-server`, all `libggml*.so`, `libllama.so`, and `libmtmd.so` together under `build/bin/` rather than in scattered subdirs as older versions did.

---

## Model sources

The local stack pulls models from two locations:

### Ollama symlinks (`/var/lib/ollama/blobs`)

For models the user already has via `ollama pull`, a helper script (`scripts/sync-ollama-symlinks.sh`) reads the manifest, finds the layer with `mediaType: application/vnd.ollama.image.model`, and creates a human-readable symlink under `./models/` pointing into `/var/lib/ollama/blobs/sha256-<digest>`. The `docker-compose.yml` mounts both `./models` and `/var/lib/ollama/blobs` read-only, so the symlinks resolve transparently inside the container.

This avoids redownloading models that Ollama already has, while still letting llama-server read them via the human-readable filename in the config.

### HuggingFace GGUFs (`./hf/`)

For models that need a specific quant or aren't on Ollama, GGUFs are downloaded directly into `./hf/`. The `hf/` and `models/` directories are gitignored.

The current local set:

| File | Quant | Size |
|---|---|---:|
| `Qwen_Qwen3.5-35B-A3B-Q3_K_M.gguf` | Q3_K_M | 15 GB |
| `Jackrong_Qwen3.5-27B-Claude-Q3_K_M.gguf` | Q3_K_M | 12 GB |
| `google_gemma-4-26B-A4B-it-Q3_K_M.gguf` | Q3_K_M | 12 GB |
| `openai_gpt-oss-20b-Q3_K_M.gguf` | Q3_K_M | 11 GB |
| `Qwen3.5-27B-Sushi-Coder-RL-Q4_K_M.gguf` | Q4_K_M | 15 GB |

### Important: `OLLAMA_HOST` env var trap

If your shell has `OLLAMA_HOST` pointing at a remote Ollama server (e.g. the AMD bench server), `ollama list` and `ollama show` will return models from the **remote** server, not your local machine. This means the symlink helper might create symlinks to digests that don't exist locally.

The benchmark harness inherits the parent shell's environment when spawning `opencode`, so any `OLLAMA_HOST` / `OLLAMA_API_BASE` / `OLLAMA_HOME` / `OLLAMA_MODELS` variables can leak through and accidentally route inference to the wrong machine. Always launch the benchmark with these variables explicitly unset:

```bash
env -u OLLAMA_HOST -u OLLAMA_API_BASE -u OLLAMA_HOME -u OLLAMA_MODELS python scripts/run_benchmark.py ...
```

The opencode benchmark config generator already overrides the `baseURL` of the `ollama` provider entry to whatever you pass via `--local-api-base`, but unsetting the env vars is a belt-and-suspenders safety net.

---

## VRAM budget and context overrides

A 32 GB card with q8_0 KV cache fits roughly:

- **27-32B model at Q3_K_M (~12-15 GB weights)** → 17-20 GB free for KV cache → safely 128K context
- **35B-A3B MoE at Q3_K_M (~15 GB weights)** → ~17 GB free → 128K context
- **20B at Q3_K_M (~11 GB weights)** → ~21 GB free → easily 128K context (probed up to 384K stable)
- **32B Q4_K_M from Ollama (~20 GB weights)** → ~12 GB free → only 64K context safely
- **35B Q4_K_M from Ollama (~23 GB weights)** → ~9 GB free → 49K context tight

Models that **don't fit at all** on a 32 GB card and are explicitly excluded:

- `qwen3.5:122b`, `mdq100/qwen3.5-coder:122b` (81 GB)
- `llama4:scout` (67 GB sharded)
- `qwen2.5:72b` (47 GB)
- `llama3.3:70b` (42 GB)
- `deepseek-r1:70b` (42 GB)
- `qwen3-coder-next-ctx` (51 GB)
- `glm-4.7-flash:q8` (~30 GB, no KV cache headroom)

**Always set `--ctx-size` explicitly.** Never use `--ctx-size 0` on a 32 GB card — that reads the model's training context which can be 1M+ tokens for Qwen 3.5 / Llama 4 / Gemma 4 and instantly OOMs at startup.

The probed context limits per model are set in [`~/Projects/llama-swap-docker/config.yaml`](../../llama-swap-docker/config.yaml). The matching `benchmark_context_override` values in [`config/models.nvidia.json`](../config/models.nvidia.json) keep the benchmark harness honest about what context the model is actually serving.

---

## llama-server flags for Blackwell

Macros in `config.yaml`:

```yaml
macros:
  base: >-
    --host 0.0.0.0
    --gpu-layers 99
    --jinja
    --flash-attn on
    --cache-type-k q8_0
    --cache-type-v q8_0
    --parallel 1
    --ctx-size 65536
```

Per flag rationale:

| Flag | Why |
|---|---|
| `--gpu-layers 99` | Full GPU offload. Still the right way to do it; no replacement flag in current llama.cpp. |
| `--flash-attn on` | sm_120 FA kernels exist and are a big speedup. Required if you want q8 KV cache. |
| `--cache-type-k q8_0 --cache-type-v q8_0` | Halves KV memory vs f16, near-zero quality loss. Required to fit any reasonable context on 32 GB. |
| `--jinja` | Use the model's native Jinja chat template (required for tool calling). |
| `--parallel 1` | Single agentic stream. Higher values split the KV cache and hurt single-user latency. |
| `--ctx-size <explicit>` | Always per-model. The macro default is conservative; per-model lines override with the actual probed limit. |

**Dropped from the AMD config:**

- `-dio` (Vulkan/ROCm direct I/O, irrelevant on CUDA)
- `GGML_HIP_NO_VMM` (ROCm-only stability flag)
- `HSA_OVERRIDE_GFX_VERSION` (AMD-only)

**CUDA-specific env vars in `docker-compose.yml`:**

- `CUDA_VISIBLE_DEVICES=0` — pin to GPU 0
- `GGML_CUDA_FORCE_MMQ=1` — force quantized matmul kernel, generally faster on Ada/Blackwell for q4/q5/q8 GGUFs

### Per-model variants

A few models need their own macro:

- **Phi 4** family: `--cache-type-k f16 --cache-type-v f16` (q8_0 KV cache causes `ggml_abort`). Use the `base_f16kv` macro.
- **GLM 4.7 Flash**: `--flash-attn off` (uses deepseek2 arch internally which is FA-incompatible). Use the `base_no_fa` macro. Note: not in the current NVIDIA profile because the Q8 GGUF (~30 GB) leaves no KV cache headroom.

### `--reasoning-format none` for harmony / channel models

Models that emit reasoning content as separate "channels" need `--reasoning-format none` added to their command line:

- **gpt-oss:20b** — uses OpenAI's harmony format with `<|channel|>analysis|commentary|final` tags. Without `--reasoning-format none`, llama.cpp's autoparser tries to parse `<|channel|>` strings as tool calls and errors out with `Failed to parse input at pos N: <|channel|>...`. The flag tells llama-server to leave the channel content in the regular `content` field instead of trying to extract reasoning into a separate field, which lets opencode parse it normally.
- **GLM 4.7 Flash** would need this too if it were in the local set, for the same reason (`<think>` tags).

If you see error spam like `error: {'name': 'UnknownError', 'data': {'message': '"Failed to parse input at pos 755: <|channel|>write...'}}` in the benchmark heartbeats, that's the harmony parser bug — add `--reasoning-format none` to the model's command line in `config.yaml`.

---

## Running the benchmark against the local stack

### One-time setup

```bash
# 1. Pull whichever Ollama models you want to expose locally
ollama pull qwen3:32b qwen2.5-coder:32b qwen3-coder:30b   # examples

# 2. Sync symlinks from Ollama blobs into the docker-compose models/ dir
cd ~/Projects/llama-swap-docker
./scripts/sync-ollama-symlinks.sh

# 3. (Optional) Drop HF GGUFs into ./hf/ for models not on Ollama
#    - Qwen 3.5 35B A3B Q3_K_M
#    - Jackrong Qwen 3.5 27B Claude Q3_K_M
#    - Gemma 4 27B Q3_K_M
#    - GPT OSS 20B Q3_K_M
#    - bigatuna Qwen 3.5 27B Sushi Coder RL Q4_K_M

# 4. Build and start the container
docker compose up -d --build
docker compose logs -f llama-swap   # wait for "llama-swap listening on http://:8080"
```

### Verify with the warmup probe

```bash
cd /mnt/data/Projects/llm-coding-benchmark
env -u OLLAMA_HOST -u OLLAMA_API_BASE -u OLLAMA_HOME -u OLLAMA_MODELS \
  python scripts/warmup_llama_swap.py \
    --api-base http://localhost:11435 \
    --config config/models.nvidia.json \
    --output results-nvidia/llama_swap_warmup.json \
    --report docs/llama_swap_warmup.nvidia.md
```

This loads each model in turn through llama-swap, records preflight tok/s, and writes a markdown report. Models that fail to load are flagged before you waste a benchmark run on them.

### Run the full benchmark

```bash
cd /mnt/data/Projects/llm-coding-benchmark
env -u OLLAMA_HOST -u OLLAMA_API_BASE -u OLLAMA_HOME -u OLLAMA_MODELS \
  python scripts/run_benchmark.py \
    --config config/models.nvidia.json \
    --results-dir results-nvidia \
    --report docs/report.nvidia.md \
    --local-backend llama-swap \
    --local-api-base http://localhost:11435 \
    --opencode-config config/opencode.benchmark.local.json
```

The runner caches per-model results in `results-nvidia/<slug>/result.json`. To re-run a single model:

```bash
... --model qwen3_5_27b_claude --force
```

To run only the not-yet-completed models, omit `--force` — the runner skips any slug that already has a terminal result (`completed`, `completed_with_errors`, `failed`, `timeout`).

### Per-model retry one-liners

```bash
# Just the Claude-distilled Qwen
env -u OLLAMA_HOST -u OLLAMA_API_BASE python scripts/run_benchmark.py \
  --config config/models.nvidia.json --results-dir results-nvidia \
  --report docs/report.nvidia.md --local-backend llama-swap \
  --local-api-base http://localhost:11435 \
  --opencode-config config/opencode.benchmark.local.json \
  --model qwen3_5_27b_claude --force

# Just the new coder variants
env -u OLLAMA_HOST -u OLLAMA_API_BASE python scripts/run_benchmark.py \
  --config config/models.nvidia.json --results-dir results-nvidia \
  --report docs/report.nvidia.md --local-backend llama-swap \
  --local-api-base http://localhost:11435 \
  --opencode-config config/opencode.benchmark.local.json \
  --model qwen2_5_coder_32b --model qwen3_coder_30b --model qwen3_5_27b_sushi_coder --force
```

---

## Common pitfalls

### "model not found" or wrong model loaded

Almost always an env var leak. Check:

```bash
env | grep -i ollama
```

If `OLLAMA_HOST` is set, your `ollama` CLI commands talk to that remote host. Use the `env -u` prefix when running the benchmark, or unset the variables in your shell:

```bash
unset OLLAMA_HOST OLLAMA_API_BASE OLLAMA_HOME OLLAMA_MODELS
```

### Symlink points at a digest that doesn't exist

The sync helper resolves blob digests via `ollama show <model> --modelfile`, which talks to whatever Ollama server `OLLAMA_HOST` points at. If the local manifest doesn't actually have the blob, the symlink resolves to a path that doesn't exist on disk.

Verify symlinks after running the sync helper:

```bash
cd ~/Projects/llama-swap-docker/models
for f in *.gguf; do
  target=$(readlink "$f")
  if sudo test -f "$target"; then echo "ok $f"; else echo "BROKEN $f -> $target"; fi
done
```

### "no kernel image available for execution on the device"

The `llama-server` binary in the container was built without `sm_120` support. Rebuild the Docker image:

```bash
cd ~/Projects/llama-swap-docker
docker compose build --no-cache
```

### "Failed to parse input at pos N: <|channel|>..." or similar

Tool call parser bug for harmony/channel-format models. Add `--reasoning-format none` to the offending model's command in `config.yaml` and restart llama-swap. This is documented above for `gpt-oss:20b`.

### "OOM" or "failed to allocate" partway through a benchmark

Model weights + KV cache + inference scratch buffers exceeded the 32 GB budget. The probe script verifies that the model **loads** at the requested context size, but doesn't account for inference scratch buffers that get allocated on the first real request. If you see this, drop the model's `--ctx-size` by 25-50% and re-warmup.

### Two `wget` processes corrupting the same file

If you re-run a download script while the previous one is still alive, `wget -c` (continue) on both will race and corrupt the file. Always check `pgrep wget` before starting a fresh download, or use `nohup wget ... </dev/null & disown` to make sure the process survives shell exit cleanly without spawning duplicates.

### Stale `opencode` processes holding the SQLite lock

If a benchmark run is killed mid-flight, the spawned `opencode` subprocesses can survive and keep a write lock on `~/.local/share/opencode/opencode.db`, causing all subsequent runs to hang silently. The runner now auto-kills stale opencode processes before each model run, but if you see suspicious hangs, check manually:

```bash
pgrep -af opencode
pkill -f 'opencode.*run.*--agent'
```

---

## Why this is separate from the AMD profile

The AMD Strix Halo server (`192.168.0.90`) and the NVIDIA workstation are two different machines with very different VRAM budgets:

- **AMD**: 128 GB unified memory (CPU+GPU shared), runs most models at Q8_0 with 200K+ context
- **NVIDIA**: 32 GB dedicated VRAM, needs Q3_K_M / Q4_K_M and capped contexts

Sharing a single config across both would be confusing and the results wouldn't be comparable on equal terms (the smaller quant on NVIDIA inherently degrades quality vs the AMD Q8). So they live as **two parallel profiles**:

| | AMD server | NVIDIA workstation |
|---|---|---|
| Hardware | Strix Halo gfx1151, 128 GB | RTX 5090 sm_120, 32 GB |
| llama-swap host | `192.168.0.90:11435` | `localhost:11435` |
| Models config | `config/models.json` | `config/models.nvidia.json` |
| Results dir | `results/` | `results-nvidia/` |
| Report | `docs/report.md` | `docs/report.nvidia.md` |
| Warmup report | `docs/llama_swap_warmup.md` | `docs/llama_swap_warmup.nvidia.md` |
| Docker setup | `/var/opt/docker/utils/llama-swap/` (server) | `~/Projects/llama-swap-docker/` (this repo) |

The NVIDIA profile is a **strict subset** of the AMD profile — only the local models that fit in 32 GB are included, with smaller `benchmark_context_override` values. The cloud OpenRouter / Z.ai models live in the AMD `models.json` and aren't duplicated in the NVIDIA profile since they don't depend on local hardware.

---

## See also

- [`README.md`](../README.md) — main project README, AMD profile, "Adding a new model" workflow
- [`CLAUDE.md`](../CLAUDE.md) — agent guide with the same patterns
- [`docs/success_report.md`](success_report.md) — comprehensive runtime viability analysis (what code actually works)
- [`docs/report.md`](report.md) — auto-generated AMD profile results
- [`docs/report.nvidia.md`](report.nvidia.md) — auto-generated NVIDIA profile results
- [`~/Projects/llama-swap-docker`](../../llama-swap-docker) — separate repo with the actual Docker stack
