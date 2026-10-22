#!/usr/bin/env python3
"""B300 campaign driver: guard + cost ledger around the standard v4 sprint flow.

The v4 protocol stays unchanged (run_v4_wave.py per sprint, manual grade/inject
boundaries between sprints). This wrapper adds, per config/b300_campaign.json:

  * 4h per-model guard (user rule updated 2026-10-17): cumulative SPRINT execution time
    per model is tracked in results-v4/_b300_campaign/ledger.json. `--sprint NN`
    REFUSES to launch a model already at/over budget, and instead writes
    results-v4/<slug>/TIME_GUARD.md + DNF (annotated, skipped — infra throughput
    limit, never charged to the model in scoring).
  * Per-sprint timeout kill: a single sprint may not exceed the model's remaining
    budget; on timeout the sprint process group is killed and annotated.
  * Cost ledger: every sprint's wall seconds are recorded; pod cost is computed
    at the annotated rate (USD 9.09/hr) — model-time cost plus separately
    tracked phase wall time (download + serve-load + sprint + idle) so the
    report can compare self-hosted infra cost vs subscription/per-token cloud.

Usage:
  run_b300_campaign.py --status
  run_b300_campaign.py --sprint 01_foundation            # whole queue, in order
  run_b300_campaign.py --sprint 03_admin --models v2_glm_5_3_flash_oss
  run_b300_campaign.py --annotate-download v2_glm_5_3_flash_oss --seconds 1234
"""
from __future__ import annotations
import argparse, hashlib, json, os, signal, subprocess, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results-v4"
CAMP = json.loads((REPO / "config" / "b300_campaign.json").read_text())
LEDGER_DIR = OUT / "_b300_campaign"
LEDGER = LEDGER_DIR / "ledger.json"
GUARD_S = CAMP["guard"]["per_model_sprint_budget_seconds"]
if GUARD_S is None:
    GUARD_S = float('inf')
RATE = CAMP["pod"]["rate_usd_per_hour"]
SLUGS = [q["slug"] for q in CAMP["queue"]]


def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"pod": {"rate_usd_per_hour": RATE}, "models": {}}


def save_ledger(d: dict) -> None:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    tmp = LEDGER.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2))
    tmp.replace(LEDGER)


def conditional_ready(slug: str) -> bool:
    model = next(q for q in CAMP["queue"] if q["slug"] == slug)
    parent = model.get("run_only_if_dnf")
    return not parent or any((OUT / parent / marker).exists() for marker in ("DNF", "PAUSED"))


def serving_fingerprint(slug: str) -> str:
    model = next(q for q in CAMP['queue'] if q['slug'] == slug)
    payload = json.dumps(model, sort_keys=True).encode()
    payload += (REPO / 'scripts/b300_serve.py').read_bytes()
    return hashlib.sha256(payload).hexdigest()


def performance_validated(slug: str) -> bool:
    path = LEDGER_DIR / 'performance-validation' / f'{slug}.json'
    if not path.exists():
        return False
    record = json.loads(path.read_text())
    return (record.get('passed') is True
            and record.get('tool_preflight_passed') is True
            and record.get('decode_tokens_per_second', 0) >= CAMP.get('optimization_policy', {}).get('minimum_decode_tokens_per_second', 100)
            and record.get('serving_fingerprint') == serving_fingerprint(slug)
            and bool(record.get('evidence'))
            and all((REPO / p).is_file() for p in record['evidence']))


def record_result(slug: str, sprint: str, wrapper_rc: int) -> dict:
    path = OUT / slug / "sprints" / f"sprint{sprint}" / "sprint.result.json"
    if not path.exists():
        return {"exit": wrapper_rc or 1, "wrapper_exit": wrapper_rc,
                "status": "missing_result"}
    result = json.loads(path.read_text())
    return {"exit": result.get("exit_code"), "wrapper_exit": wrapper_rc,
            "stall_aborted": result.get("stall_aborted", False),
            "status": "completed" if result.get("exit_code") == 0 and
                not result.get("stall_aborted") else "failed"}


def process_identity(pid: int):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().split(") ", 1)[1].split()
        return int(fields[1]), fields[19], fields[0]
    except (FileNotFoundError, ProcessLookupError):
        return None


def stop_sprint_tree(proc: subprocess.Popen, grace: float = 30) -> None:
    # run_phase starts OpenCode in a separate session, so killing only the
    # sprint wrapper's process group leaves the expensive inference running.
    snapshot = {}
    for p in Path("/proc").iterdir():
        if p.name.isdigit():
            ident = process_identity(int(p.name))
            if ident:
                snapshot[int(p.name)] = ident
    owned = {proc.pid}
    while True:
        children = {pid for pid, ident in snapshot.items() if ident[0] in owned}
        if children <= owned:
            break
        owned |= children

    def alive(pid):
        now = process_identity(pid)
        return now and pid in snapshot and now[1] == snapshot[pid][1] and now[2] != "Z"

    for pid in sorted(owned - {proc.pid}) + [proc.pid]:
        if alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline and any(alive(pid) for pid in owned):
        proc.poll()
        time.sleep(0.1)
    for pid in owned:
        if alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    proc.wait()


