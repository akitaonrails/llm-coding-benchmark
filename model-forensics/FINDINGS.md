# Genesys forensic findings and feasibility notes

Updated 2026-10-09. Observations, external facts and engineering estimates are separated below. The GPT-4o confirmatory run has completed; its control calibration did not support a formal attribution or exclusion. The gpt-oss reference-discovery run also finished without a validated signature. No forensic collection is currently scheduled. Start at the [kit README](README.md) for reproduction and the [confirmatory protocol](confirmatory/PROTOCOL.md) for the frozen statistical analysis.

## Current conclusions and confidence

As of 2026-10-09, the strongest finding concerns endpoint token accounting, not model ancestry. Genesys matched o200k_base on all 768 held-out strings after removing a constant offset. Confidence is high for that measured pattern; it does not identify the tokenizer implementation, model weights or backend.

Genesys differed substantially from the tested GPT-4o deployments on actual outputs: mean answer-distribution distance 0.6167 versus 0.2900 for a GPT-4o repeat, with tested GPT-4o wrappers/snapshot between 0.3456 and 0.4691. This is descriptive evidence against simple passthrough under the tested configurations. However, known positive and negative controls overlapped, so the formal classification remained inconclusive. Deprioritizing GPT-4o is reasonable; declaring every GPT-4o-derived implementation excluded is not.

The dedicated gpt-oss discovery resolved 672 observations and found one qualifying independent candidate block against a locked minimum of eight. It therefore stopped before validation or Genesys collection. It established no new Genesys–gpt-oss correlation. The 20B comparison was mostly unavailable because of provider rate limits. A gpt-oss derivative with additional agent training/orchestration is technically plausible but has no validated attribution evidence from this experiment.

No origin was conclusively ruled out, no base model was identified, and ownership/training provenance was not verified. Behavioral originality is not proof of independently trained weights. No defensible numerical probability of ancestry can be assigned from these tests. The evidence supports measured differences and capabilities much more strongly than an origin claim.

All forensic collection is finished or stopped. The incomplete process supplement retains 191 observations; it is not a completed attribution study. The v4.1 third Genesys run remains paused. The v5 benchmark is a design proposal only.

## Observed so far

The first pilot recorded 992 observations across eight endpoints. Genesys returned 124/124 usable responses. Its reported prompt-token deltas matched GPT-4o across six string families, with a constant +995-token difference across the 12 base/doubled prompts and both repetitions. This supports a shared tokenization/accounting pattern on that panel. It does not identify weights or prove forwarding to an OpenAI API.

No model origin was ruled out. Six reference endpoints differed from Genesys on at least one measured tokenizer delta; that only distinguishes those endpoint measurements. A common tokenizer, derivative model, altered chat template or accounting layer remains compatible with the evidence. The [pilot JSON](runs/report-a2d0e339f9e7-38bb86434d0e/analysis.json) and [pilot report](runs/report-a2d0e339f9e7-38bb86434d0e/report.md) are local ignored artifacts.

The confirmatory experiment separately measures tokenizer agreement, reference-selected rare errors, prompt perturbations, explicitly constructed GPT-4o wrappers, alternative model controls and temporal repetition. Its classification gate must distinguish known controls before classifying Genesys. A result inconsistent with tested controls cannot exclude every possible hidden wrapper, snapshot or model mixture.

## Verified API pricing: GPT-4o versus GPT-5.6 Sol

USD per million text tokens, standard processing, verified 2026-10-09:

| Model | Uncached input | Cached input | Output |
|---|---:|---:|---:|
| GPT-4o | $2.50 | $1.25 | $10.00 |
| GPT-5.6 Sol | $4.00 | $0.40 | $20.00 |

