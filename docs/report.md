# Benchmark Report

Generated at: 2026-04-04T13:02:04+00:00
Prompt SHA256: `d25f119447215ebf47477c1ce61b24f801bfcb9336467f5b019d554f3c83537c`

## Progress

- `completed`: 8
- `completed_with_errors`: 0
- `failed`: 4
- `timeout`: 0
- `not_run`: 10

## Runner

`opencode run --agent build --format json`

- Selected after local probing because it exposes machine-readable JSON events with session IDs and token counts.
- The local crush install advertised --yolo in help output but rejected the flag at runtime, which makes it a poor default for unattended benchmarking here.
- The explicit build agent has permissive filesystem/tool rules, which is the closest match to the requested autonomous coding workflow.

## Model Selection

- `gemma4_31b` -> `ollama/google/gemma4-31b-it-bf16`: Hosted locally and is the largest Gemma 4 variant exposed by opencode. Skipped by default until the provider load issue is resolved.
- `glm_4_7_flash_bf16` -> `ollama/glm/glm-4.7-flash-bf16`: Added back as a local benchmark target after increasing server swap. Skipped by default because observed throughput is too low to be practical on current hardware.
- `llama4_scout` -> `ollama/meta/llama4-scout`: Requested local model family; exact hosted variant available through opencode. Skipped by default because Ollama unloads or goes idle before the benchmark run can begin reliably.
- `qwen3_32b` -> `ollama/qwen/qwen3-32b`: Requested local model family; exact hosted variant available through opencode. Superseded by the Qwen 3.5 line for future local benchmarking. Skipped by default after benchmark preview averaged 7.96 output tok/s over the first 3 steps (< 20.00).
- `qwen3_coder_next` -> `ollama/qwen/qwen3-coder-next`: Best direct coding-oriented local Qwen variant matching the original benchmark brief. Skipped by default after benchmark preview measured 6.59 output tok/s (< 20.00).
- `qwen3_5_35b` -> `ollama/qwen/qwen3.5-35b`: Requested local model family; exact hosted variant available through opencode. Skipped by default because the current benchmark pass is restricted to OpenRouter models that previously completed successfully.
- `qwen3_5_122b` -> `ollama/qwen/qwen3.5-122b`: Largest requested local Qwen 3.5 variant hosted on the Ollama server. Skipped by default because opencode repeatedly stalls before first output and Ollama drifts back to 262144 context during the run.
- `gpt_oss_20b` -> `ollama/openai/gpt-oss-20b`: Added as a local Ollama GPT OSS baseline for later warmup and benchmark testing.
- `nemotron_cascade_2` -> `ollama/nemotron_cascade_2`: Added as a local Ollama Nemotron Cascade 2 candidate for later warmup and benchmark testing. This entry uses explicit local model metadata because it is not yet mapped in the home opencode config.
- `claude_opus_4_6` -> `openrouter/anthropic/claude-opus-4.6`: Exact requested cloud model.
- `gpt_5_4_pro` -> `openrouter/openai/gpt-5.4-pro`: Chosen from the OpenRouter GPT 5.4 family as the largest and most coding-oriented variant. Skipped by default because it failed in the previous benchmark pass.
- `kimi_k2_5` -> `openrouter/moonshotai/kimi-k2.5`: Chosen as the latest/highest Kimi variant listed by OpenRouter locally.
- `glm_5` -> `openrouter/z-ai/glm-5`: Chosen as the latest/highest GLM variant listed by OpenRouter locally; this replaces the local GLM test. Skipped by default because it completed with errors in the previous benchmark pass.
- `qwen3_6_plus` -> `openrouter/qwen/qwen3.6-plus:free`: Added from OpenRouter cloud availability; chose the non-preview Qwen 3.6 Plus variant exposed locally. Skipped by default because it completed with errors in the previous benchmark pass.
- `qwen3_5_397b_cloud` -> `openrouter/qwen/qwen3.5-397b-a17b`: Added as the OpenRouter cloud Qwen 3.5 flagship under the requested qwen3.5:397b-cloud benchmark slot. Skipped by default because it stalled after completing validation steps and never emitted a terminal stop.
- `gemma4_31b_cloud` -> `openrouter/google/gemma-4-31b-it`: Added as the OpenRouter cloud Gemma 4 benchmark counterpart to the unusable local Gemma 4 path. Skipped by default because the current opencode build does not ship an OpenRouter Gemma 4 registry entry and fails immediately with ProviderModelNotFoundError.
- `llama4_scout_cloud` -> `openrouter/meta-llama/llama-4-scout`: Added as the OpenRouter cloud Llama 4 Scout benchmark counterpart to the unusable local Scout path. Skipped by default because it does not currently resolve cleanly in this opencode build.
- `nemotron_3_super_cloud` -> `openrouter/nvidia/nemotron-3-super-120b-a12b`: Added as the closest OpenRouter cloud Nemotron line available after local Nemotron Cascade 2 proved unusable in this harness. Skipped by default because it still needs a clean first benchmark run.
- `minimax_m2_7` -> `openrouter/minimax/minimax-m2.7`: Chosen as the largest/latest MiniMax variant listed by OpenRouter locally.
- `deepseek_v3_2` -> `openrouter/deepseek/deepseek-v3.2`: Latest DeepSeek model on OpenRouter. Input $0.26/M, output $0.38/M.
- `step_3_5_flash` -> `openrouter/stepfun/step-3.5-flash`: StepFun Step 3.5 Flash on OpenRouter. Input $0.10/M, output $0.30/M.
- `claude_sonnet_4_6` -> `openrouter/anthropic/claude-sonnet-4.6`: Anthropic Claude Sonnet 4.6 on OpenRouter. Input $3.00/M, output $15.00/M.

