# v5 design: useful comparisons of model+harness kits

Date: 2026-10-09. Status: proposal, not implemented or preregistered. Budgets, sample sizes and thresholds below are design defaults to validate on development tasks before freezing the scored release. No existing scores are overwritten. The original benchmark remains paused; forensic collection is independent.

## 1. Questions and claims

Primary questions:

1. What correct work can each kit complete unattended?
2. How much of its failure rate disappears with at most two generic, nontechnical nudges?
3. Which failures persist despite verified tool compatibility and sufficient opportunity to act?
4. How does success change with task difficulty, accumulated history and resource budget?
5. Which kit minimizes cost and supervision for a stated workload and reliability target?

Working hypothesis: some lower-ranked kits already possess enough coding capability for the tasks but lose runs through premature stopping, context loss or poor recovery. The competing hypothesis is that substantive implementation/reasoning gaps remain after those execution problems are controlled. Both may hold on different tasks.

Do not claim pure-model intelligence, training ancestry, or universal convergence. A deployment is a bundle of weights, post-training, prompts, reasoning settings, provider behavior, tools, context policy, environment and resource allocation. Fixing an adapter defect is different from improving a model's action selection. Agentic skill can itself be learned in the weights.

## 2. Evidence from this repository that motivates v5

- v4's evolving Rails application and successive teammate changes are realistic and worth preserving. Its delayed vulnerability reveal already distinguishes detection from prompted repair, but normal feature execution needs a similarly explicit assistance policy. [v4 design](../benchmark-v4/README.md)
- Genesys's original run, Astra and Fable all scored 100 on v4.1 P1–P3. Passing a finite suite does not establish equal capability outside its ceiling. [v4.1 results](../benchmark-v4.1/README.md)
- On Lean, Genesys's official zero included a false-proof soundness failure; its ungated diagnostic score was 73.7777, versus Astra's 98.0695. A zero is meaningful for trust while being a poor description of all completed work. Preserve both views. [case-level analysis](../docs/success_report.v4_1.frontier_comparison.md)
- Different native harnesses were used for Genesys, Astra and Fable. That is valid for kit comparisons but insufficient to assign differences solely to weights.
- Cranelift used a local 32 GiB limit versus upstream 128 GiB. Resource constraints belong in the tested configuration, not in a footnote after ranking.
- The current v4.1 grader rebuilds from trusted harness/grader code and imports submitted source. Preserve this separation; model-authored tests are useful evidence but cannot determine the official score. [grader](../scripts/run_v41_grade.py)

## 3. Experimental structure

### Primary: native-kit comparison

Use each kit's documented, compatible production configuration, pinned before scored runs. Publish model identifier/snapshot when available, provider, CLI version, agent instructions, reasoning setting, context/compaction policy, permitted tools, built-in continuation policy, concurrency, network policy and resource limits. Record changes in hosted endpoints that cannot be frozen.

Apply the same task contracts, starting repositories, external budgets, intervention policy and grader to all kits. Built-in autonomous verification or recovery is part of the kit and is allowed when declared. Additional benchmark-controller messages count as interventions. This answers the user's practical model+harness question.

### Diagnostic: harness crossover

On a preregistered subset, run at least two models through a common compatible harness and at least one model through two harnesses, where provider access permits. This yields within-model and within-harness comparisons rather than treating 'same wrapper' as proof of fairness. Freeze prompts/settings per cell and report unavoidable differences.

Crossover is a separate table. Do not force a proprietary native kit through an incompatible adapter merely to fill the matrix. Missing cells remain missing, limiting causal conclusions. Allocate an equal development tuning allowance per kit and disclose tuning; no tuning on scored tasks.

### Separate task difficulty from session length

Use a 2×2 development grid: short/easier, short/harder, long/easier, long/harder. Measure realized human effort on a subset; initial labels are editorial until validated. Long/easier tasks must involve accumulated requirements and meaningful state, not artificial transcript padding. Short/harder tasks give all needed information in a compact repository and require a real diagnosis or invariant.

Do not label wall-clock model runtime a human task horizon. A statistically estimated horizon requires human timing data and a substantially larger task bank than the pilot.

## 4. Concrete task bank

Start with six families, each with at least two independently authored instances for the first scored candidate release (12 instances). Two instances are a minimum breadth check, not enough for precise general rankings. Keep development and scored instances separate. The pilot uses six development instances, one per family. Expand based on precision and coverage, not on which model wins.

