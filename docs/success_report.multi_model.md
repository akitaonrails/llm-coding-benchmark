# Multi-Model Benchmark Report

This report covers two rounds of multi-model orchestration experiments:

1. **Free-choice round (7 variants)**: Main model + registered subagent, "Use PROACTIVELY" description language. Models decided whether to delegate. **Zero of 7 actually did.**
2. **Forced-delegation round (6 variants)**: Same model pairs, but with an explicit planner/executor prompt that forbade the planner from using Write/Edit/Bash and required every code change to flow through the subagent. **All 6 runs had real delegations (5–15 per run), and the original hypothesis still holds.**

The goal was to settle community pushback on the free-choice result: critics argued "the `description` was too weak" or "models don't trust unfamiliar subagents." The forced round eliminates those confounds. The answer is the same: forcing delegation produces equivalent-quality output at higher cost and longer wall time. The free-choice models' refusal to delegate was rational, not a failure of prompt engineering.

The short answer: **on a cohesive greenfield task, forcing the orchestrator pattern costs more for the same quality.** The one exception (GPT 5.4 faster improving Tier 2 → Tier 1 under forcing) suggests that **the value of the pattern isn't delegation per se — it's the structured verification rounds** that came with the plan-delegate-converge-validate workflow.

For baseline comparisons, the reference is `results/claude_opus_4_7` (Opus 4.7 via opencode, Tier 1, 18m, 28 tests, ~$1.10). See [`success_report.md`](success_report.md) for the main-benchmark context.

---

## Headline Findings

1. **Zero delegations across all 7 multi-model runs.** Every variant had at least one coding subagent visible to the main model (some more than intended — see Methodology Caveat below). Every variant ran with the main model doing 100% of the work. The `Task` tool, opencode's task dispatcher, and Codex's `spawn_agent` all went unused.

2. **Claude Code is 4-7× more expensive than opencode** for the identical Opus 4.7 model on the identical prompt. Harness overhead (CLAUDE.md context, tool specs, TodoWrite events) produced 6-11M cache-read tokens per run vs opencode's ~210K.

3. **Same Opus 4.7 model produces different code quality in different harnesses.** In opencode it nails the RubyLLM API (Tier 1). In Claude Code, 2 of 3 variants hallucinated `chat.complete` — a method that doesn't exist — producing Tier 3 code. This is the first benchmark evidence that harness context itself can degrade model correctness.

4. **Subagent `description` language is not persuasive.** Both "Use PROACTIVELY" (Claude Code and opencode) and Codex's agent descriptions failed to trigger delegation. Greenfield Rails work is apparently too cohesive for models to voluntarily hand off.

---

## Results Summary

| Variant | Tool | Status | Time | Files | Total Cost | Delegations | Tier |
|---|---|---|---:|---:|---:|---:|---|
| `claude_opus_alone` | Claude Code | completed | 11m | 1742 | $6.74 | 0 | **3** |
| `claude_opus_sonnet` | Claude Code | completed | 10m | 1829 | $5.13 | 0 | **2** |
| `claude_opus_haiku` | Claude Code | completed | 15m | 1984 | $7.83 | 0 | **3** |
| `opencode_opus_glm` | opencode | completed | 19m | 1888 | ~$1.10 | 0 | **1** |
| `opencode_opus_qwen` | opencode | completed | 30m | 1623 | ~$1.10 | 0 | **1** |
| `gpt_5_4_multi_balanced` | Codex | completed | 21m | 1671 | ~$11 | 0 | **1** |
| `gpt_5_4_multi_faster` | Codex | completed | 20m | 1716 | ~$10 | 0 | **2** |
| *baseline* `claude_opus_4_7` | opencode | completed | 18m | 11345 | ~$1.10 | n/a | **1** |

Tiers use the same criteria as the main report: Tier 1 = correct RubyLLM API + proper test mocks, Tier 2 = correct entry but multi-turn broken, Tier 3 = hallucinated API that crashes at runtime.

---

## Methodology Caveat: Claude Code Baseline Contamination

