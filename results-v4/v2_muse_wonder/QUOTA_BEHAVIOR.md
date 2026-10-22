# Muse Wonder — subscription quota behavior (v4 operational finding, 2026-10-13)

**Headline for the analysis:** Muse Wonder (Meta, `muse exec` on the Muse Code subscription) is the
**only model in the entire v4 field that could not sustain a run on its own billing path** — it
exhausts its usage-window quota mid-benchmark, and a **plan upgrade did not fix it**. Every other v4
model (Claude Max, ChatGPT/Codex, z.ai GLM coding plan, Kimi subscription, all OpenRouter models)
completed full 7-sprint runs without a per-window quota wall. This is a real usability/economic penalty
independent of raw model quality, and it must be reflected in the ranking (operational cost axis), not
charged to the model's code quality (infra failures are never scored).

## Evidence (concrete)
- **Attempt 1 (pre-upgrade tier):** sprint 1 ran ~33 min of real work (built a full Rails skeleton),
  then `run.terminal.failed`:
  `API error 429 … Subscription quota exhausted. Your usage window resets at 2026-10-13T22:31:16Z
  (rate_limit_error)`. ~0.9 sprint before exhaustion.
- **User upgraded the plan** (Power → higher tier) explicitly to clear this.
- **Attempt 2 (upgraded tier):** sprint 1 completed CLEAN (exit 0, 714 s / 12 min, committed
  "feat: scaffold Rails 8 chat app …"), sprint 2 ran partway, then the **same** 429:
  `Subscription quota exhausted … window resets at 2026-10-13T22:31:16Z`. ~1.5 sprints before
  exhaustion. The reset timestamp was **identical** pre/post upgrade — the upgrade raised the quota
  *ceiling* but not the *reset cadence* (a fixed daily 22:31 UTC window).
- All 134 model-stream opens in the clean attempt were `attempt 1/10` (no retries/backend errors) —
  the model/harness are fine; the wall is purely the subscription quota.

## Quantified impact
- Sustained throughput: **~1.5 v4 sprints per daily window** on the upgraded plan.
- A 7-sprint v4 run therefore spans **~5 calendar days** (one 22:31-UTC window per ~1.5 sprints) on the
  subscription — vs a single multi-hour session for every other model.
- Harness is fully working (sprint 1 end-to-end clean); constraint is 100% the quota.

## Access caveats (related, same source)
- **Wonder Full is not CLI/subscription-reachable at any tier** — `muse-wonder-full` → HTTP 404
  "model does not exist or you lack access", before AND after the upgrade. Only standard
  `muse-wonder-1.0` (AA Intelligence Index ~52, near-frontier) is exposed to `muse exec`.
- Alternative route: OpenRouter `meta/muse-wonder` (same standard model) is metered per-token
  (~$4 in / $20 out per M), no quota wall — the only way to complete a full run in one session, but
  it abandons the flat-rate subscription and still can't reach Wonder Full.

## Disposition
Run is **provisional / infra-constrained** (per scoring-discipline rule #7: infra failures get no
rankable total and are never charged to the model). Sprint 1 is clean and preserved. Decision
(2026-10-13): wait for the 22:31-UTC reset and resume sprint-by-sprint across windows, reassessing
how many sprints a fresh full window clears. The quota behavior above is a reportable result in its
own right — a model that is operationally impractical to run at length on its vendor's own plan.

## Second operational failure mode: rspec/system-test hang (2026-10-14)
Sprint 4 (reports) **stall-aborted at the 60-min cap** (V4_STALL_TIMEOUT=3600): muse went
completely silent for 60 min. Last logged activity before the silence = `bundle exec rspec`
(running its own test suite). No quota 429 this time — a genuine **hang running system tests**
(capybara/selenium browser tests) inside muse's bwrap network-isolated sandbox. muse had already
reverted injections #4–6 in the working tree (safe `search_by_email` scope restored,
`skip_before_action :require_admin` removed, email `downcase` restored) but hung BEFORE committing,
so sprint 4 did not complete (DNF=stall_aborted, 13 uncommitted changes discarded on reset).

**Two independent operational blockers now observed for Muse Wonder (muse exec subscription), both
absent in every other v4 model:** (1) subscription quota exhaustion (~1.5 sprints/window even after
upgrade), (2) long silent hangs during rspec/system-test execution. muse's CODE and security
instincts are strong (clean S1–S3 builds; 6/6 planted sabotage items caught unprompted across the
sprint-3 and sprint-4 boundaries), but the muse Code CLI harness is operationally fragile for long
autonomous multi-sprint runs. For the ranking: strong quality signal, but a heavy operational/
reliability penalty — report both.

## Correction: rolling window, not fixed-daily (2026-10-14)
The reset is a ROLLING usage window, not a fixed daily 22:31-UTC boundary. A single fresh window
(opened ~22:31Z Oct 13) carried sprint 1 clean through sprint 5 + several sprint-6 hang-retries before
exhausting at ~07:38Z Oct 14, and the 429 then advertised reset at ~08:38:39Z — i.e. ~1h later, not
22:31. So earlier "22:31" readings were just that window's boundary. Net: quota replenishes on a
rolling ~hourly-to-daily cadence; a fresh full window sustains ~5 sprints of this benchmark before
exhausting. Still uniquely quota-limited vs every other v4 model, but pauses are ~1h, not ~15h.

## Weekly cap hit: ~4-day block (2026-10-14)
After S1–S6 completed (incl. 7 sprint-6 hang-retries) + a quick sprint-7 start, the 429 this time
advertised reset at **2026-10-19T00:00:00Z — ~4 days out**, not the ~1h rolling reset seen earlier.
So the subscription has TWO limits: a short rolling window (~1h) AND a longer weekly/period cap. The
full v4 run (heavily retried due to the system-test hangs) exhausted the WEEKLY cap, hard-blocking the
final sprint (7/reveal) for ~4 days. Net: completing even a single v4 model run on the Muse Code
subscription can blow a multi-day quota — a severe operational constraint unique in the v4 field.
Run state at block: S1–S6 done, 13/14 sabotage caught unprompted (only #7b dropped-index missed);
only sprint 7 (explicit reveal) remains, and the result is already essentially determined.