| Family | Concrete task and why it discriminates | Objective acceptance and diagnostic dimensions |
|---|---|---|
| F1: multi-tenant change in a real application | Add resumable background CSV export to an existing Rails app. Authorization must still hold if membership is revoked after enqueue; jobs may retry; downloads may race with deletion. Tests integration of authorization, asynchronous state and idempotency beyond CRUD. | Hidden request/job/browser tests; cross-tenant and revoked-access attempts; exactly-once externally visible effects; valid-user availability; existing flows preserved. A deny-everything implementation fails positive cases. |
| F2: migration while old and new clients coexist | Migrate a money field to explicit amount/currency while readers and writers run different schema versions. Preserve records through partial backfill, retries and rollback; use integer/decimal contracts, not floating-point guesswork. Tests reasoning about transitions rather than final-schema correctness alone. | Generated data including boundary values, old/new API clients, crash at every migration phase, loss/duplication checks, rollback contract and measured query budget. A passing final schema with data loss fails the critical gate. |
| F3: distributed incident diagnosis | Repair duplicate application or lost acknowledgment in a compact queue/replication implementation. Provide logs, a reproducer and a pinned specification; reorder, duplicate and drop messages. A harder sibling adds membership transition. Tests causal diagnosis and invariants with little scaffolding overhead. | Deterministic schedule enumeration within declared bounds; reference state-machine oracle; safety plus liveness under stated assumptions. Always rejecting operations cannot pass. Longer sibling integrates the repair into a service. |
| F4: unfamiliar API and semantic change | Use a small unfamiliar, locally documented library to implement a cancellation-safe streaming client or change a typed interpreter's closure semantics. Public examples cover happy paths; held-out combinations expose guessed contracts. Tests learning from source/specifications rather than API recall. | Independent reference interpreter/state model; generated valid/invalid programs or streams; cancellation and cleanup checks; error semantics. Domain rules are public; only test instances are hidden. |
| F5: optimization with a correctness boundary | Optimize an existing query engine or parser on mixed workloads, including skew and adversarial inputs, without changing results. Tests algorithmic choice and measurement discipline; avoids turning the task into a giant compiler build. | Differential correctness first, then held-out throughput, p95 latency and peak RSS on controlled hardware. Baseline/reference runs interleaved. Report speedups only for correct submissions; include regressions on small workloads. |
| F6: accumulated project evolution and handoff | Evolve a realistic service through 3, 6 and 9 checkpoints: new feature, teammate change, requirement revision, dependency upgrade and handoff. A matched uninterrupted condition isolates forced context reset from ordinary task length. Tests preservation of earlier contracts, recovery and selective use of history. | Per-checkpoint private grading snapshots; final integrated flows; contract survival after each change; valid requirement supersession; state retention after declared compaction/handoff. Keep security discovery and explicit repair as distinct phases. |

These are proposed task specifications, not existing finished tasks. Use established stacks and pinned local dependencies. Novelty should come from interacting constraints, task-specific semantics and unanticipated combinations, not obscure language syntax or broken installation.

For each family, include three development difficulty levels: baseline behavior, one interacting constraint, and a combination of constraints. Freeze scored levels after pilot calibration. A task all kits pass may remain a useful reliability control; a task all fail needs review for ambiguity, infrastructure and unreasonable scope before it is called hard. Do not tune selection to produce a preferred ordering.

### Prevent an early failure from erasing later capability

Maintain two separate views:

- **Accumulating track:** the kit carries its own implementation forward. Earlier damage and technical debt count in the final deployed result.
- **Independent-checkpoint track:** each selected later task starts from the same validated reference snapshot, so a failed foundation does not prevent measuring migration, diagnosis or optimization skill.

Never splice a reference solution into an accumulating run and call it uninterrupted success. Report checkpoint tasks as separate trials. For handoff tests, provide identical externally supplied summaries in one condition, and let each kit create its own summary in another; do not confuse those measurements.

## 5. Assistance policy: directly test the 'two nudges' hypothesis

All task instructions upfront already require implementing the contract, using available tests and reporting completion honestly. Nudges add no task-specific knowledge. Freeze exact texts:

- **Minimal continuation control:** `Continue working on the original task.`
- **Nudge 1:** `Review the original requirements against the current implementation. Continue any unfinished work and verify it before concluding.`
- **Nudge 2:** `Run the available relevant checks, investigate any failures, and complete the original task. Do not assume the previous attempt finished it.`