def entry(d: dict, slug: str) -> dict:
    return d["models"].setdefault(slug, {
        "sprints": {}, "sprint_seconds_total": 0, "guard_tripped": False,
        "download_seconds": 0, "serve_load_seconds": 0, "phase_started": None,
    })


def usd(seconds: float) -> float:
    return round(seconds / 3600.0 * RATE, 2)


def sprint_seconds(d: dict, slug: str) -> float:
    return entry(d, slug)["sprint_seconds_total"]


def trip_guard(slug: str, d: dict, why: str) -> None:
    e = entry(d, slug)
    e["guard_tripped"] = True
    e["guard_reason"] = why
    e["model_time_cost_usd"] = usd(e["sprint_seconds_total"] + e.get("prior_attempt_sprint_seconds", 0))
    save_ledger(d)
    mdir = OUT / slug
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "TIME_GUARD.md").write_text(
        f"# Time guard tripped — {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"Reason: {why}\n\n"
        f"Cumulative sprint execution: {e['sprint_seconds_total']:.0f}s "
        f"(budget {GUARD_S}s).\n\n"
        f"Per user rule (2026-10-16): stopped, annotated, skipped. This is a "
        f"throughput/infra limit of the B300 pod ($ {RATE}/hr), NOT a model-quality "
        f"failure — infra failures are never charged to the model (CLAUDE.md). "
        f"Model-time pod cost so far: ${e.get('model_time_cost_usd', 0):.2f}.\n")
    (mdir / "DNF").write_text(
        f"TIME GUARD: {why} — cumulative sprint time exceeded {GUARD_S}s "
        f"(B300 throughput limit, not charged to model)\n")
    e['status'] = 'paused_pending_batch_review'
    save_ledger(d)
    from b300_pause import checkpoint
    checkpoint(slug, why)
    print(f"[guard] TRIPPED for {slug}: {why}")


def run_sprint(slug: str, sprint: str, d: dict) -> None:
    e = entry(d, slug)
    spent = e["sprint_seconds_total"]
    remaining = current_budget() - spent
    if remaining <= 0:
        trip_guard(slug, d, f"pre-sprint check: {spent:.0f}s already >= budget")
        return
    print(f"[guard] {slug} sprint {sprint}: {spent:.0f}s spent, "
          f"{remaining:.0f}s remaining", flush=True)
    t0 = time.time()
    cmd = [sys.executable, str(REPO / "scripts" / "run_v4_sprint.py"),
           "--model", slug, "--sprint", sprint,
           "--config", str(REPO / "config" / "models_v2.json")]
    env = dict(os.environ)
    if current_budget() == float('inf'):
        env['V4_PHASE_TIMEOUT'] = '0'
    proc = subprocess.Popen(cmd, start_new_session=True, env=env)
    monitor_sprint(proc, slug, sprint, d, t0)


def current_budget() -> float:
    config = json.loads((REPO / 'config/b300_campaign.json').read_text())
    budget = config['guard']['per_model_sprint_budget_seconds']
    return float('inf') if budget is None else budget


class AgentLoopDetected(RuntimeError):
    pass


def wait_with_live_budget(proc, spent: float, started_at: float, progress=None):
    while True:
        if progress:
            reason=progress.check()
            if reason:
                raise AgentLoopDetected(reason)
        remaining = current_budget() - spent - (time.time() - started_at)
        if remaining <= 0:
            raise subprocess.TimeoutExpired('sprint budget', 0)
        try:
            return proc.wait(timeout=min(5, remaining))
        except subprocess.TimeoutExpired:
            pass


