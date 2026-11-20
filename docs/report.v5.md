# Benchmark v5 — Cost, Speed & Prompt-Caching Report

Models completed: **16** · Task: 14-goal greenfield Rails RubyLLM SPA (2 phases + up to 2 standardized nudges).
All costs are computed from verified November 19, 2026 official first-party rates (`config/pricing_v5.json`) using exact 5-bucket token accounting (`input_uncached`, `cache_read`, `cache_write`, `output`, `reasoning`).

## 1. Cost × Time × Quality Gate Leaderboard

| Rank | Model | Family | Harness | Gate | Nudges | Wall | Actual $ | No-Cache $ | Cache Saved | Cache Hit % | Total Tok |
|---:|---|---|---|:---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | GPT-6 Luna | OpenAI | `codex` | **PASS** | 0 | 19.4m | **$0.15** | $1.03 | -85.6% | 97.8% | 10.10M |
| 2 | GPT-6.1 Terra | OpenAI | `codex` | **PASS** | 0 | 7.4m | **$0.50** | $4.77 | -89.5% | 96.8% | 4.67M |
| 3 | DeepSeek V4.1 Flash (1017) | DeepSeek | `opencode` | **PASS** | 0 | 29.2m | **$0.56** | $9.87 | -94.3% | 98.4% | 32.35M |
| 4 | Gemini 4 Hydrogen | Google | `agy` | **PASS** | 0 | 16.2m | **$1.89** | $12.89 | -85.3% | 95.4% | 8.19M |
| 5 | GPT-6.2 Sol | OpenAI | `codex` | **PASS** | 0 | 25.3m | **$2.02** | $17.20 | -88.2% | 96.7% | 8.33M |
| 6 | Claude Sonnet 5.5 | Anthropic | `claude` | **PASS** | 0 | 15.7m | **$2.14** | $11.50 | -81.4% | 96.5% | 5.39M |
| 7 | Kimi K3.1 Pro | Moonshot | `opencode` | **PASS** | 0 | 16.0m | **$2.66** | $14.23 | -81.3% | 95.6% | 6.80M |
| 8 | Gemini 4 Neon | Google | `agy` | **PASS** | 0 | 24.1m | **$3.10** | $16.01 | -80.6% | 93.9% | 4.92M |
| 9 | Gemini 4 Carbon | Google | `agy` | **PASS** | 0 | 39.1m | **$3.29** | $21.32 | -84.6% | 95.4% | 10.09M |
| 10 | DeepSeek V4 Pro (0813) | DeepSeek | `opencode` | **PASS** | 0 | 35.2m | **$3.39** | $49.25 | -93.1% | 98.3% | 36.81M |
| 11 | Claude Opus 5.5 | Anthropic | `claude` | **PASS** | 0 | 19.7m | **$5.73** | $40.06 | -85.7% | 97.7% | 9.58M |
| 12 | GPT-6.2 Astra | OpenAI | `codex` | **PASS** | 0 | 15.9m | **$5.78** | $58.92 | -90.2% | 97.6% | 7.20M |
| 13 | GLM-5.3 | Z.ai | `opencode` | **PASS** | 0 | 28.5m | **$6.08** | $29.44 | -79.4% | 99.1% | 20.80M |
| 14 | Claude Fable 5.2 | Anthropic | `claude` | **PASS** | 0 | 35.0m | **$12.96** | $82.14 | -84.2% | 96.9% | 9.63M |
| 15 | Grok 4.7 | xAI | `grok` | **PASS** | 0 | 87.4m | **$14.19** | $46.09 | -69.2% | 95.0% | 22.60M |
| 16 | Muse Wonder 1.0 | Meta | `muse` | **FAIL** | 2 | 2.3m | **$0.91** | $2.16 | -57.5% | 62.0% | 528.9K |

## 2. Token & Prompt-Caching Breakdown

