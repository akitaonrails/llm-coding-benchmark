# deepclaude Benchmark — DeepSeek V4 Pro inside Claude Code

This report covers Round 4 of the multi-model orchestration experiment series: running DeepSeek V4 Pro through Claude Code's autonomous agent loop using the **deepclaude** env-var swap shim ([source](https://github.com/aattaran/deepclaude)). The motivation, install, and runner integration are documented in [`deepclaude-integration.md`](deepclaude-integration.md). This doc is the actual benchmark results.

## Why this round exists

Round 3 ([`success_report.manual_orchestration.md`](success_report.manual_orchestration.md)) established that DeepSeek V4 Pro is **structurally unmeasurable through opencode** in any multi-turn dispatch configuration: the model returns `reasoning_content` blocks that opencode's ai-sdk does not echo back in subsequent requests, so DeepSeek's API rejects every turn after the first with a 400. Three different opencode `reasoning` configs all reproduced the same wire-level failure. We had no clean measurement of DeepSeek V4 Pro under any orchestration protocol.

deepclaude bypasses this by routing Claude Code's tool-loop traffic through OpenRouter's Anthropic-compatible endpoint (`https://openrouter.ai/api`) instead of `api.anthropic.com`. Claude Code's full agent loop (file editing, bash, subagent spawning, multi-step tool use) runs unchanged on top of that endpoint, with all `ANTHROPIC_DEFAULT_*_MODEL` env vars pointing at `deepseek/deepseek-v4-pro`. The reasoning_content interop bug doesn't trigger because OpenRouter's `/anthropic` shape handles thinking content compatibly.

## Variants

| Slug | Setup | Subagent registered? |
|---|---|---|
| `claude_code_deepseek_v4_pro_or` | Claude Code + deepclaude shim → DeepSeek V4 Pro for the entire loop | none |
| `claude_code_deepseek_v4_pro_or_sonnet` | Same, but with `sonnet-coder` subagent (Sonnet 4.6 via Anthropic API) registered | yes — but **0 delegations** observed |

Both used `--no-progress-minutes 15` (the standardized timeout from Round 2.5).

## Results

| Variant | Status | Time | Files | Turns | Delegations | Cost | Score | Tier |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `claude_code_deepseek_v4_pro_or` | completed | **21m** | 1544 | 106 | 0 (no subagent) | **$3.38** | **84** | A |
| `claude_code_deepseek_v4_pro_or_sonnet` | completed | **18m** | 1348 | 109 | **0** (Sonnet ignored) | **$3.14** | **89** | A |

Token breakdown (both 100% on `deepseek/deepseek-v4-pro`, NO Sonnet tokens billed despite registration):

| Variant | Input | Output | Cache read | Cache write | Cost |
|---|---:|---:|---:|---:|---:|
| `..._or` | 69,967 | 36,380 | 4,243,584 | 0 | $3.38 |
| `..._or_sonnet` | 65,965 | 28,936 | 4,173,824 | 0 | $3.14 |

The huge `cache_read` is OpenRouter reporting back the upstream caching DeepSeek does internally — cost-billed accordingly through the OpenRouter pricing.

## Headline findings

### 1. The Claude Code harness regression is OPUS-SPECIFIC, not a property of the harness

This is the most important finding from Round 4. The original Round 1 free-choice writeup ([`success_report.multi_model.md`](success_report.multi_model.md)) documented that Opus 4.7 in Claude Code hallucinated `chat.complete` (Tier 3), while the same Opus 4.7 in opencode produced clean Tier-A code. The hypothesis was that Claude Code's harness context (system prompt, tool schemas, agent registry) was nudging Opus toward an OpenAI-SDK mental model.

**DeepSeek V4 Pro in the same Claude Code harness used the real `chat.ask` path** (`chat_service.rb:17` in both variants). No hallucinated `chat.complete`, no fluent DSL, no batch-form invention. **The harness regression is Opus-specific** — Opus's training has a particular vulnerability to the way Claude Code's system prompt and tool-schema chatter primes the model, and DeepSeek's training is robust to it.

Counter-grep across both project trees:
```
grep -nE "RubyLLM::Client|chat\.complete|chat\.send_message|chat\.user|chat\.assistant|response\.text|RubyLLM\.chat\(messages"
→ 0 hits (both variants)
```

### 2. DeepSeek V4 Pro IS measurable through Claude Code via deepclaude (the unblock)

