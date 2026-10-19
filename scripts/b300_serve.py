#!/usr/bin/env python3
"""Run on the pod: start/stop only the recorded campaign vLLM process."""
import json
import os
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path

STATE = Path('/root/logs/serve-state.json')


def identity(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()
        return None if fields[0] == 'Z' else fields[19]
    except FileNotFoundError:
        return None


def stop():
    if not STATE.exists():
        return
    s = json.loads(STATE.read_text())
    pid = s['pid']
    if identity(pid) != s['start_ticks']:
        return
    os.killpg(pid, signal.SIGTERM)
    for _ in range(30):
        if identity(pid) != s['start_ticks']:
            return
        time.sleep(1)
    if identity(pid) == s['start_ticks']:
        os.killpg(pid, signal.SIGKILL)


def main():
    if sys.argv[1] == 'status':
        state = json.loads(STATE.read_text()) if STATE.exists() else {}
        alive = bool(state and identity(state['pid']) == state['start_ticks'])
        print(json.dumps({'alive': alive, 'slug': state.get('slug')}))
        return
    if sys.argv[1] == 'stop':
        stop()
        return
    campaign = json.loads(Path('/root/campaign.json').read_text())
    if not campaign.get('billing_safety', {}).get('paid_execution_enabled', False):
        raise RuntimeError('Paid execution blocked until independent billing watchdog and persistent supervisor are verified')
    q = next(q for q in campaign['queue']
             if q['slug'] == sys.argv[1])
    if STATE.exists():
        s = json.loads(STATE.read_text())
        if identity(s['pid']) == s['start_ticks']:
            raise RuntimeError('Recorded server still running; stop explicitly before replacement')
    env = os.environ.copy()
    env['VLLM_API_KEY'] = Path('/root/.vllm_key').read_text().strip()
    venv = q.get('runtime_venv', '/root/venv')
    cuda = q.get('cuda_home', '/usr/local/cuda-12.9')
    env['CUDA_HOME'] = cuda
    env['PATH'] = venv + '/bin:' + cuda + '/bin:' + env['PATH']
    env['VLLM_ENGINE_READY_TIMEOUT_S'] = '3600'
    cmd = [venv + '/bin/vllm', 'serve', '/root/models/' + q['local_dir'],
           '--served-model-name', q['served_name'], '--host', '127.0.0.1', '--port', '8000',
           '--max-num-seqs', '1', *shlex.split(q['serve_args'])]
    log_path = Path('/root/logs') / f'{q["slug"]}-serve-{time.time_ns()}.log'
    with log_path.open('ab') as log:
        p = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL,
                             stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    state = {'slug': q['slug'], 'pid': p.pid, 'start_ticks': identity(p.pid),
             'started_at': time.time(), 'log': str(log_path), 'command_without_secrets': cmd}
    STATE.write_text(json.dumps(state, indent=2))
    print(json.dumps({'slug': q['slug'], 'pid': p.pid, 'log': str(log_path)}))


if __name__ == '__main__':
    main()
