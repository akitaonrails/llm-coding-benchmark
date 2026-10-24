# Qwen3.8-27B inference optimization notes (DFlash2 / context lookup / prefix caching)

Source: X post by @Oluwaphilemon1 summarizing TeksEdge's work —
<https://x.com/Oluwaphilemon1/status/2113912192017805321> (archived 2026-10-24).

## Headline numbers

Qwen3.8-27B on a **single RTX 3090 (24 GB)**, no hardware/model change:

| Stage | Throughput |
|---|---|
| Baseline inference | 82 tok/s |
| Optimized MTP (multi-token prediction) | 114 tok/s |
| + DFlash2 + context lookup | 138 tok/s |
| + optimized lookup verification | **381 tok/s** (~4.6×) |

Prefix caching separately cut **time-to-first-token from 22.4 s → 0.56 s (~40×)** on
repeated shared prefixes (system prompt, tool defs, repo context).

## The four techniques

1. **Speculative decoding** — a fast draft process proposes several tokens; the main
   model verifies and can accept multiple tokens per step, cutting sequential decode work.
   **DFlash2** is the specific speculative-decoding variant used; gains depend on
   draft/verify match rate and verification cost.
2. **Context lookup** — for input/output-overlapping workloads (doc copying, structured
   transforms, code with repeated sequences), reusable spans in the context become
   candidate output instead of fresh generation. TeksEdge reports blocks up to 16 tokens,
   ~15 accepted per block; a 25k-token document-reproduction task went ~260 → 382 tok/s.
   Caveat: conversational/novel output sees much smaller gains.
3. **Faster verification** — the 138 → 381 tok/s jump came from optimizing the lookup
   *verification* stage, i.e. verification overhead was the main bottleneck in this
   workload. Treat the 4.6× as workload-specific, not universal.
4. **Prefix caching** — orthogonal: reuses KV for repeated input prefixes instead of
   recomputing prefill. This is the big one for agentic coding loops (same system
   prompt + tools + repo context every turn).

## Relevance to our setup

- Our Strix Halo runs of `qwen3.8:27b` (llama-swap, Q8_0) measured ~7.7 tok/s generation
  during the v4 sprint benchmark — any of these techniques landing in llama.cpp/llama-swap
  would directly cut wall time (sprint 05 took 3 h).
- Prefix caching matters most for our opencode harness: long shared prefixes every turn.
  llama.cpp already has prompt caching; verify it's actually enabled/effective in the
  llama-swap model entries (`--cache-reuse`, slot management).
- Watch DFlash2 / context-lookup support in llama.cpp releases before the next local
  campaign wave.
- **5090 Strata side: verified 2026-10-24 — nothing to change.** Spec/MTP already on and
  tuner-tuned, `--lookup-chain` tuner-rejected on this hardware (3–8.5% slower), prefix
  reuse already inherent (17k-token repeat prefill 4004 → 130 ms). Full writeup:
  `docs/strata-serving.md` → "TeksEdge-style optimization review".
