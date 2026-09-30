# LUA Vision Genesys PI — provenance forensics (black-box)

Self-contained, reproducible test suite to assess whether the LUA Vision **Genesys PI** models are a
genuinely independent model or a derivative (finetune / continued-pretrain / distillation / rebadge / proxy)
of a known family (Qwen, DeepSeek, Llama, Mistral, GPT/gpt-oss, Claude, Gemini).

**Isolated from the main v4 benchmark** — nothing here touches `benchmark-v4/`, `results-v4/`, or the ranking.

## Why these tests (signal hierarchy)
1. **Tokenizer fingerprint** — strongest exclusion. A finetune/distill keeps its base's tokenizer; the token
   *counts* for fixed strings are a near-immutable family fingerprint.
2. **Glitch / undertrained tokens** — separates "borrowed vocab + fresh embeddings" from "teacher's embeddings
   kept" (a gpt-4o/gpt-oss finetune tends to reproduce the *teacher's specific* glitch substitution).
3. **Special-/Harmony-token behavior + gateway/infra headers** — stack fingerprint; catches proxies + gpt-oss.
4. **Parallel teacher-similarity grid** — the only black-box move that *leans* on distillation: run identical
   idiosyncratic prompts on LUA + a reference panel and see if LUA clusters with one teacher.
5. Idiosyncratic failures / corpus tells — weaker corroboration.

Credit: test design refined against a Grok critique (gpt-oss/o200k_harmony hypothesis, X+X delta, glitch panel,
similarity grid, infra leaks) and Paulo Câmara's (LUA co-founder) own recommended methods (tokenizer counts,
self-ID as clue-not-proof, weight fingerprinting — the last needs weights, out of black-box scope).

## Layout
- `lib/clients.py` — stdlib clients. `LUA_API_KEY` + `OPENROUTER_API_KEY` read from `~/.config/zsh/secrets`
  (never printed). Reference panel via OpenRouter (`PANEL` dict): gpt-oss-120b, gpt-5, gpt-4o, claude-4.5,
  qwen3-max/235b, deepseek, llama-3.3, gemini-2.5-flash.
- `tokenizer_forensics.py` — Test 1+3: token-count table (X+X−X delta) vs o200k/cl100k/Qwen/DeepSeek/Llama/
  Mistral + special-token single-token probe.
- `behavioral_probes.py` — Test 2+3: glitch tokens (LUA vs panel) + special-token injection (obedience/error).
- `similarity_grid.py` — Test 5: idiosyncratic prompts × panel; char-4gram cosine + structural features.
- `results/*.latest.json` (+ timestamped) — raw outputs for every run.

## Reproduce
```
pip install --user tiktoken transformers        # tokenizers (o200k via tiktoken; Qwen/DeepSeek/Llama/Mistral via HF)
export HF_HUB_DISABLE_PROGRESS_BARS=1 TRANSFORMERS_VERBOSITY=error TOKENIZERS_PARALLELISM=false
python3 lua-forensics/tokenizer_forensics.py
python3 lua-forensics/behavioral_probes.py
python3 lua-forensics/similarity_grid.py
```
Keys must be in `~/.config/zsh/secrets` as `export LUA_API_KEY=...` / `export OPENROUTER_API_KEY=...`.

## Findings snapshot (2026-09-30)
- Tokenizer = **o200k_base** (distance 3 vs next family Llama3 77; Qwen 206, DeepSeek 290). Rules out a
  Qwen/DeepSeek/Llama/Mistral vocab rebadge with high confidence.
- Gateway headers: all `x-lua-*` custom, **no** openai-/anthropic-/cf-/vllm passthrough tells.
- Glitch tokens: LUA is undertrained on o200k CJK glitches (o200k-native) but its mangling **differs from
  gpt-4o/gpt-oss** → leans *own embeddings on borrowed vocab*, not a gpt-oss/gpt-4o weight-continuation.
- Injection: distinctive custom `prompt_injection_detected` guard; no role obedience, no family/stack leak.
- Similarity grid: see `results/similarity_grid.latest.json` and `docs/success_report.v4.lua_forensics.md`.

Full write-up + confidence table: `../docs/success_report.v4.lua_forensics.md`.
