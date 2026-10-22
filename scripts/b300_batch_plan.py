#!/usr/bin/env python3
"""Assemble sequential model plans, preserving all grading boundaries."""
import json
import sys
from pathlib import Path
from b300_model_plan import build
from b300_supervisor import validate
from run_b300_campaign import CAMP, REPO


def build_batch(campaign):
    queue = list(campaign['queue'])
    fallback = next(q for q in queue if q.get('run_only_if_dnf'))
    queue.remove(fallback)
    parent = next(i for i,q in enumerate(queue) if q['slug'] == fallback['run_only_if_dnf'])
    queue.insert(parent+1, fallback)
    stages = []
    for index,q in enumerate(queue):
        slug=q['slug']; prefix=f'm{index:02d}-'
        next_id=f'm{index+1:02d}-gate' if index+1<len(queue) else None
        cmd=lambda name,*args:[sys.executable,str(REPO/'scripts'/name),*args]
        stages.append(dict(id=prefix+'gate',argv=cmd('b300_queue_gate.py',slug),
                           timeout_seconds=30,on_success=prefix+'prepare',on_failure=next_id))
        stages.append(dict(id=prefix+'prepare',
                           argv=cmd('b300_prepare_model.py',slug,*(['--already-downloaded'] if index==0 else [])),
                           timeout_seconds=6600,on_success=prefix+('sprint-02' if index==0 else 'sprint-01'),
                           on_failure=prefix+'pause'))
        for stage in build(slug, 2 if index==0 else 1)['stages']:
            stage['id']=prefix+stage['id']
            for key in ('on_success','on_failure'):
                if stage.get(key):stage[key]=prefix+stage[key]
            if stage['id'].endswith(('archive-paused','archive-complete')):
                stage['on_success']=prefix+'stop-server'
                stage['on_failure']=prefix+'stop-server'
            stages.append(stage)
        stages.append(dict(id=prefix+'stop-server',argv=cmd('b300_stop_server.py'),
                           timeout_seconds=180,on_success=next_id))
    plan=dict(stages=stages)
    validate(plan)
    return plan


def main():
    plan = build_batch(CAMP)
    path=REPO/'results-v4/_b300_campaign/supervisor/full-batch-plan.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(plan,indent=2)+'\n')
    print(f'Validated {len(plan["stages"])} bounded stages for {len(CAMP["queue"])} queue entries')


if __name__=='__main__':main()
