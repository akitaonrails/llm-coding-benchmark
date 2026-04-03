# AGENTS

## Benchmark Retry Hygiene

- Before retrying a stuck benchmark, check for stale `run_benchmark.py` and `opencode` worker processes and kill them if they are still alive.
- Stale benchmark workers can keep remote Ollama models resident and interfere with unload/reload behavior on the server.
- If Ollama appears to have the wrong model loaded or ignores a fresh retry, inspect and clear old benchmark-related processes first.