A sanity check of the 7 runs revealed that the `claude_opus_alone` and `claude_opus_haiku` variants were contaminated by a user-level subagent file at `~/.claude/agents/sonnet-coder.md` that had been created earlier in the same session for an unrelated purpose. Claude Code inherits user-level agents in addition to project-local ones, so:

| Variant | Intended subagents | Subagents actually registered (from init event) |
|---|---|---|
| `claude_opus_alone` | none | `sonnet-coder` (leaked from `~/.claude/agents/`) |
| `claude_opus_sonnet` | sonnet-coder | `sonnet-coder` (correct by accident) |
| `claude_opus_haiku` | haiku-coder | `haiku-coder` + `sonnet-coder` (leaked) |

The opencode and Codex variants were not affected — verified by reading the generated opencode config and the written `.codex-coder.toml` files.

**Implication for the finding:** The "zero delegations" conclusion is **strengthened**, not weakened. Three independent Claude Code runs all had a `sonnet-coder` subagent available, and all three ignored it. The "alone" baseline is mis-labeled — there is no true single-agent Claude Code run in this dataset. To get a clean "Opus with ZERO subagents available" control, the run would need to be repeated with `~/.claude/agents/` temporarily emptied. The closest true-baseline we have is the opencode `claude_opus_4_7` run (Tier 1, ~$1.10, no subagents configured).

---

## Part 1: Claude Code — The Harness Regression

All three Claude Code variants ran Opus 4.7 as the main model via `claude -p --output-format stream-json`. The variants were intended to differ in what subagent file was placed in `.claude/agents/` inside the project directory before the run. Due to the contamination described above, the actual available-subagent sets were:

| Variant | Agents available to Opus (from init event) |
|---|---|
| `claude_opus_alone` | `Explore`, `Plan`, `general-purpose`, `statusline-setup`, **`sonnet-coder`** |
| `claude_opus_sonnet` | same + **`sonnet-coder`** (intended) |
| `claude_opus_haiku` | same + **`sonnet-coder`** + **`haiku-coder`** (intended) |

Despite having delegation options available, **Opus invoked the `Task` tool zero times across all three runs.** The variants effectively measure the same thing: "Opus with a sonnet-coder subagent and built-in Explore/Plan/general-purpose agents, deciding whether to delegate on a greenfield Rails build." Answer: no, it doesn't.

### Token Usage vs opencode Baseline

| Run | Output tokens | Cache-read tokens | Total tokens | Cost |
|---|---:|---:|---:|---:|
| `claude_opus_4_7` (opencode baseline) | ~30K | ~50K | **118K** | $1.10 |
| `claude_opus_alone` | 44K | 9.31M | **~9.5M** | $6.74 |
| `claude_opus_sonnet` | 39.5K | 6.61M | **~6.8M** | $5.13 |
| `claude_opus_haiku` | 50.8K | 10.88M | **~11.1M** | $7.83 |

Cache-read tokens dominate Claude Code's cost. Every turn re-sends the full system prompt, CLAUDE.md, tool schemas, and agent registry. Over 100+ turns this multiplies to 6-11M tokens per run. opencode's more minimal context keeps this to ~50K.

### The "Haiku auto-delegation" hypothesis — disproved

Earlier I asked whether Claude Code silently routes some work through built-in Haiku-backed agents (Explore, Plan, general-purpose). The data says no. All three variants show identical **890 input / 24 output** Haiku tokens — the signature of Claude Code's title-summarization feature, nothing more. No Explore/Plan subagent was invoked during any run.

### The RubyLLM Correctness Regression

This is the most surprising finding. The same Opus 4.7 that nailed the RubyLLM API in opencode invented a non-existent `chat.complete` method in 2 of 3 Claude Code runs:

**`claude_opus_alone`** (`app/services/chat_client.rb`):
```ruby
chat = RubyLLM.chat(model: @model, provider: @provider)   # correct entry
chat.add_message(role: msg.role, content: msg.content)    # keyword args — wrong
reply = chat.complete                                      # METHOD DOES NOT EXIST
```

**`claude_opus_haiku`** (`app/services/chat_completion.rb`): same pattern — `chat.add_message(role:, content:)` + `chat.complete`. No `chat.ask(message)` anywhere.

