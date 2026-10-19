# Genesys forensic kit: protocol v1.1

## Question and scope
Identify observable similarities between the Genesys endpoint and a declared reference panel, and measure stability across independent sessions. This is not a capability ranking and cannot establish authorship, licensing, theft, geographical origin, absence of distillation, or absence of proxying.

The prior `lua-forensics` results are historical exploratory evidence. In particular, a tokenizer match identifies a component, not weight ancestry; distillation can use a different tokenizer. No old samples enter this experiment.

## Evidence path
1. Freeze endpoint/model identifiers, settings, code, probes and randomized schedule in a manifest before requests. Preserve manifests and responses for every session. No automatic retries or silent parameter fallback.
2. Collect fresh single-turn responses with one common system prompt, bounded output, explicitly recorded sampling policy, and interleaved model order. Keep HTTP/transport/schema failures distinct from empty, truncated and usable answers. No tools, retrieval, benchmark prompts, or benchmark files enter requests.
3. Use four channels: categorical preferences, objectively scored short-answer errors, exact Unicode copying, and relative prompt-token counts. Compare channels independently; do not invent an overall provenance score.
4. Reserve entire probe families for holdout, rather than putting near-identical variants on opposite sides. Holdout prompts are public and frozen: this is an analysis holdout, not a secret contamination-resistant evaluation. Do not tune on holdout results. A genuinely blind follow-up needs a new unpublished panel and independent custodian.
5. Report empirical total-variation distance for categorical distributions, exact answer agreement for determinate probes, shared wrong answers, coverage, and tokenizer delta differences. Bootstrap intervals resample probe families, not individual completions. These are descriptive uncertainty intervals, not calibrated identity probabilities or proof of independence.
6. Compare the same endpoint across separately collected session directories to establish its own variability. Use independently documented same-model deployments as positive controls, known derivatives as relationship controls, and independently trained models as negative controls. Derivative similarity is an empirical question, not a required outcome.
7. Before any attribution claim, check a fresh holdout session, provider version/routing metadata, missingness, truncation, prompt effects, and control performance. No universal identity threshold is built in; an unknown source stays unknown.

## Collection budget
Pilot: 2 replicates per probe (plumbing only). Full: 20 replicates per probe. The plan command prints exact request and requested maximum completion-token counts before collection. These are caps on submitted request parameters, not monetary or actual billed-token guarantees. Reasoning budgets and provider accounting can differ. Serial bounded-time requests avoid load testing. No paid calls are part of building or testing the kit.

Use the same profile, suite seed, common settings, exact model revisions and reference endpoints across sessions. Record UTC start/end times and operator session labels. Repeat full sessions at three separated times before investigating routing. Failure-rate changes or score variance alone are not routing evidence.

## Verification budget / owner
Owner: implementing agent; future operator reruns `python3 -m unittest discover -s model-forensics/tests -v`.
- Frozen experiment: deterministic generation, family-disjoint splits, input mutation rejection and manifest/schedule integrity checks.
- Collection: local HTTP fixture exercises success, 429, malformed/empty response, truncation, credential redaction and redirect refusal; no vendor calls required.
- Interrupted collection: append-only records, journaled request starts, exclusive lock, no duplicate replay of completed or uncertain requests.
- Analysis: synthetic identical and opposite distributions, incomplete coverage, tokenizer offset invariance, cross-session pairing and tamper rejection.
- Isolation: no benchmark imports/writes, no global settings or credential-file reads, output restricted to this kit's ignored runs directory.

## Stronger evidence requiring cooperation
An independently supervised offline deployment binds fresh behavior to a locally executing artifact. Weight inspection can test exact identity or ancestry against available candidates. A provenance review must connect that artifact to dated intermediate checkpoints, training code, experiment records, externally corroborated compute records, and documented base-model rights. None of these is replaced by API fingerprinting. See PROVENANCE.md.

## Research basis
- https://arxiv.org/abs/2407.01235 — black-box model fingerprints; research method, not universal forensic certainty.
- https://arxiv.org/abs/2607.10252 — distributions of short answers as behavioral signatures.
- https://arxiv.org/abs/2608.29930 — token-count matches identify tokenization stacks, not necessarily model lineage.
- https://cnut1648.github.io/Model-Fingerprint/ — publisher-inserted fingerprints need prior embedding and publisher cooperation.
- https://github.com/LUMIA-Group/AWM — weight-access comparison methods.
- https://github.com/OPTML-Group/LLM-Biometrics — weight-space lineage research.

## Compatibility amendment (2026-10-08)
Genesys House returned HTTP 400 unsupported_parameter for temperature, explicitly requiring omission because House uses fixed sampling. The original failed observation and a separate diagnostic are preserved in runs/genesys-compat-20261008. New runs use temperature:null, which omits that field for every endpoint. This is a declared change, not a runtime fallback. Different provider defaults are a material confound; conclusions concern endpoint behavior under these settings, not equal-temperature weight identity.
