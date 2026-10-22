import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import b300_hourly_status as reporter


class ReporterHandoffTest(unittest.TestCase):
    def test_existing_reporter_adopts_successor_before_reporting_old_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'supervisor').mkdir()
            manifest = root / 'supervisor/active-supervisor.json'
            old = {'pid': 10, 'start_ticks': '100'}
            new = {'pid': 20, 'start_ticks': '200'}
            manifest.write_text(json.dumps(old))
            alive = {10: '100'}
            reports = []

            def advance(_seconds):
                if 10 in alive:
                    alive.clear()
                    alive[20] = '200'
                    manifest.write_text(json.dumps(new))
                else:
                    alive.clear()

            with patch.object(reporter, 'LOCK', root / 'lock'), \
                 patch.object(reporter, 'locate', return_value=root), \
                 patch.object(reporter, 'identity', side_effect=lambda pid: alive.get(pid)), \
                 patch.object(reporter, 'report', side_effect=lambda c, n: reports.append(c['pid'])), \
                 patch.object(reporter.time, 'sleep', side_effect=advance), \
                 patch.object(reporter.time, 'monotonic', return_value=0), \
                 patch('sys.argv', ['reporter']):
                reporter.main()
            self.assertEqual(reports, [10, 20, 20])


if __name__ == '__main__':
    unittest.main()
