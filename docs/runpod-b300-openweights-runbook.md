# RunPod B300 pod — open-weights v4 benchmark runbook

Date: 2026-10-16. Purpose: serve the larger open-weights LLMs that do not fit on the home-lab
RTX 5090 (32 GB) or Strix Halo server (61 GB unified), and run the v4 benchmark against them
through the same opencode harness as every other model.

## Pod spec (recreate this)

| Item | Value |
|---|---|
| GPU | 1× NVIDIA B300 SXM6 AC — 275,040 MiB usable |
| Host | 344 vCPU, 4 TB RAM |
| Disk | 700 GB on `/` (container/overlay disk — **ephemeral**: wiped when the pod is terminated or rebuilt; re-download weights on restart) |
| `/workspace` | 50 GB local disk (unused for weights) |
| Base template | plain CUDA/Ubuntu (Python 3.12, **no docker**) — pip vLLM in a venv |
| Cost | ~$7.89–8.99/hr (Secure Cloud), billed per second |

## SSH quirks (important)

- RunPod's SSH proxy (`ssh.runpod.io`) **ignores the remote command** and drops you into an
  interactive root shell; it also refuses PTY-less sessions ("Your SSH client doesn't support PTY").
- `scripts/pod_exec.py` drives that shell with pexpect: waits for the prompt, disables terminal
  echo + bash bracketed-paste (long pasted lines are otherwise quoted, not executed), then runs
  the command and returns its exit code. Target is read from `/tmp/runpod.txt`.
- Usage: `python3 scripts/pod_exec.py --timeout 300 'df -h /'`

## On-pod layout

- `/root/venv/` — vLLM + flashinfer-python + huggingface_hub[hf_transfer]
- `/root/models/` — HF checkpoints (700 GB overlay; ~3 large models at a time)
- `/root/logs/setup.log` — setup + download log
- `/root/logs/vllm.log` — server log

## Serving recipe (per model)

**Connectivity (solved 2026-10-16, after three failed approaches):**
- RunPod's SSH proxy **blocks `direct-tcpip` channels** — `ssh -L`/`-R` forwards bind locally but
  reset on use. (`scripts/pod_tunnel.py` + `scripts/restart_tunnel.sh` kept for reference; dead end.)
- The HTTP proxy URL `https://<pod>-8000.proxy.runpod.net` returns 404 unless port 8000 is exposed
  in the pod's console networking settings.
- **Working path: `cloudflared` quick tunnel FROM the pod** (pods have full egress):
  `/root/cloudflared tunnel --url http://localhost:8000 --no-autoupdate` → prints a
  `https://<words>.trycloudflare.com` URL in `/root/logs/cf.log`. vLLM's `--api-key` still guards
  the endpoint. Update `runpod-vllm.options.baseURL` in the home opencode config to the URL.
- **Key discipline**: serve script must read `--api-key "$(cat /root/.vllm_key)"` with the file as
  source of truth. Writing the script through the PTY once expanded `$(...)` at creation time and
  embedded a mangled literal — always deliver scripts via `base64 -d` (`pod_exec` + heredoc b64).


```bash
export HF_HUB_ENABLE_HF_TRANSFER=1
/root/venv/bin/hf download <repo> --local-dir /root/models/<name>
# serve (NVFP4 models are Blackwell-only; B300 = sm_103)
nohup /root/venv/bin/vllm serve /root/models/<name> \
  --tool-call-parser glm47 --reasoning-parser glm45 --enable-auto-tool-choice \
  --max-model-len 131072 --port 8000 --api-key <random> \
  --served-model-name <short-name> > /root/logs/vllm.log 2>&1 &
```

Parser/flags per family: GLM-5.x → `glm47`/`glm45`; check the vLLM recipe page per model.

## Harness wiring (workstation side)

- Provider `runpod-vllm` in `~/.config/opencode/opencode.json` → `http://localhost:8100/v1`
  (SSH tunnel) or the RunPod `https://<pod>-8000.proxy.runpod.net` endpoint; auto-cloned into the
  isolated benchmark config by `scripts/benchmark/config.py`.
- Config entries live in `config/models_v2.json` (slugs `v2_*_oss`), billing self-hosted,
  `rates_per_m` all zero; pod wall-time is recorded in the report as infra cost.
- Run: `python scripts/run_v4_wave.py --sprint 01_foundation --models v2_<slug>` per sprint,
  standard shield + grade/inject boundaries, Tier set per the cloud sibling's score.

## Loader policy — best loader per model (documented 2026-10-16)

**vLLM (pip, `/root/venv`) for ALL campaign models.** Rationale per model:

| Model | Loader | Why this loader |
|---|---|---|
| GLM-5.3-Flash NVFP4 | vLLM | NVFP4 experts require vLLM's Blackwell FP4 stack (compressed-tensors → FlashInfer/cutlass); llama.cpp would need GGUF re-quant (fidelity loss); ollama has no NVFP4/glm5next support |
| Qwen3.5-397B-A17B NVFP4 | vLLM | modelopt FP4 checkpoint — vLLM `--quantization modelopt`; no other loader supports the GDN hybrid + NVFP4 combo |
| Qwen3.5-122B-A10B FP8 (conditional) | vLLM | official Qwen FP8 checkpoint is vLLM-first |
| DeepSeek-V4-Flash 0731 | vLLM | native mixed MXFP4/MXFP8 checkpoint; vLLM recipe exists; SGLang is the alternative but vLLM keeps one stack for all |
| Nemotron-3-Super NVFP4 | vLLM | NVIDIA's own cookbook is vLLM (+`super_v3` reasoning parser from the model repo) |
| Qwen3.8-27B BF16 | vLLM | full-fidelity HF checkpoint; vLLM serves BF16 natively; ollama would re-quantize |
| GLM-4.7-Flash BF16 | vLLM | BF16 full fidelity (the whole point: quant-vs-model A/B vs the local Q5) |
| Qwen3.8-Flash-Next NVFP4 | vLLM | modelopt FP4; explicitly requires recent vLLM |
| *(optional)* GLM-5.3 flagship 753B GGUF IQ1/IQ2 | **llama.cpp** | only loader that fits it in 275GB (GGUF); degradation-tier run, NOT comparable to cloud FP8 scores |

