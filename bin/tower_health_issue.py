"""Sanitized live-tower report inside the EXISTING public MylesAI issue #49.

Full receipts and credentials remain private on Windows. No extra repository,
commits, branch pushes, arbitrary remote commands, or GitHub workflows.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import shutil
import socket
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "MylesAI"
DATA = ROOT / "data"
ENABLED = DATA / "remote_deploy_enabled.json"
STATE = DATA / "tower_health_publish_state.json"
ISSUE_REPO = "JoshuaDuskin/MylesAI"
ISSUE_NUMBER = 49
ISSUE_PATH = "repos/" + ISSUE_REPO + "/issues/" + str(ISSUE_NUMBER)
MARKER = "<!-- MYLES_TOWER_HEALTH_V1 -->"
ORIGIN = "https://github.com/JoshuaDuskin/MylesAI.git"
OWNER = "JoshuaDuskin"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
LOCAL_HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
SHA = re.compile(r"[0-9a-f]{40}\Z")
VERSION = re.compile(r"[A-Za-z0-9._-]{1,32}\Z")
ALLOWED_STATES = {"launched", "succeeded", "failed", "failed_unverified",
                  "installed_verified_post_restart"}


def now():
    return dt.datetime.now(dt.timezone.utc)


def read_json(path, max_bytes=200_000):
    try:
        if path.stat().st_size > max_bytes:
            return {}
        value=json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value,dict) else {}
    except (OSError, ValueError):
        return {}


def write_state(value):
    import uuid
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temp=STATE.with_name(STATE.name+"."+uuid.uuid4().hex+".tmp")
    try:
        temp.write_text(json.dumps(value,sort_keys=True),encoding="utf-8")
        os.replace(temp,STATE)
    finally:
        temp.unlink(missing_ok=True)


def execute(args, *, env=None, data=None, timeout=18):
    opts = {}
    if os.name == "nt":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        opts["startupinfo"] = si
    if data is None:
        opts["stdin"] = subprocess.DEVNULL
    p=subprocess.run(args,env=env,input=data,stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL,text=True,errors="replace",
                     timeout=timeout,creationflags=NO_WINDOW,check=False,
                     **opts)
    return p.returncode,(p.stdout or "")[:100_000]


def git(*args):
    rc,result=execute(["git","-C",str(ROOT),*args],timeout=12)
    return result.strip() if rc==0 else ""


def core_health():
    try:
        with LOCAL_HTTP.open("http://127.0.0.1:8766/health",timeout=2.5) as r:
            result=json.loads(r.read(12_000))
            if r.status!=200 or not isinstance(result,dict) or result.get("ok") is not True:
                return False,None
            ver=str(result.get("version") or "")
            return True,ver if VERSION.fullmatch(ver) else None
    except (OSError,ValueError,TypeError):
        return False,None


def port_up(port):
    try:
        with socket.create_connection(("127.0.0.1",port),timeout=1.2):
            return True
    except OSError:
        return False


def worker_counts():
    result={"quant":None,"gmx":None,"copy_research":None}
    try:
        import psutil
        result={k:0 for k in result}
        for proc in psutil.process_iter(["cmdline"]):
            try:
                command=" ".join(proc.info.get("cmdline") or []).casefold()
            except Exception:
                continue
            if str(ROOT).casefold() not in command:
                continue
            if "quant_service.mjs" in command:result["quant"]+=1
            if "gmx_live.mjs" in command and "--daemon" in command:result["gmx"]+=1
            if "copy_trader_service.mjs" in command and "--daemon" in command:result["copy_research"]+=1
    except Exception:
        pass
    return result


def quant_feed_verified():
    """Reuse the gateway's *real* paper/GMX freshness and source checks.

    The raw trading_status.json has no _verified marker. The trusted gateway
    adds it only after validating mode, timestamps, engine, and GMX source.
    """
    try:
        try:
            from public_gateway_v074 import local_trading_snapshot
        except ImportError:
            from bin.public_gateway_v074 import local_trading_snapshot
        _, diagnostics = local_trading_snapshot()
        return bool(isinstance(diagnostics, dict) and diagnostics.get("verified") is True)
    except Exception:
        return False


def intelligence_summary(sha):
    """Read ONLY the allowlisted aggregate live result for public Issue #49."""
    try:
        try:
            from intelligence_baseline import public_summary
        except ImportError:
            from bin.intelligence_baseline import public_summary
        return public_summary(sha)
    except Exception:
        return {"status":"unverified"}


