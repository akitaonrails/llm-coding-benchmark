# Local Provider Status

Last checked: 2026-06-13.

## Homeserver: 192.168.0.90

### Ollama (`http://192.168.0.90:11434`)

Reachable.

Models listed by `/api/tags`:

- `qwen3:32b`
- `nomic-embed-text:latest`

MiniMax probe result: not present. Checked likely tags with `/api/show`:

- `minimax-m3`
- `minimax:m3`
- `minimax/minimax-m3`
- `minimax-v3`
- `minimax-v3:latest`
- `minimax-m3:latest`

All returned 404 / model not found.

### llama-swap (`http://192.168.0.90:11435/v1`)

Reachable and OpenAI-compatible. `/running` reported no active model at check time.

Configured models:

- `deepseek-coder-v2:16b`
- `deepseek-coder:33b`
- `deepseek-r1:32b`
- `deepseek-r1:70b`
- `gemma4:27b`
- `glm-4.7-flash:q8`
- `gpt-oss:20b`
- `llama3.3:70b`
- `llama4:scout`
- `phi4-reasoning:latest`
- `phi4-reasoning:plus`
- `phi4:latest`
- `qwen2.5-coder:14b`
- `qwen2.5-coder:32b`
- `qwen2.5:72b`
- `qwen3-coder:30b`
- `qwen3.5:122b`
- `qwen3.5:27b-claude`
- `qwen3.5:35b`
- `qwen3:14b`
- `qwen3:32b`

MiniMax/Kimi/Moonshot probe result: no configured entries matched those names.

### vLLM-like service (`http://192.168.0.90:8080`)

Reachable but protected. `/running` and `/v1/models` return 401 without the correct authorization token.

Checked available environment variables without printing values:

- `VLLM_API_KEY`: unset
- `LOCAL_API_KEY`: unset
- `OPENAI_API_KEY`: set, rejected with 401
- `OPENROUTER_API_KEY`: set, rejected with 401
- `OLLAMA_API_KEY`: set, rejected with 401

Current blocker for local MiniMax V3 testing: the vLLM service may exist on `:8080`, but this workspace does not have the authorization token needed to list or run models there. MiniMax V3 is not currently visible through Ollama or llama-swap.

## Kimi K2.7 Code

OpenRouter lists the new model as `moonshotai/kimi-k2.7-code` with 262K context and tool-calling support. It has been added to `config/models.json` as `kimi_k2_7_code` and successfully completed the two-phase benchmark via OpenRouter.

Key result:

- Status: `completed`
- Runtime: 1295.74 seconds
- Tokens: 86,967 total
- Artifacts: 1,687 files
- Phase 2: local boot, live OpenRouter chat, Docker build, Docker Compose boot, Docker Compose live chat, and `bin/ci` all passed

Important harness fix from this run: opencode needed an explicit `--dir <absolute project_dir>` argument. `cwd` alone was insufficient in this environment and let the first K2.7 attempt create files in the repository-level placeholder `llm-chat/` directory instead of `results/kimi_k2_7_code/project`. The runner now passes `--dir` for opencode runs.
