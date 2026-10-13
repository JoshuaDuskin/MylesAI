"""Acceptance runner is pure-read by default; all external probes mocked."""
from __future__ import annotations
import unittest
from unittest.mock import patch

from bin import acceptance_windows as a


class WindowsAcceptanceTests(unittest.TestCase):
    def test_default_does_not_capture_or_call_model(self):
        with patch.object(a, "is_windows", return_value=True), \
             patch.object(a, "git_head", return_value="abc"), \
             patch.object(a, "probe_http", return_value={"ok":True}), \
             patch.object(a, "windows_snapshot", return_value={"ok":True}), \
             patch("myles_model_runtime.model_health_dict",
                   return_value={"available":True,"supports_tools":True,"supports_vision":True}), \
             patch("myles_model_runtime.model_chat") as model, \
             patch("myles_windows.capture_desktop_png") as capture:
            result = a.run_acceptance()
            self.assertTrue(result["pass"])
            self.assertTrue(result["checks"]["screen"]["skipped"])
            self.assertTrue(result["checks"]["live_model"]["skipped"])
            model.assert_not_called()
            capture.assert_not_called()

    def test_disconnected_tower_is_not_pass(self):
        with patch.object(a, "is_windows", return_value=True), \
             patch.object(a, "git_head", return_value="abc"), \
             patch.object(a, "probe_http", return_value={"ok":False,"reason":"ConnectionRefusedError"}), \
             patch.object(a, "windows_snapshot", return_value={"ok":False}), \
             patch("myles_model_runtime.model_health_dict",return_value={"available":False}):
            report=a.run_acceptance()
            self.assertFalse(report["pass"])

    def test_requested_source_mismatch_is_error(self):
        with patch.object(a, "is_windows", return_value=True), \
             patch.object(a, "git_head", return_value="abc"), \
             patch.object(a, "probe_http", return_value={"ok":True}), \
             patch.object(a, "windows_snapshot", return_value={"ok":True}), \
             patch("myles_model_runtime.model_health_dict",return_value={"available":True}):
            report=a.run_acceptance(expected_head="def")
            self.assertFalse(report["pass"])
            self.assertFalse(report["checks"]["source"]["ok"])

    def test_live_model_marker_only_when_explicit(self):
        with patch.object(a, "is_windows", return_value=True), \
             patch.object(a, "git_head", return_value="abc"), \
             patch.object(a, "probe_http", return_value={"ok":True}), \
             patch.object(a, "windows_snapshot", return_value={"ok":True}), \
             patch("myles_model_runtime.model_health_dict",return_value={"available":True}), \
             patch("myles_model_runtime.model_chat",
                   return_value={"message":{"content":"MYLES_TEST_OK"}}) as model:
            report=a.run_acceptance(live_model=True)
            self.assertTrue(report["checks"]["live_model"]["ok"])
            model.assert_called_once()


if __name__=="__main__":
    unittest.main()
