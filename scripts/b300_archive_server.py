#!/usr/bin/env python3
"""Preserve a secret-free owned RunPod launch manifest, server log and GPU sample."""
import argparse,hashlib,json,re,time
from pathlib import Path
from b300_remote import execute
ROOT=Path(__file__).resolve().parent.parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('slug');ap.add_argument('--label',required=True);a=ap.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_.-]+',a.label):raise ValueError('Invalid archive label')
    raw=execute('test ! -f /root/logs/serve-state.json || cat /root/logs/serve-state.json').strip()
    if not raw:
        print('No inference launch exists to archive; setup evidence remains local')
        return
    state=json.loads(raw)
    if state['slug']!=a.slug:
        live=json.loads(execute('python3 /root/b300_serve.py status').strip())
        if live.get('alive'):
            raise RuntimeError('Active server belongs to a different model')
        print('Requested model never launched; previous server is stopped')
        return
    log=state['log']
    if not re.fullmatch(r'/root/logs/[a-zA-Z0-9_.-]+',log):raise ValueError('Unexpected log path')
    out=ROOT/'results-v4/_b300_campaign/migration-20261017'/f'server-{a.label}-{time.time_ns()}'
    out.mkdir(mode=0o700)
    (out/'serve-state.json').write_text(json.dumps(state,indent=2)+'\n')
    (out/'server.log').write_text(execute('cat '+log,timeout=60))
    (out/'gpu.csv').write_text(execute('nvidia-smi --query-gpu=name,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw,power.limit --format=csv'))
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}
    (out/'sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for p in out.iterdir():p.chmod(0o600)
    print(str(out))
if __name__=='__main__':
    for attempt in range(3):
        try:
            main()
            break
        except RuntimeError:
            if attempt==2:raise
            time.sleep(2)

