"""Phone onboarding and independent authorization proof."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class PhoneTrust(unittest.TestCase):
 def test_owner_auth_check_not_message_service(self):
  s=(ROOT/"index.html").read_text(encoding="utf-8")
  self.assertIn("await fetchJson(`${url}/dashboard/quant/config`",s)
  self.assertIn("state.bridge.healthy=true",s)
  self.assertIn("state.bridge.recoveryCode&&await exchangePair(false)",s)
 def test_new_browser_prompts_for_first_pair_and_preserves_trust(self):
  s=(ROOT/"index.html").read_text(encoding="utf-8")
  self.assertIn("if(!recovered&&!state.bridge.token&&!state.bridge.recoveryCode){showView('chat');openPairModal();",s)
  self.assertIn("localStorage.setItem('myles_bridge_token'",s)
  self.assertIn("localStorage.setItem('myles_bridge_pair_code'",s)
if __name__=="__main__":unittest.main()
