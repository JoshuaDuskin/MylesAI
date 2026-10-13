"""CI-approved tower auto-update regressions. No Windows service is touched."""
from __future__ import annotations
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from bin import verified_release as release
from bin import remote_deploy_agent as agent

OLD = "a" * 40
NEW = "b" * 40


def workflow(sha=NEW, *, conclusion="success", event="push", status="completed",
             path=".github/workflows/validate-runtime.yml", branch="main",
             repo=release.REPO):
    return {"head_sha": sha, "status": status, "conclusion": conclusion,
            "event": event, "head_branch": branch, "path": path,
            "repository": {"full_name": repo}}


class VerifiedReleaseTests(unittest.TestCase):
    def test_only_matching_completed_main_push_is_approved(self):
        p = {"workflow_runs": [workflow()]}
        self.assertTrue(release.approved_run(NEW, p))
        for kwargs in (
            {"sha": OLD}, {"conclusion": "failure"}, {"conclusion": None},
            {"status": "in_progress"}, {"status": "queued"}, {"event": "pull_request"},
            {"path": ".github/workflows/another.yml"}, {"branch": "feature"},
            {"repo": "somebody/another-project"},
        ):
            with self.subTest(kwargs=kwargs):
                self.assertFalse(release.approved_run(NEW, {
                    "workflow_runs": [workflow(**kwargs)]
                }))
        self.assertFalse(release.approved_run("not-a-sha", p))
        self.assertFalse(release.approved_run(NEW, {"workflow_runs": "wrong"}))

    def test_candidate_rejects_unchanged_rewritten_failed_and_repeated(self):
        state = {"status": "succeeded", "request_id": "ci_" + NEW}
        self.assertEqual(release.candidate_allowed(NEW, NEW, {}, True, True)[1],
                         "already installed")
        self.assertFalse(release.candidate_allowed(NEW, OLD, {}, False, True)[0])
        self.assertFalse(release.candidate_allowed(NEW, OLD, {}, True, False)[0])
        self.assertFalse(release.candidate_allowed(NEW, OLD, state, True, True)[0])
        self.assertTrue(release.candidate_allowed(NEW, OLD, {}, True, True)[0])
        for status in ("launched", "succeeded", "failed", "failed_unverified"):
            with self.subTest(status=status):
                record={"request_id":"ci_"+NEW,"status":status}
                self.assertFalse(release.candidate_allowed(NEW, OLD, record, True, True)[0])

    def test_approved_release_will_only_launch_fixed_wrapper_once(self):
        with tempfile.TemporaryDirectory() as d:
            state_path=Path(d)/"state.json"
            apply=Path(d)/"fixed_apply.ps1"
            apply.write_text("# fixture", encoding="utf8")
            process=Mock(pid=31415)
            with patch.object(agent, "STATE", state_path), \
                 patch.object(agent, "APPLY", apply), \
                 patch.object(agent, "is_windows", return_value=True), \
                 patch.object(agent.subprocess, "STARTUPINFO", return_value=Mock(), create=True), \
                 patch.object(agent.subprocess, "Popen", return_value=process) as proc, \
                 patch.object(agent, "git", side_effect=lambda *args:
                              OLD if args[0]=="rev-parse" else OLD), \
                 patch.object(agent, "verify_ci", return_value=True), \
                 patch.object(agent, "idle_gate", return_value=""):
                self.assertEqual(agent.try_approved_release(NEW, {}), 0)
                result=json.loads(state_path.read_text())
                self.assertEqual(result["request_id"], "ci_"+NEW)
                self.assertEqual(result["wrapper_pid"], 31415)
                args=proc.call_args.args[0]
                self.assertEqual(args[-4:], ["-RequestId","ci_"+NEW,"-ExpectedHead",NEW])
                self.assertNotIn("cmd.exe", args)

    def test_games_and_pending_work_block_wrapper(self):
        with patch.object(agent, "git", side_effect=lambda *args: OLD), \
             patch.object(agent, "verify_ci", return_value=True), \
             patch.object(agent, "idle_gate", return_value="game running"), \
             patch.object(agent, "write_json"), \
             patch.object(agent.subprocess, "Popen") as proc:
            self.assertEqual(agent.try_approved_release(NEW, {}), 0)
            proc.assert_not_called()

    def test_failed_ci_or_non_descendant_never_launches(self):
        with patch.object(agent,"git",side_effect=lambda *args: OLD), \
             patch.object(agent, "verify_ci", return_value=False), \
             patch.object(agent,"write_json"), \
             patch.object(agent.subprocess,"Popen") as p:
            self.assertEqual(agent.try_approved_release(NEW, {}),0)
            p.assert_not_called()
        with patch.object(agent,"git",side_effect=lambda *args: "c"*40 if args[0]=="merge-base" else OLD), \
             patch.object(agent, "verify_ci") as ci, \
             patch.object(agent, "write_json"), \
             patch.object(agent.subprocess, "Popen") as p:
            self.assertEqual(agent.try_approved_release(NEW, {}),0)
            ci.assert_not_called()
            p.assert_not_called()

    def test_auto_mode_skips_request_marker_completely(self):
        class Lock:
            def close(self): pass
        with patch.object(agent,"ENABLED",Path("remote_deploy_enabled.json")), \
             patch.object(agent,"read_json",side_effect=lambda p: {
                 "enabled":True,"auto_update":True} if p.name=="remote_deploy_enabled.json" else {}), \
             patch.object(agent,"lock",return_value=Lock()), \
             patch.object(agent,"git",side_effect=lambda *args: NEW if args[0]=="rev-parse" else ""), \
             patch.object(agent,"try_approved_release",return_value=0) as auto:
            self.assertEqual(agent.poll(),0)
            auto.assert_called_once()
            self.assertEqual(auto.call_args.args[0],NEW)

    def test_exact_revision_is_pinned_and_opt_in(self):
        base=Path(__file__).resolve().parents[1]
        updater=(base/"UPDATE_TOWER.ps1").read_text(encoding="utf8")
        launcher=(base/"bin"/"remote_deploy_apply.ps1").read_text(encoding="utf8")
        enable=(base/"ENABLE_REMOTE_DEPLOY.ps1").read_text(encoding="utf8")
        self.assertEqual(updater.count("Installing exact CI-approved revision"),1)
        self.assertEqual(updater.count("[CmdletBinding()]"),1)
        self.assertIn('"cat-file", "-t", $ExpectedHead',updater)
        self.assertIn('"checkout", "-B", "main", $CheckoutRef',updater)
        self.assertIn('-RemoteQuiet -ExpectedHead $ExpectedHead',launcher)
        self.assertIn('auto_update = $true',enable)
        self.assertIn('Register-ScheduledTask',enable)


if __name__=="__main__":
    unittest.main()