def recent_console_events():
    """Only aggregate, fixed-category telemetry; no commands or private logs."""
    try:
        try:
            from console_window_audit import recent_summary
        except ImportError:
            from bin.console_window_audit import recent_summary
        return recent_summary()
    except Exception:
        return {"status": "unavailable"}


def snapshot(timestamp=None):
    """Strict allowlist: no raw local content is copied to GitHub."""
    timestamp=timestamp or now()
    head=git("rev-parse","HEAD").lower()
    if not SHA.fullmatch(head) or git("remote","get-url","origin")!=ORIGIN:
        raise ValueError("canonical source identity unavailable")
    healthy,version=core_health()
    receipt=read_json(DATA/"remote_deploy_result.json")
    state=read_json(DATA/"remote_deploy_state.json")
    verified_quant = quant_feed_verified()
    exit_code=receipt.get("updater_exit_code")
    receipt_matches=bool(
        receipt.get("success") is True
        and receipt.get("health_verified") is True
        and isinstance(exit_code,int) and not isinstance(exit_code,bool) and exit_code==0
        and str(receipt.get("installed_sha") or "").lower()==head
        and str(receipt.get("expected_head") or "").lower()==head
    )
    last=state.get("status")
    target=str(state.get("target_sha") or "").lower()
    return {
        "schema":1,
        "reported_at":timestamp.isoformat(timespec="seconds"),
        "installed_commit":head,
        "myles_version":version,
        "core_healthy":healthy,
        "bridge_reachable":port_up(8790),
        "gateway_reachable":port_up(8791),
        "quant_feed_verified_and_fresh":verified_quant,
        "worker_processes":worker_counts(),
        "intelligence_baseline":intelligence_summary(head),
        "console_window_audit":recent_console_events(),
        "deployment":{
            "last_state":last if last in ALLOWED_STATES else "none_recorded",
            "target_commit":target if SHA.fullmatch(target) else None,
            "verified_local_receipt_matches_installed":receipt_matches,
            "verified_after_restart":bool(
                last=="installed_verified_post_restart"
                and state.get("post_restart_health_verified") is True
                and str(state.get("installed_sha") or "").lower()==head),
        },
        "report_kind":"PUBLIC_sanitized_no_private_receipts",
    }


def format_issue(report):
    # This public issue intentionally excludes private receipts, logs, paths,
    # game activity, messages, IPs, credentials, wallet data and trading values.
    return (
        "## Myles Windows tower check-in\n\n"
        "**PUBLIC, sanitized health summary.** Raw deployment receipts, logs, "
        "pairing codes, wallet information and credentials remain local.\n\n"
        "Consider this report **stale after 20 minutes**. Process/port health "
        "is not proof that all tasks, FPS or network latency are optimized.\n\n"
        "~~~json\n"+json.dumps(report,sort_keys=True,indent=2)+"\n~~~\n\n"+MARKER+"\n"
    )


