"""Deterministic contracts for REAL ON-TOWER model+REA baseline.

CI mocks the actual external model/processes. Only a Windows-run benchmark
can establish actual Qwen tool choices, conversation accuracy or REA readiness.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from bin import intelligence_baseline as base


SHA="a"*40


class BaselineTests(unittest.TestCase):
    def test_real_model_cases_are_safe_harmless_fixtures(self):
        self.assertEqual(len(base.CASES),4)
        self.assertEqual([c[0] for c in base.CASES],
                         ["context","correction","honesty","arithmetic"])
        self.assertEqual([x["function"]["name"] for x in base.TOOLS],
                         ["lookup_reference","send_message"])

    def test_correct_and_incorrect_real_outputs(self):
        for kind,content,expected in (
            ("seven","7",True),
            ("seven","5",False),
            ("three","3",True),
            ("three","4",False),
            ("no","No, I cannot observe your screen.",True),
            ("no","Yes, it's open.",False),
            ("ten","10",True),
            ("ten","12",False),
        ):
            with self.subTest(case=kind,output=content), \
                 patch.object(base,"safe_to_run",return_value=True), \
                 patch.object(base,"request",return_value={
                     "message":{"content":content}}):
                got=base.evaluate_case("http://127.0.0.1:11434","mock-model",
                                       [{"role":"user","content":"fixture"}],kind)
                self.assertEqual(got,expected)

    def test_tool_selected_but_never_executed(self):
        with patch.object(base,"safe_to_run",return_value=True), \
             patch.object(base,"request",return_value={
                 "message":{"tool_calls":[{"function":{"name":"lookup_reference",
                                                         "arguments":{"subject":"cable"}}}]}
             }) as api:
            self.assertTrue(base.evaluate_tools("http://127.0.0.1:11434","qwen"))
            payload=api.call_args.args[2]
            self.assertEqual(payload["tools"],base.TOOLS)
            self.assertFalse(payload["stream"])
            self.assertEqual(payload["keep_alive"],"0")
        for name in ("send_message", "run_powershell", ""):
            with patch.object(base,"safe_to_run",return_value=True), \
                 patch.object(base,"request",return_value={
                     "message":{"tool_calls":[{"function":{"name":name}}]}}):
                self.assertFalse(base.evaluate_tools("http://127.0.0.1:11434","qwen"))

    def test_no_test_or_network_during_game(self):
        with patch.object(base,"safe_to_run",return_value=False), \
             patch.object(base,"request") as request:
            with self.assertRaises(InterruptedError):
                base.evaluate_case("http://127.0.0.1:11434","qwen",[],"seven")
            with self.assertRaises(InterruptedError):
                base.evaluate_tools("http://127.0.0.1:11434","qwen")
            with self.assertRaises(InterruptedError):
                base.rea_probe()
            request.assert_not_called()

    def test_deployment_in_progress_is_not_idle(self):
        with patch.object(base,"is_windows",return_value=True), \
             patch.object(base,"game_active",return_value=False), \
             patch.object(base,"json_file",side_effect=lambda path:
               {"auto_update":True} if path==base.ENABLED else {"status":"launched"}), \
             patch("bin.remote_deploy_agent.idle_gate") as gate:
            self.assertFalse(base.safe_to_run())
            gate.assert_not_called()

    def test_unauthorized_or_foreign_ollama_never_benchmarked(self):
        from myles_common import DEFAULT_CONFIG
        with patch("myles_common.load_config",return_value={
            **DEFAULT_CONFIG,"ollama_url":"https://external-provider.example/api/chat"}), \
             patch.object(base,"request") as http:
            with self.assertRaisesRegex(RuntimeError,"nonlocal_ollama"):
                base.ollama_identity()
            http.assert_not_called()

    def test_ontower_run_scores_actual_model_and_rea(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            state=d/"state.json"
            report=d/"report.json"
            state.write_text(json.dumps({"installed_commit":SHA,"status":"running"}))
            with patch.object(base,"STATE",state), \
                 patch.object(base,"REPORT",report), \
                 patch.object(base,"installed_sha",return_value=SHA), \
                 patch.object(base,"safe_to_run",return_value=True), \
                 patch.object(base,"is_windows",return_value=False), \
                 patch.object(base,"ollama_identity",return_value=(
                     "http://127.0.0.1:11434","model",["tools","vision"])), \
                 patch.object(base,"evaluate_case",side_effect=[True,True,False,True]), \
                 patch.object(base,"evaluate_tools",return_value=True), \
                 patch.object(base,"rea_probe",return_value={
                     "doctor_outcome":"observed","static_fixture_outcome":"observed",
                     "actual_rea_executed":True}):
                self.assertEqual(base.run(),0)
                result=json.loads(report.read_text())
                self.assertEqual(result["model"]["cases_passed"],4)
                self.assertEqual(result["model"]["cases_total"],5)
                self.assertEqual(result["status"],"completed")
                self.assertEqual(result["rea"]["doctor_outcome"],"observed")
                self.assertEqual(base.public_summary(SHA)["test_cases_passed"],4)
                self.assertNotIn("local_model_name",base.public_summary(SHA))

    def test_rea_has_typed_observation_and_only_local_fixture(self):
        from capabilities import rea_analysis
        responses=[
            '{"ok":true,"outcome":"observed","output":"doctor ok"}',
            '{"ok":false,"outcome":"provider_or_analysis_failure","output":"missing provider"}',
        ]
        with patch.object(base,"safe_to_run",return_value=True), \
             patch.object(rea_analysis,"_run",side_effect=responses) as cli:
            verdict=base.rea_probe()
            self.assertEqual(verdict["doctor_outcome"],"observed")
            self.assertEqual(verdict["static_fixture_outcome"],"provider_or_analysis_failure")
            self.assertEqual(cli.call_count,2)
            self.assertEqual(cli.call_args.args[0][0],"analyze-javascript-application")
            self.assertEqual(cli.call_args.args[0][1],str(base.FIXTURE))
            self.assertNotIn("Muse",str(cli.call_args))
            self.assertNotIn("GrokBot",str(cli.call_args))

    def test_result_privacy_and_wrong_revision_are_unverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"report.json"
            path.write_text(json.dumps({
                "installed_commit":SHA,"evaluation_type":"actual_installed_model_not_mock",
                "status":"completed","checked_at":"2026-10-13T00:00:00+00:00",
                "model":{"present":True,"tools_capable":True,"vision_capable":False,
                         "cases_passed":3,"cases_total":5,
                         "local_model_name":"PRIVATE_MODEL_NAME","raw_reply":"PRIVATE_REPLY"},
                "rea":{"doctor_outcome":"unavailable",
                       "static_fixture_outcome":"not_run","private_stdout":"SECRET"}}))
            with patch.object(base,"REPORT",path):
                published=base.public_summary(SHA)
                self.assertEqual(published["test_cases_passed"],3)
                self.assertEqual(base.public_summary("b"*40)["status"],"unverified")
                self.assertNotIn("PRIVATE",json.dumps(published))
                self.assertNotIn("local_model_name",published)
                self.assertNotIn("raw_reply",published)
                self.assertNotIn("private_stdout",published)

    def test_dead_worker_gets_one_bounded_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            py=path/"pythonw.exe"
            py.write_text("fixture")
            state=path/"state.json"
            stale=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(minutes=20)).isoformat()
            state.write_text(json.dumps({
                "installed_commit":SHA,"status":"running",
                "checked_at":stale,"worker_pid":321
            }))
            process=Mock(pid=654)
            class MissingProcess(Exception):
                pass
            fake_psutil=type("FakePsutil",(),{
                "NoSuchProcess":MissingProcess,
                "Process":staticmethod(lambda pid: (_ for _ in ()).throw(MissingProcess()))
            })
            with patch.object(base,"STATE",state), \
                 patch.object(base,"PYTHONW",py), \
                 patch.object(base,"safe_to_run",return_value=True), \
                 patch.object(base,"is_windows",return_value=True), \
                 patch.object(base,"installed_sha",return_value=SHA), \
                 patch.dict(sys.modules,{"psutil":fake_psutil}), \
                 patch.object(base.subprocess,"Popen",return_value=process) as popen:
                self.assertEqual(base.launch_if_due(),"started")
                self.assertEqual(base.launch_if_due(),"already_launched")
                popen.assert_called_once()
            saved=json.loads(state.read_text())
            self.assertEqual(saved["recovery_attempts"],1)
            self.assertEqual(saved["worker_pid"],654)

    def test_launch_uses_existing_windowless_venv_only_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            py=path/"pythonw.exe"
            py.write_text("fixture")
            state=path/"state.json"
            process=Mock(pid=123)
            with patch.object(base,"STATE",state), \
                 patch.object(base,"PYTHONW",py), \
                 patch.object(base,"safe_to_run",return_value=True), \
                 patch.object(base,"is_windows",return_value=True), \
                 patch.object(base,"installed_sha",return_value=SHA), \
                 patch.object(base.subprocess,"Popen",return_value=process) as popen:
                self.assertEqual(base.launch_if_due(),"started")
                self.assertEqual(base.launch_if_due(),"already_launched")
                popen.assert_called_once()
                args=popen.call_args.args[0]
                self.assertEqual(args[0],str(py))
                self.assertIn("--run",args)
                self.assertEqual(popen.call_args.kwargs["creationflags"],base.NO_WINDOW)


if __name__=="__main__":
    unittest.main()