## Results

| Model | Provider | Warmup ctx | Status | Elapsed (s) | Total tokens | Tok/s | Works? | Files | Notes |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |
| Gemma 4 31B | ollama | - | failed | 0.00 | - | - | no | 0 | Project directory is empty. |
| GLM 4.7 Flash BF16 | ollama | - | failed | 0.00 | - | - | no | 0 | Project directory is empty. |
| Llama 4 Scout | ollama | - | failed | 0.00 | - | - | no | 0 | Project directory is empty. |
| Qwen 3 32B | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3 Coder Next | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3.5 35B | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3.5 122B | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| GPT OSS 20B | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Nemotron Cascade 2 | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Claude Opus 4.6 | openrouter | - | completed | 970.51 | 136806 | 347.18 | yes | 1536 | Rails app, tests, README, and container files detected. |
| GPT 5.4 Pro | openrouter | - | failed | 2910.65 | 63491 | 21.81 | partial | 1118 | Exit code -15. Some expected benchmark artifacts exist, but the scaffold looks incomplete. |
| Kimi K2.5 | openrouter | - | completed | 1738.77 | 63638 | 160.14 | yes | 3405 | Rails app, tests, README, and container files detected. |
| GLM 5 | openrouter | - | completed | 1033.99 | 59378 | 400.01 | yes | 1680 | Rails app, tests, README, and container files detected. |
| Qwen 3.6 Plus | openrouter | - | completed | 1031.84 | 88940 | 182.91 | yes | 744 | Rails app, tests, README, and container files detected. |
| Qwen 3.5 397B Cloud | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Gemma 4 31B Cloud | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Llama 4 Scout Cloud | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Nemotron 3 Super Cloud | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| MiniMax M2.7 | openrouter | - | completed | 847.23 | 79743 | 574.52 | yes | 100 | Rails app, tests, README, and container files detected. |
| DeepSeek V3.2 | openrouter | - | completed | 3606.46 | 115278 | 53.37 | yes | 99 | Rails app, tests, README, and container files detected. |
| Step 3.5 Flash | openrouter | - | completed | 2273.00 | 156267 | 242.11 | yes | 1606 | Rails app, tests, README, and container files detected. |
| Claude Sonnet 4.6 | openrouter | - | completed | 966.85 | 127067 | 532.26 | yes | 2042 | Rails app, tests, README, and container files detected. |

## Per-Run Paths

Each run writes to `results/<slug>/` with these files:

- `project/`: the generated project workspace
- `prompt.txt`: exact prompt used for the run
- `opencode-output.ndjson`: raw JSON event stream from opencode
- `opencode-stderr.log`: stderr from the opencode process
- `followup-prompt.txt`: second-phase validation prompt for continuations when enabled
- `followup-opencode-output.ndjson`: raw JSON event stream from the follow-up continuation
- `followup-opencode-stderr.log`: stderr from the follow-up continuation
- `session-export.json`: exported opencode session snapshot when available
- `result.json`: normalized metadata used for this report

