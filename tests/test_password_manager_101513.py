"""Phone credential manager recovery after browser site data is cleared."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class PhoneCredentialRecovery(unittest.TestCase):
 def test_owner_form_exposes_password_manager_autofill(self):
  h=(ROOT/"index.html").read_text(encoding="utf-8")
  self.assertIn('id="ownerPairForm"',h)
  self.assertIn('autocomplete="username"',h)
  self.assertIn('autocomplete="current-password"',h)
  self.assertIn("['ownerPairSubmit',true]",h)
  self.assertNotIn('id="bridgeTokenInput" type="text"',h)
 def test_pairing_secret_is_not_committed(self):
  h=(ROOT/"index.html").read_text(encoding="utf-8")
  self.assertNotIn("C6NANWDQ",h)
  self.assertIn("exchangePair",h)
if __name__=="__main__": unittest.main()
