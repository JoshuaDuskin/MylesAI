"""Owner phone screenshot regressions and Windows-only game-close truth gates.

All process and Win32 calls are simulated in GitHub CI; no actual Fortnite
process is touched. Tower-only acceptance still requires a real game session.
"""
from __future__ import annotations
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

import myles_core as core
import myles_windows as windows
from bin import remote_deploy_agent as deploy


class FortniteCloseTests(unittest.TestCase):
    def test_explicit_commands_are_narrowly_accepted(self):
        for command in ("Close Fortnite", "I said close Fortnite",
                        "please quit Fortnite", "can you close Fortnite?",
                        "close Fortnite now", "I told you to close Fortnite"):
            with self.subTest(command=command):
                self.assertTrue(core._direct_fortnite_close_request(command))
        for command in ("Don't close Fortnite", "Do not close Fortnite",
                        "What happens if I close Fortnite?",
                        "I like Fortnite", "Close Xbox", "Stop all tasks",
                        "Can you explain how to close Fortnite?"):
            with self.subTest(command=command):
                self.assertFalse(core._direct_fortnite_close_request(command))

    def test_game_mode_close_bypasses_qwen_and_worker(self):
        messages=[]
        for command in ("Close Fortnite", "I said close Fortnite"):
            with self.subTest(command=command), \
                 patch.object(core,"game_is_active",return_value=True), \
                 patch.object(core,"add_message",side_effect=lambda *x:
                     messages.append(x) or len(messages)), \
                 patch.object(core,"close_fortnite_verified",return_value=
                     "FORTNITE_CLOSED_VERIFIED: actual game exited.") as close, \
                 patch.object(core,"_conversation_agent_turn") as model, \
                 patch.object(core,"_start_task") as worker:
                result=core.handle_owner_message(command,"dashboard")
                self.assertEqual(result["kind"],"conversation")
                self.assertIn("verified",result["reply"].casefold())
                self.assertIsNone(result.get("job_id"))
                close.assert_called_once()
                model.assert_not_called()
                worker.assert_not_called()

    def test_close_failure_is_truthful_and_does_not_claim_game_exited(self):
        with patch.object(core,"game_is_active",return_value=True), \
             patch.object(core,"add_message",return_value=99), \
             patch.object(core,"close_fortnite_verified",return_value=
                 "FORTNITE_CLOSE_NOT_VERIFIED: game still active"), \
             patch.object(core,"_start_task") as worker:
            response=core.handle_owner_message("Close Fortnite","dashboard")
            self.assertIn("couldn't verify",response["reply"])
            self.assertNotIn("is closed",response["reply"])
            worker.assert_not_called()

    def test_negative_owner_instruction_still_defers_in_game_mode(self):
        with patch.object(core,"game_is_active",return_value=True), \
             patch.object(core,"add_message",return_value=99), \
             patch.object(core,"_direct_fortnite_close") as close, \
             patch.object(core,"_start_task") as worker:
            response=core.handle_owner_message("Don't close Fortnite","dashboard")
            self.assertIn("Fortnite is running",response["reply"])
            close.assert_not_called()
            worker.assert_not_called()

    def test_native_close_requests_verified_window_and_observed_exit(self):
        window={"Id":122,"ProcessName":"FortniteClient-Win64-Shipping.exe",
                "Handle":994,"MainWindowTitle":"Fortnite"}
        ui=MagicMock()
        with patch.object(windows.os,"name","nt"), \
             patch.object(windows,"_fortnite_client_pids",return_value={122}), \
             patch.object(windows,"visible_windows",return_value=[window]), \
             patch.object(windows,"_fortnite_client_still_present",side_effect=[True,False]), \
             patch.object(windows,"_terminate_exact_fortnite_client") as kill, \
             patch.object(windows.ctypes,"windll",new=types.SimpleNamespace(user32=ui),create=True), \
             patch.object(windows.time,"sleep",return_value=None):
            report=windows.close_fortnite_verified(timeout_seconds=4)
            self.assertTrue(report.startswith("FORTNITE_CLOSED_VERIFIED"))
            ui.PostMessageW.assert_called_once_with(994,0x0010,0,0)
            kill.assert_not_called()

    def test_does_not_close_launcher_xbox_or_other_apps(self):
        with patch.object(windows.os,"name","nt"), \
             patch.object(windows,"_fortnite_client_pids",return_value=set()), \
             patch.object(windows,"_fortnite_client_still_present",return_value=False), \
             patch.object(windows,"_terminate_exact_fortnite_client") as kill:
            self.assertTrue(windows.close_fortnite_verified().startswith("FORTNITE_NOT_RUNNING"))
            kill.assert_not_called()
        assert "xboxpcapp.exe" not in windows.FORTNITE_CLIENT_EXES
        assert "epicgameslauncher.exe" not in windows.FORTNITE_CLIENT_EXES
        assert "fortniteclient-win64-shipping_eac_eos.exe" not in windows.FORTNITE_CLIENT_EXES

    def test_unverified_wrong_process_identity_never_terminated(self):
        app=MagicMock()
        app.name.return_value="XboxPcApp.exe"
        fake=types.SimpleNamespace(Process=lambda pid:app)
        with patch.object(windows.os,"name","nt"), \
             patch.dict(sys.modules,{"psutil":fake}):
            self.assertFalse(windows._terminate_exact_fortnite_client(999))
            app.terminate.assert_not_called()


class UpdateWrapperProcessTests(unittest.TestCase):
    def test_windows_missing_process_is_not_mistaken_for_alive(self):
        self.assertTrue(deploy._windows_open_process_is_gone(87))
        self.assertTrue(deploy._windows_open_process_is_gone(1168))
        self.assertFalse(deploy._windows_open_process_is_gone(5))
        self.assertFalse(deploy._windows_open_process_is_gone(0))

    def test_windows_process_open_error_is_classified(self):
        # Simulated WinDLL: NULL handle means missing PID only when the OS
        # returns an explicit 'process not found' error, not access denied.
        kernel=MagicMock()
        kernel.OpenProcess.return_value=0
        win=MagicMock(return_value=kernel)
        with patch.object(deploy.os,"name","nt"), \
             patch("ctypes.WinDLL",win,create=True), \
             patch("ctypes.get_last_error",return_value=87,create=True):
            self.assertFalse(deploy.process_running(10022))
        with patch.object(deploy.os,"name","nt"), \
             patch("ctypes.WinDLL",win,create=True), \
             patch("ctypes.get_last_error",return_value=5,create=True):
            self.assertTrue(deploy.process_running(10022))

    def test_conservative_when_wrapper_has_handle_but_cannot_prove_exit(self):
        kernel=MagicMock()
        kernel.OpenProcess.return_value=100
        kernel.WaitForSingleObject.return_value=0x102  # WAIT_TIMEOUT
        with patch.object(deploy.os,"name","nt"), \
             patch("ctypes.WinDLL",MagicMock(return_value=kernel),create=True):
            self.assertTrue(deploy.process_running(10022))
            kernel.CloseHandle.assert_called_once()


if __name__ == "__main__":
    unittest.main()
