"""One-click, owner-approved GitHub connection for MylesAI Issue #49.

The public source updater needs no GitHub login; the Issue reporter DOES.
Authorize once in GitHub's official browser through GH CLI. Credentials stay
inside a dedicated Windows-owner GitHub CLI profile, never in source/Issue 49.
No private logs, token strings, PineTree profiles or new repos are touched.
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT=Path(os.environ.get("LOCALAPPDATA") or (Path.home()/"AppData"/"Local"))/"MylesAI"
DATA=ROOT/"data"
PROFILE=DATA/"github_cli_tower"
IDENTITY=DATA/"github_identity.json"
OWNER="JoshuaDuskin"
ISSUE_PATH="repos/JoshuaDuskin/MylesAI/issues/49"
NO_WINDOW=getattr(subprocess,"CREATE_NO_WINDOW",0)


def read_json(path):
    try:
        v=json.loads(path.read_text(encoding="utf-8-sig"))
        return v if isinstance(v,dict) else {}
    except (OSError,ValueError):
        return {}


def atomic_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_name(path.name+"."+uuid.uuid4().hex+".tmp")
    try:
        t.write_text(json.dumps(obj,sort_keys=True,indent=2),encoding="utf8")
        os.replace(t,path)
    finally:
        t.unlink(missing_ok=True)


def gh_exe():
    options=(shutil.which("gh.exe"),shutil.which("gh"),
             str(Path(os.environ.get("ProgramFiles",r"C:\Program Files"))/"GitHub CLI"/"gh.exe"),
             str(Path(os.environ.get("LOCALAPPDATA",""))/"Programs"/"GitHub CLI"/"gh.exe"))
    return next((str(x) for x in options if x and Path(x).is_file()),None)


def gh_env():
    env=os.environ.copy()
    for key in ("GH_TOKEN","GITHUB_TOKEN","GH_ENTERPRISE_TOKEN","GH_CONFIG_DIR","GIT_ASKPASS"):
        env.pop(key,None)
    env["GH_HOST"]="github.com"
    env["GH_CONFIG_DIR"]=str(PROFILE)
    return env


def capture(gh,args,env,timeout=15):
    p=subprocess.run([gh,*args],env=env,stdin=subprocess.DEVNULL,
          stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
          text=True,errors="replace",timeout=timeout,
          creationflags=NO_WINDOW,check=False)
    return p.returncode,(p.stdout or "").strip()[:1000]


def verified_owner(gh,env):
    try:
        c,username=capture(gh,["api","user","--jq",".login"],env)
        return c==0 and username.casefold()==OWNER.casefold()
    except (OSError,subprocess.TimeoutExpired):
        return False


def browser_login(gh,env):
    print("Approve the GitHub CLI request ONLY for the JoshuaDuskin account.")
    print("GitHub will request public_repo permission to update the one public Issue #49.")
    try:
        p=subprocess.run([gh,"auth","login","--hostname","github.com",
             "--git-protocol","https","--web","--scopes","public_repo"],
             env=env,timeout=600,check=False)
        return p.returncode==0
    except (OSError,subprocess.TimeoutExpired):
        return False


def is_windows():
    return os.name=="nt"


def connect(interactive=True):
    if not is_windows():
        return False,"windows_required"
    if not (ROOT/"bin"/"tower_health_issue.py").is_file():
        return False,"reporter_not_installed"
    old=read_json(IDENTITY)
    if old and str(old.get("owner") or "").casefold() not in ("",OWNER.casefold()):
        return False,"different_existing_owner_preserved"
    gh=gh_exe()
    if not gh:
        return False,"github_cli_missing"
    PROFILE.mkdir(parents=True,exist_ok=True)
    env=gh_env()
    if not verified_owner(gh,env):
        if not interactive:
            return False,"github_browser_approval_required"
        if not browser_login(gh,env) or not verified_owner(gh,env):
            return False,"github_browser_approval_failed_or_wrong_account"
    try:
        code,number=capture(gh,["api",ISSUE_PATH,"--jq",".number"],env)
    except (OSError,subprocess.TimeoutExpired):
        return False,"github_issue_access_unverified"
    if code or number!="49":
        return False,"github_issue_access_unverified"
    if not (read_json(DATA/"remote_deploy_enabled.json").get("enabled") is True
            and read_json(DATA/"remote_deploy_enabled.json").get("auto_update") is True):
        return False,"tower_auto_update_not_enabled"
    # Only the explicit owner action changes a preexisting profile selection.
    # Preserve any preexisting identity metadata locally for rollback.
    if old and str(old.get("gh_config_dir") or "")!=str(PROFILE):
        atomic_json(DATA/"github_identity_before_reporting_connect.json",old)
    atomic_json(IDENTITY,{**{k:v for k,v in old.items() if k not in
       ("owner","gh_config_dir")},"owner":OWNER,"gh_config_dir":str(PROFILE)})
    sys.path.insert(0,str(ROOT))
    from bin import tower_health_issue as reporter
    # Explicit button/owner approval bypasses rate limiting of earlier
    # unauthenticated attempts. Does not fetch/deploy code or execute a job.
    reporter.STATE.unlink(missing_ok=True)
    try:
        outcome=reporter.tick()
    except Exception:
        return False,"reporter_error"
    return outcome=="published",("published" if outcome=="published" else "report_"+outcome)


def main():
    print("MYLES TOWER GITHUB CHECK-IN — OWNER AUTHORIZATION")
    print("Repository: JoshuaDuskin/MylesAI; report: Issue #49")
    print("No new repository, incoming port, or remote command access.")
    ok,why=connect()
    print("STATUS:", "CONNECTED" if ok else "ACTION REQUIRED")
    print("DETAIL:",why)
    if why=="github_cli_missing":
        print("Install GitHub CLI from https://cli.github.com/ and rerun this shortcut.")
    if ok:
        print("The real tower report is now visible at:")
        print("https://github.com/JoshuaDuskin/MylesAI/issues/49")
    return 0 if ok else 2


if __name__=="__main__":
    raise SystemExit(main())