Fallback rule: if a model's official vLLM path fails irrecoverably on this pod (after the CUDA/JIT fixes), annotate DNF-infra and skip — never silently swap loaders mid-campaign, because loader is part of the tested kit (v5 design principle).

## Critical pod fix: CUDA 12.9 toolkit (sm_103a)

The stock image ships CUDA **12.8**, whose nvcc **cannot compile `compute_103a`** (B300) —
FlashInfer FP4 JIT and DeepGEMM both require ≥12.9. Fix (done 2026-10-16):

```bash
curl -fsSLo /root/cuda129.run https://developer.download.nvidia.com/compute/cuda/12.9.0/local_installers/cuda_12.9.0_575.51.03_linux.run
sh /root/cuda129.run --silent --toolkit --override --no-man-page   # -> /usr/local/cuda-12.9
ln -sfn /usr/local/cuda-12.9 /usr/local/cuda
apt-get install -y ninja-build   # FlashInfer JIT needs ninja on PATH (pip ninja alone is NOT enough — EngineCore subprocess PATH)
```

Keep torch's bundled 12.8 runtime untouched — only the toolkit/nvcc is 12.9 (same major, minor-forward compatible for JIT).

## Models considered (fit on 275 GB)

- **GLM-5.3-Flash NVFP4 (320B-A18B, 198 GB)** — RedHatAI quant of zai-org/GLM-5.3-Flash. Fits.
- Qwen3.5-122B, Qwen3.8-27B, GLM-4.7-Flash BF16, Hunyuan A13B — fit (see models_v2.json notes).
- Does NOT fit: GLM-5.3/5.2 flagship (744B+), DeepSeek-V4.1-Flash (~750B incl. engram tables),
  DeepSeek V4-Pro (1.6T), Kimi K3 (2.8T), MiniMax M3 official MXFP8 (444 GB), Nemotron-3-Ultra
  BF16. MiniMax-M3 community NVFP4 (259 GB) is too tight on 275 GB with KV headroom.

## Migrated pod continuation — 2026-10-17

The new SSH target comes from `/tmp/runpod.txt`. The migrated pod was empty: software,
weights and the old tunnel had to be recreated. This attempt pins vLLM **0.31.0**;
its installed code includes GLM5Next, Qwen4Exp and Muse Glimmer support. Runtime
preflight is still mandatory. `cohere-melody==0.15.2` supplies Command A+ parsing.
The authoritative configured pod rate is **$9.09/hour**.

User-approved additions, after the original queue:

| Model | Checkpoint | Weight size | Serving |
|---|---|---:|---|
| Muse Glimmer 30B | `meta-models/Muse-Glimmer-30B` BF16 | ~60 GB | `muse_glimmer` tools/reasoning |
| Command A+ | `CohereLabs/command-a-plus-05-2026-w4a4` | 132 GB | `cohere_command4` tools/reasoning |
| Ornith 1.5 35B-A3B | `ornith-ai/Ornith-1.5-35B-A3B` BF16 | ~70 GB | `qwen3_xml` tools, `qwen3` reasoning |

All retain 128K context, the isolated OpenCode harness, and the 7200-second cumulative
sprint guard. Qwen 122B remains conditional on the 397B run becoming DNF. Strata was
researched and excluded: no demonstrated benefit for this B300 batch. New models without
an existing benchmark tier will use the full Tier A injection set provisionally; this is
an experimental condition, not a claim of Tier A performance. Existing cloud/local sibling
tiers remain the comparison anchors.

The original GLM sprint is retained at
`results-v4/v2_glm_5_3_flash_oss.infra-tunnel-attempt1/`. Its actual exit was 1 (Cloudflare
HTTP 530 / tunnel 1033), despite the wrapper recording exit 0. The pre-correction ledger
is preserved in `results-v4/_b300_campaign/migration-20261017/ledger.before.json`.
Its elapsed sprint time remains in the cumulative guard and cost ledger.

The runner now reads the underlying sprint outcome, enforces conditional eligibility,
and stops verified descendants on timeout (OpenCode starts a separate process session).
The shield also hides older benchmark outputs and forensic material; a sentinel round-trip
check verified complete restoration. This closes an exposure under the existing
shield-all policy; it does not change prompts or scoring.

Reproducible support:
- `scripts/b300_remote.py`: secret-safe PTY transport, chunked file upload.
- `scripts/b300_serve.py`: remote serving process ownership and lifecycle.
- `scripts/b300_preflight.py <slug>`: authenticated chat, streamed tool call and tool-result round trip.
- `scripts/test_b300_campaign.py`: failure bookkeeping, conditional fallback and descendant cleanup checks.

