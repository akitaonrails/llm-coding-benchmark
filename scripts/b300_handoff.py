"""Apply an approved queue extension only after owned inference has stopped.

The old supervisor waits for this child. Replace that supervisor only after
validating its PID identity, stop-stage ownership, continuation and fresh lease.
Any failure leaves the existing watchdog fail-closed; never reset sprint budgets.
"""
import json
import os
import signal
import sys
import time
from pathlib import Path

from b300_batch_plan import build_batch
from b300_model_plan import build as build_model
from b300_supervisor import OUT, ROOT, renew, validate
from run_b300_campaign import process_identity


def continuation(campaign, completed_stage):
    if not completed_stage.endswith('-stop-server'):
        raise ValueError('Handoff requires a completed model stop stage')
    plan = build_batch(campaign)
    index = next(i for i, s in enumerate(plan['stages']) if s['id'] == completed_stage)
    plan['stages'] = plan['stages'][index+1:]
    validate(plan)
    return plan


def continuation_from_plan(plan, completed_stage):
    if not completed_stage.endswith('-stop-server'):
        raise ValueError('Handoff requires the model stop boundary')
    index=next(i for i,s in enumerate(plan['stages']) if s['id']==completed_stage)
    return dict(stages=plan['stages'][index+1:])


def append_recovery(plan, entries, prefix_label='r'):
    """One explicit bounded retry per entry, after the remaining first pass."""
    for index, entry in enumerate(entries):
        prefix = f'{prefix_label}{index:02d}-'
        for stage in plan['stages']:
            for edge in ('on_success', 'on_failure'):
                if not stage.get(edge):
                    # Only the prior final gate's skip or successful server stop
                    # may advance; an inability to stop inference stays fatal.
                    if (stage['id'].endswith('-gate') and edge == 'on_failure') or (stage['id'].endswith('-stop-server') and edge == 'on_success'):
                        stage[edge] = prefix+'resume'
        slug = entry['slug']; boundary = entry.get('boundary')
        cmd = lambda script,*args: [sys.executable,str(ROOT/'scripts'/script),*args]
        stages = [dict(id=prefix+'resume',argv=cmd('b300_resume_recovery.py',slug),timeout_seconds=60,on_success=prefix+'prepare'),
                  dict(id=prefix+'prepare',argv=cmd('b300_prepare_model.py',slug),timeout_seconds=6600,
                       on_success=prefix+(f'boundary-{boundary:02d}' if boundary else 'sprint-01'),on_failure=prefix+'pause')]
        if boundary:
            if entry.get('repair'):
                stages[1]['on_success']=prefix+'repair'
                stages.append(dict(id=prefix+'repair',argv=cmd('b300_run_repair.py',slug,f'{boundary:02d}'),
                                   timeout_seconds=720,on_success=prefix+f'boundary-{boundary:02d}',on_failure=prefix+'pause'))
            stages.append(dict(id=prefix+f'boundary-{boundary:02d}',argv=cmd('b300_boundary.py',slug,f'{boundary:02d}'),
                               timeout_seconds=960,on_success=prefix+f'sprint-{boundary+1:02d}',on_failure=prefix+'pause'))
        for stage in build_model(slug, boundary+1 if boundary else 1)['stages']:
            stage['id']=prefix+stage['id']
            for edge in ('on_success','on_failure'):
                if stage.get(edge):stage[edge]=prefix+stage[edge]
            if stage['id'].endswith(('archive-paused','archive-complete')):
                stage['on_success']=stage['on_failure']=prefix+'stop-server'
            stages.append(stage)
        stages.append(dict(id=prefix+'stop-server',argv=cmd('b300_stop_server.py'),timeout_seconds=180))
        plan['stages'].extend(stages)
    validate(plan)
    return plan


def maybe_handoff():
    request = OUT/'pending-extension.json'
    if not request.exists():
        return
    data = json.loads(request.read_text())
    parent = os.getppid()
    identity = process_identity(parent)
    if parent != data['supervisor_pid'] or not identity or identity[1] != data['start_ticks']:
        raise RuntimeError('Queue extension supervisor identity mismatch')
    state = json.loads((OUT/'status.json').read_text())
    if state.get('status') != 'starting' or not state.get('stage', '').endswith('-stop-server'):
        raise RuntimeError('Queue extension is only allowed at the stop boundary')
    campaign_path = ROOT/'config/b300_campaign.json'
    campaign = json.loads(campaign_path.read_text())
    for entry in data['queue_entries']:
        existing = next((q for q in campaign['queue'] if q['slug'] == entry['slug']), None)
        if existing is None:
            campaign['queue'].append(entry)
        elif existing != entry:
            raise RuntimeError('Conflicting queue entry')
    if data.get('source_plan'):
        source=json.loads(Path(data['source_plan']).read_text())
        plan=continuation_from_plan(source,state['stage'])
    else:
        plan=continuation(campaign,state['stage'])
    if not plan['stages'] and not data.get('recovery_entries'):
        raise RuntimeError('Nothing left to hand off')
    plan = append_recovery(plan, data.get('recovery_entries', []),data.get('recovery_prefix','r'))
    plan_path = OUT/f'extended-plan-{time.time_ns()}.json'
    plan_path.write_text(json.dumps(plan, indent=2)+'\n')
    tmp = campaign_path.with_suffix('.tmp')
    tmp.write_text(json.dumps(campaign, indent=2)+'\n'); tmp.replace(campaign_path)
    options_path = ROOT/'config/opencode.benchmark.json'
    options = json.loads(options_path.read_text())
    options['provider']['runpod-vllm']['models'].update(data['provider_models'])
    tmp = options_path.with_suffix('.tmp')
    tmp.write_text(json.dumps(options, indent=2)+'\n'); tmp.chmod(0o600); tmp.replace(options_path)
    # The stop child cannot return before replacement, so the parent cannot
    # advance to another stage. Renew immediately before the atomic takeover.
    renew('queue-extension-handoff', time.time()+120)
    current_identity = process_identity(parent)
    if not current_identity or current_identity[1] != identity[1] or current_identity[2] == 'Z':
        raise RuntimeError('Supervisor identity changed before handoff')
    receipt = dict(old_pid=parent, new_pid=os.getpid(), completed_stage=state['stage'],
                   plan=str(plan_path), time=time.time(), added=[q['slug'] for q in data['queue_entries']])
    (OUT/f'handoff-{time.time_ns()}.json').write_text(json.dumps(receipt, indent=2)+'\n')
    request.rename(request.with_name(f'applied-extension-{time.time_ns()}.json'))
    # SIGTERM would run the old supervisor's pod shutdown finally block. At this
    # verified idle boundary only, replace it without stopping the paid pod.
    os.kill(parent, signal.SIGKILL)
    for _ in range(100):
        current = process_identity(parent)
        if not current or current[2] == 'Z':
            break
        time.sleep(.05)
    else:
        raise RuntimeError('Old supervisor did not exit')
    os.execv(sys.executable, [sys.executable, str(ROOT/'scripts/b300_supervisor.py'), str(plan_path)])
