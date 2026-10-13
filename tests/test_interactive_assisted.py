"""Focused regression tests for MYLES visual/focus conversation tools.

These tests mock all OS actions: no screenshot, focus, keyboard or click reaches
the test runner's real desktop.
"""
from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import myles_assisted as assisted
import myles_interactive as interactive


class AssistedDesktopTests(unittest.TestCase):
    def test_explicit_screen_intent_only(self):
        self.assertTrue(interactive.screen_request("What is on my screen?"))
        self.assertTrue(interactive.screen_request("Take a screenshot"))
        self.assertTrue(assisted.read_only_intent("Look at my desktop"))
        self.assertFalse(interactive.screen_request("Take a screenshot and send it"))
        self.assertFalse(interactive.screen_request("Click the button on my screen"))
        self.assertFalse(interactive.screen_request("How does a computer screen work?"))
        self.assertTrue(interactive.authorized("inspect_desktop_screen", "What is on my screen?", {}))
        self.assertFalse(interactive.authorized("inspect_desktop_screen", "Hey", {}))
        self.assertFalse(interactive.authorized("inspect_desktop_screen", "What is on my screen?", {"path": "secret"}))

    def test_window_focus_requires_owner_target(self):
        self.assertTrue(interactive.authorized("focus_existing_window", "Focus Notepad", {"title": "Notepad"}))
        self.assertFalse(interactive.authorized("focus_existing_window", "Focus Notepad", {"title": "Terminal"}))
        self.assertFalse(interactive.authorized("focus_existing_window", "What is Notepad?", {"title": "Notepad"}))
        self.assertFalse(interactive.authorized("focus_existing_window", "Focus PineTree", {"title": "PineTree"}))
        self.assertFalse(interactive.authorized("focus_existing_window", "Focus Notepad", {}))

    def test_focus_result_requires_exact_foreground_handle(self):
        visible = [{"MainWindowTitle": "Notes - Notepad", "ProcessName": "notepad.exe", "Handle": 42}]
        mock_result = json.dumps({"activated": True, "handle": 42, "title": "Notes - Notepad"})
        with patch.object(interactive, "_on_windows", return_value=True), \
             patch.object(interactive, "active_job", return_value=None), \
             patch.object(interactive, "visible_windows", return_value=visible), \
             patch("myles_tools.desktop_activate_window", return_value=mock_result), \
             patch.object(interactive, "_foreground", return_value=42):
            result, ok = interactive.focus_window("Notepad", "chat_fixture")
        self.assertTrue(ok)
        self.assertIn("WINDOW_FOCUS_VERIFIED", result)
        with patch.object(interactive, "_on_windows", return_value=True), \
             patch.object(interactive, "active_job", return_value=None), \
             patch.object(interactive, "visible_windows", return_value=visible), \
             patch("myles_tools.desktop_activate_window", return_value=mock_result), \
             patch.object(interactive, "_foreground", return_value=999):
            result, ok = interactive.focus_window("Notepad", "chat_fixture")
        self.assertFalse(ok)
        self.assertNotIn("WINDOW_FOCUS_VERIFIED", result)

    def test_ambiguous_and_protected_windows_never_focus(self):
        visible = [
            {"MainWindowTitle": "Notes - Notepad", "ProcessName": "notepad.exe", "Handle": 42},
            {"MainWindowTitle": "Todo - Notepad", "ProcessName": "notepad.exe", "Handle": 43},
        ]
        with patch.object(interactive, "_on_windows", return_value=True), \
             patch.object(interactive, "active_job", return_value=None), \
             patch.object(interactive, "visible_windows", return_value=visible), \
             patch("myles_tools.desktop_activate_window") as action:
            result, ok = interactive.focus_window("Notepad", "chat_fixture")
            self.assertFalse(ok)
            action.assert_not_called()
        with patch.object(interactive, "_on_windows", return_value=True), \
             patch.object(interactive, "active_job", return_value=None), \
             patch.object(interactive, "visible_windows", return_value=[
                 {"MainWindowTitle": "PineTree Payments", "ProcessName": "chrome.exe", "Handle": 50}
             ]), \
             patch("myles_tools.desktop_activate_window") as action:
            result, ok = interactive.focus_window("Notepad", "chat_fixture")
            self.assertFalse(ok)
            self.assertIn("PineTree", result)
            action.assert_not_called()

    def test_screenshot_is_ephemeral_and_digest_checked(self):
        with tempfile.TemporaryDirectory(prefix="myles_visual_test_") as d:
            root = Path(d)
            def mock_capture(path):
                path.write_bytes(interactive.PNG_HEADER + b"fake-test-bytes" * 12)
                return {"width": 1, "height": 1}
            with patch.object(interactive, "CAPTURE_DIR", root), \
                 patch.object(interactive, "_on_windows", return_value=True), \
                 patch.object(interactive, "_vision_available", return_value=True), \
                 patch.object(interactive, "active_job", return_value=None), \
                 patch.object(interactive, "visible_windows", return_value=[]), \
                 patch.object(interactive, "capture_desktop_png", side_effect=mock_capture):
                result, ok = interactive.capture_screen()
                self.assertTrue(ok)
                self.assertEqual(len(list(root.glob("*.png"))), 1)
                image = interactive.consume_screen_image(result)
                self.assertIsNotNone(image)
                self.assertEqual(base64.b64decode(image["images"][0]),
                                 interactive.PNG_HEADER + b"fake-test-bytes" * 12)
                self.assertEqual(list(root.glob("*.png")), [])

    def test_tampered_screen_digest_rejected_and_erased(self):
        with tempfile.TemporaryDirectory(prefix="myles_visual_test_") as d:
            root = Path(d)
            data = interactive.PNG_HEADER + b"fixtures"
            path = root / "visual_test.png"
            path.write_bytes(data)
            meta = {"path": str(path), "bytes": len(data), "sha256": "0" * 64}
            with patch.object(interactive, "CAPTURE_DIR", root):
                self.assertIsNone(interactive.consume_screen_image(
                    "EVIDENCE_ID=1\nVISUAL_EVIDENCE=" + json.dumps(meta)))
                self.assertFalse(path.exists())

    def test_pinetree_or_missing_vision_blocks_capture(self):
        with patch.object(interactive, "_on_windows", return_value=True), \
             patch.object(interactive, "_vision_available", return_value=False), \
             patch.object(interactive, "capture_desktop_png") as capture:
            result, ok = interactive.capture_screen()
            self.assertFalse(ok)
            self.assertIn("vision", result)
            capture.assert_not_called()
        with patch.object(interactive, "_on_windows", return_value=True), \
             patch.object(interactive, "_vision_available", return_value=True), \
             patch.object(interactive, "active_job", return_value=None), \
             patch.object(interactive, "visible_windows", return_value=[
                 {"MainWindowTitle": "PineTree", "ProcessName": "chrome.exe"}
             ]), \
             patch.object(interactive, "capture_desktop_png") as capture:
            result, ok = interactive.capture_screen()
            self.assertFalse(ok)
            capture.assert_not_called()


if __name__ == "__main__":
    unittest.main()
