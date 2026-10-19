import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import supervise


class SupervisorTests(unittest.TestCase):
    def run_case(self, outcomes, initial=None):
        rows = list(initial or [])
        manifest = {'schedule': list(range(len(rows) + len(outcomes)))}
        def collect(command):
            rows.append(outcomes.pop(0))
            return SimpleNamespace(returncode=0)
        with TemporaryDirectory() as tmp, patch.object(sys, 'argv', ['supervise', 'fixture']), \
             patch.object(supervise.kit, 'run_path', return_value=Path(tmp)), \
             patch.object(supervise.kit, 'load_manifest', return_value=manifest), \
             patch.object(supervise.kit, 'read_records', side_effect=lambda *a: list(rows)), \
             patch.object(supervise.subprocess, 'run', side_effect=collect) as calls, \
             patch.object(supervise.time, 'sleep') as sleep, \
             patch.object(supervise.kit, 'report') as report:
            supervise.main()
            return rows, calls.call_count, [c.args[0] for c in sleep.call_args_list], report.call_count

    def test_cooldown_does_not_retry_failed_observation(self):
        rows, calls, sleeps, reports = self.run_case([{'status':'ok'}], [{'status':'http_error','http_status':429}])
        self.assertEqual(len(rows), 2)
        self.assertEqual(calls, 1)
        self.assertEqual(sleeps, [60,3])
        self.assertEqual(reports, 1)

    def test_other_http_errors_stop(self):
        with self.assertRaisesRegex(RuntimeError, 'Non-rate-limit'):
            self.run_case([{'status':'http_error','http_status':401}])

    def test_repeated_rate_limits_stop(self):
        with self.assertRaisesRegex(RuntimeError, 'Three consecutive'):
            self.run_case([{'status':'http_error','http_status':429} for _ in range(3)])

    def test_isolated_malformed_response_kept_without_retry(self):
        rows, calls, sleeps, reports = self.run_case([
            {'status':'invalid_response', 'request':{'model':'reference'}},
            {'status':'ok', 'request':{'model':'reference'}}])
        self.assertEqual(calls, 2)
        self.assertEqual(rows[0]['status'], 'invalid_response')
        self.assertEqual(reports, 1)

    def test_malformed_endpoint_streak_across_interleaved_models(self):
        with self.assertRaisesRegex(RuntimeError, 'Three consecutive malformed'):
            self.run_case([
                {'status':'invalid_response', 'request':{'model':'bad'}},
                {'status':'ok', 'request':{'model':'good'}},
                {'status':'invalid_response', 'request':{'model':'bad'}},
                {'status':'ok', 'request':{'model':'good'}},
                {'status':'invalid_response', 'request':{'model':'bad'}}])
