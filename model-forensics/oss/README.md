# gpt-oss output forensics

This is the follow-up to the inconclusive GPT-4o calibration. It asks whether Genesys shares a **distinctive actual-output signature** with gpt-oss, beyond the shared tokenizer. Coding benchmarks remain paused and isolated.

Read the [locked protocol](PROTOCOL.md), [probe generator](oss_probes.py), [selection and analysis](oss_analysis.py), [runner](run.py) and [tests](../tests/test_oss.py). Overall context: [findings](../FINDINGS.md).

## What is new

- Exact copying outputs on rare and common Unicode strings; shared copying errors can be informative, identical token counts cannot.
- Algorithmic final answers and specific repeated wrong answers, instead of aggregate accuracy alone.
- Choice preferences with reversed presentation order, grouped so twins do not inflate evidence.
- Same gpt-oss-120B model through **Groq and DeepInfra BF16**, alternate system instructions and a two-call verification wrapper. This measures normal deployment variation before comparing Genesys.
- GLM 5.3 and Kimi K3 through Relace as negative controls; gpt-oss-20B through DeepInfra BF16 as an exploratory sibling comparison. This is primarily a 120B assay, not an independently calibrated exclusion test for 20B.
- A stop gate: at least eight distinctive reference-only blocks, then fresh validation responses must separate known positive and negative controls. No Genesys batch unless this succeeds.

Genesys rejected the `logprobs` parameter, so matched token-probability comparison is unavailable. Provider metadata and usage are saved as diagnostics, not ancestry evidence. Cerebras passed one 120B preflight but then returned HTTP 429; Groq 20B also returned 429. DeepInfra replacements passed before freezing. There is no fallback within the experiment.

## Reproduce

Use Python 3.10+ and install the pinned [requirements](../confirmatory/requirements.txt) in a virtual environment. Supply `OPENROUTER_API_KEY` and `LUA_API_KEY` through your environment; never put credentials in source or a shared command transcript.

From the repository root:

```sh
python -m unittest discover -s model-forensics/tests -q
python model-forensics/oss/run.py preflight oss-my-preflight
python model-forensics/oss/run.py freeze oss-my-run
python model-forensics/oss/run.py run oss-my-run
```

Run names must be new for preflight/freeze. Resume an interrupted frozen experiment with the same `run` command and unchanged source. Started calls without results become `interrupted_unknown`; they are not silently replayed. Do not launch two workers for the same run.

The run writes `model-forensics/runs/oss-my-run/`: frozen `manifest.json`, source snapshots, per-phase schedules/calls/records, `selection.json`, optional `calibration.json`, and final `report.md`/`report.json`. `status.json` updates every ten observations; the log gives the same count. All records include integrity hashes. Maximum 1,664 API calls, often far fewer because of the gate. Truncations and errors are reported as missing evidence.

## Current run

`oss-output-20261009`: reference discovery completed on October 9 at 15:13:29 UTC. Only one independent candidate block qualified (eight required), so collection stopped before validation or Genesys. This is no attribution/exclusion result. There were 562 usable responses, 17 HTTP errors, 6 truncations and 87 circuit-open skips; 20B was mostly unavailable. Results are in [local report](../runs/oss-output-20261009/report.md) and [live local status](../runs/oss-output-20261009/status.json). Raw runs are git-ignored and these links are local; share this README plus an exported run/report for reproducibility of the findings. The code and protocol suffice to run a new experiment, not to reproduce provider sampling exactly.

A validated match would support similarity to the tested deployment envelope. It would not prove training ancestry or ownership. A failed reference gate means these probes cannot discriminate adequately; it must not be presented as evidence excluding gpt-oss.
