#!/usr/bin/env python3
"""Wait for the selected remote model, preflight it, then run one guarded sprint.

Does not advance across grading/injection boundaries. The operator must finish
that boundary before invoking the next sprint.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--sprint', default='01_foundation')
    ap.add_argument('--ready-timeout', type=int, default=1800)
    ap.add_argument('--preflight-only', action='store_true', help='Validate readiness/tools without starting a timed sprint')
    a = ap.parse_args()
    campaign = json.loads((ROOT/'config/b300_campaign.json').read_text())
    if not campaign.get('billing_safety', {}).get('paid_execution_enabled', False):
        print('Paid execution blocked: billing watchdog and persistent supervisor have not been verified.', flush=True)
        return 2
    q = next(q for q in campaign['queue'] if q['slug']==a.slug)
    p = json.loads((ROOT/'config/opencode.benchmark.json').read_text())['provider']['runpod-vllm']['options']
    deadline = time.monotonic() + a.ready_timeout
    print(f'Waiting for {q["served_name"]} before {a.sprint}', flush=True)
    next_process_check = time.monotonic() + 60
    while time.monotonic() < deadline:
        req = urllib.request.Request(p['baseURL']+'/models', headers={'Authorization':'Bearer '+p['apiKey']})
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                names = [m['id'] for m in json.load(response).get('data',[])]
            if q['served_name'] in names:
                break
        except Exception:
            pass
        if time.monotonic() >= next_process_check:
            from b300_remote import execute
            try:
                state = json.loads(execute('python3 /root/b300_serve.py status', timeout=15).strip())
                if state.get('slug') == a.slug and state.get('alive') is False:
                    print('Inference process exited during startup; failing promptly.', flush=True)
                    return 2
            except (RuntimeError, ValueError):
                pass  # A transient SSH failure is bounded by the readiness deadline.
            next_process_check = time.monotonic() + 60
        time.sleep(15)
    else:
        print('Infrastructure blocked: server readiness deadline exceeded.', flush=True)
        return 2
    print('Server ready; checking chat and streamed tool round trip.', flush=True)
    pre = subprocess.run([sys.executable, str(ROOT/'scripts/b300_preflight.py'), a.slug])
    if pre.returncode:
        print('Preflight failed; sprint was NOT started.', flush=True)
        return pre.returncode
    if a.preflight_only:
        return 0
    print('Preflight passed; starting guarded sprint.', flush=True)
    return subprocess.call([sys.executable, str(ROOT/'scripts/run_b300_campaign.py'),
                            '--sprint', a.sprint, '--models', a.slug],
                           env=dict(os.environ, B300_ALLOW_MINOR_NUDGES='1'))


if __name__ == '__main__':
    raise SystemExit(main())
