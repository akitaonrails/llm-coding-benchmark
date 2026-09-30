# LUA Vision Genesys PI — provenance forensics: DETAILS & FINDINGS
_Black-box investigation, 2026-09-30. Reproducible via the scripts in this directory (see README.md)._
_v2 (this file) supersedes v1: the improved glitch panel **removed** a v1 overclaim (see Test 2)._

**Question:** are the Genesys PI models a genuinely independent/new model, or a derivative (finetune /
continued-pretrain / distillation / rebadge / proxy) of Qwen, DeepSeek, Llama, Mistral, GPT/gpt-oss, or Claude?

**Access used:** LUA's OpenAI-compatible API (free eval key) + an OpenRouter reference panel (gpt-4o, gpt-4o-mini,
gpt-oss-120b, gpt-oss-20b, gpt-5, claude-sonnet-4.5, qwen3-max/235b, deepseek-chat, llama-3.3-70b,
gemini-2.5-flash) + local tokenizers (tiktoken o200k_base/o200k_harmony/cl100k; HF Qwen3/DeepSeek-V2/Llama3/
Mistral/BERTimbau/Tucano).

---

## The one fact that structures everything: the tokenizer

LUA serves on **`o200k_base`** (Test 1). A **finetune or continued-pretrain inherits its base model's
tokenizer** — you cannot change vocab without full retraining. So the provenance question splits into two branches
that need *different* candidate lists and *different* tests:

- **Branch A — finetune / continued-pretrain / rebadge.** The base **must** also be `o200k_base`. This is a hard,
  narrow filter (see "Candidate universe" below): almost nothing open qualifies.
- **Branch B — distillation / synthetic-data training.** A fresh student adopts whatever tokenizer it likes;
  choosing the public `o200k_base` says **nothing** about the teacher. Only the behavioral/similarity grid can
  speak here, and it speaks weakly (Test 5).

---

## Test 1 — Tokenizer fingerprint (DECISIVE)
Method: `content_tokens(S) = prompt_tokens(S+S) − prompt_tokens(S)` (cancels LUA's ~915-token injected system
prompt and the boundary). Strings pinned utf-8/NFC, trailing newline stripped, `repr` logged. House ≡ Enterprise
on every string (same tokenizer). Rebuilt run: `results/tokenizer_v2.latest.json`.

**Distance to LUA-enterprise (Σ|ref−LUA| over the probe strings):**

| tokenizer | distance | verdict |
|---|--:|---|
| **o200k_base** | **2** | match |
| o200k_harmony (as text) | 2 | same base vocab, see Test 3 |
| Llama3 | 68–77 | excluded |
| cl100k | ~143 | excluded (this is also Phi-4 / DBRX) |
| Qwen3 | 193–206 | excluded |
| DeepSeek | 255–290 | excluded |
| Mistral | ~330 | excluded |

Killers: CJK packs to o200k's count (Qwen/DeepSeek pack tighter to 30/34), digits×20 = 67 (Qwen/DeepSeek/Mistral
split to 200), emoji-ZWJ matches o200k alone. → **LUA's serving tokenizer is `o200k_base`.** Strong **exclusion**
of any Qwen/DeepSeek/Llama/Mistral rebadge that kept its native vocab.
Caveat: `o200k_base` is **public**, so this proves *non-derivation from other tokenizer families*, not positively
"OpenAI weights."

## Test 2 — Glitch / undertrained tokens (STRONG confirmation; v1 overclaim REMOVED)
"Repeat this exact string" × n, glitch set vs well-trained controls, LUA-house/enterprise + o200k panel. Rebuilt
with a proper token budget so reasoning models (gpt-5, gpt-oss) stop returning empty. `results/glitch_panel.latest.json`.

Aggregate fail-rate (glitch / control):

| model | glitch-fail | control-fail |
|---|--:|--:|
| LUA-house / LUA-enterprise | 0.38 / 0.38 | 0.0 / 0.0 |
| gpt-4o | 0.50 | 0.0 |
| gpt-4o-mini | 0.38 | 0.0 |
| gpt-oss-120b / gpt-oss-20b | 0.38 / 0.38 | 0.0 / 0.0 |
| gpt-5 | 0.38 | 0.14 |
| claude-4.5 / qwen3-max | 0.0 / 0.0 | 0.0 / 0.0 |

**Per-string mask — LUA and the entire o200k family agree 8/8:**
- MANGLE (all): `植物百科通`, `给主人留下些什么吧`, `彩神争霸`
- OK (all): `微信公众号`, `龙腾世纪`, `请稍候片刻`, `bagbogbo`, `Japgolly`

