"""REA-derived observable behavior replay (no model weights or private APIs).

Mocks OS activity and Qwen responses. Every case is a local-controller contract,
not a claim that GrokBot, Muse, REA's native engines or the Windows tower ran.
"""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import myles_assisted as assisted
import myles_core as core
import myles_interactive as interactive
from myles_runtime_v9 import (
    app_launch_target, behavior_feedback_request, desktop_action_request,
    natural_question, stop_request_scope,
)


def call(name: str, args: dict | None = None) -> dict:
    return {"function": {"name": name, "arguments": args or {}}}


class IntentReplay(unittest.TestCase):
    def test_foreground_focus_words_have_consistent_targets(self):
        utterances = (
            "Focus Notepad", "Please focus Notepad", "Can you focus Notepad?",
            "Switch to Notepad", "Bring Notepad to front",
            "Go ahead and focus Notepad", "I need you to focus Notepad",
            "Myles, focus Notepad", "Put Notepad in the front",
        )
        for phrase in utterances:
            with self.subTest(phrase=phrase):
                parsed = desktop_action_request(phrase)
                self.assertIsNotNone(parsed)
                self.assertEqual(parsed.get("kind"), "focus")
                self.assertEqual(parsed.get("target"), "Notepad")

    def test_windows_is_not_a_fake_app_launch(self):
        for phrase in ("Open windows", "Open running apps", "Open applications"):
            with self.subTest(phrase=phrase):
                self.assertEqual(app_launch_target(phrase), "")
        self.assertTrue(assisted.read_only_intent("Show open windows"))
        self.assertTrue(assisted.authorized("inspect_open_windows", "Show open windows", {}))

    def test_screen_read_only_against_mutation_and_description(self):
        wanted = (
            "What is on my screen?", "What's on the desktop?",
            "Take a screenshot", "Look at my desktop",
            "Please inspect the screen", "Show me the screen",
            "Describe my screen", "Can you inspect my desktop?",
        )
        not_wanted = (
            "What is a screen?", "Explain my computer",
            "Click the screen", "Take a screenshot and send it",
            "Show the Windows settings panel", "Restart the desktop",
            "Close the window", "Deploy the screen update",
        )
        for phrase in wanted:
            with self.subTest(phrase=phrase):
                self.assertTrue(interactive.screen_request(phrase))
        for phrase in not_wanted:
            with self.subTest(phrase=phrase):
                self.assertFalse(interactive.screen_request(phrase))

    def test_feedback_not_a_background_task(self):
        statements = (
            "I didn't ask you to start a task.",
            "That should just be a quick lookup.",
            "Stop making everything into a job.",
            "I wasn't asking you to fix anything.",
            "I am just talking.",
            "Is there anything you need to fix?",
            "This should have been a quick search, not a whole job.",
            "Why did you start a task?",
        )
        for phrase in statements:
            with self.subTest(phrase=phrase):
                self.assertTrue(behavior_feedback_request(phrase))
                self.assertFalse(core._conversation_tool_authorized(
                    "start_background_job", phrase, {"prompt": "Fix the dashboard"}))

    def test_questions_are_not_hard_actions(self):
        queries = (
            "How do I install Python?", "What is myles?",
            "Why did the window disappear?", "Is it finished?",
            "Explain how the dashboard works", "Where are the settings?",
            "Should I close the app?", "How can I fix it?",
        )
        for phrase in queries:
            with self.subTest(phrase=phrase):
                self.assertTrue(natural_question(phrase))
                self.assertFalse(core._conversation_tool_authorized(
                    "start_background_job", phrase, {"prompt": "Do unrelated work"}))

    def test_generic_navigation_allowlist_intent(self):
        allowed = (
            "Press escape", "Press tab", "Press shift+tab", "Press ctrl+l",
            "Press ctrl+f", "Press up", "Press down", "Press left",
            "Press right", "Press home", "Press end", "Press pageup",
            "Press pagedown", "Show desktop",
        )
        for phrase in allowed:
            with self.subTest(phrase=phrase):
                parsed = desktop_action_request(phrase)
                self.assertIsNotNone(parsed)
                self.assertEqual(parsed["kind"], "key")
                self.assertTrue(interactive.authorized(
                    "send_navigation_key", phrase, {"keys": parsed["keys"]}))
        denied = ("Press ALT+F4", "Press CTRL+V", "Press CTRL+C", "Press WIN+R",
                  "Press CTRL+ALT+DELETE", "Press CTRL+SHIFT+ESC")
        for phrase in denied:
            with self.subTest(phrase=phrase):
                parsed = desktop_action_request(phrase)
                if parsed is not None and parsed.get("kind") == "key":
                    self.assertFalse(interactive.authorized(
                        "send_navigation_key", phrase, {"keys": parsed["keys"]}))

    def test_stop_all_priority(self):
        for phrase in (
            "Stop all tasks", "Cancel every running task", "Quit all queued tasks",
            "Clear the task queue", "Stop everything", "Abort all active jobs",
        ):
            with self.subTest(phrase=phrase):
                self.assertEqual(stop_request_scope(phrase), "all")

    def test_pinetree_window_never_focused(self):
        for title in ("PineTree", "PineTree Checkout", "pinetree payments"):
            with self.subTest(title=title):
                self.assertFalse(interactive.authorized(
                    "focus_existing_window", "Focus " + title, {"title": title}))


