#!/usr/bin/env python3
"""Render the comparison from saved results; optionally watch the active queue."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / 'results-v4.1/frontier'
REPORT = ROOT / 'docs/success_report.v4_1.frontier_comparison.md'
TASKS = [('crash-proof-flash-filesystem', 'P4: flash filesystem'),
         ('lean-4-kernel-type-checker-in-pascal', 'P5: Lean checker'),
         ('cranelift-codegen-opt', 'P6: Cranelift optimization')]


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def render():
    data = {(task, model): read(RESULTS / task / f'{model}.json')
            for task, _ in TASKS for model in ('genesys', 'astra', 'fable')}
    queue = read(RESULTS / 'anchors-queue.json')
    finished = all(data[t, 'fable'].get('status') == 'completed' for t, _ in TASKS)
    text = f'''# v4.1 FrontierSWE comparison: Genesys, Astra and Fable

Status: {'complete' if finished else 'partial — Fable results pending'}. Updated {datetime.now(timezone.utc).isoformat(timespec='seconds')}.

Genesys and Astra have completed all three tasks. Genesys scored higher on the
filesystem; Astra was substantially more reliable on the Lean proof checker.
Neither earned optimization credit on Cranelift. These results show a task-specific
difference, not a universal ranking of the models.

## Scores

Scores are 100 × the original grader reward, not interchangeable test-pass percentages.

| Task | Genesys House | Astra | Fable |
|---|---:|---:|---:|
'''
    for task, label in TASKS:
        values = []
        for model in ('genesys', 'astra', 'fable'):
            d = data[task, model]
            values.append(f"{d['score']:.3f}" if d.get('status') == 'completed'
                          else {'prepared': 'In progress', 'error': 'Infrastructure error',
                                'interrupted_or_error': 'Interrupted/error'}.get(d.get('status'), 'Pending'))
        text += f"| {label} | {' | '.join(values)} |\n"
    text += '''
## What the tests require, and how Genesys compared with Astra

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

### P5: Lean 4 kernel type checker in Pascal

Implement a checker that accepts valid Lean environments and rejects invalid ones.
The central requirement is soundness: a checker that accepts a bogus proof cannot
be trusted merely because it also accepts many valid proofs. The grader therefore
includes a hard gate for accepting closed proofs of False.

| Diagnostic | Genesys | Astra |
|---|---:|---:|
| Valid cases accepted | 473/476 | 476/476 |
| Invalid cases rejected | 96/131 | 130/131 |
| Soundness subset passed | 49/60 | 59/60 |
| Ungated diagnostic score /100 | 73.778 | 98.070 |
| False-proof gate | Failed | Passed |
| Official score /100 | 0 | 98.070 |

Both executed all 607 cases without hitting the suite deadline. Genesys incorrectly
accepted 35 invalid cases, compared with one for Astra. Genesys accepted 16 cases
containing a closed proof of False, triggering the mandatory zero. The soundness
subset and false-proof gate are distinct checks: Astra missed one soundness case
but still passed the false-proof gate.

The 0-versus-98 gap is magnified by the gate, but the underlying difference is real:
Astra rejected substantially more invalid inputs. Genesys built substantial working
functionality; its zero does not mean it did nothing. The ungated score is diagnostic
and must not replace its official zero.

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

## Fable progress and results

'''
    for task, label in TASKS:
        d = data[task, 'fable']
        text += f"- **{label}:** "
        if d.get('status') != 'completed':
            text += {'prepared': 'attempt in progress.', 'error': 'infrastructure error; no valid score.',
                     'interrupted_or_error': 'attempt interrupted; no valid score.'}.get(d.get('status'), 'queued.') + '\n'
            continue
        r = d['rewards']
        text += f"{d['score']:.3f}/100. "
        if task == TASKS[0][0]:
            text += f"Correctness {100*r['correctness']:.4f}%; performance component {r['performance']}; block-device gate {r['bd_gate']}."
        elif task == TASKS[1][0]:
            text += f"Accepted {r['accept_ok']}/{r['accept_total']} valid cases; rejected {r['reject_ok']}/{r['reject_total']} invalid cases; false-proof gate {r['false_proof_gate']}."
        else:
            text += f"Scored speedup {r.get('speedup')}; correctness {r.get('correctness')}; build success {r.get('build_ok')}."
        text += '\n'
    text += f"\nQueue state at this update: `{queue.get('status', 'unknown')}`"
    if queue.get('task'):
        text += f" — {queue.get('phase')}, {queue['task']}"
    text += '''.

## Conditions and limitations

- One scored attempt per model/task; no automatic retries of scored attempts.
- Same pinned upstream tasks and separate verifiers, with a 20-hour maximum agent
  budget per task. Genesys and Astra finished before that limit.
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

'''
    for task, label in TASKS:
        links = [f'[{model}](../results-v4.1/frontier/{task}/{model}.json)'
                 for model in ('genesys', 'astra', 'fable') if data[task, model]]
        text += f"- {label}: {', '.join(links)}.\n"
    if finished:
        text = text.replace(
            "Genesys and Astra have completed all three tasks. Genesys scored higher on the\nfilesystem; Astra was substantially more reliable on the Lean proof checker.\nNeither earned optimization credit on Cranelift. These results show a task-specific\ndifference, not a universal ranking of the models.",
            "All nine scored attempts are complete. **Fable achieved the highest score on\nall three tasks in this run.** Its strongest separation was the filesystem,\nwhere it approached full correctness, and Cranelift, where it was the only model\nto earn optimization credit. Astra and Fable both substantially outperformed\nGenesys on Lean's soundness requirements. Genesys nevertheless outscored Astra\non the filesystem, so the results do not form a uniform model hierarchy.")
        text = text.replace("## What the tests require, and how Genesys compared with Astra",
                            "## What the tests require, and how the three models compared")
        text = text.replace("Neither produced a broadly correct filesystem under this grader.",
            "Neither produced a broadly correct filesystem under this grader.\n\n"
            "Fable scored **99.267/100**, with **99.6993% correctness** and a performance\n"
            "component of 0.978305. Its correctness was above 99.4% on every geometry.\n"
            "This is a large improvement in the underlying checks, not a rounding effect\n"
            "or just a scoring gate. It still missed some checks, so the result does not\n"
            "establish perfect crash safety outside this suite.")
        text = text.replace("| Diagnostic | Genesys | Astra |\n|---|---:|---:|",
                            "| Diagnostic | Genesys | Astra | Fable |\n|---|---:|---:|---:|")
        for old, new in [
            ("| Valid cases accepted | 473/476 | 476/476 |", "| Valid cases accepted | 473/476 | 476/476 | 475/476 |"),
            ("| Invalid cases rejected | 96/131 | 130/131 |", "| Invalid cases rejected | 96/131 | 130/131 | 131/131 |"),
            ("| Soundness subset passed | 49/60 | 59/60 |", "| Soundness subset passed | 49/60 | 59/60 | 59/60 |"),
            ("| Ungated diagnostic score /100 | 73.778 | 98.070 |", "| Ungated diagnostic score /100 | 73.778 | 98.070 | 98.410 |"),
            ("| False-proof gate | Failed | Passed |", "| False-proof gate | Failed | Passed | Passed |"),
            ("| Official score /100 | 0 | 98.070 |", "| Official score /100 | 0 | 98.070 | 98.410 |")]:
            text = text.replace(old, new)
        text = text.replace("Both executed all 607 cases", "All three executed all 607 cases")
        text = text.replace("and must not replace its official zero.",
            "and must not replace its official zero.\n\n"
            "Fable rejected every invalid case but rejected one valid case; Astra accepted\n"
            "every valid case but also accepted one invalid case. Fable's slightly higher\n"
            "score follows the grader's weighting. This is a close result between those\n"
            "two models, unlike the much larger difference from Genesys. Neither checker\n"
            "is proven generally sound by a finite test suite.")
        text = text.replace("## Fable progress and results", "## Fable final results")
        text = text.replace("not API failures.\n\n## Fable final results",
            "not API failures.\n\n"
            "Fable changed 26 code-generation source files and achieved a scored speedup\n"
            "of **1.070854×**: about 7.1% greater throughput, or 6.6% less execution time\n"
            "at the same work. It built successfully, preserved correctness on all ten\n"
            "hidden workloads, and introduced no detected Wasm-suite regressions. Its\n"
            "**26.375/100** is an optimization reward, not a 26% correctness pass rate.\n\n"
            "## Fable final results")
        text = text.replace("## Conditions and limitations", """## Final interpretation

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

## Conditions and limitations""")
        text = text.replace("budget per task. Genesys and Astra finished before that limit.",
                            "budget per task. All three models finished before that limit.")
    if finished:
        text = text.replace(
            "of **1.070854×**: about 7.1% greater throughput, or 6.6% less execution time\nat the same work.",
            "of **1.070854×** in the grader's simulated work metric: about 6.62% less\nmodeled generated-code work, not a measured wall-clock speedup.")
        text = text.replace("## Final interpretation", (ROOT / "benchmark-v4.1/frontier/gap_analysis.md").read_text() + "\n## Final interpretation")
    temporary = REPORT.with_suffix('.md.tmp')
    temporary.write_text(text)
    temporary.replace(REPORT)
    return finished, queue.get('status')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    while True:
        finished, status = render()
        if not args.watch or finished or status == 'error':
            break
        time.sleep(30)


if __name__ == '__main__':
    main()
