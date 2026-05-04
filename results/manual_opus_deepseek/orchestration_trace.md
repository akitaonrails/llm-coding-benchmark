# Orchestration trace: manual_opus_deepseek

## Outcome: FAILED (harness incompatibility) — UNBLOCKED IN ROUND 4 VIA deepclaude

> **Update (Round 4)**: DeepSeek V4 Pro was successfully benchmarked through a different harness (Claude Code via the deepclaude env-swap shim, routing through OpenRouter's Anthropic-compatible endpoint). Both `claude_code_deepseek_v4_pro_or` and `claude_code_deepseek_v4_pro_or_sonnet` completed end-to-end at 84/100 and 89/100 (both Tier A). See [`docs/success_report.deepclaude.md`](../../docs/success_report.deepclaude.md). The reasoning_content failure documented below is specific to the opencode/ai-sdk request payload construction; Claude Code with deepclaude does not trigger it.

This variant attempted to test Opus 4.7 (Claude Code planner) + DeepSeek V4 Pro (opencode executor) under the same manual-orchestration protocol used for `manual_opus_qwen36plus` and `manual_opus_kimi`.

It failed on the first dispatch with a structural incompatibility: **DeepSeek V4 Pro on OpenRouter requires that `reasoning_content` from each assistant turn be echoed back in subsequent requests within the same conversation**, and opencode's ai-sdk does not preserve/echo reasoning_content.

## Failure mode (reproduced 3 times)

Three dispatch retries with three different opencode `reasoning` configurations:

| Attempt | `reasoning` config | Outcome |
|---|---|---|
| 1 | `reasoning: true` (auto-emitted by config.py patch from Round 2.5) | Failed at turn 4: `[DeepSeek] The "reasoning_content" in the thinking mode must be passed back to the API.` |
| 2 | `reasoning: false` (manually patched) | Failed at turn 2 with statusCode=400 "Provider returned error" |
| 3 | `reasoning` field entirely removed | Failed at turn 2: identical reasoning_content error |

In every case, a few initial bash commands ran successfully (pwd, ls, source secrets, ruby --version) within turn 1, but the model's response contained reasoning_content that opencode could not preserve in the next request payload.

## Why this happens (CLAUDE.md confirmation)

This is the documented DeepSeek V4 Pro reasoning_content interop bug. From the project's CLAUDE.md before this experiment:

> "**DeepSeek V4 Pro reasoning_content**: opencode strips reasoning_content but DeepSeek requires it echoed back. Tried `reasoning: false` config; only delayed the issue."

The Round 2.5 fix attempt (auto-emit `reasoning: true` on the provider entry) does NOT fix this bug — it changes which UI surface displays reasoning content, not whether opencode echoes it back to the API in subsequent requests. **No combination of opencode model-level config flags resolves this.**

## What this means for the round 2.5 in-process forced-delegation runs

The previous `opencode_opus_deepseek_forced` runs (both with and without the patched config) reported "completed" with substantive artifacts (1900 files). Per the trace audits in [`orchestration_traces.md`](../../docs/orchestration_traces.md), most of those dispatches went to opencode's built-in `general` agent (Opus fallback), not to DeepSeek. **Now we know why DeepSeek "no-op'd"**: it wasn't returning empty results — it was actively erroring with a reasoning_content protocol violation that opencode silently dropped from the visible output. The planner saw an empty `<task_result>` because the request to DeepSeek had failed at the wire level.

## What we did NOT measure

- DeepSeek V4 Pro's actual capability under Opus orchestration
- Whether the +47-pt GLM lift / +23-pt Qwen 3.6 Plus lift / +10-pt Kimi lift extends to DeepSeek V4 Pro
- Any DeepSeek V4 Pro Tier-A artifact

The closest comparison we have is DeepSeek V4 Pro solo at 69/100 (Tier B, "Tier 1 RubyLLM code with Tier 3 deliverables — missing compose, stock README"). Solo DeepSeek goes through a different code path (single-turn opencode, no multi-turn dispatch), which is why it works. The manual-orchestration protocol requires multi-turn within each opencode session (the model needs to call tools, see their output, and continue), which is exactly the path that breaks.

## Workarounds NOT pursued

- **OpenRouter "exclude reasoning" provider option**: would require opencode source patch to set `extra_body: {provider: {require_parameters: false}}` or similar
- **Single-bash-command-per-dispatch protocol**: would require ~50+ dispatches per variant, each enforcing one shell command — impractical scope
- **Different DeepSeek model**: DeepSeek V4 Flash (which doesn't have aggressive thinking mode) might work, but the user requested V4 Pro specifically

## Artifact state

`results/manual_opus_deepseek/project/` contains ~80 files from the partial Rails generator runs across the failed dispatches. Not a coherent app. Not auditable.

## Cost incurred

- Dispatch 1 (`reasoning: true` attempt): $0.05
- Dispatch 2 (`reasoning: false` attempt): $0.03
- Dispatch 3 (no `reasoning` field): $0.04

Total: ~$0.12, which was wasted establishing reproducibility of the harness incompatibility.
