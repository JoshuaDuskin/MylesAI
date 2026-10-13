"""Private receipt channel tests. No GitHub repo, token or network is touched."""
from __future__ import annotations
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,Mock

from bin import tower_receipt_publisher as p
from bin import remote_deploy_agent as agent

SHA="a"*40
OK_REPO={"full_name":p.DEST,"private":True,"default_branch":"main"}


class PrivateReceiptTests(unittest.TestCase):
    def test_public_or_wrong_repo_never_receives_receipt(self):
        for info in (
            {"full_name":p.DEST,"private":False,"default_branch":"main"},
            {"full_name":"SomeoneElse/Mylles","private":True,"default_branch":"main"},
            {"full_name":p.DEST,"private":True,"default_branch":"master"},
        ):
            with self.subTest(info=info), \
                 patch.object(p,"_gh_json",return_value=(0,info)), \
                 patch.object(p,"_run") as native:
                self.assertFalse(p._private_repo("gh",{}))
                native.assert_not_called()

    def test_create_private_only_on_confirmed_not_found(self):
        for signal,should_create in (
            ("HTTP/2.0 403 Forbidden\n",False),
            ("HTTP/2.0 429 Too Many Requests\n",False),
            ("HTTP/2.0 404 Not Found\n",True),
            ("",False),
        ):
            calls=[]
            def api(*args,**kwargs):
                calls.append((args,kwargs))
                return (1,{}) if len(calls)==1 else (0,OK_REPO)
            with self.subTest(signal=signal), \
                 patch.object(p,"_gh_json",side_effect=api), \
                 patch.object(p,"_run",return_value=(1,signal)):
                good=p._private_repo("gh",{})
                self.assertEqual(good,should_create)
                self.assertEqual(len(calls),2 if should_create else 1)
                if should_create:
                    payload=calls[1][1]["data"]
                    self.assertTrue(payload["private"])
                    self.assertEqual(payload["name"],"MylesTowerReceipts")

    def test_publisher_fails_closed_when_private_repo_unavailable(self):
        with patch.object(p,"_private_repo",return_value=False), \
             patch.object(p,"_gh_json") as api:
            self.assertFalse(p.publish({"installed_sha":SHA},"gh",{}))
            api.assert_not_called()

    def test_private_write_has_only_allowlisted_status(self):
        with patch.object(p,"_private_repo",return_value=True), \
             patch.object(p,"_gh_json",side_effect=[
                 (1,{}),(0,{}),(0,{"content":{"sha":"b"*40}})]), \
             patch.object(p,"_run",return_value=(1,"HTTP/2.0 404 Not Found\n")) as proc:
            report={"schema":1,"installed_sha":SHA}
            self.assertTrue(p.publish(report,"gh",{}))

    def test_snapshot_reports_version_ports_jobs_without_user_secrets(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            state={"status":"succeeded","target_sha":SHA}
            receipt={"installed_sha":SHA,"success":True,"health_verified":True,
                     "updater_exit_code":0,"secret":"never_include_secret_1"}
            (root/"remote_deploy_state.json").write_text(json.dumps(state))
            (root/"remote_deploy_result.json").write_text(json.dumps(receipt))
            (root/"config.json").write_text('{"light_mode":false,"api_key":"never_include_secret_2"}')
            (root/"game_mode_state.json").write_text('{"active":false}')
            (root/"trading_status.json").write_text('{"_verified":true,"wallet":"never_include_secret_3"}')
            with patch.object(p,"DATA",root), \
                 patch.object(p,"git",side_effect=lambda *args:SHA if args[0]=="rev-parse" else p.ORIGIN), \
                 patch.object(p,"_local_health",side_effect=[
                     (True,{"ok":True,"version":"10.14.0","secret":"never_include_secret_4"}),
                     (True,{}),(True,{})]), \
                 patch.object(p,"_worker_counts",return_value={
                     "quant":1,"gmx":1,"copy_research":1,"worker_jobs":0}):
                report=p.snapshot()
            raw=json.dumps(report)
            self.assertEqual(report["installed_sha"],SHA)
            self.assertTrue(report["update"]["receipt_matched_installed"])
            self.assertEqual(report["services"]["workers"]["quant"],1)
            self.assertTrue(report["quant_feed_verified"])
            self.assertNotIn("never_include_secret",raw)
            self.assertNotIn("wallet",raw)
            self.assertNotIn(str(root),raw)

    def test_no_false_success_from_stale_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"remote_deploy_result.json").write_text(json.dumps({
                "installed_sha":"c"*40,"success":True}))
            with patch.object(p,"DATA",root), \
                 patch.object(p,"git",side_effect=lambda *args:SHA if args[0]=="rev-parse" else p.ORIGIN), \
                 patch.object(p,"_local_health",return_value=(False,{})), \
                 patch.object(p,"_worker_counts",return_value={}):
                report=p.snapshot()
            self.assertFalse(report["update"]["receipt_matched_installed"])
            self.assertFalse(report["services"]["core_health"])

    def test_disabled_telemetry_cannot_call_github(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"enabled.json"
            f.write_text('{"enabled":false,"auto_update":true}')
            with patch.object(p,"ENABLED",f),patch.object(p,"_gh") as gh:
                self.assertEqual(p.tick(),"disabled")
                gh.assert_not_called()

    def test_no_auth_has_local_receipt_but_no_remote_publication(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            enabled=root/"enabled.json"
            enabled.write_text('{"enabled":true,"auto_update":true}')
            with patch.object(p,"ENABLED",enabled), \
                 patch.object(p,"ATTEMPT",root/"attempt.json"), \
                 patch.object(p,"REPORT",root/"report.json"), \
                 patch.object(p,"snapshot",return_value={"schema":1,"installed_sha":SHA}), \
                 patch.object(p,"_gh",return_value=None), \
                 patch.object(p,"publish") as publish:
                self.assertEqual(p.tick(),"blocked_dedicated_github_auth")
                self.assertTrue((root/"report.json").exists())
                publish.assert_not_called()

    def test_private_report_skips_active_game(self):
        with patch.object(agent,"read_json",side_effect=lambda path:
                 {"enabled":True,"auto_update":True} if path==agent.ENABLED else {"active":True}), \
             patch.dict("sys.modules",{"tower_receipt_publisher":Mock()}):
            agent.private_receipt_tick()  # no work or network

    def test_production_account_and_destination_are_hardcoded(self):
        self.assertEqual(p.DEST,"JoshuaDuskin/MylesTowerReceipts")
        self.assertEqual(p.OWNER,"JoshuaDuskin")
        self.assertNotIn("PineTree",p.DEST)
        self.assertEqual(p.REMOTE_FILE,"health.json")


if __name__=="__main__":
    unittest.main()
