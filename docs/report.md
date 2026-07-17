# Benchmark Report

Generated at: 2026-07-17T13:04:57+00:00
Prompt SHA256: `d25f119447215ebf47477c1ce61b24f801bfcb9336467f5b019d554f3c83537c`

## Progress

- `completed`: 46
- `completed_with_errors`: 3
- `failed`: 8
- `timeout`: 1
- `not_run`: 12

## Runner

`opencode run --agent build --format json`

- Selected after local probing because it exposes machine-readable JSON events with session IDs and token counts.
- The local crush install advertised --yolo in help output but rejected the flag at runtime, which makes it a poor default for unattended benchmarking here.
- The explicit build agent has permissive filesystem/tool rules, which is the closest match to the requested autonomous coding workflow.

## Model Selection

- `gemma4_31b` -> `ollama/google/gemma4-31b-it-bf16`: Hosted locally via llama-swap. Requires llama.cpp b8665+ for the dedicated Gemma 4 tool call parser (PR #21418). Skipped by default; re-enable for llama-swap benchmark runs.
- `glm_4_7_flash_bf16` -> `ollama/glm/glm-4.7-flash-bf16`: Hosted locally via llama-swap. Needs --jinja --reasoning-format none to suppress <think> tags in content. Tool calling works correctly with these flags.
- `llama4_scout` -> `ollama/meta/llama4-scout`: Hosted locally via llama-swap. Skipped by default: llama.cpp has no parser for Llama 4's pythonic tool call format — model outputs tool calls as plain text content instead of structured tool_calls. Requires upstream llama.cpp support (similar to vLLM's llama4_pythonic parser).
- `qwen3_32b` -> `ollama/qwen/qwen3-32b`: Requested local model family; exact hosted variant available through opencode. Superseded by the Qwen 3.5 line for future local benchmarking. Skipped by default after benchmark preview averaged 7.96 output tok/s over the first 3 steps (< 20.00).
- `qwen3_coder_next` -> `ollama/qwen/qwen3-coder-next`: Best direct coding-oriented local Qwen variant matching the original benchmark brief. Skipped by default after benchmark preview measured 6.59 output tok/s (< 20.00).
- `qwen3_5_35b` -> `ollama/qwen/qwen3.5-35b`: Requested local model family; exact hosted variant available through opencode. Skipped by default because the current benchmark pass is restricted to OpenRouter models that previously completed successfully.
- `qwen3_6_35b` -> `ollama/qwen/qwen3.6-35b`: Qwen 3.6 35B-A3B (released 2026-04-15). Same qwen3_5_moe architecture as 3.5 (35B total / 3B active MoE). Q3_K_M ~16 GB — drop-in replacement for 3.5. Significant benchmark gains: SWE-bench 73.4 (was 70), Terminal-Bench 51.5 (was 40.5), MCPMark 37 (was 27). Has vision encoder. Same chat template and llama.cpp flags as 3.5.
- `qwen3_5_122b` -> `ollama/qwen/qwen3.5-122b`: Hosted locally via llama-swap. Needs --reasoning-format none on llama-server to avoid reasoning_content tokens that some clients mishandle. Tool calling works correctly with Qwen chat template.
- `gpt_oss_20b` -> `ollama/openai/gpt-oss-20b`: Added as a local Ollama GPT OSS baseline for later warmup and benchmark testing.
- `nemotron_cascade_2` -> `ollama/nemotron_cascade_2`: Added as a local Ollama Nemotron Cascade 2 candidate for later warmup and benchmark testing. This entry uses explicit local model metadata because it is not yet mapped in the home opencode config.
- `claude_opus_4_6` -> `openrouter/anthropic/claude-opus-4.6`: Exact requested cloud model.
- `claude_opus_4_7` -> `openrouter/anthropic/claude-opus-4.7`: Anthropic Claude Opus 4.7 on OpenRouter. Built for long-running async agents. Same pricing as 4.6: $5/M input, $25/M output. 1M context, 128K max output. Released 2026-04-16.
- `claude_opus_4_8` -> `openrouter/anthropic/claude-opus-4.8`: Anthropic Claude Opus 4.8 on OpenRouter. Direct successor to Opus 4.7 using the regular (non-fast) endpoint. 1M context, tool calling supported, $5/M input and $25/M output. Tests whether the 4.8 release keeps Opus 4.7's benchmark-leading RubyLLM correctness while improving speed or implementation discipline.
- `claude_fable_5` -> `openrouter/anthropic/claude-fable-5`: Anthropic Claude Fable 5 on OpenRouter (snapshot claude-5-fable-20260609, released 2026-06). New Claude 5-generation model. 1M context, tool calling supported, $10/M input and $50/M output — 2x Opus 4.x pricing. Tests whether the new generation improves on Opus 4.7/4.8's benchmark-leading RubyLLM correctness.
- `claude_fable_5_rerelease` -> `openrouter/anthropic/claude-fable-5`: Anthropic Claude Fable 5 re-release on OpenRouter, tested separately from the original 2026-06 claude_fable_5 run after the model was removed and re-released. Uses the same concrete model ID so the old result remains intact while measuring whether the new serving snapshot regressed in RubyLLM/Rails benchmark behavior.
- `claude_sonnet_5` -> `openrouter/anthropic/claude-sonnet-5`: Anthropic Claude Sonnet 5 on OpenRouter, released 2026-06-30. Direct successor to Sonnet 4.6 with 1M context, tool calling, and adaptive thinking. Tests whether the Claude 5-generation Sonnet tier catches up to Opus/Fable on RubyLLM API correctness while remaining cheaper than Opus-class models.
- `opencode_opus_glm` -> `openrouter/anthropic/claude-opus-4.7`: opencode multi-agent: Opus 4.7 primary + GLM 5.1 (Z.ai) coding subagent. Tests whether the cost-effective Chinese model handles coding when Opus plans. GLM 5.1 via Z.ai coding plan endpoint (subscription). Comparable to Claude Code's opus+sonnet variant but with a non-Anthropic coder.
- `opencode_opus_glm_forced` -> `openrouter/anthropic/claude-opus-4.7`: Forced-delegation variant of opencode_opus_glm. Runs with prompts/benchmark_prompt_forced_delegation.txt. Measures whether forcing the orchestrator pattern produces usable code via Opus (plan) + GLM 5.1 (execute) vs the free-choice version which didn't delegate at all.
- `opencode_opus_kimi_forced` -> `openrouter/anthropic/claude-opus-4.7`: Replacement for opencode_opus_glm_forced after Z.ai GLM 5.1 subagent stalled twice in the forced-delegation experiment. Kimi K2.6 was Tier A (87/100) in the solo benchmark vs GLM 5.1's Tier C (46/100), and both planner+subagent run through OpenRouter (no provider mixing latency). Runs with prompts/benchmark_prompt_forced_delegation.txt.
- `opencode_opus_qwen36plus_forced` -> `openrouter/anthropic/claude-opus-4.7`: Test the cheap-cloud-executor pairing: Opus plans, Qwen 3.6 Plus (Tier B 71/100 solo via OpenRouter free tier) executes. Same provider lane as planner so should not exhibit the cross-provider task-dispatch stall seen with GLM 5.1 (Z.ai) and local Qwen (llama-swap). Runs with prompts/benchmark_prompt_forced_delegation.txt.
- `opencode_opus_deepseek_forced` -> `openrouter/anthropic/claude-opus-4.7`: Test whether DeepSeek V4 Pro (solo Tier C 69/100 — Tier 1 code with Tier 3 deliverables) executes cleanly when Opus handles the planning/integration. Same OpenRouter provider lane to avoid the cross-provider task-dispatch stall. Runs with prompts/benchmark_prompt_forced_delegation.txt.
- `opencode_gpt55_qwen36plus_forced` -> `openrouter/openai/gpt-5.5`: Stress test: GPT 5.5 (typically Codex-only because OpenAI restricts tool calling on OpenRouter for GPT 5.x) as opencode planner with cheap Qwen executor. KNOWN RISK: GPT 5.5 may not tool-call on OpenRouter; if it can't, the run will fail with no Task dispatches and that itself is a useful finding. Runs with prompts/benchmark_prompt_forced_delegation.txt.
- `opencode_gpt55_deepseek_forced` -> `openrouter/openai/gpt-5.5`: Stress test: GPT 5.5 + DeepSeek V4 Pro both via OpenRouter. KNOWN RISK: GPT 5.5 may lack tool calling on OpenRouter, in which case no delegation will occur. Runs with prompts/benchmark_prompt_forced_delegation.txt.
- `opencode_opus_qwen_forced` -> `openrouter/anthropic/claude-opus-4.7`: Forced-delegation variant of opencode_opus_qwen. Most interesting test case: expensive cloud orchestrator + free local executor. If this produces working code it's the cheapest usable multi-agent configuration. Depends on llama-swap with qwen3.6:35b loaded.
- `opencode_opus_qwen` -> `openrouter/anthropic/claude-opus-4.7`: opencode multi-agent: Opus 4.7 primary (cloud) + Qwen 3.6 35B (local llama-swap) coding subagent. Tests the 'local hybrid' hypothesis — expensive cloud orchestrator with free local executor. Depends on llama-swap running with qwen3.6:35b loaded.
- `gpt_5_4_pro` -> `openrouter/openai/gpt-5.4-pro`: Chosen from the OpenRouter GPT 5.4 family as the largest and most coding-oriented variant. Skipped by default because it failed in the previous benchmark pass.
- `gpt_5_4_codex` -> `gpt-5.4`: GPT 5.4 via Codex CLI at xhigh reasoning effort. Tier 2: correct entry point (RubyLLM.chat + ask + response.content) but add_message uses keyword args instead of positional hash — crashes on multi-turn. ~$16/run (15x Claude). Polished architecture but wrong API calling convention.
- `gpt_5_5_codex` -> `gpt-5.5`: GPT 5.5 via Codex CLI at xhigh reasoning effort. Successor to GPT 5.4 — matches gpt_5_4_codex config exactly so the comparison measures model capability delta, not harness differences. Expected to produce similar ~$16/run cost band.
- `gpt_5_6_sol` -> `gpt-5.6-sol`: GPT 5.6 Sol via Codex CLI at xhigh reasoning effort, run 2026-07-10 on the user's ChatGPT subscription (codex logged in via ChatGPT; probe confirmed gpt-5.6-sol + xhigh accepted). OpenAI's new-generation flagship (Sol/Terra/Luna naming), public release delayed by a US government review; API rates $5/$30 per M (same card as GPT 5.5). Mirrors gpt_5_4_codex/gpt_5_5_codex config so the comparison measures model delta, not harness differences. A gpt-5.6-sol-pro variant also exists on OpenRouter (untested, likely the $30/$180-class tier).
- `sakana_fugu` -> `sakana/fugu`: Sakana Fugu default router via Sakana's OpenAI-compatible Chat Completions API (https://api.sakana.ai/v1). Docs list 1M context, streaming, tools/tool_choice, and reasoning effort high/xhigh/max; this opencode path uses @ai-sdk/openai-compatible with SAKANA_AI_TOKEN because the benchmark harness expects Chat Completions-style tool calling. Skipped by default until an in-house benchmark run confirms cost, latency, and long-session stability.
- `sakana_fugu_ultra` -> `sakana/fugu-ultra`: Sakana Fugu Ultra via Sakana's OpenAI-compatible Chat Completions API. Docs describe it as the higher-quality/deeper multi-agent Fugu mode with 1M context, tools/tool_choice, streaming, and fixed pay-as-you-go pricing for fugu-ultra-20260615 ($5/M input, $30/M output; higher above 272K context). Skipped by default because long benchmark sessions may be slower/costlier and should be launched explicitly.
- `gpt_5_4_multi_balanced` -> `gpt-5.4`: Codex multi-agent: xhigh plans and orchestrates, medium/balanced handles coding. Tests whether GPT 5.4 at lower effort can execute well when the xhigh parent makes decisions. Comparison against gpt_5_4_codex (xhigh alone).
- `gpt_5_4_multi_balanced_forced` -> `gpt-5.4`: Forced-delegation variant of gpt_5_4_multi_balanced. Same config as the free-choice version — the only difference is the forcing prompt at prompts/benchmark_prompt_forced_delegation.txt. Measures whether forcing the orchestrator pattern changes output quality or cost on Codex's multi_agent feature.
- `gpt_5_4_multi_faster_forced` -> `gpt-5.4`: Forced-delegation variant of gpt_5_4_multi_faster. Compares against the free-choice version to isolate the effect of the forcing prompt.
- `gpt_5_4_multi_faster` -> `gpt-5.4`: Codex multi-agent: xhigh plans, low handles fast coding. Tests the 'cheap executor' hypothesis — whether minimal reasoning on the subagent is enough when the parent provides the plan.
- `kimi_k2_5` -> `openrouter/moonshotai/kimi-k2.5`: Chosen as the latest/highest Kimi variant listed by OpenRouter locally.
- `kimi_k2_6` -> `openrouter/moonshotai/kimi-k2.6`: Direct successor to K2.5. $0.74/$4.66 per M, 256K context, tool calling supported. Tests whether K2.6 fixes K2.5's Tier 3 hallucinations of RubyLLM add_message() and complete().
- `kimi_k2_7_code` -> `openrouter/moonshotai/kimi-k2.7-code`: MoonshotAI Kimi K2.7 Code on OpenRouter. Direct successor to K2.6 for coding. OpenRouter lists 262K context, tool calling, structured outputs, and reasoning controls; pricing $0.95/M input and $4/M output. Tests whether the Kimi line keeps K2.6's Tier A trajectory while improving RubyLLM API accuracy and Rails app execution quality.
- `kimi_k3` -> `openrouter/moonshotai/kimi-k3`: Moonshot Kimi K3 on OpenRouter ($3/$15, 1M ctx, reasoning). HARNESS-INCOMPATIBLE with opencode as of 2026-07-16: K3's Moonshot endpoint enforces strict JSON-schema validation and rejects opencode's tool definitions ('when using anyOf, type should be defined in anyOf items instead of the parent schema'). Controlled probe confirmed K3 tool-calling works with clean schemas — the model is fine, the opencode toolset pairing is broken (same genre as DeepSeek V4 Pro reasoning_content). Only upstream is Moonshot itself (no alternate OR provider to route around). Retest when opencode normalizes tool schemas or another provider serves K3. K2.5/K2.6/K2.7 ran fine with identical tooling.
- `kimi_k3_cli` -> `kimi-code/k3`: Kimi K3 via Moonshot's own Kimi Code CLI (runner_type kimi, added 2026-07-16), billed via Kimi subscription OAuth. Workaround for the opencode incompatibility (Moonshot rejects opencode's anyOf tool schemas) — same precedent as GPT 5.4 via Codex CLI. 256K context on this plan. Non-interactive via -p + --output-format stream-json; phase 2 via -S <session>; tokens from kimi export wire.jsonl step.end sums.
- `kimi_k2_7_coding_cli` -> `kimi-code/kimi-for-coding`: K2.7 Coding via Kimi Code CLI — HARNESS-COMPARISON run against the opencode kimi_k2_7_code result (86/A). Managed 'kimi-for-coding' model; Moonshot positions it as the K2.7 Code lineage though the serving snapshot may differ from OpenRouter's kimi-k2.7-code. skip_by_default: comparison study only, not part of the default set. Note: the Kimi subscription does NOT expose K2.5/K2.6, so the harness comparison is limited to the K2.7 generation.
- `grok_4_3` -> `openrouter/x-ai/grok-4.3`: x.AI Grok 4.3 via OpenRouter. $1.25/$2.50 per M (mid-tier), 1M context, tool calling supported. First Grok variant in the benchmark — tests whether Grok's RubyLLM API recall is correct (real chat.ask path) or hits the same fluent-DSL/chat.complete hallucinations seen in some Tier B/C cloud models. Pricing positions it between Kimi K2.6 ($0.50/$2.50) and DeepSeek V4 Pro ($0.44/$0.87), well below Opus ($5/$25).
- `grok_4_5` -> `openrouter/x-ai/grok-4.5`: xAI Grok 4.5 via OpenRouter (snapshot grok-4.5-20260708, released 2026-07-08). xAI's flagship 'smartest model' with frontier coding claims. 500K context, $2/$6 per M, tool calling + reasoning supported. Reasoning effort maxes at 'high' which is the DEFAULT (no xhigh tier; reasoning cannot be disabled), so the standard run is already highest-effort. Tests whether 4.5 fixes the Grok-family weaknesses: 4.20's Tier D collapse and 4.3's dead Stimulus wiring, bypassed test stubs, and stale claude-3.7-sonnet pin.
- `mimo_v2_5_pro` -> `openrouter/xiaomi/mimo-v2.5-pro`: Xiaomi's flagship coding model. $1/$3 per M, 1M context, tool calling supported. Brand-new family we haven't tested — competitive pricing with mid-tier Chinese models like Kimi and GLM.
- `glm_5` -> `openrouter/z-ai/glm-5`: Chosen as the latest/highest GLM variant listed by OpenRouter locally; this replaces the local GLM test. Skipped by default because it completed with errors in the previous benchmark pass.
- `qwen3_6_plus` -> `openrouter/qwen/qwen3.6-plus`: Added from OpenRouter cloud availability; chose the non-preview Qwen 3.6 Plus variant exposed locally. Skipped by default because it completed with errors in the previous benchmark pass.
- `qwen3_5_397b_cloud` -> `openrouter/qwen/qwen3.5-397b-a17b`: The raw OpenRouter Qwen 3.5 397B A17B base — the architecture Nex AGI fine-tuned into Nex-N2-Pro. Force-run 2026-06-15 as a controlled base-vs-fine-tune comparison: completed_with_errors at 42/100 Tier C (hallucinates the RubyLLM API via chat.system/chat.user/response.text, builds in a nested chat-app/ subdir, tests mock the hallucinated API). Kept skip_by_default because it's a broken Tier C reference run, not a routine target. See Cross-Cutting Finding #6 in docs/success_report.md.
- `gemma4_31b_cloud` -> `openrouter/google/gemma-4-31b-it`: Google Gemma 4 31B IT BF16 served via Ollama's hosted cloud (https://ollama.com). Originally added to bypass the local llama.cpp parser bugs that caused infinite repetition loops on local Q3/Q8 GGUFs. Curl tests confirm the model itself works correctly for tool calling. **However, opencode benchmark runs hit HTTP 504 Gateway Timeout consistently around 20-24K total tokens of conversation history** — Cloudflare edge appears to enforce a ~100s per-request limit which 20K+ token prefill exceeds. Tried maxRetries:5 (didn't help — failures are consistent, not transient). Set limit.context:16384 to force opencode history trimming below the wall. Skipped by default until either Ollama Cloud raises the timeout or we test via Google's native Gemini API. Requires OLLAMA_API_KEY env var with Ollama Cloud subscription.
- `llama4_scout_cloud` -> `openrouter/meta-llama/llama-4-scout`: Added as the OpenRouter cloud Llama 4 Scout benchmark counterpart to the unusable local Scout path. Skipped by default because it does not currently resolve cleanly in this opencode build.
- `nemotron_3_super_cloud` -> `openrouter/nvidia/nemotron-3-super-120b-a12b`: Added as the closest OpenRouter cloud Nemotron line available after local Nemotron Cascade 2 proved unusable in this harness. Skipped by default because it still needs a clean first benchmark run.
- `minimax_m2_7` -> `openrouter/minimax/minimax-m2.7`: Chosen as the largest/latest MiniMax variant listed by OpenRouter locally.
- `minimax_m3` -> `openrouter/minimax/minimax-m3`: MiniMax M3 on OpenRouter. Direct successor to MiniMax M2.7. 1M context, tool calling supported, $0.30/M input and $1.20/M output. Tests whether the new MiniMax release fixes M2.7's RubyLLM batch-form hallucination and becomes a viable low-cost Rails/RubyLLM builder. Cloud-only: a GGUF exists (unsloth/MiniMax-M3-GGUF, ollama.com/library/minimax-m3), but as a 230B-total MoE it needs ~195 GB (Q3) / ~264 GB (Q4) for weights alone; usable inference also needs KV cache, runtime scratch, and OS headroom, so it exceeds both local profiles (RTX 5090 32 GB; Strix Halo ≤128 GB) — see docs/llama-swap.md.
- `deepseek_v3_2` -> `openrouter/deepseek/deepseek-v3.2`: Latest DeepSeek model on OpenRouter. Input $0.26/M, output $0.38/M.
- `deepseek_v4_flash` -> `openrouter/deepseek/deepseek-v4-flash`: DeepSeek V4 Flash — budget-tier variant at $0.14/M input, $0.28/M output (cheaper than V3.2). 1M context. Tool calling supported via OpenRouter. Test whether V4 fixes the RubyLLM API hallucination that made V3.2 Tier 3. Phase 2 disabled: DeepSeek's thinking-mode API rejects replayed `reasoning_content` tokens from opencode's session continuation.
- `deepseek_v4_pro` -> `openrouter/deepseek/deepseek-v4-pro`: DeepSeek V4 Pro — premium variant at $1.74/M input, $3.48/M output. 1M context. Uses thinking mode by default which requires the client to echo reasoning_content on subsequent turns (opencode doesn't). reasoning=false tells opencode to treat it as a non-reasoning model so it won't extract/pass back reasoning_content.
- `step_3_5_flash` -> `openrouter/stepfun/step-3.5-flash`: StepFun Step 3.5 Flash on OpenRouter. Input $0.10/M, output $0.30/M.
- `step_3_7_flash` -> `openrouter/stepfun/step-3.7-flash`: StepFun Step 3.7 Flash on OpenRouter (snapshot step-3.7-flash-20260528). Added 2026-06-15 per community Issue #7. 256K context, tool calling supported, $0.20/M input and $1.15/M output. Tests whether 3.7 fixes Step 3.5's ruby-openai bypass (3.5 scored 56/C ⚠️ bypass for using the wrong gem instead of ruby_llm).
- `claude_sonnet_4_6` -> `openrouter/anthropic/claude-sonnet-4.6`: Anthropic Claude Sonnet 4.6 on OpenRouter. Input $3.00/M, output $15.00/M.
- `gemini_3_1_pro` -> `openrouter/google/gemini-3.1-pro-preview`: Latest Google Gemini model with enhanced SWE performance and agentic reliability. Input $2.00/M, output $12.00/M.
- `gemini_3_5_flash` -> `openrouter/google/gemini-3.5-flash`: Google Gemini 3.5 Flash on OpenRouter (GA snapshot gemini-3.5-flash-20260519). Added 2026-06-15 to run + score in-house after community PR #6 submitted pre-scored results without the gitignored project code. Input $1.50/M, output $9.00/M, 1M context. Tests whether a Flash-tier model can match the 3.1 Pro RubyLLM correctness baseline.
- `grok_4_20` -> `openrouter/x-ai/grok-4.20`: xAI's latest flagship on OpenRouter. Fastest model in the benchmark (8 min) but produced architecturally broken code: bypassed RubyLLM with ruby-openai (only in dev/test group, NameError in prod), used format.turbo_stream without installing turbo-rails, RUBY_VERSION=4.0.2 Dockerfile bug. Tier 3 — broken core.
- `glm_5_1` -> `zai/glm-5.1`: Z.ai's latest flagship GLM model. Uses Z.ai coding plan endpoint at https://api.z.ai/api/coding/paas/v4 (NOT the general /api/paas/v4) — Lite subscription includes glm-5.1 only via the coding endpoint. Completed in 22 min with 24 tests, correct primary RubyLLM.chat/ask usage, but invented chat.user/chat.assistant for multi-turn history seeding (single-turn works, multi-turn crashes). Tier 2 — works with caveats.
- `glm_5_2` -> `zai/glm-5.2`: Z.ai's newest flagship GLM (released 2026-06). Served on the coding plan endpoint at https://api.z.ai/api/coding/paas/v4 (live and key-verified 2026-06-14, though not yet in that endpoint's /models listing; not on OpenRouter yet). Like all GLM models it returns reasoning in reasoning_content with empty content by default — the zai provider wiring already handles this for GLM 5.1. Tests whether 5.2 fixes 5.1's hallucinated chat.user/chat.assistant multi-turn DSL (the bug that put 5.1 in Tier C).
- `qwen3_5_27b_claude` -> `ollama/qwen/qwen3.5-27b-claude`: Qwen 3.5 27B distilled from Claude 4.6 Opus reasoning traces (Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled). Tests whether Claude reasoning distillation transfers RubyLLM API correctness — most non-Anthropic models hallucinate the gem's API, so a Claude-distilled Qwen is an interesting natural experiment.
- `qwen2_5_coder_32b` -> `ollama/qwen/qwen2.5-coder-32b`: Most popular dedicated coder of the Qwen 2.5 generation. Sourced from Ollama (Q4_K_M ~19 GB). On NVIDIA 5090 fits with 64K context.
- `qwen3_coder_30b` -> `ollama/qwen/qwen3-coder-30b`: Qwen 3 dedicated coder variant (the regular 30B, not the 51 GB qwen3-coder-next-ctx). Direct comparison with the general qwen3:32b. Sourced from Ollama (Q4_K_M ~18 GB).
- `qwen3_5_27b_sushi_coder` -> `ollama/qwen/qwen3.5-27b-sushi-coder`: Qwen 3.5 27B fine-tuned via reinforcement learning on Codeforces problems (bigatuna/Qwen3.5-27b-Sushi-Coder-RL). Q4_K_M ~15 GB. Tests whether RL coding fine-tuning transfers correct RubyLLM API usage — direct comparison with the Claude reasoning distillation (qwen3.5:27b-claude) and the general qwen3.5:35b.
- `gemma4_31b_cloud` -> `ollama-cloud/gemma4-31b`: Google Gemma 4 31B IT BF16 served via Ollama's hosted cloud (https://ollama.com). Bypasses the local llama.cpp parser bugs that caused infinite repetition loops on local Q3/Q8 GGUFs. Tests whether Gemma 4 is actually capable for agentic tool calling when served by Google's full-precision infrastructure rather than crippled by quantization + parser regressions. Requires OLLAMA_API_KEY env var with an Ollama Cloud subscription.
- `qwen3_7_max` -> `openrouter/qwen/qwen3.7-max`: Alibaba Qwen3.7 Max on OpenRouter. Added 2026-06-15 to run + score in-house after community PR #4 submitted pre-scored results (82/A on a phase-2 DNF) without the gitignored project code. Tests whether the flagship Qwen Max tier achieves correct RubyLLM API usage and completes phase 2 validation under our harness.
- `nex_n2_pro` -> `openrouter/nex-agi/nex-n2-pro:free`: Nex AGI Nex-N2-Pro on OpenRouter (free tier). Agentic MoE, 397B total / 17B active, built on the Qwen3.5-397B-A17B architecture with 'Adaptive Thinking'; 262K context, supports tool calling. Added 2026-06-15. Vendor claims rival GPT-5.5/Opus 4.7 on coding (SWE-Bench Verified ~80.8). Tests whether Nex AGI's agentic fine-tune of the Qwen3.5 base fixes the RubyLLM API hallucination that the Qwen3.5 family typically exhibits. Caveat: the :free endpoint has aggressive rate limits that may stall a long agentic run.