**`claude_opus_sonnet`** (`app/models/chat.rb`): correct — `chat_client.ask(user_message.content)` and `reply.content`. Multi-turn replay uses `chat_client.add_message(role:, content:)` (keyword args), which breaks on turn 2, putting this at Tier 2.

Compare the opencode baseline (`results/claude_opus_4_7/app/services/llm_client.rb`):
```ruby
chat = RubyLLM.chat(model: @model, provider: @provider)
chat.with_instructions(@system_prompt)
response = chat.ask(user_message)                          # correct
response.content                                           # correct
```

**Same model, different harness, different correctness.** The Claude Code harness appears to nudge Opus toward a generic OpenAI-SDK mental model (`chat.complete`, keyword-arg `add_message`) — possibly because the system prompt or tool schemas contain patterns the model generalizes from. Whatever the mechanism, the effect is real: Claude Code Opus produced worse RubyLLM code than opencode Opus on three separate runs.

### Tests Papered Over the Bugs

All three variants have substantial test suites (24, 18, 34 tests respectively). Every test fake defines `def complete(...)` and `def add_message(role:, content:)` with keyword args — so the hallucinated API passes tests. This is the same failure mode documented in the main report: **API correctness is binary recall; test coverage measures nothing when the tests mock the wrong API.**

### Verdict: Claude Code performed worse than opencode here

On this specific benchmark, Claude Code's harness cost 5-7× more and produced worse code for the same underlying Opus 4.7 model. This contradicts the intuition that Claude Code is the natural home for Claude models. Two caveats:

1. This is a **single-task** measurement on a prompt designed for one-shot Rails generation. Claude Code is likely better-optimized for interactive multi-session work.
2. The prompt pattern ("build a complete Rails app") may trigger Claude Code's more expensive orchestration paths (TodoWrite, subagent registry) even when they aren't useful.

But the RubyLLM regression is a genuine finding worth flagging: harness context matters for model correctness, not just cost.

---

## Part 2: opencode Multi-Agent — Plumbing Works, Delegation Doesn't

### Config generation works correctly

Verified by the generated `config/opencode.benchmark.local.json`: both runs correctly wired up the primary Opus agent + the subagent coder (GLM 5.1 for one, Qwen 3.6 via llama-swap for the other), with both providers authenticated. opencode loaded the subagents into its agent manifest — confirmed by the init event.

### Opus ignored the coder subagent

Zero `tool:task` events in either ndjson. Zero child sessions. Zero tokens spent on GLM or Qwen. Opus handled the entire job via `bash`/`write`/`read`/`edit` in the main session.

**opencode_opus_glm**: 44 bash, 32 write, 25 read, 8 edit — all Opus. GLM 5.1 never called.

**opencode_opus_qwen**: 39 bash, 30 write, 16 read, 15 edit — all Opus. Qwen 3.6 never called (llama-swap logs confirm no requests during the run).

### Both variants are Tier 1

Same correct `RubyLLM.chat(model:, provider:)` + `chat.ask(msg)` + `response.content` as the baseline. Multi-turn replay uses `chat.add_message(role:, content:)` keyword args in both variants — different from the baseline's explicit-hash form but Ruby 3's implicit hash conversion means both work against RubyLLM's positional-hash method signature. Not a bug in Ruby 3, just a stylistic difference.

### Quality Differences Are Run Variance

`opencode_opus_glm` had a cleaner phase-2 Docker build than the baseline (114s vs longer, no Dockerfile fixups needed). `opencode_opus_qwen` produced slightly better code structure (dependency-injected `chat_factory` for test isolation). Neither is attributable to the subagent — same Opus variance we see across single-model runs.

### Why didn't Opus delegate?

The subagent descriptions said "Use PROACTIVELY for concrete coding execution" with a caveat "Skip delegation for cross-file architectural decisions." A Rails chat app IS cross-file architectural work (views depend on controllers depend on services depend on initializers), so Opus kept it for itself. The caveat was probably too strong.

---

## Part 3: Codex Multi-Agent — Same Story

### Agent configs loaded, never spawned

