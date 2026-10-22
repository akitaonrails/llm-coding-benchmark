#!/usr/bin/env python3
"""Serial comparison queue: P1–P3, then FrontierSWE P4–P6."""
import argparse
import json
import subprocess
import sys
from run_v41_frontier import ROOT, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', choices=['sol_medium', 'genesys_repeat2', 'genesys_repeat3'], default='sol_medium')
    args = parser.parse_args()
    attempt = {'genesys_repeat2': 2, 'genesys_repeat3': 3}.get(args.model)
    slug = f'v41_genesys_house_repeat{attempt}' if attempt else 'v41_gpt_6_sol_medium'
    state_path = ROOT / 'results-v4.1' / (f'genesys-repeat{attempt}-queue.json' if attempt else 'sol-medium-queue.json')
    identity = ({'model': 'lua/genesys-pi-house', 'attempt': attempt,
                 'reason': 'Independent fresh attempt; preserve prior results'} if attempt else
                {'model': 'gpt-6-sol', 'reasoning_effort': 'medium'})
    try:
        for problem in ('raft', 'storage', 'typedlang'):
            write_json(state_path, {'status': 'running', 'task': problem, **identity})
            subprocess.run([sys.executable, str(ROOT / 'scripts/run_v41_wave.py'),
                            '--problem', problem, '--models', slug], cwd=ROOT, check=True)
            out = ROOT / 'results-v4.1'
            if problem != 'raft':
                out /= problem
            for phase in (out / slug / 'sprints').glob('*/*.result.json'):
                result = json.loads(phase.read_text())
                if result.get('exit_code') != 0:
                    raise RuntimeError(f'Sprint process failed; inspect {phase}')
            if not (out / slug / 'grade.json').exists():
                raise RuntimeError(f'Missing grade for {problem}')
        write_json(state_path, {'status': 'running', 'task': 'frontier P4–P6', **identity})
        subprocess.run([sys.executable, str(ROOT / 'scripts/run_v41_frontier_wave.py'),
                        '--models', args.model, '--cranelift-memory-mb', '32768'], cwd=ROOT, check=True)
        write_json(state_path, {'status': 'completed', **identity})
    except Exception as error:
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        write_json(state_path, {**state, 'status': 'error', 'error': str(error)})
        raise


if __name__ == '__main__':
    main()
