#!/usr/bin/env python3
"""Wait for bounded restore, then transfer to the durable full-batch supervisor."""
import json
import os
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'results-v4/_b300_campaign'
status=OUT/'migration-20261017/restore-status.json'
deadline=time.time()+3600
while time.time()<deadline:
    data=json.loads(status.read_text()) if status.exists() else {}
    if data.get('status','').endswith('\n0'):
        # The restore monitor archives its log and hands off a short lease after
        # writing readiness. Wait for that process to exit before taking ownership.
        time.sleep(45)
        model=ROOT/'results-v4/v2_glm_5_3_flash_oss'
        if (model/'DNF').exists():raise SystemExit('GLM unexpectedly marked DNF; preserve for review')
        paused=model/'PAUSED'
        if paused.exists():
            archive=model/'pause-checkpoints'/f'resume-{time.time_ns()}'
            archive.mkdir()
            paused.rename(archive/'PAUSED')
            (archive/'authorization.json').write_text(json.dumps({'at':time.time(),'reason':'User explicitly authorized full-batch continuation and supplied new SSH. Original budget retained.'},indent=2)+'\n')
        script=ROOT/'scripts/b300_supervisor.py'
        os.execv(sys.executable,[sys.executable,str(script),str(OUT/'supervisor/full-batch-plan.json')])
    if data.get('status','').endswith('\n1'):
        raise SystemExit('Restore failed; billing watchdog/restore monitor handles stop')
    time.sleep(10)
raise SystemExit('Restore readiness deadline exceeded')
