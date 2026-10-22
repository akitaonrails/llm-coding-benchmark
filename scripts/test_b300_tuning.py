import json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import b300_tuning as tuning

class TuningTest(unittest.TestCase):
    def test_decode_rate_excludes_first_token_and_uses_warm_median(self):
        rows=[{'elapsed_seconds':ttft+255/rate,'first_token_seconds':ttft,'usage':{'completion_tokens':256}}
              for ttft,rate in [(100,10),(1,60),(2,80)]]
        self.assertAlmostEqual(tuning.probe_rate({'records':rows}),70)
        rows[-1]['usage']['completion_tokens']=128
        with self.assertRaises(ValueError):tuning.probe_rate({'records':rows})

    def test_round_and_time_limits(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(tuning.campaign,'LEDGER_DIR',Path(tmp)), patch.object(tuning,'update_runbook'):
            slug='v2_glm_5_3_flash_oss'
            s=tuning.begin(slug,'initial')
            with self.assertRaises(RuntimeError):tuning.begin(slug,'overlap')
            s['rounds'][0]['finished_at']=time.time();s['rounds']*=3;tuning.save(slug,s)
            with self.assertRaisesRegex(RuntimeError,'Configuration limit'):tuning.begin(slug,'fourth')
            s['rounds']=[];s['started_at']=time.time()-2701;tuning.save(slug,s)
            with self.assertRaisesRegex(RuntimeError,'wall-time'):tuning.begin(slug,'late')

if __name__=='__main__':unittest.main()
