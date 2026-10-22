"""Two household browsers receive full owner role only after pairing."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class HouseholdFullAccessContract(unittest.TestCase):
    def test_regular_link_opens_dashboard_with_public_chat(self):
        page=(ROOT/"index.html").read_text(encoding="utf-8")
        self.assertIn("await initPublicApp();return;",page)
        self.assertNotIn("get('owner') !== '1'",page)
        self.assertIn("localStorage.setItem('myles_bridge_token'",page)
        self.assertIn("await exchangePair(false)",page)

    def test_anonymous_full_control_is_impossible(self):
        bridge=(ROOT/"dashboard_bridge"/"dashboard_bridge.py").read_text(encoding="utf-8")
        gateway=(ROOT/"bin"/"public_gateway_v074.py").read_text(encoding="utf-8")
        self.assertIn('if not authorized(self):',bridge)
        self.assertIn('if not allowed:',gateway)
        self.assertIn('"/dashboard/public-chat/messages"',gateway)
        self.assertIn("guest_chat_module().public_send(text.strip())",bridge)
        self.assertIn("guest_chat_module().public_messages()",bridge)

if __name__=="__main__":
    unittest.main()
