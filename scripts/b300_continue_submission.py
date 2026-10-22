"""Resume an explicitly authorized incomplete submission; preserve original sprints."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import run_b300_campaign as campaign
from b300_progress import ProgressWatch
from run_v4_sprint import PROMPTS

# These candidates stopped for ordinary implementation deficiencies, not a
# review-service security rejection. Never use this entry point to evade one.
CONTINUATIONS = {'v2_nex_n2_5_mini_oss': ('01_foundation',),
                 'v2_command_a_plus_oss': ('02_multiuser', '03_admin')}


def main():
    slug = sys.argv[1]
    allowed = CONTINUATIONS[slug]
    sprint = sys.argv[2] if len(sys.argv) > 2 else allowed[0]
    if sprint not in allowed:
        raise ValueError('Continuation is not authorized for this boundary')
    diagnostic_recovery = '--diagnostic-recovery' in sys.argv[3:]
    if diagnostic_recovery and (slug, sprint) != ('v2_command_a_plus_oss', '03_admin'):
        raise ValueError('The additional ordinary-defect recovery is Command admin only')
    if not campaign.CAMP.get('billing_safety', {}).get('paid_execution_enabled'):
        raise RuntimeError('Paid execution is disabled')
    if not campaign.performance_validated(slug):
        raise RuntimeError('Fresh performance and tool admission required')
    root = campaign.OUT / slug
    tag = f'continuation{sprint[:2]}_{time.time_ns()}'
    records = root / 'assistance'
    records.mkdir(exist_ok=True)
    if len(list(records.glob('*.json'))) >= (3 if diagnostic_recovery else 2):
        raise RuntimeError('Assistance limit reached; preserve for explicit review')
    # Repeat only the original task plus ordinary completion criteria. No hidden
    # grading material, injection targets or reviewer reasoning enter this prompt.
    prompt = (PROMPTS / f'sprint{sprint}.txt').read_text()
    prompt += ('\n\nContinue your existing implementation of the task above. '
               'Complete missing functionality, fix syntax and boot errors, run '
               'the relevant tests, and commit your changes. Use the existing '
               'workspace; do not discard its history. Verify the application '
               'actually starts and its documented user flow is usable.\n')
    if sprint == '03_admin':
        prompt += ('Your previous attempt repeatedly rewrote identical files and '
                   'did not complete the task. Inspect the current files before '
                   'editing; preserve complete Ruby classes rather than replacing '
                   'a file with a method fragment. Check syntax, exercise the '
                   'routes required by the original task, and run the actual test '
                   'command. Diagnose each concrete failure before another edit. '
                   'Do not claim a commit or test succeeded unless its command '
                   'did succeed. Keep server checks bounded so a foreground '
                   'server does not block your work.\n')
    if diagnostic_recovery:
        prompt += ('Concrete ordinary failures still need correction: running '
                   '`ruby -c app/controllers/application_controller.rb` reports '
                   'an unexpected end near line 32. Inspect the whole class and '
                   'fix its structure. The test setup does not execute tests; '
                   'make the selected test framework load the Rails environment '
                   'and run the actual model and feature tests required above. '
                   'Use paths under your current project directory, check each '
                   'changed Ruby file with ruby -c, and verify eager loading with '
                   '`RAILS_ENV=test bundle exec rails runner "Rails.application.eager_load!"`. '
                   'Finish the original task and verify your git commit succeeds.\n')
    record = records / f'{tag}.json'
    record.write_text(json.dumps({'sprint': tag, 'classification': 'assisted',
        'prompt': prompt, 'issued_at': time.time(),
        'reason': '2026-10-19 user authorized further attempts at incomplete implementations',
        'additional_diagnostic_recovery': diagnostic_recovery,
        'policy_exception': ('Third nudge: latest instruction to push past fixable failures interpreted as authorization for one concrete ordinary syntax/test recovery' if diagnostic_recovery else None),
        'timing': 'No elapsed cap; retains loop diagnosis and original cumulative accounting'}, indent=2)+'\n')
    archive = root / 'pause-checkpoints' / tag
    archive.mkdir(parents=True)
    for name in ('PAUSED', 'DNF', 'RESUME.md', 'TIME_GUARD.md'):
        path = root / name
        if path.exists():
            path.rename(archive / name)
    ledger = campaign.load_ledger()
    entry = campaign.entry(ledger, slug)
    start = time.time()
    proc = subprocess.Popen([sys.executable, str(campaign.REPO/'scripts/run_v4_sprint.py'),
        '--model', slug, '--sprint', sprint, '--repair-prompt', str(record),
        '--repair-tag', tag], env=dict(os.environ, V4_PHASE_TIMEOUT='0'), start_new_session=True)
    watch = ProgressWatch(root/'project', root/'repairs'/tag/f'{tag}.ndjson')
    reason = None
    try:
        while proc.poll() is None:
            reason = watch.check()
            if reason:
                campaign.stop_sprint_tree(proc)
                break
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
    finally:
        if proc.poll() is None:
            campaign.stop_sprint_tree(proc)
        elapsed = time.time()-start
        entry['sprint_seconds_total'] += elapsed
        entry['sprints'][tag] = {'seconds': elapsed, 'exit': proc.returncode,
                                 'assisted': True, 'reason': reason}
        entry['model_time_cost_usd'] = campaign.usd(entry['sprint_seconds_total'])
        campaign.save_ledger(ledger)
        (archive/'continuation.json').write_text(json.dumps(entry['sprints'][tag], indent=2)+'\n')
    # A nonzero CLI exit is not a quality verdict; the independent boundary
    # examines the preserved submission. A loop pause requires diagnosis first.
    return 2 if reason else 0


if __name__ == '__main__':
    raise SystemExit(main())
