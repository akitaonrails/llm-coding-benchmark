# Open-weight benchmark operating rules

Standing user directions consolidated on 2026-10-17. Read this before planning,
starting, recovering, or reporting an open-weight model batch. These rules govern
the model plus harness evaluation; they do not turn assisted runs into unassisted
results or waive the fixed hidden-test protocol.

## Preparation and admission

- Pin each official checkpoint to an immutable revision. Preserve model cards,
  licenses, runtime versions, launch settings, chat templates, reasoning mode,
  context/output limits and optimization evidence. Choose a suitable official
  quantization when needed; do not silently substitute a model or quantization.
- Check the official Hugging Face card even if the first probe exceeds 100 tok/s,
  so inexpensive supported optimizations are not overlooked. Check tool/reasoning
  parsers, prefix/KV caching, CUDA graphs, native kernels and supported speculation.
- Admission requires the fixed cold plus two warm decode probes and successful
  chat, streamed tool call, and tool-result round-trip checks. The threshold is
  **100 decoded tokens/sec**, measured by the median of the two warm probes, not
  prefill speed. Report actual benchmark latency separately.
- Below threshold, research official recipes and relevant upstream issues and
  try at most **three distinct configurations within 45 minutes**, including
  load/compilation. Stop tuning once admitted and the card review is complete.
  Do not reduce reasoning, context or output allowance merely to pass timing.
- A startup crash is not a slow model. Read the actual exception and classify it
  before another attempt. Repeating the same dependency failure with different
  batch sizes is not optimization. Check runtime/library compatibility, CUDA
  loader paths, cache compatibility, architecture support and parser support.
- Shared failures across models require a shared-environment investigation.
  Verify the specific repair before retrying. Current example: installing CUDA
  13 changed loader resolution; existing FlashInfer kernels still needed CUDA 12.
  `scripts/b300_repair_cuda12_loader.py` records before/after `ldd` evidence and
  tests loading the actual CUDA 12 library. Never fake ABI compatibility with a
  cross-major library symlink. Run the repair only in the intended B300 runtime.
- Check gated repository access before paid preparation. Preserve an access-blocked
  entry and advance if unavailable; never wait on the GPU for human approval.

## Minor issues, assistance and fair reporting

- Expect open-weight models to need some assistance. Do not abort a usable run
  for a small typo, missing import, ordinary setup/test mistake, or a harness
  assumption. A single nested Rails app is not the same as no Rails app.
- Fix harness/infrastructure bugs without charging them to model quality. Keep
  the original failure and repair evidence; resume from the proper boundary.
- Allow at most **two short, targeted nudges per model** for ordinary minor issues,
  within the existing cumulative time budget. The isolated reviewer may request
  a nudge; the controller records and appends it to the next normal sprint.
  Do not repair candidate code directly to improve its score.
- Never reveal hidden criteria, scores, planted-bug identities or solutions in
  a nudge. Preserve ordinary pre-injection defect provenance. Do not bypass an
  external review/security rejection by disguising or rerouting the same request.
- Record exact prompts, reasons, timing, outcomes and all prior attempts. Label
  results after a nudge **assisted**, including later sprints. Report whether the
  issue was fixed; do not present assisted outcomes as unassisted performance.
  Record assisted sprint time; do not claim a causal “extra time” estimate without
  an appropriate comparison. Reports must expose nudge counts and infrastructure
  interventions separately from model-quality findings.
- Required isolated grading/injection boundaries remain mandatory. Minor ordinary
  defects do not themselves block an otherwise valid boundary; missing boundary
  work, ambiguous injection parity and substantial failures need explicit handling.

## Prevent loops and bound spending

- Use a durable sequential supervisor, explicit success/failure transitions,
  stage deadlines and an independent pod-local billing watchdog. A dead controller
  must expire its lease and stop the actual paid pod. Merely killing inference is
  insufficient. The user must not need to keep asking for work to continue.
- Current B300 policy: **four hours cumulative sprint execution per model** across
  pauses/resumes. Setup, download and grading time are bounded separately and their
  costs recorded. Infrastructure recovery never resets accumulated sprint time.
- Detect repetitive activity, not merely silent output. Current B300 guard pauses
  five identical tool input/output repetitions or three cycles of length 2–4 when
  monitored source content has not changed for at least two minutes. Duplicate
  stream events are not new attempts; changed tool results are not identical.
- Independently pause after **20 minutes without monitored source-content change**.
  This is conservative: a legitimate long build can also trigger it. Record the
  observation as a resumable no-progress pause, not a proven reasoning failure.
  Log churn, timestamp touches and identical rewrites do not count as fixes.
  Source-change detection is a heuristic, not proof of useful semantic progress;
  the four-hour cap still bounds loops that evade it.
- A detected loop checkpoints and advances the queue. Nudges do not create an
  unlimited retry loop, reset a deadline, or keep the pod waiting. Recovery passes
  must be finite, explicitly authorized, and tied to a diagnosis or changed premise.
