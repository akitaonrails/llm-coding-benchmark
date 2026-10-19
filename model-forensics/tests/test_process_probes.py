import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'confirmatory'))
import process_probes as p


class ProcessProbeTests(unittest.TestCase):
    def test_bank_and_state_contract(self):
        bank=p.probes()
        self.assertEqual(len(bank),48)
        self.assertEqual(len({x['id'] for x in bank}),48)
        self.assertEqual(bank,p.probes())
        for x in bank:
            self.assertEqual(x['states'][-1],x['expected'])
            self.assertEqual(len(x['states']),x['steps'])

    def test_correct_answer_does_not_hide_incorrect_trace(self):
        probe=next(x for x in p.probes() if x['mode']=='trace')
        states=list(probe['states']);states[1]='wrong'
        r=p.parse({'status':'ok','text':json.dumps({'answer':probe['expected'],'states':states})},probe)
        self.assertTrue(r['correct']);self.assertEqual(r['first_wrong_step'],2)

    def test_missing_trace_steps_detected(self):
        probe=next(x for x in p.probes() if x['mode']=='trace')
        r=p.parse({'status':'ok','text':json.dumps({'answer':probe['expected'],'states':probe['states'][:-1]})},probe)
        self.assertEqual(r['first_wrong_step'],probe['steps'])

    def test_invalid_and_truncated_excluded(self):
        probe=next(x for x in p.probes() if x['mode']=='check')
        self.assertFalse(p.parse({'status':'truncated','text':'{}'},probe)['usable'])
        self.assertFalse(p.parse({'status':'ok','text':'not JSON'},probe)['usable'])
        self.assertFalse(p.parse({'status':'ok','text':json.dumps({'answer':probe['expected']})},probe)['usable'])

    def test_surface_similarity_does_not_match_numbers_alone(self):
        self.assertEqual(p.check_similarity('verify by reverse substitution','VERIFY BY REVERSE SUBSTITUTION'),1)
        self.assertIsNone(p.check_similarity('123','456'))
        self.assertEqual(p.check_similarity('check arithmetic backwards','run independent simulation'),0)