Both variants wrote a valid `.codex-coder.toml` in the project directory and passed `-c agents.coder.config_file=...` to the codex exec command. Codex parsed the config (visible in the init event). The main session never called `spawn_agent`.

Event-type tally proves it:

| Event type | balanced | faster |
|---|---:|---:|
| agent_message | 18 | 23 |
| command_execution | 172 | 156 |
| file_change | 0 | 18 |
| web_search | 12 | 6 |
| **spawn_agent** | **0** | **0** |

### Quality Variance, Not Delegation Effect

- **Balanced (xhigh + medium coder)**: **Tier 1.** Fixed the `add_message` keyword-args bug that plagued the baseline. Uses a positional-hash pattern (`message = {role:, content:}` then `chat.add_message(message)`). 22 tests, clean fakes.
- **Faster (xhigh + low coder)**: **Tier 2.** Reproduced the baseline's keyword-args bug exactly. `chat.add_message(role: msg.role.to_sym, content: msg.content)` at `chat_completion.rb:29` — crashes on turn 2.

The balanced variant happened to write better code; the faster variant happened to write the same broken code as the baseline. Since the subagent never ran, both differences are attributable to main-session variance. The tier gap between these two runs is the same kind of noise we've seen across multiple GPT 5.4 runs.

### Cost Comparison with Baseline

| Run | Total Tokens | Output | Cost Est. |
|---|---:|---:|---:|
| `gpt_5_4_codex` (xhigh alone, baseline) | 7.6M | 63K | ~$16 |
| `gpt_5_4_multi_balanced` | 5.44M | 63K | ~$11 |
| `gpt_5_4_multi_faster` | 4.28M | 60K | ~$10 |

The multi-agent variants are **cheaper** than the baseline, but only because they skipped phase 2 entirely (`continued_from_session: null`, no followup paths). The xhigh-alone baseline included phase 2's Docker validation work. Normalizing for that, per-phase cost is roughly equivalent.

### Neither variant is a win

Same Tier-1/Tier-2 outcomes as the baseline, same ~$10-16 cost band, same xhigh reasoning producing sophisticated architecture. Adding a subagent that never runs adds no value.

---

## Cross-Tool Insights

### Why did zero of 7 models voluntarily delegate?

1. **Rails is too cohesive.** The prompt is "build a complete Rails chat app" — every file depends on decisions in other files. Delegating a single write to a dumber model means the model sees less context than the planner and may make choices that contradict the plan. Smart planners (Opus, GPT 5.4 xhigh) correctly intuit that the coordination cost exceeds the execution savings.

2. **Description tuning matters more than expected.** All three tools allow a subagent `description` field. We wrote strong "Use PROACTIVELY" language, but every description also contained a caveat ("skip for architectural decisions"). In cohesive greenfield work, the entire task qualifies as "architectural," so the caveat vetoed every delegation. A stricter description (e.g., "Use for ALL file writes, no exceptions") might force delegation but would also force handoffs where they hurt quality.

3. **Delegation works better when the tasks are genuinely chunked.** The hypothesis for multi-agent is "Opus can oversee 20 parallel file ports." That's a structurally different task from "build a coherent app from scratch." Future benchmarks should include a task where delegation is the obviously correct choice (e.g., apply an API change across 30 files) to measure whether the pattern works at all.

### Why did Claude Code perform worse on Opus?

- The harness context is 100-200× more tokens than opencode's
- Those extra tokens include agent registries, TodoWrite events, Skill descriptions, MCP server references
- Opus appears to generalize patterns from that context onto code generation, nudging it toward an "OpenAI SDK-shaped" mental model of the RubyLLM gem
- Same model, same prompt, opposite correctness — a real and measurable regression

This does NOT mean Claude Code is bad. It means **Claude Code is optimized for interactive multi-session work**, not one-shot code generation. For benchmarking purposes, opencode is a fairer harness: less context pollution, tighter output, and (on this task) better correctness.

---

## Recommendations for Future Multi-Agent Benchmarks

