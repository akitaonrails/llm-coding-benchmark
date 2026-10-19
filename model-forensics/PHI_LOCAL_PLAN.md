# Phi-4 feasibility on the RTX 5090

Checked 2026-10-09. User explicitly requested no GPU execution while the card is busy. Only nvidia-smi and public repository metadata were read. No weights downloaded, no inference started, no job queued to auto-start.

Observed hardware: NVIDIA GeForce RTX 5090, 32,607 MiB total (31.84 GiB), 19,459 MiB occupied (19.00 GiB) at inspection. Available memory is transient and is not permission to share the GPU.

## Candidates

- Largest official downloadable Phi-4 checkpoint found: **microsoft/Phi-4-reasoning-vision-15B**, released March 4, 2026. Its checkpoint index reports 15,119,518,144 parameters and 30,239,036,288 bytes (28.16 GiB). It combines a Phi-4-Reasoning language backbone with a SigLIP-2 vision encoder. The documented context is 16,384 despite a 32,768 internal config maximum; use the documented limit. BF16 weights leave too little headroom for comfortable full-context use on this GPU. Quantization or partial offload is plausible, but an exact quantized runtime path has NOT been validated. Microsoft's card recommends BF16 vLLM and does not list a tested 5090. [Official card](https://huggingface.co/microsoft/Phi-4-reasoning-vision-15B).
- Largest text-only tier found: **Phi-4, Phi-4-reasoning and Phi-4-reasoning-plus**, all nominally 14B. For a first text reasoning comparison, choose **Reasoning Plus Q8_0**, preserving more weight precision than 4-bit while leaving context headroom. Largest size does not establish the most likely Genesys ancestor. [Official card](https://huggingface.co/microsoft/Phi-4-reasoning-plus).
- **Phi-4-mini-instruct / mini-reasoning (3.8B)** also fit, including BF16 at moderate contexts. They remain more directly relevant to the o200k fingerprint: their tokenizers matched 768/768 strings, whereas Phi-4 and Reasoning Plus matched 309/768. Do not discard mini purely because the user also wants the largest comparison.

## Measured file sizes, not measured runtime VRAM

The [Unsloth quantization repository](https://huggingface.co/unsloth/Phi-4-reasoning-plus-GGUF/tree/main) reports:

| Reasoning Plus weights | File bytes | GiB |
|---|---:|---:|
| BF16 | 29,323,401,664 | 27.31 |
| Q8_0 | 15,580,502,720 | 14.51 |
| Q6_K | 12,030,253,760 | 11.20 |
| Q4_K_M | 9,053,117,120 | 8.43 |

Runtime allocations differ from file size. From the official config: 40 layers, 10 KV heads, head dimension 128. For one sequence with an FP16/BF16 KV cache, cache bytes = 2 (K,V) × 40 × 10 × 128 × 2 bytes × sequence tokens. This is 1.5625 GiB at 8,192 tokens, 3.125 GiB at 16,384 and 6.25 GiB at 32,768. Context includes prompt plus generated tokens. Multiple concurrent sequences and runtime workspaces add memory.

Q8_0 weights plus a 32K cache are approximately 20.76 GiB before compute buffers/runtime overhead. A provisional 2–4 GiB overhead allowance gives roughly 23–25 GiB, comfortably below the idle card's capacity. This is a planning estimate, not a measured peak. BF16 weights plus even an 8K cache total 28.87 GiB before overhead; full 32K requires 33.56 GiB before overhead, so full-GPU BF16/32K does not fit under these assumptions.

## Deferred execution plan

When the user releases the GPU for this work: pin model/conversion revision and a CUDA runtime supporting RTX 5090; inspect conversion/chat template compatibility; begin with Reasoning Plus Q8_0, one sequence, 8K total context, then increase only after measuring headroom. Allow longer output/context when needed to avoid confusing truncated reasoning with failure. Use the publisher's generation settings as a documented baseline. A modern compatible llama.cpp build is a candidate GGUF runtime, not yet installed or tested by this assessment.

Quantization is an experimental variable: compare a small short-context subset against BF16 if it can be accommodated later, or report the precision limitation explicitly. Preserve the original model's tokenizer/template and distinguish reasoning text from final answers. No claim of lineage follows from similarity alone. No automatic start is scheduled.