A message identifying a bug, failed invariant, file, algorithm or hidden test is substantive assistance. Log it separately and exclude the run from the standardized two-nudge score. Infrastructure repair is also a separate event, never an invisible nudge.

### Paired rescue experiment

1. Run the original kit unattended to its first terminal handoff or base budget T0, whichever comes first. Snapshot repository, conversation, controller state and consumed budget; grade the snapshot outside the agent environment.
2. For unsuccessful but infrastructure-valid attempts, branch the identical state into C (minimal continuation) and N (standardized nudges). Use fresh isolated sandboxes and randomized execution order. Both get the same additional budget and at most two controller messages.
3. Send the first message on branch start. Send the second only after another terminal handoff with no success under the private grader, subject to the fixed remaining budget. A still-working agent receives no interruption or extra hints. The controller sees only the eligibility result; it never exposes hidden cases or failure labels.
4. Grade the final states separately. Report original unattended result, C result and N result. A branch inherits the original cost/time for total-cost calculations. Shared initial successes count as successes in all policy estimates, rather than dropping them from denominators.
5. Built-in messages/actions remain logged. If a kit cannot faithfully clone/resume conversation/controller state, declare the pair unsupported. Run independently randomized policies from the task start for that kit instead; do not pretend the states are matched.

Interpretation: C versus original measures the combined effect of reactivation and extra opportunity. N versus C measures the incremental effect of the stronger generic reminder at matched budget ceilings. A terminal model cannot be given more time without some reactivation, so this is NOT a pure 'time alone' experiment. Report actual consumed time/calls as well as ceilings.

A separate all-run budget ladder on a small preregistered subset (T0 versus 2×T0) tests additional compute from a fresh start, without conditioning only on failed attempts. Do not use repeated attempts to select the best and call it pass@1.

## 6. Budgets and clocks

Development starting defaults, to be calibrated and frozen before scoring:

| Task tier | Initial agent budget T0 | Each rescue branch additional budget | Candidate workspace RAM reservation / hard ceiling |
|---|---:|---:|---:|
| Compact diagnosis/semantic task | 20 minutes | 20 minutes shared across its two messages | 4 / 8 GiB |
| Repository change/migration | 60 minutes | 60 minutes shared across its two messages | 8 / 16 GiB |
| Accumulating project | 180 minutes total with declared checkpoint allocations | 180 minutes shared across its two messages | 8 / 16 GiB |

These are proposed caps, not claims that all tasks fit them. Reference implementations and human pilots must validate resources. Freeze CPU, storage, process count, compiler versions, network policy and concurrent job limits as well. Serialize performance grading on dedicated resources.

Primary budget is user-observed elapsed agent time after environment readiness; compilation and tool execution count. Publish provider wait time, active tool time and known outage intervals separately. Setup and private grading do not consume the agent budget. An outage-invalidated trial stays in availability statistics and gets a new attempt ID under a fixed rerun rule; do not silently pause clocks until success. A planned suspend/handoff has a declared clock rule.

Also report API dollars when billable usage is available, tokens by provider definition, tool calls and peak resources. Tokens are not equal compute across architectures. Subscription access cost is unknown per run unless measured; do not assign zero or invent API-equivalent cost. Use separate cost-controlled experiments if needed rather than claiming a time-controlled comparison is cost-controlled.

## 7. Qualification and failure attribution

Before any scored task, each adapter must pass a small deterministic compatibility contract: receive text, make and receive a tool call, read/edit a file, run a command, handle a failed command, resume a session and preserve non-ASCII output. Add long-message, tool-output truncation and context-limit checks. Use scripted mock endpoints as well as live smoke checks to distinguish adapter bugs from model choices. Passing qualification does not prove complex-task compatibility.

Before every task block, validate image/toolchain health, disk capacity and a known-good solution against the verifier. Include reference and intentionally defective submissions to validate graders. Record CPU/RAM reservations and kill limits, not just Docker flags.

Preserve observed facts separately from causal review:

| Observation | Scoring and interpretation |
|---|---|
| Authentication failure, provider outage or evaluator crash | Infrastructure-invalid for capability comparisons; counts against observed service availability; preserve and apply fixed replacement policy |
| Proven harness drops/corrupts valid model output | Invalidate affected capability trials, fix/version adapter and rerun all affected cells; retain history |
| Model emits an invalid tool call despite a validated adapter | Kit execution failure; potentially recoverable; not automatically infrastructure |
| Model stops with work remaining | Unattended failure; eligible for standardized rescue |
| Model loops or exceeds its declared resource budget | Kit failure under that budget, unless a separate environment defect is demonstrated |
| Compiles but violates a required invariant | Functional failure; report concrete counterexample and coverage |
| Diagnosis remains uncertain | Unknown cause, not a forced attribution to reasoning or harness |

