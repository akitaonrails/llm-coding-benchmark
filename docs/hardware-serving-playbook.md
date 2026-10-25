# Hardware Serving Playbook — B300 vs H200 vs Local (5090 / Strix Halo)

Current local hardware serving notes are maintained at [my-omarchy-config-next/docs/machine/llm-hardware-serving-playbook.md](../../my-omarchy-config-next/docs/machine/llm-hardware-serving-playbook.md). This benchmark-era comparison remains for provenance.

Cross-hardware field notes for serving open-weight coding models for this benchmark:
the hurdles, limitations, and the tricks that actually made each tier run optimally.
Four tiers, two worlds:

- **Datacenter (rented RunPod), vLLM, tensor-parallel, built for concurrency:** 4×B300 (Blackwell) and 4×H200 (Hopper).
- **Local, single-stream agentic coding:** RTX 5090 (consumer Blackwell, llama.cpp/llama-swap) and the AMD Strix Halo server (unified-memory APU, Ollama).

Companion docs: [`docs/llama-swap.md`](llama-swap.md) (the 5090 stack in depth), [`CLAUDE.md`](../CLAUDE.md) (serving policy), the v4.2 concurrency report (throughput numbers), and the campaign log [`docs/b300-4x-overnight-campaign.md`](b300-4x-overnight-campaign.md).

---

## TL;DR matrix

| | 4×B300 | 4×H200 | RTX 5090 | Strix Halo |
|---|---|---|---|---|
| Arch (SM) | Blackwell Ultra `sm_103a` | Hopper `sm_90` | consumer Blackwell `sm_120` | AMD `gfx1151` (RDNA/CDNA APU) |
| Memory | ~280–288 GB/GPU (~1.1 TB) | ~140 GB/GPU (~560 GB) | 32 GB dedicated | ≤128 GB **unified** (CPU+GPU) |
| Runtime | vLLM (TP=4) | vLLM (TP=4) | llama.cpp via llama-swap | Ollama / llama.cpp |
| Native quant | **FP4/NVFP4** + FP8 | **FP8** (no FP4) + BF16/AWQ | GGUF Q3_K_M/Q4_K_M | GGUF Q8_0 |
| Typical decode | 110–263 tok/s | 137–175 tok/s single-stream (DeepSeek/GLM FP8) | ~80–159 tok/s | slower, huge capacity |
| Perf gate | ≥100 tok/s (datacenter) | ≥100 tok/s | ~30 tok/s (consumer) | ~30 tok/s |
| Best for | trillion-param MoEs, FP4, max concurrency | FP8 flagships, stable mainstream serving, concurrency | single-user coding, small-mid models | big-context Q8 of mid models no 32 GB card can hold |
| Top gotcha | `sm_103a` JIT needs CUDA ≥12.9 + bleeding-edge vLLM | **FP4 checkpoints don't run** — must re-source FP8/BF16 | official image lacks `sm_120` → build from source | ROCm env flags; slow but fits what VRAM can't |

**The one-line rule of thumb:** B300 = maximum capability but bleeding-edge toolchain pain; H200 = slightly less memory but *mainstream and boring* (a feature); 5090 = fast for what fits, but 32 GB is the whole story; Strix Halo = the "it won't fit on the 5090" escape hatch, at the cost of speed.

---

## 1. 4×B300 (Blackwell Ultra, `sm_103a`) — maximum capability, bleeding-edge toolchain

Served ~13 models here (DeepSeek V4.1 Flash, Kimi K2, GLM 5.3, Ornith-122B, MiMo, Laguna, Nex, Step-5, Muse Spark, …), all vLLM TP=4. This is the most powerful tier and the one that fought back the hardest.

### Setup
- vLLM TP=4, `--gpu-memory-utilization 0.90`, per-model reasoning/tool-call parsers, served behind an API-key-guarded port + a **cloudflared** tunnel so the workstation's opencode runs reach it.
- CUDA 12.8 ships on the base image; **`sm_103a` JIT needs CUDA ≥12.9** (see below).
- Base weights FP8 or **NVFP4** (native Blackwell FP4 — the big win of this tier: trillion-param MoEs fit).