The endpoint and credentials are updated only in ignored `config/opencode.benchmark.json`;
the user's home OpenCode configuration is untouched. Keep the actual credential out of
reports, command arguments and Git. The server reads `VLLM_API_KEY` from a protected file.

### Serving optimization restart (2026-10-17)

User authorized cancellation of the initial eager attempt, optimization, a clean
restart, and a measured comparison before running the remaining models.
The cancelled attempt is preserved as
`results-v4/v2_glm_5_3_flash_oss.eager-cancelled-attempt2`; it is not a model-quality
failure. Its execution time and cost remain in the campaign ledger.

Per-model performance validation is now required before the timed benchmark:

- Enable CUDA graphs and compilation; eager mode requires a documented compatibility exception.
- Use interactive latency mode for the single serial agent; do not increase concurrency merely to inflate aggregate throughput.
- Verify prefix caching, hybrid state caching where applicable, KV-cache format,
  chunked prefill, native attention and quantization kernels from runtime logs.
- Run `scripts/b300_perf_probe.py SLUG --label CONFIGURATION` to preserve identical
  cold/warm synthetic 256-token SSE probes, time to first token, usage and decode rate.
  These are infrastructure probes, not benchmark scores. Forced-length greedy
  generation applies only to probes; benchmark reasoning/sampling stays unchanged.
- Evaluate native MTP/speculative decoding only when checkpoint tensors and the
  installed backend support it. Retain it only after measured speed benefit and
  successful chat/streamed-tool-result preflight. Do not blindly enable unsupported flags.
- Preserve exact serving arguments and software/checkpoint provenance. Freeze the
  selected configuration for a clean benchmark attempt. Keep all prior artifacts.
- Do not shorten the 128K context or lower reasoning effort to improve timing.

The initial runtime had prefix caching enabled (30.3% reported hit rate), FP8 KV
cache, chunked prefill, FlashInfer sparse MLA and autotuned TRT-LLM NVFP4 MoE
kernels. However `--enforce-eager` explicitly disabled torch.compile and CUDA
graphs; MTP was off. Observed single-stream decode was approximately 10.4 tok/s,
GPU utilization 10%, memory-controller utilization 4%, power 209W/1100W.
Those utilization samples suggest headroom; they do not alone prove its cause.

User-added throughput guard (2026-10-17): minimum **50 decoded tokens/sec**, median
of two warm single-request 256-output-token probes after one cold probe. This is
an operational threshold, not a model capability score or a prediction of speed
at the full 128K context. Count reasoning output tokens too. Preserve TTFT and
all three measurements separately. Maximum **three serving configurations per
model (initial plus two retries)** and **45 minutes total tuning wall time**,
including loading/compilation, excluding initial weight download. Research
supported optimizations before retries. On exhaustion, preserve evidence, write
`THROUGHPUT_SKIP.md` and an explicitly infrastructure-only DNF marker, and move
on. This allows the existing 397B→122B fallback without calling slowness a
reasoning failure. `scripts/b300_tuning.py` records bounded rounds and creates
admission evidence; the campaign runner refuses missing/stale/sub-50 admission.

The user-authorized optimized restart receives a fresh 7200-second sprint guard.
Earlier attempt seconds remain under `prior_attempt_sprint_seconds` and remain
included in model-time cost; their original transcripts and ledgers are retained.

Operator sequence for each candidate (all local except inference):

```sh
python scripts/b300_tuning.py SLUG --begin LABEL
# Upload the selected config and start the recorded pod server.
python scripts/b300_tuning.py SLUG --measure
```

`--measure` supervises readiness, tool preflight and throughput probes against the
remaining tuning deadline, terminates its owned local subprocess tree on timeout,
and marks an infrastructure skip when attempts/time are exhausted. After a skip,
archive remote logs and stop/clean the owned server before loading the next model.
The standard campaign launch refuses a candidate without successful evidence for
its current configuration. A server restart is still needed to apply changed args.

Primary-source optimization candidates researched for upcoming models:

