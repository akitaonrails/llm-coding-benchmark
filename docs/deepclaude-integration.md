# deepclaude Integration

**Source**: https://github.com/aattaran/deepclaude

## What it is

deepclaude is a shell-script shim for Claude Code that swaps the underlying API target. It sets a few env vars (`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_DEFAULT_*_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL`), launches Claude Code, and on exit restores the originals. Claude Code never knows it's not talking to Anthropic — its full agent loop (file editing, bash, subagent spawning, multi-step tool use) runs unchanged on top of whatever Anthropic-compatible endpoint the shim points at.

Supported backends:
- **DeepSeek** direct (`api.deepseek.com/anthropic`) — needs `DEEPSEEK_API_KEY`
- **OpenRouter** (`openrouter.ai/api`) — needs `OPENROUTER_API_KEY` (we already have this)
- **Fireworks AI** (`api.fireworks.ai/inference`) — needs `FIREWORKS_API_KEY`
- **Anthropic** (no override, normal Claude Code)

## Why we wired it in

Round 3 of this benchmark established that DeepSeek V4 Pro is **structurally unmeasurable** through opencode in any multi-turn dispatch configuration: the model returns `reasoning_content` blocks that opencode's ai-sdk does not echo back in subsequent requests, so DeepSeek's API rejects every turn after the first with a 400. Three different opencode `reasoning` configs (`true`, `false`, absent) all reproduced the same wire-level failure. See [`results/manual_opus_deepseek/orchestration_trace.md`](../results/manual_opus_deepseek/orchestration_trace.md) for the failed-attempt log.

