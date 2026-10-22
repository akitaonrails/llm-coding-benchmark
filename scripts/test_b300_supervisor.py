import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import b300_supervisor as s


class SupervisorTests(unittest.TestCase):
    def test_unlimited_execution_requires_explicit_marker(self):
        stage = dict(id='sprint', argv=['true'], timeout_seconds=None, model_execution=True)
        self.assertIn('sprint', s.validate({'stages': [stage]}))
        stage.pop('model_execution')
        with self.assertRaises((TypeError, ValueError)):
            s.validate({'stages': [stage]})

    def test_unlimited_execution_can_outlive_initial_lease_deadline(self):
        events = []
        class Process:
            def __init__(self):
                self.remaining = 3
                self.returncode = 0
            def poll(self):
                self.remaining -= 1
                return None if self.remaining > 0 else 0
        with tempfile.TemporaryDirectory() as tmp, patch.object(s, 'OUT', Path(tmp)), \
             patch.object(s, 'renew') as renew, \
             patch.object(s.time, 'time', side_effect=[0, 500, 1000]), \
             patch.object(s.time, 'monotonic', side_effect=[0, 500, 500, 1000, 1000]), \
             patch.object(s.time, 'sleep'), patch.object(s.subprocess, 'Popen', return_value=Process()):
            s.run({'stages': [dict(id='sprint', argv=['true'], timeout_seconds=None,
                                  model_execution=True)]}, events.append)
        self.assertEqual(events[-1]['exit_code'], 0)
        self.assertEqual(renew.call_count, 3)

    def test_explicit_approval_policy_never_sends_stop(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(s, 'ROOT', Path(tmp)), patch.object(s, 'execute') as execute:
            (Path(tmp)/'config').mkdir()
            (Path(tmp)/'config/b300_campaign.json').write_text('{"billing_safety":{"pod_shutdown_policy":"explicit_approval"}}')
            self.assertEqual(s.shutdown(), 'pod_retained_requires_explicit_user_shutdown_approval')
            execute.assert_not_called()

    def test_rejects_infinite_retry_and_unknown_transition(self):
        for target in ('a', 'missing'):
            with self.assertRaises(ValueError):
                s.validate({'stages': [dict(id='a', argv=['true'], timeout_seconds=10, on_failure=target)]})

    def test_rejects_unbounded_stage(self):
        for timeout in (0, -1, 14401):
            with self.assertRaises(ValueError):
                s.validate({'stages': [dict(id='a', argv=['true'], timeout_seconds=timeout)]})

    def test_no_launch_when_lease_delivery_fails(self):
        with patch.object(s, 'renew', side_effect=RuntimeError('offline')), \
             patch.object(s.subprocess, 'Popen') as launch:
            with self.assertRaises(RuntimeError):
                s.run({'stages': [dict(id='a', argv=['true'], timeout_seconds=10)]}, lambda e: None)
            launch.assert_not_called()

    def test_explicit_failure_transition(self):
        plan = {'stages': [dict(id='a', argv=['false'], timeout_seconds=10, on_failure='b'),
                           dict(id='b', argv=['true'], timeout_seconds=10)]}
        stages = s.validate(plan)
        self.assertEqual(stages['a']['on_failure'], 'b')

    def test_real_failed_child_advances_to_recovery_then_next_stage(self):
        events = []
        with tempfile.TemporaryDirectory() as tmp, patch.object(s, 'OUT', Path(tmp)), \
             patch.object(s, 'renew'):
            s.run({'stages': [
                dict(id='crash', argv=['/bin/false'], timeout_seconds=10, on_failure='recover'),
                dict(id='recover', argv=['/bin/true'], timeout_seconds=10, on_success='next'),
                dict(id='next', argv=['/bin/true'], timeout_seconds=10)]}, events.append)
        self.assertEqual([e['stage'] for e in events if e['status'] == 'finished'],
                         ['crash', 'recover', 'next'])
        self.assertEqual([e['exit_code'] for e in events if e['status'] == 'finished'], [1, 0, 0])

    def test_stage_timeout_kills_child_and_runs_recovery(self):
        events = []
        with tempfile.TemporaryDirectory() as tmp, patch.object(s, 'OUT', Path(tmp)), \
             patch.object(s, 'renew'):
            s.run({'stages': [
                dict(id='stall', argv=['/bin/sleep', '30'], timeout_seconds=0.1, on_failure='recover'),
                dict(id='recover', argv=['/bin/true'], timeout_seconds=10)]}, events.append)
        self.assertTrue(any(e.get('error_type') == 'TimeoutError' for e in events))
        self.assertEqual(events[-1]['stage'], 'recover')
        self.assertEqual(events[-1]['exit_code'], 0)


if __name__ == '__main__':
    unittest.main()
