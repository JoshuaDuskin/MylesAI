"""Keep existing verified updater semantics while making polling console-quiet."""
from __future__ import annotations
import datetime as dt
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock,patch

from bin import remote_deploy_agent as agent
from bin import tower_health_issue as reporter
from bin import intelligence_baseline as baseline
from bin import console_window_audit as audit

SHA="a"*40
NEW="b"*40

class Response:
    def __init__(self,body): self.body=body
    def __enter__(self): return self
    def __exit__(self,*args):pass
    def read(self,n=-1):return self.body[:n]

class QuietGitPollTests(unittest.TestCase):
    def test_file_head_detection_requires_exact_local_sha(self):
        with tempfile.TemporaryDirectory() as temp:
            repo=Path(temp)
            ref=repo/".git"/"refs"/"heads"/"main"
            ref.parent.mkdir(parents=True)
            (repo/".git"/"HEAD").write_text("ref: refs/heads/main\n")
            ref.write_text(SHA)
            with patch.object(agent,"ROOT",repo):
                self.assertEqual(agent.local_head_without_process(),SHA)
                ref.write_text("not-commit")
                self.assertEqual(agent.local_head_without_process(),"")
                (repo/".git"/"HEAD").write_text("ref: ../../secrets")
                self.assertEqual(agent.local_head_without_process(),"")

    def test_same_official_github_commit_skips_git_subprocesses(self):
        with tempfile.TemporaryDirectory() as temp:
            repo=Path(temp); ref=repo/".git"/"refs"/"heads"/"main"
            ref.parent.mkdir(parents=True)
            (repo/".git"/"HEAD").write_text("ref: refs/heads/main\n")
            ref.write_text(SHA)
            payload=json.dumps({"commit":{"sha":SHA}}).encode()
            with patch.object(agent,"ROOT",repo), \
                 patch.object(agent.urllib.request,"urlopen",return_value=Response(payload)), \
                 patch.object(agent,"git") as git:
                self.assertTrue(agent.unchanged_main_without_git())
                git.assert_not_called()

    def test_new_main_or_http_failure_falls_back_to_signed_git_path(self):
        with patch.object(agent,"local_head_without_process",return_value=SHA), \
             patch.object(agent.urllib.request,"urlopen",return_value=Response(
                 json.dumps({"commit":{"sha":NEW}}).encode())):
            self.assertFalse(agent.unchanged_main_without_git())
        with patch.object(agent,"local_head_without_process",return_value=SHA), \
             patch.object(agent.urllib.request,"urlopen",side_effect=OSError("offline")):
            self.assertFalse(agent.unchanged_main_without_git())
        with patch.object(agent,"local_head_without_process",return_value=SHA), \
             patch.object(agent.urllib.request,"urlopen",return_value=Response(
                 b'{"commit":{"sha":"not-a-commit"}}')):
            self.assertFalse(agent.unchanged_main_without_git())

    def test_approved_release_poll_skips_git_only_on_unchanged_shas(self):
        class Lock:
            def close(self):pass
        with patch.object(agent,"lock",return_value=Lock()), \
             patch.object(agent,"read_json",side_effect=lambda p:
                 {"enabled":True,"auto_update":True} if p==agent.ENABLED else {}), \
             patch.object(agent,"unchanged_main_without_git",return_value=True), \
             patch.object(agent,"git") as git, \
             patch.object(agent,"report_tower_health"), \
             patch.object(agent,"start_intelligence_baseline"):
            self.assertEqual(agent.poll(),0)
            git.assert_not_called()

    def test_changed_release_keeps_ci_gated_updater(self):
        class Lock:
            def close(self):pass
        with patch.object(agent,"lock",return_value=Lock()), \
             patch.object(agent,"read_json",side_effect=lambda p:
                 {"enabled":True,"auto_update":True} if p==agent.ENABLED else {}), \
             patch.object(agent,"unchanged_main_without_git",return_value=False), \
             patch.object(agent,"git",side_effect=["",NEW]) as git, \
             patch.object(agent,"try_approved_release",return_value=0) as approve, \
             patch.object(agent,"report_tower_health"), \
             patch.object(agent,"start_intelligence_baseline"):
            self.assertEqual(agent.poll(),0)
            self.assertEqual(git.call_count,2)
            approve.assert_called_once_with(NEW,{})

    def test_hidden_git_flags_on_windows(self):
        fake=MagicMock()
        fake.dwFlags=0
        with patch.object(agent,"is_windows",return_value=True), \
             patch.object(agent.subprocess,"STARTUPINFO",return_value=fake,create=True), \
             patch.object(agent.subprocess,"STARTF_USESHOWWINDOW",2,create=True), \
             patch.object(agent.subprocess,"SW_HIDE",0,create=True), \
             patch.object(agent.subprocess,"run",return_value=MagicMock(returncode=0,stdout=SHA)) as run:
            self.assertEqual(agent.git("rev-parse","HEAD"),SHA)
            self.assertIs(run.call_args.kwargs["startupinfo"],fake)
            self.assertTrue(fake.dwFlags & 2)
            self.assertEqual(fake.wShowWindow,0)
            self.assertEqual(run.call_args.kwargs["stdin"],agent.subprocess.DEVNULL)

    def test_reporter_preserves_json_stdin_to_gh_api(self):
        with patch.object(reporter.subprocess,"run",return_value=MagicMock(returncode=0,stdout='{"ok":true}')) as run:
            result=reporter.execute(["gh","api","-X","PATCH",
                                     "repos/JoshuaDuskin/MylesAI/issues/49","--input","-"],
                                    data='{"body":"test"}')
            self.assertEqual(result[0],0)
            self.assertEqual(run.call_args.kwargs["input"],'{"body":"test"}')
            self.assertNotIn("stdin",run.call_args.kwargs)

    def test_intelligence_baseline_git_is_noninteractive(self):
        with patch.object(baseline,"is_windows",return_value=False), \
             patch.object(baseline.subprocess,"run",return_value=MagicMock(returncode=0,stdout=SHA)) as run:
            self.assertEqual(baseline.installed_sha(),SHA)
            self.assertEqual(run.call_args.kwargs["stdin"],baseline.subprocess.DEVNULL)

    def test_audit_public_reports_only_allowlisted_suppressed_sources(self):
        stamp=dt.datetime.now().isoformat()
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"audit.log"
            path.write_text(
               f"[{stamp}] pid=1 ppid=9 name=git.exe myles_owned=True hidden_windows=2 "
               "command='PASSWORD_XX_PRIVATE' ancestry='remote_deploy_agent.py'\n"
               f"[{stamp}] pid=2 ppid=9 name=powershell.exe myles_owned=True hidden_windows=1 "
               "command='SECRET_YY_PRIVATE' ancestry='job_worker.py'\n"
               f"[{stamp}] pid=3 ppid=9 name=git.exe myles_owned=False hidden_windows=1 "
               "command='irrelevant'\n",encoding="utf-8")
            data=audit.recent_summary(path=path)
        self.assertEqual(data["suppressed_source_counts"],
                         {"update_poll":1,"worker_tool":1})
        self.assertEqual(data["suppressed_executable_counts"],
                         {"git.exe":1,"powershell.exe":1})
        self.assertEqual(data["visible_windows_suppressed_last_hour"],3)
        self.assertNotIn("PASSWORD_XX_PRIVATE",json.dumps(data))
        self.assertNotIn("SECRET_YY_PRIVATE",json.dumps(data))
        self.assertNotIn("pid",json.dumps(data))

if __name__=="__main__":
    unittest.main()
