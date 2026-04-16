# Benchmark Report

Generated at: 2026-04-16T23:17:27+00:00
Prompt SHA256: `d25f119447215ebf47477c1ce61b24f801bfcb9336467f5b019d554f3c83537c`

## Progress

- `completed`: 3
- `completed_with_errors`: 3
- `failed`: 1
- `timeout`: 1
- `not_run`: 1

## Runner

`opencode run --agent build --format json`

- Selected after local probing because it exposes machine-readable JSON events with session IDs and token counts.
- The local crush install advertised --yolo in help output but rejected the flag at runtime, which makes it a poor default for unattended benchmarking here.
- The explicit build agent has permissive filesystem/tool rules, which is the closest match to the requested autonomous coding workflow.

## Model Selection

- `gemma4_31b` -> `ollama/google/gemma4-31b-it-bf16`: Hosted locally via llama-swap. Requires llama.cpp b8665+ for the dedicated Gemma 4 tool call parser (PR #21418). Skipped by default; re-enable for llama-swap benchmark runs. [NVIDIA RTX 5090 profile: ctx capped to fit 32 GB VRAM]
- `qwen3_32b` -> `ollama/qwen/qwen3-32b`: Requested local model family; exact hosted variant available through opencode. Superseded by the Qwen 3.5 line for future local benchmarking. Skipped by default after benchmark preview averaged 7.96 output tok/s over the first 3 steps (< 20.00). [NVIDIA RTX 5090 profile: ctx capped to fit 32 GB VRAM]
- `qwen3_5_35b` -> `ollama/qwen/qwen3.5-35b`: Requested local model family; exact hosted variant available through opencode. Skipped by default because the current benchmark pass is restricted to OpenRouter models that previously completed successfully. [NVIDIA RTX 5090 profile: ctx capped to fit 32 GB VRAM]
- `qwen3_6_35b` -> `ollama/qwen/qwen3.6-35b`: Qwen 3.6 35B-A3B (released 2026-04-15). Same qwen3_5_moe architecture, Q3_K_M ~16 GB — identical VRAM footprint as 3.5. Significant benchmark gains over 3.5. [NVIDIA RTX 5090 profile: ctx 131072 to fit 32 GB VRAM]
- `gpt_oss_20b` -> `ollama/openai/gpt-oss-20b`: GPT OSS 20B (HF Q3_K_M) on llama-swap. **Skipped on NVIDIA profile**: current llama.cpp main has a regression in the harmony tool-call autoparser. Both with and without --reasoning-format none, the parser errors on multi-turn tool call patterns like 'commentary to=<|tool_name|>...' that gpt-oss emits. On the older llama.cpp build (b8643) used by the AMD server profile, gpt-oss completed 51 tool-calling steps successfully (model failed there for a different reason — created Rails app under project/app/ instead of project/). Re-enable when llama.cpp adds a dedicated peg-gpt-oss / harmony tool call parser (similar to the peg-gemma4 fix in PR #21418).
- `qwen3_5_27b_claude` -> `ollama/qwen/qwen3.5-27b-claude`: Qwen 3.5 27B distilled from Claude 4.6 Opus reasoning traces (Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled). Tests whether Claude reasoning distillation transfers RubyLLM API correctness — most non-Anthropic models hallucinate the gem's API, so a Claude-distilled Qwen is an interesting natural experiment. [NVIDIA RTX 5090 profile: ctx capped to fit 32 GB VRAM]
- `qwen2_5_coder_32b` -> `ollama/qwen/qwen2.5-coder-32b`: Most popular dedicated coder of the Qwen 2.5 generation. Sourced from Ollama (Q4_K_M ~19 GB). On NVIDIA 5090 fits with 64K context. [NVIDIA RTX 5090 profile]
- `qwen3_coder_30b` -> `ollama/qwen/qwen3-coder-30b`: Qwen 3 dedicated coder variant (the regular 30B, not the 51 GB qwen3-coder-next-ctx). Direct comparison with the general qwen3:32b. Sourced from Ollama (Q4_K_M ~18 GB). [NVIDIA RTX 5090 profile]
- `qwen3_5_27b_sushi_coder` -> `ollama/qwen/qwen3.5-27b-sushi-coder`: Qwen 3.5 27B fine-tuned via reinforcement learning on Codeforces problems (bigatuna/Qwen3.5-27b-Sushi-Coder-RL). Q4_K_M ~15 GB. Tests whether RL coding fine-tuning transfers correct RubyLLM API usage — direct comparison with the Claude reasoning distillation (qwen3.5:27b-claude) and the general qwen3.5:35b. [NVIDIA RTX 5090 profile]

## Results

| Model | Provider | Warmup ctx | Status | Elapsed (s) | Total tokens | Tok/s | Works? | Files | Notes |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |
| Gemma 4 31B | ollama | - | completed_with_errors | 511.94 | 108962 | 212.84 | no | 1288 | Generated files do not resemble the requested Rails project. |
| Qwen 3 32B | ollama | - | completed_with_errors | 261.75 | 18185 | 69.47 | no | 1134 | Generated files do not resemble the requested Rails project. |
| Qwen 3.5 35B | ollama | - | completed | 307.68 | 84158 | 273.52 | yes | 128 | Rails app, tests, README, and container files detected. |
| Qwen 3.6 35B | ollama | - | completed | 282.31 | 67946 | 240.68 | yes | 169 | Rails app, tests, README, and container files detected. |
| GPT OSS 20B | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3.5 27B Claude Distilled | ollama | - | completed | 735.48 | 94865 | 128.98 | yes | 1662 | Rails app, tests, README, and container files detected. |
| Qwen 2.5 Coder 32B | ollama | - | timeout | 5400.14 | 15421 | 2.86 | no | 0 | Timed out. Project directory is empty. |
| Qwen 3 Coder 30B | ollama | - | completed_with_errors | 348.47 | 50609 | 145.23 | no | 1333 | Generated files do not resemble the requested Rails project. |
| Qwen 3.5 27B Sushi Coder RL | ollama | - | failed | 361.23 | - | - | no | 0 | Project directory is empty. |

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

