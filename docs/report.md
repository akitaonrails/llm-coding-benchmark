# Benchmark Report

Generated at: 2026-04-03T19:46:37+00:00
Prompt SHA256: `133f6e7bfd7098eec49db2e8bd9c90c018bbbd734e7dfee6f2eb1b315df3b89f`

## Progress

- `completed`: 0
- `completed_with_errors`: 0
- `failed`: 2
- `timeout`: 0
- `not_run`: 13

## Runner

`opencode run --agent build --format json`

- Selected after local probing because it exposes machine-readable JSON events with session IDs and token counts.
- The local crush install advertised --yolo in help output but rejected the flag at runtime, which makes it a poor default for unattended benchmarking here.
- The explicit build agent has permissive filesystem/tool rules, which is the closest match to the requested autonomous coding workflow.

## Model Selection

- `gemma4_31b` -> `ollama/google/gemma4-31b-it-bf16`: Hosted locally and is the largest Gemma 4 variant exposed by opencode. Skipped by default until the provider load issue is resolved.
- `glm_4_7_flash_bf16` -> `ollama/glm/glm-4.7-flash-bf16`: Added back as a local benchmark target after increasing server swap. Skipped by default because observed throughput is too low to be practical on current hardware.
- `llama4_scout` -> `ollama/meta/llama4-scout`: Requested local model family; exact hosted variant available through opencode. Skipped by default because Ollama unloads or goes idle before the benchmark run can begin reliably.
- `qwen3_32b` -> `ollama/qwen/qwen3-32b`: Requested local model family; exact hosted variant available through opencode.  Skipped by default after benchmark preview averaged 7.96 output tok/s over the first 3 steps (< 20.00).
- `qwen3_coder_next` -> `ollama/qwen/qwen3-coder-next`: Best direct coding-oriented local Qwen variant matching the benchmark brief.  Skipped by default after benchmark preview measured 6.59 output tok/s (< 20.00).
- `qwen3_5_35b` -> `ollama/qwen/qwen3.5-35b`: Requested local model family; exact hosted variant available through opencode.
- `qwen3_5_122b` -> `ollama/qwen/qwen3.5-122b`: Largest requested local Qwen 3.5 variant hosted on the Ollama server.
- `gpt_oss_20b` -> `ollama/openai/gpt-oss-20b`: Added as a local Ollama GPT OSS baseline for later warmup and benchmark testing.
- `nemotron_cascade_2` -> `ollama/nvidia/nemotron-cascade-2`: Added as a local Ollama Nemotron Cascade 2 candidate for later warmup and benchmark testing. This entry uses explicit local model metadata because it is not yet mapped in the home opencode config.
- `claude_opus_4_6` -> `openrouter/anthropic/claude-opus-4.6`: Exact requested cloud model.
- `gpt_5_4_pro` -> `openrouter/openai/gpt-5.4-pro`: Chosen from the OpenRouter GPT 5.4 family as the largest and most coding-oriented variant.
- `kimi_k2_5` -> `openrouter/moonshotai/kimi-k2.5`: Chosen as the latest/highest Kimi variant listed by OpenRouter locally.
- `glm_5` -> `openrouter/z-ai/glm-5`: Chosen as the latest/highest GLM variant listed by OpenRouter locally; this replaces the local GLM test.
- `qwen3_6_plus` -> `openrouter/qwen/qwen3.6-plus:free`: Added from OpenRouter cloud availability; chose the non-preview Qwen 3.6 Plus variant exposed locally.
- `minimax_m2_7` -> `openrouter/minimax/minimax-m2.7`: Chosen as the largest/latest MiniMax variant listed by OpenRouter locally.

## Ollama Warmup

Loaded from `results/ollama_warmup.json`.

Minimum useful context target: `32768`

| Model | Highest verified ctx | Recommendation |
| --- | ---: | --- |
| Gemma 4 31B | 131072 | keep in benchmark at 131072 |
| GLM 4.7 Flash BF16 | 202752 | keep in benchmark at 202752 |
| Llama 4 Scout | 131072 | keep in benchmark at 131072 |
| Qwen 3 32B | 40960 | keep in benchmark at 40960 |
| Qwen 3 Coder Next | 262144 | keep in benchmark at 262144 |
| Qwen 3.5 35B | 262144 | keep in benchmark at 262144 |
| Qwen 3.5 122B | 262144 | keep in benchmark at 262144 |
| GPT OSS 20B | 131072 | keep in benchmark at 131072 |
| Nemotron Cascade 2 | 262144 | keep in benchmark at 262144 |

## Results

| Model | Provider | Warmup ctx | Status | Elapsed (s) | Total tokens | Tok/s | Works? | Files | Notes |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |
| Gemma 4 31B | ollama | 131072 | not_run | - | - | - | n/a | 0 | Run has not been executed yet. Warmup verified 131072 context. keep in benchmark at 131072. |
| GLM 4.7 Flash BF16 | ollama | 202752 | not_run | - | - | - | n/a | 0 | Run has not been executed yet. Warmup verified 202752 context. keep in benchmark at 202752. |
| Llama 4 Scout | ollama | 131072 | not_run | - | - | - | n/a | 0 | Run has not been executed yet. Warmup verified 131072 context. keep in benchmark at 131072. |
| Qwen 3 32B | ollama | 40960 | failed | 304.74 | 11714 | 38.44 | no | 1 | Exit code -15. Generated files do not resemble the requested Rails project. Warmup verified 40960 context. keep in benchmark at 40960. |
| Qwen 3 Coder Next | ollama | 262144 | failed | 98.07 | 15176 | 154.75 | partial | 1507 | Exit code -15. Some expected benchmark artifacts exist, but the scaffold looks incomplete. Warmup verified 262144 context. keep in benchmark at 262144. |
| Qwen 3.5 35B | ollama | 262144 | not_run | - | - | - | n/a | 0 | Run has not been executed yet. Warmup verified 262144 context. keep in benchmark at 262144. |
| Qwen 3.5 122B | ollama | 262144 | not_run | - | - | - | n/a | 0 | Run has not been executed yet. Warmup verified 262144 context. keep in benchmark at 262144. |
| GPT OSS 20B | ollama | 131072 | not_run | - | - | - | n/a | 0 | Run has not been executed yet. Warmup verified 131072 context. keep in benchmark at 131072. |
| Nemotron Cascade 2 | ollama | 262144 | not_run | - | - | - | n/a | 0 | Run has not been executed yet. Warmup verified 262144 context. keep in benchmark at 262144. |
| Claude Opus 4.6 | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| GPT 5.4 Pro | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Kimi K2.5 | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| GLM 5 | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3.6 Plus | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| MiniMax M2.7 | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |

## Per-Run Paths

Each run writes to `results/<slug>/` with these files:

- `project/`: the generated project workspace
- `prompt.txt`: exact prompt used for the run
- `opencode-output.ndjson`: raw JSON event stream from opencode
- `opencode-stderr.log`: stderr from the opencode process
- `result.json`: normalized metadata used for this report

