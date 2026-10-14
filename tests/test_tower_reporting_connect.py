"""Owner-approved GitHub CLI auth for same-repo Issue #49. No real logins."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from bin import tower_reporting_connect as connect
from bin import tower_health_issue as reporter


class AuthTests(unittest.TestCase):
    def test_credentials_never_inherit_another_project_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(connect,"PROFILE",Path(tmp)/"gh"), \
                 patch.dict(connect.os.environ,{
                   "GH_TOKEN":"NEVER_USE_THIS",
                   "GITHUB_TOKEN":"NEVER_USE_THIS",
                   "GH_CONFIG_DIR":"/some/other/project",
                   "GH_ENTERPRISE_TOKEN":"NEVER_USE_THIS",
                 }):
                env=connect.gh_env()
                for key in ("GH_TOKEN","GITHUB_TOKEN","GH_ENTERPRISE_TOKEN","GIT_ASKPASS"):
                    self.assertNotIn(key,env)
                self.assertEqual(env["GH_CONFIG_DIR"],str(Path(tmp)/"gh"))
                self.assertEqual(env["GH_HOST"],"github.com")

    def test_username_must_be_exact_github_owner(self):
        with patch.object(connect,"capture",return_value=(0,"JoshuaDuskin")):
            self.assertTrue(connect.verified_owner("gh",{}))
        with patch.object(connect,"capture",return_value=(0,"PineTreePayments")):
            self.assertFalse(connect.verified_owner("gh",{}))
        with patch.object(connect,"capture",return_value=(1,"")):
            self.assertFalse(connect.verified_owner("gh",{}))

    def test_disabled_or_missing_source_makes_no_credential_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            with patch.object(connect,"is_windows",return_value=True), \
                 patch.object(connect,"ROOT",d), \
                 patch.object(connect,"IDENTITY",d/"data"/"github_identity.json"), \
                 patch.object(connect,"gh_exe") as lookup:
                self.assertEqual(connect.connect(False)[1],"reporter_not_installed")
                lookup.assert_not_called()

    def test_existing_different_owner_is_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            (d/"bin").mkdir()
            (d/"bin"/"tower_health_issue.py").write_text("# fixture")
            identity=d/"github_identity.json"
            identity.write_text('{"owner":"PineTreePayments","gh_config_dir":"protected"}')
            with patch.object(connect,"is_windows",return_value=True), \
                 patch.object(connect,"ROOT",d), \
                 patch.object(connect,"IDENTITY",identity), \
                 patch.object(connect,"gh_exe") as lookup:
                self.assertEqual(connect.connect(False)[1],"different_existing_owner_preserved")
                lookup.assert_not_called()
                self.assertIn("PineTreePayments",identity.read_text())

    def test_auth_required_without_browser_cannot_succeed(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            (d/"bin").mkdir()
            (d/"bin"/"tower_health_issue.py").write_text("# fixture")
            with patch.object(connect,"is_windows",return_value=True), \
                 patch.object(connect,"ROOT",d), \
                 patch.object(connect,"PROFILE",d/"gh"), \
                 patch.object(connect,"IDENTITY",d/"identity.json"), \
                 patch.object(connect,"gh_exe",return_value="gh"), \
                 patch.object(connect,"verified_owner",return_value=False), \
                 patch.object(connect,"browser_login") as browser:
                self.assertEqual(connect.connect(False)[1],"github_browser_approval_required")
                browser.assert_not_called()

    def test_connected_only_after_live_issue_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            (d/"bin").mkdir()
            (d/"bin"/"tower_health_issue.py").write_text("# fixture")
            (d/"data").mkdir()
            flag=d/"data"/"remote_deploy_enabled.json"
            flag.write_text('{"enabled":true,"auto_update":true}')
            state=d/"state.json"
            state.write_text('{"last_attempt":"old"}')
            identity=d/"data"/"github_identity.json"
            with patch.object(connect,"is_windows",return_value=True), \
                 patch.object(connect,"ROOT",d), \
                 patch.object(connect,"DATA",d/"data"), \
                 patch.object(connect,"PROFILE",d/"data"/"gh"), \
                 patch.object(connect,"IDENTITY",identity), \
                 patch.object(connect,"gh_exe",return_value="gh"), \
                 patch.object(connect,"verified_owner",return_value=True), \
                 patch.object(connect,"capture",return_value=(0,"49")), \
                 patch.object(reporter,"STATE",state), \
                 patch.object(reporter,"tick",return_value="published") as publish:
                result=connect.connect(False)
                self.assertEqual(result,(True,"published"))
                self.assertFalse(state.exists())
                self.assertEqual(json.loads(identity.read_text())["owner"],"JoshuaDuskin")
                self.assertEqual(json.loads(identity.read_text())["gh_config_dir"],str(d/"data"/"gh"))
                publish.assert_called_once()
            # Simulated GitHub write failure is not reported as success.
            with patch.object(connect,"is_windows",return_value=True), \
                 patch.object(connect,"ROOT",d), \
                 patch.object(connect,"DATA",d/"data"), \
                 patch.object(connect,"PROFILE",d/"data"/"gh"), \
                 patch.object(connect,"IDENTITY",identity), \
                 patch.object(connect,"gh_exe",return_value="gh"), \
                 patch.object(connect,"verified_owner",return_value=True), \
                 patch.object(connect,"capture",return_value=(0,"49")), \
                 patch.object(reporter,"STATE",state), \
                 patch.object(reporter,"tick",return_value="issue_write_denied_or_unavailable"):
                self.assertFalse(connect.connect(False)[0])

    def test_no_repo_creation_or_arbitrary_remote_commands(self):
        self.assertEqual(connect.ISSUE_PATH,"repos/JoshuaDuskin/MylesAI/issues/49")
        self.assertEqual(connect.OWNER,"JoshuaDuskin")
        # Launcher uses an exact local Python file; never accepts a remote command.
        path=Path(__file__).resolve().parents[1]/"CONNECT_TOWER_REPORTING.cmd"
        s=path.read_text(encoding="utf-8")
        self.assertIn("tower_reporting_connect.py",s)
        self.assertNotIn("powershell.exe",s.lower())
        self.assertNotIn("curl ",s.lower())


if __name__=="__main__":
    unittest.main()
