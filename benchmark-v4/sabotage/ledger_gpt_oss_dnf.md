# GPT-OSS 120B & 20B — v4 DNF (opencode harness-incompatibility) — 2026-09-30

Both sizes DNF at sprint01 in the opencode/OpenRouter harness. **Not an instrumentation bug** —
diagnosed with four independent checks (raw API tool-calls OK; trivial-task build OK; bash cwd==--dir;
provider pin honored). Root cause is gpt-oss's own behavior in opencode:

1. **Weak agentic persistence** — 120b runs `rails new .` (58-file bare skeleton) then ends its turn;
   20b writes ~2 files then stops. Never a working chat app. Reproduced across the DeepInfra provider
   pin and the workspace preamble.
2. **Tool-convention mismatch** — 20b tried OpenAI-native `apply_patch` (gpt-oss's trained file tool),
   which opencode doesn't expose (it offers write/edit). Same class as Kimi-K3's schema incompatibility.

Assisted, non-parity mitigations applied and verified working for what they target — workspace preamble
(fixed a separate /tmp/opencode write-misdirection) and DeepInfra pin (removes OpenRouter routing
variance) — but neither addresses the persistence/tool-vocabulary gap.

**Proxy-analysis relevance:** raw gpt-oss cannot complete v4 in opencode, whereas LUA Genesys runs
cleanly there (83–95.5). A thin/light stripped-Harmony-gpt-oss LUA would inherit this opencode
incompatibility; LUA's clean completion therefore argues against a light gpt-oss reskin (it would
require substantial tool-behavior retraining — effectively a new model).

Attempts preserved: results-v4/v2_gpt_oss_{120b,20b}.noop-wave-*, .partial-preamble-* (batch cleanup later).
