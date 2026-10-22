#!/usr/bin/env python3
"""Build a bounded sprint/boundary plan for an already admitted running model.

Model download, restore, card review, tuning and watchdog deployment must finish
before this plan is launched. Failure always archives and checkpoints the model;
after that the supervisor stops the pod rather than awaiting another chat turn.
"""
import argparse
import json
import sys
from pathlib import Path
from run_b300_campaign import CAMP, REPO
from b300_supervisor import validate

SPRINTS = ['01_foundation', '02_multiuser', '03_admin', '04_reports',
           '05_api', '06_production', '07_reveal']


def build(slug, first):
    def cmd(script, *args):
        return [sys.executable, str(REPO / 'scripts' / script), *args]
    stages = []
    for i in range(first - 1, 7):
        sprint = SPRINTS[i]
        review = f'boundary-{i+1:02d}'
        stages.append(dict(id=f'sprint-{i+1:02d}',
                           argv=cmd('b300_start_sprint.py', slug, '--sprint', sprint),
                           timeout_seconds=14400, on_success=review, on_failure='pause'))
        stages.append(dict(id=review, argv=cmd('b300_boundary.py', slug, f'{i+1:02d}'),
                           timeout_seconds=960,
                           on_success=f'sprint-{i+2:02d}' if i < 6 else 'archive-complete',
                           on_failure='pause'))
    stages.extend([
        dict(id='pause', argv=cmd('b300_pause.py', slug, '--reason',
                                 'Automatic supervisor: sprint or boundary failed; preserve for batch review'),
             timeout_seconds=300, on_success='archive-paused', on_failure='archive-paused'),
        dict(id='archive-paused', argv=cmd('b300_archive_server.py', slug, '--label', 'automatic-paused'),
             timeout_seconds=240),
        dict(id='archive-complete', argv=cmd('b300_archive_server.py', slug, '--label', 'automatic-complete'),
             timeout_seconds=240)])
    plan = dict(slug=slug, requires='running admitted model and deployed watchdog', stages=stages)
    validate(plan)
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug', choices=[q['slug'] for q in CAMP['queue']])
    ap.add_argument('--first-sprint', type=int, choices=range(1, 8), default=1)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(build(a.slug, a.first_sprint), indent=2) + '\n')
    print('Plan written; no execution started')


if __name__ == '__main__':
    main()
