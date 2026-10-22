import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import b300_run_repair as repair


class RepairTests(unittest.TestCase):
    def test_repair_charged_to_existing_budget_and_does_not_overwrite_sprint(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);root=out/'model'
            review=root/'boundaries/sprint03-100';review.mkdir(parents=True)
            (review/'assistance.json').write_text(json.dumps(dict(category='ordinary_minor_defect',prompt='Fix the route syntax.')))
            prior=root/'sprints/sprint03_admin/sprint.result.json';prior.parent.mkdir(parents=True);prior.write_text('preserved')
            ledger={'models':{'model':{'sprint_seconds_total':50,'sprints':{}}}}
            proc=Mock();proc.poll.return_value=0;proc.returncode=0
            with patch.object(repair.campaign,'OUT',out),patch.object(repair.campaign,'load_ledger',return_value=ledger),patch.object(repair.campaign,'save_ledger'),patch.object(repair.campaign,'current_budget',return_value=14400),patch.object(repair.subprocess,'Popen',return_value=proc) as launch,patch.object(repair.sys,'argv',['repair','model','03']),patch.object(repair.time,'time',side_effect=[1,2,12]):
                self.assertEqual(repair.main(),0)
                self.assertIn('--repair-prompt',launch.call_args.args[0])
            self.assertEqual(ledger['models']['model']['sprint_seconds_total'],60)
            self.assertEqual(prior.read_text(),'preserved')
            self.assertEqual(len(list((root/'assistance').glob('*.json'))),1)


if __name__=='__main__':unittest.main()
