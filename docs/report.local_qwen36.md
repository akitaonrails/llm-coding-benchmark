# Benchmark Report

Generated at: 2026-06-18T14:42:49+00:00
Prompt SHA256: `d25f119447215ebf47477c1ce61b24f801bfcb9336467f5b019d554f3c83537c`

## Progress

- `completed`: 2
- `completed_with_errors`: 0
- `failed`: 0
- `timeout`: 0
- `not_run`: 1

## Runner

`opencode run --agent build --format json`

- ik_llama.cpp local server profile. Models served by an ik_llama.cpp Docker container on localhost:8000 with an OpenAI-compatible /v1 endpoint and a custom llamacpp provider in the generated benchmark config.

## Model Selection

- `qwen3_6_35b_a3b_q8_ik_llamacpp` -> `llamacpp/Qwen3.6-35B-A3B`: Remote-provider-style benchmark of Qwen 3.6 35B A3B Q8_0.gguf served by an ik_llama.cpp Docker container on localhost:8000. First GPU is capped to 200W to limit thermals, so inference speed is not representative of the hardware. Skipped by default because it requires a third-party local backend.
- `qwen3_6_35b_a3b_ud_q5_k_m_ik_llamacpp` -> `llamacpp/Qwen3.6-35B-A3B`: Remote-provider-style benchmark of Qwen 3.6 35B A3B UD-Q5_K_M.gguf served by an ik_llama.cpp Docker container on localhost:8000. First GPU is capped to 200W to limit thermals, so inference speed is not representative of the hardware. Skipped by default because it requires a third-party local backend.
- `qwen3_6_35b_a3b_q6_k_ik_llamacpp` -> `llamacpp/Qwen3.6-35B-A3B`: Remote-provider-style benchmark of Qwen 3.6 35B A3B Q6_K.gguf served by an ik_llama.cpp Docker container on localhost:8000. First GPU is capped to 200W to limit thermals, so inference speed is not representative of the hardware. Skipped by default because it requires a third-party local backend.

## Results

| Model | Provider | Warmup ctx | Status | Elapsed (s) | Total tokens | Tok/s | Works? | Files | Notes |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |
| Qwen 3.6 35B A3B Q8 (ik_llama.cpp localhost) | llamacpp | - | completed | 926.78 | 76784 | 82.85 | yes | 179 | Rails app, tests, README, and container files detected. |
| Qwen 3.6 35B A3B UD-Q5_K_M (ik_llama.cpp localhost) | llamacpp | - | completed | 1201.73 | 118742 | 98.81 | yes | 87 | Rails app, tests, README, and container files detected. |
| Qwen 3.6 35B A3B Q6_K (ik_llama.cpp localhost) | llamacpp | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |

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

