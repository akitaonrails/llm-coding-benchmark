#!/usr/bin/env python3
"""Independent pod-local lease guard. Never needs a secret in argv or logs.

A controller renews a short lease while a bounded stage is running. The fixed
stage deadline cannot be extended by ordinary heartbeats. Missing/corrupt leases
fail closed. Run under a pod-local service independent of the SSH connection.
"""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path

MAX_LEASE = 300


def expired(lease, now):
    try:
        issued = float(lease['issued_at'])
        until = float(lease['expires_at'])
        deadline = float(lease['stage_deadline'])
        return not (0 <= now - issued <= MAX_LEASE and
                    issued < until <= issued + MAX_LEASE and
                    now < min(until, deadline))
    except (KeyError, TypeError, ValueError, OverflowError):
        return True


def read_lease(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def stop_pod(pod_id):
    # Pod-scoped credentials are inherited by runpodctl, never serialized.
    try:
        result = subprocess.run(['runpodctl', 'stop', 'pod', pod_id],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=30)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def run(lease_path, event_path, pod_id, interval=5, on_expiry='stop'):
    stopping = False
    reported = False
    while True:
        now = time.time()
        if on_expiry == 'retain':
            stale = expired(read_lease(lease_path), now)
            if stale and not reported:
                with event_path.open('a') as log:
                    log.write(json.dumps({'time': now, 'event': 'lease_expired_pod_retained',
                                          'requires': 'explicit user shutdown approval'}) + '\n')
            reported = stale
            time.sleep(interval)
            continue
        stopping = stopping or expired(read_lease(lease_path), now)
        if stopping:
            accepted = stop_pod(pod_id)
            with event_path.open('a') as log:
                log.write(json.dumps({'time': now, 'event': 'pod_stop_requested',
                                      'command_accepted': accepted}) + '\n')
            # Keep retrying even after command success until provider stops us.
            # Success is not proof that billing has stopped.
        time.sleep(interval)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--lease', type=Path, default=Path('/root/logs/billing-lease.json'))
    p.add_argument('--events', type=Path, default=Path('/root/logs/billing-watchdog.ndjson'))
    p.add_argument('--on-expiry', choices=['stop', 'retain'], default='stop')
    a = p.parse_args()
    pod_id = os.environ.get('RUNPOD_POD_ID')
    if not pod_id:
        raise SystemExit('RUNPOD_POD_ID missing; watchdog cannot protect this pod')
    a.events.parent.mkdir(parents=True, exist_ok=True)
    run(a.lease, a.events, pod_id, on_expiry=a.on_expiry)


if __name__ == '__main__':
    main()
