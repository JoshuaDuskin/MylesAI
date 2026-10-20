"""Regression: Windows updater must not terminate its own receipt writer.

All verification tests use synthetic Windows state and mocked source/CI/health.
They do not treat Linux CI as an actual Windows tower installation.
"""
from __future__ import annotations
import datetime as dt
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bin import remote_deploy_agent as agent
from bin import verified_release as release
from bin import tower_health_issue as issue

SHA="a"*40
OTHER="b"*40


def launched(sha=SHA,*,age=600):
    return {
        "source":"ci_approved_main","request_id":"ci_"+sha,
        "target_sha":sha,"status":"launched","wrapper_pid":12345,
        "started_at":(dt.datetime.now(dt.timezone.utc)-dt.timedelta(seconds=age)).isoformat(),
    }


def healthy(sha=SHA):
    return {"installed_commit":sha,"core_healthy":True,
            "bridge_reachable":True,"gateway_reachable":True,
            "quant_feed_verified_and_fresh":True}


class ReceiptRecoveryTests(unittest.TestCase):
    def _guards(self,snapshot=None,*,wrapper_alive=False,head=SHA,ci=True):
        from contextlib import ExitStack
        s=ExitStack()
        s.enter_context(patch.object(agent,"wrapper_process_running",return_value=wrapper_alive))
        s.enter_context(patch.object(agent,"git",return_value=head))
        s.enter_context(patch.object(agent,"verify_ci",return_value=ci))
        s.enter_context(patch.object(issue,"snapshot",return_value=snapshot if snapshot is not None else healthy()))
        return s

    def test_pid_identity_distinguishes_reused_process_from_wrapper(self):
        class NoSuchProcess(Exception):
            pass

        unrelated=SimpleNamespace(
            Process=lambda pid: SimpleNamespace(
                cmdline=lambda: ["python.exe","unrelated_worker.py"]),
            NoSuchProcess=NoSuchProcess,
        )
        wrapper=SimpleNamespace(
            Process=lambda pid: SimpleNamespace(
                cmdline=lambda: ["powershell.exe","-File",str(agent.APPLY)]),
            NoSuchProcess=NoSuchProcess,
        )
        with patch.object(agent,"process_running",return_value=True), \
             patch.dict(sys.modules,{"psutil":unrelated}):
            self.assertFalse(agent.wrapper_process_running(12345))
        with patch.object(agent,"process_running",return_value=True), \
             patch.dict(sys.modules,{"psutil":wrapper}):
            self.assertTrue(agent.wrapper_process_running(12345))

    def test_recovered_state_is_not_faked_as_successful_wrapper_receipt(self):
        with self._guards():
            result=agent.reconcile_interrupted_update(launched(),{})
        self.assertEqual(result["status"],"installed_verified_post_restart")
        self.assertEqual(result["verification_source"],"git_ci_and_live_local_services")
        self.assertTrue(result["receipt_missing"])
        self.assertTrue(result["post_restart_health_verified"])
        self.assertNotIn("updater_exit_code",result)
        self.assertNotEqual(result["status"],"succeeded")

    def test_mismatched_or_failed_local_checks_block_recovery(self):
        variants=(
            {"installed_commit":OTHER},
            {"core_healthy":False},
            {"bridge_reachable":False},
            {"gateway_reachable":False},
            {"quant_feed_verified_and_fresh":False},
        )
        for changes in variants:
            with self.subTest(changes=changes),self._guards({**healthy(),**changes}):
                self.assertIsNone(agent.reconcile_interrupted_update(launched(),{}))
        with self._guards(head=OTHER):
            self.assertIsNone(agent.reconcile_interrupted_update(launched(),{}))
        with self._guards(ci=False):
            self.assertIsNone(agent.reconcile_interrupted_update(launched(),{}))

    def test_no_early_recovery_while_wrapper_running_or_receipt_available(self):
        with self._guards(wrapper_alive=True):
            self.assertIsNone(agent.reconcile_interrupted_update(launched(),{}))
        with self._guards():
            self.assertIsNone(agent.reconcile_interrupted_update(launched(age=120),{}))
            self.assertIsNone(agent.reconcile_interrupted_update(launched(),{"request_id":"ci_"+SHA}))
            self.assertIsNone(agent.reconcile_interrupted_update({
                **launched(),"source":"untrusted_issue_comment"},{}))
            self.assertIsNone(agent.reconcile_interrupted_update({
                **launched(),"request_id":"not_the_CI_request"},{}))

    def test_candidate_never_reinstalls_independently_verified_sha(self):
        accepted,reason=release.candidate_allowed(
            SHA,OTHER,{"request_id":"ci_"+SHA,
                       "status":"installed_verified_post_restart"},True,True)
        self.assertFalse(accepted)
        self.assertIn("already attempted",reason)
    
    def test_orphaned_legacy_launch_becomes_explicitly_unverified(self):
        from contextlib import ExitStack
        state = launched(age=3*3600)
        state.pop("wrapper_pid")
        with ExitStack() as s:
            s.enter_context(patch.object(agent,"ENABLED",Path("remote_deploy_enabled.json")))
            s.enter_context(patch.object(agent,"STATE",Path("remote_deploy_state.json")))
            s.enter_context(patch.object(agent,"RESULT",Path("remote_deploy_result.json")))
            s.enter_context(patch.object(agent,"read_json",side_effect=lambda p:(
                {"enabled":True,"auto_update":True}
                if p==agent.ENABLED else state
                if p==agent.STATE else {})))
            s.enter_context(patch.object(agent,"lock",return_value=type("Held",(),{"close":lambda self:None})()))
            s.enter_context(patch.object(agent,"reconcile_interrupted_update",return_value=None))
            s.enter_context(patch.object(agent,"report_tower_health"))
            s.enter_context(patch.object(agent,"start_intelligence_baseline"))
            s.enter_context(patch.object(agent,"process_running",return_value=False))
            write=s.enter_context(patch.object(agent,"write_json"))
            self.assertEqual(agent.poll(),0)
        self.assertEqual(write.call_args.args[1]["status"],"failed_unverified")
        self.assertEqual(write.call_args.args[1]["reason"],"receipt missing after wrapper exited")

    def test_reporter_keeps_missing_receipt_explicit(self):
        with patch.object(issue,"git",side_effect=lambda *args:
                 SHA if args[0]=="rev-parse" else issue.ORIGIN), \
             patch.object(issue,"core_health",return_value=(True,"10.15.2")), \
             patch.object(issue,"port_up",return_value=True), \
             patch.object(issue,"quant_feed_verified",return_value=True), \
             patch.object(issue,"worker_counts",return_value={
                 "quant":1,"gmx":1,"copy_research":1}), \
             patch.object(issue,"intelligence_summary",return_value={"status":"unverified"}), \
             patch.object(issue,"read_json",side_effect=lambda path,**kwargs:
                {"status":"installed_verified_post_restart",
                 "installed_sha":SHA,"post_restart_health_verified":True,
                 "target_sha":SHA} if Path(path).name=="remote_deploy_state.json" else {}):
            data=issue.snapshot()
        self.assertTrue(data["deployment"]["verified_after_restart"])
        self.assertFalse(data["deployment"]["verified_local_receipt_matches_installed"])
        self.assertEqual(data["deployment"]["last_state"],"installed_verified_post_restart")

    def test_powershell_parent_writer_is_exempt_from_cleanup(self):
        script=(Path(__file__).resolve().parents[1]/"UPDATE_TOWER.ps1").read_text(encoding="utf-8")
        self.assertIn("Protecting CI receipt writer PID",script)
        self.assertIn("remote_deploy_apply",script)
        self.assertIn("$ParentProc.CommandLine",script)
        self.assertIn("$RemoteQuiet -and $ExpectedHead",script)
        self.assertIn("$_.ProcessId -ne $ReceiptWriterPid",script)
        self.assertIn("Stop-Process -Id $proc.ProcessId",script)

    def test_poll_reconciles_before_reporting_and_benchmark(self):
        from contextlib import ExitStack
        with ExitStack() as s:
            s.enter_context(patch.object(agent,"ENABLED",Path("remote_deploy_enabled.json")))
            s.enter_context(patch.object(agent,"read_json",side_effect=lambda p:(
                {"enabled":True,"auto_update":True}
                if p==agent.ENABLED else launched()
                if p==agent.STATE else {})))
            class Held:
                def close(self):pass
            s.enter_context(patch.object(agent,"lock",return_value=Held()))
            s.enter_context(patch.object(agent,"reconcile_interrupted_update",
                                         return_value={"status":"installed_verified_post_restart"}))
            write=s.enter_context(patch.object(agent,"write_json"))
            s.enter_context(patch.object(agent,"report_tower_health"))
            s.enter_context(patch.object(agent,"start_intelligence_baseline"))
            self.assertEqual(agent.poll(),0)
            write.assert_called_once()
            self.assertEqual(write.call_args.args[1]["status"],
                             "installed_verified_post_restart")


if __name__=="__main__":
    unittest.main()
