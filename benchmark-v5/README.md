# v5 proposal: coding capability, autonomy and supervision cost

**Status: design proposal, 2026-10-09. No v5 implementation or model runs yet.**

v5 should answer: **Which model+harness kit produces correct, safe changes, on which kinds of work, with how much supervision, time and money?** It should also test the hypothesis that modest assistance makes the tested kits converge. It must be capable of finding convergence; separation is not a required outcome.

The primary object is a complete, versioned kit, not an inferred model IQ or training origin. The full [design and staged implementation plan](DESIGN.md) specifies concrete tasks, assistance policies, diagnostic controls, scoring, replication and acceptance criteria.

## Proposed changes

| v4/v4.1 limitation | v5 change |
|---|---|
| DNF mixes stopping, infrastructure and incorrect solutions | Preserve completion status, infrastructure validity and functional correctness as separate fields |
| Small prompts can potentially rescue a run | Report unattended and standardized two-nudge outcomes separately, with a minimal-continuation control |
| Early failure blocks later sprints | Keep the accumulating project track; add independent validated starting checkpoints |
| First three v4.1 tasks saturated for several kits | Add hidden variants, interacting constraints and a calibrated difficulty ladder |
| Gated zeros hide distance from success | Retain critical gates, also publish ungated diagnostic facets and concrete counterexamples |
| One run can dominate the story | Repeat, pair task variants, interleave kits and report uncertainty at the task-family level |
| Different kits/resources are hard to interpret | Freeze full deployment manifests; compare native kits first and run selected harness crossover controls |
| One score obscures user tradeoffs | Publish success versus assistance/time/cost, with regressions and critical failures visible |

## First pilot

Four representative kits, six development task instances, two fresh repetitions: **48 initial attempts**, with up to two continuation branches per unsuccessful attempt where reliable state cloning is possible. This is an instrument-validation pilot, not a public ranking. Candidate identities and exact versions are frozen only after access and compatibility checks. No paid run is launched by this proposal.

The main gpt-oss [forensic experiment](../model-forensics/oss/README.md) remains separate. v5 will not infer ancestry from coding scores or reuse forensic probes as capability tests.

Existing evidence: [v4 design](../benchmark-v4/README.md), [v4.1 suite](../benchmark-v4.1/README.md), [frontier gap analysis](../docs/success_report.v4_1.frontier_comparison.md).
