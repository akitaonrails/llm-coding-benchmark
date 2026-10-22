"""Regression checks for campaign eligibility and actual sprint outcomes."""
import json
import tempfile
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
import run_b300_campaign as campaign


class CampaignTest(unittest.TestCase):
    def test_null_budget_preserves_execution_after_old_four_hour_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'config').mkdir()
            (root/'config/b300_campaign.json').write_text(json.dumps({'guard': {'per_model_sprint_budget_seconds': None}}))
            proc = Mock()
            proc.wait.return_value = 0
            with patch.object(campaign, 'REPO', root), patch.object(campaign.time, 'time', return_value=50000):
                self.assertEqual(campaign.current_budget(), float('inf'))
                self.assertEqual(campaign.wait_with_live_budget(proc, 20000, 0), 0)
            proc.wait.assert_called_once_with(timeout=5)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.override = patch.object(campaign, 'OUT', self.root)
        self.override.start()
        self.addCleanup(self.override.stop)

    def test_wrapper_success_does_not_mask_model_failure(self):
        result = self.root / 'model/sprints/sprint01_foundation/sprint.result.json'
        result.parent.mkdir(parents=True)
        result.write_text(json.dumps({'exit_code': 1}))
        actual = campaign.record_result('model', '01_foundation', 0)
        self.assertEqual(actual['exit'], 1)
        self.assertEqual(actual['status'], 'failed')
        self.assertEqual(actual['wrapper_exit'], 0)

    def test_missing_result_is_failure_even_if_wrapper_succeeded(self):
        actual = campaign.record_result('model', '01_foundation', 0)
        self.assertEqual(actual['exit'], 1)
        self.assertEqual(actual['status'], 'missing_result')

    def test_stalled_success_is_not_complete(self):
        result = self.root / 'model/sprints/sprint01_foundation/sprint.result.json'
        result.parent.mkdir(parents=True)
        result.write_text(json.dumps({'exit_code': 0, 'stall_aborted': True}))
        self.assertEqual(campaign.record_result('model', '01_foundation', 0)['status'], 'failed')

    def test_fallback_requires_parent_dnf(self):
        slug = 'v2_qwen35_122b_oss'
        self.assertFalse(campaign.conditional_ready(slug))
        parent = self.root / 'v2_qwen35_397b_oss'
        parent.mkdir()
        (parent / 'DNF').write_text('time guard\n')
        self.assertTrue(campaign.conditional_ready(slug))
        self.assertTrue(campaign.conditional_ready('v2_glm_5_3_flash_oss'))

    def test_performance_gate_requires_current_config_and_existing_evidence(self):
        slug = 'v2_glm_5_3_flash_oss'
        with patch.object(campaign, 'LEDGER_DIR', self.root):
            self.assertFalse(campaign.performance_validated(slug))
            directory = self.root / 'performance-validation'
            directory.mkdir()
            evidence = self.root / 'probe.json'
            evidence.write_text('{}')
            record = {'passed': True, 'tool_preflight_passed': True, 'decode_tokens_per_second': 120,
                      'serving_fingerprint': campaign.serving_fingerprint(slug),
                      'evidence': [str(evidence)]}
            path = directory / f'{slug}.json'
            path.write_text(json.dumps(record))
            self.assertTrue(campaign.performance_validated(slug))
            record['decode_tokens_per_second'] = 99
            path.write_text(json.dumps(record))
            self.assertFalse(campaign.performance_validated(slug))
            record['decode_tokens_per_second'] = 120
            record['serving_fingerprint'] = 'stale'
            path.write_text(json.dumps(record))
            self.assertFalse(campaign.performance_validated(slug))
            record['serving_fingerprint'] = campaign.serving_fingerprint(slug)
            path.write_text(json.dumps(record))
            evidence.unlink()
            self.assertFalse(campaign.performance_validated(slug))

    def test_active_guard_accepts_budget_extension_without_resetting_time(self):
        proc = Mock()
        proc.wait.side_effect = [subprocess.TimeoutExpired('sprint', 1), 0]
        with patch.object(campaign, 'current_budget', side_effect=[10, 20]), patch.object(campaign.time, 'time', side_effect=[9, 11]):
            self.assertEqual(campaign.wait_with_live_budget(proc, 0, 0), 0)
        self.assertEqual(proc.wait.call_args_list[0].kwargs['timeout'], 1)
        self.assertEqual(proc.wait.call_args_list[1].kwargs['timeout'], 5)

    def test_active_guard_counts_prior_sprints_and_current_elapsed(self):
        proc = Mock()
        with patch.object(campaign, 'current_budget', return_value=20), patch.object(campaign.time, 'time', return_value=15):
            with self.assertRaises(subprocess.TimeoutExpired):
                campaign.wait_with_live_budget(proc, 6, 0)
        proc.wait.assert_not_called()

    def test_guard_stops_child_in_separate_session(self):
        pidfile = self.root / 'child.pid'
        program = (
            'import subprocess,sys,time,pathlib; '
            'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"],start_new_session=True); '
            f'pathlib.Path({str(pidfile)!r}).write_text(str(p.pid)); '
            'time.sleep(60)'
        )
        parent = subprocess.Popen([sys.executable, '-c', program], start_new_session=True)
        try:
            deadline = time.monotonic() + 5
            while not pidfile.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(pidfile.exists())
            child = int(pidfile.read_text())
            campaign.stop_sprint_tree(parent, grace=2)
            self.assertIsNotNone(parent.poll())
            identity = campaign.process_identity(child)
            self.assertTrue(identity is None or identity[2] == 'Z')
        finally:
            if parent.poll() is None:
                campaign.stop_sprint_tree(parent, grace=1)


if __name__ == '__main__':
    unittest.main()
