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
