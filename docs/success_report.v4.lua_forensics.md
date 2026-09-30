# LUA Vision Genesys PI — provenance forensics (black-box, 2026-09-30)

Question: are the LUA Genesys PI models **new models trained from scratch**, or a **derivative of an existing
model** (a Chinese base like Qwen/DeepSeek, a Llama/Mistral finetune, or a distillation/proxy of Claude/GPT)?

Method is black-box only (OpenAI-compatible API, free eval key). No weights. Findings are confidence-weighted.

## 1. Tokenizer fingerprint — the decisive test
Each model family ships a distinct tokenizer (vocab + merges). A finetune / continued-pretrain / LoRA of a base
model **keeps that base's tokenizer** (you cannot swap it without full retraining). So the tokenizer is a
near-immutable fingerprint of lineage.

Measured LUA's token count for discriminating strings via the **delta method** (prompt_tokens of `anchor+S`
minus `anchor`, cancelling LUA's ~915-token injected system prompt), and compared to reference tokenizers
computed locally (tiktoken o200k/cl100k; HF Qwen2.5, Qwen3, DeepSeek-V2, Llama3, Mistral).

| test string | o200k | cl100k | Qwen2.5/3 | DeepSeek | Llama3 | Mistral | **LUA** |
|---|--:|--:|--:|--:|--:|--:|--:|
| Chinese | 38 | 78 | 28 | 28 | 44 | 75 | **38** |
| Portuguese (accented) | 65 | 79 | 77 | 104 | 79 | 88 | **64** |
| English | 41 | 41 | 41 | 42 | 41 | 48 | **40** |
| code | 72 | 72 | 72 | 94 | 72 | 102 | **71** |
| digit runs | 77 | 77 | 134 | 136 | 77 | 139 | **77** |
| emoji | 109 | 163 | 71 | 163 | 163 | 157 | **108** |

Distance to LUA (Σ|ref−LUA| over the natural-language/code/digit rows): **o200k = 3**, Llama3 = 23,
cl100k = 57, Qwen = 82, DeepSeek = 134, Mistral = 162.

Killer discriminators: **Chinese 38** (Qwen/DeepSeek pack it into 28), **digit runs 77** (Qwen/DeepSeek/Mistral
split into 134–139), **emoji 108** (matches only o200k's 109; every other family is 157–163 or 71).

→ **LUA's tokenizer is OpenAI's `o200k_base`, with very high confidence.** Text handling of `<|endoftext|>`
(6 tokens as text) and `<|end|>` (4) also matches o200k; the server special-cases raw `<|im_start|>`
(chatml defense), consistent with an o200k/chatml stack.

## 2. Not a thin GPT/Claude API proxy
LUA's API **rejects `temperature`, `top_p`, `n`, `presence_penalty`, and `logprobs`** (all `unsupported_parameter`).
OpenAI's own API supports every one of these. A passthrough proxy would forward them. Combined with:
- a **distinct capability profile** on our v4 benchmark (Genesys PI 82–95.5 with its own detection curve and
  failure modes — e.g. enterprise's RubyLLM-recon grep loop — not matching any GPT-5.6/GPT-6 run, which score
  91–100), and
- guarded identity (see §3),

→ it behaves like its own model, **not** a transparent GPT/Claude relay. (Medium-high confidence.)

## 3. Identity & metadata (weak, but consistent)
- Self-ID: consistently "LUA, a Genesys PI model by LUA Vision; architecture proprietary" — in EN and PT-BR,
  and it **resists a system-prompt override** (their persona is server-baked). No leakage to Claude/GPT/Qwen
  identity (lazy distillations often leak; this doesn't — mildly exculpatory, not proof).
- Knowledge cutoff (self-reported): **September 2025** — a specific, recent date consistent with a 2026 model.
- Strong PT-BR fluency with efficient accented-text tokenization (Portuguese 64 tokens ≈ o200k, better than
  Qwen/DeepSeek) — consistent with a Brazilian-focused model on the o200k vocab.

## Verdict (confidence-weighted)
| hypothesis | verdict | confidence |
|---|---|---|
| Derivative/finetune of **Qwen / DeepSeek** (Chinese base) | **RULED OUT** | high — tokenizer is o200k, not theirs |
| Derivative of **Llama / Mistral** | **RULED OUT** | high — tokenizer mismatch |
| Thin **GPT/Claude API proxy** | **argued against** | medium-high — rejects OpenAI params; distinct behavior |
| **New model trained from scratch**, adopting the open o200k tokenizer | **CONSISTENT with all evidence** | medium |
| Trained-from-scratch **vs distilled on frontier (GPT/Claude) outputs** | **cannot separate black-box** | — |

**Bottom line:** with high confidence, Genesys PI is **not a rebadged Chinese model (Qwen/DeepSeek) or a
Llama/Mistral finetune** — its tokenizer is OpenAI's o200k, which those lineages don't use and can't acquire via
finetuning. It is also not a transparent GPT/Claude proxy. The evidence is **consistent with a genuinely new
model** that adopted the (public) o200k tokenizer, though a black-box test cannot distinguish "trained from
scratch" from "a new model distilled on frontier outputs" — both yield an independent model with its own weights
and tokenizer.

## Limitations
Black-box only. The o200k tokenizer is public (anyone can adopt it), so it proves *non-derivation from other
tokenizer families*, not positively "OpenAI." Logprobs are unavailable (blocks distribution fingerprinting).
Single vendor endpoint; identity is server-masked. A stronger test would need weight access or logprob/top-token
distribution comparison against reference models on identical prompts.
