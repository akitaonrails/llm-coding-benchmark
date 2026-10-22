import tempfile
import unittest
from pathlib import Path
from b300_progress import ProgressWatch


class ProgressTests(unittest.TestCase):
    def test_repeated_failures_pause_but_changed_results_do_not(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);watch=ProgressWatch(root,root/'absent.ndjson',now=0)
            for i in range(5):
                watch.record(dict(type='tool_use',part=dict(callID=str(i),tool='bash',state=dict(status='completed',input={'command':'test'},output='same failure'))))
            self.assertIn('Repeated',watch.check(now=121))
            (root/'app.rb').write_text('fixed')
            self.assertIsNone(watch.check(now=160))
            for i in range(5,10):
                watch.record(dict(type='tool_use',part=dict(callID=str(i),tool='bash',state=dict(status='completed',input={'command':'test'},output=f'{i} passing tests'))))
            self.assertIsNone(watch.check(now=300))

    def test_touch_or_logs_do_not_count_as_source_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);p=root/'app.rb';p.write_text('same')
            watch=ProgressWatch(root,root/'absent.ndjson',now=0)
            p.touch();(root/'log').mkdir();(root/'log/development.log').write_text('activity')
            self.assertIn('20 minutes',watch.check(now=1201))

    def test_two_step_cycle_and_duplicate_event_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);watch=ProgressWatch(root,root/'absent.ndjson',now=0)
            for i in range(6):
                event=dict(type='tool_use',part=dict(callID=str(i),tool='bash',state=dict(status='completed',input={'command':str(i%2)},output='unchanged')))
                watch.record(event);watch.record(event)
            self.assertEqual(len(watch.history),6)
            self.assertIn('period 2',watch.check(now=121))


if __name__=='__main__':unittest.main()