deepclaude uses a different Anthropic-compatible endpoint (the OpenRouter `/anthropic` route, or DeepSeek's own native `/anthropic` route) that handles thinking-mode content correctly for Claude Code's request shape. This finally gives us a way to run DeepSeek V4 Pro inside a real autonomous coding agent loop and benchmark it apples-to-apples against the Claude Code Opus 4.7 baseline.

## Install

The shim is a single shell script:

```bash
git clone https://github.com/aattaran/deepclaude /home/akitaonrails/Projects/deepclaude
ln -sf /home/akitaonrails/Projects/deepclaude/deepclaude.sh ~/.local/bin/deepclaude
chmod +x /home/akitaonrails/Projects/deepclaude/deepclaude.sh
deepclaude --status   # Confirms which backend keys are detected
```

For our benchmark integration, we DO NOT actually invoke the `deepclaude` script. Instead we replicate its env-var injection inside `scripts/benchmark/claude_code_runner.py` — that lets us run the same Claude Code subprocess pipeline we already use for `claude_opus_alone` / `claude_opus_sonnet` / `claude_opus_haiku`, with just the env vars swapped per variant.

## How it's wired into our benchmark

### Runner patch

`scripts/benchmark/claude_code_runner.py` now honors an optional `env_overrides` dict on each variant. The shape:

```json
{
  "env_overrides": {
    "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
    "ANTHROPIC_AUTH_TOKEN": "$OPENROUTER_API_KEY",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek/deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek/deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek/deepseek-v4-pro",
    "CLAUDE_CODE_SUBAGENT_MODEL": "deepseek/deepseek-v4-pro",
    "UNSET:ANTHROPIC_API_KEY": ""
  }
}
```

Conventions:
- A value starting with `$` is an indirect lookup in the parent env (`$OPENROUTER_API_KEY` resolves to whatever's in the user's shell). This keeps secrets out of `config/*.json`.
- A key starting with `UNSET:` removes the named variable from the subprocess env (used to drop `ANTHROPIC_API_KEY` when swapping to a non-Anthropic backend, otherwise the SDK might prefer it over `ANTHROPIC_AUTH_TOKEN`).
- Everything else is a literal string set in the subprocess env.

The runner logs which overrides were applied (with masked secret values) at the start of each variant so the benchmark output captures the full setup.

### New variants in `config/claude_code_models.json`

| Slug | Backend | Subagent | Notes |
|---|---|---|---|
| `claude_code_deepseek_v4_pro_or` | OpenRouter → DeepSeek V4 Pro | none | DeepSeek runs the entire Claude Code loop (planner + executor + subagent dispatcher) |
| `claude_code_deepseek_v4_pro_or_sonnet` | OpenRouter → DeepSeek V4 Pro for main loop, Anthropic API → Claude Sonnet 4.6 for subagent | sonnet-coder | Asymmetric pairing: DeepSeek as planner-orchestrator, Sonnet as implementation subagent |

Both are `skip_by_default` style — they only run when explicitly requested via `--variant <slug>`.

## Live smoke test (verified working)

```bash
$ ANTHROPIC_BASE_URL=https://openrouter.ai/api \
  ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY" \
  ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek/deepseek-v4-pro" \
  ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek/deepseek-v4-pro" \
  ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek/deepseek-v4-pro" \
  ANTHROPIC_API_KEY="" \
  HOME=/tmp/deepclaude_smoke \
  claude -p --dangerously-skip-permissions \
    "Reply with exactly the word PONG and nothing else." \
    --output-format json
```

Output (excerpt):
```
"modelUsage":{"deepseek/deepseek-v4-pro":{"inputTokens":21052,"outputTokens":54,
              "cacheReadInputTokens":2432,"costUSD":0.107826,...}}
```

This confirms:
- Claude Code authenticated against OpenRouter using `OPENROUTER_API_KEY`
- The request was routed to DeepSeek V4 Pro via OpenRouter's `/anthropic` shape
- Claude Code's `result.json` correctly attributes tokens + cost to the `deepseek/deepseek-v4-pro` model

## Running a benchmark variant

```bash
python scripts/run_claude_code_benchmark.py \
  --variant claude_code_deepseek_v4_pro_or \
  --no-progress-minutes 15
```

(The standardized 15-min watchdog from Round 2.5 is recommended because Claude Code's autonomous loop with a non-default backend may have slower first-call latency.)

## Caveats from the deepclaude README + our integration

1. **No image input**: DeepSeek's Anthropic endpoint doesn't support vision. Our benchmark prompt is text-only so this is not a problem here.
2. **No MCP server tools**: not supported through the compatibility layer. Our benchmark doesn't use MCP.
3. **Anthropic prompt caching with `cache_control` is ignored**: DeepSeek has its own automatic caching but the explicit cache markers Claude Code emits get dropped. Cost will be higher per turn than the comparable Anthropic run because of this — relevant for cost comparisons.
4. **Asymmetric variant gotcha**: `claude_code_deepseek_v4_pro_or_sonnet` assumes that when Claude Code spawns the `sonnet-coder` subagent, it uses the subagent's own model name (`claude-sonnet-4-6`) which routes to Anthropic, NOT to OpenRouter. If Claude Code reuses `ANTHROPIC_AUTH_TOKEN` for the subagent spawn too, Sonnet would route through OpenRouter and likely fail. **This needs empirical verification on the first run** — see the `selection_reason` field in the variant config.

## What the new variants will measure

Once benchmarked, these variants close important gaps in the benchmark:

- **Solo DeepSeek V4 Pro inside Claude Code**: directly comparable to `claude_opus_alone` (same harness, different model). Tests whether DeepSeek's "96.4% LiveCodeBench" claim translates to greenfield Rails work in the Claude Code agent loop, or whether it has the same RubyLLM API recall failures we saw in DeepSeek V4 Flash / V3.2.
- **DeepSeek planner + Sonnet executor**: tests whether a non-Anthropic planner can drive the same constraint-via-prescriptive-prompts mechanism that lifted GLM 5.1 +47, Qwen 3.6 Plus +23, Kimi K2.6 +10 in earlier rounds. This would settle whether "the planner has to be Opus" is fundamental or just incidental to those experiments.
