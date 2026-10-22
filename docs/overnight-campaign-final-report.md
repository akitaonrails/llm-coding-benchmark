# Overnight Campaign — Final Comparison Report (v4 vigilance + v4.2 concurrency)

Self-hosted open-weight coding models scored on the **v4 security-vigilance protocol** (7 sprints, 14 planted sabotage items, denominator 40; score = `(unprompted_weight + 0.4 × reveal_weight) / 40 × 100`; tiers anchored on Opus 4.6 = 83: **A ≥ 83, B 73–82, C 51–72, D ≤ 50**), across a rented 4×B300 pod, a rented 4×H200 pod (concurrency only), the local RTX 5090, and one cloud anchor. Plus the **v4.2 concurrency/capacity** study.

Detailed docs: [`docs/v4.2-concurrency-report.md`](v4.2-concurrency-report.md), [`docs/hardware-serving-playbook.md`](hardware-serving-playbook.md), running log [`docs/b300-4x-overnight-campaign.md`](b300-4x-overnight-campaign.md), scoreboard `results-v4/_local_campaign/summary.json`.

## Final standings (v4 /100)

| # | Model | Box / engine | Score | Tier | unprompted / reveal | Notes |
|---|-------|--------------|------:|:----:|:---:|-------|
| 1 | DeepSeek V4.1 Flash | 4×B300 vLLM FP8 | **92.5** | A | 35 / 5 | Caught both compounds unprompted; ties the frontier. |
| 2 | Qwen3.8 Flash-Next | RTX 5090 Strata IQ3_S | **91.0** | A | 34 / 6 | 3-bit local ≈ its B300 NVFP4 (−1.5, noise). |
| 3 | MiniMax M3.1 Flash | cloud (OpenRouter) | **89.5** | A | 33 / 7 | Cloud anchor. |
| 4 | GLM 5.3 full (~700B) | 4×B300 vLLM FP8 | **76.0** | B | 24 / 16 | Genuine capstone sweep; swept all 6 open at reveal. |
| 5 | Ornith-1.5-122B | 4×B300 vLLM FP8 | **73.0** | B | 24 / 13 | Strong; left only the #6 compound test. |
| 6 | Step-5-Preview | 4×B300 vLLM NVFP4 (MTP) | **72.5** | C | 27 / 5 | Highest pre-reveal base; weakest reveal follow-through. |
| 7 | Muse Spark Open 816B | 4×B300 vLLM NVFP4 | **69.5** | C | 21 / 17 | Lowest base, best reveal sweep (6/7 when told). |
| 8 | MiMo V2.6 Pro (~0.5T) | 4×B300 vLLM FP8 | **67.0** | C | 18 / 22 | Fixed the entire 40/40 set, but half at reveal (timing). |
| 9 | Laguna-S-2.1 | 4×B300 vLLM NVFP4 | **65.5** | C | 19 / 18 | — |
| 10 | **Ornith-1.5-35B** | **RTX 5090 Strata** | **64.5** | C | 23 / 7 | **Same model = 81.0/B on B300 BF16 → −16.5 on the 5090.** |
| 11 | Kimi K2 Thinking (1T) | 4×B300 vLLM INT4 | **46.0** | D | 14 / 14 | "Security-checklist theatre"; 1T flagship weakest at vigilance. |
| 12 | Nex N2.5 Pro (~397B) | 4×B300 vLLM FP8 | **27.0** | D | 0 / 27 | FP8 token corruption → non-booting app; 0 unprompted. |

*(Reference, same protocol, earlier waves: Ornith-1.5-35B **oss on B300 BF16 = 81.0/B**; Qwen3.5-397B = 68.5.)*

## Headline findings

1. **Top open-weights reach cloud parity on coding vigilance.** DeepSeek V4.1 Flash (92.5), Qwen3.8 Flash-Next (91.0) and MiniMax M3.1 Flash (89.5) cluster at the top — the best self-hostable models are competitive with the cloud anchor on this benchmark.

2. **The universal pattern: loud-caught, silent-missed-until-reveal.** Nearly every model (GLM, Step-5, Muse, Ornith-122B/35B, Laguna, MiMo) fixes the *conspicuous* class unprompted — deploy-reachable CVE pins, hardcoded secrets, wildcard CORS, obvious SQLi/XSS — but stays blind to the *silent* class (broken-access-control, undercount aggregates, gutted test assertions, dropped indexes) until the explicit reveal. Capstones behave like production-hardening checklists, not security re-audits. The separator between B and C/D is how much of the silent class a model recovers when finally told, and whether it fixes *both halves* of the compound items.

3. **Parameter count ≠ vigilance.** The 1T Kimi K2 (46.0/D) and ~397B Nex (27.0/D) are the two worst; mid-size models (DeepSeek Flash, Qwen, GLM) dominate. Nex additionally shipped FP8-corrupted source → a non-booting app.

4. **Quantization/offload cost is model-specific (local-serving lesson).** The *same* Ornith-1.5-35B dropped **−16.5** (81.0/B → 64.5/C) moving from B300 BF16 to the 5090's Strata expert-offload — almost entirely in *unprompted* detection (30→23). Yet Qwen3.8 Flash-Next lost only **−1.5** (3-bit IQ3_S vs B300 NVFP4) on the same card. Pick the local quant per model; some models' vigilance survives aggressive quantization, others' collapses.

## v4.2 concurrency / capacity (DeepSeek V4.1 Flash & GLM 5.3 Flash, matched FP8, TP=4)

How many concurrent coding-shaped users a pod comfortably serves (SLO: TTFT ≤ 2 s **and** TPOT ≤ 20 ms; comfortable-N = max N at ≥ 95% per-request goodput):

| Run | Comfortable-N | Peak aggregate | Bottleneck |
|---|---|---|---|
| DeepSeek — **4×B300** | **32** | 2778 tok/s | prefill/TTFT (KV 0.4%) |
| DeepSeek — **4×H200** | **8** | 2506 tok/s | prefill/TTFT (KV 14%) |
| GLM — **4×H200** | **8** | 1930 tok/s | **KV (97%)** |

- **B300 serves ~4× the comfortable coders of the H200** for the same model (32 vs 8); the limiter is the p99 time-to-first-token wall, not decode or memory — neither box saturates compute.
- **On the H200, heavy (DeepSeek) and light (GLM) both land at 8** but for opposite reasons: DeepSeek is compute-bound with a tiny MLA KV (scales aggregate higher), GLM is KV-bound at 97% util (caps lower despite faster single-stream). Serving capacity is set by KV architecture, not parameter count.
- Serving these FP8 MoEs on Hopper was *not* plug-and-play — a DeepGEMM/FlashInfer cu13 JIT fix chain was needed (see the playbook).

## Status / housekeeping
- **All planned campaign work complete:** 11 B300 v4 models, the v4.2 concurrency study (B300 + H200), and the local Ornith-1.5-35B. Scoreboard: `results-v4/_local_campaign/summary.json` (12 entries).
- The 4×B300 and 4×H200 rented pods are released.
- Not run (gated on explicit user confirmation): Gemini 4 via the Antigravity (agy) harness.
