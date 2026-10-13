"""Fortnite gets precedence over autonomous and owner model/tool workloads.

All process and model effects are mocked. No actual game is launched, stopped
or benchmarked in GitHub CI; real Windows performance needs later observation.
"""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bin import game_mode_watch as watcher
import myles_core as core
import myles_model_runtime as model
import myles_game_guard as guard


class GameDetectionTests(unittest.TestCase):
    def test_fortnite_process_detected_without_xbox_false_positive(self):
        xbox = {"pid":13,"name":"XboxPcApp.exe","exe":"C:\\Windows\\XboxPcApp.exe","cmdline":"",
                "rss":300_000_000}
        fortnite = {"pid":14,"name":"FortniteClient-Win64-Shipping.exe",
                    "exe":"D:\\Fortnite\\FortniteClient-Win64-Shipping.exe",
                    "cmdline":"","rss":800_000_000}
        with patch.object(watcher, "process_rows", return_value=[xbox]):
            self.assertIsNone(watcher.detect_game())
        with patch.object(watcher, "process_rows", return_value=[xbox,fortnite]):
            match=watcher.detect_game()
            self.assertEqual(match["pid"],14)
            self.assertEqual(match["reason"],"known_game_process")

    def test_non_myles_processes_are_never_terminated(self):
        canonical=str(watcher.ROOT)
        rows=[
            {"pid":11,"exe":"C:\\Python\\python.exe",
             "cmdline":"C:\\OtherAI\\job_worker.py","name":"python.exe"},
            {"pid":12,"exe":"C:\\Program Files\\nodejs\\node.exe",
             "cmdline":canonical+"\\quant\\quant_service.mjs","name":"node.exe"},
            {"pid":13,"exe":"C:\\Python\\python.exe",
             "cmdline":canonical+"\\job_worker.py myles_job1","name":"python.exe"},
        ]
        with patch.object(watcher, "process_rows", return_value=rows), \
             patch.object(watcher,"kill_tree") as kill:
            stopped=watcher.stop_heavy_myles_processes()
        self.assertEqual(stopped,[12,13])
        self.assertEqual([x.args[0] for x in kill.call_args_list],[12,13])

    def test_recheck_rate_is_bounded(self):
        self.assertGreaterEqual(watcher.CHECK_SECONDS,2)
        self.assertGreaterEqual(watcher.HEAVY_RECHECK_SECONDS,10)
        self.assertGreaterEqual(watcher.OLLAMA_RECHECK_SECONDS,30)


class GamePauseTests(unittest.TestCase):
    def test_game_state_and_auto_light_mode_gate(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"game_mode_state.json").write_text('{"active":true}')
            (root/"config.json").write_text('{"light_mode":false}')
            with patch.object(guard,"DATA",root):
                self.assertTrue(guard.game_is_active())
                (root/"game_mode_state.json").write_text('{"active":false}')
                self.assertFalse(guard.game_is_active())
                (root/"config.json").write_text(
                    '{"light_mode":true,"light_mode_source":"manual"}')
                self.assertFalse(guard.game_is_active())
                (root/"config.json").write_text(
                    '{"light_mode":true,"light_mode_source":"automatic_game_detection"}')
                self.assertTrue(guard.game_is_active())

    def test_no_job_worker_starts_during_game(self):
        with patch.object(core,"game_is_active",return_value=True), \
             patch.object(core,"claim_job_for_launch") as claim, \
             patch.object(core.subprocess,"Popen") as popen:
            self.assertFalse(core.start_job({"id":"queued_test"}))
            claim.assert_not_called()
            popen.assert_not_called()

    def test_no_qwen_chat_during_game(self):
        with patch.object(guard,"game_is_active",return_value=True), \
             patch.object(model,"ensure_model_runtime") as ensure:
            with self.assertRaisesRegex(model.ModelRuntimeError,"game_performance_mode"):
                model.model_chat({},[{"role":"user","content":"Hello"}])
            ensure.assert_not_called()

    def test_status_message_remains_read_only(self):
        with patch.object(core,"game_is_active",return_value=True), \
             patch.object(core,"add_message",return_value=99), \
             patch.object(core,"active_job",return_value=None), \
             patch.object(core,"looks_like_status_request",return_value=True), \
             patch.object(core,"status_text",return_value="Core online"), \
             patch.object(core,"_conversation_agent_turn") as ai, \
             patch.object(core,"_start_task") as start:
            res=core.handle_owner_message("What are you doing?","owner")
            self.assertIn("Fortnite performance mode",res["reply"])
            ai.assert_not_called()
            start.assert_not_called()

    def test_regular_prompt_is_deferred_without_inference(self):
        with patch.object(core,"game_is_active",return_value=True), \
             patch.object(core,"add_message",return_value=100), \
             patch.object(core,"active_job",return_value=None), \
             patch.object(core,"looks_like_status_request",return_value=False), \
             patch.object(core,"_continuous_disable_request",return_value=False), \
             patch.object(core,"_conversation_agent_turn") as ai, \
             patch.object(core,"_start_task") as start:
            res=core.handle_owner_message("Can you research the latest market strategy?","owner")
            self.assertIn("Fortnite is running",res["reply"])
            ai.assert_not_called()
            start.assert_not_called()


if __name__=="__main__":
    unittest.main()
