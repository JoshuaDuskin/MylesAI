"""Remote deployment control-plane tests; never invoke a real Windows updater."""
from __future__ import annotations
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bin import remote_deploy_agent as agent

SOURCE = "a" * 40
MARKER = "b" * 40
NOW = dt.datetime(2026, 10, 13, 3, 0, tzinfo=dt.timezone.utc)
REQ = {"schema": 1, "action": "update",
       "request_id": "chat_20261013_12345678",
       "target_sha": SOURCE,
       "requested_at": NOW.isoformat()}


class RemoteDeployTests(unittest.TestCase):
    def test_request_must_be_exact_main_child_and_single_file(self):
        self.assertEqual(agent.validate(REQ, MARKER, SOURCE,
                                        agent.REQUEST_PATH, NOW), "")
        self.assertIn("descendant", agent.validate(REQ, MARKER, MARKER,
                      agent.REQUEST_PATH, NOW))
        self.assertIn("other files", agent.validate(REQ, MARKER, SOURCE,
                      agent.REQUEST_PATH + "\nmyles_core.py", NOW))
        self.assertIn("expired", agent.validate(REQ, MARKER, SOURCE,
                      agent.REQUEST_PATH, NOW + dt.timedelta(days=2)))
        self.assertEqual(agent.validate({"schema": 1, "action": "idle"},
                      MARKER, SOURCE, agent.REQUEST_PATH, NOW), "idle")

    def test_disallow_arguments_payloads_and_non_update_actions(self):
        for payload in [
            {**REQ, "action": "shell", "command": "whoami"},
            {**REQ, "command": "calc.exe"},
            {**REQ, "url": "https://example.com/code.ps1"},
            {**REQ, "target_sha": "not-a-real-sha"},
            {**REQ, "request_id": "bad"},
            {**REQ, "requested_at": "2026-10-13T03:00:00"},
        ]:
            self.assertNotEqual(agent.validate(payload, MARKER, SOURCE,
                                                agent.REQUEST_PATH, NOW), "")

    def test_disabled_agent_does_not_touch_network_or_execution(self):
        with patch.object(agent, "read_json", return_value={"enabled": False}), \
             patch.object(agent, "git") as git, \
             patch.object(agent.subprocess, "Popen") as spawn:
            self.assertEqual(agent.poll(), 0)
            git.assert_not_called()
            spawn.assert_not_called()

    def test_game_mode_and_active_job_defers(self):
        with patch.object(agent, "read_json", side_effect=lambda p:
                          {"light_mode": True} if p.name == "config.json" else {}):
            self.assertEqual(agent.idle_gate(), "light mode")
        with patch.object(agent, "read_json", return_value={}), \
             patch.object(agent.urllib.request, "urlopen") as client:
            client.return_value.__enter__.return_value.read.return_value = json.dumps(
                {"jobs": [{"state": "running"}]}).encode()
            self.assertEqual(agent.idle_gate(), "owner task active")

    def test_launched_state_cannot_replay_and_reconciles_once(self):
        with tempfile.TemporaryDirectory(prefix="myles_remote_test_") as d:
            root = Path(d)
            state = root / "state.json"
            receipt = root / "result.json"
            enabled = root / "enabled.json"
            enabled.write_text('{"enabled":true}', encoding="utf-8")
            state.write_text(json.dumps({"status": "launched",
                                         "request_id": REQ["request_id"]}), encoding="utf-8")
            receipt.write_text(json.dumps({"request_id": REQ["request_id"],
                                           "success": True, "installed_sha": MARKER,
                                           "health_verified": True, "updater_exit_code": 0}),
                               encoding="utf-8")
            with patch.object(agent, "ENABLED", enabled), \
                 patch.object(agent, "STATE", state), \
                 patch.object(agent, "RESULT", receipt), \
                 patch.object(agent, "lock", return_value=open(root / "lock", "w")), \
                 patch.object(agent, "git") as git, \
                 patch.object(agent.subprocess, "Popen") as spawn:
                self.assertEqual(agent.poll(), 0)
                self.assertEqual(json.loads(state.read_text())["status"], "succeeded")
                self.assertEqual(agent.poll(), 0)
                git.assert_called()
                spawn.assert_not_called()

    def test_installer_is_fixed_purpose(self):
        repo = Path(__file__).resolve().parents[1]
        installer = (repo / "ENABLE_REMOTE_DEPLOY.ps1").read_text()
        wrapper = (repo / "bin" / "remote_deploy_apply.ps1").read_text()
        updater = (repo / "UPDATE_TOWER.ps1").read_text()
        self.assertIn('Register-ScheduledTask -TaskName $TaskName', installer)
        self.assertIn("MylesAI Remote Deploy Poll", installer)
        self.assertIn('UPDATE_TOWER.ps1', wrapper)
        self.assertIn("-RemoteQuiet", wrapper)
        self.assertIn("if (-not $RemoteQuiet) { pause }", updater)
        self.assertNotIn("Invoke-Expression", wrapper)


if __name__ == "__main__":
    unittest.main()
