"""Owner-bootstrap smoke checker tests without network or update execution."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from bin import remote_deploy_smoketest as smoke

SHA = "f" * 40

class BootstrapProbeTests(unittest.TestCase):
    def test_ready_requires_opt_in_canonical_and_green_ci(self):
        with tempfile.TemporaryDirectory() as d:
            flag = Path(d)/"enabled.json"
            flag.write_text(json.dumps({"enabled":True,"auto_update":True}))
            with patch.object(smoke,"FLAG",flag), \
                 patch.object(smoke,"git",side_effect=lambda *a:
                     smoke.EXPECTED_ORIGIN if a[0]=="remote" else SHA), \
                 patch("bin.verified_release.verify_ci",return_value=True):
                self.assertTrue(smoke.probe()["ready"])
            with patch.object(smoke,"FLAG",flag), \
                 patch.object(smoke,"git",side_effect=lambda *a:
                     smoke.EXPECTED_ORIGIN if a[0]=="remote" else SHA), \
                 patch("bin.verified_release.verify_ci",return_value=False):
                self.assertFalse(smoke.probe()["ready"])
            flag.write_text(json.dumps({"enabled":True,"auto_update":False}))
            with patch.object(smoke,"FLAG",flag), \
                 patch.object(smoke,"git",side_effect=lambda *a:
                     smoke.EXPECTED_ORIGIN if a[0]=="remote" else SHA), \
                 patch("bin.verified_release.verify_ci",return_value=True):
                self.assertFalse(smoke.probe()["ready"])

if __name__=="__main__":
    unittest.main()