def dedicated_gh():
    """Authenticate GitHub Issue #49 with a VERIFIED owner account.

    Prefer the isolated Myles GH profile. If it is missing/unavailable,
    permit the already-authorized Windows user's gh profile, but ONLY when
    GitHub confirms it is exactly JoshuaDuskin. Never borrow PineTree's
    identity or inherit an environment-supplied credential/token.
    """
    identity=read_json(DATA/"github_identity.json",max_bytes=16_000)
    owner=str(identity.get("owner") or "").strip()
    config_dir=str(identity.get("gh_config_dir") or "").strip()
    if owner and owner.casefold()!=OWNER.casefold():
        return None
    if config_dir and (not Path(config_dir).is_absolute()
                       or "pinetree" in config_dir.casefold()):
        return None
    gh=shutil.which("gh") or shutil.which("gh.exe")
    if not gh:
        for candidate in (
            Path(os.environ.get("ProgramFiles",r"C:\Program Files"))/"GitHub CLI"/"gh.exe",
            Path(os.environ.get("LOCALAPPDATA",""))/"Programs"/"GitHub CLI"/"gh.exe",
        ):
            if candidate.is_file():
                gh=str(candidate)
                break
    if not gh:
        return None

    clean=os.environ.copy()
    for key in ("GH_TOKEN","GITHUB_TOKEN","GH_ENTERPRISE_TOKEN","GH_CONFIG_DIR"):
        clean.pop(key,None)
    clean["GH_HOST"]="github.com"
    choices=[]
    if owner.casefold()==OWNER.casefold() and config_dir:
        isolated=clean.copy()
        isolated["GH_CONFIG_DIR"]=config_dir
        choices.append(isolated)
    # A default profile is used only after proving ownership with 'gh api
    # user'; it does NOT inherit the machine's potentially foreign GH_CONFIG_DIR.
    choices.append(clean)
    for env in choices:
        try:
            code,login=execute([gh,"api","user","--jq",".login"],env=env,timeout=12)
        except (OSError,subprocess.TimeoutExpired):
            continue
        if code==0 and login.strip().casefold()==OWNER.casefold():
            return gh,env
    return None


def publish(report,gh,env):
    # Fixed single issue in the existing repository. The issue is not code
    # and editing its text never triggers the canonical CI deploy watcher.
    code,raw=execute([gh,"api",ISSUE_PATH],env=env,timeout=15)
    if code:
        return False
    try:
        issue=json.loads(raw)
    except ValueError:
        return False
    if (not isinstance(issue,dict) or issue.get("number")!=ISSUE_NUMBER
            or issue.get("state")!="open"
            or (issue.get("user") or {}).get("login")!=OWNER
            or MARKER not in str(issue.get("body") or "")):
        return False
    payload=json.dumps({"body":format_issue(report)})
    code,raw=execute([gh,"api","-X","PATCH",ISSUE_PATH,"--input","-"],
                     env=env,data=payload,timeout=20)
    if code:
        return False
    try:
        updated=json.loads(raw)
        return bool(updated.get("number")==ISSUE_NUMBER
                    and MARKER in str(updated.get("body") or ""))
    except (ValueError,AttributeError):
        return False


def tick():
    enabled=read_json(ENABLED)
    if enabled.get("enabled") is not True or enabled.get("auto_update") is not True:
        return "disabled"
    game=read_json(DATA/"game_mode_state.json")
    cfg=read_json(DATA/"config.json")
    if game.get("active") is True or (
        cfg.get("light_mode") is True and
        cfg.get("light_mode_source")=="automatic_game_detection"
    ):
        return "deferred_during_game"
    timestamp=now()
    previous=read_json(STATE)
    try:
        last=dt.datetime.fromisoformat(str(previous.get("last_attempt") or ""))
        if last.tzinfo and (timestamp-last.astimezone(dt.timezone.utc)).total_seconds()<540:
            return "throttled"
    except (ValueError,OverflowError):
        pass
    write_state({"last_attempt":timestamp.isoformat(),"result":"attempting"})
    try:
        report=snapshot(timestamp)
        creds=dedicated_gh()
        if creds is None:
            result="dedicated_github_auth_unavailable"
        elif publish(report,*creds):
            result="published"
        else:
            result="issue_write_denied_or_unavailable"
    except Exception as exc:
        result="report_error_"+type(exc).__name__
    write_state({"last_attempt":timestamp.isoformat(),"result":result})
    return result


if __name__=="__main__":
    print("MYLES TOWER HEALTH: "+tick())
