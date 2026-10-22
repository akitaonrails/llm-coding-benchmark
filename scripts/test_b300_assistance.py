import json
import tempfile
import unittest
from pathlib import Path
from b300_assistance import consume


class AssistanceTests(unittest.TestCase):
    def test_requires_completed_review_and_caps_total_at_two(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for n in (1,2,3):
                d=root/'boundaries'/f'sprint{n:02d}-100';d.mkdir(parents=True)
                (d/'assistance.json').write_text(json.dumps(dict(category='ordinary_minor_defect',prompt='Fix the missing import reported by your test.')))
                self.assertIsNone(consume(root,f'{n+1:02d}_test'))
                (d/'verdict.json').write_text('{"eligible":true}')
                result=consume(root,f'{n+1:02d}_test')
                self.assertEqual(result is not None,n<=2)
                self.assertIsNone(consume(root,f'{n+1:02d}_test'))
            self.assertEqual(len(list((root/'assistance').glob('*.json'))),2)


if __name__=='__main__':unittest.main()
