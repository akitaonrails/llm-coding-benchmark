#!/usr/bin/env python3
"""Pace a frozen collection; retain failed observations, never retry them."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
import kit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    args = parser.parse_args()
    path = kit.run_path(args.name)
    m = kit.load_manifest(path, check_code=True)
    consecutive_limits = 0
    with (path / '.supervisor.lock').open('a') as lock:
        kit.fcntl.flock(lock, kit.fcntl.LOCK_EX | kit.fcntl.LOCK_NB)
        while True:
            rows = kit.read_records(path, m)
            if len(rows) == len(m['schedule']):
                print('Collection complete; generating report.', flush=True)
                kit.report([args.name])
                return
            if rows and rows[-1].get('http_status') == 429:
                print('Rate limit: cooling down 60 seconds; failed observation will not be retried.', flush=True)
                time.sleep(60)
            before = len(rows)
            result = subprocess.run([sys.executable, str(Path(kit.__file__)), 'collect', args.name, '--limit', '1'])
            rows = kit.read_records(path, m)
            if result.returncode or len(rows) <= before:
                raise RuntimeError('Collector failed or made no progress; inspect logs')
            latest = rows[-1]
            consecutive_limits = consecutive_limits + 1 if latest.get('http_status') == 429 else 0
            if consecutive_limits >= 3:
                raise RuntimeError('Three consecutive rate limits; stopping for diagnosis')
            if latest['status'] in ('transport_error', 'oversize_response') or (
                latest['status'] == 'http_error' and latest.get('http_status') != 429):
                raise RuntimeError('Non-rate-limit collection failure; stopping for diagnosis')
            if latest['status'] == 'invalid_response':
                model = latest['request']['model']
                history = [r for r in rows if r.get('request', {}).get('model') == model]
                if len(history) >= 3 and all(r['status'] == 'invalid_response' for r in history[-3:]):
                    raise RuntimeError('Three consecutive malformed responses from one endpoint; stopping for diagnosis')
                print(f'{model}: malformed observation preserved; continuing without retry.', flush=True)
            time.sleep(3)


if __name__ == '__main__':
    main()
