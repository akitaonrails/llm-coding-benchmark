#!/usr/bin/env python3
"""Durable bounded stage execution with a pod-local billing lease.

Plan entries contain argv arrays (never shell fragments or credentials). All
paths and logs stay local. A failure chooses an explicit recovery stage; absent
one, stop the pod. A new stage gets a fixed deadline; polling never extends it.
"""
import argparse
import fcntl
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from b300_remote import execute
from run_b300_campaign import stop_sprint_tree

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'results-v4/_b300_campaign/supervisor'


def renew(stage, deadline):
    now = time.time()
    lease = json.dumps(dict(issued_at=now, expires_at=now + 120,
                           stage_deadline=deadline, stage=stage))
    import base64
    data = base64.b64encode(lease.encode()).decode()
    execute('pgrep -f "^python3 /root/b300_billing_watchdog.py( |$)" >/dev/null && echo ' + data + ' | base64 -d > /root/logs/billing-lease.tmp && '
            'mv /root/logs/billing-lease.tmp /root/logs/billing-lease.json', timeout=15)


def shutdown():
    config = json.loads((ROOT / 'config/b300_campaign.json').read_text())
    if config.get('billing_safety', {}).get('pod_shutdown_policy') == 'explicit_approval':
        return 'pod_retained_requires_explicit_user_shutdown_approval'
    try:
        execute('mkdir -p /workspace/b300-preserved/logs; cp -a /root/logs/. /workspace/b300-preserved/logs/; runpodctl stop pod "$RUNPOD_POD_ID"', timeout=30)
        return 'stop_command_accepted_not_provider_verified'
    except Exception:
        return 'stop_command_failed_or_connection_closed_watchdog_lease_will_expire'


def validate(plan):
    stages = plan['stages']
    ids = {s['id'] for s in stages}
    if len(ids) != len(stages) or not stages:
        raise ValueError('Stages must have unique IDs and cannot be empty')
    for s in stages:
        if not isinstance(s['argv'], list) or not s['argv'] or not all(isinstance(x, str) for x in s['argv']):
            raise ValueError('argv must be a nonempty string array')
        unlimited = (s.get('timeout_seconds') is None and
                     s.get('model_execution') is True)
        if not unlimited and not 0 < s['timeout_seconds'] <= 14400:
            raise ValueError('Stage deadline must be positive and at most four hours')
        for key in ('on_success', 'on_failure'):
            if s.get(key) is not None and s[key] not in ids:
                raise ValueError('Unknown transition')
    # Reject cycles: retries must be explicit bounded stages, never a loop.
    checked = set()
    def visit(name, path):
        if name in checked:
            return
        if name in path:
            raise ValueError('Cyclic transition would permit indefinite spending')
        stage = next(s for s in stages if s['id'] == name)
        for key in ('on_success', 'on_failure'):
            if stage.get(key):
                visit(stage[key], path | {name})
        checked.add(name)
    for name in ids:
        visit(name, set())
    return {s['id']: s for s in stages}


def run(plan, event):
    stages = validate(plan)
    current = plan['stages'][0]['id']
    while current:
        s = stages[current]
        unlimited = s['timeout_seconds'] is None
        deadline = time.time() + (120 if unlimited else s['timeout_seconds'])
        renew(current, deadline)  # No launch unless lease delivery succeeded.
        event(dict(stage=current, status='starting', deadline=deadline))
        proc = None
        rc = 1
        try:
            with (OUT / f'{time.time_ns()}-{current}.log').open('wb') as log:
                proc = subprocess.Popen(s['argv'], cwd=ROOT, stdout=log,
                                        stderr=subprocess.STDOUT, start_new_session=True)
                next_renew = time.monotonic() + 30
                while proc.poll() is None:
                    if not unlimited and time.time() >= deadline:
                        raise TimeoutError('Stage deadline reached')
                    if time.monotonic() >= next_renew:
                        if unlimited:
                            deadline = time.time() + 120
                        renew(current, deadline)
                        next_renew = time.monotonic() + 30
                    time.sleep(1)
                rc = proc.returncode
        except Exception as exc:
            event(dict(stage=current, status='failed', error_type=type(exc).__name__))
        finally:
            if proc is not None and proc.poll() is None:
                stop_sprint_tree(proc, grace=5)
        event(dict(stage=current, status='finished', exit_code=rc))
        current = s.get('on_success' if rc == 0 else 'on_failure')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan', type=Path)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    plan = json.loads(args.plan.read_text())
    validate(plan)
    if args.validate_only:
        print('Plan valid; no paid execution started')
        return
    OUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = (OUT / 'lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    def event(data):
        data['time'] = time.time()
        with (OUT / 'events.ndjson').open('a') as stream:
            stream.write(json.dumps(data) + '\n')
        (OUT / 'status.tmp').write_text(json.dumps(data, indent=2) + '\n')
        (OUT / 'status.tmp').replace(OUT / 'status.json')
    def interrupted(signum, frame):
        raise SystemExit(128 + signum)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        from run_b300_campaign import process_identity
        (OUT/'active-supervisor.json').write_text(json.dumps(dict(
            pid=os.getpid(), start_ticks=process_identity(os.getpid())[1],
            plan=str(args.plan.resolve()), started_at=time.time()), indent=2)+'\n')
        subprocess.Popen([sys.executable, str(ROOT/'scripts/b300_live_status.py')],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        with Path('/tmp/b300-hourly-status.log').open('a') as report_log:
            subprocess.Popen([sys.executable, str(ROOT/'scripts/b300_hourly_status.py'), '--notify'],
                             stdin=subprocess.DEVNULL, stdout=report_log,
                             stderr=subprocess.STDOUT, start_new_session=True)
        run(plan, event)
    finally:
        event(dict(status='supervisor_exited', shutdown=shutdown()))


if __name__ == '__main__':
    main()
