# Open-weight serving capacity — consumer HW and big-iron planning

_Written 2026-10-19. Reference for where each class of open-weight model can actually run, at what
speed, and what it would take to serve the very large (trillion-param) models. Measurements are
this project's; vendor figures are cited inline. Supersedes nothing — it's a planning companion to
the B300 batch (`docs/b300-cost-quality-comparison.md`) and the serving optimizations doc._

## TL;DR

- **Decode speed on local HW is memory-bandwidth-bound**, not compute-bound. Approx ceiling:
  `tok/s ≈ memory_bandwidth ÷ bytes_resident_per_token`.
- **Dense 27B on the Strix Halo tops out at ~12–15 tok/s** (measured: Q4 12.6, Q8 7.7) — the
  256 GB/s LPDDR5X wall. No optimization clears a 30 tok/s bar; it's physics.
- **The same 27B on an RTX 5090 would do ~100 tok/s** (1.8 TB/s GDDR7) — if it fits with context.
- **MoE models (Qwen3.8-Flash-Next, GLM, DeepSeek) run far faster per their size** because only the
  active experts stream per token — but only with an engine that does **expert offloading**
  (Strata, or llama.cpp `-ot`), otherwise the whole model must be resident.
- **4× B300 (~1.1 TB) runs essentially every frontier open model, including true 1-trillion-param
  ones, at FP8 or NVFP4.** Only full BF16 of a 1 T model (~2 TB) needs 8×.

## Hardware envelopes (measured)

| Box | GPU mem | System RAM | Bandwidth | Notes |
|---|---:|---:|---:|---|
| RTX 5090 (workstation) | 32 GB GDDR7 | 91 GB | ~1.8 TB/s | driver 615; fast but small VRAM |
| Strix Halo (Ryzen AI Max 395) | 64 GB VRAM (UMA) + ~31 GB GTT | 61 GB | ~256 GB/s | unified LPDDR5X shared CPU/GPU; GPU addresses ~64 GB fast / ~95 GB w/ GTT |
| B300 (single) | 275 GB usable (288 GB HBM3e) | — | ~8 TB/s | NVFP4-native (Blackwell) |
| 4× B300 node | ~1.1 TB | — | — | needs tensor/expert parallelism, one NVLink node |

## Local decode-speed ceilings (bandwidth ÷ model size)

| Model / quant | Resident | Strix (256 GB/s) | 5090 (1.8 TB/s) | Measured |
|---|---:|---:|---:|---|
| 27B dense Q4_K_M | 17 GB | ~15 tok/s | ~105 tok/s | Strix 12.6 |
| 27B dense Q8_0 | 29 GB | ~9 tok/s | n/a (no ctx room) | Strix 7.7 |
| Flash-Next IQ3_S (125B MoE, expert-offload) | active set only | ~? (testing) | ~50+ (vendor: ~53 on a 12 GB 5070) | pending |

**The 30 tok/s practicality gate** (adopted 2026-10-19): only benchmark configs that clear ~30
decoded tok/s — slower than that isn't usable for interactive local dev. Consequence: **dense 27Bs
are skipped on the Strix** (bandwidth wall), **pass on the 5090**, and **MoE-via-Strata** is the way
to run the big models fast on either box.

## Strata (expert-offload engine)