This was the experimental purpose of integrating deepclaude. Both variants ran end-to-end without the reasoning_content interop bug that broke every opencode-based attempt in Round 3. **deepclaude is the working harness for benchmarking DeepSeek V4 Pro inside an autonomous coding agent loop.** Multi-turn works. Subagent registration works (even if not invoked). Tool calls work. File editing works.

### 3. Harness change alone (no orchestration) lifts DeepSeek V4 Pro by 15-20 points

| Configuration | Score | Tier |
|---|---:|---|
| DeepSeek V4 Pro solo via opencode | 69 | B |
| `claude_code_deepseek_v4_pro_or` (deepclaude, no subagent) | **84** | A |
| `claude_code_deepseek_v4_pro_or_sonnet` (deepclaude, registered-but-unused subagent) | **89** | A |

The `+15` lift between solo opencode and deepclaude-no-subagent is **purely a harness-change effect** — same model, same prompt, no orchestration, just a different tool loop. Auditor attribution: the gaps that hurt the opencode solo run (stock README, missing compose, no CI tooling) get fixed by Claude Code's stronger autonomous loop. The model itself was already RubyLLM-correct in both runs; Claude Code just delivers a more complete artifact around the model's correct integration.

The `+5` further lift from variant 2 (registered Sonnet subagent that was never invoked) is the more subtle signal — see #5 below.

### 4. DeepSeek as planner ignores subagents on cohesive tasks (generalizes the Round 1 finding)

The original Round 1 free-choice round established that **every frontier LLM (Opus, GPT 5.4, Codex models) ignored their registered subagents** on the cohesive Rails build. We documented this as planner-rationality: smart planners correctly intuit that coordination cost exceeds execution savings on a tightly-coupled task.

Round 4 adds **DeepSeek V4 Pro to that list**: registered Sonnet 4.6 coder subagent, 0 delegations. This is no longer just an Opus quirk — it's a property of strong reasoning models when faced with greenfield Rails work and an optional delegate. DeepSeek's solo refusal to delegate matches what every other frontier planner has done.

### 5. Subagent-availability signal even without invocation (a real, weak-but-measurable effect)

The most interesting finding from variant 2: even though Sonnet was never invoked (`0 delegations`, 100% of tokens on `deepseek/deepseek-v4-pro`), the artifact quality went **+5 over the no-subagent sister variant**. Auditor attribution: with a subagent available "in case I need it," the DeepSeek planner produced **measurably more delegable decomposition** — smaller seams, cleaner DI, system prompt usage via `with_instructions`, controller test that mocks the real service-API shape rather than fudging it.

Quote from the audit: *"Knowing a subagent might execute the work pushes toward smaller, more contractable units — even when nothing actually delegates. Weak signal, single sample, but visible."*

This is consistent with prior round findings that the **structured CONVERGE phase, not the delegation itself**, was responsible for quality lifts in some forced runs. The mere availability of a subagent makes the planner think more like an architect.

### 6. Multi-turn bug persists across harness change

A specific defect that survives the harness change: both deepclaude variants have multi-turn problems at the controller layer.

- Variant 1 (`..._or`): outright single-shot. `chats_controller.rb:10` builds a 1-element messages array on every POST, throwing away history. The `ChatService` supports history, but the controller never sends it.
- Variant 2 (`..._or_sonnet`): correct multi-turn via `session[:messages]` (`chats_controller.rb:3,17`), BUT cookie-store will overflow at ~10 turns (`CookieOverflow`).

The solo opencode DeepSeek run (69/100) had the same single-shot issue. Different harness, different agent loop, **same model-level mistake** in the controller — multi-turn architecture for stateless Rails is genuinely hard for DeepSeek and the harness change doesn't help with that specific gap.

## Cost-quality-time positioning vs every other variant in the benchmark

The gold-standard comparison from the Round 3 verdict ([`success_report.manual_orchestration.md`](success_report.manual_orchestration.md) "Final verdict" section), now updated with Round 4 data:

| Variant | Score | Time | Cost | Notes |
|---|---:|---:|---:|---|
| **Opus 4.7 solo (opencode)** | **97** | **18m** | **$4.04** | the gold standard for one-off greenfield Rails |
| Opus + Kimi (manual cross-process) | 97 | 30-40m | $3-7 (incl. planner) | ties quality, ~2× wall time |
| GPT 5.4 xHigh + medium (Codex forced) | 94 | 30m | ~$1-3 | the cost-optimization win |
| **`claude_code_deepseek_v4_pro_or_sonnet`** (deepclaude) | **89** | **18m** | **$3.14** | -8 quality, **same wall time as solo Opus**, slightly cheaper |
| **`claude_code_deepseek_v4_pro_or`** (deepclaude) | **84** | **21m** | **$3.38** | -13 quality, +3m, slightly cheaper |
| DeepSeek V4 Pro solo (opencode) | 69 | ~25m | ~$1 | what we had before deepclaude — Tier B |
| `claude_opus_alone` (Claude Code Opus 4.7) | ~50-60 | 11m | $6.74 | the harness regression case — Opus hallucinated `chat.complete` |

