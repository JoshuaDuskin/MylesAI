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

    def test_visible_basic_app_aliases_are_allowlisted(self):
        with patch("myles_windows.launch_app_verified", return_value="DESKTOP_APP_LAUNCH_VERIFIED: private title") as launch:
            for prompt, app in (("Open VS Code", "Visual Studio Code"),
                                ("Open Windows Media Player", "Windows Media Player Legacy"),
                                ("Open Chat GPT", "ChatGPT")):
                with self.subTest(prompt=prompt):
                    status, out = guest_chat.public_app_reply(prompt)
                    self.assertEqual(status, 200)
                    self.assertEqual(out["reply"], f"{app} is open on the tower.")
                    launch.assert_called_with(app, timeout_seconds=20)

    def test_disabled_marker_never_reaches_windows_file_association(self):
        import myles_windows as w
        self.assertEqual(w._normalized_app_name("Myles.disabled"), "Myles")
        with patch.object(w.os, "name", "nt"), patch.object(w.ctypes, "windll", create=True):
            self.assertEqual(w._shell_open("C:\\Users\\Joshu\\Desktop\\Myles.disabled"),
                             (False, "refused disabled marker target"))

    def test_unverified_launch_does_not_claim_success_or_disclose_error(self):
        with patch("myles_windows.launch_app_verified", return_value="DESKTOP_APP_LAUNCH_ERROR: C:/private/path"):
            status, out = guest_chat.public_app_reply("Open Calculator")
        self.assertEqual(status, 200)
        self.assertIn("couldn't verify", out["reply"])
        self.assertNotIn("private/path", str(out))

    def test_xbox_tray_and_companion_are_not_the_xbox_app(self):
        from myles_windows import _matching_visible_windows
        app = {"ProcessName": "XboxPcApp.exe", "MainWindowTitle": "XBOX", "Handle": 1}
        with patch("myles_windows.visible_windows", return_value=[
            {"ProcessName": "XboxPcTray.exe", "MainWindowTitle": "DesktopWindowXamlSource"},
            {"ProcessName": "ApplicationFrameHost.exe", "MainWindowTitle": "Xbox Console Companion"},
            app,
        ]):
            self.assertEqual(_matching_visible_windows("Xbox"), [app])

    def test_background_window_does_not_verify_launch(self):
        from myles_windows import launch_app_verified
        with patch("myles_windows.os.name", "nt"), \
             patch("myles_windows._matching_visible_windows", return_value=[{"Id": 1, "Handle": 1}]), \
             patch("myles_windows._activate_window", return_value=False), \
             patch("myles_windows.visible_windows", return_value=[]), \
             patch("myles_windows._best_start_app", return_value={"app_id": "Xbox", "name": "Xbox"}), \
             patch("myles_windows._shell_open", return_value=(True, "sent")), \
             patch("myles_windows.time.time", side_effect=[0, 0, 100]), \
             patch("myles_windows.time.sleep"):
            self.assertTrue(launch_app_verified("Xbox").startswith("DESKTOP_APP_LAUNCH_NOT_VERIFIED:"))

    def test_close_xbox_uses_verified_server_action(self):
        for prompt in ("Close Xbox", "Close Xbox app", "Can you close the Xbox app please?"):
            with self.subTest(prompt=prompt), patch("myles_windows.close_xbox_verified", return_value="DESKTOP_APP_CLOSE_VERIFIED: closed") as close, patch("myles_windows.launch_app_verified") as launch:
                _, out = guest_chat.public_app_reply(prompt)
                self.assertEqual(out["reply"], "Xbox is closed on the tower.")
                close.assert_called_once_with(timeout_seconds=10)
                launch.assert_not_called()

    def test_close_failure_and_already_closed_are_honest(self):
        for result, expected in (("DESKTOP_APP_CLOSE_NOT_VERIFIED: still open", "couldn't verify"), ("DESKTOP_APP_CLOSE_ALREADY_CLOSED: absent", "no open app window")):
            with patch("myles_windows.close_xbox_verified", return_value=result):
                self.assertIn(expected, guest_chat.public_app_reply("Close Xbox")[1]["reply"])

    def test_close_extra_commands_never_execute(self):
        with patch("myles_windows.close_xbox_verified") as close:
            for prompt in ("Close Xbox and delete files", "Close Xbox; calc", "Close PowerShell"):
                self.assertIsNone(guest_chat.public_app_reply(prompt))
            close.assert_not_called()

    def test_close_waits_for_xbox_window_to_disappear(self):
        import myles_windows as w
        from types import SimpleNamespace
        from unittest.mock import Mock
        post = Mock()
        with patch.object(w.os, "name", "nt"), patch.object(w.ctypes, "windll", SimpleNamespace(user32=SimpleNamespace(PostMessageW=post)), create=True), patch.object(w, "_matching_visible_windows", side_effect=[[{"Handle": 42}], []]):
            self.assertTrue(w.close_xbox_verified().startswith("DESKTOP_APP_CLOSE_VERIFIED:"))
            post.assert_called_once_with(42, 0x0010, 0, 0)

    def test_fortnite_uses_epic_and_verified_game_result(self):
        for prompt in ("Launch Fortnite", "Open Fortnite", "Can you start Fortnite please?"):
            with self.subTest(prompt=prompt), patch("myles_game_guard.game_is_active", return_value=False), patch("myles_windows.launch_fortnite_verified", return_value="FORTNITE_RUNNING: game window") as launch, patch("myles_windows.launch_app_verified") as generic, patch("myles_model_runtime.model_chat") as model:
                _, out = guest_chat.public_send(prompt)
                self.assertEqual(out["reply"], "Fortnite is running on the tower.")
                launch.assert_called_once_with(timeout_seconds=70)
                generic.assert_not_called()
                model.assert_not_called()

    def test_epic_launcher_alone_is_not_game_success(self):
        with patch("myles_windows.launch_fortnite_verified", return_value="FORTNITE_NOT_VERIFIED: launcher only"):
            reply = guest_chat.public_app_reply("Launch Fortnite")[1]["reply"]
            self.assertIn("haven't verified", reply)
            self.assertNotIn("Fortnite is running", reply)

    def test_fortnite_arguments_never_reach_launcher(self):
        with patch("myles_windows.launch_fortnite_verified") as launch:
            guest_chat.public_app_reply("Launch Fortnite --extra-argument")
            launch.assert_not_called()

    def test_fortnite_launches_installed_windows_edition(self):
        import myles_windows as w
        with patch.object(w.os, "name", "nt"), patch.object(w, "_fortnite_visible", side_effect=[None, {"ProcessName": "FortniteClient-Win64-Shipping.exe"}]), patch.object(w, "_best_start_app", return_value={"name": "Fortnite", "app_id": "InstalledFortnite!Game"}), patch.object(w, "_shell_open", return_value=(True, "sent")) as shell, patch.object(w, "epic_launcher_executable", return_value=None), patch.object(w, "_activate_window", return_value=True):
            self.assertTrue(w.launch_fortnite_verified().startswith("FORTNITE_RUNNING:"))
            shell.assert_called_once_with("shell:AppsFolder\\InstalledFortnite!Game")

    def test_fortnite_controls_work_during_game_mode_without_model(self):
        with patch("myles_game_guard.game_is_active", return_value=True), patch("myles_windows.close_fortnite_verified", return_value="FORTNITE_CLOSED_VERIFIED: exited") as close, patch("myles_windows.launch_fortnite_verified", return_value="FORTNITE_RUNNING: foreground") as launch, patch("myles_model_runtime.model_chat") as model:
            self.assertEqual(guest_chat.public_send("Close Fortnite")[1]["reply"], "Fortnite is closed on the tower.")
            self.assertEqual(guest_chat.public_send("Launch Fortnite")[1]["reply"], "Fortnite is running on the tower.")
            close.assert_called_once_with(timeout_seconds=12)
            launch.assert_called_once_with(timeout_seconds=70)
            model.assert_not_called()

    def test_fortnite_close_failure_never_claims_success(self):
        with patch("myles_windows.close_fortnite_verified", return_value="FORTNITE_CLOSE_NOT_VERIFIED: still running"):
            self.assertIn("couldn't verify", guest_chat.public_send("Close Fortnite")[1]["reply"])

    def test_fortnite_close_arguments_do_not_bypass_game_mode(self):
        with patch("myles_game_guard.game_is_active", return_value=True), patch("myles_windows.close_fortnite_verified") as close:
            self.assertEqual(guest_chat.public_send("Close Fortnite and Xbox")[0], 503)
            close.assert_not_called()

    def test_game_mode_prevents_public_launch(self):
        with patch("myles_game_guard.game_is_active", return_value=True), \
             patch("myles_windows.launch_app_verified") as launch:
            self.assertEqual(guest_chat.public_send("Open Paint")[0], 503)
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
