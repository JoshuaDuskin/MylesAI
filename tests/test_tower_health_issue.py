"""Single canonical repository issue #49 reporting; no real GH writes."""
from __future__ import annotations
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bin import tower_health_issue as issue
from bin import remote_deploy_agent as agent

COMMIT="a"*40
UTC=dt.datetime(2026,10,13,20,0,tzinfo=dt.timezone.utc)


def valid_issue():
    return {"number":49,"state":"open","user":{"login":"JoshuaDuskin"},
            "body":"Before upload\n"+issue.MARKER}


class HealthIssueTests(unittest.TestCase):
    def test_single_existing_repository_and_issue_only(self):
        self.assertEqual(issue.ISSUE_REPO,"JoshuaDuskin/MylesAI")
        self.assertEqual(issue.ISSUE_NUMBER,49)
        self.assertEqual(issue.ISSUE_PATH,"repos/JoshuaDuskin/MylesAI/issues/49")
        self.assertNotIn("MylesTowerReceipts",issue.ISSUE_PATH)

    def test_snapshot_contains_no_credentials_paths_wallet_or_private_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            (d/"remote_deploy_result.json").write_text(json.dumps({
                "success":True,"health_verified":True,"installed_sha":COMMIT,
                "expected_head":COMMIT,"updater_exit_code":0,
                "private_token":"DONT_EVER_REPORT_SECRET_A"}))
            (d/"remote_deploy_state.json").write_text(json.dumps({
                "status":"succeeded","target_sha":COMMIT,"private_note":"DONT_EVER_REPORT_SECRET_B"}))
            (d/"trading_status.json").write_text(json.dumps({
                "_verified":True,"_verified_source":"data/trading_status.json",
                "wallet":"DONT_EVER_REPORT_SECRET_C","paper_equity":100.0}))
            with patch.object(issue,"DATA",d), \
                 patch.object(issue,"git",side_effect=lambda *args:
                     COMMIT if args[0]=="rev-parse" else issue.ORIGIN), \
                 patch.object(issue,"core_health",return_value=(True,"10.14.0")), \
                 patch.object(issue,"port_up",return_value=True), \
                 patch.object(issue,"worker_counts",return_value={
                     "quant":1,"gmx":1,"copy_research":1}), \
                 patch.object(issue,"now",return_value=UTC):
                # use real current time to evaluate feed freshness independently
                result=issue.snapshot()
            self.assertEqual(result["installed_commit"],COMMIT)
            self.assertEqual(result["myles_version"],"10.14.0")
            self.assertTrue(result["deployment"]["verified_local_receipt_matches_installed"])
            self.assertEqual(result["worker_processes"]["quant"],1)
            raw=json.dumps(result)
            self.assertNotIn("DONT_EVER_REPORT_SECRET",raw)
            self.assertNotIn("wallet",raw)
            self.assertNotIn("paper_equity",raw)
            self.assertNotIn(str(d),raw)
            self.assertNotIn("Fortnite",raw)
            body=issue.format_issue(result)
            self.assertIn("PUBLIC, sanitized",body)
            self.assertIn(issue.MARKER,body)
            self.assertNotIn("DONT_EVER_REPORT_SECRET",body)

    def test_quant_truth_reuses_the_existing_gateway_validator(self):
        from bin import public_gateway_v074 as gateway
        with patch.object(gateway, "local_trading_snapshot",
                          return_value=({"_verified":True},{"verified":True})):
            self.assertTrue(issue.quant_feed_verified())
        with patch.object(gateway, "local_trading_snapshot",
                          return_value=(None,{"verified":False,"status":"stale"})):
            self.assertFalse(issue.quant_feed_verified())

    def test_wrong_source_cannot_report(self):
        with patch.object(issue,"git",return_value="not-canonical"):
            with self.assertRaises(ValueError):
                issue.snapshot(UTC)

    def test_receipt_from_other_commit_not_marked_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            (d/"remote_deploy_result.json").write_text(json.dumps({
                "success":True,"health_verified":True,"installed_sha":"b"*40,
                "expected_head":"b"*40,"updater_exit_code":0}))
            with patch.object(issue,"DATA",d), \
                 patch.object(issue,"git",side_effect=lambda *args:
                     COMMIT if args[0]=="rev-parse" else issue.ORIGIN), \
                 patch.object(issue,"core_health",return_value=(False,None)), \
                 patch.object(issue,"port_up",return_value=False), \
                 patch.object(issue,"worker_counts",return_value={}):
                report=issue.snapshot(UTC)
                self.assertFalse(report["deployment"]["verified_local_receipt_matches_installed"])
                self.assertFalse(report["core_healthy"])

    def test_public_issue_must_be_exact_owner_and_marker(self):
        for bad in [
            {"number":47,**{k:v for k,v in valid_issue().items() if k!="number"}},
            {**valid_issue(),"user":{"login":"someone_else"}},
            {**valid_issue(),"body":"marker missing"},
            {**valid_issue(),"state":"closed"},
        ]:
            with self.subTest(issue=bad), \
                 patch.object(issue,"execute",return_value=(0,json.dumps(bad))) as api:
                self.assertFalse(issue.publish({"schema":1},"gh",{}))
                self.assertEqual(api.call_count,1)

    def test_valid_public_issue_receives_only_one_patch(self):
        seen=[]
        def execute(args,**kwargs):
            seen.append((args,kwargs))
            if len(seen)==1:
                return 0,json.dumps(valid_issue())
            if len(seen)==2:
                self.assertEqual(args,["gh","api","-X","PATCH",issue.ISSUE_PATH,
                                       "--input","-"])
                body=json.loads(kwargs["data"])["body"]
                self.assertIn('"installed_commit"',body)
                self.assertIn(issue.MARKER,body)
                self.assertNotIn("secret",body)
                return 0,json.dumps(valid_issue())
            raise AssertionError("unexpected network call")
        with patch.object(issue,"execute",side_effect=execute):
            self.assertTrue(issue.publish({"installed_commit":COMMIT},"gh",{}))
            self.assertEqual(len(seen),2)

    def test_disabled_and_game_mode_do_not_touch_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            flag=d/"enabled.json"
            flag.write_text('{"enabled":false,"auto_update":true}')
            with patch.object(issue,"ENABLED",flag), \
                 patch.object(issue,"DATA",d), \
                 patch.object(issue,"dedicated_gh") as gh:
                self.assertEqual(issue.tick(),"disabled")
                gh.assert_not_called()
            flag.write_text('{"enabled":true,"auto_update":true}')
            (d/"game_mode_state.json").write_text('{"active":true}')
            with patch.object(issue,"ENABLED",flag), \
                 patch.object(issue,"DATA",d), \
                 patch.object(issue,"dedicated_gh") as gh:
                self.assertEqual(issue.tick(),"deferred_during_game")
                gh.assert_not_called()

    def test_no_dedicated_credential_never_publishes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            f=d/"enabled.json"
            f.write_text('{"enabled":true,"auto_update":true}')
            with patch.object(issue,"ENABLED",f), \
                 patch.object(issue,"DATA",d), \
                 patch.object(issue,"STATE",d/"publisher.json"), \
                 patch.object(issue,"snapshot",return_value={"installed_commit":COMMIT}), \
                 patch.object(issue,"dedicated_gh",return_value=None), \
                 patch.object(issue,"publish") as publish:
                self.assertEqual(issue.tick(),"dedicated_github_auth_unavailable")
                self.assertEqual(issue.read_json(d/"publisher.json")["result"],
                                 "dedicated_github_auth_unavailable")
                publish.assert_not_called()

    def test_dedicated_profile_must_be_owner_and_not_other_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            (d/"github_identity.json").write_text(json.dumps({
                "owner":"PineTreePayments","gh_config_dir":str(d)}))
            with patch.object(issue,"DATA",d),patch.object(issue,"execute") as run:
                self.assertIsNone(issue.dedicated_gh())
                run.assert_not_called()
            (d/"github_identity.json").write_text(json.dumps({
                "owner":"JoshuaDuskin","gh_config_dir":str(d/"PineTree-credentials")}))
            with patch.object(issue,"DATA",d),patch.object(issue,"execute") as run:
                self.assertIsNone(issue.dedicated_gh())
                run.assert_not_called()

    def test_verified_owner_default_gh_profile_can_report_without_extra_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=Path(tmp)
            # No dedicated local GH profile has been configured.
            # A verified, already-authorized owner CLI profile suffices.
            with patch.object(issue,"DATA",data), \
                 patch.object(issue.shutil,"which",return_value="gh"), \
                 patch.object(issue,"execute",return_value=(0,"JoshuaDuskin\n")) as api, \
                 patch.dict(issue.os.environ,{"GH_TOKEN":"inherited_should_never_be_used",
                                             "GH_CONFIG_DIR":str(data/"untrusted-env")}):
                creds=issue.dedicated_gh()
                self.assertIsNotNone(creds)
                self.assertEqual(creds[0],"gh")
                self.assertNotIn("GH_TOKEN",creds[1])
                self.assertNotIn("GH_CONFIG_DIR",creds[1])
                api.assert_called_once()
                self.assertEqual(api.call_args.args[0],
                                 ["gh","api","user","--jq",".login"])

    def test_non_owner_default_gh_identity_is_never_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(issue,"DATA",Path(tmp)), \
                 patch.object(issue.shutil,"which",return_value="gh"), \
                 patch.object(issue,"execute",return_value=(0,"PineTreePayments\n")):
                self.assertIsNone(issue.dedicated_gh())

    def test_configured_pinetree_profile_never_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            (d/"github_identity.json").write_text(json.dumps({
                "owner":"PineTreePayments",
                "gh_config_dir":str(d/"PineTree-profile")}))
            with patch.object(issue,"DATA",d), \
                 patch.object(issue.shutil,"which",return_value="gh"), \
                 patch.object(issue,"execute") as api:
                self.assertIsNone(issue.dedicated_gh())
                api.assert_not_called()

    def test_poll_reports_independently_of_update_decision(self):
        class Lock:
            def close(self): pass
        with patch.object(agent,"ENABLED",Path("remote_deploy_enabled.json")), \
             patch.object(agent,"read_json",side_effect=lambda p:
                 {"enabled":True,"auto_update":True} if p==agent.ENABLED else {}), \
             patch.object(agent,"lock",return_value=Lock()), \
             patch.object(agent,"git",side_effect=lambda *args:
                 COMMIT if args[0]=="rev-parse" else ""), \
             patch.object(agent,"try_approved_release",return_value=0), \
             patch.object(agent,"report_tower_health") as report:
            self.assertEqual(agent.poll(),0)
            report.assert_called_once()


if __name__=="__main__":
    unittest.main()
