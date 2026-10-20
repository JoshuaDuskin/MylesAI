"""Regression: live gaming must gate an update even before watcher heartbeat."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class GameUpdateGuard(unittest.TestCase):
 def test_live_process_detection_is_first_gate(self):
  s=(ROOT/"bin"/"remote_deploy_agent.py").read_text(encoding="utf-8")
  block=s[s.index("def idle_gate()"):s.index("def try_approved_release(")]
  self.assertIn("from bin.game_mode_watch import detect_game",block)
  self.assertIn('return "game process running"',block)
  self.assertIn('return "game detection unavailable"',block)
  self.assertLess(block.index("detect_game()"),block.index('read_json(DATA / "config.json")'))
 def test_hidden_update_launch(self):
  s=(ROOT/"bin"/"remote_deploy_agent.py").read_text(encoding="utf-8")
  self.assertIn('"-WindowStyle", "Hidden", "-File", str(APPLY)',s)
  self.assertIn('creationflags=NO_WINDOW',s)
if __name__=="__main__":unittest.main()