def monitor_sprint(proc, slug: str, sprint: str, d: dict, t0: float) -> None:
    global GUARD_S
    e = entry(d, slug)
    spent = e['sprint_seconds_total']
    from b300_progress import ProgressWatch
    model_root=OUT/slug
    progress=ProgressWatch(model_root/'project',model_root/'sprints'/f'sprint{sprint}'/f'sprint{sprint}.ndjson')
    try:
        rc = wait_with_live_budget(proc, spent, t0, progress)
    except AgentLoopDetected as exc:
        stop_sprint_tree(proc)
        elapsed=time.time()-t0
        e['sprints'][sprint]={'seconds':round(elapsed),'loop_paused':True,'reason':str(exc)}
        e['sprint_seconds_total']+=elapsed
        e['model_time_cost_usd']=usd(e['sprint_seconds_total']+e.get('prior_attempt_sprint_seconds',0))
        save_ledger(d)
        (model_root/'loop-pause.json').write_text(json.dumps(dict(sprint=sprint,reason=str(exc),elapsed_seconds=elapsed),indent=2)+'\n')
        from b300_pause import checkpoint
        checkpoint(slug,'Agent loop/no-progress guard: '+str(exc))
        return
    except subprocess.TimeoutExpired:
        GUARD_S = current_budget()
        remaining = GUARD_S - spent
        stop_sprint_tree(proc)
        elapsed = time.time() - t0
        e["sprints"][sprint] = {"seconds": round(elapsed), "timeout_killed": True}
        e["sprint_seconds_total"] += elapsed
        trip_guard(slug, d, f"sprint {sprint} exceeded remaining budget "
                            f"({elapsed:.0f}s > {remaining:.0f}s); killed")
        return
    elapsed = time.time() - t0
    e["sprints"][sprint] = {"seconds": round(elapsed), **record_result(slug, sprint, rc)}
    e["sprint_seconds_total"] += elapsed
    e["model_time_cost_usd"] = usd(e["sprint_seconds_total"] + e.get("prior_attempt_sprint_seconds", 0))
    save_ledger(d)
    print(f"[guard] {slug} sprint {sprint} done in {elapsed:.0f}s "
          f"(total {e['sprint_seconds_total']:.0f}s, model-time cost "
          f"${e['model_time_cost_usd']})")
    GUARD_S = current_budget()
    if e["sprint_seconds_total"] >= GUARD_S:
        trip_guard(slug, d, f"post-sprint check: cumulative "
                            f"{e['sprint_seconds_total']:.0f}s >= {GUARD_S}s")


def annotate(slug: str, kind: str, seconds: float, d: dict) -> None:
    e = entry(d, slug)
    e[f"{kind}_seconds"] = e.get(f"{kind}_seconds", 0) + seconds
    save_ledger(d)
    print(f"[ledger] {slug}: +{seconds:.0f}s {kind} "
          f"(pod cost ${usd(seconds)})")


def status(d: dict) -> None:
    print(f"B300 campaign — pod rate ${RATE}/hr, guard {GUARD_S}s/model\n")
    for q in CAMP["queue"]:
        slug = q["slug"]
        cond = q.get("run_only_if_dnf")
        if cond and not (OUT / cond / "DNF").exists():
            print(f"  [skip] {slug}: conditional — {cond} has not DNF'd")
            continue
        slug = q["slug"]
        e = d["models"].get(slug, {})
        spent = e.get("sprint_seconds_total", 0)
        sprints = sorted(e.get("sprints", {}))
        guard = " GUARDED" if e.get("guard_tripped") else ""
        dnf = " DNF" if (OUT / slug / "DNF").exists() else ""
        print(f"  {slug:32s} {spent:6.0f}s/{GUARD_S}s  "
              f"${e.get('model_time_cost_usd', 0):5.2f}  "
              f"sprints={len(sprints)}/7{guard}{dnf}")
        print(f"    repo={q['hf_repo']} ({q['size_gb']}GB) — {q['notes']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--sprint")
    ap.add_argument("--models", help="comma-separated slugs (default: whole queue in order)")
    ap.add_argument("--annotate-download", metavar="SLUG")
    ap.add_argument("--annotate-serve-load", metavar="SLUG")
    ap.add_argument("--seconds", type=float, default=0.0)
    a = ap.parse_args()
    d = load_ledger()

    if a.status:
        status(d)
        return 0
    if a.annotate_download:
        annotate(a.annotate_download, "download", a.seconds, d)
        return 0
    if a.annotate_serve_load:
        annotate(a.annotate_serve_load, "serve_load", a.seconds, d)
        return 0
    if not a.sprint:
        ap.error("need --status, --sprint NN, or --annotate-*")
    if not CAMP.get('billing_safety', {}).get('paid_execution_enabled', False):
        print('[billing-safety] Paid execution blocked; independent watchdog and persistent supervisor must be verified first.')
        return 2
    models = [m.strip() for m in a.models.split(",")] if a.models else SLUGS
    for slug in models:
        if slug not in SLUGS:
            print(f"[guard] {slug} not in campaign queue — skipping")
            continue
        if not conditional_ready(slug):
            print(f"[guard] {slug}: conditional fallback not eligible — skipping")
            continue
        if CAMP.get('optimization_policy', {}).get('require_per_model_validation') and not performance_validated(slug):
            print(f'[performance] {slug}: serving configuration has no current validated performance evidence; refusing timed sprint')
            return 2
        if (OUT / slug / "PAUSED").exists():
            print(f'[pause] {slug}: preserved for explicit resume review; skipping')
            continue
        if (OUT / slug / "DNF").exists():
            print(f"[guard] {slug} already DNF — skipping")
            continue
        sprints_dir = OUT / slug / "sprints"
        done = sprints_dir.glob(f"sprint{a.sprint}*") if sprints_dir.exists() else []
        if any((p / "sprint.result.json").exists() for p in done):
            print(f"[guard] {slug} sprint {a.sprint} already done — skipping")
            continue
        run_sprint(slug, a.sprint, d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