### Hurdles & fixes
- **The `sm_103a` JIT wall (the signature B300 problem).** FlashInfer JIT-compiles certain ops (e.g. head_dim-192 `batch_prefill`, FP4 quantization) with the *system* nvcc = CUDA 12.8, which **cannot target `compute_103a`** (sm_103 needs CUDA ≥12.9). The bundled CUDA-13 nvcc instead trips FlashInfer's cu12 **cccl header check**. **Fix:** assemble a standalone CUDA **12.9** toolkit and point `CUDA_HOME` at it:
  ```
  /root/cuda-12.9  =  nvcc 12.9.86 + cudart 12.9.79 + cccl 12.9.27   (lib64 -> lib symlink)
  export CUDA_HOME=/root/cuda-12.9
  ```
  This is the *general* fix for any `sm_103`/head_dim-192 MSA model on this pod (Step-5, MiniMax M3-class, etc.).
- **NVFP4 `modelopt` FP4 op needs math libs 12.9 lacks.** Muse Spark's `fp4_quantization_103` wants `cublasLt`/`curand`, which the hand-assembled `/root/cuda-12.9` doesn't ship. **Fix:** a *merged* toolkit `/root/muse_cuda` = **12.9 nvcc (device targeting) + 12.8 math libs (host-side)**. cuBLAS is host-side and does not affect device targeting, so mixing is safe — the 12.9 nvcc still emits `compute_103a`.
- **vLLM arch gaps → isolated nightly.** vLLM 0.32 didn't register newer archs: `step5_vl` (needed PR #61727) and `muse_spark` (needed PR #61879, served from the *draft* branch — no nightly had it). **Fix:** keep 0.32 for the live campaign, build the nightly in an **isolated venv** (`/root/vllm-next-venv`, uv + py3.12, `--extra-index-url https://wheels.vllm.ai/nightly`) so the upgrade never touches the running campaign.
- **MiniMax M3 crashed on 0.32** at CUDA-graph/MSA warmup — the bundled `fmha_sm100` CUTLASS references CUDA-13 symbols (`cudaFuncAttributeSharedMemoryMode`, `AllowOversizedSharedMemory`) absent in 0.32's toolchain (sm100 FMHA JIT mismatch on lightning-attention). It was infra-blocked on 0.32 regardless and needed the Step-5 nightly.
- **The flashinfer NVFP4 one-time autotune killed the pod.** On first NVFP4 serve, FlashInfer runs a ~35-min autotune that **pins all CPU cores**, which starved `sshd` and made the pod unreachable (this is what ended the B300 run). **Tip:** expect it, run the first serve under `nice`/`taskset` to leave a core for sshd, warm the model *before* a ramp, and keep a watchdog. (`fused_moe_trtllm_sm100` also JITs for several minutes on first load — normal, not an error.)
- **FP8 vs NVFP4 vs INT4 sizing.** Even ~1.1 TB fills up: Kimi K2 FP8 Instruct (1029 GB) does **not** leave KV headroom at TP=4, so it ran as **INT4 Thinking** (594 GB) — a hardware-driven variant choice (annotate it). Prefer NVFP4 when a checkpoint exists; FP8 otherwise.
- **Under-gate single-stream on huge models → MTP speculative decode.** Step-5 served at only 74 tok/s single-stream (below the ≥100 datacenter gate) despite 623 tok/s aggregate — i.e. a latency, not scaling, problem. **Fix:** MTP speculative decoding (Step5MTP head, n=2) → **2.24× → 166 tok/s**, clears the gate with 73.7% acceptance.

