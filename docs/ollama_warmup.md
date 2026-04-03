# Ollama Warmup Report

Generated at: 2026-04-03T20:12:24+00:00
Minimum useful context target: `32768`
Maximum practical context tested: `262144`
Per-attempt timeout: `180` seconds

| Model | Ollama name | Config ctx | Highest verified ctx | Recommendation |
| --- | --- | ---: | ---: | --- |
| gemma4_31b | `gemma4:31b-it-bf16` | 262144 | 131072 | keep in benchmark at 131072 |
| glm_4_7_flash_bf16 | `glm-4.7-flash:bf16` | 202752 | 202752 | keep in benchmark at 202752 |
| gpt_oss_20b | `gpt-oss:20b` | 131072 | 131072 | keep in benchmark at 131072 |
| llama4_scout | `llama4:scout` | 10485760 | 131072 | keep in benchmark at 131072 |
| nemotron_cascade_2 | `nemotron-cascade-2:latest` | 262144 | 262144 | keep in benchmark at 262144 |
| qwen3_32b | `qwen3:32b` | 40960 | 40960 | keep in benchmark at 40960 |
| qwen3_5_122b | `qwen3.5:122b` | 262144 | 262144 | keep in benchmark at 262144 |
| qwen3_5_35b | `qwen3.5:35b` | 262144 | 262144 | keep in benchmark at 262144 |
| qwen3_5_coder_122b | `mdq100/qwen3.5-coder:122b` | 262144 | 262144 | keep in benchmark at 262144 |
| qwen3_5_coder_35b | `mdq100/qwen3.5-coder:35b` | 262144 | 262144 | keep in benchmark at 262144 |
| qwen3_coder_next | `qwen3-coder-next:latest` | 262144 | 262144 | keep in benchmark at 262144 |

## Attempt Log

### gemma4_31b

- `num_ctx=262144`: fail: model failed to load, this may be due to resource limitations or an internal error, check ollama server logs for details
- `num_ctx=131072`: ok in 29.48s

### glm_4_7_flash_bf16

- `num_ctx=202752`: ok in 30.22s

### gpt_oss_20b

- `num_ctx=131072`: ok in 6.19s

### llama4_scout

- `num_ctx=262144`: fail: model failed to load, this may be due to resource limitations or an internal error, check ollama server logs for details
- `num_ctx=131072`: ok in 58.18s

### nemotron_cascade_2

- `num_ctx=262144`: ok in 4.20s

### qwen3_32b

- `num_ctx=40960`: ok in 7.87s

### qwen3_5_122b

- `num_ctx=262144`: ok in 22.46s

### qwen3_5_35b

- `num_ctx=262144`: ok in 7.84s

### qwen3_5_coder_122b

- `num_ctx=262144`: ok in 23.37s

### qwen3_5_coder_35b

- `num_ctx=262144`: ok in 9.64s

### qwen3_coder_next

- `num_ctx=262144`: ok in 11.95s

