# Confirmatory GPT-4o relationship experiment

This extension follows the first 992-observation forensic pilot. It asks whether Genesys resembles **specified GPT-4o snapshots and wrappers**, rather than treating a tokenizer match as model identity.

The companion [findings and cost analysis](../FINDINGS.md) covers pricing, model size and the separate gpt-oss distillation hypothesis. It does not modify this frozen experiment.

Read the frozen [protocol](PROTOCOL.md), [probe generator](panel.py), [runner](experiment.py), [analysis](analysis.py), and [tests](../tests/test_confirmatory.py). The old pilot and coding benchmark remain separate. No generated model code is executed.

## Current experiment

Run name: `gpt4o-confirmatory-20261009`. The complete pipeline runs without manual phase handoffs:

1. **Tokenization:** 1,024 unique generated strings from eight families, sent to GPT-4o and Genesys. Compare reported usage with locally computed `o200k_base` and `cl100k_base` counts. Estimate offsets on 256 strings, evaluate on 768 held-out strings.
2. **Reference discovery:** 48 algorithmic tasks × GPT-4o/Qwen/Llama × 3 repeats. Select at most eight families exhibiting repeatable, distinctive GPT-4o wrong answers. Genesys behavioral data is not available to the selector.
3. **Calibration:** 48 preference/perturbation prompts plus up to 16 fresh error prompts. Six observations per prompt per reference profile. GPT-4o repeat, alternate system prompt, draft/check wrapper and another snapshot are positive controls. Qwen, equally wrapped Qwen and Llama are alternative controls.
4. **Target holdout:** Genesys answers the selected panel only after reference selection and calibration are saved. Compare with a threshold only if the controls separated successfully.
5. **Temporal repeat:** repeat eight fixed sentinels for Genesys and three controls, no earlier than ten minutes after the first target observation. This checks short-term consistency, not multi-day identity stability.

Maximum: **6,824 physical calls**. The eight reference profiles use three underlying reference families; they are not eight independently trained controls. GPT-4o snapshots are `2024-08-06` and `2024-11-20`, through OpenRouter. Direct OpenAI preflight returned 429; it is preserved under `../runs/confirmatory-preflight/`. A snapshot name does not independently attest the aggregator's actual backend.

Genesys requires omission of temperature. All profiles therefore use provider-default sampling, with that confound recorded. In preflight it reported 129 completion tokens despite `max_tokens=1`; token-count requests may consume more output tokens than requested. Tokenizer-phase `truncated` is normally expected from the one-token request and does not invalidate input-token usage; behavioral truncation is excluded from distributions.

## Output/process supplement

The separately frozen [process-signals experiment](PROCESS_SIGNALS.md) adds 576 observations comparing final answers, brief verification sentences, explicit task-state traces and metadata across GPT-4o, verified GPT-4o, gpt-oss-120b and Genesys. It is queued to start after tokenization, without changing this experiment.

## Setup

Python 3.10+ on Linux/macOS, with tiktoken and its pinned dependencies. The repository environment already has these. For a clean reproduction:

```sh
python3 -m venv model-forensics/runs/confirmatory-venv
model-forensics/runs/confirmatory-venv/bin/pip install -r model-forensics/confirmatory/requirements.txt
model-forensics/runs/confirmatory-venv/bin/python -m unittest discover -s model-forensics/tests -v
```

Supply `LUA_API_KEY` and `OPENROUTER_API_KEY` through your secret manager/environment, never as CLI arguments or in a config file. The direct OpenAI key is not required for the frozen live run.

```sh
# Use a new run name; plan never overwrites a prior experiment.
python3 model-forensics/confirmatory/experiment.py plan my-confirmatory-session
python3 model-forensics/confirmatory/experiment.py run my-confirmatory-session
```

`plan` freezes generated prompts, expected answers, profile IDs, source hashes, tiktoken version and merge-table hashes, local token counts and settings. It performs no inference calls. Tiktoken may download its public encoding tables when first used. Source changes prevent resuming an old run; retain the frozen `source/` files and matching module layout for reproduction.

## Status and report

```sh
python3 model-forensics/confirmatory/experiment.py status gpt4o-confirmatory-20261009
tail -n 15 model-forensics/runs/gpt4o-confirmatory-20261009/runner.log
```

The detached run PID is in `runner.pid`. `status.json` includes a UTC heartbeat every ten completed observations and distinguishes waiting for temporal replication from active requests. A PID file alone is not proof of activity.

The runner creates intermediate tokenizer, selection and calibration JSON files as phases finish, then generates `report.md` and `report.json` after target evaluation and again after temporal replication. A partial report can be generated at any time:

```sh
python3 model-forensics/confirmatory/experiment.py report gpt4o-confirmatory-20261009
```

All output lives in ignored `model-forensics/runs/<name>/`. Share the report together with its manifest/JSON evidence after reviewing model-produced text. Expected-answer metadata is never sent to the evaluated models. Stored responses omit hidden reasoning content; they may include provider-reported reasoning-token usage.

## Failure handling and custody

Each phase has a sealed plan, per-observation start journal and sealed result file, and separately journaled physical calls. A two-call wrapper preserves both responses. Writes are atomic; a resumed request with an uncertain prior outcome is labeled `interrupted_unknown`, not replayed. Completed phases verify their artifact digests on reuse.

Eight workers allow at most two active observations per endpoint/model, with a minimum interval between physical-call starts. A 429 delays subsequent calls by 60 seconds. Three consecutive infrastructure failures per endpoint trip a circuit breaker; remaining scheduled observations for that endpoint are recorded as `circuit_open`. These are **not** successful collection, and inadequate coverage disables attribution. Individual failures do not silently vanish or get replaced by successful retries.

Hashes catch accidental alteration, not a malicious party rewriting all files and hashes. No independent timestamping or remote attestation is claimed. Public probes are held out from selection/analysis, not guaranteed absent from a provider's training or protected against a provider recognizing the experiment.

## Interpreting outcomes

The analysis explicitly tests whether known GPT-4o controls can be separated from the alternatives. If their intervals overlap, **the method is inconclusive**, even if Genesys looks close to GPT-4o. Passing calibration enables only:

- Consistent with the tested GPT-4o control envelope.
- Inconsistent with that tested envelope.
- Inconclusive because of overlap or missing coverage.

Neither result proves live API forwarding or excludes an untested orchestration layer, snapshot, model mixture or derivative. The output is not a posterior probability of ownership or origin. The draft/check wrapper is a controlled two-call intervention, not a recreation of the Rails benchmark or proof of long-horizon capability.
