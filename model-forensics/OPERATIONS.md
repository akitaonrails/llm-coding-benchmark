# First forensic collection: operational notes

Collection began 2026-10-08 UTC. This is exploratory API evidence, not a provenance verdict.

## Benchmark suspension

At the user's request, the v4.1 Genesys attempt #3 process group was SIGSTOPed and its active P4 Docker container was paused. The record is `../results-v4.1/genesys-repeat3-pause.json`. P1–P3 completed results remain preserved; P5–P6 have not started. The P4 workspace was not deleted or restarted.

Clock-based budgets continue advancing during suspension. Before resuming, inspect Harbor's deadlines and record the interruption in any eventual result. Do not silently compare suspended wall-clock duration to uninterrupted trials. No automatic benchmark resume is scheduled.

## Compatibility observations

- `runs/genesys-compat-20261008`: first scheduled request returned HTTP 400. A separate diagnostic reported `unsupported_parameter`: Genesys House uses fixed sampling and requires temperature to be omitted. This was a request-compatibility failure, not reasoning failure. Original observation retained.
- `runs/genesys-fixed-compat-20261008`: new manifest with `temperature: null`; first four requests succeeded. This is a separate pilot, not a repaired replacement for the failed one.
- `runs/panel-pilot-20261009`: eight endpoints, 124 requests each, 992 planned observations. The session label is only an identifier; manifest/response timestamps record actual UTC dates. Sampling is provider-default/fixed, not controlled equal temperature.
- Initial panel batch: six `ok`, one Kimi `truncated`, one DeepSeek `invalid_response`. A separate DeepSeek diagnostic succeeded. The invalid observation is preserved; no successful replacement was inserted. Diagnostic calls are excluded from fingerprint analysis.

## Reference panel

Genesys House directly; GPT-4o, gpt-oss-120b, Qwen3 Max, Kimi K3, GLM 5.3, DeepSeek Chat and Llama 3.3 70B through OpenRouter. Current listed model IDs and supported parameter declarations were captured in `reference-catalog.json` beside the panel manifest. Aggregator routing and mutable aliases are limitations; these are candidates, not independently verified lineage controls.

## Inspect progress

From the repository root:

```sh
python3 model-forensics/kit.py status panel-pilot-20261009
tail -n 15 model-forensics/runs/panel-pilot-20261009/collector.log
```

The detached collector PID is recorded in `collector.pid`. HTTP, transport and malformed-response failures pause collection as designed. Diagnose such a pause, then explicitly continue with `collect panel-pilot-20261009`; it skips already-recorded observations and does not retry failed ones. Do not assume a PID file means a process is still alive.

Once collection stops or completes:

```sh
python3 model-forensics/kit.py report panel-pilot-20261009
```

Pilot output is for compatibility, missingness and protocol assessment. Two observations per prompt do not support model attribution. Decide on any needed new protocol version before full-session collection; retain every pilot and failure.

## Rate-limit pacing amendment

The initial collector stopped at observation 43 on a DeepSeek HTTP 429. Collection resumed under `supervise.py`: serial requests with a 3-second gap, a 60-second cooldown after a recorded 429, and no replay of failed observations. Three consecutive 429s or any other infrastructure/schema error stop the supervisor for diagnosis. The supervisor generates a report when the frozen schedule completes. `collector.pid` now identifies the supervisor; short-lived collector children perform one scheduled request each. Request payloads and the frozen experiment manifest are unchanged.

## Isolated malformed-response continuation

At observation 67 the supervisor stopped on another DeepSeek invalid response (HTTP 200 without a usable response schema). The collector did not retain its raw body, so its exact upstream cause is unresolved. Supervisor policy was amended: isolated invalid responses remain in the dataset and collection continues without replay; three consecutive invalid responses from the same endpoint, even with other endpoints interleaved, stop collection. Other infrastructure/error stops are unchanged. Frozen prompts, payloads and analysis code are unchanged.

## Confirmatory experiment started

The pilot completed all 992 scheduled observations (933 ok, 41 truncated, 13 HTTP errors and 5 invalid responses). Genesys had 124/124 ok. The new `gpt4o-confirmatory-20261009` experiment runs through `confirmatory/experiment.py`; see [its README](confirmatory/README.md) for phase counts, status commands and interpretation. Its runner proceeds automatically through reference-only calibration before target behavioral evaluation. The coding benchmark remains suspended.

## Output/process supplement queued

`process-signals-20261009` is planned and its worker is waiting for the main tokenizer phase to complete. It adds 576 observations (at most 720 calls) across actual answers, verification sentences and explicit state traces, including gpt-oss-120b. It uses its own manifest and results. See [process-signals instructions](confirmatory/PROCESS_SIGNALS.md).


## GPT-4o complete; gpt-oss output investigation active

The main GPT-4o experiment finished at 2026-10-09T14:45:21Z. Its calibration controls overlap; no formal classification is justified. The mixed GPT-4o process supplement was stopped at the user's pivot, preserving 191 completed observations and any started-call journals. Neither worker remains intentionally running.

`oss-output-20261009` now runs independently with `oss/run.py`. Its `runner.pid`, `runner.log`, and `status.json` are under `model-forensics/runs/oss-output-20261009/`. A detached PID alone is not proof of liveness: check process state and record timestamps. Reference discovery is 672 observations; further validation and Genesys collection depend on the locked gate. See [protocol and commands](oss/README.md). Automated tests: 39 passed before launch. All five final provider compatibility checks returned `ok` and the requested A; selected routes are frozen, with no fallback. Original failed preflights remain preserved.

The v4.1 Genesys third run remains paused. No benchmark result was changed by this experiment.

### Discovery infrastructure update

The OSS 20B DeepInfra route accumulated repeated HTTP 429 failures and its circuit opened. Remaining observations on that route are recorded as `circuit_open` without making requests. This is infrastructure missingness, not a 20B reasoning failure. The 120B and negative-control references continue; 20B is exploratory and is not required by the frozen 120B gate. No provider was silently replaced after freezing and no failed observation was replayed. The per-profile snapshot is saved as `runs/oss-output-20261009/progress-snapshot.json`.

### gpt-oss run completed

At 2026-10-09T15:13:29Z all 672 discovery observations were resolved. Only one block qualified; the locked minimum was eight. The worker exited normally without validation or Genesys collection. See the final report and updated FINDINGS.md. No automatic additional collection is pending. The benchmark remains paused.
