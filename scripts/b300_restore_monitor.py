#!/usr/bin/env python3
"""Bounded fresh-pod restore with an independent remote billing lease."""
import json
import time
from pathlib import Path
from b300_remote import upload, execute
from b300_supervisor import renew, shutdown

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'results-v4/_b300_campaign/migration-20261017'

def main():
    deadline = time.time() + 3600
    success = False
    try:
        renew('fresh-pod-restore', deadline)
        upload((OUT / 'restore-new-pod.sh').read_bytes(), '/root/restore-new-pod.sh', '700')
        renew('fresh-pod-restore', deadline)
        execute('nohup bash /root/restore-new-pod.sh > /root/logs/setup.log 2>&1 < /dev/null & echo setup_launched')
        while time.time() < deadline:
            renew('fresh-pod-restore', deadline)
            status = execute('cat /root/logs/setup.status; test ! -f /root/logs/setup.exit || cat /root/logs/setup.exit', timeout=15).strip()
            record = dict(time=time.time(), stage='fresh-pod-restore', status=status, deadline=deadline)
            (OUT / 'restore-status.json').write_text(json.dumps(record, indent=2)+'\n')
            print(status, flush=True)
            if status.endswith('\n0'):
                (OUT / 'new-pod-setup.log').write_text(execute('cat /root/logs/setup.log'))
                success = True
                # Short handoff only: watchdog stops pod if next stage never arrives.
                renew('restore-complete-awaiting-serving', time.time()+300)
                return
            if status.endswith('\n1'):
                raise RuntimeError('Remote restore failed')
            time.sleep(20)
        raise TimeoutError('Restore deadline reached')
    finally:
        if not success:
            print(shutdown(), flush=True)

if __name__ == '__main__':
    main()
