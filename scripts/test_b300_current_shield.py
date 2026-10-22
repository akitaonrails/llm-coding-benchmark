import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import run_v4_sprint as sprint


class OwnEvidenceShieldTests(unittest.TestCase):
    def test_own_grades_are_hidden_and_restored_without_touching_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'results-v4';model=out/'fixture'
            (model/'boundaries').mkdir(parents=True)
            (model/'boundaries/report.md').write_text('private injection evidence')
            (model/'project').mkdir();(model/'project/code.rb').write_text('candidate')
            with patch.object(sprint,'REPO',root),patch.object(sprint,'OUT',out),patch.object(sprint,'SHIELD',[]),patch.object(sprint,'SHIELD_BASE',root/'private'):
                shield=sprint.shield(model)
                self.assertFalse((model/'boundaries').exists())
                self.assertEqual((model/'project/code.rb').read_text(),'candidate')
                sprint.unshield(shield)
                self.assertEqual((model/'boundaries/report.md').read_text(),'private injection evidence')
                self.assertFalse(shield.exists())

    def test_restore_conflict_preserves_both_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'results-v4';model=out/'fixture'
            (model/'boundaries').mkdir(parents=True)
            (model/'boundaries/report.md').write_text('original')
            with patch.object(sprint,'REPO',root),patch.object(sprint,'OUT',out),patch.object(sprint,'SHIELD',[]),patch.object(sprint,'SHIELD_BASE',root/'private'):
                shield=sprint.shield(model)
                (model/'boundaries').mkdir();(model/'boundaries/fake.md').write_text('candidate created')
                with self.assertRaises(RuntimeError):sprint.unshield(shield)
                self.assertEqual((shield/'current-evidence/boundaries/report.md').read_text(),'original')
                self.assertTrue((model/'boundaries/fake.md').exists())


if __name__=='__main__':unittest.main()
