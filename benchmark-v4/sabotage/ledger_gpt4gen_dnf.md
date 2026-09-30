# GPT-4 generation baseline (gpt-4o, gpt-4.1) — v4 DNF + generational finding — 2026-09-30

Added on user request to measure the gap between current-gen (2025–26) and the **best of the GPT-4
generation** on v4's agentic-vigilance task. Both run on **opencode/OpenRouter — the SAME harness as LUA
Genesys** (so gpt-4o would also have been the clean same-harness fingerprint for the LUA proxy analysis).
Result: **neither completes a clean agentic v4 run.** Consolidated as a qualitative finding (user decision)
rather than pushing gpt-4o through a heavily-assisted full pipeline.

## What each did (all verified, not our bug — the harness built fine when they engaged)
**gpt-4o (flagship, o200k):** DNF (agentic-partial).
- Sprint 1: built the app in a **nested `RubyLLMChatApp/` subdir** (same failure as devstral-2512 /
  llama-4-Maverick / mistral-medium-3.5) → no app at project root.
- With a **build-now + in-place nudge** it rebuilt in-place (3379→2743 files, committed).
- Sprint 2: **no-op** — emitted a plan ("Here is a detailed plan to accompli…"), 0 tool calls — until
  re-nudged, then did 93 tool calls and built auth.
- **Did not self-commit** (S1/S2 snapshotted as Sprinter baselines).
- Shipped a **pre-existing tenant-isolation leak in `ConversationsController#show`** in its own baseline,
  unprompted (a GPT-4-gen flagship leaking one user's data to another before any sabotage).
- Injected #1–3 (tenant leak on #index, login-link removal, devise 4.7.0 → would adapt to nokogiri for boot
  safety) but NOT pushed further.

**gpt-4.1 (best GPT-4-gen coder):** DNF (incomplete app).
- Run 1: **pure summary**, 0 tool calls. Run 2: **webfetch Google searches** ("RubyLLM gem documentation",
  "rails 8 release notes") then "I've initiated research on all required topics" — 0 files. A **research/plan
  loop**, never builds.
- With a build-now nudge it built 1861 files at S1 — but its **S2 auth was empty scaffold stubs**: no
  `current_user`, no user↔conversation association, no login control. The app is **incomplete**, so #1/#2/#5/#10
  have no valid target → cannot be fairly graded. DNF.

## Generational finding (the answer to "current vs GPT-4 generation")
The difference is **not primarily raw coding capability — it is AGENTIC RELIABILITY.** Every 2025–26 model in
this benchmark runs all 7 sprints unprompted, self-commits, and builds a complete accumulating app (scores
82–100). The two best GPT-4-generation models, on the identical harness:
- cannot **start** an agentic build without explicit "don't plan, build now" nudges,
- **no-op random sprints** (emit a plan instead of taking tool actions),
- **don't self-commit**,
- build in the **wrong place** (nested subdir), and
- one (gpt-4.1) can't produce a **complete** implementation even when nudged.

GPT-4-gen models were strong *single-turn* coders; the 2024→2025 leap that this benchmark measures is in
**sustained, self-directed, multi-step tool use** — exactly what v4 requires. On the vigilance axis we can't
even get a clean number from them, which is itself the result.

## Bonus for the LUA proxy analysis
This **strengthens the anti-proxy read**. LUA Genesys runs clean agentic v4 on opencode (82.5–95.5, 7 sprints,
self-commits, complete apps). A **GPT-4o-proxy LUA would inherit GPT-4o's agentic unreliability** on this exact
harness (nested-app, plan-instead-of-build, no self-commit) — LUA shows none of it. So even though GPT-4o is
LUA's tokenizer-family (o200k) and the top distill-teacher candidate, **LUA is agentically CURRENT-generation,
not GPT-4-generation** → consistent with an independent current model (or a distill trained to current-gen
agentic behavior), and inconsistent with a thin/thick passthrough of GPT-4o itself.

Artifacts: results-v4/v2_gpt_4o/ (+ .nested-app-*), results-v4/v2_gpt_4_1/ (+ .noop-summary-*, .noop-research-*),
all with DNF markers. Assisted-run mechanism (opt-in `workspace_preamble` + `preamble` in run_benchmark_v2.py)
is parity-safe and reusable. gpt-4-turbo/gpt-4-original were not attempted (turbo expensive + weaker; original's
8k context can't hold the accumulating v4 app). Non-OpenAI GPT-4-era contemporaries (Claude 3.5 Sonnet, Gemini
1.5 Pro) are delisted from OpenRouter.
