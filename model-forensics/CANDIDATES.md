# Additional o200k-compatible model candidates

Research date: 2026-10-09. This is a candidate-discovery exercise, not an ancestry finding. No model inference or paid API comparison was run. Only public metadata and tokenizer JSON files were downloaded; no remote model code was executed.

## Direct local checks

Downloaded tokenizer.json at the exact Hugging Face commit in each result. Encoded the 768 existing held-out strings with Hugging Face tokenizers, with add_special_tokens=False, and compared token counts to tiktoken o200k_base. This tests plain-text count compatibility on this panel, not full tokenizer equivalence, chat templates, special tokens, model behavior or ancestry. Genesys previously matched those same 768 counts after removing its constant reported offset.

| Checkpoint | Matches /768 | Published tokenizer vocab size | Declared license |
|---|---:|---:|---|
| [microsoft/Phi-4-mini-flash-reasoning](https://huggingface.co/microsoft/Phi-4-mini-flash-reasoning) | 768 | 200029 | mit |
| [microsoft/Phi-4-multimodal-instruct](https://huggingface.co/microsoft/Phi-4-multimodal-instruct) | 768 | 200029 | mit |
| [microsoft/phi-4](https://huggingface.co/microsoft/phi-4) | 309 | 100352 | mit |
| [microsoft/Phi-4-mini-instruct](https://huggingface.co/microsoft/Phi-4-mini-instruct) | 768 | 200029 | mit |
| [microsoft/Phi-4-mini-reasoning](https://huggingface.co/microsoft/Phi-4-mini-reasoning) | 768 | 200029 | mit |
| [microsoft/Phi-4-reasoning-plus](https://huggingface.co/microsoft/Phi-4-reasoning-plus) | 309 | 100352 | mit |
| [Motif-Technologies/Motif-2.6B](https://huggingface.co/Motif-Technologies/Motif-2.6B) | 694 | 219520 | apache-2.0 |
| [LLMWildling/gpt-oss-160b-kiwi](https://huggingface.co/LLMWildling/gpt-oss-160b-kiwi) | 768 | 200019 | other |
| [yasserrmd/gpt-oss-coder-20b](https://huggingface.co/yasserrmd/gpt-oss-coder-20b) | 768 | 200019 | apache-2.0 |

## Interpretation and testing priority

1. **Phi-4-mini-instruct and Phi-4-mini-reasoning:** the most useful new independent-family controls. Both match all 768 counts. Microsoft publishes weights under MIT and documents local inference; the mini cards also describe Azure deployment. This is a reason to include them in candidate coverage, not a probability ranking for Genesys origin. Their approximately 3.8B scale does not by itself establish whether an adapted system could match Genesys.
2. **Phi-4-mini-flash-reasoning and Phi-4-multimodal-instruct:** additional Microsoft checkpoints with the same count match. Flash uses the SambaY hybrid architecture and its card links local inference, Azure and NVIDIA NIM. Multimodal provides another implementation of the tokenization family. Start with representative mini variants rather than spending on every related checkpoint. Serving documentation is not a verified live endpoint or a local inference compatibility test.
3. **LLMWildling/gpt-oss-160b-kiwi:** the publisher describes an agentic coder derived from gpt-oss-120B and documents vLLM serving with reasoning/tool-call parsers. Its tokenizer matches all 768 counts. This is a concrete public example of the kind of OSS adaptation we hypothesized; the publisher’s architecture/training/performance claims have not been independently audited. Hugging Face metadata declares license `other`; inspect the actual terms before reuse. Repository creation date in metadata is 2026-05-01, before our September tests, but creation date is not proof of when these particular weights became available.
4. **yasserrmd/gpt-oss-coder-20b:** community coding fine-tune whose card identifies an Unsloth GPT-OSS-20B base and claims training on a coding dataset. All 768 counts match. It is another possible adaptation control, with local weight availability; its training quality and claimed capabilities are unverified. Testing stock OSS does not substitute for testing this checkpoint.
5. **Motif-Technologies/Motif-2.6B:** an independent architecture/pretraining project with Apache-2.0 weights. Its report explicitly starts from o200k_base and adds roughly 19,000 Korean tokens, yielding a 219,520-token vocabulary. Local check matches 694/768, so it is o200k-derived but not an exact count match. Lower priority for an unchanged-tokenizer hypothesis; differences do not exclude a modified model or separate API accounting layer. The card documents local Transformers inference with custom code; custom code was not run. [Tokenizer description in the primary paper](https://arxiv.org/html/2508.09148v1#S2.SS2).

## Important exclusions and availability

**Phi-4 14B and Phi-4-reasoning-plus 14B are not interchangeable with Phi-4-mini.** Their 100,352-entry tokenizer files match only 309/768 counts. Do not choose the larger Phi checkpoint as an o200k-matching control simply because the family name is similar.
The current public OpenRouter catalog check found only `microsoft/phi-4` among these nine exact candidate families/names. It is the nonmatching 14B model. No inference request was sent. Microsoft cards document other hosted paths for mini variants, but account access and current endpoint operation are unverified. Local/self-hosted inference is the reproducible fallback. Neither Kiwi nor the coder fine-tune was found by that catalog filter; absence there does not establish absence from all hosts.
Tokenizer libraries, tokenizer-only Hugging Face repositories, models merely using the o200k regex, and models evaluated with o200k token counting are not automatically o200k-native language models. Search results of those kinds were not promoted to candidates.

## What changed in our hypotheses

The earlier GPT-4o-versus-gpt-oss framing was too narrow. There are at least four Microsoft checkpoints and two community OSS derivatives that meet our existing plain-text token-count pattern and were not in the forensic reference panels. This is not an exhaustive census, and shared-tokenizer checkpoints are not six independent ancestry signals.
The best next independent-family comparison is Phi-4-mini-instruct plus its reasoning variant. A known adapted OSS coder could serve as a useful positive control for how much post-training changes output fingerprints. Any new behavioral protocol must first show discrimination on controls; the completed OSS assay failed that gate and should not simply be rerun with more volume. No new behavioral run has been launched.
API token accounting may be separate from the inference tokenizer. If Genesys reports o200k-normalized usage, even a non-o200k backend remains possible. Also, replacing a tokenizer can be done with embedding adaptation and continued training; it is not categorically necessary to pretrain the whole model from scratch. We have no evidence that Genesys does either.

## Saved evidence

The local, git-ignored directory `runs/candidate-tokenizers-20261009/` contains the check script, downloaded tokenizer JSONs, per-model results and the OpenRouter catalog subset. Compact exact revisions and results are also saved alongside this document as [candidate-tokenizers-20261009.json](candidate-tokenizers-20261009.json). Full model cards and weights are not mirrored. Counts are our measurements; lineage and deployment descriptions are publisher claims linked above.


## OpenRouter live availability test

On 2026-10-09, refreshed the public model catalog and sent one bounded chat-completion compatibility request for each of the seven candidate model IDs below. None returned a model response. These are availability checks, not behavioral failures. No alternative model was substituted. The noncatalog IDs were candidate routing names based on publisher/repository names; their rejection alone does not prove absence under every possible alias. The catalog also contained no matching aliases.

| Requested ID | HTTP | Result |
|---|---:|---|
| `microsoft/phi-4-mini-instruct` | 404 | No endpoints found for microsoft/phi-4-mini-instruct. |
| `microsoft/phi-4-mini-reasoning` | 400 | microsoft/phi-4-mini-reasoning is not a valid model ID |
| `microsoft/phi-4-mini-flash-reasoning` | 400 | microsoft/phi-4-mini-flash-reasoning is not a valid model ID |
| `microsoft/phi-4-multimodal-instruct` | 404 | No endpoints found for microsoft/phi-4-multimodal-instruct. |
| `llmwildling/gpt-oss-160b-kiwi` | 400 | llmwildling/gpt-oss-160b-kiwi is not a valid model ID |
| `yasserrmd/gpt-oss-coder-20b` | 400 | yasserrmd/gpt-oss-coder-20b is not a valid model ID |
| `motif-technologies/motif-2.6b` | 400 | motif-technologies/motif-2.6b is not a valid model ID |

The available catalog includes `microsoft/phi-4`, stock gpt-oss-20B/120B and safeguard-20B, but none is a substitute for these exact candidates. Testing the shortlist requires another provider or local/self-hosted inference. Raw redacted responses and the catalog subset are retained under `runs/openrouter-candidate-check-20261009/`.


Local feasibility follow-up: [RTX 5090 assessment and deferred Phi execution plan](PHI_LOCAL_PLAN.md). A newer official 15B vision checkpoint was found; 14B Reasoning Plus Q8_0 is the recommended text-only test. No GPU inference or weight download has started.