Primary end-to-end success uses all launched scored attempts, with invalidity/availability visible. Also publish success conditional on infrastructure validity, its denominator and invalid fraction. Do not compare conditional scores alone when exclusions differ; give best/worst missing-outcome bounds. Allow at most one replacement for a proven infrastructure-invalid attempt; retain both and never choose the better valid score. Widespread incidents stop the affected block rather than triggering unlimited retries.

## 8. Graders: meaningful difficulty and informative failures

- Every hidden assertion maps to a public requirement. Hidden data must not mean hidden requirements.
- Separate positive functionality, negative/safety cases, liveness, resource efficiency and regression preservation. Blocking all requests, rejecting all programs or aborting every transaction cannot earn a soundness-only victory.
- Use differential/reference oracles, deterministic fault schedules, generated boundary cases and metamorphic properties where valid. A reference implementation is not infallible: test it against independently reasoned examples and adversarial mutants.
- For each critical invariant, include a known-bad mutant that the verifier rejects and a known-good solution that passes. Have a reviewer independently inspect oracle logic and counterexamples. Metamorphic tests supplement, not replace, absolute correctness checks.
- Keep private verifiers outside agent-readable mounts and grade copied submissions in a fresh sandbox. Pin allowed submission surfaces and detect modifications to protected components. The candidate must not reach the oracle over the network.
- Report binary trusted success AND grouped diagnostic coverage. A dangerous false proof or data leak remains a failed deployment even if most happy paths pass. Avoid invented weighted sums that let many easy cases cancel one critical failure.
- Measure distance with interpretable quantities: requirement groups passed, valid/invalid case counts, shortest reproducible counterexample, surviving earlier contracts, and correct-only performance ratio. These are diagnostics, not a promise that a nearly passing solution needs little repair effort.
- Do not count thousands of generated cases as thousands of independent task samples. Cluster by task family/instance when estimating cross-task uncertainty.
- Evaluate the artifact at fixed milestones privately without sending hidden feedback to the agent. A green public suite is not sufficient for completion. Do not let repeated private tests become an interactive oracle.

## 9. Results useful for choosing a kit

Publish a profile rather than one universal ordinal ranking:

1. **Unattended trusted success:** original attempts satisfying all critical requirements and required functionality.
2. **Success with ≤2 generic nudges:** unconditional policy estimate plus rescue rate among eligible original failures.
3. **Minimal-continuation success:** distinguishes reminders from extra opportunities.
4. **Correctness by task family and difficulty:** independently initialized and accumulating tracks shown separately.
5. **Critical regression frequency and retention:** earlier contracts broken by later changes, plus safety/liveness failures.
6. **Cost and latency to verified success:** show unsuccessful spend too; restricted means/censoring at budget, not only median of winners.
7. **Supervision burden:** number and type of controller interventions. Scripted nudges do not measure actual human minutes; measure those in a separately instrumented user study.
8. **Repeatability and availability:** per-task success frequency, run-to-run spread, API/adapter incidents and invalidity.

Use plots of verified success against budget and assistance, and cost/reliability Pareto comparisons. A buyer may prefer the cheaper kit after two nudges; an unattended operator may prefer a more expensive kit with fewer stalls. State the workload and preference that support each recommendation.

Convergence requires an equivalence test with a predeclared practical margin, proposed ±5 percentage points for assisted trusted success on the target workload, AND examination of critical failure rates and cost. Overlapping confidence intervals or an insignificant difference are not proof of equivalence. The small pilot cannot establish that margin; use its variance to plan the main sample, potentially hundreds of independent tasks/trials. Report 'insufficient precision' instead of forcing a ranking.

## 10. Replication, contamination and scope

Pilot: four representative kits × six development instances × two repetitions = 48 initial attempts. Up to two rescue branches per failed attempt yields at most 96 additional continuations (144 segments total). Each branch can receive two messages; messages are not fresh independent trials. Launching this pilot requires a separate execution decision and a measured cost ceiling; this document launches nothing.