## Results

| Model | Provider | Warmup ctx | Status | Elapsed (s) | Total tokens | Tok/s | Works? | Files | Notes |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |
| Gemma 4 31B | ollama | - | failed | 364.15 | - | - | no | 1277 | Generated files do not resemble the requested Rails project. |
| GLM 4.7 Flash BF16 | ollama | - | failed | 1208.80 | 41709 | 34.50 | yes | 2029 | Exit code -15. Rails app, tests, README, and container files detected. |
| Llama 4 Scout | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3 32B | ollama | - | completed_with_errors | 1271.45 | 22922 | 18.03 | no | 87 | Generated files do not resemble the requested Rails project. |
| Qwen 3 Coder Next | ollama | - | completed | 1041.72 | 39054 | 37.49 | yes | 1675 | Rails app, tests, README, and container files detected. |
| Qwen 3.5 35B | ollama | - | completed | 1671.20 | 76919 | 46.03 | yes | 1478 | Rails app, tests, README, and container files detected. |
| Qwen 3.6 35B | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3.5 122B | ollama | - | completed | 2564.18 | 57472 | 22.41 | yes | 1503 | Rails app, tests, README, and container files detected. |
| GPT OSS 20B | ollama | - | failed | 609.59 | 32553 | 53.40 | no | 1310 | Generated files do not resemble the requested Rails project. |
| Nemotron Cascade 2 | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Claude Opus 4.6 | openrouter | - | completed | 970.51 | 136806 | 347.18 | yes | 1536 | Rails app, tests, README, and container files detected. |
| Claude Opus 4.7 | openrouter | - | completed | 1091.67 | 118216 | 328.24 | yes | 11345 | Rails app, tests, README, and container files detected. |
| Claude Opus 4.8 | openrouter | - | completed | 1008.12 | 104470 | 478.63 | yes | 2838 | Rails app, tests, README, and container files detected. |
| Claude Fable 5 | openrouter | - | completed | 1458.86 | 103119 | 436.22 | yes | 2710 | Rails app, tests, README, and container files detected. |
| Claude Fable 5 (re-release) | openrouter | - | completed | 1058.76 | 62493 | 260.74 | yes | 1860 | Rails app, tests, README, and container files detected. |
| Claude Sonnet 5 | openrouter | - | completed | 1625.32 | 128727 | 372.26 | yes | 100 | Rails app, tests, README, and container files detected. |
| opencode Opus 4.7 + GLM 5.1 coder | openrouter | - | completed | 618.15 | 108279 | 947.65 | yes | 1888 | Rails app, tests, README, and container files detected. |
| opencode Opus 4.7 + GLM 5.1 coder (FORCED delegation) | openrouter | - | completed | 765.82 | 111912 | 633.13 | yes | 1703 | Rails app, tests, README, and container files detected. |
| opencode Opus 4.7 + Kimi K2.6 coder (FORCED delegation) | openrouter | - | failed | 1509.82 | 57073 | 37.80 | yes | 1642 | Exit code -15. Rails app, tests, README, and container files detected. |
| opencode Opus 4.7 + Qwen 3.6 Plus coder (FORCED delegation) | openrouter | - | completed | 668.45 | 103920 | 188.13 | yes | 138 | Rails app, tests, README, and container files detected. |
| opencode Opus 4.7 + DeepSeek V4 Pro coder (FORCED delegation) | openrouter | - | completed | 1931.30 | 124949 | 691.17 | yes | 1902 | Rails app, tests, README, and container files detected. |
| opencode GPT 5.5 + Qwen 3.6 Plus coder (FORCED delegation) | openrouter | - | failed | 1113.17 | 20457 | 18.38 | no | 0 | Exit code -15. Project directory is empty. |
| opencode GPT 5.5 + DeepSeek V4 Pro coder (FORCED delegation) | openrouter | - | completed_with_errors | 226.74 | 23770 | 848.32 | no | 0 | Project directory is empty. |
| opencode Opus 4.7 + Qwen 3.6 local coder (FORCED delegation) | openrouter | - | completed | 768.05 | 93868 | 1603.48 | yes | 1537 | Rails app, tests, README, and container files detected. |
| opencode Opus 4.7 + Qwen 3.6 local coder | openrouter | - | completed | 1165.77 | 126817 | 231.15 | yes | 1623 | Rails app, tests, README, and container files detected. |
| GPT 5.4 Pro | openrouter | - | failed | 2910.65 | 63491 | 21.81 | partial | 1118 | Exit code -15. Some expected benchmark artifacts exist, but the scaffold looks incomplete. |
| GPT 5.4 xHigh (Codex) | codex | - | completed | 1312.34 | 7643800 | 5824.56 | yes | 1808 | Rails app, tests, README, and container files detected. |
| GPT 5.5 xHigh (Codex) | codex | - | completed | 1080.90 | 4904634 | 4537.55 | yes | 1553 | Rails app, tests, README, and container files detected. |
| GPT 5.6 Sol xHigh (Codex) | codex | - | completed | 1011.30 | 3918623 | 3874.84 | yes | 1373 | Rails app, tests, README, and container files detected. |
| Sakana Fugu | sakana | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Sakana Fugu Ultra | sakana | - | completed | 1297.34 | 142469 | 492.26 | yes | 1967 | Rails app, tests, README, and container files detected. |
| GPT 5.4 xHigh + medium coder (Codex multi-agent) | codex | - | completed | 1271.76 | 5438106 | 4276.05 | yes | 1671 | Rails app, tests, README, and container files detected. |
| GPT 5.4 xHigh + medium coder (FORCED delegation) | codex | - | completed | 1828.09 | 987886 | 540.39 | yes | 2960 | Rails app, tests, README, and container files detected. |
| GPT 5.4 xHigh + low coder (FORCED delegation) | codex | - | completed | 3153.95 | 4780483 | 1515.71 | yes | 1852 | Rails app, tests, README, and container files detected. |
| GPT 5.4 xHigh + low coder (Codex multi-agent) | codex | - | completed | 1213.33 | 4275845 | 3524.06 | yes | 1716 | Rails app, tests, README, and container files detected. |
| Kimi K2.5 | openrouter | - | completed | 1738.77 | 63638 | 160.14 | yes | 3405 | Rails app, tests, README, and container files detected. |
| Kimi K2.6 | openrouter | - | completed | 1181.65 | 102250 | 258.32 | yes | 1890 | Rails app, tests, README, and container files detected. |
| Kimi K2.7 Code | openrouter | - | completed | 1295.74 | 86967 | 486.83 | yes | 1687 | Rails app, tests, README, and container files detected. |
| Kimi K3 | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Kimi K3 (Kimi Code CLI) | kimi | - | completed | 1533.45 | 884937 | 4232.93 | yes | 2592 | Rails app, tests, README, and container files detected. |
| Kimi K2.7 Coding (Kimi Code CLI) | kimi | - | completed | 976.24 | 1620218 | 8167.24 | yes | 2989 | Rails app, tests, README, and container files detected. |
| Grok 4.3 | openrouter | - | completed | 900.07 | 46929 | 175.07 | yes | 2355 | Rails app, tests, README, and container files detected. |
| Grok 4.5 | openrouter | - | completed | 964.07 | 154335 | 553.25 | yes | 1564 | Rails app, tests, README, and container files detected. |
| Xiaomi MiMo V2.5 Pro | openrouter | - | completed | 644.40 | 80447 | 288.04 | yes | 1554 | Rails app, tests, README, and container files detected. |
| GLM 5 | openrouter | - | completed | 1033.99 | 59378 | 400.01 | yes | 1680 | Rails app, tests, README, and container files detected. |
| Qwen 3.6 Plus | openrouter | - | completed | 1031.84 | 88940 | 182.91 | yes | 744 | Rails app, tests, README, and container files detected. |
| Qwen 3.5 397B Cloud | openrouter | - | completed_with_errors | 920.18 | 96659 | 337.43 | no | 169 | Generated files do not resemble the requested Rails project. |
| Gemma 4 31B Cloud | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Llama 4 Scout Cloud | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Nemotron 3 Super Cloud | openrouter | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| MiniMax M2.7 | openrouter | - | completed | 847.23 | 79743 | 574.52 | yes | 100 | Rails app, tests, README, and container files detected. |
| MiniMax M3 | openrouter | - | failed | 3172.78 | - | - | yes | 1899 | Rails app, tests, README, and container files detected. |
| DeepSeek V3.2 | openrouter | - | completed | 3606.46 | 115278 | 53.37 | yes | 99 | Rails app, tests, README, and container files detected. |
| DeepSeek V4 Flash | openrouter | - | completed | 155.12 | 51929 | 334.77 | yes | 1704 | Rails app, tests, README, and container files detected. |
| DeepSeek V4 Pro | openrouter | - | failed | 1359.25 | 61170 | 45.00 | partial | 1972 | Some expected benchmark artifacts exist, but the scaffold looks incomplete. |
| Step 3.5 Flash | openrouter | - | completed | 2273.00 | 156267 | 242.11 | yes | 1606 | Rails app, tests, README, and container files detected. |
| Step 3.7 Flash | openrouter | - | completed | 1623.79 | 181572 | 771.20 | yes | 104 | Rails app, tests, README, and container files detected. |
| Claude Sonnet 4.6 | openrouter | - | completed | 966.85 | 127067 | 532.26 | yes | 2042 | Rails app, tests, README, and container files detected. |
| Gemini 3.1 Pro | openrouter | - | completed | 811.00 | 104034 | 508.18 | yes | 138 | Rails app, tests, README, and container files detected. |
| Gemini 3.5 Flash | openrouter | - | completed | 1079.70 | 165172 | 442.50 | yes | 1983 | Rails app, tests, README, and container files detected. |
| Grok 4.20 | openrouter | - | completed | 502.68 | 63457 | 412.54 | yes | 108 | Rails app, tests, README, and container files detected. |
| GLM 5.1 | zai | - | completed | 1291.19 | 81666 | 166.62 | yes | 1571 | Rails app, tests, README, and container files detected. |
| GLM 5.2 | zai | - | completed | 2602.50 | 92430 | 151.63 | yes | 811 | Rails app, tests, README, and container files detected. |
| Qwen 3.5 27B Claude Distilled | ollama | - | timeout | 5400.95 | 75753 | 14.03 | partial | 2231 | Timed out. Some expected benchmark artifacts exist, but the scaffold looks incomplete. |
| Qwen 2.5 Coder 32B | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3 Coder 30B | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen 3.5 27B Sushi Coder RL | ollama | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Gemma 4 31B (Ollama Cloud) | ollama-cloud | - | not_run | - | - | - | n/a | 0 | Run has not been executed yet. |
| Qwen3.7 Max | openrouter | - | completed | 1130.81 | 142463 | 500.92 | yes | 1916 | Rails app, tests, README, and container files detected. |
| Nex-N2-Pro | openrouter | - | completed | 1490.98 | 145823 | 559.42 | yes | 1923 | Rails app, tests, README, and container files detected. |

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

