import unittest
from unittest.mock import patch
import subprocess
import b300_billing_watchdog as w


class BillingWatchdogTests(unittest.TestCase):
    def test_retain_mode_never_stops_pod_on_expired_lease(self):
        with patch.object(w, 'read_lease', return_value={}), \
             patch.object(w.time, 'sleep', side_effect=RuntimeError('end')), \
             patch.object(w, 'stop_pod') as stop, \
             patch('pathlib.Path.open', unittest.mock.mock_open()) as log:
            from pathlib import Path
            with self.assertRaises(RuntimeError):
                w.run(Path('lease'), Path('events'), 'test-pod', on_expiry='retain')
            stop.assert_not_called()
            self.assertIn('lease_expired_pod_retained', log().write.call_args.args[0])

    def test_controller_death_expires_lease(self):
        lease = dict(issued_at=100, expires_at=400, stage_deadline=900)
        self.assertFalse(w.expired(lease, 399))
        self.assertTrue(w.expired(lease, 400))

    def test_heartbeat_cannot_exceed_stage_deadline(self):
        self.assertTrue(w.expired(dict(issued_at=390, expires_at=690,
                                      stage_deadline=400), 400))

    def test_corruption_and_clock_jump_fail_closed(self):
        for lease in ({}, None, [], {'issued_at': 'bad'},
                      dict(issued_at=100, expires_at=999, stage_deadline=900),
                      dict(issued_at=float('nan'), expires_at=400, stage_deadline=900),
                      dict(issued_at=100, expires_at=400, stage_deadline=900)):
            self.assertTrue(w.expired(lease, 99))

    def test_shutdown_timeout_is_retryable(self):
        with patch.object(w.subprocess, 'run', side_effect=subprocess.TimeoutExpired('stop', 30)):
            self.assertFalse(w.stop_pod('test-pod'))

    def test_shutdown_latches_and_retries_after_success(self):
        with patch.object(w, 'read_lease', side_effect=[{}, dict(issued_at=0, expires_at=300, stage_deadline=300)]), \
             patch.object(w.time, 'time', return_value=1), \
             patch.object(w.time, 'sleep', side_effect=[None, RuntimeError('end')]), \
             patch.object(w, 'stop_pod', side_effect=[False, True]) as stop, \
             patch('pathlib.Path.open', unittest.mock.mock_open()):
            from pathlib import Path
            with self.assertRaises(RuntimeError):
                w.run(Path('lease'), Path('events'), 'test-pod')
            self.assertEqual(stop.call_count, 2)


if __name__ == '__main__':
    unittest.main()