- Review the completed first pass before retries. The currently authorized recovery
  pass resumes both Qwen3.5 models at review 2, then retries the six CUDA-startup
  failures once under the repaired environment. Nemotron's externally rejected
  review remains separately blocked with partial injections preserved.

## Evidence, isolation, status and cleanup

- Run one model/sprint at a time. Shield reference answers, grading material,
  sibling results and the current model's review/nudge ledgers. Preserve isolated
  project Git history and all existing contamination safeguards.
- The RunPod is for GPU inference. Keep generated code, transcripts, results and
  resumable harness sessions locally; archive pod logs/settings before switching.
  Do not let a later model read a predecessor's generated workspace or results.
- Preserve paused workspaces, temporary execution state, sessions, volumes and
  grading/injection state. Only downloaded model weights may be deleted when space
  is needed, after recording immutable repository/revision provenance.
- On queue extensions, verify the live controller adopts the change. A JSON edit
  alone does not update an in-memory plan. Handoff only at a verified model stop
  boundary, keep billing protection active and preserve the exact continuation DAG.
- Report verified current stage, activity freshness, completed sprints, measured
  speed and failure category. A heartbeat is not evidence of model progress;
  “starting” may only be a supervisor transition. Show a todo/status snapshot after
  completed tasks. Avoid claiming a model failed when only serving or grading failed.
- Follow [CLEANUP.md](CLEANUP.md) after completed tasks. Remove only verified
  disposable owned resources; preserve evidence and all active/paused dependencies.
  Record exact removals and intentional retention. Never globally prune Docker.

See [the B300 runbook](runpod-b300-openweights-runbook.md) for pinned recipes,
incidents, deployment details and evidence paths.

## Additional authorized recovery pass (2026-10-18 continuation)

The user authorized a further finite resolution round after the current pass, ending when additional attempts cease to have a concrete new remedy. The controller schedules targeted MTP optimization for Qwen3.8-27B (same original weights), one ordinary route-syntax repair for GLM-4.7, and dependency-target compatibility resolution for Qwen3.5-122B and Swift. A blocked ordinary issue may use a dedicated repair phase capped at ten minutes and the original remaining sprint budget, counted against the same two-nudge limit. Original sprint outputs are never overwritten: repair transcripts/results live under repairs/. Required boundary verification must then pass before continuing. No new automatic round follows this list. ThinkingCap may join after verified repository approval. Externally rejected security operations and unchanged restarts of a substantially incomplete foundation are excluded.

## User correction: incomplete batch is not finished (2026-10-19)

This correction supersedes earlier queue-end shutdown instructions. The user authorizes continued attempts toward completing the comparison, including resuming partial models from their verified boundaries. Exhausting a finite queue does not complete the requested comparison. Report partial/review-blocked runs as unfinished immediately. Do not stop a paid pod merely because the queue is exhausted or an intermediate review fails; obtain explicit user approval before such a shutdown while required work remains. Do not silently substitute an emergency billing rule for this instruction. Before any new paid launch, reconcile both supervisor and pod watchdog behavior with this correction; the old unconditional-finally shutdown plan is not suitable. Never skip mandatory boundaries or repeat/reroute externally rejected security operations. Those require an authorized resolution of the review-service access block. Preserve source, partial injections, sessions, results, cumulative budgets and assistance records.

## Execution limits superseded by user (2026-10-19)

Remove elapsed-time caps for admitted model execution, including the inherited 90-minute phase cap. Retain >=100 decoded tok/s admission, bounded optimization/research, checkpointing and loop detection; loop detection pauses for diagnosis, not automatic final disqualification. Continue working models through all seven sprints. The pod must remain allocated on controller exit, lease expiry, queue exhaustion or review block until explicitly approved for shutdown. This knowingly retains billing while blocked and supersedes earlier fail-closed pod-stop defaults. Resolve infrastructure and candidate failures before declaring a model unworkable; document attempted remedies. Never bypass externally rejected security operations.

### Additional ordinary-defect recovery in this continuation

The controller interprets the latest user instruction to push admitted models toward full v4 completion as authorization for one additional targeted Command A Plus syntax/test recovery after two generic completion nudges. This is an explicit exception to the earlier two-nudge ceiling, not a claim that the user specified three. Preserve and label the third prompt and all later results assisted. The prompt may mention only ordinary observed syntax/test failures, never hidden injection targets or solutions. Mandatory independent boundaries remain unchanged.

## Valid negative application results (2026-10-19 user clarification)

A model that runs but produces a bad application yields a valid negative result. Annotate concrete defects, assistance and completed protocol scope; do not relabel it as an inference failure or invent a full score for incomplete v4. Focus remaining effort on other candidates instead of indefinitely repairing poor outputs. The user explicitly reaffirmed leaving the pod on.
