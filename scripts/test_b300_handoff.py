import copy
import unittest
from unittest.mock import patch
from b300_handoff import continuation, continuation_from_plan, maybe_handoff, append_recovery
from run_b300_campaign import CAMP


class HandoffTests(unittest.TestCase):
    def test_second_recovery_preserves_remaining_first_recovery(self):
        plan=continuation(CAMP,'m09-stop-server')
        append_recovery(plan,[dict(slug='first'),dict(slug='second')])
        remaining=continuation_from_plan(plan,'r00-stop-server')
        append_recovery(remaining,[dict(slug='repair',boundary=3,repair=True)],'t')
        stages={s['id']:s for s in remaining['stages']}
        self.assertEqual(remaining['stages'][0]['id'],'r01-resume')
        self.assertEqual(stages['r01-stop-server']['on_success'],'t00-resume')
        self.assertEqual(stages['t00-prepare']['on_success'],'t00-repair')
        self.assertEqual(stages['t00-repair']['on_success'],'t00-boundary-03')
        self.assertNotIn('t00-sprint-03',stages)

    def test_recovery_resumes_review_and_does_not_replay_sprints(self):
        plan=continuation(CAMP, 'm09-stop-server')
        append_recovery(plan,[dict(slug='test_qwen',boundary=2),dict(slug='test_startup')])
        stages={s['id']:s for s in plan['stages']}
        self.assertEqual(stages[f'm{len(CAMP["queue"])-1:02d}-stop-server']['on_success'],'r00-resume')
        self.assertEqual(stages[f'm{len(CAMP["queue"])-1:02d}-gate']['on_failure'],'r00-resume')
        self.assertNotIn('on_failure',stages['m10-stop-server'])
        self.assertEqual(stages['r00-prepare']['on_success'],'r00-boundary-02')
        self.assertNotIn('r00-sprint-02', stages)
        self.assertEqual(stages['r00-stop-server']['on_success'],'r01-resume')
        self.assertEqual(stages['r01-prepare']['on_success'],'r01-sprint-01')

    def test_remaining_queue_includes_extension_without_replaying_current(self):
        campaign = copy.deepcopy(CAMP)
        campaign['queue'].append(dict(slug='test_extension'))
        plan = continuation(campaign, 'm06-stop-server')
        self.assertEqual(plan['stages'][0]['id'], 'm07-gate')
        self.assertEqual(plan['stages'][-1]['id'], f'm{len(CAMP["queue"]):02d}-stop-server')
        self.assertIn('test_extension', plan['stages'][-20]['argv'])
        self.assertFalse(any(s['id'].startswith('m06-') for s in plan['stages']))

    def test_cannot_handoff_during_sprint(self):
        with self.assertRaises(ValueError):
            continuation(CAMP, 'm06-sprint-01')

    def test_wrong_parent_never_signaled(self):
        import tempfile, json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out/'pending-extension.json').write_text(json.dumps(dict(supervisor_pid=-1, start_ticks='bad')))
            with patch('b300_handoff.OUT', out), patch('b300_handoff.os.kill') as kill:
                with self.assertRaises(RuntimeError):
                    maybe_handoff()
                kill.assert_not_called()

    def test_real_waiting_parent_is_replaced_and_queue_preserved(self):
        import tempfile, json, subprocess, sys, time
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'config').mkdir()
            (root/'supervisor').mkdir()
            (root/'config/b300_campaign.json').write_text(json.dumps(CAMP))
            (root/'config/opencode.benchmark.json').write_text(json.dumps(
                {'provider': {'runpod-vllm': {'models': {}}}}))
            (root/'supervisor/status.json').write_text(json.dumps(
                {'status': 'starting', 'stage': 'm06-stop-server'}))
            child = root/'child.py'
            child.write_text('''import sys, os, json
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import b300_handoff as h
h.ROOT=Path(sys.argv[2]); h.OUT=h.ROOT/'supervisor'
h.renew=lambda *args: None
def replacement(executable, argv):
    plan=json.loads(Path(argv[-1]).read_text())
    (h.ROOT/'replaced.json').write_text(json.dumps(plan))
    os._exit(0)
h.os.execv=replacement
h.maybe_handoff()
''')
            parent_code = '''import sys, os, json, subprocess
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from run_b300_campaign import process_identity
root=Path(sys.argv[2])
(root/'supervisor/pending-extension.json').write_text(json.dumps(dict(
supervisor_pid=os.getpid(),start_ticks=process_identity(os.getpid())[1],
queue_entries=[dict(slug='test_extension')],provider_models={})))
subprocess.run([sys.executable,str(root/'child.py'),sys.argv[1],str(root)],check=True)
'''
            parent = subprocess.Popen([sys.executable, '-c', parent_code,
                str(Path(__file__).resolve().parent), str(root)])
            try:
                self.assertEqual(parent.wait(timeout=10), -9)
                deadline=time.monotonic()+5
                while not (root/'replaced.json').exists() and time.monotonic()<deadline:
                    time.sleep(.05)
                plan=json.loads((root/'replaced.json').read_text())
                self.assertEqual(plan['stages'][0]['id'], 'm07-gate')
                self.assertEqual(plan['stages'][-1]['id'], f'm{len(CAMP["queue"]):02d}-stop-server')
                self.assertFalse((root/'supervisor/pending-extension.json').exists())
            finally:
                if parent.poll() is None:
                    parent.kill(); parent.wait()


if __name__ == '__main__':
    unittest.main()
