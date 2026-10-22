import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import b300_pause

class PauseTest(unittest.TestCase):
    def test_checkpoint_preserves_workspace_and_pins_and_records_incomplete_sprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'config').mkdir()
            (root/'config/b300_campaign.json').write_text(json.dumps({'queue':[{'slug':'model','hf_repo':'publisher/model','local_dir':'weights'}]}))
            out=root/'results-v4/model';project=out/'project';project.mkdir(parents=True)
            evidence=project/'unfinished.tmp';evidence.write_text('resume me')
            (out/'sprints/sprint01_foundation').mkdir(parents=True)
            control=root/'results-v4/_b300_campaign/migration-20261017';control.mkdir(parents=True)
            (control/'checkpoints.json').write_text(json.dumps({'model':{'revision':'abc123'}}))
            with patch.object(b300_pause,'ROOT',root):
                manifest=b300_pause.checkpoint('model','time budget')
            state=json.loads(manifest.read_text())
            self.assertEqual(evidence.read_text(),'resume me')
            self.assertEqual(state['checkpoint_revision_manifest']['model']['revision'],'abc123')
            self.assertIsNone(state['sprints'][0]['result_path'])
            self.assertTrue((out/'PAUSED').exists())
            self.assertTrue((out/'RESUME.md').exists())
            self.assertEqual(state['status'],'paused_pending_batch_review')

if __name__=='__main__':unittest.main()
