# Genesys code-stylometry vs. the B300 open-weight models

_Added 2026-10-19. Resumes the [Genesys forensics](FINDINGS.md) from a new angle: with the
B300 open-weight batch complete, do any of the newly-tested top models **resemble Genesys** in
their generated code? This is a **code-stylometry** study on the shared v4 Rails task, not an
ancestry finding. It separates brief-forced convergence from idiosyncratic habit, and it inherits
the project rule that **behavioral/stylistic similarity is never promoted to an identity verdict**
([FINDINGS.md](FINDINGS.md))._

## Why code stylometry (and its hard limit)

The strong lineage channels from the prior forensics are **unavailable** for this comparison:
Genesys is API-only and **rejects `logprobs`**, and the B300 models are self-hosted — so there is
no common channel to compare tokenizer behavior, logprobs, or weights across the two. The only
thing both sides produced under identical conditions is **source code for the same v4 Rails brief**.

That is a weak substrate for lineage: a RubyLLM chat app under a fixed brief has only a handful of
reasonable shapes, so **all competent models converge** on the same gems, layout, and canonical
RubyLLM calls. Stylometry here can only ask a narrow question — *is any model idiosyncratically
closer to Genesys than the shared-brief baseline?* — and the honest answer below is **no**.

## Corpus

- **Genesys**: `v2_genesys_pi_enterprise`, `v2_genesys_pi_house`, and the `_0929` reruns (4 projects).
- **Top B300 open-weight**: GLM 5.3 Flash (92.5), Qwen3.8 Flash-Next (92.5), Swift 1.5 27B (88.0),
  ThinkingCap 3.8 27B (83.0).
- **Hypothesis anchor**: gpt-oss-120B (the prior leading "base" theory) — **no usable code**: it
  DNF'd at sprint 2 with no RubyLLM integration, so the gpt-oss-ancestry theory **cannot be
  corroborated or refuted from code**.

Extractors (deterministic, reproducible): `scratchpad stylo.py` (signatures) and `lexical.py`
(verbatim-phrase overlap). Generated code was read as untrusted data, never executed.

## 1. Quantitative signatures

| Model | rb files | rb lines | comment% | frozen% | single-quote% | test fw | RubyLLM idiom |
|---|---:|---:|---:|---:|---:|---|---|
| genesys enterprise | 61 | 1,689 | 17% | 1.6% | 2% | rspec | `chat.ask` (naive replay loop) |
| genesys house | 66 | 1,814 | 12% | 1.5% | 3% | minitest | `add_message` + `chat.complete` |
| genesys ent. 0929 | 65 | 2,134 | 12% | 1.5% | 4% | rspec | `chat.ask` |
| genesys house 0929 | 76 | 2,686 | 7% | 0% | 6% | minitest | `chat.ask` |
| GLM 5.3 Flash | 113 | 5,416 | 11% | 0.9% | 4% | minitest | job + namespaced services, 98 broadcasts |
| Qwen3.8 Flash-Next | 78 | 4,169 | 10% | **24%** | **78%** | rspec | `Struct` result, `chat.messages=` |
| Swift 1.5 27B | 74 | 3,338 | 19% | 7% | 5% | minitest | `.generate`, heavy RDoc |
| ThinkingCap 3.8 27B | 76 | 3,714 | 10% | 0% | 2% | minitest | `add_message` + `with_instructions` |

**Convergent (brief-forced / Rails-8-omakase defaults — weak evidence):** identical core Gemfile
(propshaft, importmap, turbo/stimulus, tailwind, ruby_llm, rack-cors, brakeman, bundler-audit),
standard `app/` layout, service objects, double-quote dominance, minitest as the common default,
`before_action`, two `I18n` touches. Every model does these; they carry no lineage signal.

**Idiosyncratic / habitual (the discriminating axes — they DIVERGE):**
- **Verbosity:** Genesys is the **tersest of the whole set** (1.7k–2.7k lines), with the *most
  naive* integration — `genesys_enterprise` literally loops `chat.ask(...)` over each stored message
  (a wrong, round-trip-per-message history replay). Every top OSS model is **1.5–3× larger** and
  **more defensive** (custom error classes, rescue chains, `Struct` results, namespaced
  `Conversations::Streamer`/`TitleGenerator`, Turbo broadcasting). Genesys writes the least, and the
  least careful, code of the group — the **opposite** of the elaborate top OSS apps.
- **`frozen_string_literal`:** Genesys **never** uses it (0–1.6%). Qwen3.8 Flash-Next uses it on
  **~24%** of files and Swift on 7% — a strong, consistent habit Genesys does not share.
- **Quote style:** Qwen3.8 Flash-Next is **single-quote-dominant (78%)** — the inverse of Genesys's
  double-quote habit (2–6%).
- **Test framework:** Genesys itself is inconsistent (enterprise=rspec, house=minitest), which
  already argues its "style" is not a fixed fingerprint.

## 2. Verbatim-phrase overlap (the strongest tell) — null

Distinctive comment/string phrases (≥4 words, boilerplate-filtered) shared between the Genesys
corpus and each model:

| Model | Jaccard with Genesys | What the shared phrases actually are |
|---|---:|---|
| GLM 5.3 Flash | 0.048 | `config/puma.rb`, `inflections.rb`, `schema.rb` columns, test assertions |
| Qwen3.8 Flash-Next | 0.055 | same Rails-generator boilerplate |
| Swift 1.5 27B | ~0.05 | same |
| ThinkingCap 3.8 27B | ~0.05 | same |

The overlap is **uniform (~0.05) and entirely framework-generated boilerplate** — the stock Puma
config comments, the inflections initializer, schema column definitions, standard test assertions.
**Zero model-authored phrases are shared distinctively with Genesys**, and **no model is lexically
closer to Genesys than any other.** This is the cleanest result in the study: a null.

## 3. Nearest neighbour — and why it means nothing

The closest stylistic neighbour is **ThinkingCap** (shares the `chat.add_message(role:, content:)`
+ `with_instructions` idiom, double quotes, minitest). But:
1. Those shared idioms are the **RubyLLM-README-canonical** forms, not idiosyncratic.
2. ThinkingCap is far more defensive/documented than terse Genesys.
3. ThinkingCap is a **Qwen3.8 fine-tune** — yet **base Qwen3.8 Flash-Next is the *least*
   Genesys-like model in the set** (single-quote, frozen-heavy, rspec, `Struct`-functional). A base
   model unlike Genesys while one of its fine-tunes is "nearest" is a textbook sign of **coincidental
   convergence, not lineage.**

## Conclusion

**No. None of the newly-tested open-weight models show an idiosyncratic code signature correlating
with Genesys.** Every resemblance is a convergent, brief-forced, Rails-omakase-default feature that
all competent models share; on the discriminating axes (verbosity, `frozen_string_literal`, quote
habit, integration correctness) the top OSS models **diverge** from Genesys, and the
verbatim-phrase overlap is a uniform boilerplate-only null. Genesys's one distinguishing trait —
extreme terseness with naive integration — is the opposite of the larger, more defensive top OSS
apps.

This neither supports nor excludes any ancestry hypothesis; it adds a **code-level null** on top of
the prior **inconclusive** API-level forensics. The gpt-oss "base" theory specifically **cannot be
tested from code** because gpt-oss produced no usable v4 app. The only way to move Genesys
provenance past "inconclusive" remains the strong channels (weights, tokenizer internals, logprobs)
that its API does not expose — stylometry over a shared benchmark brief cannot substitute for them.

_Reproduce: `python3 -I scratchpad/stylo.py <repo>` and `python3 -I scratchpad/lexical.py <repo>`._
