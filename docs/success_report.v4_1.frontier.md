# v4.1 P4–P6: Genesys House on FrontierSWE v2

Completed 2026-10-05 at 04:19 São Paulo. **Genesys House scored 40.901 on the
flash filesystem, 0 on the Lean checker, and 0 on Cranelift optimization.**
These tasks expose limitations that the saturated P1–P3 suite did not measure.
This initial report covers Genesys only. Astra has since completed the extension;
see the [current comparison with Astra and Fable](success_report.v4_1.frontier_comparison.md).

## Results

| Task | Score / 100 | Trial wall time | Grader finding |
|---|---:|---:|---|
| P4: flash filesystem in Zig | 40.901 | 6h 59m | 51.1263% correctness; zero performance component |
| P5: Lean kernel checker in Pascal | 0 | 1h 54m | Accepted invalid proofs, triggering the hard soundness gate |
| P6: Cranelift code-generation optimization | 0 | 4h 06m | Correct compilation, but no qualifying held-out speedup |

Wall times include setup and verification; their sum is approximately 12h 59m.
All three trials completed before their 20-hour agent limits, without recorded
agent exceptions. These are valid grader outcomes, not infrastructure zeroes.
Billing is unavailable in Harbor's results; null cost does not mean free usage.

### P4: substantial implementation, incomplete correctness

Correctness across the four flash geometries ranged from 46.68% to 59.32%.
The block-device gate passed. All nine performance metrics were measured, but
the worst-metric performance component was zero (`bench_file.readed`). The
upstream formula yielded reward 0.40901. The score is not simply a test pass rate.

### P5: permissive acceptance defeats proof checking

The checker accepted 473/476 valid environments and rejected 96/131 invalid
ones. It incorrectly accepted **16 cases containing a closed proof of False**.
The upstream hard gate therefore forced reward zero. The ungated diagnostic
reward was 0.737777, which must not be substituted for the official result.
All 607 cases were executed; the suite deadline was not hit. The verifier's
execution-delegation tripwire was clean.

### P6: correct edits that did not generalize into sufficient speedup

Genesys changed 11 code-generation source files. The submission built, passed
the canaries and edge checks, and introduced no regressions relative to the
344 passing reference cases in the 492-case Wasm suite. All ten hidden workloads
produced correct outputs.

The full geometric-mean speedup was only 1.001601×. The outlier-dampened scored
speedup was 0.999861×, below the 0.5% deadband, so the reward was zero. Compilation
work was 1.000543× baseline and incurred no penalty. This is an optimization
failure under the benchmark metric, not a broken compiler.

## Provenance and limits

- Source: [FrontierSWE v2](https://github.com/Proximal-Labs/frontier-swe-v2),
  pinned at `da83f84f8fbcec3cbf0f2b17c98ebc811355c2df`; original task prompts,
  artifact rules, and digest-pinned agent/verifier images. See the
  [manifest](../benchmark-v4.1/frontier/manifest.json).
- Model: `lua/genesys-pi-house`; Harbor 0.23.0 with OpenCode 1.18.34 and a small
  installation/network-preflight adapter. One scored attempt per task. Worker
  logs show OpenCode subagent activity; this was not a tools-off evaluation.
- Separate verifiers graded captured submissions. P4/P5 references scored 100
  and no-op controls scored zero. P6's unchanged compiler scored zero, with
  correctness passing, in both controls. This establishes pipeline operation;
  it is not an exhaustive independent audit of every verifier rule.
- **P6 used 32 GiB instead of upstream's 128 GiB.** P4/P5 kept their original
  limits. P6 therefore cannot be called a resource-matched reproduction.
- The published leaderboard uses Proximus and five trials. Its scores are
  contextual evidence, not a controlled local ranking against this single
  OpenCode attempt. Astra/Fable parity or superiority on P4–P6 remains untested
  locally. Keep these results separate from the historical P1–P3 total.
- Three setup/network/preflight failures preceded the scored P4 attempt. Their
  records are retained separately; they produced no model solutions and are
  excluded from capability scores.

## Evidence and conclusion

The [machine-readable summary](../results-v4.1/frontier/summary.json) records
scores, timings, controls, resource deviations, and hashes of each original
Harbor result and reward file. Compact task records:
[P4](../results-v4.1/frontier/crash-proof-flash-filesystem/genesys.json),
[P5](../results-v4.1/frontier/lean-4-kernel-type-checker-in-pascal/genesys.json),
[P6](../results-v4.1/frontier/cranelift-codegen-opt/genesys.json).
Large submitted artifacts, case-level evidence, and transcripts remain local
under the ignored `results-v4.1/frontier/jobs/` tree. Seven runner regression
checks passed; summary values were checked against the original grader outputs.

The original perfect scores establish success on P1–P3. This extension shows
that success does not extend to these harder tasks under the tested setup.
The strongest failure is Lean soundness; Cranelift retained correctness but
failed the optimization objective. A next comparison would run Astra and Fable
on the same pinned tasks and local resource profile. Those runs are not scheduled.
