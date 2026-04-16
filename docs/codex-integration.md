# Codex CLI Integration

This document covers the integration of OpenAI's **Codex CLI** (`codex exec`) as an alternative runner alongside `opencode run` for benchmarking GPT 5.4 models that can't run through OpenRouter (no tool calling support there).

## Why Codex?

GPT 5.4 through OpenRouter fails in opencode because OpenRouter doesn't expose tool calling for the model. The opencode agent stalls after the first assistant turn with no tool calls being issued. Codex CLI is OpenAI's own agentic coding tool (their equivalent of Claude Code) and talks directly to the OpenAI API, bypassing OpenRouter entirely.

## Installation

```bash
npm install -g @openai/codex
# or: the user may have a shell wrapper at ~/.local/bin/codex
```

Auth: `OPENAI_API_KEY` env var (not ChatGPT account login).

## How It's Wired

Models opt into the Codex runner via `"runner_type": "codex"` in `config/models.json`. When absent, the default runner is `"opencode"`. The dispatch happens in `run_model()` inside `scripts/benchmark/runner.py`.

```json
{
  "slug": "gpt_5_4_codex",
  "id": "gpt-5.4",
  "label": "GPT 5.4 xHigh (Codex)",
  "provider": "codex",
  "runner_type": "codex",
  "codex_reasoning_effort": "xhigh"
}
```

The benchmark command is identical:

```bash
python scripts/run_benchmark.py --model gpt_5_4_codex --force
```

## Hurdles and Fixes

### 1. `codex` binary is a shell wrapper, not a binary

The `codex` installed via npm is actually a bash script:

```bash
#!/bin/bash
exec npx --yes @openai/codex "$@"
```

This means it depends on `npx` being in the PATH, which requires the Node.js environment (mise, nvm, etc.) to be activated. When spawned from `subprocess.Popen` with `start_new_session=True`, the shell environment may not propagate correctly.

**Fix:** Wrap the codex command in `bash -lc` to get a login shell that activates mise/node:

```python
cmd = ["bash", "-lc", " ".join(shlex_quote(a) for a in codex_args)]
```

### 2. Relative path in `-C` flag causes ENOENT

The benchmark's `BenchmarkConfig.results_dir` is a relative `Path` (e.g., `results/gpt_5_4_codex/project`). When passed to codex's `-C` flag AND used as subprocess `cwd`, the path gets double-nested: codex cd's into `project/` then tries to `-C results/gpt_5_4_codex/project` relative to that, resulting in a non-existent path.

The error is cryptic: just `Error: No such file or directory (os error 2)` on stderr with no further context. Codex keeps the process alive but produces no JSON stdout, causing the benchmark to stall until the no-progress timeout.

**Fix:** Resolve to absolute path before passing to `-C`:

```python
"-C", str(project_dir.resolve()),
```

And also resolve the subprocess `cwd`:

```python
process = subprocess.Popen(command, cwd=project_dir.resolve(), ...)
```

This is the same class of bug as the OPENCODE_CONFIG relative path issue documented in CLAUDE.md -- relative paths silently break when the subprocess cwd is different from the parent's.

### 3. Codex sandbox flags

Codex has its own sandbox for shell commands the LLM runs. For the benchmark, we need full access since the LLM creates files, runs `bundle install`, `rails new`, etc. The flags:

- `--dangerously-bypass-approvals-and-sandbox` -- skip ALL confirmation prompts (equivalent to opencode's `--agent build` with yolo permissions)
- `-s danger-full-access` -- explicitly set the sandbox policy to full access (belt and suspenders)
- `--skip-git-repo-check` -- allow running in a non-git directory (the project dir is freshly created)
- `--ephemeral` -- don't persist codex session files to disk

### 4. Reasoning effort is a config key, not a CLI flag

Codex doesn't have a `--reasoning-effort` flag. Instead, it's set via the config override mechanism:

```bash
codex exec -c model_reasoning_effort=xhigh ...
```

The benchmark passes this through the `codex_reasoning_effort` field in the model's JSON config entry.

### 5. Prompt delivery via stdin

Codex reads the prompt from stdin when `-` is the prompt argument (unlike opencode which takes the prompt as a CLI positional argument). The subprocess pipes the prompt to stdin and closes it before entering the stream monitoring loop:

```python
process = subprocess.Popen(command, stdin=subprocess.PIPE, ...)
process.stdin.write(prompt)
process.stdin.close()
```

### 6. Different JSONL event format

Codex emits different event types than opencode:

| Concept | opencode | Codex |
|---|---|---|
| Session start | `sessionID` field on events | `thread.started` with `thread_id` |
| Turn start | `step_start` | `turn.started` |
| Turn end | `step_finish` with `reason` | `turn.completed` with `usage` |
| Tool use | `tool_use` | `item.completed` with `type: "command_execution"` |
| Text output | `text` with `part.text` | `item.completed` with `type: "agent_message"` |
| Error | `part.type == "error"` | `turn.failed` or `type: "error"` |
| Token counts | `step_finish.part.tokens` | `turn.completed.usage.{input_tokens, output_tokens}` |

The `stream_process_output()` function was extended to handle both formats -- Codex event types are checked alongside opencode's, and since they never collide (different event names), existing opencode runs are unaffected.

### 7. No session continuity for phase 2

Codex with `--ephemeral` doesn't persist sessions. Phase 2 (follow-up validation) runs as a fresh codex invocation in the same project directory. The follow-up prompt includes fallback instructions to inspect the existing project first (same mechanism used when opencode session continuation fails).

By default, follow-up is disabled for codex models (`model_enables_followup` returns False for `provider: "codex"`).

## Architecture

```
config/models.json          "runner_type": "codex" on the model entry
        |
run_benchmark.py            checks for `codex` binary, skips opencode config generation
        |
runner.py: run_model()      dispatches to run_codex_phase() or run_opencode_phase()
        |
run_codex_phase()           builds command, pipes prompt via stdin, calls stream_process_output()
        |
stream_process_output()     shared monitoring: timeout, progress, error loops, tool-call loops
        |                   (extended with Codex event types alongside opencode's)
        |
extract_codex_metrics()     parses Codex JSONL for tokens, session, finish reason
```

## Files Changed

| File | What |
|---|---|
| `scripts/benchmark/runner.py` | `build_codex_command`, `extract_codex_metrics`, `describe_codex_event`, `run_codex_phase`; extended `stream_process_output` with `event_describer` param + Codex event types; `run_model` dispatch |
| `scripts/run_benchmark.py` | Conditional binary checks; filter codex models from opencode config generation |
| `scripts/benchmark/config.py` | `model_enables_followup` excludes `codex` provider; `prepare_local_opencode_config` falls back to `llama-swap` source provider |
| `config/models.json` | `gpt_5_4_codex` model entry |

## See Also

- [`success_report.md`](success_report.md) -- main benchmark analysis (GPT 5.4 results will be added here)
- [`llama-swap.md`](llama-swap.md) -- local NVIDIA llama-swap setup
- [Codex CLI GitHub](https://github.com/openai/codex) -- upstream repo
