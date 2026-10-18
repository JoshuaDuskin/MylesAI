"""Regression for one approved Myles update path and quiet Windows launches."""
from __future__ import annotations
import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bin import console_window_audit as audit
from bin import tower_health_issue as health

ROOT=Path(__file__).resolve().parents[1]


class QuietConsoleTests(unittest.TestCase):
    def test_nested_ci_updater_is_explicitly_hidden(self):
        script=(ROOT/"bin"/"remote_deploy_apply.ps1").read_text(encoding="utf-8")
        self.assertIn("powershell.exe -NoLogo -NoProfile",script)
        self.assertIn("-WindowStyle Hidden -File $Updater",script)
        self.assertIn("-RemoteQuiet -ExpectedHead $ExpectedHead",script)

    def test_supervisor_prevents_cli_windows_and_preserves_owner_console(self):
        source=(ROOT/"bin"/"runtime_supervisor_v074.py").read_text(encoding="utf-8")
        self.assertIn('"startupinfo": si',source)
        self.assertIn("si.wShowWindow = subprocess.SW_HIDE",source)
        self.assertIn("owner_console_excluded",source)
        self.assertIn('"node.exe", "git.exe"',source)
        self.assertIn("CREATE_NO_WINDOW",source)
        self.assertIn("console_spawn_monitor",source)

    def test_public_console_report_is_strictly_sanitized(self):
        stamp=dt.datetime(2026,10,14,18,0,0)
        data=(
          f"[{stamp.isoformat()}] pid=123 ppid=4 name=powershell.exe "
          "myles_owned=True hidden_windows=1 "
          "command='SECRET_TOKEN=never-publish remote_deploy_apply.ps1' "
          "ancestry='C:\\Users\\Private\\AppData\\Local\\MylesAI'\n"
          f"[{stamp.isoformat()}] pid=456 ppid=3 name=cmd.exe "
          "myles_owned=False hidden_windows=1 command='Private owner terminal'\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"console.log"
            p.write_text(data,encoding="utf-8")
            result=audit.recent_summary(stamp+dt.timedelta(minutes=4),path=p)
        self.assertEqual(result["status"],"events_observed")
        self.assertEqual(result["myles_console_process_launches_last_hour"],1)
        self.assertEqual(result["visible_windows_suppressed_last_hour"],1)
        self.assertEqual(result["last_source_category"],"update_child")
        self.assertEqual(result["last_executable_category"],"powershell.exe")
        self.assertNotIn("SECRET_TOKEN",str(result))
        self.assertNotIn("Private",str(result))
        self.assertNotIn("Users",str(result))
        self.assertNotIn("pid",str(result).lower())

    def test_ancestry_classification_uses_safe_parent_category(self):
        stamp=dt.datetime(2026,10,14,18,0,0)
        data=(
          f"[{stamp.isoformat()}] pid=123 ppid=4 name=python.exe "
          "myles_owned=True hidden_windows=1 command='opaque' "
          "ancestry='root<- 7:cmd.exe:opaque<- 8:python.exe:opaque'\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"console.log"
            p.write_text(data,encoding="utf-8")
            result=audit.recent_summary(stamp+dt.timedelta(minutes=4),path=p)
        self.assertEqual(result["status"],"events_observed")
        self.assertEqual(result["last_source_category"],"shell_parent")
        self.assertNotIn("opaque",str(result))
        self.assertNotIn("root",str(result))

    def test_no_log_and_stale_events_never_claim_window_was_seen(self):
        now=dt.datetime(2026,10,14,22,0,0)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"audit"
            self.assertEqual(audit.recent_summary(now,path=p)["status"],"no_audit_log")
            p.write_text("[2026-10-13T12:00:00] pid=1 ppid=2 name=cmd.exe "
                         "myles_owned=True hidden_windows=1 command='legacy'",encoding="utf-8")
            self.assertEqual(audit.recent_summary(now,path=p)["status"],
                             "no_recent_myles_console_events")

    def test_reporting_only_allowlists_aggregate(self):
        value={"status":"events_observed","myles_console_process_launches_last_hour":2}
        with patch.object(health,"recent_console_events",return_value=value), \
             patch.object(health,"git",side_effect=lambda *args:
                          "a"*40 if args[0]=="rev-parse" else health.ORIGIN), \
             patch.object(health,"core_health",return_value=(True,"10.15.6")), \
             patch.object(health,"port_up",return_value=True), \
             patch.object(health,"quant_feed_verified",return_value=True), \
             patch.object(health,"worker_counts",return_value={}), \
             patch.object(health,"intelligence_summary",return_value={"status":"unverified"}), \
             patch.object(health,"read_json",return_value={}):
            result=health.snapshot()
        self.assertEqual(result["console_window_audit"],value)


if __name__=="__main__":
    unittest.main()
