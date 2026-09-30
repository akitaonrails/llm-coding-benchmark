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
It **accepts** `seed` / `stop` / `response_format` (`200`) and — notably — the **reasoning-model knob
`reasoning_effort`**. `results/gateway.latest.json`. → The control surface is **OpenAI-shaped**; it rejects exactly
the params a vLLM/SGLang server fronting Qwen/Llama/DeepSeek would accept. Argues against a Chinese-open-model
backend behind a proxy, and (with the distinct v4 capability profile, Genesys PI 82–95.5) against a *thin*
GPT/Claude passthrough.
**But `reasoning_effort` is not a generic compat field like `seed`** — it's a reasoning knob, and paired with the
silent 250K-token context the gateway reads like someone **cloned a recent OpenAI surface**. That is equally
compatible with (a) a **thick** wrapper in front of a reasoning API (a thin proxy is excluded; a thick one is not),
or (b) a local stack that copied OpenAI's flags because its client SDK did. Treat it as **"API cosplay or a
reasoning backend," not proof of either.** Context: enterprise silently accepts up to 2M chars (250K prompt tokens)
with no hard-limit error. Latency 47–92 tok/s.

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
| gpt-oss-20b / 120b (stock Harmony serving) | o200k_**harmony** | **No** — Harmony native vocab, LUA is plain o200k_base (Test 3) |
| **gpt-oss weights with Harmony stripped at serve time** | o200k_base (Harmony rows just unused) | **⚠ SURVIVES** — the one awkward Branch-A candidate (see below) |
| Microsoft Phi-4 | **cl100k** (100,352) | No |
| Databricks DBRX | **cl100k** (GPT-4 vocab) | No |
| Llama 3/4 | own ~128k/202k tiktoken-style | No (distance 68–77) |
| Qwen3 / Gemma3 / Mistral / DeepSeek | own vocabs | No (distance 193–330) |
| Sabiá (Maritaca, BR) | Llama lineage | No (Llama tokenizer) |
| Tucano (BR) | PT-native ~32k | No (fertility PT/EN 0.69 vs LUA 1.31) |

→ **The finetune-of-a-known-open-model story has one awkward survivor, not zero.** The only widely-available open
o200k weights are **gpt-oss**, and Harmony vs base is mostly *extra special-token rows + a chat template* — the BPE
for ordinary text is the same family (our own harmony-as-text distance = 2). You can take an oss checkpoint, **never
emit** `<|channel|>`, and serve it behind ChatML or a custom "Lua" template. Test 3 **kills "this is a stock
Harmony gpt-oss endpoint"**; it does **not** kill **"oss (or a community oss finetune) checkpoint, base tokenizer,
Lua template."** So the honest confidence split is: **med-high against *vanilla oss serving*, NOT med-high against
every oss-derived weight.**
Beyond that survivor, no other *public* o200k base exists. **This narrows Branch A to essentially {stripped-Harmony
oss}** — it does not by itself promote Branch B. "If derived, then a distill on an OpenAI o200k teacher" is a
**reasonable prior, not a test result** (see verdict).

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
| **Stock gpt-oss (Harmony) serving** | **argued against** | med-high (o200k_base, NOT o200k_harmony) |
| **gpt-oss weights with Harmony stripped / Lua template** | **cannot exclude** — Branch A's one survivor | — (Test 3 only kills stock Harmony serving) |
| **Finetune of any *other* public o200k model** | **no eligible base exists** | med-high (candidate universe) |
| **Thin GPT/Claude/open-model API proxy** | **argued against** | medium (custom headers, OpenAI-shaped param set, distinct profile) |
| **Thick wrapper over a reasoning API / OpenAI-surface cosplay** | **not excluded** | — (`reasoning_effort` + 250K ctx) |
| **Distilled on an OpenAI o200k teacher (GPT-4o family)** | **reasonable prior, NOT a finding** | — (untestable black-box) |
| **Distilled specifically on Claude / other single teacher** | no distinctive single-teacher signature | low-medium |
| **New model on the public o200k vocab, own weights** | **CONSISTENT with all evidence** | medium |
| **Trained fully from scratch** vs **distilled-on-frontier** | **not separable black-box** | — |

**Bottom line.** What the tests *positively established*: LUA is **o200k-native** (Test 1/2), **not stock
gpt-oss/Harmony serving** (Test 3), **not a Qwen/Llama/Mistral/DeepSeek vocab rebadge** (Test 1), **not a thin
GPT/Claude/OpenRouter pipe** (Test 3/4), and its research-page **"PT-native / sovereign vocab" claim is falsified**
(fertility 1.31 = o200k, not a PT tokenizer). What remains **open**: (a) a **stripped-Harmony gpt-oss** checkpoint
served under a Lua template (Branch A's one survivor); (b) a **thick wrapper / OpenAI-surface cosplay over a
reasoning backend**; (c) **from-scratch on o200k** vs **distilled on a frontier o200k teacher** — genuinely not
separable black-box. The improved glitch test **retracted** the v1 "own embeddings" inference — it proves o200k
*family membership*, not independent weights. "If derived, then a distill on GPT-4o-family" is a **reasonable prior,
not a test result**: from-scratch-on-o200k-because-the-tokenizer-is-free fits the *same* observations.
**Net for a memo:** enough to **stop underwriting "we built a different brain-inspired stack / sovereign vocab"**
(the API contradicts that on tokenizer, glitch mask, controls, and PT fertility). **Not** enough to call it a scam
or a Qwen sticker — a competent small lab can train or distill a student on the public o200k vocab, and adopting it
is the cheap, professional choice. The problem is the *research-page claim*, not the existence of the model.

## To move from "independent, unproven-from-scratch" to certainty (needs vendor cooperation, not more black-box)
- **Test 5 is a closed null — do NOT spend embedding credits on it.** Constraint-agreement and feature-distance
  already contradict; a 20-prompt cosine grid cannot separate "own mix" from "soup of teacher traces." Leave it.
- **Weight fingerprinting** (Zeng et al., NeurIPS 2024) — needs the weights; out of scope for an API.
- **Vendor artifacts** (the only thing that would settle it): tokenizer file + special-token map (must match the
  o200k measurements), training recipe (tokens/compute, random vs continued-from-oss init), loss curves, a held-out
  benchmark you run, whether Genesys PI is one model or a router. API games cannot certify "from scratch."

_Raw outputs: `results/tokenizer_v2.latest.json`, `results/glitch_panel.latest.json`, `results/gateway.latest.json`,
`results/similarity_v2.latest.json` (+ v1: `tokenizer_forensics`, `behavioral_probes`, `similarity_grid`).
Companion narrative: `../docs/success_report.v4.lua_forensics.md`._
