#!/usr/bin/env python3
"""Admit an already-running frozen recipe without restarting cold JIT work."""
import json
import shlex
import sys
import time
from pathlib import Path
import run_b300_campaign as c
from b300_remote import execute
from b300_prepare_model import local, EVIDENCE
from b300_tuning import probe_rate

slug=sys.argv[1]
started=float(sys.argv[2])
deadline=started+2700
q=next(q for q in c.CAMP['queue'] if q['slug']==slug)
state=json.loads(execute('cat /root/logs/serve-state.json').strip())
expected=[q.get('runtime_venv','/root/venv')+'/bin/vllm','serve','/root/models/'+q['local_dir'],
          '--served-model-name',q['served_name'],'--host','127.0.0.1','--port','8000',
          '--max-num-seqs','1',*shlex.split(q['serve_args'])]
if state['slug']!=slug or state['command_without_secrets']!=expected:
    raise SystemExit('Running server differs from frozen recipe')
remaining=lambda:max(1,int(deadline-time.time()))
marker=time.time()
rc=local(['b300_start_sprint.py',slug,'--preflight-only','--ready-timeout',str(max(1,remaining()-360))],remaining())
if rc:raise SystemExit(rc)
rc=local(['b300_perf_probe.py',slug,'--label','adopted-cold-start'],min(330,remaining()))
if rc:raise SystemExit(rc)
def latest(pattern):
    return max((p for p in EVIDENCE.glob(pattern) if p.stat().st_mtime>=marker),key=lambda p:p.stat().st_mtime)
probe=latest(f'perf-{slug}-adopted-cold-start-*.json')
pre=latest(f'preflight-{slug}-*.json')
rate=probe_rate(json.loads(probe.read_text()))
card=c.LEDGER_DIR/'model-cards'/f'{slug}.md'
record=dict(passed=rate>=100 and time.time()<=deadline,
            tool_preflight_passed=json.loads(pre.read_text()).get('passed') is True,
            decode_tokens_per_second=rate,serving_fingerprint=c.serving_fingerprint(slug),
            evidence=[str(p.relative_to(c.REPO)) for p in (probe,pre,card)],
            original_tuning_started_at=started,deadline=deadline,
            note='Existing server adopted without restart; cold compilation retained; original 45-minute wall limit retained.')
record['passed']=record['passed'] and record['tool_preflight_passed']
dest=c.LEDGER_DIR/'performance-validation'/f'{slug}.json'
if dest.exists():dest.rename(dest.with_name(f'{slug}-prior-{time.time_ns()}.json'))
dest.write_text(json.dumps(record,indent=2)+'\n')
c.annotate(slug,'serve_load',time.time()-started,c.load_ledger())
print(json.dumps({'slug':slug,'passed':record['passed'],'decode_tokens_per_second':rate}),flush=True)
raise SystemExit(0 if record['passed'] else 2)