Choose kits to cover the observed strong native system, a second strong system, Genesys, and a compatible open-weight baseline. Exact IDs/versions are selected after access qualification, not guessed here. The pilot's purpose is diagnosing instruments and estimating costs, not proving relative rank with 12 starts per kit.

Candidate release: at least 12 new instances, three repetitions per cell as an initial design floor; expand when task-level uncertainty demands it. Pair all kits on variants, randomize/interleave run order and spread repeats over multiple blocks/days. Use paired differences and family-clustered uncertainty; six families give weak tail estimates, which must be stated. Do not mistake more repeats on one task for broader task coverage.

Use public development tasks and embargoed scored instances authored independently. Commit cryptographic hashes of hidden task/seed manifests before collection, then release tasks/graders after that benchmark round where licenses permit. Public tests become regression/development material for subsequent versions. Do not claim random renaming eliminates training contamination. Avoid training on scored instances and disclose all prompt/harness tuning.

Human baselines: have an experienced developer solve a subset, record work and verification time and ambiguity reports. A task author knowing the solution is not a comparable human baseline. These timings guide task tiers; they do not warrant a METR-style horizon fit from a tiny sample.

## 11. Implementation sequence and acceptance gates

| Stage | Deliverables | Gate before moving on |
|---|---|---|
| 0: failure audit | Classify a balanced sample of v4/v4.1 failures and successes using traces, including premature stops, soundness failures and suspected adapter faults | Evidence-backed categories; no automatic 'DNF = weak reasoning' or 'DNF = harness bug' |
| 1: measurement substrate | Versioned kit/task manifests; isolated runs; append-only events; checkpoints; distinct clocks; canonical outcome schema; resumable controller with locks | Mock and live compatibility tests; interrupted-call semantics; no duplicate side effects or unrecorded retries; secrets excluded from artifacts |
| 2: first discriminating tasks | F1, F3 and F6 development instances plus trusted reference states, public contracts and hidden graders | Known-good pass, targeted mutants fail, public/hidden requirement alignment reviewed |
| 3: assistance experiment | Exact intervention policy, C/N branches, state-clone checks, randomized execution and cost accounting | Synthetic stopping/looping agents verify message counts, budgets, denominator logic and no hidden-feedback leakage |
| 4: broaden pilot | F2, F4 and F5, difficulty tiers, four qualified kits and 48 initial attempts | Infrastructure defects resolved; measured cost envelope; saturated/impossible tasks explained; no premature ranking |
| 5: freeze scored release | Independent tasks, hashes, preregistered policies, sample/precision plan and resource specs | Reference runs stable; enough precision for intended claims; no tuning to scored model outcomes |
| 6: publish | Single entry README linking manifests, results, failure exemplars, reproduction and analysis | Every headline traceable to artifacts; assistance and exclusions visible; no unsupported universal rank |

Recommended first implementation: F1 multi-tenant export, F3 distributed diagnosis and F6 accumulating/handoff. Together they cover practical coding, compact reasoning and long-session reliability without immediately committing to expensive compiler infrastructure. Keep the existing v4.1 tasks as historical/regression controls, not the entire new ranking suite.

Suggested layout when implementation begins:

```text
benchmark-v5/
  README.md, DESIGN.md
  schemas/                 # task, kit, attempt, intervention, outcome
  tasks/dev/               # contracts, starter snapshots, development fixtures
  runner/                  # orchestration and adapter qualification
  analysis/                # paired policies, uncertainty, diagnostic reports
  tests/                   # runner/analysis and verifier integrity
results-v5/                # compact public manifests/results, no credentials
```

Private scored tasks and live workspaces must be stored outside candidate access. Source snapshots, environment digests and raw-artifact hashes should accompany each attempt. No changes to v4/v4.1 runners are necessary to begin v5.

## 12. Research informing the design

- [SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering](https://arxiv.org/abs/2405.15793): interface design is an experimental variable; it supports testing harness effects, not attributing every failure to them.
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents): evaluates the combined agent system and distinguishes traces from actual outcomes. This motivates explicit kit identities and artifact grading.
- [Anthropic: Quantifying infrastructure noise](https://www.anthropic.com/engineering/infrastructure-noise): reports score changes under different resource enforcement. This motivates frozen reservations/ceilings and availability accounting; its effect sizes are not estimates for our suite.
- [METR task-completion time horizons](https://metr.org/time-horizons/): relates task success to measured human task duration. This motivates a duration/difficulty profile but not a copied horizon statistic without adequate human data and task coverage.
