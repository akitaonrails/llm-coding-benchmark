#!/usr/bin/env python3
"""Read-only campaign reporting; hourly local reports and desktop notifications."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = Path('/tmp/b300-hourly-status.md')
LOCK = Path('/tmp/b300-hourly-status.lock')


def locate(relative):
    direct = ROOT / relative
    if direct.exists():
        return direct
    for shield in ROOT.parent.glob('.v4shield_*'):
        candidate = shield / relative.replace('results-v4/', 'results/', 1)
        if candidate.exists():
            return candidate
    raise FileNotFoundError(relative)


def identity(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return fields[19] if fields[0] != 'Z' else None
    except FileNotFoundError:
        return None


def report(controller, notify=False):
    campaign = locate('results-v4/_b300_campaign')
    status = json.loads((campaign / 'supervisor/status.json').read_text())
    plan = json.loads(locate('results-v4/_b300_campaign/supervisor/' + Path(controller['plan']).name).read_text())
    stages = plan['stages']
    stage = status.get('stage', 'supervisor exited')
    alive = identity(controller['pid']) == str(controller['start_ticks'])
    index = next((i for i, s in enumerate(stages) if s['id'] == stage), len(stages))
    pending = []
    for s in stages[index:]:
        for arg in s['argv']:
            if arg.startswith('v2_') and arg not in pending:
                pending.append(arg)
    ledger = json.loads((campaign / 'ledger.json').read_text())
    now = time.time()
    lines = ['# B300 hourly status', '', time.strftime('%Y-%m-%d %H:%M:%S %Z'), '',
             f'Supervisor: {"running" if alive else "stopped"}; stage: {stage}.',
             f'Last stage event: {round((now-status["time"])/60, 1)} minutes ago.', '',
             'Remaining queue (including current model): ' + (', '.join(pending) or 'none') + '.', '',
             '| Model | Sprints executed | State | Completed sprint minutes |',
             '|---|---:|---|---:|']
    queue = json.loads((ROOT / 'config/b300_campaign.json').read_text())['queue']
    for model in queue:
        slug = model['slug']
        try:
            directory = locate('results-v4/' + slug)
        except FileNotFoundError:
            continue
        count = len(list((directory / 'sprints').glob('*/sprint.result.json')))
        paused = directory / 'PAUSED'
        verdicts = list((directory / 'boundaries').glob('sprint07-*/verdict.json'))
        complete = any(json.loads(p.read_text()).get('eligible') is True for p in verdicts)
        if pending and slug == pending[0] and alive:
            state = 'active: ' + stage
        elif slug in pending and alive:
            state = 'queued recovery / execution'
        elif paused.exists():
            state = paused.read_text().splitlines()[0].replace('|', '/')
        else:
            state = 'completed' if complete else 'partial / pending review'
        minutes = ledger.get('models', {}).get(slug, {}).get('sprint_seconds_total', 0) / 60
        lines.append(f'| {slug} | {count}/7 | {state} | {minutes:.1f} |')
    lines += ['', 'Sprint counts are execution counts, not scores. Completed sprint minutes exclude active work and setup/review time.',
              'Supervisor exit does not independently prove provider billing has stopped.']
    body = '\n'.join(lines) + '\n'
    folder = campaign / 'hourly-reports'
    folder.mkdir(exist_ok=True)
    (folder / f'{int(now)}.md').write_text(body)
    temp = PUBLIC.with_suffix('.tmp')
    temp.write_text(body)
    temp.replace(PUBLIC)
    if notify:
        message = f'{stage}; supervisor {"running" if alive else "stopped"}. Remaining models: {len(pending)}. Report: {PUBLIC}'
        try:
            options = [] if alive else ['--urgency=critical', '--expire-time=0',
                                         '--hint=boolean:resident:true']
            title = 'B300 benchmark progress' if alive else 'B300 BATCH STOPPED — review final status'
            result = subprocess.run(['notify-send', *options, title, message], timeout=10)
            print(f'notification_exit={result.returncode}', flush=True)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f'notification_failed={type(exc).__name__}', flush=True)
    print(f'report={PUBLIC} supervisor_alive={alive}', flush=True)
    return alive


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--notify', action='store_true')
    args = parser.parse_args()
    os.umask(0o077)
    with LOCK.open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            # The existing reporter follows supervisor handoffs itself.
            return
        controller = json.loads((locate('results-v4/_b300_campaign') / 'supervisor/active-supervisor.json').read_text())
        next_report = 0
        while True:
            try:
                latest = json.loads((locate('results-v4/_b300_campaign') / 'supervisor/active-supervisor.json').read_text())
                if latest != controller and identity(latest['pid']) == str(latest['start_ticks']):
                    controller = latest
                    next_report = 0
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            alive = identity(controller['pid']) == str(controller['start_ticks'])
            if time.monotonic() >= next_report or not alive:
                try:
                    report(controller, args.notify)
                    next_report = time.monotonic() + 3600
                except (FileNotFoundError, json.JSONDecodeError):
                    # A shield rename or atomic stage transition can race a read.
                    if args.once:
                        raise
                if args.once or not alive:
                    return
            time.sleep(30)


if __name__ == '__main__':
    main()
