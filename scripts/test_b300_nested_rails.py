import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from run_v4_wave import project_has_rails


class NestedRailsTests(unittest.TestCase):
    def test_single_nested_app_detected_without_accepting_ambiguous_or_vendor(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory); project=out/'candidate/project'; project.mkdir(parents=True)
            def app(name):
                p=project/name; (p/'app').mkdir(parents=True);(p/'config').mkdir()
                (p/'Gemfile').touch();(p/'config/application.rb').touch()
            with patch('run_v4_wave.OUT',out):
                self.assertFalse(project_has_rails('candidate'))
                app('vendor'); self.assertFalse(project_has_rails('candidate'))
                app('chat'); self.assertTrue(project_has_rails('candidate'))
                app('other'); self.assertFalse(project_has_rails('candidate'))


if __name__=='__main__':unittest.main()
