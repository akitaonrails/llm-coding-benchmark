# v4.1 coding benchmark: tests, results, analysis and reproduction

Start here for the complete v4.1 suite. It contains three original accumulating
builds (P1–P3) and three independent FrontierSWE tasks (P4–P6). It is separate
from the v4 Rails/sabotage benchmark.

**Finding:** Genesys House, Astra and Fable saturated the original three tasks.
The harder extension separated them: Fable led all three extension scores,
Astra and Fable both substantially outperformed Genesys on Lean soundness, and
Genesys outscored Astra on filesystem correctness. These are single-attempt
model-and-harness results, not proof of a universal model ranking.

## Read the results

| Task — score /100 | Genesys House | Astra | Fable |
|---|---:|---:|---:|
| P1: replicated key/value store | 100 | 100 | 100 |
| P2: transactional storage engine | 100 | 100 | 100 |
| P3: typed language implementation | 100 | 100 | 100 |
| P4: crash-proof filesystem | 40.901 | 27.232 | 99.267 |
| P5: Lean kernel checker | 0 | 98.070 | 98.410 |
| P6: Cranelift optimization | 0 | 0 | 26.375 |

P1–P3 are objective grader scores. P4–P6 use distinct upstream reward formulas;
zero can mean a failed soundness gate or insufficient optimization, not an API
failure or no working implementation. Do not combine the six into an unexplained
pass percentage.

- **[Final P4–P6 comparison and gap analysis](../docs/success_report.v4_1.frontier_comparison.md):**
  what each task requires, why it is difficult, case-level failures, distance from
  success, scoring gates, runtime differences, and limits of the conclusions.
- **[Original P1 report](../docs/success_report.v4_1.md):** Raft findings, original
  model/control comparison and harness details. Its parity claims are limited to
  those original tests.
- **[P1 machine-readable results](../results-v4.1/_wave_summary.json),
  [P2 results](../results-v4.1/storage/_wave_summary.json),
  [P3 results](../results-v4.1/typedlang/_wave_summary.json):** include the broader
  control-model roster and completion status, not just the three headline models.
- **[Initial Genesys P4–P6 report](../docs/success_report.v4_1.frontier.md):** historical
  detail and provenance. The final comparison above supersedes its then-current
  statements about which anchor runs were pending.

## Understand the tests

| Task | Definition and implementation materials |
|---|---|
| P1: linearizable replicated KV, Raft variant in Go | [Contract](raft/CONTRACT.md), [sprint prompts](raft/prompts), [grader](raft/grader) |
| P2: transactional storage engine | [Contract](storage/CONTRACT.md), [sprint prompts](storage/prompts), [grader](storage/grader) |
| P3: type inference, bytecode VM and garbage collection | [Contract](typedlang/CONTRACT.md), [language specification](typedlang/harness/SPEC.md), [sprint prompts](typedlang/prompts), [grader](typedlang/grader) |
| P4: crash-proof NOR flash filesystem in Zig | [Task explanation and results](../docs/success_report.v4_1.frontier_comparison.md#p4-crash-proof-nor-flash-filesystem-in-zig) |
| P5: Lean 4 kernel type checker in Pascal | [Task explanation and results](../docs/success_report.v4_1.frontier_comparison.md#p5-lean-4-kernel-type-checker-in-pascal) |
| P6: optimize Cranelift-generated machine code | [Task explanation and results](../docs/success_report.v4_1.frontier_comparison.md#p6-improve-cranelift-generated-machine-code) |

P1–P3 accumulate functionality over successive sprints and culminate in objective
adversarial grading. P4–P6 retain the original upstream prompts and independent
containerized verifiers rather than converting them into Go sprints.

## Reproduce the runs

**[P4–P6 reproduction guide](frontier/README.md)** contains host requirements,
authentication, pinned harness versions, control runs, exact queue commands,
monitoring, artifact locations and failure recovery. Start there to reproduce
the Genesys/Astra/Fable comparison. The local Cranelift runs used **32 GiB**, below
upstream's 128 GiB; this is explicitly recorded and must be preserved for a
matched local comparison.

For P1–P3, use the existing problem-parameterized runners and model configuration:

- [Model IDs and harness configuration](../config/models_v41.json).
- [Full sprint-wave runner](../scripts/run_v41_wave.py).
- [Individual sprint runner](../scripts/run_v41_sprint.py).
- [Objective grader](../scripts/run_v41_grade.py).

The wave runner accepts `--problem raft`, `storage`, or `typedlang` and a
**comma-separated** list of configured model slugs, for example:

```sh
python scripts/run_v41_wave.py --problem raft --models v2_genesys_pi_house,v41_gpt_6_astra,v41_fable_5_1
```

Run from the repository root, with the configured provider/native CLI access and
Go toolchain available. Inspect the runner and model configuration before starting;
these older runners have different setup and resume behavior from the FrontierSWE
queue. Preserve existing results and use an isolated checkout for replication.
The FrontierSWE guide documents P4–P6 setup, not a replacement setup guide for
these older runners.

## Evidence and scoring integrity

- [Pinned upstream revision, image digests and resource settings](frontier/manifest.json).
- [P4 compact records](../results-v4.1/frontier/crash-proof-flash-filesystem),
  [P5 records](../results-v4.1/frontier/lean-4-kernel-type-checker-in-pascal),
  [P6 records](../results-v4.1/frontier/cranelift-codegen-opt): model scores,
  controls, versions and raw-result provenance.
- [Initial Genesys evidence summary](../results-v4.1/frontier/summary.json).
- [FrontierSWE runner](../scripts/run_v41_frontier.py),
  [serial queue](../scripts/run_v41_frontier_wave.py),
  [runner checks](../scripts/test_v41_frontier.py).

The final report links individual result files. Raw transcripts, large submitted
workspaces, and private credential material are not bundled in the public repo;
raw paths in compact records refer to the original machine. New runs generate
their own evidence. Subscription/API availability and model behavior may change,
so identical setup does not guarantee identical outputs.

Different native harnesses were used: Genesys/OpenCode, Astra/Codex, and
Fable/Claude Code. The tested object is the complete model-plus-harness system.
The original hypothesis was that a smaller model with strong agentic training
could match frontier systems; the harder extension limits that claim rather than
assuming it true. See the final report for the observed differences and caveats.
