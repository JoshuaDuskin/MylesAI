"""v10.15.9: verifiable lost-receipt recovery and local model readiness."""
from __future__ import annotations
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from bin import remote_deploy_agent as agent
from bin import intelligence_baseline as baseline
from bin import tower_health_issue as health_issue
from myles_model_runtime import ModelHealth

SHA = "a" * 40


def stale_state(status="failed_unverified"):
    return {
        "status": status, "source": "ci_approved_main",
        "target_sha": SHA, "request_id": "ci_" + SHA,
        "wrapper_pid": 8765,
        "started_at": (dt.datetime.now(dt.timezone.utc) -
                       dt.timedelta(hours=3)).isoformat(),
    }


def observed():
    return {"installed_commit": SHA, "core_healthy": True,
            "bridge_reachable": True, "gateway_reachable": True,
            "quant_feed_verified_and_fresh": True}


class RecoveryTests(unittest.TestCase):
    def test_timed_out_installed_release_requires_live_evidence(self):
        with patch.object(agent, "process_running", return_value=False), \
             patch.object(agent, "git", return_value=SHA), \
             patch.object(agent, "verify_ci", return_value=True), \
             patch.object(health_issue, "snapshot", return_value=observed()):
            result = agent.reconcile_interrupted_update(stale_state(), {})
        self.assertEqual(result["status"], "installed_verified_post_restart")
        self.assertTrue(result["receipt_missing"])
        self.assertNotEqual(result["status"], "succeeded")

    def test_no_recovery_if_any_verified_tower_service_fails(self):
        for field in ("core_healthy", "bridge_reachable", "gateway_reachable",
                      "quant_feed_verified_and_fresh"):
            broken = observed()
            broken[field] = False
            with self.subTest(field=field), \
                 patch.object(agent, "process_running", return_value=False), \
                 patch.object(agent, "git", return_value=SHA), \
                 patch.object(agent, "verify_ci", return_value=True), \
                 patch.object(health_issue, "snapshot", return_value=broken):
                self.assertIsNone(
                    agent.reconcile_interrupted_update(stale_state(), {}))

    def test_never_recover_while_wrapper_runs_or_ci_fails(self):
        with patch.object(agent, "process_running", return_value=True), \
             patch.object(agent, "git", return_value=SHA):
            self.assertIsNone(agent.reconcile_interrupted_update(stale_state(), {}))
        with patch.object(agent, "process_running", return_value=False), \
             patch.object(agent, "git", return_value=SHA), \
             patch.object(agent, "verify_ci", return_value=False):
            self.assertIsNone(agent.reconcile_interrupted_update(stale_state(), {}))
        self.assertIsNone(agent.reconcile_interrupted_update(
            stale_state(), {"request_id": "ci_" + SHA, "success": False}))

    def test_expired_and_noncanonical_states_are_not_recovered(self):
        old = stale_state()
        old["started_at"] = (dt.datetime.now(dt.timezone.utc) -
                             dt.timedelta(days=9)).isoformat()
        self.assertIsNone(agent.reconcile_interrupted_update(old, {}))
        other = stale_state()
        other["source"] = "untrusted"
        self.assertIsNone(agent.reconcile_interrupted_update(other, {}))

    def test_poll_reconciles_fail_state_without_new_updater(self):
        record = stale_state()
        with patch.object(agent, "read_json", side_effect=lambda p:
                          {"enabled": True} if p == agent.ENABLED
                          else record if p == agent.STATE else {}), \
             patch.object(agent, "lock", return_value=Mock()), \
             patch.object(agent, "reconcile_interrupted_update", return_value={
                 **record, "status": "installed_verified_post_restart"}), \
             patch.object(agent, "write_json") as written, \
             patch.object(agent, "git") as git, \
             patch.object(agent, "report_tower_health"), \
             patch.object(agent, "start_intelligence_baseline"):
            self.assertEqual(agent.poll(), 0)
            git.assert_not_called()
            self.assertEqual(written.call_args.args[1]["status"],
                             "installed_verified_post_restart")


class ModelBaselineTests(unittest.TestCase):
    def test_provider_is_recovered_before_real_model_benchmark(self):
        good = ModelHealth(True, model="installed-model", endpoint="http://127.0.0.1:11434",
                           capabilities=("completion", "tools"))
        with patch("myles_common.load_config", return_value={
                 "ollama_url": "http://127.0.0.1:11434/api/chat"}), \
             patch("myles_model_runtime.ensure_model_runtime", return_value=good) as recovery:
            base, model, caps = baseline.ollama_identity()
        recovery.assert_called_once_with(
            {"ollama_url": "http://127.0.0.1:11434/api/chat"}, force=True)
        self.assertEqual(base, "http://127.0.0.1:11434")
        self.assertEqual(model, "installed-model")
        self.assertIn("tools", caps)

    def test_missing_model_is_typed_and_not_downloaded(self):
        missing = ModelHealth(False, error_kind="no_chat_model")
        with patch("myles_common.load_config", return_value={}), \
             patch("myles_model_runtime.ensure_model_runtime", return_value=missing):
            with self.assertRaises(baseline.ModelProbeUnavailable) as caught:
                baseline.ollama_identity()
        self.assertEqual(str(caught.exception), "no_chat_model")

    def test_nonlocal_provider_never_contacted(self):
        with patch("myles_common.load_config", return_value={
                 "ollama_url": "https://example.com/api/chat"}), \
             patch("myles_model_runtime.ensure_model_runtime") as recovery:
            with self.assertRaises(baseline.ModelProbeUnavailable):
                baseline.ollama_identity()
            recovery.assert_not_called()

    def test_public_report_only_allows_fixed_model_issue(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "baseline.json"
            obj = {"installed_commit": SHA, "evaluation_type":
                   "actual_installed_model_not_mock", "status": "completed",
                   "model": {"failure_kind": "no_chat_model", "cases_total": 5},
                   "rea": {}}
            p.write_text(json.dumps(obj))
            with patch.object(baseline, "REPORT", p):
                self.assertEqual(
                    baseline.public_summary(SHA)["model_runtime_issue"], "no_chat_model")
                obj["model"]["failure_kind"] = "C:/secret/private-token"
                p.write_text(json.dumps(obj))
                self.assertEqual(
                    baseline.public_summary(SHA)["model_runtime_issue"], "unknown")

    def test_windows_updater_preserves_receipt_parent_if_cim_fails(self):
        root=Path(__file__).resolve().parents[1]
        source=(root / "UPDATE_TOWER.ps1").read_text(encoding="utf-8")
        self.assertIn("$IsRemoteReceiptWriter = $RemoteQuiet", source)
        self.assertIn("-not $IsRemoteReceiptWriter", source)
        self.assertIn("remote_deploy_apply", source)


if __name__ == "__main__":
    unittest.main()
