import base64
import unittest
from unittest.mock import patch
import b300_remote as remote


class TransferTests(unittest.TestCase):
    def test_lost_ack_retries_identical_atomic_file(self):
        from pathlib import Path
        from types import SimpleNamespace
        payload=b'evidence-test'*900
        observed=[]
        def run(argv, **kwargs):
            source=Path(argv[argv.index('--upload')+1])
            observed.append(source.read_bytes())
            return SimpleNamespace(returncode=125 if len(observed)==1 else 0)
        with patch.object(remote.subprocess,'run',side_effect=run),patch.object(remote.time,'sleep'):
            remote.upload(payload,'/root/fixture.bin')
        self.assertEqual(observed,[payload,payload])

    def test_transfer_failure_is_bounded(self):
        with patch.object(remote,'_upload_once',side_effect=RuntimeError('offline')) as transfer,patch.object(remote.time,'sleep'):
            with self.assertRaises(RuntimeError):remote.upload(b'x','/root/fixture.bin')
            self.assertEqual(transfer.call_count,3)


if __name__=='__main__':unittest.main()