class ForegroundReplay(unittest.TestCase):
    def test_direct_key_avoids_background_queue_and_keeps_truth(self):
        with patch.object(core, "add_message", return_value=123), \
             patch.object(core, "_start_task") as task, \
             patch.object(core.assisted, "execute", return_value='EVIDENCE_ID=1\nKEY_EVENTS_SENT={"keys":"ESC","effect_verified":false}') as send:
            answer = core.handle_owner_message("Press escape", "test")
            self.assertIn("sent", answer["reply"])
            self.assertIn("not the resulting screen change", answer["reply"])
            self.assertEqual(answer["kind"], "conversation")
            task.assert_not_called()
            send.assert_called_once()

    def test_key_sent_only_to_observed_foreground(self):
        windows = [{"MainWindowTitle": "Notes - Notepad",
                    "ProcessName": "notepad.exe", "Handle": 27}]
        with patch.object(interactive, "_on_windows", return_value=True), \
             patch.object(interactive, "active_job", return_value=None), \
             patch.object(interactive, "visible_windows", return_value=windows), \
             patch.object(interactive, "_foreground", return_value=27), \
             patch("myles_tools.desktop_key", return_value='{"sent": true, "keys": "ESC"}') as send:
            text, verified = interactive.send_navigation_key("ESC", "chat_test")
            self.assertTrue(verified)
            self.assertEqual(json.loads(text.split("=", 1)[1])["effect_verified"], False)
            send.assert_called_once()
        with patch.object(interactive, "_on_windows", return_value=True), \
             patch.object(interactive, "active_job", return_value=None), \
             patch.object(interactive, "visible_windows", return_value=windows), \
             patch.object(interactive, "_foreground", return_value=999), \
             patch("myles_tools.desktop_key") as send:
            text, verified = interactive.send_navigation_key("ESC", "chat_test")
            self.assertFalse(verified)
            send.assert_not_called()

    def test_pinetree_and_active_job_never_get_keys(self):
        for active, windows in [
            ({"id": "running-job"}, [{"MainWindowTitle": "Notepad", "Handle": 27}]),
            (None, [{"MainWindowTitle": "PineTree", "ProcessName": "chrome", "Handle": 27}]),
        ]:
            with self.subTest(active=bool(active)):
                with patch.object(interactive, "_on_windows", return_value=True), \
                     patch.object(interactive, "active_job", return_value=active), \
                     patch.object(interactive, "visible_windows", return_value=windows), \
                     patch("myles_tools.desktop_key") as send:
                    _, verified = interactive.send_navigation_key("ESC", "chat_test")
                    self.assertFalse(verified)
                    send.assert_not_called()


class ConversationLoopReplay(unittest.TestCase):
    def _mock(self, replies):
        return patch.multiple(
            core, history_for_model=lambda *a, **kw: [],
            _conversation_runtime_context=lambda: "mocked test runtime",
            _conversation_call=__import__("unittest.mock", fromlist=["Mock"]).Mock(side_effect=replies),
            _conversation_tool_authorized=lambda name, raw, args: True,
        )

    def test_only_one_background_job_even_if_model_repeats(self):
        replies = [
            {"message": {"content": "", "tool_calls": [
                call("start_background_job", {"prompt": "Build one safe fixture"}),
                call("start_background_job", {"prompt": "Build one safe fixture again"})]}},
            {"message": {"content": "A single tracked task was started."}},
        ]
        with self._mock(replies), patch.object(core, "_conversation_tool",
              return_value="STARTED task_id=test_job_1 state=RUNNING task=fixture") as execute:
            answer, jid = core._conversation_agent_turn("Build a safe fixture", "test")
            self.assertEqual(jid, "test_job_1")
            self.assertEqual(execute.call_count, 1)
            self.assertIn("tracked task", answer)

    def test_repeated_side_effect_is_refused(self):
        replies = [
            {"message": {"content": "", "tool_calls": [
                call("set_light_mode", {"enabled": True}),
                call("set_light_mode", {"enabled": True})]}},
            {"message": {"content": "Mode requested."}},
        ]
        with self._mock(replies), patch.object(core, "_conversation_tool",
              return_value="Game Mode is on") as execute:
            _, jid = core._conversation_agent_turn("Turn game mode on", "test")
            self.assertIsNone(jid)
            self.assertEqual(execute.call_count, 1)

    def test_failed_worker_launch_does_not_become_started_job(self):
        replies = [
            {"message": {"content": "", "tool_calls": [
                call("start_background_job", {"prompt": "Build fixture"})]}},
            {"message": {"content": "Worker startup failed."}},
        ]
        with self._mock(replies), patch.object(core, "_conversation_tool",
              return_value="ERROR: task was created but worker could not launch: OSError. task_id=unstarted") as execute:
            answer, jid = core._conversation_agent_turn("Build fixture", "test")
            self.assertIsNone(jid)
            self.assertEqual(execute.call_count, 1)
            self.assertIn("failed", answer)

    def test_refused_or_malformed_calls_do_not_execute(self):
        replies = [
            {"message": {"content": "", "tool_calls": [
                call("unlisted_shell", {"command": "whoami"}),
                {"function": {"name": "start_background_job", "arguments": "{invalid"}}]}},
            {"message": {"content": "Nothing was started."}},
        ]
        with self._mock(replies), patch.object(core, "_conversation_tool") as execute:
            answer, jid = core._conversation_agent_turn("Hello there", "test")
            execute.assert_not_called()
            self.assertIsNone(jid)
            self.assertIn("Nothing", answer)


if __name__ == "__main__":
    unittest.main()
