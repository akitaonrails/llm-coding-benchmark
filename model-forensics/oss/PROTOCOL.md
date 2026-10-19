# gpt-oss reference-gated output experiment

Frozen before collecting new reference answers. No GPT-4o collection. No use of prior Genesys answers to select signatures.

## Question

Does Genesys reproduce a distinctive, independently validated gpt-oss-120B output signature, robust across two hosting providers, an alternate system instruction and a draft/check wrapper? How does the 20B sibling behave on the same signatures?

## Evidence

48 fresh prompts: 12 rare Unicode copying tasks selected deterministically from the shared vocabulary, four common copying controls, 12 algorithmic exact-answer tasks and 20 underdetermined choices (ten choice blocks in two orders). Copying measures actual generated characters/errors, not token counts; vocabulary sharing alone earns no evidence. Correct answers shared by all models are uninformative. Choices measure output preferences, not accuracy or internal reasoning. Explicit visible answers and API usage are retained; private reasoning is not requested or treated as provenance.

Reference profiles: gpt-oss-120B through Groq, the same named weights through DeepInfra BF16, alternate system instruction through Groq, two-call verification through Groq; gpt-oss-20B through DeepInfra BF16; GLM 5.3 and Kimi K3 through Relace as negative controls. Hosted model/provider names are provider claims, not independent weight attestations. Pin exact provider routes for OSS with fallback disabled. Reference reasoning effort low; omit temperature everywhere. Genesys uses its fixed default sampling. Differences may reflect this configuration as well as weights.

## Locked decision rules

1. Discovery: two repetitions per prompt and seven references. Exclude missing/truncated/invalid observations from answer distributions, never score them as wrong answers. Require both repetitions usable for each required profile. Select probes with worst positive-control total-variation distance <=0.25 and minimum negative-control distance minus positive distance >=0.5. Exclude common copying controls. At most 16 blocks, one variant per block, sorted by margin then ID. Require eight independent blocks; otherwise stop without a Genesys batch.
2. Validation: six NEW responses per selected prompt and reference profile. These are new observations on the selected prompts, not a claim of generalization to unseen prompts. Require >=4 usable responses per profile/probe, >=90% prompt coverage and at least eight blocks. Compute 2,000 deterministic block bootstrap mean-distance intervals. All positive upper bounds must fall below all negative lower bounds. The midpoint is the locked decision threshold. Otherwise stop without a Genesys batch. The 20B sibling is exploratory and does not determine this 120B gate.
3. Target: eight Genesys responses per selected prompt, only after validation passes. Require >=90% coverage and >=4 usable responses per included block. If its entire distance interval is below/above the threshold, report inside/outside the tested behavioral envelope; otherwise report inconclusive. Report exact shared wrong-answer probability per task alongside distances.

Normalization strips whitespace, a single enclosing Markdown JSON fence and JSON string encoding. It does not repair answers, translate text or remove explanatory prose. Choice responses must equal one allowed item. Invalid formats remain excluded with coverage explicitly reported.

Maximum 1,664 physical API calls: discovery 768, validation <=768, target <=128. Each verification observation uses up to two calls. Budget 4,096 output tokens and 120 seconds per call; reasoning may consume output budget. No failed observation replay, no automatic provider fallback. Three consecutive infrastructure failures open an endpoint/model circuit. Started but unrecorded calls become interrupted_unknown upon resume. Every schedule, observation and completion is sealed; sources and manifest hashes are frozen. Credentials remain environment-only.

## Interpretation limits

This can distinguish an unmodified/lightly wrapped 120B behavior envelope if the references validate a signature. It cannot universally exclude arbitrarily extensive fine-tuning, distillation or untested base models. No ancestry probability is derived from a bootstrap interval. A failed reference gate means no adequate signature found, not evidence against gpt-oss. No classification is made from tokenizer choice, provider metadata, model self-identification, speed alone, or shared correctness.

Routing reference: https://openrouter.ai/docs/guides/routing/provider-selection
