# GPT-4o relationship experiment v2.0

Question: does Genesys House share a distinctive behavioral fingerprint with the specified GPT-4o endpoints under the tested wrappers? Separate this from tokenization, live remote dependence, legal ownership, and arbitrary hidden orchestration.

Frozen before collection: code, generated probes/answers, model IDs, system prompts, wrapper algorithms, sampling policy, schedules, analysis and decision rules. All artifacts stay in `model-forensics/runs/`. Prior benchmark and pilot answers are not used to select these probes. Genesys behavioral requests start only after reference-only discovery, selection, and calibration artifacts have been sealed. Token counts are a separate channel and never enter the behavioral selection algorithm.

## Endpoints and budget

Direct OpenAI GPT-4o preflight returned HTTP 429, so the planned references use OpenRouter with named snapshots. Primary: `openai/gpt-4o-2024-08-06`; additional positive control: `openai/gpt-4o-2024-11-20`. Independently named alternatives: Qwen3 Max and Llama 3.3 70B. These are provider-declared identities, not audited weights. Genesys uses its direct House API. System prompts and inference defaults are explicit in the manifest; temperature is omitted everywhere because Genesys rejects it. No provider fallback is introduced by this client; upstream routing remains unverified.

Tokens: 1,024 generated strings × Genesys/GPT-4o = 2,048 one-output-token requests. Reference discovery: 48 short-answer tasks × 3 endpoints × 3 repeats = 432 calls. Holdout: up to 64 probes × 6 replicates × 9 profiles = 3,456 observations; two profiles use two calls, adding up to 768 calls. Temporal sentinels: 8 probes × 3 replicates × 4 profiles = 96 observations, plus 24 verification calls. Maximum 6,824 physical calls; actual counts are printed by the plan/selection. Requested output limit is 512 tokens for behavior and 1 for tokenizer probes. In preflight Genesys reported 129 completion tokens (113 reasoning) despite max_tokens=1. The request parameter therefore is not an enforceable billed-token ceiling; deviations are recorded and provider usage is treated as reported rather than independently verified. No inferred dollar estimate or retry budget is hidden.

Collection concurrency: up to 8 observations, up to 2 active observations per underlying endpoint/model, at least 0.5 seconds between call starts per underlying endpoint/model. A 429 adds a 60-second cooldown before a subsequent observation, never a retry. Every attempted physical call is journaled. Transport/schema errors remain missing; three successive infrastructure failures per endpoint trip a circuit breaker, recording later scheduled observations as `circuit_open` rather than silently discarding them. An interrupted in-flight observation becomes `interrupted_unknown`, never automatically replayed. Completion and failure counts are reported separately.

## Probes and reference-only selection

1. Token counts: eight generated string families, 128 unique instances each. One quarter of each family estimates a constant offset versus local `o200k_base` and `cl100k_base`; the remaining three quarters test that frozen offset. Report match fractions and per-family mismatches; counts alone do not identify model weights. Pin tiktoken version and hash its encoding tables in the manifest.
2. Discovery: 12 deterministic algorithmic task families × 4 instances, all with executable reference answers. These are string, numeric, state and parsing operations, not trivia or benchmark memorization. Three repeats per reference. Rank families by repeatable GPT-4o wrong answers that are uncommon in the two alternatives. A family qualifies only with at least one wrong answer observed at least twice for GPT-4o and with estimated alternative frequency <=1/3 for that same answer. Choose at most 8 families. Do not fill missing error candidates with post-hoc invented fingerprints. If none qualify, report the rare-error channel unavailable.
3. Error holdout: 2 fresh instances from each selected family; generated and frozen before discovery, chosen by the fixed family-selection rule. Similarity on these new instances is measured against contemporaneous GPT-4o, not assumed from discovery errors.
4. Perturbations: 12 categorical-choice contexts × 4 changes (original, reversed choices, paraphrase, irrelevant context). Choices are stable textual items, avoiding answer-letter confounds. Each context is a bootstrap block. Exact response formatting is required; invalid/truncated responses are missing, counted explicitly.
5. Wrappers: primary GPT-4o baseline A and independent repeat stream B, a different system prompt, a two-call draft/check wrapper, and the alternate GPT-4o snapshot. Negative controls: Qwen plain, Qwen with the same draft/check wrapper, Llama plain. Genesys is evaluated separately after calibration. There are 8 reference profiles plus Genesys; the live manifest prints the precise resulting budget.

## Analysis frozen before target evaluation

Use total-variation distance on categorical distributions, separately from wrong-answer agreement. Compare candidate distributions with GPT-4o baseline A. Equal-weight context/family blocks; 2,000 deterministic block bootstrap resamples. Report nominal 95% descriptive intervals, not posterior probabilities of identity. Probe-level counts and distances are saved. Missingness: require >=4/6 valid samples for each candidate and baseline on at least 90% of holdout probes; otherwise classification is unavailable.

Calibration: compute the greatest upper interval bound among known GPT-4o controls (repeat, alternate system, verify, alternate snapshot) and the smallest lower bound among Qwen/plain, Qwen/verify and Llama. Only if the former is strictly below the latter is there a separation threshold (midpoint). Otherwise, the attribution gate FAILS: retain descriptive results but emit no positive/exclusion classification. No threshold tuning after inspecting Genesys.

Target: if calibration passed and coverage is adequate, a target interval entirely below the frozen threshold is consistent with the tested GPT-4o controls; entirely above contradicts that tested control envelope. Overlap is inconclusive. None of these classifications establishes live passthrough, excludes untested wrappers or snapshots, or rules out distillation. Tokenizer matches cannot override a failed behavioral calibration.

Perturbation response: additionally compare each context's change from its original distribution under each perturbation, using half-L1 distance between the response-change vectors. This exploratory channel has no separate tuned attribution threshold. Rare-error agreement reports matching incorrect outputs and error opportunities, with no identity probability.

Temporal replication: after target holdout, repeat preselected sentinels for Genesys, baseline GPT-4o, GPT-4o verify and Qwen. Record actual wall-clock separation; the runner waits until 10 minutes after the first target observation if needed. This is a short same-day stability test, not multi-day evidence. No model version/routing conclusion is inferred from latency alone.

## Verification evidence / owner

Implementing agent owns checks: deterministic/unique panel and correct algorithmic answers; selection cannot read target observations; synthetic identical and distinct distributions; failed-control gate; inadequate coverage; per-endpoint pacing/failure journal/resumption; wrapper second-call behavior; physical-call budgets; manifest/result tamper rejection. Local HTTP fixture and mocks avoid live calls during unit tests. Live preflight responses are retained separately. No old scored benchmarks, data or artifacts are modified.

## Boundaries

This kit does not rerun the Rails v4 benchmark or execute model-produced code. A successful two-call check is not evidence of long-horizon capability. Reproducing the old v4 gap with a full agent wrapper would be a separate capability experiment. Offline deployment and infrastructure attestation remain necessary stronger avenues for identifying remote dependence.