1. **Pick tasks that naturally chunk.** "Port 30 files from API v1 to v2" forces delegation; "build a Rails app" doesn't.
2. **Write forcing subagent descriptions.** Drop the "skip delegation for X" caveats. Test "MUST delegate" as the upper bound to confirm the plumbing works, then relax.
3. **Run both multi-agent and single-agent variants of the same model+task.** The real measurement is the delta. Without a paired single-agent run, we can't tell whether delegation helped.
4. **Report actual delegation counts, not just model configuration.** All 7 runs in the free-choice round show "multi-agent" in config but "single-agent" in behavior. The gap between configuration and behavior is the most important data point.

---

# Round 2: Forced-Delegation Experiment

Community pushback on the free-choice findings: "your `description` language was too weak" / "models don't trust unfamiliar delegates" / "you didn't structure the workflow properly." To eliminate those confounds, round 2 used an explicit planner-orchestrator prompt ([`prompts/benchmark_prompt_forced_delegation.txt`](../prompts/benchmark_prompt_forced_delegation.txt)) that:

- Structures the full **plan → delegate → converge → validate** workflow
- Explicitly forbids the planner from using Write/Edit/Bash
- Requires every file creation and shell command to flow through the subagent via `Task` / `spawn_agent`
- Merges phase 1 + phase 2 validation into a single unified brief
- Allowed tools for the planner: Read, Task/spawn_agent, TodoWrite, Glob, Grep

Same 6 model pairs as the free-choice round (dropping `claude_opus_alone` since it has no subagent):

## Round 2 Results

| Variant | Status | Time | Files | Delegations | Total Cost | Rubric |
|---|---|---:|---:|---:|---:|---|
| `claude_opus_sonnet_forced` | completed | 25m | 1892 | **10** | $5.77 | ~95/100 Tier A |
| `claude_opus_haiku_forced` | completed | 19m | 134 | **5** | $3.49 | ~93/100 Tier A |
| `opencode_opus_glm_forced` | **failed** (phase 2 stalled) | 22m | 1965 | **10** | ~$1.34 + subscription | ~88/100 Tier A (phase 1 only) |
| `opencode_opus_qwen_forced` | **failed** (phase 1 stalled) | 16m | 2038 | **7** | ~$0.22 | ~70/100 Tier 2 (`reply.content` bug) |
| `gpt_5_4_multi_balanced_forced` | completed | 30m | 2960 | **8** | ~$2–5 | ~94/100 Tier A |
| `gpt_5_4_multi_faster_forced` | completed | 53m | 1852 | **15** | ~$6+ | ~93/100 Tier A |

**Delegations actually happened this time.** 5–15 per run, compared to 0/0/0/0/0/0/0 in the free-choice round. The forcing prompt is mechanically effective.

## Compliance with the "no direct Write/Edit/Bash" rule

| Variant | Direct Bash (planner) | Direct Write/Edit (planner) |
|---|---:|---:|
| claude_opus_sonnet_forced | 11 (all read-only: `ls`, `mise ls`, `cat`) | **0** |
| claude_opus_haiku_forced | 16 (read-only + 5 `ruby -e "..."` introspection probes) | **0** |
| opencode_opus_glm_forced | 5 (read-only) | **0** |
| opencode_opus_qwen_forced | 19 (read-only + gem source `sed`/`grep`/`ruby -e`) | **0** |
| gpt_5_4_multi_balanced_forced | **0** | **0** |
| gpt_5_4_multi_faster_forced | **0** | **0** |

**Full compliance from Codex** (the `spawn_agent` harness makes cheating mechanically impossible — the parent thread has no shell access). **Partial compliance from Claude Code + opencode** — Opus ran up to 19 read-only inspection commands despite the prompt forbidding Bash outright. The spirit was respected (zero file mutations by the planner) but the letter wasn't.

## Quality: equivalent to slightly-better when forcing succeeds

- **Claude Code Sonnet + Haiku**: same Tier 1 quality as solo Opus 4.7 / free-choice. No measurable lift, no degradation.
- **Codex balanced**: equivalent Tier 1 to free-choice.
- **Codex faster**: forced **improved** quality from Tier 2 → Tier 1. The single positive datapoint. Caused by the structured verification rounds baked into the prompt — every implementation spawn was followed by a read-only verification spawn that caught issues the solo run missed.
- **opencode GLM**: Tier 1 code in phase 1, but phase 2 validation stalled at the no-progress timeout.
- **opencode Qwen local**: produced a real runtime bug — `MessagesController#create` returns `reply` (a `RubyLLM::Message` object) instead of `reply.content` (a String). Local subagent executed literally without catching the semantic issue. Tier 2 if it had finished.