Sources: official [GPT-4o model page](https://developers.openai.com/api/docs/models/gpt-4o) and [GPT-5.6 Sol model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol).

At equal uncached input/output volumes, Sol costs 1.6× as much for input and 2× for output; GPT-4o is 37.5% and 50% cheaper respectively. Sol's cached-input rate is lower. Sol's promotional rate is stated to last at least through 2026-11-21. Its requests above 272K input tokens have higher rates, and cache writes are separately priced; the table does not describe those cases. Rates are not subscription prices or cost-per-success comparisons. Our earlier v4.1 Sol benchmark was labeled **GPT-6 Sol medium**, not this GPT-5.6 Sol pricing comparison.

Illustrative calculation: 10M uncached input plus 1M output tokens costs $35 with GPT-4o and $60 with GPT-5.6 Sol at these rates. A GPT-4o wrapper that consumes three times those token volumes would cost $105. More calls, replayed context, verification and retries can erase a cheaper model's per-token advantage. These examples are arithmetic, not measured benchmark bills; account for actual reasoning/output accounting, caching, tool costs and provider pricing before comparing cost per solved task.

## Model size: what is known

OpenAI has not publicly disclosed a verified GPT-4o parameter count in the official API documentation or [system card](https://cdn.openai.com/gpt-4o-system-card.pdf) reviewed here. We cannot infer its size from price, context length, latency or tokenization. Rumored parameter counts are not used in this analysis.

In contrast, gpt-oss has published approximate sizes:

| Model | Total parameters | Active parameters per token |
|---|---:|---:|
| gpt-oss-120b | 117B | 5.1B |
| gpt-oss-20b | 21B | 3.6B |

These are mixture-of-experts models. Active parameters describe per-token computation, not the total weight storage or full training memory requirement. OpenAI describes their tokenizer, `o200k_harmony`, as a superset of that used by GPT-4o/o4-mini. Therefore shared tokenizer behavior is intrinsically compatible with a gpt-oss-based system; differences in our endpoint counts do not disprove that ancestry. [Official gpt-oss architecture and tokenizer description](https://openai.com/index/introducing-gpt-oss/).

## Could GPT-4o behavior be distilled into gpt-oss?

Yes, technically this is a plausible development path. The precise claim would be: start with a pretrained gpt-oss checkpoint, then further train it on selected GPT-4o-generated demonstrations. The deployed weights remain derived from gpt-oss; GPT-4o supplies training examples. The resulting model can run without calling GPT-4o at inference time. Distillation does not require access to GPT-4o weights, its undisclosed parameter count, or the same tokenizer. It does not establish that Genesys used this process.

OpenAI describes output-based distillation as a way to transfer task-specific behavior, and separately provides gpt-oss fine-tuning recipes. Those establish that the components exist, not that a particular recipe reproduces all GPT-4o capabilities or passes our benchmark. [Distillation overview](https://openai.com/index/api-model-distillation/), [gpt-oss fine-tuning recipe](https://developers.openai.com/cookbook/articles/gpt-oss/fine-tune-transfomers).

The teacher/student ordering is task-dependent: gpt-oss already has substantial reasoning and coding training. GPT-4o is not necessarily the stronger teacher for every task. I would test which behaviors improve and preserve the student's existing strengths, rather than imitate all GPT-4o outputs indiscriminately.

A technically plausible workflow is:

1. Establish clean unmodified gpt-oss baselines with correct Harmony/tool-call handling. Our historical gpt-oss DNF was described as a harness-compatibility problem, so repair that before attributing an execution failure to missing model capability.
2. Generate demonstrations of the desired actions: edit in the right directory, actually call tools rather than merely propose actions, interpret test failures, repair a patch, persist across context compaction, and finish with independently checked work.
3. Filter demonstrations using executable outcomes; retain useful recovery examples, not only immaculate successful trajectories. A GPT-4o run that needed scaffolding may supply usable steps, but it is not automatically a sound long-horizon teacher.
4. Fine-tune the student, initially with a bounded adaptation experiment, and evaluate on new repositories/tasks. Add execution-feedback training or further curated data only when failures justify it.
5. Keep the benchmark's exact prompts, reference solutions, hidden tests and reports out of training. Passing a memorized benchmark is not evidence of generalization.

Better orchestration and targeted adaptation could improve completion on our Rails-style v4 tasks. That does not imply solving v4.1's crash-consistency checks, proof-kernel soundness or compiler optimization. In particular, GPT-4o distillation alone is not an established route to the frontier tasks where our stronger reference models also failed.

## Estimated development effort: planning scenarios, not measured requirements

There is no observed learning curve for this proposed student/dataset, so no defensible claim that N examples or $X guarantees a pass. The ranges below are my engineering planning estimates for an experienced team with existing serving/training infrastructure, not published sample-complexity results or evidence of Genesys's expenditure.

| Goal | Initial retained dataset to investigate | Team/time planning allowance | What this might establish |
|---|---|---|---|
| Improve tool-call formatting and action-taking | 1K–5K verified short episodes | 1–2 engineers, roughly 2–4 weeks | Narrow behavior improvement; not reliable long-horizon completion |
| Improve completion across unseen tasks resembling v4 | 5K–30K diverse, verified multi-turn episodes plus recovery cases | 2–3 engineers, roughly 6–12 weeks | Whether targeted adaptation and scaffolding generalize across that task family |
| Reproduce broad GPT-4o capability or solve all hard v4.1 tasks | Cannot responsibly size from current evidence | Open-ended research effort | No performance guarantee from either preceding scenario |

The work includes dataset infrastructure, clean splits, regression checks, tool integration and several failed experiments. Actual effort can fall far outside these ranges. Buying more teacher samples cannot substitute for obtaining useful demonstrations and independent verification.

### Teacher-data generation arithmetic

For a concrete sensitivity calculation, assume each generated **episode** consumes a total of 10,000 uncached input and 4,000 output tokens across its calls. These are deliberately explicit example volumes, not measurements of our full seven-sprint runs. Full agent trajectories can replay much more input.

| Generated episodes | GPT-4o teacher cost | GPT-5.6 Sol teacher cost |
|---|---:|---:|
| 5,000 | $325 | $600 |
| 20,000 | $1,300 | $2,400 |
| 100,000 | $6,500 | $12,000 |

Formula: episodes × (input_tokens × input_price + output_tokens × output_price) / 1,000,000. This is $0.065/episode for GPT-4o and $0.12/episode for Sol under the assumptions above. It excludes training, test execution, storage, human review and unsuccessful extra attempts.

If only 25% of generated episodes survive quality filtering, obtaining **20,000 retained episodes** requires 80,000 generated episodes: **$5,200 GPT-4o teacher cost**, or $9,600 for Sol at the same assumed token volumes. A fourfold longer context/output budget multiplies those costs by four again. A cheaper teacher may have a lower retention rate, so price per accepted demonstration matters more than price per raw token.

### Student training compute: measure throughput before budgeting

A reproducible cost model is:

`training dollars = processed training tokens / aggregate measured tokens-per-second / 3600 × GPU count × dollars per GPU-hour`

For illustration only, assume 20,000 retained episodes averaging 14,000 training tokens, three epochs, eight GPUs and a hypothetical $3/GPU-hour. That is 840M processed tokens. At **1,000 aggregate tokens/second**, one run takes about 233 hours and costs **$5,600**; at **10,000 aggregate tokens/second**, about 23 hours and **$560**. Neither throughput is a claim about a specific gpt-oss training implementation, and $3 is an arithmetic assumption, not a current vendor quote.

Benchmark actual throughput and peak memory on the selected 20B/120B checkpoint, adapter/full-training method, context length and hardware before choosing a budget. Multiple trials multiply compute; filtering and independent evaluation add costs. The fact that quantized weights can fit on a GPU for inference does not imply full training fits there. Engineering labor may exceed the teacher and training bills.

## What this means for the Genesys hypotheses

- An independently deployed gpt-oss derivative trained with GPT-4o demonstrations is technically plausible and is **not** live GPT-4o passthrough.
- Shared `o200k` behavior is compatible with that scenario even before distillation.
- Better task completion than our assisted GPT-4o baseline is compatible with a different base, specialized training, better orchestration, or a mixture of these.
- Price and feasibility estimates establish possible development paths, not evidence that the company took one.
- The current confirmatory experiment tests behavioral resemblance to selected GPT-4o configurations. It does not include a trained gpt-oss distillation control and cannot exclude that hypothesis. Weight comparison and provenance records would be stronger evidence for gpt-oss ancestry.

## Added observable-output evidence channel

A separate [process-signals panel](confirmatory/PROCESS_SIGNALS.md) now compares final answers, short verification sentences, explicit intermediate task states, common wrong answers and wrong traces, timing, and provider-reported reasoning tokens. It includes gpt-oss-120b as an alternative. This does not treat visible explanations as private reasoning or promote stylistic similarity into an identity verdict. Collection was stopped at the user’s pivot to gpt-oss; 191 completed observations were preserved. These partial results are exploratory. Strict JSON formatting failures must be distinguished from wrong semantic answers.


## GPT-4o completion and gpt-oss pivot

The completed `gpt4o-confirmatory-20261009` run placed Genesys at mean answer-distribution distance **0.6167** from the GPT-4o baseline (95% block interval **0.5196–0.7156**). GPT-4o repeat distance was **0.2900**; alternate-system **0.4691**; verification wrapper **0.3456**; alternate snapshot **0.4061**. This is descriptive evidence against the tested plain/wrapped GPT-4o deployments. However, positive-control upper bounds overlapped negative-control lower bounds (**0.5594 vs 0.4531**), so the locked gate was **inconclusive_controls_overlap**. There is no calibrated ancestry probability or universal exclusion of GPT-4o-derived training.

At the user's request, further GPT-4o collection is stopped and the working investigation moves to [gpt-oss output forensics](oss/README.md). The new experiment uses provider and wrapper controls, fresh reference-only signature discovery, independent validation responses, and a mandatory gate before any Genesys batch. It measures actual answers and characteristic errors rather than tokenizer identity. The primary calibrated hypothesis is lightly modified gpt-oss-120B; 20B is an exploratory comparator. Extensive fine-tuning/distillation remains outside what a black-box negative result can universally exclude.

Run: `oss-output-20261009`. The frozen protocol and reproduction instructions are linked above. Token-probability comparison was capability-tested: Genesys rejects `logprobs`, so it is unavailable through the tested API. The run has now completed reference discovery without establishing enough candidate signatures; see the completion note below.

## Working hypothesis: gpt-oss adapted for long-horizon agent work

**Hypothesis, not an attribution finding:** Genesys could use a gpt-oss base with additional training and/or orchestration that improves sustained agent execution. Better completion than the tested stock deployments does not exclude that ancestry.

Our DNF results establish failure of the tested model/provider/harness configuration. They do not establish an architectural ceiling. The historical v4 120B DNF note records two sprint-2 no-op runs with no multiuser implementation; the v4.1 Raft grades for both OSS sizes record 0/24 passing tests despite compilable artifacts. These observations do not, by themselves, isolate context management, model reasoning, tool integration, or termination behavior as the sole cause. The earlier shorthand “harness-compatibility problem” should not be treated as a proven complete explanation.

Plausible development paths:

| Mechanism | Intended improvement | What would distinguish it experimentally |
|---|---|---|
| Supervised training on successful and corrected tool-use trajectories | Act instead of repeatedly planning; interpret tool results; repair errors; continue until verified completion | Fewer premature stops and tool mistakes under the same external harness, measured on held-out tasks |
| Reinforcement learning in executable coding environments | Recover from failed attempts, avoid loops, preserve working features and complete longer task sequences | Improved verified success as task length increases, without rewarding token consumption or mere persistence |
| Training for context compaction and external memory | Preserve decisions, outstanding requirements and recovery state across context resets | Controlled compaction/resumption tests with identical supplied state and explicit checks for lost requirements |
| Inference-time orchestration, without weight changes | Persist task state, manage context, detect stalls, verify progress and restart failed steps | Stock gpt-oss improves when supplied the same orchestration; differences shrink under matched scaffolding |

These mechanisms can coexist. Long-running sessions consist of many bounded calls and need not fit their entire history into a single context window. Fixing workflow reliability is a narrower achievement than learning all the reasoning needed for the hardest tasks. Session completion and functional correctness must be scored separately.

OpenAI publishes a gpt-oss LoRA fine-tuning recipe; its demonstrated task is multilingual reasoning, not long-horizon coding. It establishes a practical adaptation mechanism, not a result on our benchmark. [Official recipe](https://developers.openai.com/cookbook/articles/gpt-oss/fine-tune-transfomers).

AutoCompact provides research evidence for training context-management behavior: supervised training followed by reinforcement learning for compaction and coding reportedly improves SWE-bench Verified by 9.2 percentage points and SWE-PolyBench Verified by 5.0 points. Those are the authors' results on their setup, not measurements of Genesys or proof of equivalent gpt-oss gains. [AutoCompact](https://arxiv.org/abs/2610.02163).

An illustrative reliability calculation explains why completion can improve sharply: if 100 steps each independently avoid an unrecoverable failure with probability 0.98, all-step survival is 0.98^100, approximately 13.3%; at 0.995 it is approximately 60.6%. Real agent failures are dependent and recoverable, so this is an explanatory toy model, not a fit to our observations or a forecast.

**Implication for the current forensics:** a stock-OSS behavioral mismatch would weaken the unmodified/lightly wrapped hypothesis. It would not exclude substantial post-training. Our current short-output assay does not test whether long-horizon adaptation caused Genesys's improvement, and it contains no independently trained long-horizon OSS derivative as a positive control. The stronger causal follow-up would compare stock OSS, stock OSS with matched orchestration, and an adapted OSS checkpoint on held-out tasks at increasing horizons, holding tool interface, budgets and grading fixed. That follow-up is a proposed experiment, not an experiment already run.

## Working hypothesis: benchmark performance is limited partly by agent execution

The user proposes that many programming tasks may already be within older/open models' knowledge and reasoning capabilities, while observed completion gaps reflect tool integration, context handling, persistence and recovery. This is plausible for some tasks and is consistent with a derivative achieving strong end-to-end results. It is not evidence that general programming is solved or that underlying model capability has stopped improving since GPT-4o.

v4.1 measures a deployed system: model weights and post-training, prompts, provider behavior, tool interfaces, agent controller, available context/compute and environment. Identical external harness code does not ensure identical compatibility with different models. DNF is an outcome category, not a causal diagnosis. Conversely, defective agent behavior learned by a model is not necessarily a harness bug. Context use, planning and error correction may improve through weight changes; 'agentic improvement' and 'core-model improvement' are not mutually exclusive.

The first Genesys run and Astra/Fable reached 100 on the first three tasks, creating a ceiling that limits ranking on those tasks. The added frontier tasks did separate systems: on the Lean kernel task, Genesys scored 0 while Astra and Fable scored about 98; on flash filesystem, the initial Genesys score was about 40.9 versus Fable's 99.3. Those gaps require failure-specific diagnosis before being assigned to reasoning or infrastructure. They do not support an unrestricted single ordering of models, nor does any single run establish a stable general 'between Grok and Fable' position.

The discriminating experiment would cross models with harness configurations, and independently vary task horizon and reasoning difficulty. Include short, difficult, self-contained programming subproblems; long sequences of individually straightforward steps; and full repository tasks. Under matched budgets, measure functional correctness, infrastructure failures, premature termination, recovery and repetition variability separately. If model gaps shrink after compatibility fixes, that supports an execution bottleneck. If gaps persist on short, correctly delivered tasks, that supports a capability difference on those tasks. Larger budgets can compensate for some weaknesses and should be measured rather than silently unequal.

This experiment is proposed, not launched. The existing OSS forensic run remains unchanged. No premise here assumes a model can solve an open Millennium Prize Problem; bounded, independently verifiable difficult problems are appropriate controls.

Research context: Anthropic explicitly describes agent evaluations as measuring harness and model together in [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents). [SWE-agent](https://arxiv.org/abs/2405.15793) studies how the agent-computer interface affects software-engineering performance. These support investigating harness effects, not attributing every observed gap to the harness.


## v5 benchmark design follow-up

The harness-versus-capability hypothesis now has a concrete [v5 design proposal](../benchmark-v5/DESIGN.md), summarized in the [v5 entry point](../benchmark-v5/README.md). It separates native-kit unattended results, standardized two-nudge rescue, minimal continuation controls and independently initialized capability tasks. It also retains accumulated-project failures, critical correctness gates and actual service availability. No v5 implementation or paid run has started; the gpt-oss forensic protocol remains unchanged.


## gpt-oss output discovery completed — no usable classification assay

`oss-output-20261009` finished at 2026-10-09T15:13:29Z. All 672 scheduled discovery observations were resolved: 562 usable responses, 17 HTTP errors, 6 truncated responses, and 87 circuit-open skips. The exploratory 20B route contributed only 5 usable responses out of 96; repeated provider failures opened its circuit. Each 120B profile had 90–95 usable observations out of 96, so the primary references were substantially observed.

The locked discovery rule selected **one independent block**, a rare-copy response pattern, against a minimum of eight. It therefore stopped with `completed_no_validated_signature`. No independent validation or Genesys target batch was run. One selected pattern is exploratory and could be sampling noise; it is not an attribution result. The study failed to establish a sufficiently distinctive, robust output assay. It neither confirms nor rules out gpt-oss derivation, and the impaired 20B route cannot support a 20B comparison.

[Local detailed report](runs/oss-output-20261009/report.md), [sealed selection](runs/oss-output-20261009/selection.json), [frozen protocol](oss/PROTOCOL.md). Raw run links are local/git-ignored. No new volume-only run has been started after the gate stopped.


## Expanded candidate search: Phi-4-mini and OSS derivatives

A new [candidate survey](CANDIDATES.md) checked nine tokenizer files at pinned Hugging Face revisions. Six previously untested checkpoints matched all 768 existing held-out o200k token counts: Phi-4-mini-instruct, mini-reasoning, mini-flash-reasoning, multimodal-instruct, gpt-oss-160b-kiwi and gpt-oss-coder-20b. Motif-2.6B matched 694/768; Phi-4 and Phi-4-reasoning-plus matched 309/768. This broadens candidate coverage, particularly to an independent Microsoft family, without adding ancestry evidence. No generation or paid comparison was run. The survey records local/hosted options and the distinction between tokenizer compatibility and behavioral correlation.


OpenRouter follow-up: seven live candidate availability probes returned no usable endpoint (two HTTP 404, five HTTP 400 invalid model IDs), consistent with the refreshed catalog. No behavioral comparison was possible through OpenRouter. See [candidate availability details](CANDIDATES.md#openrouter-live-availability-test).