[github.com/Niko1221/Strata](https://github.com/Niko1221/Strata) — inference engine purpose-built to
run **Qwen3.8-Flash-Next (125B MoE)** on consumer HW. MoE has 24,576 experts, 10 fire per token;
hot experts in VRAM, rest in RAM, index on SSD → you don't need the whole 80–90 GB resident. Adds
speculative decoding (1.6–1.8×). Self-contained AppImages: **dedicated `linux-amd-strixhalo`** and
`nvidia-cuda12/13` builds; needs ≥32 GB combined RAM+VRAM + ~80 GB disk. Serves OpenAI API on
`:8080`. Variants include IQ2_XS, IQ3_XXS, **IQ3_S**, Q2_0, Q8_0. **Confirmed runnable on both the
5090 and the Strix.** Caveat: IQ3_S is ~3-bit — below the 27Bs' Q4 and far below B300 NVFP4, so a
score is quant-penalized vs the datacenter result, but it's the realistic way to run a 125B MoE
locally.

## Consumer-HW fit matrix

| Model | Size | 5090 (32 GB + 91 GB) | Strix (64 GB + 61 GB) | Engine |
|---|---|---|---|---|
| Qwen/Swift/ThinkingCap 27B Q4 | 17 GB | ✅ fast (~100 tok/s), fits 128K w/ q8 KV | ✅ but slow (~12) | ollama |
| 27B Q8 | 29 GB | ❌ no context room | ✅ slow (~8) | ollama |
| Qwen3.8 Flash-Next IQ3_S | ~40–70 GB (MoE) | ✅ via Strata | ✅ via Strata | Strata |
| **DeepSeek V4.1 Flash** | see below | borderline (1-bit only) | borderline (1-bit only) | llama.cpp |

### DeepSeek V4.1 Flash — the awkward one
552 B backbone + 196 B **Engram** = ~748 B MoE ([unsloth guide](https://unsloth.ai/docs/models/deepseek-v4.1-flash)).
Key design: the **Engram table (110 GB at IQ1_S) stays on SSD via mmap**, so only the **~122 GB of
non-Engram weights** need RAM+VRAM. GGUF quants:
UD-IQ1_S **233 GB** · IQ1_M 250 · IQ2_XXS 300 · IQ3_XXS 395 · Q4 500 · Q8 508.
- unsloth: UD-IQ1_S "works on 128 GB setups." Our boxes are **123 GB (5090) / 125 GB (Strix)**
  combined — right at the 122.4 GB line, with **~0 headroom** for 128K context → likely SSD spill →
  slow, and it's **1-bit** (quality-degraded). Verdict: borderline-loadable, not a clean run.
- **Single B300 (275 GB)** fits only **IQ1_S/IQ1_M** (1-bit). A quality-representative quant
  (IQ3/Q4 = 395–500 GB) needs a **2–4× B300 / multi-GPU node**.

## Big-iron: 4× B300 for trillion-param models

4× B300 ≈ **1.1 TB** VRAM. Weight memory by precision: BF16 2 B/param, FP8 1 B/param, NVFP4 0.5 B/param.

| Model | Params | BF16 | FP8 | NVFP4 | Fits 4× B300 (1.1 TB)? |
|---|---|---:|---:|---:|---|
| Qwen3.5 397B | 397 B | 0.8 TB | 0.4 TB | 0.2 TB | ✅ even BF16 |
| GLM 5.3 full* | ~355–700 B* | 0.7–1.4 TB | 0.35–0.7 TB | 0.18–0.35 TB | ✅ FP8/FP4 (BF16 if ≤~500 B) |
| DeepSeek V3/V4 | 671–748 B | ~1.4 TB | ~0.7 TB | ~0.36 TB | ✅ FP8/FP4 · ❌ BF16 |
| **Kimi K2 (1 T)** | 1 T | ~2.0 TB | ~1.0 TB | ~0.5 TB | ✅ NVFP4 (comfortable), FP8 (tight) · ❌ BF16 |

Add KV cache + activations + framework overhead. At **NVFP4** a 1 T model is ~500 GB, leaving
~600 GB for KV → very large context. At FP8 (~1 TB weights) only ~100 GB headroom → limited
context/concurrency.

**Verdict: 4× B300 is enough for every current frontier open model — including true 1 T ones — at
FP8 or (better) NVFP4**, which is how they're meant to be served. The only miss is full BF16 of a
1 T model (~2 TB → 8× B300), which nobody does in production. NVFP4 is the Blackwell-native sweet
spot. Needs `--tensor-parallel-size 4` on one NVLink node; ~4× the hourly (~$36/hr).

\*GLM 5.3's largest full-model size is unconfirmed here (the B300 batch ran "GLM 5.3 **Flash**" =
320B-A18B). If it's in the GLM-4.x/5.x ~355–700 B class, 4× handles it at FP8/FP4. Confirm the spec
before provisioning.

## RunPod operational gotcha (learned 2026-10-19)

**Stopping and restarting the same pod WIPES `/root`** — it's an ephemeral container overlay, not a
persistent volume. After a restart the B300 came back as a fresh 700 GB overlay (16 MB used): **no
vLLM, no CUDA 12.9 toolkit, no models, no cloudflared** — the entire batch environment (incl. the
CUDA-12 loader fix and flashinfer) was gone. For repeat large-model work, either:
1. put models + venvs on a **persistent network volume** (`/workspace`) that survives stop/restart, or
2. budget full rebuild time each session (toolkit + serving stack + model download).

Exec on the RunPod SSH proxy needs a PTY — use `scripts/pod_exec.py` (pexpect-driven), not raw
`ssh pod 'cmd'`; refresh `/tmp/runpod.txt` with the new per-restart session id.
