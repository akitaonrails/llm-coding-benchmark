# llama.cpp Notes

This file records what we learned while evaluating whether to replace local Ollama serving with `llama.cpp` for `opencode`.

## Short Answer

Yes, `opencode` can talk to a remote `llama.cpp` server.

The relevant shape is:

- run `llama-server` on the model host
- expose its OpenAI-compatible HTTP API
- point a custom `opencode` provider at that `/v1` base URL

## Why This Matters Here

The current local Ollama path was unreliable for unattended coding benchmarks on this hardware. The main failure patterns were:

- load succeeds, but the first real streamed request fails later
- `opencode` waits forever for the first output chunk
- model unload and context behavior are inconsistent after retries
- some custom local models fail with `ProviderModelNotFoundError` in `opencode`

Those are strong reasons to test a more direct OpenAI-compatible local server.

## Expected `opencode` Shape

`opencode` supports custom OpenAI-compatible providers. A `llama.cpp` provider can be configured like this:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "llamacpp": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "llama.cpp (server)",
      "options": {
        "baseURL": "http://192.168.0.90:8080/v1"
      },
      "models": {
        "qwen-coder-local": {
          "name": "Qwen Coder Local",
          "limit": {
            "context": 65536,
            "output": 8192
          }
        }
      }
    }
  }
}
```

With that config, the model would be selected in `opencode` as:

```text
llamacpp/qwen-coder-local
```

## Expected `llama.cpp` Server Shape

On the model host, the basic pattern is:

```bash
llama-server -m /path/to/model.gguf --port 8080 -c 65536
```

The important pieces are:

- use a `GGUF` model that is known to behave well in chat mode
- keep the context realistic for the hardware
- verify the server actually responds through its OpenAI-compatible `/v1/chat/completions` path before involving `opencode`

## Practical Advice For This Repo

- Prefer coding-tuned GGUF models with good chat-template support.
- Treat tool-calling support as a hard requirement if the goal is agentic coding in `opencode`.
- Start with a modest context window and increase only after proving stable first-token behavior.
- Validate the server directly with a tiny request before running the benchmark harness.
- Keep the benchmark-local `opencode` config generation model-specific so the repo can switch between OpenRouter, Ollama, and `llama.cpp` cleanly.

## What To Test First

If local serving is still the goal, the next sensible experiment is:

1. stand up `llama-server` on `192.168.0.90`
2. add one custom `llamacpp` provider entry to the generated benchmark config
3. test one coding-oriented model only
4. verify that `opencode` receives the first stream chunk reliably
5. only then add it back into the benchmark rotation

## Bottom Line

`llama.cpp` is a viable local serving path for this benchmark. It is not guaranteed to make oversized models fast on the current hardware, but it gives cleaner control over the server path than the current Ollama setup and is worth testing next if local agentic coding remains a requirement.
