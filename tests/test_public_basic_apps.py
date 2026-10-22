"""Anonymous app requests have a fixed scope and verified, non-private replies."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from dashboard_bridge import guest_chat


class PublicBasicApps(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.history = patch.object(guest_chat, "PUBLIC_HISTORY", Path(self.folder.name) / "history.json")
        self.history.start()
        self.addCleanup(self.history.stop)

    def test_public_launch_without_model_or_private_window_details(self):
        with patch("myles_game_guard.game_is_active", return_value=False), \
             patch("myles_windows.launch_app_verified", return_value="DESKTOP_APP_LAUNCH_VERIFIED: private document title") as launch, \
             patch("myles_model_runtime.model_chat") as model:
            status, out = guest_chat.public_send("Can you open Notepad please?")
        self.assertEqual(status, 200)
        self.assertEqual(out["reply"], "Notepad is open on the tower.")
        self.assertNotIn("private document", str(out))
        launch.assert_called_once_with("Notepad", timeout_seconds=20)
        model.assert_not_called()
        self.assertEqual(guest_chat.public_messages()["messages"], out["messages"])

    def test_unapproved_apps_and_arguments_never_reach_launcher(self):
        with patch("myles_windows.launch_app_verified") as launch:
            for text in ("Open PowerShell -Command calc", "Open cmd", "Open Notepad & calc", "Open Chrome --remote-debugging-port=9222", "Open Notepad and delete my files", "Open https://example.com", "Open C:/private/file.txt"):
                with self.subTest(text=text):
                    result = guest_chat.public_app_reply(text)
                    if result is not None:
                        self.assertIn("Other computer actions require owner access", result[1]["reply"])
            launch.assert_not_called()

    def test_requested_powershell_and_xbox_launches(self):
        with patch("myles_windows.launch_app_verified", return_value="DESKTOP_APP_LAUNCH_VERIFIED: private title") as launch:
            for prompt, app in (("Open PowerShell", "Windows PowerShell"), ("Open Xbox app", "Xbox")):
                with self.subTest(prompt=prompt):
                    status, out = guest_chat.public_app_reply(prompt)
                    self.assertEqual(status, 200)
                    self.assertEqual(out["reply"], f"{app} is open on the tower.")
                    launch.assert_called_with(app, timeout_seconds=20)

    def test_unverified_launch_does_not_claim_success_or_disclose_error(self):
        with patch("myles_windows.launch_app_verified", return_value="DESKTOP_APP_LAUNCH_ERROR: C:/private/path"):
            status, out = guest_chat.public_app_reply("Open Calculator")
        self.assertEqual(status, 200)
        self.assertIn("couldn't verify", out["reply"])
        self.assertNotIn("private/path", str(out))

    def test_game_mode_prevents_public_launch(self):
        with patch("myles_game_guard.game_is_active", return_value=True), \
             patch("myles_windows.launch_app_verified") as launch:
            self.assertEqual(guest_chat.public_send("Open Paint")[0], 503)
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
