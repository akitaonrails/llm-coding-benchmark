# Benchmark Report

Generated at: 2026-04-16T23:50:00+00:00
Prompt SHA256: `d25f119447215ebf47477c1ce61b24f801bfcb9336467f5b019d554f3c83537c`

## Progress

- `completed`: 16
- `completed_with_errors`: 1
- `failed`: 4
- `timeout`: 1
- `not_run`: 11

## Runner

`opencode run --agent build --format json`

- Selected after local probing because it exposes machine-readable JSON events with session IDs and token counts.
- The local crush install advertised --yolo in help output but rejected the flag at runtime, which makes it a poor default for unattended benchmarking here.
- The explicit build agent has permissive filesystem/tool rules, which is the closest match to the requested autonomous coding workflow.

## Model Selection

- `gemma4_31b` -> `ollama/google/gemma4-31b-it-bf16`: Hosted locally via llama-swap. Requires llama.cpp b8665+ for the dedicated Gemma 4 tool call parser (PR #21418). Skipped by default; re-enable for llama-swap benchmark runs.
- `glm_4_7_flash_bf16` -> `ollama/glm/glm-4.7-flash-bf16`: Hosted locally via llama-swap. Needs --jinja --reasoning-format none to suppress <think> tags in content. Tool calling works correctly with these flags.
- `llama4_scout` -> `ollama/meta/llama4-scout`: Hosted locally via llama-swap. Skipped by default: llama.cpp has no parser for Llama 4's pythonic tool call format — model outputs tool calls as plain text content instead of structured tool_calls. Requires upstream llama.cpp support (similar to vLLM's llama4_pythonic parser).
- `qwen3_32b` -> `ollama/qwen/qwen3-32b`: Requested local model family; exact hosted variant available through opencode. Superseded by the Qwen 3.5 line for future local benchmarking. Skipped by default after benchmark preview averaged 7.96 output tok/s over the first 3 steps (< 20.00).
- `qwen3_coder_next` -> `ollama/qwen/qwen3-coder-next`: Best direct coding-oriented local Qwen variant matching the original benchmark brief. Skipped by default after benchmark preview measured 6.59 output tok/s (< 20.00).
- `qwen3_5_35b` -> `ollama/qwen/qwen3.5-35b`: Requested local model family; exact hosted variant available through opencode. Skipped by default because the current benchmark pass is restricted to OpenRouter models that previously completed successfully.
- `qwen3_6_35b` -> `ollama/qwen/qwen3.6-35b`: Qwen 3.6 35B-A3B (released 2026-04-15). Same qwen3_5_moe architecture as 3.5 (35B total / 3B active MoE). Q3_K_M ~16 GB — drop-in replacement for 3.5. Significant benchmark gains: SWE-bench 73.4 (was 70), Terminal-Bench 51.5 (was 40.5), MCPMark 37 (was 27). Has vision encoder. Same chat template and llama.cpp flags as 3.5.
- `qwen3_5_122b` -> `ollama/qwen/qwen3.5-122b`: Hosted locally via llama-swap. Needs --reasoning-format none on llama-server to avoid reasoning_content tokens that some clients mishandle. Tool calling works correctly with Qwen chat template.
- `gpt_oss_20b` -> `ollama/openai/gpt-oss-20b`: Added as a local Ollama GPT OSS baseline for later warmup and benchmark testing.
- `nemotron_cascade_2` -> `ollama/nemotron_cascade_2`: Added as a local Ollama Nemotron Cascade 2 candidate for later warmup and benchmark testing. This entry uses explicit local model metadata because it is not yet mapped in the home opencode config.
- `claude_opus_4_6` -> `openrouter/anthropic/claude-opus-4.6`: Exact requested cloud model.
- `claude_opus_4_7` -> `openrouter/anthropic/claude-opus-4.7`: Anthropic Claude Opus 4.7 on OpenRouter. Built for long-running async agents. Same pricing as 4.6: $5/M input, $25/M output. 1M context, 128K max output. Released 2026-04-16.
- `gpt_5_4_pro` -> `openrouter/openai/gpt-5.4-pro`: Chosen from the OpenRouter GPT 5.4 family as the largest and most coding-oriented variant. Skipped by default because it failed in the previous benchmark pass.
- `gpt_5_4_codex` -> `gpt-5.4`: GPT 5.4 via Codex CLI (codex exec) at xhigh reasoning effort. Bypasses OpenRouter — uses OpenAI API directly. Required because GPT 5.4 does not support tool calling through OpenRouter, causing opencode to stall.
- `kimi_k2_5` -> `openrouter/moonshotai/kimi-k2.5`: Chosen as the latest/highest Kimi variant listed by OpenRouter locally.
- `glm_5` -> `openrouter/z-ai/glm-5`: Chosen as the latest/highest GLM variant listed by OpenRouter locally; this replaces the local GLM test. Skipped by default because it completed with errors in the previous benchmark pass.
- `qwen3_6_plus` -> `openrouter/qwen/qwen3.6-plus:free`: Added from OpenRouter cloud availability; chose the non-preview Qwen 3.6 Plus variant exposed locally. Skipped by default because it completed with errors in the previous benchmark pass.
- `qwen3_5_397b_cloud` -> `openrouter/qwen/qwen3.5-397b-a17b`: Added as the OpenRouter cloud Qwen 3.5 flagship under the requested qwen3.5:397b-cloud benchmark slot. Skipped by default because it stalled after completing validation steps and never emitted a terminal stop.
- `gemma4_31b_cloud` -> `openrouter/google/gemma-4-31b-it`: Google Gemma 4 31B IT BF16 served via Ollama's hosted cloud (https://ollama.com). Originally added to bypass the local llama.cpp parser bugs that caused infinite repetition loops on local Q3/Q8 GGUFs. Curl tests confirm the model itself works correctly for tool calling. **However, opencode benchmark runs hit HTTP 504 Gateway Timeout consistently around 20-24K total tokens of conversation history** — Cloudflare edge appears to enforce a ~100s per-request limit which 20K+ token prefill exceeds. Tried maxRetries:5 (didn't help — failures are consistent, not transient). Set limit.context:16384 to force opencode history trimming below the wall. Skipped by default until either Ollama Cloud raises the timeout or we test via Google's native Gemini API. Requires OLLAMA_API_KEY env var with Ollama Cloud subscription.
- `llama4_scout_cloud` -> `openrouter/meta-llama/llama-4-scout`: Added as the OpenRouter cloud Llama 4 Scout benchmark counterpart to the unusable local Scout path. Skipped by default because it does not currently resolve cleanly in this opencode build.
- `nemotron_3_super_cloud` -> `openrouter/nvidia/nemotron-3-super-120b-a12b`: Added as the closest OpenRouter cloud Nemotron line available after local Nemotron Cascade 2 proved unusable in this harness. Skipped by default because it still needs a clean first benchmark run.
- `minimax_m2_7` -> `openrouter/minimax/minimax-m2.7`: Chosen as the largest/latest MiniMax variant listed by OpenRouter locally.
- `deepseek_v3_2` -> `openrouter/deepseek/deepseek-v3.2`: Latest DeepSeek model on OpenRouter. Input $0.26/M, output $0.38/M.
- `step_3_5_flash` -> `openrouter/stepfun/step-3.5-flash`: StepFun Step 3.5 Flash on OpenRouter. Input $0.10/M, output $0.30/M.
- `claude_sonnet_4_6` -> `openrouter/anthropic/claude-sonnet-4.6`: Anthropic Claude Sonnet 4.6 on OpenRouter. Input $3.00/M, output $15.00/M.
- `gemini_3_1_pro` -> `openrouter/google/gemini-3.1-pro-preview`: Latest Google Gemini model with enhanced SWE performance and agentic reliability. Input $2.00/M, output $12.00/M.
- `grok_4_20` -> `openrouter/x-ai/grok-4.20`: xAI's latest flagship on OpenRouter. Fastest model in the benchmark (8 min) but produced architecturally broken code: bypassed RubyLLM with ruby-openai (only in dev/test group, NameError in prod), used format.turbo_stream without installing turbo-rails, RUBY_VERSION=4.0.2 Dockerfile bug. Tier 3 — broken core.
- `glm_5_1` -> `zai/glm-5.1`: Z.ai's latest flagship GLM model. Uses Z.ai coding plan endpoint at https://api.z.ai/api/coding/paas/v4 (NOT the general /api/paas/v4) — Lite subscription includes glm-5.1 only via the coding endpoint. Completed in 22 min with 24 tests, correct primary RubyLLM.chat/ask usage, but invented chat.user/chat.assistant for multi-turn history seeding (single-turn works, multi-turn crashes). Tier 2 — works with caveats.
- `qwen3_5_27b_claude` -> `ollama/qwen/qwen3.5-27b-claude`: Qwen 3.5 27B distilled from Claude 4.6 Opus reasoning traces (Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled). Tests whether Claude reasoning distillation transfers RubyLLM API correctness — most non-Anthropic models hallucinate the gem's API, so a Claude-distilled Qwen is an interesting natural experiment.
- `qwen2_5_coder_32b` -> `ollama/qwen/qwen2.5-coder-32b`: Most popular dedicated coder of the Qwen 2.5 generation. Sourced from Ollama (Q4_K_M ~19 GB). On NVIDIA 5090 fits with 64K context.
- `qwen3_coder_30b` -> `ollama/qwen/qwen3-coder-30b`: Qwen 3 dedicated coder variant (the regular 30B, not the 51 GB qwen3-coder-next-ctx). Direct comparison with the general qwen3:32b. Sourced from Ollama (Q4_K_M ~18 GB).
- `qwen3_5_27b_sushi_coder` -> `ollama/qwen/qwen3.5-27b-sushi-coder`: Qwen 3.5 27B fine-tuned via reinforcement learning on Codeforces problems (bigatuna/Qwen3.5-27b-Sushi-Coder-RL). Q4_K_M ~15 GB. Tests whether RL coding fine-tuning transfers correct RubyLLM API usage — direct comparison with the Claude reasoning distillation (qwen3.5:27b-claude) and the general qwen3.5:35b.
- `gemma4_31b_cloud` -> `ollama-cloud/gemma4-31b`: Google Gemma 4 31B IT BF16 served via Ollama's hosted cloud (https://ollama.com). Bypasses the local llama.cpp parser bugs that caused infinite repetition loops on local Q3/Q8 GGUFs. Tests whether Gemma 4 is actually capable for agentic tool calling when served by Google's full-precision infrastructure rather than crippled by quantization + parser regressions. Requires OLLAMA_API_KEY env var with an Ollama Cloud subscription.

