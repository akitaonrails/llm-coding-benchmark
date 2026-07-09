# Model Pricing Reference

Prices as of **July 9, 2026**. OpenRouter prices from their live `/api/v1/models` endpoint; subscription pricing from vendor pages. Previous revision (April 3, 2026) is in git history — notable changes since then are flagged in the Notes column. For per-run cost analysis and the quality × cost trade-off, see [`cost_analysis.md`](cost_analysis.md).

## OpenRouter API Pricing (per million tokens)

| Model | Input $/M | Output $/M | Context | Notes |
|-------|-----------|------------|---------|-------|
| Claude Opus 4.7 / 4.8 | $5.00 | $25.00 | 1,000,000 | Top-2 benchmark scores |
| Claude Fable 5 | $10.00 | $50.00 | 1,000,000 | Claude 5 generation; premium tier |
| Claude Sonnet 5 | $2.00 | $10.00 | 1,000,000 | Tier C in benchmark despite the name |
| Claude Sonnet 4.6 | $3.00 | $15.00 | 1,000,000 | |
| Claude Opus 4.6 | $5.00 | $25.00 | 1,000,000 | |
| GPT 5.4 Pro (OR) | $30.00 | $180.00 | 1,050,000 | Unused — benchmark uses Codex/OpenAI direct |
| GPT 5.6 Sol / Sol Pro | $5.00 | $30.00 | 1,050,000 | New generation (2026-07-09); same card as GPT 5.5 |
| GPT 5.6 Terra | $2.50 | $15.00 | 1,050,000 | Same card as GPT 5.4 |
| GPT 5.6 Luna | $1.00 | $6.00 | 1,050,000 | Cheap tier |
| Gemini 3.5 Flash | $1.50 | $9.00 | 1,048,576 | Best non-Anthropic/OpenAI score (93) |
| Gemini 3.1 Pro | $2.00 | $12.00 | 1,048,576 | |
| Kimi K2.5 | $0.38 | $2.02 | 262,144 | Output rate up from $1.72 (Apr) |
| Kimi K2.6 | $0.65 | $3.41 | 262,144 | **Rates rose ~30% since its benchmark run** |
| Kimi K2.7 Code | $0.74 | $3.50 | 262,144 | |
| Grok 4.5 | $2.00 | $6.00 | 500,000 | Reasoning always on; max effort = default |
| Grok 4.3 / 4.20 | $1.25 | $2.50 | 1,000,000 | |
| Nex-N2-Pro | $0.25 | $1.00 | 262,144 | **`:free` endpoint delisted** — was free at benchmark run time (2026-06-15) |
| DeepSeek V4 Flash | $0.09 | $0.18 | 1,048,576 | Cheapest working model |
| DeepSeek V4 Pro | $0.43 | $0.87 | 1,048,576 | |
| DeepSeek V3.2 | $0.23 | $0.34 | 131,072 | |
| MiniMax M3 | $0.30 | $1.20 | 1,048,576 | |
| MiniMax M2.7 | $0.18 | $0.72 | 204,800 | |
| Qwen3.7 Max | $1.25 | $3.75 | 1,000,000 | |
| Qwen 3.6 Plus | $0.33 | $1.95 | 1,000,000 | **No longer free** (was free-tier in Apr) |
| Qwen 3.5 397B A17B | $0.39 | $2.45 | 256,000 | Nex-N2-Pro's base model |
| Step 3.7 Flash | $0.20 | $1.15 | 256,000 | |
| Step 3.5 Flash | $0.10 | $0.30 | 262,144 | |
| Xiaomi MiMo V2.5 Pro | $0.43 | $0.87 | 1,048,576 | |
| GLM 5 | $0.60 | $1.92 | 202,752 | Context grew from 80K; rates changed |
| Gemma 4 31B | $0.12 | $0.35 | 262,144 | |
| Llama 4 Scout | $0.10 | $0.30 | 10,000,000 | Context now 10M |
| Nemotron 3 Super | $0.08 | $0.45 | 1,000,000 | |

### Cost tiers

