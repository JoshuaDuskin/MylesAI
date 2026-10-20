"""Owner-chosen bridge URL must override stale published discovery."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class BridgeSelection(unittest.TestCase):
 def test_owner_override_is_not_ignored(self):
  s=(ROOT/"index.html").read_text(encoding="utf-8")
  self.assertIn("normalizeUrl(state.bridge.url || state.bridge.discovered || '')",s)
  self.assertNotIn("normalizeUrl(state.bridge.discovered || state.bridge.url || '')",s)
  self.assertIn("state.bridge.url=normalizeUrl($('bridgeUrlInput').value)",s)
 def test_no_pair_code_or_full_access_in_published_config(self):
  s=(ROOT/"bridge.json").read_text(encoding="utf-8")
  self.assertNotIn("C6NANWDQ",s)
  self.assertNotIn("owner_token",s)
if __name__=="__main__":unittest.main()
