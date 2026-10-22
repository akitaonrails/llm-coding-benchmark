#!/usr/bin/env python3
"""Publish live stage status outside the benchmark's temporary answer shield."""
import json
import os
import time
from pathlib import Path
from run_b300_campaign import process_identity

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'results-v4/_b300_campaign/supervisor'
PUBLIC=Path('/tmp/b300-batch-status.json')


def main():
    os.umask(0o077)
    controller=json.loads((OUT/'active-supervisor.json').read_text())
    pid=controller['pid'];identity=process_identity(pid)
    if not identity:raise SystemExit('Supervisor is not live')
    plan=json.loads(Path(controller.get('plan', OUT/'full-batch-adopted-plan.json')).read_text())
    models={s['id'].split('-')[0]:s['argv'][2] for s in plan['stages'] if s['id'].endswith(('-gate', '-prepare'))}
    state={};started=None
    # Keep the open inode while the containing directory is moved by shielding.
    with (OUT/'events.ndjson').open() as stream:
        while True:
            while True:
                pos=stream.tell();line=stream.readline()
                if not line:break
                try:event=json.loads(line)
                except ValueError:
                    stream.seek(pos);break
                state=event
                if event.get('status')=='starting':started=event['time']
            now=time.time();current=process_identity(pid)
            if (OUT/'active-supervisor.json').exists() and json.loads((OUT/'active-supervisor.json').read_text())['pid'] != pid:
                return
            alive=bool(current and current[1]==identity[1] and current[2]!='Z')
            stage=state.get('stage','unknown')
            status=dict(updated_at=now,supervisor_pid=pid,supervisor_alive=alive,
                        model=models.get(stage.split('-')[0]),stage=stage,
                        state=state.get('status'),
                        stage_elapsed_seconds=round(now-started) if started else None,
                        last_transition_at=state.get('time'),
                        note='Stage time includes preparation/review; this is not the cumulative sprint budget.')
            tmp=PUBLIC.with_suffix('.tmp');tmp.write_text(json.dumps(status,indent=2)+'\n');tmp.replace(PUBLIC)
            if not alive:return
            time.sleep(5)


if __name__=='__main__':main()
