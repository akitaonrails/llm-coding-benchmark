import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import b300_start_sprint as start


class ReadinessTests(unittest.TestCase):
    def test_dead_server_fails_before_readiness_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'config').mkdir()
            (root/'config/b300_campaign.json').write_text(json.dumps({
                'billing_safety':{'paid_execution_enabled':True},
                'queue':[{'slug':'test','served_name':'test'}]}))
            (root/'config/opencode.benchmark.json').write_text(json.dumps({
                'provider':{'runpod-vllm':{'options':{'baseURL':'http://localhost:1','apiKey':'fixture'}}}}))
            with patch.object(start,'ROOT',root), \
                 patch('sys.argv',['start','test']), \
                 patch.object(start.time,'monotonic',side_effect=[0,0,61,61]), \
                 patch.object(start.urllib.request,'urlopen',side_effect=OSError('unavailable')), \
                 patch('b300_remote.execute',return_value='{"slug":"test","alive":false}'), \
                 patch.object(start.subprocess,'run') as launch:
                self.assertEqual(start.main(),2)
                launch.assert_not_called()


if __name__=='__main__':unittest.main()
