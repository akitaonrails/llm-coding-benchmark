# Model Pricing Reference

Prices updated **November 19, 2026** from official first-party vendor pricing pages, cross-checked against OpenRouter's live `/api/v1/models` endpoint. Machine-readable v5 rate card: [`config/pricing_v5.json`](../config/pricing_v5.json). Previous revision (July 9, 2026) is preserved in git history.

## v5 Tier-A Roster — Official First-Party API Pricing (USD per 1M tokens)

| Family | Model | Input $/M | Cache Read $/M | Cache Write $/M | Output $/M | Context | Caching & Tier Notes |
|---|---|---:|---:|---:|---:|---:|---|
| **Anthropic** | Claude Fable 5.2 | $8.00 | $0.20 | $10.00 *(5m)* / $16.00 *(1h)* | $40.00 | 1,000,000 | Explicit caching (97.5% read discount); Fast Mode 2× ($16/$80) |
| **Anthropic** | Claude Mythos 5.2 | $8.00 | $0.20 | $10.00 *(5m)* / $16.00 *(1h)* | $40.00 | 1,000,000 | Same pricing as Fable 5.2; gated on Cyber/Life Sciences Verification |
| **Anthropic** | Claude Opus 5.5 | $4.00 | $0.20 | $5.00 *(5m)* / $8.00 *(1h)* | $20.00 | 1,000,000 | Explicit caching (95% read discount); thinking billed as output |
| **Anthropic** | Claude Sonnet 5.5 | $2.00 | $0.10 | $2.50 *(5m)* / $4.00 *(1h)* | $10.00 | 1,000,000 | Explicit caching (95% read discount) |
| **OpenAI** | GPT-6.2 Astra | $8.00 | $0.40 | $10.00 *(30m)* / $20.00 *(12h)* | $40.00 | 1,050,000 | 95% cache read; >272K ctx: 2× in/cached, 1.5× out |
| **OpenAI** | GPT-6.2 Sol | $2.00 | $0.10 | $2.50 *(30m)* / $5.00 *(12h)* | $10.00 | 1,050,000 | 95% cache read; >272K ctx step-up |
| **OpenAI** | GPT-6.1 Terra | $1.00 | $0.05 | $1.25 *(30m)* | $5.00 | 1,050,000 | 95% cache read |
| **OpenAI** | GPT-6 Luna | $0.10 | $0.01 | $0.125 | $0.50 | 1,050,000 | 90% cache read |
| **Google** | Gemini 4 Carbon | $2.00 *(→$4.00 Dec 1)* | $0.10 *(→$0.20 Dec 1)* | $0.00 *(implicit)* | $10.00 *(→$20.00 Dec 1)* | 1,048,576 | **Intro rate through 2026-11-30**; shifts to $4/$20 on 2026-12-01; implicit caching only (≥4,096 tok, 95% off) |
| **Google** | Gemini 4 Neon | $3.00 | $0.15 | $0.00 *(implicit)* | $15.00 | 1,048,576 | Implicit caching only (≥4,096 tok, 95% off); thinking billed as output |
| **Google** | Gemini 4 Hydrogen | $1.50 | $0.075 | $0.00 *(implicit)* | $7.50 | 1,048,576 | Implicit caching only (95% off) |
| **xAI** | Grok 4.7 | $2.00 | $0.50 | $0.00 *(implicit)* | $6.00 | 500,000 | 75% cache read; **≥200K ctx doubles all rates** ($4/$1/$12) |
| **Z.ai** | GLM-5.3 | $1.40 | $0.26 | $0.00 *(implicit)* | $4.40 | 1,000,000 | Official Z.ai API; OpenRouter discounted providers at $0.07/$0.069/$1.40 |
| **Moonshot** | Kimi K3.1 Pro | $2.00 | $0.20 | $0.00 *(implicit)* | $10.00 | 1,000,000 | Official Moonshot API (90% cache read); OpenRouter at $0.253/$0.18/$8.80 |
| **Alibaba** | Qwen 4 Max | $1.50 | $0.075 | $1.875 *(5m)* / $3.00 *(1h)* | $4.50 | 1,000,000 | International/Model Studio pricing (OpenRouter: $1.425/$0.071/$1.78/$4.275) |
| **DeepSeek** | DeepSeek V4.1 Flash (1017) | $0.30 *(off-peak $0.15)* | $0.006 *(off-peak $0.003)* | $0.00 *(implicit)* | $1.20 *(off-peak $0.60)* | 1,048,576 | Official peak/off-peak (50% off off-peak); OpenRouter: $0.036/$0.01/$0.50 |
| **DeepSeek** | DeepSeek V4 Pro (0813) | $1.32 *(off-peak $0.66)* | $0.044 *(off-peak $0.022)* | $0.00 *(implicit)* | $3.96 *(off-peak $1.98)* | 1,048,576 | Official peak/off-peak; OpenRouter: $0.27/$0.21/$11.50 |
| **Meta** | Muse Wonder 1.0 | $4.00 | $0.20 | $0.00 *(implicit)* | $20.00 | 1,000,000 | Standard API (95% cache read); also in Muse Code plans ($50/$200/mo) |

## Other Notable November 2026 OpenRouter Rates (Reference Only — Not in v5)

| Model | OpenRouter ID | Input $/M | Cache Read $/M | Output $/M |
|---|---|---:|---:|---:|
| Xiaomi MiMo V2.6 Pro | `xiaomi/mimo-v2.6-pro` | $0.435 | $0.0036 | $0.87 |
| Nex N2.6 | `nex-agi/nex-n2.6` | $0.12 | $0.024 | $0.40 |
| Sakana Fugu Ultra v2 | `sakana/fugu-ultra-v2` | $5.00 | $0.50 | $30.00 |
| Step 5 Preview | `stepfun/step-5-preview` | $1.00 | $0.10 | $2.70 |
| MiniMax M3.1 Flash | `minimax/minimax-m3.1-flash` | $0.15 | $0.015 | $0.60 |

## Key Pricing Shifts (July → November 2026)

1. **Prompt-caching economics reshaped agentic costs:** Cache-read discounts deepened to **95–97.5%** across frontier labs (Fable 5.2 at $0.20/M = 97.5% off; GPT-6.2 Astra at $0.40/M = 95% off; Gemini 4 at 95% off).
2. **Cache-write fees now apply to both Anthropic and OpenAI:** GPT-6.x introduced explicit 1.25× cache-write charges (30m retention), matching Anthropic's 1.25× (5m) / 2× (1h) structure. Measuring cache-write vs. cache-read separately is now mandatory for accurate cost comparisons.
3. **Frontier price compression:** Fable 5.2 ($8/$40) and GPT-6.2 Astra ($8/$40) dropped 20% from Fable 5 / GPT-6 Astra ($10/$50); Opus 5.5 dropped 20% ($5/$25 → $4/$20); GPT-6.2 Sol ($2/$10) and Sonnet 5.5 ($2/$10) sit at the former Sonnet-4.6 discount floor.
4. **Gemini 4 Carbon price cliff on Dec 1, 2026:** Currently $2/$10 intro pricing through Nov 30, 2026, doubling to $4/$20 on Dec 1. v5 reports will show both intro and post-Dec-1 costs.
