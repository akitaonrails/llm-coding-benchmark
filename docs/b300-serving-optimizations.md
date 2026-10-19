# B300 open-weight serving — optimizations, and why the defaults are too slow

_Generated 2026-10-19. Evidence: `docs/runpod-b300-openweights-runbook.md`,
`results-v4/_b300_campaign/tuning/`, `results-v4/_b300_campaign/migration-20261017/`,
`config/b300_campaign.json`, `scripts/b300_*.py`._

The headline: **out-of-the-box, these models crawl.** GLM 5.3 Flash on the stock, "it serves
and passes tool calls" configuration decoded at **10.35 tok/s**. The exact same checkpoint,
context length, and KV settings — with the compile/graph defaults turned back on and latency
mode selected — decoded at **141.40 tok/s**. That is a **13.7× speedup from configuration alone**,
no weight or precision change. Every model in this batch needed deliberate tuning to clear the
100 tok/s admission gate; none arrived fast.

All decode numbers below are warm single-stream, 256-output-token probes (reasoning tokens
counted), the admission measurement — not benchmark quality scores and not a promise of the
same rate at full 128K context.

---

## 0. TL;DR — the optimization checklist that mattered

1. **Install a CUDA toolkit that can target the GPU.** Stock image ships CUDA 12.8, whose `nvcc`
   **cannot compile `compute_103a`** (B300 = sm_103). Install CUDA 12.9 or the kernels never build.
2. **Never run `--enforce-eager`.** It disables `torch.compile` + CUDA graphs → ~10 tok/s at 10%
   GPU utilization. Removing it is the single biggest win (13.7× on GLM).
3. **`--performance-mode interactivity`** — optimize for single-stream latency, not aggregate
   throughput (the benchmark runs one serial agent).
4. **Keep FP8 KV cache, prefix caching, chunked prefill on** — and verify prefix reuse with the
   Prometheus counters, don't assume it from TTFT.
5. **Use the right per-model tool/reasoning parser** or tool calls silently break.
6. **Enable native speculative decoding (MTP / DFlash)** where the checkpoint ships a draft head.
7. **Fix the runtime loader / use the model's required vLLM version** (397B flashinfer, Nemotron).
8. **Serve NVFP4 on vLLM** — llama.cpp / ollama can't load the Blackwell FP4 MoE checkpoints.

---

## 1. The defaults are slow — the GLM 5.3 Flash proof

Same B300, same `RedHatAI/GLM-5.3-Flash-NVFP4` checkpoint, same 128K context, same FP8 KV cache,
same fixed 3,473-token prompt. Only the compile/mode flags changed:

| Configuration | Decode tok/s | GPU util | Notes |
|---|---:|---:|---|
| `--enforce-eager` (baseline) | **10.35** | ~10% | torch.compile + CUDA graphs OFF, MTP off, power 209 W / 1100 W |
| `--performance-mode interactivity` (compiled) | **141.40** | — | full + piecewise CUDA graphs captured (1.03 GiB), JIT autotune done |

**13.7× faster, zero quality/precision change.** The eager baseline already had prefix caching,
FP8 KV, FlashInfer sparse MLA and autotuned TRT-LLM NVFP4 MoE kernels — so the gain is **almost
entirely torch.compile + CUDA graphs**, which `--enforce-eager` had switched off. Utilization at
10% GPU / 4% memory-controller / 209 W of 1100 W is the tell: the default was leaving ~90% of the
card idle on the critical path.

Confirmed at long context too: at **11,427 input tokens**, decode held **136.6–143.1 tok/s**, cold
TTFT 4.29 s dropping to 0.63 s on repeat, with Prometheus counters showing **exactly 8,576 prefix
tokens reused** per repeat (0 cold) — real prefix-cache reuse, not a TTFT artifact.

> Caveat kept from the runbook: the 13.7× is a short synthetic-decode figure; it does not guarantee
> the same end-to-end benchmark speedup or the same rate at full 128K context. It is, however, the
> difference between an unusable server and a usable one.

---

## 2. CUDA toolchain — the prerequisite nobody mentions

- **Stock RunPod B300 image = CUDA 12.8.** Its `nvcc` cannot compile `compute_103a` (B300 is
  Blackwell **sm_103**). Result: JIT kernel builds fail and NVFP4 paths don't come up.
- **Fix:** install CUDA 12.9 toolkit (`cuda_12.9.0_575.51.03_linux.run --silent --toolkit`),
  symlink `/usr/local/cuda → cuda-12.9`.
- **397B runtime-loader fix:** flashinfer's JIT NVFP4-MoE kernel (`fp4_quantization_*.so`) could
  not resolve **`libcudart.so.12`** (5 `.so` deps missing) → engine-init crash that looked like OOM
  but wasn't. `scripts/b300_repair_cuda12_loader.py` writes `/etc/ld.so.conf.d/b300-cuda12-runtime.conf`
  = `/usr/local/cuda-12.9/lib64`, runs `ldconfig`, verifies `ctypes.CDLL('libcudart.so.12')`. After
  the fix, the 397B served native NVFP4 at 143.9 tok/s. **Classified infra, not model quality.**
- **Nemotron 3.5 Super VL** required its own stack entirely: **CUDA 13.0 + a separate
  `vllm-0.32` venv** (`/root/venv-nemotron032`), because its official card pins vLLM 0.32 /
  nightly. Served at 207 tok/s once on the right runtime.

---

## 3. Per-model serving arguments (the accepted configs)

Common baseline for every model: `--max-model-len 131072 --enable-auto-tool-choice
--enable-prefix-caching --enable-chunked-prefill --performance-mode interactivity
--gpu-memory-utilization 0.90–0.95`. Deltas that mattered:

| Model | Quant | KV | Spec-decode | Tool / reasoning parser | Other |
|---|---|---|---|---|---|
| GLM 5.3 Flash | NVFP4 | fp8 | — | glm47 / glm47 | gpu-util 0.92 |
| Qwen3.8 Flash-Next | **modelopt** NVFP4 | — | — | qwen3_coder / qwen3 | |
| Qwen3.5 397B | **modelopt** NVFP4 | fp8 | — | qwen3_coder / qwen3 | gpu-util 0.95, `--language-model-only` |
| Qwen 3.8 27B | — | — | **MTP ×3** | qwen3_coder / qwen3 | `--language-model-only` |
| Swift 1.5 27B | bf16 | — | **MTP ×3** | qwen3_coder / qwen3 | `--language-model-only` |
| ThinkingCap 3.8 27B | bf16 | — | **MTP ×3, probabilistic draft** | qwen3_xml / qwen3 | `--language-model-only` |
| Muse Glimmer 30B | bf16 | — | **DFlash ×15** (draft checkpoint) | muse_glimmer / muse_glimmer | `--generation-config auto` |
| Ornith 1.5 35B | bf16 | — | — (head exists, acceptance unproven) | qwen3_xml / qwen3 | preserve modified template |
| Nemotron 3.5 Super VL | NVFP4 | fp8 | — | qwen3_coder / **nemotron_v3** | CUDA 13 + vllm-0.32, `--trust-remote-code` |
| DeepSeek V4 Flash | — | — | — | deepseek_v4 / deepseek_v4 | `--tokenizer-mode deepseek_v4 --trust-remote-code` |
| GLM 4.7 Flash | bf16 | — | — | glm47 / glm45 | |
| Command A Plus | W4A4 | — | — | cohere_command4 / cohere_command4 | single-GPU W4A4 kernels |

Key levers:
- **NVFP4 / modelopt quantization** is what lets 198–251 GB MoE checkpoints fit in 275 GB *and*
  run on Blackwell FP4 tensor cores. These checkpoints are **vLLM-only** — llama.cpp would need a
  lossy GGUF re-quant and ollama has no NVFP4/glm5next support.
- **Speculative decoding (MTP / DFlash)** was enabled only where the checkpoint ships a usable
  draft head, and only after confirming tool-call correctness — a draft head existing does **not**
  by itself prove useful acceptance (explicitly left off for Ornith for that reason).
- **`--language-model-only`** on the VL / multimodal checkpoints strips the vision tower we don't
  need, freeing VRAM and load time.
- **Right parser or silent breakage:** each family needs its own `--tool-call-parser` /
  `--reasoning-parser`; a mismatch produces `reasoning_content` leakage or dropped tool calls.

---

## 4. The vLLM Qwen tool-parser repair

A reproduced vLLM Qwen tool-parser defect **dropped the final parameter** of a tool call when the
`</parameter>` close tag was missing but `</function>` was present. The narrow repair
(`scripts/b300_patch_qwen_parser.py`, verified by `scripts/b300_qwen_parser_probe.py`) only
completes the trailing parameter when the function-end marker is present, preserving genuinely
truncated calls. 24 parser cases + 45 local tests passed. No causal claim that it fixed any specific
model's quality (Nex still produced a poor app afterward with no truncation errors) — it removes a
serving-layer confound, it is not a quality boost.

---

## 5. The tuning discipline (so "slow" is never charged to the model)

Because the defaults are slow, the campaign fixed rules so that *serving* slowness is never
mistaken for *model* incapability:

- **Admission gate: ≥ 100 decoded tok/s** (raised from a provisional 50), median of two warm
  256-token probes after one cold probe. The campaign runner refuses a model without fresh,
  passing admission evidence.
- **Bounded tuning: max 3 serving configurations, 45 minutes total** wall time (including
  load/compile, excluding weight download). Stop as soon as 100 tok/s is cleared.
- **Mandatory official model-card review** even after passing — adopt the publisher's documented
  low-cost perf recommendations (MTP, hybrid-cache settings, draft checkpoints), record what was
  adopted or deferred and why.
- **Do not trade quality for speed:** no shortening the 128K context, no lowering reasoning effort,
  no silent precision downgrade to hit a number.
- **Infra failures ≠ model failures:** on tuning exhaustion, write `THROUGHPUT_SKIP.md` + an
  explicitly infrastructure-only DNF, preserve all evidence, move on. A timeout means "did not fit
  this workflow's time budget," not "unusable" — frontier baselines also ran long (GPT 5.6 Sol 317 min).

`scripts/b300_tuning.py` records bounded rounds and writes admission evidence under
`results-v4/_b300_campaign/tuning/` and `.../performance-validation/`.

---

## 6. Takeaways

1. **The vendor default is an unusable server.** `--enforce-eager` alone cost 13.7× on GLM; the
   stock CUDA 12.8 can't even build B300 kernels. Expect to do real work before the first token.
2. **Most of the speed is free** once you let vLLM compile and capture CUDA graphs and pick
   latency mode — it is configuration, not hardware or precision.
3. **NVFP4 + vLLM is the only path** for the big MoE checkpoints on a single B300; the small
   27–35B models serve in bf16 and leave the most headroom for speculative decoding.
4. **Every model is bespoke:** parser, quant, draft head, runtime version, loader fixes all differ
   per checkpoint. Budget tuning time per model — the 45-minute / 3-config cap existed precisely
   because this is fiddly, and the discipline keeps serving slowness out of the model's score.