## Results

| Model | Provider | Warmup ctx | Status | Elapsed (s) | Total tokens | Tok/s | Works? | Files | Notes |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |
| Gemma 4 31B | ollama | - | failed | 364.15 | - | - | no | 1277 | Generated files do not resemble the requested Rails project. |
| GLM 4.7 Flash BF16 | ollama | - | failed | 1208.80 | 41709 | 34.50 | yes | 2029 | Exit code -15. Rails app, tests, README, and container files detected. |
| Llama 4 Scout | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3 32B | ollama | - | completed_with_errors | 1271.45 | 22922 | 18.03 | no | 87 | Generated files do not resemble the requested Rails project. |
| Qwen 3 Coder Next | ollama | - | completed | 1041.72 | 39054 | 37.49 | yes | 1675 | Rails app, tests, README, and container files detected. |
| Qwen 3.5 35B | ollama | - | completed | 1671.20 | 76919 | 46.03 | yes | 1478 | Rails app, tests, README, and container files detected. |
| Qwen 3.6 35B | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3.5 122B | ollama | - | completed | 2564.18 | 57472 | 22.41 | yes | 1503 | Rails app, tests, README, and container files detected. |
| GPT OSS 20B | ollama | - | failed | 609.59 | 32553 | 53.40 | no | 1310 | Generated files do not resemble the requested Rails project. |
| Nemotron Cascade 2 | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Claude Opus 4.6 | openrouter | - | completed | 970.51 | 136806 | 347.18 | yes | 1536 | Rails app, tests, README, and container files detected. |
| Claude Opus 4.7 | openrouter | - | completed | 1091.67 | 118216 | 328.24 | yes | 11345 | Rails app, tests, README, and container files detected. |
| GPT 5.4 Pro | openrouter | - | failed | 2910.65 | 63491 | 21.81 | partial | 1118 | Exit code -15. Some expected benchmark artifacts exist, but the scaffold looks incomplete. |
| GPT 5.4 xHigh (Codex) | codex | - | completed | 1312.34 | 7643800 | 5824.56 | yes | 1808 | Rails app, tests, README, and container files detected. |
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
| Gemini 3.1 Pro | openrouter | - | completed | 811.00 | 104034 | 508.18 | yes | 138 | Rails app, tests, README, and container files detected. |
| Grok 4.20 | openrouter | - | completed | 502.68 | 63457 | 412.54 | yes | 108 | Rails app, tests, README, and container files detected. |
| GLM 5.1 | zai | - | completed | 1291.19 | 81666 | 166.62 | yes | 1571 | Rails app, tests, README, and container files detected. |
| Qwen 3.5 27B Claude Distilled | ollama | - | timeout | 5400.95 | 75753 | 14.03 | partial | 2231 | Timed out. Some expected benchmark artifacts exist, but the scaffold looks incomplete. |
| Qwen 2.5 Coder 32B | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3 Coder 30B | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3.5 27B Sushi Coder RL | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Gemma 4 31B (Ollama Cloud) | ollama-cloud | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |

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

