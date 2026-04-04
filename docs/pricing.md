# Model Pricing Reference

Prices as of April 3, 2026. OpenRouter prices from their live `/api/v1/models` endpoint.

## OpenRouter API Pricing (per million tokens)

| Model | Input $/M | Output $/M | Context | Notes |
|-------|-----------|------------|---------|-------|
| Claude Opus 4.6 | $5.00 | $25.00 | 1,000,000 | Premium coding model |
| GPT 5.4 Pro | $30.00 | $180.00 | 1,050,000 | Most expensive; enhanced reasoning |
| Kimi K2.5 | $0.38 | $1.72 | 262,144 | Multimodal with visual coding |
| GLM 5 | $0.72 | $2.30 | 80,000 | Smallest context window |
| Qwen 3.6 Plus | **FREE** | **FREE** | 1,000,000 | Rate-limited free tier |
| Qwen 3.5 397B | $0.39 | $2.34 | 262,144 | MoE (17B active of 397B) |
| Gemma 4 31B | $0.14 | $0.40 | 262,144 | Cheapest non-free model |
| Llama 4 Scout | $0.08 | $0.30 | 327,680 | MoE (17B active of 109B) |
| Nemotron 3 Super | $0.10 | $0.50 | 262,144 | MoE (12B active of 120B); free tier also available |
| MiniMax M2.7 | $0.30 | $1.20 | 204,800 | Up to 131K output tokens |
| DeepSeek V3.2 | $0.26 | $0.38 | 163,840 | Very cheap input+output |
| Step 3.5 Flash | $0.10 | $0.30 | 262,144 | Free tier also available |
| Claude Sonnet 4.6 | $3.00 | $15.00 | 200,000 | Mid-tier Anthropic model |

### Cost tiers

- **Free:** Qwen 3.6 Plus (rate-limited)
- **Ultra-cheap (< $0.50/M input):** Llama 4 Scout, Gemma 4 31B, Nemotron 3 Super, Kimi K2.5, Qwen 3.5 397B, MiniMax M2.7
- **Mid-range:** GLM 5
- **Premium:** Claude Opus 4.6 ($5/$25)
- **Ultra-premium:** GPT 5.4 Pro ($30/$180)

## Subscription Plans

### Anthropic (Claude)

| Plan | $/month | Models | Usage Limits | Claude Code |
|------|---------|--------|--------------|-------------|
| Free | $0 | Sonnet 4.6 (limited) | Limited messages | No |
| Pro | $20 ($17 annual) | Sonnet 4.6, Opus 4.6 | ~44K tokens/5hr window | Yes |
| Max 5x | $100 | Sonnet 4.6, Opus 4.6 | ~88K tokens/5hr window | Yes + priority |
| Max 20x | $200 | Sonnet 4.6, Opus 4.6 | ~220K tokens/5hr window | Yes + priority + early features |

Token-per-window figures are approximate (Anthropic describes Max limits as "5x" and "20x" relative to Pro).

### OpenAI (ChatGPT)

| Plan | $/month | Key Inclusions | Limits |
|------|---------|----------------|--------|
| Free | $0 | GPT-5.2 Instant (limited) | Low message caps |
| Go | $8 | GPT-5.2 Instant (unlimited), GPT-5.3 | 160 msgs/3hr for GPT-5.3; has ads |
| Plus | $20 | GPT-5.4 Thinking, Codex, Agent Mode, Deep Research (10/mo) | Generous limits |
| Pro | $200 | All models unlimited, o1 Pro mode, GPT-5.4 Pro exclusive | Unlimited messages, max compute |

Codex is included with Plus ($20/mo) and above — no separate subscription. Codex API pricing: `codex-mini-latest` at $1.50/$6.00/M tokens, GPT-5 at $1.25/$10.00/M tokens.

## Effective Cost: Subscription vs API

Estimated for moderate coding use (~15M input + ~3M output tokens/month):

| Approach | Est. $/month | Notes |
|----------|-------------|-------|
| Qwen 3.6 Plus (OpenRouter) | $0 | Free but rate-limited |
| Llama 4 Scout (OpenRouter) | ~$2 | Cheapest paid option |
| Kimi K2.5 (OpenRouter) | ~$11 | Good quality/price ratio |
| Claude Pro subscription | $20 | Capped at ~44K tokens/5hr |
| ChatGPT Plus subscription | $20 | Includes Codex |
| Claude Opus 4.6 (OpenRouter) | ~$150 | Raw API, no caps |
| Claude Max 20x subscription | $200 | ~220K tokens/5hr; best for heavy interactive use |
| ChatGPT Pro subscription | $200 | Unlimited GPT 5.4 Pro — huge value vs API |
| GPT 5.4 Pro (OpenRouter) | ~$990 | Extremely expensive via raw API |

**Key takeaway:** ChatGPT Pro at $200/mo is the best value for GPT 5.4 Pro access (API would cost ~5x more). For Claude, Pro at $20/mo covers moderate use; heavy users benefit from Max 20x. For budget benchmarking, open-source models on OpenRouter are all under $2.50/M output tokens.