- **Ultra-cheap (< $0.50/M input):** Nemotron 3 Super, DeepSeek V4 Flash, Llama 4 Scout, Step 3.5 Flash, Gemma 4 31B, MiniMax M2.7, Step 3.7 Flash, DeepSeek V3.2, Nex-N2-Pro, MiniMax M3, Qwen 3.6 Plus, Kimi K2.5, Qwen 3.5 397B
- **Mid-range ($0.50–$2/M input):** DeepSeek V4 Pro, MiMo V2.5 Pro, GLM 5, Kimi K2.6/K2.7, Grok 4.3, Qwen3.7 Max, Gemini 3.5 Flash
- **Premium ($2–$10/M input):** Grok 4.5, Gemini 3.1 Pro, Claude Sonnet 5/4.6, Claude Opus 4.6/4.7/4.8
- **Ultra-premium:** Claude Fable 5 ($10/$50), GPT 5.4 Pro ($30/$180)
- **No free tier remains** among benchmark-relevant models: Qwen 3.6 Plus and Nex-N2-Pro both converted to paid since April.

## OpenAI Direct (Codex CLI runs)

| Model | Input $/M | Cached $/M | Output $/M | Notes |
|-------|-----------|------------|------------|-------|
| GPT 5.4 | $2.50 | $0.25 | $15.00 | Used for the GPT 5.4 xHigh Codex runs |
| GPT 5.5 | $5.00 | $0.50 | $30.00 | 2× price jump over 5.4 |
| GPT 5.6 Sol | $5.00 | $0.50 | $30.00 | Benchmark run billed via ChatGPT subscription instead (Codex ChatGPT auth) |

## Subscription Plans (flat-rate, used by the benchmark)

### Z.ai GLM Coding Plan (GLM 5.1 / 5.2 runs)

| Tier | $/month | Prompts | Notes |
|------|---------|---------|-------|
| Lite | $18 ($12.60 promo) | ~80 / 5h, ~400 / week | Includes GLM-5.2 flagship on all tiers |
| Pro | $72 ($50.40 promo) | ~400 / 5h, ~2,000 / week | |
| Max | $160 ($112 promo) | ~1,600 / 5h, ~8,000 / week | 30% promo through Sept 2026 |

### Sakana (Fugu / Fugu Ultra runs)

| Tier | $/month | Notes |
|------|---------|-------|
| Standard | $20 | Both Fugu and Fugu Ultra included |
| Pro | $100 | 10× Standard usage |
| Max | $200 | 20× Standard usage |

Pay-as-you-go also exists for Fugu Ultra at $5/$30 per M (rises above 272K context; $0.50/M cached input).

## Consumer Subscriptions (Anthropic / OpenAI) — verified 2026-07-09

The benchmark itself pays raw API rates (OpenRouter BYO key; Codex runs billed via `OPENAI_API_KEY`), but individual developers often run the same models through consumer plans:

### Anthropic (Claude)

| Plan | $/month | Claude Code | Notes |
|------|---------|-------------|-------|
| Pro | $20 ($17/mo annual) | Yes | Session limits doubled 2026-05-06; weekly limits +50% promo through 2026-07-13 |
| Max 5x | $100 | Yes + priority | 5× Pro limits |
| Max 20x | $200 | Yes + priority | 20× Pro limits; monthly billing only |

### OpenAI (ChatGPT)

| Plan | $/month | Codex | Notes |
|------|---------|-------|-------|
| Go | $8 | limited | |
| Plus | $20 | Yes | 15-80 GPT-5.5 msgs / 5h window |
| Pro 5x | $100 | Yes | 5× Plus limits |
| Pro 20x | $200 | Yes | 20× Plus limits |

**Codex subscription usage is credit-metered since 2026-04-02** (GPT-5.5 = 125 in / 750 out credits per 1M tokens; GPT-5.4 = 62.5/375) — heavy real-world use runs $100-200/developer/month, so "included" is not "unlimited". See [`cost_analysis.md`](cost_analysis.md) §4 for break-even math against our per-run costs.

## Key changes since the April 3 revision

1. **Free tiers evaporated**: Qwen 3.6 Plus (now $0.33/$1.95) and Nex-N2-Pro's `:free` endpoint (now $0.25/$1.00) both converted to paid.
2. **Kimi got pricier across the line**: K2.5 output $1.72→$2.02; K2.6 effectively +30% vs its benchmark-run rates.
3. **New premium ceiling**: Claude Fable 5 at $10/$50 doubles the Opus 4.x rate card.
4. **A reminder that per-M ≠ per-run**: agentic runs are cache-read-dominated (5–15M cache-read tokens per run), so cheap rate cards with high token churn (Gemini 3.5 Flash) can out-cost pricier disciplined models per run. See [`cost_analysis.md`](cost_analysis.md).
