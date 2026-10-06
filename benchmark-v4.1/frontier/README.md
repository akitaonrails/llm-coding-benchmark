# Reproducing v4.1 FrontierSWE P4–P6

**[All v4.1 tests, results and analysis](../README.md)** — the main entry point.

This guide reproduces the **local Genesys/Astra/Fable protocol**, not the published
FrontierSWE leaderboard. The original upstream tasks and graders are pinned in
[manifest.json](manifest.json) to revision
`da83f84f8fbcec3cbf0f2b17c98ebc811355c2df` of
[FrontierSWE v2](https://github.com/Proximal-Labs/frontier-swe-v2).
Upstream licenses and attribution remain in the fetched task directories.

## What you need

- Linux with working Docker Engine and the Docker Compose plugin. The tested
  environment uses Docker 29.7.2; other platforms have not been validated here.
- Git, uv, and Python 3.12 (uv can provision Python).
- At least 8 logical CPUs and enough available RAM for a 32 GiB task container
  plus the host and Docker overhead. Reserve substantial disk space for task
  images, compiler trees, and artifacts; this guide does not claim a measured
  minimum disk requirement.
- Network access to GitHub, the pinned public container registry, harness package
  installers, and the selected model provider. Model execution uses provider-only
  network allowlists; installation temporarily has public access.
- Access to the exact model IDs below. If your account cannot access an ID, the
  result is an infrastructure/access failure, not a model score. Do not silently
  substitute another model and describe it as the same comparison.

| Model | Model ID | Harness installed in container | Authentication |
|---|---|---|---|
| Genesys House | `lua/genesys-pi-house` | OpenCode 1.18.34 | `LUA_API_KEY` |
| Astra | `gpt-6-astra` | Codex 0.156.0, high reasoning, web search disabled | Codex subscription login |
| Fable | `claude-fable-5-1` | Claude Code 2.1.280 | Claude subscription login |

| Task | CPU | Local comparison RAM | Upstream RAM | Maximum agent time |
|---|---:|---:|---:|---:|
| P4: flash filesystem in Zig | 4 | 4 GiB | 4 GiB | 20 hours |
| P5: Lean kernel checker in Pascal | 4 | 8 GiB | 8 GiB | 20 hours |
| P6: Cranelift optimization | 8 | **32 GiB** | **128 GiB** | 20 hours |

The 32 GiB Cranelift limit is an intentional local deviation. Use it to compare
with this report. Omitting the queue's memory override requests the upstream
128 GiB limit instead; controls must also use that limit. Setup and verification
add wall time beyond the agent budget. Nine model attempts can take up to 180
agent-hours in a serial run; actual durations vary.

## Prepare an isolated checkout and Python environment

Run commands from the repository root. Use a separate checkout for replication
so the existing results and active benchmark workspaces remain intact.

```sh
git clone https://github.com/akitaonrails/llm-coding-benchmark.git
cd llm-coding-benchmark
git rev-parse HEAD  # record the harness revision alongside your results
uv venv --python 3.12 .venv-frontier
uv pip install --python .venv-frontier/bin/python 'harbor==0.23.0'
docker info >/dev/null
docker compose version
.venv-frontier/bin/python scripts/test_v41_frontier.py
```

Harbor is pinned to 0.23.0; its transitive Python dependencies are not locked by
this repository. Record your installed package versions for a reproducibility log:

```sh
uv pip freeze --python .venv-frontier/bin/python > frontier-python-packages.txt
```

The runner fetches the upstream repository into `tmp/frontier-swe-v2`, checks its
exact revision and clean working tree, and validates task/instruction hashes.
Docker pulls digest-pinned images. Do not edit that checkout during a run.

**Existing results are not a request to rerun.** The queue reuses completed
records and refuses to overwrite a scored attempt. If a fresh clone includes
published compact results, archive that result directory in the disposable clone
before starting your own run:

```sh
if [ -d results-v4.1/frontier ]; then
  mv results-v4.1/frontier "results-v4.1/frontier.published.$(date +%Y%m%d-%H%M%S)"
fi
```

Do not do this while a queue is running. Compact published records contain paths
to raw artifacts on the original machine; their presence does not mean those raw
artifacts are available in a clone. A new run must produce its own controls and
model records.

## Authenticate

For Genesys, export your own `LUA_API_KEY` into the launching shell using your
normal secret manager. The runner does not read a host OpenCode configuration.
Do not put credentials into this README, a command argument, or a tracked file.

For Astra and Fable, authenticate using the host CLIs:

```sh
codex login
claude auth login
```

The adapters use only `~/.codex/auth.json` and `~/.claude/.credentials.json`, copied
into isolated container locations. They do not copy host project instructions,
plugins, or memory. Astra requires subscription tokens and rejects an auth file
containing an API key. Fable requires nonempty OAuth credentials. The native
adapters do not intentionally fall back to paid API-key authentication.

Our native queue was launched without inherited provider overrides. Before
launching it, use a dedicated shell and clear provider/CLI override variables:

```sh
unset OPENAI_API_KEY OPENAI_BASE_URL ANTHROPIC_API_KEY ANTHROPIC_BASE_URL
unset ANTHROPIC_MODEL CLAUDE_CODE_OAUTH_TOKEN CODEX_AUTH_JSON_PATH CODEX_FORCE_AUTH_JSON
```

Also remove any custom `CLAUDE_*`, `CODEX_*`, `ANTHROPIC_*`, `OPENAI_*`, or `AWS_*`
overrides from that shell if you have configured them. Keep `LUA_API_KEY` only if
running Genesys. Authenticate close to launch time: a long queue can outlive a
subscription session, and empty/expired credentials stop the queue.

## Validate the configuration without model calls

```sh
.venv-frontier/bin/python scripts/run_v41_frontier.py --mode astra --task crash-proof-flash-filesystem --dry-run
.venv-frontier/bin/python scripts/run_v41_frontier.py --mode fable --task cranelift-codegen-opt --memory-mb 32768 --dry-run
```

Dry runs check the upstream checkout and construct the configuration. They do
**not** prove provider access, usable authentication, image availability, or that
a model can execute successfully. Genesys dry runs require `LUA_API_KEY` to be set.

## Run the same sequence

Use a persistent terminal such as tmux. The scripts run in the foreground; closing
a normal terminal can interrupt them. Do not launch two queues against the same
result directory.

```sh
# Complete Genesys P4, P5, P6, including reference and no-op controls.
.venv-frontier/bin/python scripts/run_v41_frontier_wave.py --models genesys --cranelift-memory-mb 32768

# Then all Astra tasks, followed by all Fable tasks; matching controls are reused.
.venv-frontier/bin/python scripts/run_v41_frontier_wave.py --models astra fable --cranelift-memory-mb 32768
```

To run only Fable on a new result directory:

```sh
.venv-frontier/bin/python scripts/run_v41_frontier_wave.py --models fable --cranelift-memory-mb 32768
```

Each selected model runs filesystem, Lean, then Cranelift. Each task has exactly
one scored attempt, with no automatic model retries. The queue validates oracle
and baseline records at the same revision and memory limit before model execution.
On a fresh directory it creates those controls automatically. P4/P5 oracles must
score 100; no-op baselines score zero. P6's unmodified compiler correctly scores
zero in both controls because it makes no optimization. This validates the
pipeline, not every possible grader edge case.

For one task manually, run controls first:

```sh
.venv-frontier/bin/python scripts/run_v41_frontier.py --mode oracle --task cranelift-codegen-opt --memory-mb 32768
.venv-frontier/bin/python scripts/run_v41_frontier.py --mode baseline --task cranelift-codegen-opt --memory-mb 32768
.venv-frontier/bin/python scripts/run_v41_frontier.py --mode fable --task cranelift-codegen-opt --memory-mb 32768
```

Other task IDs are `crash-proof-flash-filesystem` and
`lean-4-kernel-type-checker-in-pascal`; omit the memory override for those tasks.
Omitting `--task` in the individual runner selects all three, so do not use a
single 32 GiB override that way to reproduce the per-task profile.

## Observe progress and collect evidence

- Genesys-only queue state: `results-v4.1/frontier/queue.json`.
- Native/multiple-model queue state: `results-v4.1/frontier/anchors-queue.json`.
- Compact records: `results-v4.1/frontier/<task>/<model>.json`.
- Controls: `oracle.json` and `baseline.json` in each task directory.
- Raw Harbor trials: `results-v4.1/frontier/jobs/<job>/<trial>/`.
- Per-trial evidence: `result.json`, `verifier/reward.json`, detailed verifier
  files, agent transcripts, and submitted artifacts. Follow `job_dir` and
  `result_path` from the compact record to locate them.

`prepared` means the attempt has started but has no final result; it is not proof
that the model is currently active. Check container/process status and advancing
agent logs. A stopped queue is not a finished benchmark unless its state and
all selected records say `completed`.

Raw jobs are git-ignored because they are large and can contain sensitive agent
material. Preserve them locally for auditing; review/redact before sharing.
Keep model IDs, harness/dependency versions, upstream revision, image digests,
resource deviations, and both final and failed-attempt provenance with results.

The comparison report's updater is available as:

```sh
.venv-frontier/bin/python scripts/update_v41_frontier_comparison.py
```

**That updater is specific to the original analysis:** several explanations and
case-level tables are authored against the original nine attempts, even though
its top score table reads current records. It must not be used as an unattended
final analysis of a replication with different results. Use your new compact and
raw verifier records to write a fresh analysis and verify every narrative number.
`--watch` was used for the original queue and does not launch model work.

## Failure handling and interpretation

The queue stops on infrastructure errors. Check the recorded exception before
resuming. Missing rewards, authentication failures, and invalid verifier results
are not model zeroes. A valid grade after the 20-hour agent timeout still counts.
Never discard a scored model failure merely to get a better result.

If a launch failed **before inference**, preserve its record under a separate
failure filename and preserve its raw job, fix the infrastructure/authentication
problem, then rerun the queue. It reuses completed attempts. An existing failed
record is deliberately not retried automatically. If a `prepared` record remains
after its process died, investigate its raw trial before restarting; the queue
waits for that record rather than guessing that it is safe to duplicate it.

The historical run required fixes for installer/DNS setup, a native-adapter
method collision, Harbor treating a boolean AUTH flag as a secret, and Fable
subscription expiry. The adapters now avoid the boolean AUTH flag. The original
Astra filesystem result was recovered against the unaffected job aggregate;
original artifacts and recovery hashes remain saved. Do not generalize that
specific recovery procedure to arbitrary corrupted JSON.

The Docker sidecar uses the default bridge to avoid embedded-DNS/egress-filter
interaction on the tested host. The adapters check protected grader/solution
paths are inaccessible and GitHub is blocked before model execution. The agent
container does not mount this repository, peer results, or the oracle tree.

Scores are `100 × upstream reward`, not a universal pass percentage. The Lean
soundness gate and Cranelift performance threshold can assign zero to substantial
working implementations. Cranelift measures simulated weighted generated-code
work, not host wall-clock runtime. See the
[final comparison and gap analysis](../../docs/success_report.v4_1.frontier_comparison.md).

This is one attempt per model with different native harnesses, and a local P6
memory deviation. The published FrontierSWE leaderboard uses a different harness
and repeated trials. Reproducing this protocol does not guarantee identical
outputs, scores, runtime, or provider-side model behavior.
