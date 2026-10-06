# v4.1 FrontierSWE comparison: Genesys, Astra and Fable

Status: complete. Updated 2026-10-06T18:58:48+00:00.

All nine scored attempts are complete. **Fable achieved the highest score on
all three tasks in this run.** Its strongest separation was the filesystem,
where it approached full correctness, and Cranelift, where it was the only model
to earn optimization credit. Astra and Fable both substantially outperformed
Genesys on Lean's soundness requirements. Genesys nevertheless outscored Astra
on the filesystem, so the results do not form a uniform model hierarchy.

## Scores

Scores are 100 × the original grader reward, not interchangeable test-pass percentages.

| Task | Genesys House | Astra | Fable |
|---|---:|---:|---:|
| P4: flash filesystem | 40.901 | 27.232 | 99.267 |
| P5: Lean checker | 0.000 | 98.070 | 98.410 |
| P6: Cranelift optimization | 0.000 | 0.000 | 26.375 |

## What the tests require, and how the three models compared

### P4: crash-proof NOR flash filesystem in Zig

Implement the filesystem itself in Zig, exposing the required C-compatible API.
Tests inspect both behavior and exact on-disk metadata, exercise crash recovery,
and use four flash geometries. Benchmarks measure flash reads, writes and erases.
This tests persistent-state correctness and storage efficiency, not just file API calls.

Genesys scored **40.901/100**, versus **27.232/100** for Astra. Their correctness
components were **51.1263%** and **34.0398%**, respectively. Genesys led across all
four geometries. Both passed the block-device gate. Astra had the better performance
component (1 versus 0), but its lower correctness left its overall score lower.
Neither produced a broadly correct filesystem under this grader.

Fable scored **99.267/100**, with **99.6993% correctness** and a performance
component of 0.978305. Its correctness was above 99.4% on every geometry.
This is a large improvement in the underlying checks, not a rounding effect
or just a scoring gate. It still missed some checks, so the result does not
establish perfect crash safety outside this suite.

### P5: Lean 4 kernel type checker in Pascal

Implement a checker that accepts valid Lean environments and rejects invalid ones.
The central requirement is soundness: a checker that accepts a bogus proof cannot
be trusted merely because it also accepts many valid proofs. The grader therefore
includes a hard gate for accepting closed proofs of False.

| Diagnostic | Genesys | Astra | Fable |
|---|---:|---:|---:|
| Valid cases accepted | 473/476 | 476/476 | 475/476 |
| Invalid cases rejected | 96/131 | 130/131 | 131/131 |
| Soundness subset passed | 49/60 | 59/60 | 59/60 |
| Ungated diagnostic score /100 | 73.778 | 98.070 | 98.410 |
| False-proof gate | Failed | Passed | Passed |
| Official score /100 | 0 | 98.070 | 98.410 |

All three executed all 607 cases without hitting the suite deadline. Genesys incorrectly
accepted 35 invalid cases, compared with one for Astra. Genesys accepted 16 cases
containing a closed proof of False, triggering the mandatory zero. The soundness
subset and false-proof gate are distinct checks: Astra missed one soundness case
but still passed the false-proof gate.

The 0-versus-98 gap is magnified by the gate, but the underlying difference is real:
Astra rejected substantially more invalid inputs. Genesys built substantial working
functionality; its zero does not mean it did nothing. The ungated score is diagnostic
and must not replace its official zero.

Fable rejected every invalid case but rejected one valid case; Astra accepted
every valid case but also accepted one invalid case. Fable's slightly higher
score follows the grader's weighting. This is a close result between those
two models, unlike the much larger difference from Genesys. Neither checker
is proven generally sound by a finite test suite.

### P6: improve Cranelift-generated machine code

Modify Wasmtime's Cranelift compiler backend in Rust/ISLE so the machine code it
emits executes faster, while preserving correctness and avoiding excessive compile
work. Hidden workloads check whether an optimization generalizes beyond examples.

Both submissions built, produced correct outputs on all ten hidden workloads, and
introduced no detected Wasm-suite regressions. Genesys changed 11 code-generation
source files; Astra changed five (six source files overall).

The scored speedup was **0.999861×** for Genesys and **1.002023×** for Astra.
Both fell below the grader's 0.5% speedup deadband and received **0/100**.
These are successful implementations without a qualifying optimization result,
not API failures.

