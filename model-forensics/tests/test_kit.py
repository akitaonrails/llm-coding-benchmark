import copy
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import kit
from probes import build


class Fixture(BaseHTTPRequestHandler):
    responses = []
    requests = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        self.requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
        status, body, headers = self.responses.pop(0)
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body.encode())


def response(text='23', finish='stop', tokens=12):
    return json.dumps(dict(model='fixture', choices=[dict(message=dict(content=text), finish_reason=finish)],
                           usage=dict(prompt_tokens=tokens, completion_tokens=1)))


class KitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.patch = patch.object(kit, 'RUNS', Path(self.tmp.name) / 'runs')
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.config = json.loads((kit.ROOT / 'config.example.json').read_text())
        self.config['models'][0].update(label='a', key_env='FIXTURE_KEY')
        self.config['temperature'] = 0.7
        self.env = patch.dict(os.environ, FIXTURE_KEY='fixture-secret-not-real')
        self.env.start()
        self.addCleanup(self.env.stop)

    def plan(self, name='one', config=None):
        with redirect_stdout(io.StringIO()):
            m = kit.plan(config or self.config, name, 'pilot', 4101)
        return kit.run_path(name), m

    def serve(self, responses):
        Fixture.responses = responses
        Fixture.requests = []
        server = ThreadingHTTPServer(('127.0.0.1', 0), Fixture)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.config['models'][0]['base_url'] = f'http://127.0.0.1:{server.server_port}/v1'

    def test_frozen_schedule_and_family_holdout(self):
        path, m = self.plan()
        _, other = self.plan('two')
        self.assertEqual(m['schedule'], other['schedule'])
        self.assertEqual(m['probes'], build(4101))
        self.assertEqual(len(m['schedule']), len(m['probes'])*2)
        self.assertEqual(len({p['id'] for p in m['probes']}), len(m['probes']))
        for family in {p['family'] for p in m['probes']}:
            self.assertEqual(len({p['split'] for p in m['probes'] if p['family'] == family}), 1)
        m['probes'][0]['prompt'] = 'changed'
        (path/'manifest.json').write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError, 'integrity'):
            kit.load_manifest(path)

    def test_collection_redaction_resume_and_budget(self):
        self.serve([(200, response('fixture-secret-not-real'), {}), (200, response(), {})])
        path, m = self.plan()
        with redirect_stdout(io.StringIO()):
            kit.collect('one', 1)
            kit.collect('one', 1)
        rows = kit.read_records(path, m)
        self.assertEqual(len(rows), 2)
        self.assertNotIn('fixture-secret-not-real', (path/'responses.jsonl').read_text())
        self.assertEqual(rows[0]['text'], '[REDACTED]')
        self.assertEqual(len(Fixture.requests), 2)
        self.assertTrue(all(r['max_tokens'] == 256 and r['temperature'] == 0.7 for r in Fixture.requests))
        self.assertFalse((path/'pending.json').exists())

    def test_failures_not_retried_or_scored_as_answers(self):
        self.serve([(429, 'fixture-secret-not-real', {}), (200, 'broken JSON', {}),
                    (200, response(None), {}), (200, response('x', 'length'), {})])
        path, m = self.plan()
        with redirect_stdout(io.StringIO()):
            kit.collect('one')  # pauses at 429
        self.assertEqual(len(Fixture.requests), 1)
        with redirect_stdout(io.StringIO()):
            kit.collect('one')  # pauses at invalid JSON
            kit.collect('one', 2)
        rows = kit.read_records(path, m)
        self.assertEqual([r['status'] for r in rows], ['http_error', 'invalid_response', 'empty', 'truncated'])
        self.assertNotIn('fixture-secret-not-real', (path/'responses.jsonl').read_text())
        self.assertEqual(kit.distribution(rows, {'kind':'exact'}), {})

    def test_fixed_sampling_is_explicit_and_omitted(self):
        self.config['temperature'] = None
        kit.validate_config(self.config)
        body = kit.payload(self.config, self.config['models'][0], build()[0])
        self.assertNotIn('temperature', body)
        self.config['temperature'] = 0.7
        self.assertEqual(kit.payload(self.config, self.config['models'][0], build()[0])['temperature'], 0.7)

    def test_redirect_refused(self):
        self.serve([(302, '', {'Location':'http://127.0.0.1:1/stolen'})])
        p = build()[0]
        r = kit.request(self.config, self.config['models'][0], p, ['fixture-secret-not-real'])
        self.assertEqual(r['http_status'], 302)
        self.assertEqual(r['status'], 'http_error')

    def test_interrupted_request_not_replayed(self):
        path, m = self.plan()
        (path/'pending.json').write_text(json.dumps(m['schedule'][0]))
        with patch.object(kit, 'request', return_value={'status':'ok','text':'23'}), redirect_stdout(io.StringIO()):
            kit.collect('one', 1)
        rows = kit.read_records(path, m)
        self.assertEqual(rows[0]['status'], 'interrupted_unknown')
        self.assertEqual(rows[1]['request']['id'], 1)

    def test_integrity_and_code_change(self):
        path, m = self.plan()
        records = []
        kit.append_record(path, m, records, dict(request=m['schedule'][0], status='ok', text='a'))
        with patch.object(kit, 'code_hashes', return_value={}):
            with self.assertRaisesRegex(ValueError, 'code changed'):
                kit.load_manifest(path, check_code=True)
        f = path/'responses.jsonl'
        row = json.loads(f.read_text())
        row['text'] = 'forged'
        f.write_text(json.dumps(row)+'\n')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            kit.read_records(path, m)

    def test_duplicate_collection_lock(self):
        path, _ = self.plan()
        with kit.locked(path):
            with self.assertRaisesRegex(ValueError, 'lock'):
                with kit.locked(path):
                    pass

    def synthetic(self, name, opposite=False, token_offset=0):
        path, m = self.plan(name)
        records = []
        probes = {p['id']:p for p in m['probes']}
        for task in m['schedule']:
            p = probes[task['probe']]
            value = (p['options'][1 if opposite else 0] if p['kind'] == 'choice'
                     else p.get('expected', 'unused'))
            kit.append_record(path, m, records, dict(request=task, status='ok', text=value,
                usage={'prompt_tokens': token_offset + 10*p.get('multiplier', 1)}))
        return path

    def test_known_identical_and_opposite_fingerprints(self):
        a = self.synthetic('a')
        b = self.synthetic('b', token_offset=100)
        c = self.synthetic('c', opposite=True)
        result = kit.analyze([a,b,c])
        ab = next(x for x in result['comparisons'] if x['left']=='a:a' and x['right']=='b:a' and x['split']=='holdout')
        ac = next(x for x in result['comparisons'] if x['left']=='a:a' and x['right']=='c:a' and x['split']=='holdout')
        self.assertEqual(ab['metrics']['choice_tv']['mean'], 0)
        self.assertEqual(ab['metrics']['exact_agreement']['mean'], 1)
        self.assertEqual(ab['metrics']['shared_wrong_answer']['mean'], 0)
        self.assertEqual(ab['metrics']['token_delta_absolute_gap']['mean'], 0)
        self.assertEqual(ac['metrics']['choice_tv']['mean'], 1)
        with redirect_stdout(io.StringIO()):
            out = kit.report(['a', 'b', 'c'])
        self.assertIn('Origin unresolved', (out/'report.md').read_text())

    def test_missing_observations_and_settings_rejected(self):
        a, _ = self.plan('a')
        b, _ = self.plan('b')
        result = kit.analyze([a,b])
        self.assertEqual(result['comparisons'][0]['metrics'], {})
        self.assertFalse(result['coverage']['a:a']['complete'])
        c = copy.deepcopy(self.config)
        c['temperature'] = 0
        path, _ = self.plan('c', c)
        with self.assertRaisesRegex(ValueError, 'identical'):
            kit.analyze([a,path])

    def test_invalid_choices_do_not_create_false_agreement(self):
        rows = [{'status':'ok', 'text':'unlisted'}]
        self.assertEqual(kit.distribution(rows, {'kind':'choice', 'options':['a','b']}), {})
        self.assertEqual(kit.tv({'a':.5,'b':.5}, {'a':.5,'b':.5}), 0)
        self.assertEqual(kit.tv({'a':1}, {'b':1}), 1)

    def test_secret_urls_and_escape_paths_rejected(self):
        for url in ['https://user:pass@host/v1', 'https://host/v1?key=bad', 'http://remote/v1']:
            config = copy.deepcopy(self.config)
            config['models'][0]['base_url'] = url
            with self.assertRaises(ValueError):
                kit.validate_config(config)
        for name in ['../escape', '/tmp/escape', 'name/child']:
            with self.assertRaises(ValueError):
                kit.run_path(name)


if __name__ == '__main__':
    unittest.main()
