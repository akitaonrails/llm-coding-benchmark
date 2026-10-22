#!/usr/bin/env python3
"""Pod-side ownership tracking for a bounded model download process tree."""
import json
import subprocess
import sys
import time
from pathlib import Path
import b300_serve

b300_serve.STATE=Path('/root/logs/download-state.json')
if sys.argv[1]=='stop':
    b300_serve.stop()
elif sys.argv[1]=='start':
    stamp=sys.argv[2]
    if not stamp.isdigit():raise SystemExit('Invalid download identifier')
    if b300_serve.STATE.exists():
        old=json.loads(b300_serve.STATE.read_text())
        if b300_serve.identity(old['pid'])==old['start_ticks']:
            raise SystemExit('Previous download still running')
    log_path=Path('/root/logs')/f'download-{stamp}.log'
    with log_path.open('ab') as log:
        proc=subprocess.Popen(['bash','/root/download-model.sh'],stdin=subprocess.DEVNULL,
                              stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    state=dict(pid=proc.pid,start_ticks=b300_serve.identity(proc.pid),started_at=time.time(),log=str(log_path))
    b300_serve.STATE.write_text(json.dumps(state,indent=2))
    Path(f'/root/logs/download-{stamp}.pid').write_text(str(proc.pid))
else:
    raise SystemExit('Unknown operation')
