# Observable outputs and process signals

This supplement tests actual generated answers and explicit task outputs. It is separate from the main confirmatory run and does not change its selection or calibration thresholds.

Run: `process-signals-20261009`. Its worker automatically starts after the main run's tokenizer phase completes. It may overlap reference discovery/calibration, so latency is exploratory and affected by hosting/load; this is not a clean hardware timing experiment.

## Design

Sixteen deterministic state-transformation tasks (numeric and symbolic; 4 or 12 steps), each requested in three formats:

1. Final answer only.
2. Final answer plus one short verification sentence.
3. Final answer plus the explicit state after every operation, in JSON.

Three repeats per condition and four profiles: pinned GPT-4o, the same GPT-4o with a draft/check call, gpt-oss-120b, and Genesys House. This produces **576 output observations**, with up to **720 physical calls** including verification. Temperature is omitted for all. The requested output allowance is 1,536 tokens; failures, invalid formats and truncation remain visible. No generated code is executed.

These are task-state traces, like printing the successive values of a computation. They are externally checkable answers, **not privileged internal chain of thought**. A correct final answer can coexist with an incorrect trace, and the report records that separately. Verification sentences are visible explanations, not evidence that the model actually used that procedure internally.

## Recorded indicators

- Exact final answers and their correctness.
- Same incorrect answer across endpoints, not merely similar aggregate scores.
- Entire matching incorrect state sequences and the first incorrect step.
- Changes under answer-only, short-check and state-trace instructions.
- Visible check sentences, with pairwise word-bigram similarity as a weak descriptive style signal. Shared prompt wording and common explanations can produce high similarity.
- End-to-end request latency; all calls retained for two-call wrappers.
- Provider-reported reasoning-token counts, response model, system fingerprint and violations of requested output limits.

Reported reasoning tokens are accounting metadata, not proof of a particular reasoning architecture. Identical metadata can be copied; different wrappers can rewrite it. The collector does not request or store hidden reasoning text. The checks are paired with output evidence rather than used alone for attribution.

## Reproduce / inspect

```sh
python3 model-forensics/confirmatory/process_probes.py plan my-process-run
python3 model-forensics/confirmatory/process_probes.py run my-process-run
```

Optional sequencing: pass `--after-tokenizer <main-run-name>` to `plan`. Keys come from the same environment variables as the main suite. For the live run:

```sh
cat model-forensics/runs/process-signals-20261009/status.json
tail -n 10 model-forensics/runs/process-signals-20261009/runner.log
python3 model-forensics/confirmatory/process_probes.py report process-signals-20261009
```

Manifest, source snapshots, journals and individually sealed observations live under that run directory. The runner updates status after every observation and regenerates `analysis.json`/`report.md` every eight observations. A crashed in-flight observation is marked uncertain rather than replayed. Three consecutive infrastructure failures per profile stop further network calls for that profile and label its remaining observations `circuit_open`; they are not counted as successful tests.

This panel is exploratory. Its three repeats and limited task families do not supply a calibrated identity probability. It supplies concrete output evidence—including a gpt-oss alternative—to interpret alongside the larger confirmatory experiment. It does not train a distilled gpt-oss control, recreate full long-horizon coding, or equate matching explanations with shared model internals.