Fable changed 26 code-generation source files and achieved a scored speedup
of **1.070854×** in the grader's simulated work metric: about 6.62% less
modeled generated-code work, not a measured wall-clock speedup. It built successfully, preserved correctness on all ten
hidden workloads, and introduced no detected Wasm-suite regressions. Its
**26.375/100** is an optimization reward, not a 26% correctness pass rate.

## Fable final results

- **P4: flash filesystem:** 99.267/100. Correctness 99.6993%; performance component 0.978305; block-device gate 1.0.
- **P5: Lean checker:** 98.410/100. Accepted 475/476 valid cases; rejected 131/131 invalid cases; false-proof gate 1.0.
- **P6: Cranelift optimization:** 26.375/100. Scored speedup 1.070854; correctness 1; build success 1.

Queue state at this update: `completed`.

## Gap analysis: what failed, how far short, and why it matters

“Only Fable succeeded” needs qualification. Fable was the only model to approach
complete filesystem correctness and the only one to earn Cranelift optimization
credit. **Astra was very close to Fable on Lean.** None scored 100 on any task.
The distances below describe these particular submissions, not the number of
hours or edits another attempt would require to fix them.

### Filesystem: ordinary operations worked; failure recovery was the dividing line

Imagine a device losing power halfway through renaming a file. After reboot, the
filesystem must recover a coherent state, without losing unrelated files or
reusing blocks that still contain live data. NOR flash adds erase-block and
programming constraints: updating persistent metadata requires carefully ordered
writes, recovery information, and handling of worn or unusable blocks. LittleFS's
reference design uses redundant metadata pairs and error detection for this
reason. [LittleFS design](https://github.com/littlefs-project/littlefs/blob/master/DESIGN.md)

This task is more demanding than implementing a dictionary of filenames and byte
arrays. The submission must implement the behavior in Zig, export the expected
C-compatible interface, and reproduce reference block-device checksums. Correct
API return values alone are insufficient. Tests cover allocation, directory
updates, metadata consistency, full devices, bad blocks, recovery of orphaned
metadata, relocation, and injected power loss, across four flash geometries.
These behaviors interact: fixing a write path can alter the persisted state that
crash recovery, directory traversal, or future allocation depends on.

The strongest evidence for the gap comes from the **default geometry**, where
all models faced the same denominators:

| Selected suite: checks passed | Genesys | Astra | Fable |
|---|---:|---:|---:|
| Ordinary file operations | 6,868/7,155 | 7,067/7,155 | 7,149/7,155 |
| Truncation | 1,093/1,270 | 1,270/1,270 | 1,270/1,270 |
| Paths | 217/325 | 10/325 | 325/325 |
| Allocation | 290/367 | 20/367 | 353/367 |
| Move operations | 109/161 | 8/161 | 161/161 |
| Bad blocks | 94/300 | 63/300 | 300/300 |
| Full-device/exhaustion cases | 0/85 | 1/85 | 85/85 |
| Orphan recovery | 7/60 | 21/60 | 60/60 |
| Power loss | 5/21 | 0/21 | 21/21 |
| Relocation | 0/92 | 0/92 | 89/92 |

This was **not a total implementation collapse** for Genesys or Astra. Astra even
beat Genesys on ordinary file operations and truncation. But both were far from
reliable across the behaviors that make a filesystem safe under failure. A
submission passing normal reads and writes but failing power-loss recovery has
missed a central requirement, not a cosmetic edge case. The table establishes
which behaviors failed; it does not identify a single defective algorithm as the
cause without targeted debugging of the submitted code.

The scoring deliberately prevents large easy suites from hiding these failures.
It averages suite pass fractions with weights of 1 for ordinary operations, 3 for
several metadata/allocation operations, and 5 for difficult recovery/adversarial
suites. A suite with thousands of file cases therefore does not drown out a
smaller power-loss suite.

| Distance measure | Genesys | Astra | Fable |
|---|---:|---:|---:|
| Raw checks passed, all geometries | 15,702/18,787 | 14,855/18,787 | 18,753/18,787 |
| Raw failures, all geometries | 3,085 | 3,932 | 34 |
| Weighted correctness | 51.1263% | 34.0398% | 99.6993% |
| Weighted correctness shortfall to 100% | 48.8737 pp | 65.9602 pp | 0.3007 pp |
| Official score shortfall relative to Fable | 58.3657 points | 72.0349 points | — |

Raw counts are diagnostic only; the official weighted metric is the meaningful
correctness comparison. Genesys had about **91 times**, and Astra **116 times**,
as many failing raw checks as Fable. These ratios describe the test inventory,
not independent bugs: one broken mechanism can fail many related checks.

The reward is `100 × correctness × (0.8 + 0.2 × effective performance) × gate`.
The performance bonus is disabled below 75% weighted correctness and ramps to
full strength at 95%. Thus Astra's nominally perfect I/O component contributed
**nothing** at 34% correctness; Genesys also remained below the bonus threshold.
Even perfect I/O alone could not rescue either submission. Fable passed that
threshold and combined near-complete correctness with a 97.8305% performance
component. Its remaining 34 raw failures show that it was close, not perfect.

### Lean: two near-complete checkers, and one dangerously permissive checker

A Lean kernel checker is the last verifier between a purported mathematical proof
and accepting its conclusion. The task is not to invent proofs or run tactics:
it receives exported declarations and must decide whether their terms and types
are admissible. Every declaration must check; rejecting everything is also wrong.

Types can depend on values, and deciding that two types match may require reducing
expressions rather than comparing their syntax. The checker must correctly handle
binding/substitution, universe levels, definitions, inductive declarations and
elimination rules. Lean also treats proofs of the same proposition as
definitionally equal, so an overly broad equality shortcut can accept something
invalid. [Lean's type system](https://lean-lang.org/doc/reference/latest/The-Type-System/)

The implementation must do this in Pascal, with no delegation to another checker.
The task's input contract spans tiny adversarial files through roughly 90 MB
exports with over 1.5 million objects. This combines parsing and memory-management
work with exact logical rules and efficient reduction. Being permissive makes
valid files easy to accept, but undermines the purpose of the checker.

| Distance measure | Genesys | Astra | Fable |
|---|---:|---:|---:|
| Wrong decisions among 607 cases | 38 | 1 | 1 |
| Valid environments wrongly rejected | 3/476 | 0/476 | 1/476 |
| Invalid environments wrongly accepted | 35/131 (26.72%) | 1/131 (0.76%) | 0/131 |
| Closed-False-proof cases wrongly accepted | 16 | 0 | 0 |
| Ungated diagnostic score /100 | 73.7777 | 98.0695 | 98.4102 |
| Official score /100 | 0 | 98.0695 | 98.4102 |

Genesys correctly decided **569/607** cases, so calling it wholly nonfunctional
would be inaccurate. But it admitted more than one quarter of the invalid cases,
including 16 cases in which it certified a closed proof of False. That is a
serious trust failure for this particular application. Its ungated deficit to
Astra was **24.2918 points**; the hard gate expanded the official gap to 98.0695.
Both statements matter: the gate amplifies the score difference, but does not
invent the underlying soundness problem.

Astra and Fable were **equally close in raw error count**. Astra's lone miss was
`scored-039`: an invalid soundness-tier case incorrectly accepted, but not a
closed proof of False. Fable's lone miss was `scored-225`: a valid soundness-tier
case incorrectly rejected. Neither was a suite deadline failure. Soundness-tier
cases receive tenfold weight, and the weighted accept/reject denominators differ;
that explains Fable's **0.3407-point** lead despite both missing one case.

This is not a case where Astra failed and only Fable succeeded. Both passed the
hard gate and came close to the suite maximum. Fable made the safer kind of error
in this run—rejecting a valid file rather than accepting an invalid one—but neither
finite test result proves the implementation sound for all possible inputs.

### Cranelift: correct compilers, very different breadth of optimization

Here the starting point is an already working production compiler backend. The
agent must find opportunities in Rust/ISLE code so that generated x86 machine code
does less work. It must preserve details such as integer overflow and division
edges, floating-point results, shift masking, and traps. Optimizations interact
with instruction selection, register pressure, spills, and calling conventions;
a locally shorter instruction sequence can make another workload worse.

The task measures **weighted generated-code work under simulation**, not elapsed
execution time on this host. Its “speedup” is baseline work divided by candidate
work. A 1.070854× result represents about **6.62% less modeled work**, not direct
proof of 7.1% more real-world throughput. Compile work is measured separately:
up to 10% extra is unpenalized, with reward declining to zero at 20% extra. The
objective matches Cranelift's need to balance generated-code quality with fast
compilation. [Cranelift project](https://cranelift.dev/)

All three models passed every measured workload's output check and preserved the
344 reference-passing cases in the 492-case Wasm suite. Their zero scores were
**not correctness disasters**. The distinction was whether the optimizations
benefited enough of the hidden workload mix:

| Hidden workload: baseline/candidate work | Genesys | Astra | Fable |
|---|---:|---:|---:|
| bz2 | 0.996253× | 0.991554× | 1.102193× |
| intgemm-simd | 1.002776× | 1.000056× | 1.015284× |
| libsodium-pwhash_argon2id | 1.000016× | 1.000637× | 1.052149× |
| meshoptimizer | 1.003956× | 1.000201× | 1.048261× |
| regex | 0.995773× | 1.012657× | 1.129940× |
| shootout-base64 | 1.000000× | 0.997602× | 1.028888× |
| shootout-matrix | 1.000000× | 1.003074× | 1.140774× |
| shootout-ratelimit | 1.000002× | 1.006710× | 1.070508× |
| shootout-switch | 1.000000× | 1.044830× | 1.137757× |
| zstd-benchmark | 1.017401× | 1.005857× | 1.059537× |

A ratio below 1 means more work than the reference. Genesys's best gain was zstd;
most other ratios were effectively unchanged and two regressed. Astra had useful
wins on switch dispatch and regex, but three workloads regressed. Fable reduced
modeled work on **all ten**, with ratios from 1.015284× to 1.140774×.

The grader takes the smaller of the full geometric mean and the geometric mean
with the single best workload removed. This deliberately rewards broad gains,
not a large improvement confined to one benchmark.

| Distance measure | Genesys | Astra | Fable |
|---|---:|---:|---:|
| Full geometric-mean work ratio | 1.001601× | 1.006223× | 1.077648× |
| Scored ratio after outlier dampening | 0.999861× | 1.002023× | 1.070854× |
| Scored improvement relative to baseline | −0.0139% | +0.2023% | +7.0854% |
| Position relative to +0.5% credit boundary | 0.5139 pp below | 0.2977 pp below | 6.5854 pp above |
| Compile-work ratio, candidate/baseline | 1.000543× | 1.000102× | 0.983354× |
| Official reward /100 | 0 | 0 | 26.375 |

**Astra was close to earning some credit**, although not close to Fable's result:
its undampened mean exceeded the boundary, but dropping its best workload reduced
it below the threshold. Genesys's scored result was effectively the original
compiler's level. Neither was just one rounding unit behind Fable. Fable's scored
ratio exceeded Astra's by 6.8831 percentage points and Genesys's by 7.0993 points.
Those are differences in baseline-normalized work ratios, not score points or
measured wall-clock percentages.

Fable also was not close to full optimization credit. Full credit requires
**1.20×** scored work improvement. After the 1.005× deadband, its 1.070854× result
covered about **33.77% of the interval to that target**. The convex scoring curve
maps that to 26.375/100. It needed another 0.129146 in scored ratio to reach the
full-credit target. Its compile-work ratio was about 1.66% lower than baseline;
none of the three suffered a compile-work penalty.

There is some evidence for a difference in approach. The submitted file manifests
show Genesys changing 11 code-generation files and Astra five, while Fable changed
26, including register-allocation code as well as lowering and rewrite rules.
Astra's final self-report described targeted x86 improvements; Fable described
multiple rounds of spill handling, memory-operand folding, lowering, and register
allocation experiments. **These self-reports are supporting context, not grader
proof that a particular edit caused a particular speedup.** More changed files
alone do not imply better code; establishing causality would require controlled
reversion/ablation tests. The independently graded breadth of gains is the
stronger evidence that Fable's changes generalized better.

Fable also spent about 11 hours on this task, versus Genesys's 4h 06m and Astra's
24m, including setup and verification. That supports a difference in sustained
work, but does not prove that giving the other models more time would produce
the same result: all had the same maximum allowance and stopped before it.

### Evidence boundaries

The explanations above distinguish three different meanings of “failed”:
**incomplete recovery behavior** on the filesystem, **unsafe acceptance** in
Genesys's Lean checker, and **insufficient generalized improvement** on Cranelift.
They should not be flattened into the same claim of inability.

Case-level numbers come from each saved verifier's `results_default.json`,
`results_*.json`, `details.json`, and `reward_details.json`, reached through the
compact result records linked below. Astra's filesystem data uses the documented
reversal of Harbor's accidental redaction of the literal `1`. Scoring rules were
checked against the pinned upstream filesystem and Cranelift `compute_reward.py`
files, and Lean's recorded formula. These explain observed outcomes; they do not
establish a general psychological explanation of why a model stopped improving.

## Final interpretation

The extension exposed differences hidden by the earlier saturated P1–P3 results.
On these attempts, Genesys could implement substantial functionality but struggled
with the negative cases essential to proof-checker soundness and with producing
a compiler optimization that generalized to hidden workloads. Its zeros were
valid outcomes of completed runs, not API failures.

Fable showed the strongest results across this small suite: near-complete
filesystem correctness, a Lean checker close to Astra's, and the only qualifying
Cranelift speedup. Astra's result was mixed: excellent Lean checking but lower
filesystem correctness than Genesys and no qualifying Cranelift improvement.
The evidence supports these task-specific findings; it does not establish that
only a particular model class can solve the tasks, or predict Qwen/Kimi/GLM results.

Equal maximum budgets did not mean equal time spent. Trial wall times, including
setup and grading, were approximately:

| Task | Genesys | Astra | Fable |
|---|---:|---:|---:|
| Filesystem | 6h 59m | 1h 00m | 2h 18m |
| Lean | 1h 54m | 1h 21m | 1h 32m |
| Cranelift | 4h 06m | 24m | 11h 00m |

Fable spent far longer on Cranelift than the other two agents. That matters when
interpreting its better outcome: these runs measure the model and harness's
ability to use an available budget, not quality at matched elapsed time or cost.
No scored run exhausted its 20-hour agent allowance or recorded an exception.

## Conditions and limitations

- One scored attempt per model/task; no automatic retries of scored attempts.
- Same pinned upstream tasks and separate verifiers, with a 20-hour maximum agent
  budget per task. All three models finished before that limit.
- Filesystem uses 4 GB, Lean 8 GB, and Cranelift 32 GB for all three models. The
  Cranelift setting is a documented reduction from upstream's 128 GB requirement.
- Harnesses differ: Genesys House uses OpenCode 1.18.34; Astra uses Codex 0.156.0
  with high reasoning; Fable uses Claude Code 2.1.280. This compares these complete
  model/harness configurations, not model weights in isolation.
- Genesys's two zeroes are valid grader outcomes, with no recorded infrastructure
  exceptions. Fable's initial OAuth failure occurred before model usage and is
  archived separately; it is not a scored model failure.
- Astra's P4 artifact suffered Harbor's overbroad redaction of a boolean AUTH flag.
  Its recovered metrics match the untouched job aggregate exactly. Original files
  and recovery hashes are retained; no model rerun was performed.
- These three tasks do not establish a general frontier-model classification or
  prove that other models would fail. Repeated trials are needed for consistency.

## Evidence

Task definitions, image pins and hashes: [manifest](../benchmark-v4.1/frontier/manifest.json).
Methods: [runner documentation](../benchmark-v4.1/frontier/README.md).
Original Genesys detail: [initial report](success_report.v4_1.frontier.md).

- P4: flash filesystem: [genesys](../results-v4.1/frontier/crash-proof-flash-filesystem/genesys.json), [astra](../results-v4.1/frontier/crash-proof-flash-filesystem/astra.json), [fable](../results-v4.1/frontier/crash-proof-flash-filesystem/fable.json).
- P5: Lean checker: [genesys](../results-v4.1/frontier/lean-4-kernel-type-checker-in-pascal/genesys.json), [astra](../results-v4.1/frontier/lean-4-kernel-type-checker-in-pascal/astra.json), [fable](../results-v4.1/frontier/lean-4-kernel-type-checker-in-pascal/fable.json).
- P6: Cranelift optimization: [genesys](../results-v4.1/frontier/cranelift-codegen-opt/genesys.json), [astra](../results-v4.1/frontier/cranelift-codegen-opt/astra.json), [fable](../results-v4.1/frontier/cranelift-codegen-opt/fable.json).