## Cost and wall time: uniformly worse

| Variant | Forced cost | Free-choice cost | Solo cost | Forced time | Free-choice time |
|---|---|---|---|---|---|
| Sonnet | $5.77 | $5.13 | $1.10 (solo Opus) | 25m | 9m |
| Haiku | $3.49 | $7.83 | $1.10 | 19m | 15m |
| GLM | ~$1.34 + sub | $1.10 | $1.10 | 22m | 19m |
| Qwen (local) | ~$0.22 | $1.10 | $1.10 | 16m | 30m |
| GPT balanced | ~$2–5 planner-only | ~$11 | $16 solo xhigh | 30m | 25m |
| GPT faster | ~$6+ | ~$10 | $16 | 53m | 25m |

**Haiku is the only variant where forcing was cheaper than free-choice** ($3.49 vs $7.83) — counterintuitive, but explained by the token split. Haiku absorbed 78% of tokens under forcing, vs the free-choice version where Opus did everything itself.

Every forced run was slower than its free-choice counterpart. **Coordination overhead is real**: context sent with every dispatch, verification reads between subtasks, fix-up rounds when subagent output didn't mesh.

## Token split (Claude Code, where we can measure it)

- **Sonnet variant**: Opus 41% / Sonnet 59% / trace Haiku (auto-summaries)
- **Haiku variant**: Opus 22% / Haiku 78%

The smaller subagent absorbs proportionally more tokens (expected), but the absolute Opus spend on planning + Read + verification (2.8M / 1.6M tokens) is massive vs solo (~700K–1M tokens for the same task). Round-trips aren't free.

## The meta-finding: forcing ≠ delegation's fault; verification rounds are what helped

Five of six forced runs produced equivalent-or-marginally-different output at higher dollar and wall-time cost vs the free-choice or solo baseline. **The free-choice models' refusal to delegate was rational** — they correctly intuited that coordinating across a subagent on a single cohesive Rails build costs more than it saves.

But the single quality win (`gpt_5_4_multi_faster_forced`: Tier 2 → Tier 1) points to a different mechanism. Looking at its 15 spawn_agent calls, half were **read-only verification passes** interleaved between implementation passes — exactly what the prompt asked for in the CONVERGE phase. That structured "write → verify → fix" loop caught bugs the solo run glossed over.

**Actionable takeaway**: the value of the orchestrator pattern on tasks like this isn't the delegation. It's the **forced verification rounds**. A simpler intervention — adding "after each major component is done, do a read-only verification pass to check for integration issues" to the solo prompt — would likely capture most of the quality gain without the coordination overhead of a two-thread setup.

## Round 2 updated conclusions

1. **Zero delegations wasn't because the free-choice prompt was weak.** Forcing the pattern confirms models refuse for rational reasons.
2. **Forced delegation works mechanically** but adds coordination overhead without quality gains on cohesive tasks.
3. **Codex's `spawn_agent` architecture is the only one that enforces planner compliance at the harness level**. Claude Code and opencode allowed Opus to run inspection Bash commands despite explicit prompt forbidding it.
4. **Verification rounds are the hidden win.** If your orchestrator prompt includes "write then verify then fix," you'll see quality lift. If it just includes "delegate everything," you'll see cost lift without quality lift.

---

## Cross-Reference

- [`success_report.md`](success_report.md) — main benchmark (AMD/cloud), Tier classification methodology, single-model results
- [`success_report.nvidia.md`](success_report.nvidia.md) — NVIDIA RTX 5090 workstation profile, Qwen 3.6 35B baseline (Tier 2)
- [`codex-integration.md`](codex-integration.md) — Codex CLI integration hurdles (stdin piping, sandbox flags, reasoning effort config)
- [`llama-swap.md`](llama-swap.md) — local llama-swap setup used by the Qwen 3.6 subagent variant