| Model | Uncached In | Cache Read | Cache Write | Out (incl. Reas.) | Reasoning | In $ | Cache Read $ | Cache Write $ | Out $ | Native CLI $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GPT-6 Luna | 224.5K | 9.82M | 0 | 56.9K | 23.4K | $0.02 | $0.10 | $0.00 | $0.03 | — |
| GPT-6.1 Terra | 147.3K | 4.49M | 0 | 25.7K | 4.1K | $0.15 | $0.22 | $0.00 | $0.13 | — |
| DeepSeek V4.1 Flash (1017) | 516.6K | 31.65M | 0 | 182.7K | 105.0K | $0.15 | $0.19 | $0.00 | $0.22 | $0.35 |
| Gemini 4 Hydrogen | 371.7K | 7.72M | 0 | 100.9K | 44.6K | $0.56 | $0.58 | $0.00 | $0.76 | — |
| GPT-6.2 Sol | 277.2K | 7.99M | 0 | 66.7K | 23.9K | $0.55 | $0.80 | $0.00 | $0.67 | — |
| Claude Sonnet 5.5 | 162 | 5.12M | 182.8K | 89.5K | 24.4K | $0.00 | $0.51 | $0.73 | $0.89 | $2.14 |
| Kimi K3.1 Pro | 298.5K | 6.43M | 0 | 77.6K | 36.0K | $0.60 | $1.29 | $0.00 | $0.78 | $2.66 |
| Gemini 4 Neon | 294.0K | 4.53M | 0 | 102.9K | 36.2K | $0.88 | $0.68 | $0.00 | $1.54 | — |
| Gemini 4 Carbon | 454.5K | 9.49M | 0 | 143.1K | 62.2K | $0.91 | $0.95 | $0.00 | $1.43 | — |
| DeepSeek V4 Pro (0813) | 619.6K | 35.94M | 0 | 249.8K | 171.4K | $0.82 | $1.58 | $0.00 | $0.99 | $3.39 |
| Claude Opus 5.5 | 218 | 9.26M | 214.5K | 108.3K | 23.2K | $0.00 | $1.85 | $1.72 | $2.17 | $5.73 |
| GPT-6.2 Astra | 172.5K | 6.99M | 0 | 40.1K | 7.5K | $1.38 | $2.80 | $0.00 | $1.60 | — |
| GLM-5.3 | 193.2K | 20.49M | 0 | 108.4K | 51.4K | $0.27 | $5.33 | $0.00 | $0.48 | $3.55 |
| Claude Fable 5.2 | 186 | 9.18M | 298.4K | 158.6K | 46.0K | $0.00 | $1.84 | $4.78 | $6.35 | $12.96 |
| Grok 4.7 | 1.11M | 21.27M | 0 | 223.3K | 159.7K | $2.22 | $10.63 | $0.00 | $1.34 | $3.29 |
| Muse Wonder 1.0 | 200.0K | 326.4K | 0 | 2.5K | 34 | $0.80 | $0.07 | $0.00 | $0.05 | — |

## 3. Alternate Rate Views (Post-Dec-1 Gemini 4 Carbon & OpenRouter Rates)

| Model | Scenario | Actual $ | No-Cache $ | Cache Saved |
|---|---|---:|---:|---:|
| DeepSeek V4.1 Flash (1017) | `openrouter_rates` | $0.43 | $1.25 | -65.9% |
| Kimi K3.1 Pro | `openrouter_rates` | $1.92 | $2.38 | -19.7% |
| Gemini 4 Carbon | `post_2026_12_01` | $6.58 | $42.65 | -84.6% |
| DeepSeek V4 Pro (0813) | `openrouter_rates` | $10.59 | $12.75 | -16.9% |
| GLM-5.3 | `openrouter_rates` | $1.58 | $1.60 | -1.3% |

## 4. Integrity & Quality-Gate Diagnostics

| Model | Gemfile | Dockerfile | Compose | Tests | RuboCop | Brakeman | Leak Scan |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| GPT-6 Luna | ok | ok | ok | ok | ok | ok | CLEAN |
| GPT-6.1 Terra | ok | ok | ok | ok | ok | ok | CLEAN |
| DeepSeek V4.1 Flash (1017) | ok | ok | ok | ok | ok | ok | FLAG (3): phase2.ndjson:sibling:v5_qwen_4_max, phase2.ndjson:sibling:v5_gpt_6_1_terra, phase2.ndjson:sibling:v5_gpt_6_2_astra |
| Gemini 4 Hydrogen | ok | ok | ok | ok | ok | ok | CLEAN |
| GPT-6.2 Sol | ok | ok | ok | ok | ok | ok | CLEAN |
| Claude Sonnet 5.5 | ok | ok | ok | ok | ok | ok | CLEAN |
| Kimi K3.1 Pro | ok | ok | ok | ok | ok | ok | CLEAN |
| Gemini 4 Neon | ok | ok | ok | ok | ok | ok | CLEAN |
| Gemini 4 Carbon | ok | ok | ok | ok | ok | ok | CLEAN |
| DeepSeek V4 Pro (0813) | ok | ok | ok | ok | ok | ok | FLAG (1): phase2.ndjson:sibling:v5_qwen_4_max |
| Claude Opus 5.5 | ok | ok | ok | ok | ok | ok | CLEAN |
| GPT-6.2 Astra | ok | ok | ok | ok | ok | ok | CLEAN |
| GLM-5.3 | ok | ok | ok | ok | ok | ok | CLEAN |
| Claude Fable 5.2 | ok | ok | ok | ok | ok | ok | CLEAN |
| Grok 4.7 | ok | ok | ok | ok | ok | ok | FLAG (4): phase1.ndjson:success_report, phase1.ndjson:benchmark-audit, phase1.ndjson:sibling:v5_metrics |
| Muse Wonder 1.0 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | CLEAN |