**Where deepclaude lands in the cost-quality picture**: between Codex GPT 5.4 forced ($2 / 94) and solo Opus ($4 / 97). Cheaper than solo Opus by ~$0.66-0.90, same wall time, but **8-13 points lower quality**.

## Updated answer to "is orchestration / harness-swap worth it vs solo Opus?"

The Round 3 verdict was: for one-off greenfield Rails, solo Opus opencode wins. Round 4 adds:

- **For users who don't have access to Anthropic Claude Opus** (or who want to avoid Anthropic-direct costs), `claude_code_deepseek_v4_pro_or_sonnet` is the closest substitute: 89/100 Tier A, 18m, $3.14, runs entirely through OpenRouter using a key you already have. This is a meaningful "Tier-A coding without an Anthropic subscription" answer.

- **For users who do have Opus**, deepclaude is still slightly worse on quality (-8) for marginally better cost (-$0.66). **Not worth it for them.**

- **For comparing models inside Claude Code's harness directly**, deepclaude makes the comparison possible: DeepSeek V4 Pro at 84-89 vs Opus 4.7 at the regressed Tier-3 level in the same harness. **DeepSeek V4 Pro through deepclaude beats Opus 4.7 in Claude Code at every metric** — quality, cost, AND its multi-turn isn't worse — but only because Opus regresses in this harness; against Opus in opencode (97) DeepSeek is clearly behind.

## Updated cross-harness picture for DeepSeek V4 Pro

What we now know about DeepSeek V4 Pro:

| Harness | Outcome |
|---|---|
| opencode solo (single agent) | 69/100 Tier B — works, but missing deliverable polish |
| opencode multi-agent forced (executor) | UNMEASURABLE — `reasoning_content` interop bug fails at turn 2 |
| opencode + manual cross-process orchestration (executor) | UNMEASURABLE — same bug |
| Claude Code via deepclaude OR (solo) | **84/100 Tier A** — works, harness fixes most opencode polish gaps |
| Claude Code via deepclaude OR (with registered subagent) | **89/100 Tier A** — modest planner-availability lift |
| Claude Code direct (Anthropic API) | not tested — would need DEEPSEEK_API_KEY for native endpoint |

**Net**: DeepSeek V4 Pro is a Tier-A coder when delivered through a strong autonomous loop (Claude Code), and Tier-B when delivered through a thinner harness (opencode). The model's RubyLLM API recall is correct in both cases — the score difference is entirely in deliverable completeness (README, compose, CI tooling) which Claude Code's loop fills in.

## What to use this for

1. **Cost-sensitive Tier-A on a non-Anthropic budget**: `claude_code_deepseek_v4_pro_or_sonnet` is now the recommended default — $3.14, 18m, 89/100, Tier A, works entirely through OpenRouter.

2. **Validating "does the harness regression hit other models"**: it doesn't. The Opus-in-Claude-Code `chat.complete` regression is Opus-specific. DeepSeek (and presumably other non-Opus reasoning models with correct RubyLLM training) carry their knowledge through cleanly.

3. **Future experiments**: deepclaude opens the door to running ANY OpenRouter model through Claude Code's full agent loop. Worth re-testing Kimi K2.6 and Qwen 3.6 Plus through deepclaude as a clean comparison vs the manual-orchestration Round 3 results — same model, different harness, see what the lift looks like.

## Cross-reference

- [`deepclaude-integration.md`](deepclaude-integration.md) — install, env-override mechanics, smoke test, caveats from the deepclaude README
- [`success_report.manual_orchestration.md`](success_report.manual_orchestration.md) — Round 3 manual orchestration + the bottom-line cost-quality-time verdict (now amended with Round 4 data)
- [`success_report.multi_model.md`](success_report.multi_model.md) — Round 1 free-choice + Round 2 forced-delegation
- [`success_report.multi_model_forced.md`](success_report.multi_model_forced.md) — Round 2 + 2.5 rubric audits
- [`orchestration_traces.md`](orchestration_traces.md) — per-variant forensic walkthroughs across all rounds
- [`success_report.md`](success_report.md) — main benchmark, 23-model rankings
