#!/usr/bin/env python3
"""Isolated, stdlib-only black-box collection. Python >=3.10, POSIX locking."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import random
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from probes import build

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / 'runs'
VERSION = 1


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def code_hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ('kit.py', 'probes.py', 'PLAN.md')}


def run_path(name):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', name):
        raise ValueError('Run name must be 1–80 letters, numbers, underscores or hyphens')
    path = RUNS / name
    if path.is_symlink() or (RUNS.exists() and RUNS.is_symlink()):
        raise ValueError('Run directories must not be symlinks')
    return path


def validate_config(c):
    if set(c) != {'schema', 'system', 'temperature', 'max_tokens', 'timeout_seconds', 'models'}:
        raise ValueError('Unknown or missing config fields; use config.example.json')
    if c['schema'] != 1 or not isinstance(c['system'], str):
        raise ValueError('Unsupported schema/system')
    if c['temperature'] is not None and (not isinstance(c['temperature'], (int, float)) or not 0 <= c['temperature'] <= 2):
        raise ValueError('temperature must be null (provider default) or 0..2')
    if type(c['max_tokens']) is not int or not 1 <= c['max_tokens'] <= 4096:
        raise ValueError('max_tokens must be 1..4096')
    if not isinstance(c['timeout_seconds'], (int, float)) or not 1 <= c['timeout_seconds'] <= 300:
        raise ValueError('timeout_seconds must be 1..300')
    if not isinstance(c['models'], list) or not c['models']:
        raise ValueError('At least one model is required')
    labels = set()
    for m in c['models']:
        if set(m) != {'label', 'base_url', 'model', 'key_env', 'revision_note'} or not all(isinstance(v, str) for v in m.values()):
            raise ValueError('Invalid model entry; keys belong in environment variables only')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', m['label']) or m['label'] in labels:
            raise ValueError('Model labels must be unique simple identifiers')
        labels.add(m['label'])
        u = urllib.parse.urlsplit(m['base_url'])
        if u.username or u.password or u.query or u.fragment or not u.hostname:
            raise ValueError('Endpoint must not contain credentials, query or fragment')
        if u.scheme != 'https' and not (u.scheme == 'http' and u.hostname in ('localhost', '127.0.0.1', '::1')):
            raise ValueError('HTTPS required except for loopback fixtures/local serving')
        if not re.fullmatch(r'[A-Z][A-Z0-9_]*', m['key_env']) or not m['model'].strip():
            raise ValueError('Invalid environment-variable name or model ID')


def plan(config, name, profile, seed):
    validate_config(config)
    probes = build(seed)
    replicates = {'pilot': 2, 'full': 20}[profile]
    rng = random.Random(seed)
    schedule = []
    # Every replicate contains all probes/models. Model order varies for each probe.
    for rep in range(replicates):
        for probe in rng.sample(probes, len(probes)):
            for model in rng.sample(config['models'], len(config['models'])):
                schedule.append(dict(id=len(schedule), probe=probe['id'], model=model['label'], replicate=rep))
    manifest = dict(schema=VERSION, created_at=now(), name=name, profile=profile, seed=seed,
                    replicates=replicates, config=config, probes=probes, schedule=schedule,
                    code=code_hashes(), python=sys.version, protocol='PLAN.md/v1')
    manifest['sha256'] = digest(manifest)
    path = run_path(name)
    path.mkdir(parents=True, exist_ok=False)
    source = path / 'source'
    source.mkdir()
    for filename in manifest['code']:
        (source / filename).write_bytes((ROOT / filename).read_bytes())
    (path / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(f"Planned {len(schedule)} requests; requested completion cap {len(schedule)*config['max_tokens']:,} tokens.")
    print(f"Frozen manifest: {path / 'manifest.json'}")
    return manifest


def load_manifest(path, check_code=False):
    m = json.loads((path / 'manifest.json').read_text())
    claimed = m.pop('sha256')
    if digest(m) != claimed:
        raise ValueError('Manifest integrity check failed')
    m['sha256'] = claimed
    if check_code and m['code'] != code_hashes():
        raise ValueError('Collector code changed since planning; use the frozen code or a new run')
    return m


def read_records(path, m):
    f = path / 'responses.jsonl'
    records = []
    previous = m['sha256']
    if not f.exists():
        return records
    for line in f.read_text().splitlines():
        r = json.loads(line)
        checksum = r.pop('sha256')
        if r.get('previous_sha256') != previous or digest(r) != checksum:
            raise ValueError('Response chain integrity check failed')
        r['sha256'] = checksum
        if len(records) >= len(m['schedule']) or r['request'] != m['schedule'][len(records)]:
            raise ValueError('Response sequence does not match frozen schedule')
        records.append(r)
        previous = checksum
    return records


def append_record(path, m, records, row):
    row['previous_sha256'] = records[-1]['sha256'] if records else m['sha256']
    row['sha256'] = digest(row)
    with (path / 'responses.jsonl').open('a') as f:
        f.write(canonical(row) + '\n')
        f.flush()
        os.fsync(f.fileno())
    records.append(row)


@contextmanager
def locked(path):
    with (path / '.lock').open('a') as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another collector holds this run lock') from None
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def redact(value, secrets):
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, '[REDACTED]')
        return value
    if isinstance(value, list):
        return [redact(v, secrets) for v in value]
    if isinstance(value, dict):
        return {redact(k, secrets): redact(v, secrets) for k, v in value.items()}
    return value


def payload(config, model, probe):
    body = dict(model=model['model'], messages=[{'role': 'system', 'content': config['system']},
                {'role': 'user', 'content': probe['prompt']}],
                max_tokens=config['max_tokens'], stream=False)
    if config['temperature'] is not None:
        body['temperature'] = config['temperature']
    return body


def request(config, model, probe, secrets):
    body = payload(config, model, probe)
    req = urllib.request.Request(model['base_url'].rstrip('/') + '/chat/completions',
        data=canonical(body).encode(), headers={'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + os.environ[model['key_env']]})
    started = time.monotonic()
    outcome = dict(status='transport_error', started_at=now(), request_sha256=digest(body))
    # No automatic HTTP redirects, proxy environment inheritance, retries or parameter fallback.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(req, timeout=config['timeout_seconds']) as response:
            outcome['http_status'] = response.status
            # Do not persist arbitrary headers, cookies, authentication or error bodies.
            outcome['headers'] = {k: response.headers[k] for k in
                ('content-type', 'x-request-id', 'request-id') if k in response.headers}
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                outcome['status'] = 'oversize_response'
            else:
                try:
                    d = json.loads(raw)
                    ch = d['choices'][0]
                    text = ch['message'].get('content')
                    finish = ch.get('finish_reason')
                    if text is not None and not isinstance(text, str):
                        raise TypeError()
                    outcome.update(text=text, finish_reason=finish,
                        usage=d.get('usage'), response_model=d.get('model'),
                        system_fingerprint=d.get('system_fingerprint'), logprobs=ch.get('logprobs'))
                    outcome['status'] = ('truncated' if finish == 'length' else
                        'empty' if not text else 'ok' if finish == 'stop' else 'nonstandard_finish')
                except (ValueError, KeyError, IndexError, TypeError, AttributeError):
                    outcome['status'] = 'invalid_response'
    except urllib.error.HTTPError as e:
        outcome.update(status='http_error', http_status=e.code)
        e.close()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        outcome['error_type'] = type(e).__name__
    outcome.update(elapsed_seconds=round(time.monotonic()-started, 6), finished_at=now())
    return redact(outcome, secrets)


def collect(name, limit=None):
    path = run_path(name)
    m = load_manifest(path, check_code=True)
    models = {x['label']: x for x in m['config']['models']}
    probes = {x['id']: x for x in m['probes']}
    for model in models.values():
        if not os.environ.get(model['key_env']):
            raise ValueError(f"Missing environment variable {model['key_env']}")
    secrets = [os.environ[x['key_env']] for x in models.values()]
    with locked(path):
        records = read_records(path, m)
        pending = path / 'pending.json'
        if pending.exists():
            p = json.loads(pending.read_text())
            if p['id'] == len(records):
                # Request may have reached the provider. Never replay it silently.
                if p != m['schedule'][len(records)]:
                    raise ValueError('Pending request does not match manifest')
                append_record(path, m, records, dict(request=p, status='interrupted_unknown', finished_at=now()))
            elif not records or p != records[-1]['request']:
                raise ValueError('Unexpected pending request')
            pending.unlink()
        remaining = m['schedule'][len(records):]
        if limit is not None:
            remaining = remaining[:limit]
        for task in remaining:
            with pending.open('w') as f:
                f.write(canonical(task))
                f.flush()
                os.fsync(f.fileno())
            result = request(m['config'], models[task['model']], probes[task['probe']], secrets)
            append_record(path, m, records, dict(request=task, **result))
            pending.unlink()
            print(f"{len(records)}/{len(m['schedule'])} {task['model']} {task['probe']} {result['status']}", flush=True)
            # Stop on credentials, throttling, incompatible requests, or infrastructure errors.
            # Resume explicitly to collect the next scheduled observation; failed rows remain.
            if result['status'] in ('http_error', 'transport_error', 'invalid_response', 'oversize_response'):
                print('Paused after a request failure. Inspect status; collect again to continue without retrying this observation.')
                break
    return records


def answer(text):
    # Preserve case, Unicode normalization, punctuation and interior whitespace.
    return text.strip()


def distribution(rows, probe):
    values = []
    for row in rows:
        if row['status'] != 'ok':
            continue
        a = answer(row['text'])
        # Invalid choices are missing for distance, counted explicitly in coverage.
        if probe['kind'] == 'choice' and a not in probe['options']:
            continue
        values.append(a)
    total = len(values)
    return {k: v/total for k, v in Counter(values).items()} if total else {}


def tv(a, b):
    return sum(abs(a.get(k, 0)-b.get(k, 0)) for k in a.keys() | b.keys()) / 2


def interval(values):
    """Equal-family mean and deterministic family bootstrap, descriptive only."""
    grouped = defaultdict(list)
    for family, value in values:
        grouped[family].append(value)
    means = [statistics.mean(x) for x in grouped.values()]
    if not means:
        return None
    result = dict(mean=statistics.mean(means), families=len(means), probes=len(values), interval95=None)
    if len(means) >= 3:
        rng = random.Random(741)
        sims = sorted(statistics.mean(rng.choices(means, k=len(means))) for _ in range(2000))
        result['interval95'] = [sims[49], sims[1949]]
    return result


def analyze(paths):
    loaded = [(p, load_manifest(p)) for p in paths]
    base = loaded[0][1]
    for _, m in loaded[1:]:
        if any(m[k] != base[k] for k in ('probes', 'profile', 'replicates', 'code')) or any(
                m['config'][k] != base['config'][k] for k in ('system', 'temperature', 'max_tokens')):
            raise ValueError('Comparison requires identical probes, profile, code and generation settings')
    panels, coverage, metadata, signatures = {}, {}, {}, {}
    for path, m in loaded:
        rows = read_records(path, m)
        for model in m['config']['models']:
            label = f"{m['name']}:{model['label']}"
            if label in panels:
                raise ValueError('Duplicate session/model')
            selected = [r for r in rows if r['request']['model'] == model['label']]
            grouped = defaultdict(list)
            for row in selected:
                grouped[row['request']['probe']].append(row)
            panels[label] = grouped
            invalid_choices = sum(r['status'] == 'ok' and answer(r['text']) not in p['options']
                for p in m['probes'] if p['kind'] == 'choice' for r in grouped[p['id']])
            coverage[label] = dict(planned=len(m['probes'])*m['replicates'], recorded=len(selected),
                statuses=dict(Counter(r['status'] for r in selected)), invalid_choices=invalid_choices,
                complete=len(selected) == len(m['probes'])*m['replicates'])
            metadata[label] = dict(model=model, manifest_sha256=m['sha256'], created_at=m['created_at'])
            signatures[label] = []
            for p in m['probes']:
                observations = grouped[p['id']]
                dist = distribution(observations, p)
                usable = sum(r['status'] == 'ok' and
                    (p['kind'] != 'choice' or answer(r['text']) in p['options']) for r in observations)
                counts = [r['usage']['prompt_tokens'] for r in observations
                    if isinstance(r.get('usage'), dict) and type(r['usage'].get('prompt_tokens')) is int]
                signatures[label].append(dict(probe=p['id'], family=p['family'], split=p['split'],
                    kind=p['kind'], observed=len(observations), usable=usable,
                    distribution=dist if p['kind'] != 'tokens' else None,
                    correct_fraction=dist.get(p['expected'], 0) if dist and 'expected' in p else None,
                    prompt_token_counts=counts if p['kind'] == 'tokens' else None))
    comparisons = []
    for left, right in itertools.combinations(panels, 2):
        for split in ('explore', 'holdout'):
            metrics = defaultdict(list)
            details = []
            for p in base['probes']:
                if p['split'] != split or p['kind'] == 'tokens':
                    continue
                a, b = distribution(panels[left][p['id']], p), distribution(panels[right][p['id']], p)
                if not a or not b:
                    continue
                if p['kind'] == 'choice':
                    v = tv(a, b)
                    metrics['choice_tv'].append((p['family'], v))
                    details.append(dict(probe=p['id'], metric='choice_tv', value=v))
                else:
                    agreement = sum(v*b.get(k, 0) for k, v in a.items())
                    wrong = sum(v*b.get(k, 0) for k, v in a.items() if k != p['expected'])
                    metrics['exact_agreement'].append((p['family'], agreement))
                    metrics['shared_wrong_answer'].append((p['family'], wrong))
                    details.append(dict(probe=p['id'], metric='exact_agreement', value=agreement,
                        shared_wrong_answer=wrong, left_correct=a.get(p['expected'], 0), right_correct=b.get(p['expected'], 0)))
            for family in sorted({p['family'] for p in base['probes'] if p['kind'] == 'tokens' and p['split'] == split}):
                pair = sorted([p for p in base['probes'] if p['family'] == family], key=lambda p:p['multiplier'])
                deltas = []
                for label in (left, right):
                    counts = []
                    for p in pair:
                        vals = [r.get('usage', {}).get('prompt_tokens') for r in panels[label][p['id']]
                            if isinstance(r.get('usage'), dict)]
                        vals = [v for v in vals if type(v) is int and v >= 0]
                        counts.append(statistics.median(vals) if vals else None)
                    deltas.append(counts[1]-counts[0] if None not in counts else None)
                if None not in deltas:
                    gap = abs(deltas[0]-deltas[1])
                    metrics['token_delta_absolute_gap'].append((family, gap))
                    details.append(dict(probe=family, metric='token_delta_absolute_gap', value=gap,
                                        left_delta=deltas[0], right_delta=deltas[1]))
            comparisons.append(dict(left=left, right=right, split=split,
                metrics={k: interval(v) for k, v in metrics.items()}, details=details))
    return dict(schema=VERSION, conclusion='Origin unresolved. Similarity is not ownership or ancestry proof.',
        profile=base['profile'], sampling={'requested_temperature': base['config']['temperature'],
            'limitation': 'Provider defaults/fixed sampling may differ; distributions are endpoint fingerprints, not controlled-temperature model comparisons.'
            if base['config']['temperature'] is None else 'Requested temperature may not guarantee identical sampling implementations.'},
        coverage=coverage, metadata=metadata, signatures=signatures, comparisons=comparisons)


def report(names):
    paths = [run_path(n) for n in names]
    result = analyze(paths)
    fingerprint = digest([load_manifest(p)['sha256'] for p in paths])[:12]
    # A new revision is generated as records accumulate; never overwrite a prior analysis.
    revision = digest(result)[:12]
    out = RUNS / f'report-{fingerprint}-{revision}'
    out.mkdir(exist_ok=True)
    (out / 'analysis.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    lines = ['# Model forensics report', '', result['conclusion'], '',
        f"Profile: **{result['profile']}**. Pilot results validate plumbing only; do not use for attribution.", '',
        f"Sampling: {result['sampling']['limitation']}", '',
        'Distances are descriptive. No candidate ranking or identity probability is assigned. '
        'Compare against same-model repeat sessions and documented controls. Missing, failed, '
        'empty and truncated outputs are not behavioral disagreement. Token counts are provider-reported.', '',
        '| Session:model | Recorded/planned | Status counts | Invalid choices |',
        '|---|---:|---|---:|']
    for name, c in result['coverage'].items():
        lines.append(f"| {name} | {c['recorded']}/{c['planned']} | {c['statuses']} | {c['invalid_choices']} |")
    for c in result['comparisons']:
        lines += ['', f"## {c['left']} vs {c['right']} — {c['split']}", '']
        if not c['metrics']:
            lines.append('Insufficient paired observations.')
        for metric, v in c['metrics'].items():
            ci = v['interval95']
            text = f"[{ci[0]:.4f}, {ci[1]:.4f}]" if ci else 'not estimated (<3 families)'
            lines.append(f"- {metric}: {v['mean']:.4f}; family-bootstrap 95% interval {text}; "
                         f"{v['probes']} probes in {v['families']} families.")
    lines += ['', '## Interpretation', '',
        '- choice_tv: 0 = matching empirical distributions; 1 = disjoint. Finite samples inflate distances.',
        '- exact_agreement: probability that independently drawn observed answers match. Correctness can explain high agreement.',
        '- shared_wrong_answer: probability of the same incorrect answer; common training data or task biases can explain it.',
        '- token_delta_absolute_gap: absolute difference between doubled-minus-base prompt-token counts. Zero only supports a shared tokenization pattern.',
        '- Intervals measure variation across this small set of probe families; they are not identity tests and do not account for all sampling or provider uncertainty.',
        '- Cross-session changes warrant replication and version checks; they do not establish routing.',
        '', 'See analysis.json for per-probe evidence and manifest hashes; see ../../README.md for the protocol.', '']
    (out / 'report.md').write_text('\n'.join(lines))
    print(out / 'report.md')
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('plan')
    p.add_argument('--config', type=Path, default=ROOT / 'config.example.json')
    p.add_argument('--name', required=True)
    p.add_argument('--profile', choices=('pilot', 'full'), default='pilot')
    p.add_argument('--seed', type=int, default=4101)
    p = sub.add_parser('collect')
    p.add_argument('name')
    p.add_argument('--limit', type=int)
    p = sub.add_parser('report')
    p.add_argument('names', nargs='+')
    p = sub.add_parser('status')
    p.add_argument('name')
    args = parser.parse_args()
    try:
        if args.command == 'plan':
            plan(json.loads(args.config.read_text()), args.name, args.profile, args.seed)
        elif args.command == 'collect':
            if args.limit is not None and args.limit < 1:
                raise ValueError('limit must be positive')
            collect(args.name, args.limit)
        elif args.command == 'report':
            report(args.names)
        else:
            path = run_path(args.name)
            m = load_manifest(path)
            rows = read_records(path, m)
            print(canonical(dict(recorded=len(rows), planned=len(m['schedule']),
                statuses=dict(Counter(r['status'] for r in rows)), pending=(path/'pending.json').exists(),
                last_finished_at=rows[-1].get('finished_at') if rows else None)))
    except (ValueError, OSError, KeyError) as e:
        # Exception messages are internal validation errors, never response bodies or auth values.
        if isinstance(e, OSError):
            print(f'Error: filesystem operation failed ({type(e).__name__})', file=sys.stderr)
        else:
            print(f'Error: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