- Qwen3.5: [vLLM recipe](https://github.com/vllm-project/recipes/blob/main/Qwen/Qwen3.5.md), native MTP where the selected quantized checkpoint retains the head.
- Nemotron 3.5: [NVIDIA checkpoint recipe](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-NVFP4), native MTP and appropriate hybrid-state cache settings.
- Muse Glimmer: [vLLM recipe](https://recipes.vllm.ai/meta-models/Muse-Glimmer-30B), official DFlash assistant checkpoint as a bounded retry candidate, requiring revision-pinned download and tool correctness checks.
- Qwen3.8 Flash Next: [NVIDIA checkpoint recipe](https://huggingface.co/nvidia/Qwen3.8-Flash-Next-NVFP4), architecture-specific MTP and PLE placement. Do not replace the chosen weight precision silently.
- Command A+: [Cohere checkpoint recipe](https://huggingface.co/CohereLabs/command-a-plus-05-2026-w4a4), official single-GPU W4A4 kernels. Do not infer availability of a public draft model from hosted-serving claims.
- Ornith: [publisher checkpoint](https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B), preserve its modified template. Head existence alone does not establish useful speculative acceptance; measure before enabling.


<!-- b300-measured-optimizations:start -->
### Measured optimization outcomes

Rates are warm single-request decode measurements, not benchmark quality scores. Exact arguments, errors and raw evidence are linked below.

| Model | Configuration | Decode tok/s | Tool preflight | Outcome |
|---|---|---:|---|---|
| [v2_glm_5_3_flash_oss](../results-v4/_b300_campaign/tuning/v2_glm_5_3_flash_oss.json) | eager | 10.35 | Passed | Below throughput threshold |
| [v2_glm_5_3_flash_oss](../results-v4/_b300_campaign/tuning/v2_glm_5_3_flash_oss.json) | compiled-interactivity | 141.40 | Passed | Accepted |

A slower or incompatible attempt is retained; successful flags are not generalized to other architectures without measurement.
<!-- b300-measured-optimizations:end -->


#### GLM-5.3-Flash: accepted compiled configuration

On the same B300, checkpoint, 128K context, FP8 KV cache and fixed 3,473-token
prompt, removing `--enforce-eager` and adding `--performance-mode interactivity`
raised median warm decode from **10.35 to 141.40 tokens/sec (13.7×)**. Full and
piecewise CUDA graphs were captured (1.03 GiB), JIT warmup and autotuning completed,
and all three chat/streamed-tool-result checks passed. This measures the combined
configuration change; it does not isolate the contribution of each flag.

Explicit `--enable-prefix-caching --enable-chunked-prefill` flags document settings
that were already enabled in the eager baseline, so they do not explain the gain.
FP8 KV, FlashInfer sparse MLA and TRT-LLM NVFP4 MoE kernels were retained.
MTP was **not tested**: the second configuration already cleared the bounded
throughput gate. Its checkpoint head exists, but no speed/correctness claim is made.

The small probe is below this hybrid model's 8,576-token attention cache block.
Its cold/warm TTFT difference alone does **not** establish prefix-cache reuse;
cold JIT and other startup effects also contribute. The additional 11K-token
probe records actual prefix hit counters to check reuse across a complete block.
The 13.7× figure is a short-context synthetic decode result, not a guarantee of
the same improvement in end-to-end benchmark time or at 128K context.

Reusable serving args (environment authentication remains in the private key file):

```text
--tool-call-parser glm47 --reasoning-parser glm47 --enable-auto-tool-choice
--max-model-len 131072 --kv-cache-dtype fp8 --gpu-memory-utilization 0.92
--enable-prefix-caching --enable-chunked-prefill --performance-mode interactivity
```

Evidence: [tuning ledger](../results-v4/_b300_campaign/tuning/v2_glm_5_3_flash_oss.json),
[admission record](../results-v4/_b300_campaign/performance-validation/v2_glm_5_3_flash_oss.json).
Installed versions and pinned checkpoint revisions are retained in
`results-v4/_b300_campaign/migration-20261017/`, with raw probe responses and server logs.

Long-prompt confirmation: at **11,427 input tokens**, decode was 138.74 / 143.05 /
136.60 tokens/sec. Cold TTFT was 4.290s; repeat TTFT was 0.633s / 0.707s.
Prometheus counter differences showed exactly **8,576 prefix tokens reused** on
each repeat (0 on the cold request). This directly confirms hybrid prefix reuse.


### Throughput threshold revision: 100 tokens/sec (2026-10-17)

The user raised the admission minimum from 50 to **100 decoded tokens/sec**.
This supersedes the provisional 50-token threshold described above. The maximum
three configurations and 45-minute tuning limit remain unchanged. GLM's accepted
141.40 tokens/sec still qualifies, so its clean optimized run continues.
The two warm probe rates have the same arithmetic mean and median; report actual
coding-run decode throughput separately rather than treating a short synthetic
probe as a guarantee at long context. Preserve all previous measurements.


### Mandatory official model-card review (2026-10-17)

Even if the **first probe reaches 100 tok/s**, inspect the official Hugging Face
model card and record applicable low-cost performance recommendations, including
what was adopted or deferred and why. Do not skip this check just because the
throughput threshold passed. Below 100 tok/s, perform additional online research
and bounded optimization tests. Stop tuning after reaching 100 tok/s and completing
the model-card review and correctness checks. The three-configuration / 45-minute
limits remain unchanged. Do not interrupt an already accepted active benchmark
merely to pursue optional performance gains.


### Sprint guard revision: four hours (2026-10-17)

The latest user decision raises the cumulative sprint budget to **14,400 seconds
(four hours)** per clean model attempt, superseding the earlier two-hour guard
and the briefly proposed three-hour guard. Existing elapsed time is retained.
The active GLM sprint's supervisor was replaced without restarting its runner;
the new supervisor reads budget changes every five seconds. Downloads, calibration
and grading remain outside the sprint budget and inside recorded pod costs.
The 100 tok/s admission threshold, mandatory model-card review, three tuning
configurations and 45-minute tuning allowance remain unchanged.

A timeout means **did not complete within this workflow's programming time
budget**, not proof of universal real-world unusability. The v4 report does not
support the claim that all frontier baselines completed within one hour:
Astra 99.9 min; Fable 5 approximately 85 min; GPT 5.6 Sol xHigh 317 min.
Different harnesses and reasoning settings limit model-only timing comparisons.


### Resumable pauses and post-batch review (2026-10-17)

Time/throughput cutoffs now **pause** a model pending review after the entire
batch. Keep its generated code, workspace, temporary execution files, local
sessions, logs, grading/injection records and configuration. Do not clean these
as completed disposable runs. DNF remains a queue-control marker only.

`scripts/b300_pause.py` writes `PAUSED`, `RESUME.md` and a timestamped private
`pause-checkpoints/state.json`, including sprint results, workspace/Git state,
model configuration, pinned checkpoint manifest, time/cost and throughput ledgers,
and session export results. It exports available OpenCode sessions; failed exports
are explicitly recorded and the original local session store must be retained.
The current already-running supervisor has a separate checkpoint watcher; future
time/throughput cutoffs call the checkpoint writer directly.

**Weights-only exception:** if disk space is needed, downloaded model weights
may be deleted after recording and verifying the exact Hugging Face repository
and immutable revision for re-download. This exception does not authorize deleting
other temporary files or execution state. Archive remote logs/launch metadata
locally before switching models. GPU inference processes may stop; in-flight
generation and GPU KV memory are transient and are not resumable checkpoints.
Continuation uses the saved workspace/session, with prompt prefill rebuilt.

Before resuming, inspect the checkpoint and grading boundary. Preserve the original
interrupted sprint artifacts; the normal runner skips existing result files and
DNF markers, so do not blindly rerun it or remove those files. Record additional
authorized time separately and never repeat already-applied injections.


### Billing incident — paid execution blocked (2026-10-17)

The optimized GLM sprint ended after 53.77 minutes. The single-sprint supervisor
exited and no persistent orchestration process advanced to grading/sprint02. The
pod remained allocated and idle for approximately seven hours until the user
asked for status. This was an orchestration failure, not a model failure.

Paid execution is now disabled in campaign configuration and rejected by local
launchers. A preservation script copied runtime state to the persistent volume
(`/workspace/b300-resume-20261017`) before calling `runpodctl stop pod`. A subsequent
RunPod SSH response reports the container is not running. The remote backup has
not yet been independently read back; provider billing was not independently
queried. Persistent storage charges may remain. All benchmark code/results and
exported session evidence are local.

**Do not restart paid execution** until a persistent supervisor and independent
pod-stop watchdog are deployed and verified. Every exit needs a bounded handoff:
advance, retry within limits, pause and continue, or stop the paid pod. A watchdog
must outlive the supervisor and expire on loss of progress/control, even if the
assistant never receives another user turn. Merely having vLLM alive or polling
a process PID is insufficient evidence of useful work. Test harness crash, normal
completion, API/network errors, hangs, grader failure, supervisor death, timeouts,
and shutdown API failures. Do not represent these future safeguards as implemented
or tested yet. The current verified protection is the stopped pod and launch block.

Full incident evidence: `results-v4/_b300_campaign/migration-20261017/idle-billing-incident.json`.

### Resume recovery and billing guard implementation (2026-10-17)

The user explicitly authorized continuing the entire batch after the unwanted
stop. GLM sprint 01 remains eligible for sprint 02; do not repeat its completed
53.77 minutes or discard its workspace. Pod restart currently requires account
console access: the available SSH target cannot start a stopped container.

Local recovery components now exist:

- `scripts/b300_billing_watchdog.py`: independent pod-local lease expiry requests
  actual pod stop through `runpodctl`; missing/corrupt leases fail closed, stage
  deadlines cannot be extended by heartbeats, failed shutdown requests retry.
- `scripts/b300_supervisor.py`: bounded local stage execution, short remote lease
  renewal, explicit success/failure transitions, child-tree termination, exclusive
  lock, durable event/status logs, pod-stop request on exit. Plans reject cycles.
- `scripts/b300_boundary.py`: fresh isolated headless review/injection agent per
  v4 boundary, bounded to 15 minutes, structured verdict and evidence requirements.
- `scripts/b300_model_plan.py`: builds the seven-sprint graph for an already
  prepared/admitted model. GLM's saved plan starts at sprint 02. Failure archives
  and checkpoints the model; completion archives server evidence.

Verification: `python -m unittest discover -s scripts -p 'test_b300*.py'`
passes 22 tests, including real child failure/recovery and timeout termination.
These are LOCAL checks. No remote watchdog deployment, restored inference,
headless boundary execution, or end-to-end batch handoff has been claimed.
The current model plan ends by stopping the pod; cross-model preparation and
handoff still need integration before calling the whole batch unattended-ready.
Do not confuse a passing local test suite with a verified billing cutoff.

Next: restart existing pod; verify persistent backup; deploy watchdog with an
initial bounded restore lease and verify it is alive; restore runtime/tunnel;
revalidate GLM throughput (serving script fingerprint changed); archive the pause
marker under its checkpoint, retaining original budget; launch the resume plan
under an independent local process. Complete preparation/handoff for the remaining
queue with the same official-card, 100 tok/s, three-configuration/45-minute rules.

### New disposable pod and automatic batch handoff (2026-10-17)

User supplied a replacement SSH target; it is stored only in `/tmp/runpod.txt`.
Verified host `3d759a112ffc`, B300 275040 MiB, fresh 700G container disk. No old
runtime backup was present in its workspace. Local candidate code, sessions,
sprint results and review remained intact. Restoration installs the recorded
vLLM 0.31.0/CUDA 12.9 stack and downloads GLM at immutable revision
`18d55bfd5a2194887738da73753975c9d3842f46`. Dependencies are re-recorded; do not
assume an identical software stack merely because the vLLM version matches.

The pod-local watchdog was launched independently of SSH and its live process,
`runpodctl stop pod` command, pod ID and credential presence were verified.
The shutdown credential was not printed. Actual provider shutdown is not tested
by stopping the working replacement pod. Lease renewal fails if the watchdog
process disappears; local supervisor then requests pod stop. An expired lease
also triggers pod stop independently of the local process.

`b300_restore_monitor.py` bounds restoration, renews its lease, and archives the
setup log. `b300_resume_batch.py` waits for readiness, archives GLM's old pause
marker without resetting its 4h ledger, and execs the persistent supervisor.
`b300_batch_plan.py` produces the full 218-stage queue graph, with Qwen 122B
conditional after Qwen 397B. Sprint boundaries execute fresh isolated graders.
Failures checkpoint and archive the model, stop its owned inference server and
advance. Failure to stop the server aborts the queue and requests pod shutdown.
The final stage also requests pod shutdown; no conversation turn is needed to
advance between ordinary stages.

`b300_prepare_model.py` performs pinned downloads, private tunnel/config setup,
card-backed settings, readiness/tool tests and fixed throughput measurement.
New models have at most three configurations and 45 minutes of serving tuning;
GLM's partially completed attempt keeps its frozen accepted recipe and receives
fresh-pod revalidation. Native MTP is tried when the reviewed card supplies a
compatible recipe; other bounded trials adjust prefill batching, based on
https://docs.vllm.ai/en/latest/configuration/optimization/. Context, reasoning,
output budgets and model precision are not reduced. Runtime candidate results
and exact settings are saved to `new-pod-tuning-<slug>.json`.

`b300_weight_space.py` plans exact safetensors removals only when space is needed.
The plan and immutable checkpoint provenance are copied locally BEFORE removal.
Configs, caches, logs and resumable local code/session state are retained.

Evidence/status: `results-v4/_b300_campaign/supervisor/status.json`,
`events.ndjson`, per-stage logs, and `migration-20261017/restore-status.json`.
These paths may temporarily move with the benchmark's reference shield during a
sprint; the supervisor keeps its open stage log descriptor and writes stage
completion only after the runner restores the shield. Never recreate shielded
results/docs paths while a sprint is active.

Local verification now passes 23 tests, including real child-process failure,
stall termination, recovery transitions, lease expiry and early server-death
detection. Full GPU batch results and boundary-agent execution remain runtime
verification, not conclusions established by these unit tests.

Additional recovery verification and model-specific preparation:

- An initial setup upload failed before inference started. GLM was checkpointed,
  the failed attempt logs retained, and the same attempt resumed after transfer
  repair. No benchmark progress or cumulative budget was reset. Uploads now use
  one PTY connection per file, SHA-256 verification, atomic replacement, and at
  most three whole-file attempts. A lost acknowledgement cannot duplicate chunks.
- The restored primary runtime matches the recorded key versions: vLLM 0.31.0,
  torch 2.13.0, transformers 5.17.0, flashinfer 0.7.0.post1 and cohere-melody 0.15.2.
  Full freeze: `migration-20261017/new-pod-packages.txt`. Driver: 580.126.09.
- Nemotron's current official card requires vLLM 0.32 or pinned nightly commit
  `3f1bcfd82bb2e93fcd364fc7a5491718453a77e2`. The 0.32 final PyPI release was not
  available; the official commit wheel exists. Its separate environment is
  `/root/venv-nemotron032`, with CUDA 13.0, installed only at that model's stage.
  GLM and other default-runtime models keep `/root/venv` and CUDA 12.9. Runtime
  setup is bounded and counts against the 45-minute tuning window.
- Muse's official vLLM recipe now supports released vLLM >=0.28 (the older
  special-PR note is stale). A below-threshold baseline will try DFlash using
  the official assistant at revision `e8192f3a8f617f74be2ce220360c89ef4789f39f`,
  with 15 speculative tokens, before the final bounded tuning configuration.
  Sources: https://recipes.vllm.ai/meta-models/Muse-Glimmer-30B and
  https://huggingface.co/meta-models/Muse-Glimmer-30B-assistant.
- Own-model boundary reports and pause/checkpoint metadata are now shielded
  during each sprint, along with peer results and the rubric. Restoration
  conflicts preserve both copies and fail explicitly; they never overwrite or
  discard grading evidence. This closes an exposure introduced by storing the
  automatic reviewer output beside the candidate workspace.
- Verification: 27 local tests pass, including atomic-transfer retry behavior
  and own-model report shielding/restoration conflicts. GPU serving and full
  batch execution are validated separately through their actual runtime logs.

Cold-start monitoring was transferred without restarting inference PID 5058 when
its one-time kernel build approached the earlier readiness allowance. The adopted
admission helper checks the exact running command against the frozen recipe and
retains the original 45-minute tuning deadline. No sprint budget reset occurred.
Future cold starts use a longer readiness allowance inside the same overall cap.

For a live terminal view, run:

```sh
watch -n 2 cat /tmp/b300-batch-status.json
```

The status publisher refreshes every five seconds, verifies supervisor process
identity, and follows the event-log inode even while the benchmark moves its
reference material out of sight. It exits when that supervisor exits. The JSON
shows the current stage and elapsed stage time; preparation time is not sprint
execution time. `docs/b300-batch-status.md` and the campaign's `batch-summary.json`
are regenerated at model handoffs with evidence links, without inferred grades.


## Nex N2.5 Mini queue extension (2026-10-17)

User approved `nex-agi/Nex-N2.5-mini`, original BF16, immutable revision `87420286149d9cce9bd46cd335ef9bda33c37c1b`. Appended after Ornith through a pending supervisor extension; apply at the next model stop boundary only. The running supervisor loads its plan once, so merely editing JSON is insufficient. `b300_handoff.py` verifies supervisor PID/start ticks and stop-stage ownership, builds and validates the remaining DAG, renews the independent watchdog lease, replaces only the waiting old supervisor, then execs the new supervisor. No active inference or sprint is interrupted; all budgets remain in the existing ledger. A failed takeover leaves the remote lease to expire and stop billing. Handoff receipts and exact continuation plans are retained in campaign/supervisor.

Use shipped Qwen3.5 chat template, qwen3 reasoning/qwen3_coder tools, default adaptive medium reasoning, 128K context and 32K output. Official card deployment uses SGLang; vLLM compatibility remains subject to actual tool preflight. Original BF16 weights, 100 decoded tok/s gate, three configurations/45-minute tuning cap and four-hour cumulative sprint execution guard remain unchanged. Undefined template reasoning_effort follows the same branch as medium; no thinking disablement for speed. Model is registered now; queue merge and isolated provider registration happen at the stop boundary to avoid current preparation overwriting its in-memory config.

Swift 1.5 Qwen3.8-27B and ThinkingCap Qwen3.8-27B researched, not authorized additions yet. Both are reasoning-efficient derivatives useful for comparison against the base. Swift official card reports Terminal-Bench 2.1 69.21→72.13 and 16.3% mean token reduction; ThinkingCap reports 75.84→75.28 and 10.7% reasoning-token reduction. These are separate provider evaluations, not comparable head-to-head. Swift custom license; ThinkingCap gated with PolyForm Small Business plus personal-use grant. Both fit B300 at BF16 (~55GB); speed unmeasured. Sources: https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b and https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.8-27B .


### Swift and ThinkingCap approved additions

User approved both after Nex on 2026-10-17. Extension order: Nex N2.5 Mini → Swift 1.5 Qwen3.8-27B → ThinkingCap Qwen3.8-27B (14 total queue entries). Swift pinned `b4c84d42903a8646b25857eb2827288d92ed85a4`; ThinkingCap pinned `7891e03dbda2e9b63a5b9610f20e83ea441f8e2c`. Original BF16 (~56GB each), bundled thinking defaults, standard 128K context/32K output. Official qwen3 reasoning parser, qwen3_coder tools for Swift and qwen3_xml for ThinkingCap. The official MTP3 recipes are picked up by the existing bounded optimization routine if baseline is below 100 tok/s; no lowering reasoning or context. Both model cards archived.

ThinkingCap is access-blocked BEFORE any weights or GPU execution: local authenticated pinned config returned HTTP 403, pod had no HF credential. `results-v4/v2_thinkingcap_3_8_27b_oss/PAUSED` makes the existing gate skip immediately. Resume procedure and evidence preserved in that directory. No quality conclusion applies. Swift download metadata/config accessible without authentication. Pending extension expanded atomically; validated 140-stage continuation from next model through all three additions, retaining all bounded success/failure paths.


## Standing open-weight policy and recovery (2026-10-17)

Read [OPEN_WEIGHT_BENCHMARK_POLICY.md](OPEN_WEIGHT_BENCHMARK_POLICY.md) before future runs. It consolidates the user-approved admission, diagnosis, assistance, loop prevention, billing, isolation, recovery and cleanup rules.

Six first-pass startup failures share one cause: cached FlashInfer binaries cannot resolve libcudart.so.12 after CUDA13 installation. The CUDA12 library was present, not deleted. The scoped loader repair registered `/usr/local/cuda-12.9/lib64` in `/etc/ld.so.conf.d/b300-cuda12-runtime.conf`, refreshed ldconfig and verified all five cached libraries have no unresolved dependencies plus successful ctypes loading. See `results-v4/_b300_campaign/migration-20261017/cuda12-loader-repair.json`. Exact mechanism of changed loader precedence is an inference; pre/post library resolution is directly verified.

Both Qwen3.5 runs were false-aborted because their app was one directory below the workspace root. Updated the presence check to accept a single real immediate-child Rails app, excluding symlinks/vendor/temp dependencies and ambiguous multiple apps. No candidate source was repaired. Recovery starts with review02, then sprint03. Previously executed sprints and cumulative ledger are retained.

The finite recovery DAG (194 stages including remaining first-pass entries) is armed for takeover at the next stop boundary and runs after remaining first-pass models. It retries both Qwens and six CUDA startup failures. Old control markers/tuning records are archived before retry; no source/results/session deletion or budget reset. Nemotron stopped because the external reviewer rejected an injection operation, not because the model failed. That operation is not automatically retried or rerouted.

Minor nudges: isolated boundary reviewer may record one ordinary pre-injection issue in assistance.json; at most two prompts per model are appended to the next standard sprint. Exact prompts/source/timing are recorded under the shielded assistance directory; sprint results label assisted_run, and batch reports expose counts. No hidden answers or planted-bug fixes may be included. All costs stay within the existing sprint guard. Repetitive tool input/output cycles and 20-minute absence of monitored source-content changes trigger a preserved pause and next-model advancement. The no-progress rule is conservative, not a conclusive quality diagnosis.


### Second targeted recovery authorization

After first recovery, the user requested all feasible runs followed by further resolution until diminishing returns. Found Qwen3.8-27B now starts but delivers ~92 tok/s: original optimization regex missed the official linked vLLM recipe MTP option. Archived https://recipes.vllm.ai/Qwen/Qwen3.8-27B and scheduled native MTP3, then1/5 only if necessary, within the existing three-config/45min cap. No precision/context/reasoning reduction.

GLM-4.7 reviewer requested only config/routes.rb compilation repair. A dedicated at-most-ten-minute model repair is recorded as assisted and charged to the cumulative sprint ledger, followed by re-verification of existing injections at boundary03. Existing sprint03 result/transcript remain untouched. Qwen122 and Swift repeat boundary02 using only the existing catalog equivalent-target rule, not a silently altered denominator or incompatible forced pin. Already planted items must not be duplicated.

New controller supports handoff from a recovery-stage stop while preserving remaining work. The final bounded continuation contains no recursive retry or next-round transition; supervisor requests pod stop at its end. Recovery guidance and exact preview/DAG retained in campaign/supervisor and recovery-20261017.json. Nemotron, Qwen397, Qwen Flash-Next and Muse hit external review-service security rejections; those operations are not automatically retried or rerouted. Nex had a substantially incomplete foundation with no small known remedy; no unchanged restart scheduled.

ThinkingCap access recheck now succeeds: local and pod authenticated pinned config HTTP200. Pod HF_TOKEN_PATH is `/workspace/.cache/huggingface/token`, not root home default; securely provisioned there, permission0600. No credential value printed. Temporary root-home copy and access-probe script removed. Fifth entry added to final finite recovery pass; prior blocked-access evidence/marker retained until resume-stage archival. 39 B300 tests pass, including recovery-to-recovery continuation, ten-minute repair ledger accounting and original-result preservation.


## Fresh pod continuation (2026-10-18)

User supplied a replacement SSH endpoint and authorized continuation to the end of the finite queue. Fresh B300 pod, 700GB root filesystem. Restored the same key versions (vLLM 0.31.0, torch 2.13.0, transformers 5.17.0, FlashInfer 0.7.0.post1, cohere-melody 0.15.2), CUDA 12.9 and the verified CUDA12 loader registration. Independent pod-local billing watchdog was installed before restoration; the durable supervisor renews its short lease throughout bounded setup and model execution. Credentials were provisioned privately at the actual HF_TOKEN_PATH; the duplicate root-home token and downloaded CUDA installer were removed after setup.

Ornith had no completed sprint01 result when the former supervisor exited. Its original transcript was moved intact to pause-checkpoints/migration-20261018-interrupted-sprint01, while the generated project remains in place. Charged 3381.69 seconds conservatively from prior stage start to controller exit to the original four-hour cumulative ledger before continuing with a fresh harness session. This is an infrastructure-interrupted continuation, not an independent clean run. New admission: 316.65 decoded tok/s, all tool preflights passed. Fresh-pod loading/compilation took 643 seconds, with 61 seconds download recorded separately.

Continuation plan: Ornith, then Qwen3.8-27B MTP, GLM4.7 bounded repair, Qwen3.5-122B compatible boundary, Swift compatible boundary, and ThinkingCap. No automatic additional retry pass. Exact DAG: campaign/supervisor/migration-20261018-plan.json. Setup, runtime, cleanup and recovery evidence: campaign/migration-20261018/. Final outcomes must be read from current events/results, not this launch record.

Qwen3.8-27B final targeted retry passed with native MTP3 plus language-model-only serving: 194.96 decoded tok/s (warm probes 195.21/194.71), versus earlier 92.30 without native MTP. Same BF16 checkpoint, context and reasoning settings; chat/streamed-tool/tool-result preflight passed. Stopped tuning after the first passing configuration and began sprint01. Observed ~2.11x improvement spans pods, so do not call it a same-pod controlled causal estimate. Exact arguments/evidence: campaign/migration-20261018/qwen27-mtp-success.json.


## 2026-10-19 Qwen tool-parser repair

During the Nex foundation continuation on the empty-volume replacement pod, valid tool operations were repeatedly returned as unfinished JSON (for example, a final `offset` field with no completed value). The requests were far below the output-token ceiling. vLLM 0.31.0 retains the Qwen converter behavior described in [upstream issue 57699](https://github.com/vllm-project/vllm/issues/57699): when a function closes without a final `</parameter>`, the non-streaming conversion drops the argument and the streaming conversion cannot finish JSON. The exact raw generations from the benchmark were not captured, so the reproduction establishes an installed infrastructure defect and a matching symptom, not proof that it caused every malformed benchmark call.

`scripts/b300_qwen_parser_probe.py` reproduces this without model inference or executing tools. Its 24-case matrix covers typed/untyped arguments, four chunk widths, well-formed calls, a function-closed trailing parameter, and genuinely truncated calls. The scoped fix in `scripts/b300_patch_qwen_parser.py` passes the function-close marker through the parser transition and completes a trailing parameter only upon that explicit marker. It deliberately does not complete a call cut off before the function closes. This is narrower than blindly accepting all unfinished argument buffers. All 24 post-fix checks passed on the pod; the original parser source, hashes and before/after fixtures are preserved under `results-v4/_b300_campaign/migration-20261019-empty/parser-investigation/`.

Model preparation now deploys this repair before launching a server, including after future empty-volume migrations. The helper refuses unexpected source shapes and preserves the original file. A running server needs a restart to load the repair. Revalidate speed and streamed tool round trips afterward. Nex is queued for an explicitly labeled corrected-parser continuation; previous outputs remain intact. This intervention does not alter weights, context length, reasoning mode or output limit.