### Tips
- **KV is almost never the B300 bottleneck.** DeepSeek's MLA gives a ~25 M-token KV pool; under a full concurrency ramp KV-cache utilization peaked at **0.39%**. The limiter is prefill scheduling / the p99 TTFT queueing tail, not memory.
- Typical validated decode (TP=4): DeepSeek V4.1 Flash **174.8**, Ornith-122B **244**, Laguna **263**, Nex **184**, MiMo **167**, Step-5 **166** (MTP), Muse **130.8**, Kimi/GLM **110** tok/s.
- Datacenter perf gate is **≥100 tok/s**, not the consumer 30.

---

## 2. 4×H200 (Hopper, `sm_90`) — mainstream and boring, which is the point

The fallback when B300s weren't available. ~140 GB/GPU (~560 GB), CUDA 12.8, driver 595, 96 vCPU, 2 TB RAM/disk.

### Setup
- vLLM **stable** TP=4 on CUDA 12.8 (`sm_90` is first-class). **No PR-branch build, no CUDA-12.9 hand-assembly, no FP4 autotune** — a plain-FP8 model (GLM 5.3 Flash) served clean in one shot. But "mainstream" is **not** "plug-and-play" for every model: see the hurdles below.

### The FP4→FP8 re-sourcing rule (the headline H200 constraint)
- **No native FP4.** FP4/NVFP4 is a Blackwell feature; Hopper has no FP4 tensor cores. A model whose only datacenter checkpoint is **NVFP4 (e.g. GLM 5.3 Flash's `RedHatAI/...-NVFP4`) must be re-sourced** as **FP8** (Hopper-native, preferred — used `zai-org/GLM-5.3-Flash`), **BF16** (fits, ~2× NVFP4 VRAM), or AWQ/GPTQ int4. Both concurrency models ran **FP8** on the H200 → clean matched-precision comparison, only model size varies.
- ~140 GB/GPU vs ~288 on B300: still serves 510 GB-class FP8 MoEs at TP=4, but less KV headroom — which is exactly what bit GLM (KV-bound at 97% util vs DeepSeek's MLA at 14%).

### Hurdles that *do* still bite on Hopper (DeepSeek V4.1 Flash FP8)
Hopper killed the Blackwell *FP4* pain, but the FP8 **DeepGEMM + FlashInfer** JIT path still needed a stacked fix chain to serve DeepSeek V4.1 Flash — plan for it:
- **`pip install vllm` resolver-thrashed** (hundreds of backtracking dirs, zero progress in 30 min). **Fix: use `uv`** — vLLM 0.32 installed cleanly in minutes.
- **cu13 wheel JIT chain** (the vLLM wheel bundles a CUDA-13 toolchain its DeepGEMM/FlashInfer JIT invokes), four persistent fixes:
  1. NVRTC `libnvrtc-builtins.so.13.0 not found` → `LD_LIBRARY_PATH=<cu13>/lib`.
  2. DeepGEMM asserts **nvcc ≥ 12.9** but system nvcc is 12.8 → point `DG_JIT_NVCC_COMPILER`/PATH at the wheel's **bundled cu13 nvcc 13.4**.
  3. cccl **"compiler/toolkit headers incompatible"** (nvcc 13.4 vs cudart headers 13.0) → an **in-place `nvcc` shim** that injects `-DCCCL_DISABLE_CTK_COMPATIBILITY_CHECK` (the header's own sanctioned bypass; covers both DeepGEMM and FlashInfer absolute-path calls).
  4. FlashInfer link `cannot find -lcudart` (hard-codes `lib64`, no unversioned `.so`) → symlink `lib64→lib`, `libcudart.so→.so.13`, `stubs/libcuda.so→` the system driver.
  (This is the *same class* of fix the B300 DeepSeek serve needed — DeepGEMM/FlashInfer JIT is finicky about the CUDA toolchain on both Hopper and Blackwell.)
- **Orphaned TP workers survive `pkill -f 'vllm serve'`** and keep holding ~131 GiB/GPU, OOMing the *next* model on swap. **Fix:** kill by PID from `nvidia-smi --query-compute-apps` before serving the next model (verify VRAM drops to a few MiB first).
- **`hf download --exclude "a" "b"`** parses the 2nd pattern as a positional filename → use repeated `--exclude` flags.

### Tips
- Keep the serve config **identical to the B300 one** (same TP=4, same `--max-model-len`, same parsers) so cross-pod numbers isolate the hardware.
- Per-model throughput and the concurrency ramp live in the **v4.2 concurrency report**, not here.
- For an odd GPU count (e.g. 3 GPUs) you'd need `--pipeline-parallel-size` since many models' head counts aren't divisible by 3; a 4-GPU box avoids that entirely (TP=4 just works).

---

## 3. RTX 5090 (consumer Blackwell `sm_120`, 32 GB) — fast for what fits

Single-workstation local stack via **llama-swap + llama.cpp** (GGUF). Full depth in [`docs/llama-swap.md`](llama-swap.md); the essentials:

### Setup
- **Build llama.cpp from source** against `nvidia/cuda:12.8.0-devel` with `-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=120`. The official `llama-swap:cuda` image lacks `sm_120` → you get slow PTX JIT fallback or a hard `no kernel image available for execution on the device`. Driver **≥570**.
- Serve flags that matter: `--gpu-layers 99`, `--flash-attn on` (sm_120 FA kernels exist and are a big speedup + required for q8 KV), `--cache-type-k q8_0 --cache-type-v q8_0` (halves KV, near-zero quality loss), `--jinja` (native template, needed for tool calls), `--parallel 1` (single agentic stream).

### Limitations
- **32 GB is the entire story.** Realistic fits (with q8_0 KV): a 27–35B model at **Q3_K_M** (~12–15 GB weights) → ~128K context; a 32B **Q4_K_M** → only ~64K. Models like qwen3.5:122b, llama4:scout, qwen2.5:72b, 70B-class simply **don't fit** at any useful quant.
- **Never `--ctx-size 0`** — it reads the model's training context (1M+ for Qwen3.5/Llama4/Gemma4) and OOMs at startup. Always set it explicitly per model.
- First real request allocates inference scratch on top of weights+KV — if it OOMs mid-run, drop `--ctx-size` 25–50% and re-warm.

### Model-specific tricks
- **Harmony/channel models** (gpt-oss:20b) and **`<think>` models** (GLM): add `--reasoning-format none` or llama.cpp mis-parses `<|channel|>`/`<think>` as tool calls and errors `Failed to parse input at pos N`.
- **Phi 4**: q8_0 KV causes `ggml_abort` → use **f16 KV**.
- **GLM 4.7 Flash**: `--flash-attn off` (uses deepseek2 arch internally, FA-incompatible).
- **Qwen 3.8-27B is hybrid SSM/Mamba** — the tuned (April) llama.cpp build can't load it (`missing tensor blk.N.ssm_conv1d.weight`); use a **fresh `ollama/ollama:latest`** container and import the existing HF GGUF via a `FROM /hf/<file>.gguf` Modelfile (no re-download).
- Gemma 4 needs llama.cpp **b8665+** (PR #21418) for tool calling; Llama 4 Scout has no pythonic parser (incompatible).

### The classic footgun
- **`OLLAMA_HOST` env leak.** If your shell points `OLLAMA_HOST` at a remote server, `ollama`/symlink helpers talk to the *wrong* machine and inference silently routes elsewhere. Always launch with `env -u OLLAMA_HOST -u OLLAMA_API_BASE -u OLLAMA_HOME -u OLLAMA_MODELS …`.
- Typical local decode ~80–159 tok/s (vs 130+ for the same class on a B300).

---

## 4. AMD Strix Halo (`gfx1151`, ≤128 GB unified) — the capacity escape hatch

The AMD server (`192.168.0.90:11435`, Ollama backend, `config/models.json` / `results/`). Different trade-off from everything above: **slow but huge**.

### Why it exists
- **128 GB unified memory** (CPU+GPU shared) runs most models at **Q8_0 with 200K+ context** — things no 32 GB discrete card can hold. Concretely, Qwen 3.8-27B **completed the benchmark on Strix Halo where the 5090 couldn't** (needed 128K+ context the 32 GB card couldn't fit), scoring **80.0 / Tier B** (a local-hardware milestone, but short of Tier A).
- **But it's slow:** the dense 27B tops out at **~12–15 tok/s** on the Strix (measured Q4 12.6, Q8 7.7) — below even the consumer 30 tok/s mark. Strix wins on *capacity* (what fits), never on speed.

### Limitations & tricks
- ROCm, not CUDA: the AMD serve config carries `HSA_OVERRIDE_GFX_VERSION`, `GGML_HIP_NO_VMM` (ROCm stability), and `-dio` (Vulkan/ROCm direct I/O) — all of which are **dropped** on the NVIDIA profile.
- Unified memory ≠ free lunch: it's **bandwidth-bound**, so decode is markedly slower than discrete VRAM. It wins on *what fits*, not on speed.
- Even 128 GB has a ceiling: MiniMax M3 (230B+ total MoE) doesn't run at usable quality at any quant — even a 1-bit ~128 GB quant would consume all unified memory with nothing left for KV/scratch/OS. Treat such models as cloud-only.
- Kept as a **parallel profile** to the 5090 (strict-subset NVIDIA config) precisely because a Q8 Strix result and a Q3_K_M 5090 result aren't comparable on equal terms.

---

## Cross-cutting lessons (apply on every tier)

- **Pick the quant by arch, not by habit.** FP4/NVFP4 → Blackwell only (B300; and consumer Blackwell via vendor kernels, *not* the GGUF path). FP8 → Hopper and up (H200, B300). GGUF Q3/Q4 → anywhere via llama.cpp. A model's "best" checkpoint is worthless if the target SM can't execute its format — re-source it (NVFP4→FP8 for Hopper was the headline H200 hurdle).
- **KV/context budgeting is the real capacity question.** MLA models (DeepSeek) have tiny KV and scale to high concurrency; GQA models need more. On a 32 GB card q8_0 KV is mandatory; on datacenter cards KV is rarely the limit — prefill scheduling / TTFT tail is.
- **RunPod remote-exec:** the SSH proxy **refuses non-PTY exec** — interactive PTY only, so multi-line scripts must be **base64-encoded and decoded on the pod**, and long work backgrounded with `setsid … </dev/null` then polled via a marker-wrapped helper. A dead backing pod shows as `Permission denied (publickey)` from the proxy even when your key is fine.
- **HuggingFace gating:** repo **metadata visibility ≠ download access**. Always test a real *file fetch* with your token before committing a plan — a gated repo can show a public model card and still 401/403 the weights.
- **Secrets hygiene:** the API key lives in a file read into `VLLM_API_KEY` **env only** — never in argv, never echoed (a `/root/.llmkey` value once leaked into a transcript; rotate + keep pods ephemeral). Never print tokens/keys/SSH material; redact to prefix+length.
- **Disk discipline during runs:** `mv` aside, don't `rm`, while a run is live; batch cleanup at the end. Stage/download the *next* model while the current one serves to keep an expensive pod busy.
- **Perf gates differ by tier:** datacenter ≥100 tok/s (tune TP/quant/spec-decode to reach it — MTP got Step-5 from 74→166); consumer ~30 tok/s is acceptable.

---

## See also
- [`docs/llama-swap.md`](llama-swap.md) — the 5090 llama-swap stack in full (build, model sourcing, VRAM budget, every pitfall)
- [`docs/b300-4x-overnight-campaign.md`](b300-4x-overnight-campaign.md) — the running campaign log these notes were distilled from (per-model serve details + the machine-change section)
- [`CLAUDE.md`](../CLAUDE.md) — serving policy, shield discipline, open-weight benchmark policy
- the v4.2 concurrency report — the throughput/comfortable-N numbers (B300 vs H200, DeepSeek vs GLM)