Claude & Qwen reproduce all 8 (those aren't glitches under *their* tokenizers). → **LUA has o200k-native
undertrained embeddings**, sharing the *exact* glitch mask of every OpenAI o200k model.

**v1 correction (important):** v1 argued LUA's *specific* substitution garbage differing from gpt-4o's "leans own
embeddings, against a weight-continuation." That inference is **withdrawn** — gpt-4o (`植物大香蕉网`), gpt-4o-mini
(`植物`) and gpt-oss-20b (`植物`) also produce *different* substitutions **from each other**, so substitution
variation is within-family sampling/size noise, not a lineage signal. **Glitch is an o200k-family *membership*
test, not a within-family discriminator.** It cannot separate "own model on o200k" from "OpenAI-family
derivative."

## Test 3 — Harmony special tokens + injection/gateway (MEDIUM)
Single-token test (content-token delta vs `o200k_harmony` native): the Harmony sentinels `<|start|>`,
`<|channel|>`, `<|message|>`, `<|call|>`, `<|end|>` encode to **~4 text tokens each under LUA**, **not 1** — so
LUA's vocab is plain **`o200k_base`, NOT gpt-oss's `o200k_harmony`** (which has those as native single tokens).
→ **tokenizer-level negative for the gpt-oss lineage** (no Harmony special vocab). `<|endoftext|>` also text-splits.
Gateway headers: all custom `x-lua-*` (`x-lua-route-id: fp_…`, `x-lua-processing-ms`, own
`x-ratelimit-tokens-limit: 2000000`); **no** `openai-*`/`anthropic-*`/`cf-*`/`vllm`/`openrouter` tells → not a
thin passthrough. Injection: ChatML/Llama-BOS → custom **`prompt_injection_detected`** guard; DeepSeek/Gemma/
`Human:`/`Assistant:` → stays on persona, no base-family leak, no stack name in any error.

## Test 4 — API surface / gateway params (MEDIUM — OpenAI-shaped, not an open-model server)
LUA **rejects** `temperature`, `top_p`, `n`, `presence_penalty`, `logprobs`, **and** the open-model sampling
params `min_p` / `top_k` / `repetition_penalty` / `enable_thinking` (all `400 unsupported_parameter`).
It **accepts** the OpenAI-proprietary `reasoning_effort`, plus `seed` / `stop` / `response_format` (`200`).
`results/gateway.latest.json`. → The control surface is **OpenAI-shaped**; it rejects exactly the params a
vLLM/SGLang server fronting Qwen/Llama/DeepSeek would accept. Argues against a Chinese-open-model backend behind a
proxy, and (with the distinct v4 capability profile, Genesys PI 82–95.5) against a thin GPT/Claude passthrough.
Context: enterprise silently accepts up to 2M chars (250K prompt tokens) with no hard-limit error. Latency
47–92 tok/s.

## Test 5 — Teacher-similarity grid (the distillation lean) — INCONCLUSIVE by design
20 constrained/idiosyncratic prompts × panel, with constraint-satisfaction checkers, z-scored structural features,
and (intended) OpenAI-embedding cosine. `results/similarity_v2.latest.json`. Guard: only call a "lean" if ONE
teacher is an outlier on **both** embedding-cosine **and** constraint-agreement.

- **Embedding cosine axis BLOCKED**: the OpenAI embeddings key is **out of credits (`429 insufficient_quota`)**,
  so `text-embedding-3-small` returned nothing. Pending a credit top-up. (v1's char-4gram proxy gave a
  non-result 0.389–0.414 "pancake" — discarded.)
- Constraint-agreement with LUA: claude-4.5 1.0, deepseek 1.0, qwen 0.92, gemini 0.92, gpt-4o 0.85, llama 0.85.
- Feature z-distance to LUA (lower=closer): deepseek 3.41, gemini 3.52, qwen 3.90, gpt-4o 4.28, llama 4.84,
  claude 5.12.
- These two axes **contradict** (claude closest on agreement, *farthest* on features), and gpt-5 came back dead
  over OpenRouter. → **no teacher is an outlier on both → no lean fires.** Consistent with LUA's own training
  mix, but this is weak-to-null evidence either way (as expected for a black-box distill test).

---

## Candidate universe (why the finetune branch has almost no valid base)
Researched which models actually use `o200k_base` (the only ones eligible as a Branch-A base):

| candidate | tokenizer | Branch-A eligible? |
|---|---|---|
| OpenAI GPT-4o / 4o-mini / 4.1 / GPT-5 / o-series | o200k_base | **No** — closed weights (can't finetune; distill-teacher only, Branch B) |
| gpt-oss-20b / 120b | o200k_**harmony** | **No** — Harmony native vocab, LUA is plain o200k_base (Test 3) |
| Microsoft Phi-4 | **cl100k** (100,352) | No |
| Databricks DBRX | **cl100k** (GPT-4 vocab) | No |
| Llama 3/4 | own ~128k/202k tiktoken-style | No (distance 68–77) |
| Qwen3 / Gemma3 / Mistral / DeepSeek | own vocabs | No (distance 193–330) |
| Sabiá (Maritaca, BR) | Llama lineage | No (Llama tokenizer) |
| Tucano (BR) | PT-native ~32k | No (fertility PT/EN 0.69 vs LUA 1.31) |

→ **The finetune-of-a-known-open-model story has essentially no surviving candidate.** The only open o200k
weights are gpt-oss (harmony, excluded by Test 3). This is itself a finding: if LUA is derived, it is far more
likely **Branch B (distilled on an OpenAI o200k teacher)** than a weight-level finetune of any public model.

## Fertility / marketing note (separate from lineage)
LUA PT/EN token ratio = **1.31 ≈ o200k_base's 1.30**; Tucano/BERTimbau (PT-native) = 0.69–0.71. LUA's vocab is
**English-optimized o200k, not a Portuguese-native tokenizer** — inconsistent with a "sovereign PT-first model"
marketing framing, though this speaks to tokenizer choice, not model lineage.

---

## VERDICT (confidence-weighted, black-box)
| hypothesis | verdict | confidence |
|---|---|---|
| Qwen / DeepSeek / Llama / Mistral **rebadge (kept vocab)** | **RULED OUT** | HIGH (tokenizer, distance 68–330) |
| Same family after **tokenizer swap + full retrain** | very unlikely | med-high (would be a new model anyway) |
| **gpt-oss finetune / continuation** | **argued against** | med-high (o200k_base, NOT o200k_harmony) |
| **Finetune of any *public* o200k model** | **no eligible candidate exists** | med-high (candidate universe) |
| **Thin GPT/Claude/open-model API proxy** | **argued against** | medium (custom headers, OpenAI-shaped param set, distinct profile) |
| **Distilled on an OpenAI o200k teacher (GPT-4o family)** | **most parsimonious "derived" story; not confirmable** | — (untestable black-box) |
| **Distilled specifically on Claude / other single teacher** | no distinctive single-teacher signature | low-medium |
| **New model on the public o200k vocab, own weights** | **CONSISTENT with all evidence** | medium |
| **Trained fully from scratch** vs **distilled-on-frontier** | **not separable black-box** | — |

**Bottom line.** With **high confidence LUA is NOT a rebadged/finetuned Chinese or Llama/Mistral model** and
**NOT a thin proxy**. It is **o200k-native** (Test 1/2) but **not gpt-oss/Harmony** (Test 3), and its control
surface is **OpenAI-shaped** (Test 4). The candidate universe shows the **finetune branch has no valid public
base** — so *if* derived, it is almost certainly a **Branch-B distillation on an OpenAI o200k teacher**, which is
**behaviorally convergent with "from scratch on o200k" and cannot be separated black-box** (Grok's point, upheld).
The improved glitch test **retracted** the v1 "own embeddings" lean — it proves o200k *membership*, not
independent weights. All evidence is **consistent with an independent model on the public o200k tokenizer**, but
black-box cannot certify "from scratch" vs "distilled on frontier outputs."

## To move from "independent, unproven-from-scratch" to certainty (needs vendor cooperation OR credits)
- **Add OpenAI embedding credits** → finish Test 5's cosine axis (the one remaining black-box lever, still weak).
- **Weight fingerprinting** (Zeng et al., NeurIPS 2024) — needs the weights; out of scope for an API.
- **Vendor artifacts**: tokenizer file + special-token map (must match the o200k measurements), training recipe
  (tokens/compute, random vs continued-from-X init), loss curves, a held-out benchmark you run, whether Genesys
  PI is one model or a router. API games cannot certify "from scratch."

_Raw outputs: `results/tokenizer_v2.latest.json`, `results/glitch_panel.latest.json`, `results/gateway.latest.json`,
`results/similarity_v2.latest.json` (+ v1: `tokenizer_forensics`, `behavioral_probes`, `similarity_grid`).
Companion narrative: `../docs/success_report.v4.lua_forensics.md`._
