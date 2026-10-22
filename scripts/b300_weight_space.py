#!/usr/bin/env python3
"""Pod-local exact weight-only reclamation, with pinned provenance and plan/apply."""
import argparse
import json
import shutil
from pathlib import Path


def main():
    ap=argparse.ArgumentParser();ap.add_argument('slug');ap.add_argument('--apply',action='store_true');a=ap.parse_args()
    config=json.loads(Path('/root/campaign.json').read_text())
    revisions={x['slug']:x for x in json.loads(Path('/root/checkpoints.json').read_text())}
    q=next(x for x in config['queue'] if x['slug']==a.slug)
    required=int((q['size_gb']+25)*1e9)
    model_root=Path('/root/models')
    free=shutil.disk_usage(model_root).free
    existing=sum(p.stat().st_size for p in (model_root/q['local_dir']).glob('*.safetensors'))
    need=max(0,required-existing-free)
    plan=[]
    for other in config['queue']:
        if need<=0:break
        if other['slug']==a.slug:continue
        provenance=revisions[other['slug']]
        if provenance['repo']!=other['hf_repo'] or len(provenance['revision'])!=40:
            raise RuntimeError('Missing pinned provenance')
        directory=model_root/other['local_dir']
        for path in directory.glob('*.safetensors'):
            if path.is_symlink() or path.resolve().parent!=directory.resolve():continue
            size=path.stat().st_size
            plan.append(dict(path=str(path),bytes=size,**provenance));need-=size
    if need>0:raise RuntimeError('Insufficient safe-to-reclaim weight space')
    if not a.apply:
        Path('/root/logs/weight-removal-plan.json').write_text(json.dumps(plan,indent=2))
        print(json.dumps(plan))
        return
    saved=json.loads(Path('/root/logs/weight-removal-plan.json').read_text())
    if saved!=plan:raise RuntimeError('Removal plan changed; rearchive before applying')
    removed=[]
    for item in plan:
        Path(item['path']).unlink();removed.append(item)
    print(json.dumps(dict(removed=removed,free_bytes=shutil.disk_usage(model_root).free)))


if __name__=='__main__':main()
