"""Minimal PRIVATE tower receipts over the owner's dedicated Myles GitHub profile.

This reporter has one fixed remote destination:
  JoshuaDuskin/MylesTowerReceipts (MUST be private)

Nothing is ever published to the public MylesAI or dashboard repository. A
missing dedicated credential/permission makes the reporter fail closed. The
payload is constructed from a strict allowlist and contains no local files,
emails, wallet balances, pairing codes, tokens, command lines, or raw logs.
"""
from __future__ import annotations
import base64
import datetime as dt
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "MylesAI"
DATA = ROOT / "data"
LOGS = ROOT / "logs"
ENABLED = DATA / "remote_deploy_enabled.json"
ATTEMPT = DATA / "private_receipt_publisher_state.json"
REPORT = DATA / "private_receipt_latest.json"
DEST = "JoshuaDuskin/MylesTowerReceipts"
OWNER = "JoshuaDuskin"
REMOTE_FILE = "health.json"
ORIGIN = "https://github.com/JoshuaDuskin/MylesAI.git"
NO_WINDOW = getattr(subprocess,"CREATE_NO_WINDOW",0)
SHA = re.compile(r"^[0-9a-f]{40}$")
VERSION = "1"


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def read_json(path: Path, *, max_size: int = 1_000_000) -> dict:
    try:
        if path.stat().st_size > max_size:
            return {}
        obj=json.loads(path.read_text(encoding="utf-8-sig"))
        return obj if isinstance(obj,dict) else {}
    except (OSError, ValueError):
        return {}


def write_local(path: Path, obj: dict) -> None:
    import uuid
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+"."+uuid.uuid4().hex+".tmp")
    try:
        temp.write_text(json.dumps(obj,sort_keys=True,indent=2),encoding="utf-8")
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)


def _run(args: list[str], *, env: dict[str,str] | None = None,
         input_data: str | None = None, timeout: int = 15) -> tuple[int,str]:
    p=subprocess.run(args,env=env,input=input_data,stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL,text=True,timeout=timeout,
                     creationflags=NO_WINDOW,check=False)
    return p.returncode, (p.stdout or "")[:60_000]


def git(*args: str) -> str:
    code,out=_run(["git","-C",str(ROOT),*args],timeout=10)
    return out.strip() if code==0 else ""


def _local_health(port: int, path: str = "") -> tuple[bool, dict]:
    if not path:
        try:
            with socket.create_connection(("127.0.0.1",port),timeout=1.0):
                return True,{}
        except OSError:
            return False,{}
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}",timeout=2) as r:
            data=json.loads(r.read(16_000))
            return bool(r.status==200 and data.get("ok") is True), data if isinstance(data,dict) else {}
    except (OSError, ValueError, KeyError, TypeError):
        return False,{}


def _worker_counts() -> dict[str,int | None]:
    result={"quant":None,"gmx":None,"copy_research":None,"worker_jobs":None}
    try:
        import psutil
        counts={k:0 for k in result}
        for proc in psutil.process_iter(["cmdline"]):
            try:
                cmd=" ".join(proc.info.get("cmdline") or []).casefold()
            except Exception:
                continue
            if str(ROOT).casefold() not in cmd:
                continue
            if "quant_service.mjs" in cmd: counts["quant"]+=1
            if "gmx_live.mjs" in cmd and "--daemon" in cmd: counts["gmx"]+=1
            if "copy_trader_service.mjs" in cmd and "--daemon" in cmd: counts["copy_research"]+=1
            if "job_worker.py" in cmd: counts["worker_jobs"]+=1
        return counts
    except Exception:
        return result


def snapshot(now: dt.datetime | None = None) -> dict[str,Any]:
    now=now or utc_now()
    head=git("rev-parse","HEAD").lower()
    origin=git("remote","get-url","origin")
    if not SHA.fullmatch(head) or origin != ORIGIN:
        raise ValueError("canonical source could not be verified")
    core_ok,core=_local_health(8766,"/health")
    bridge_ok,_=_local_health(8790)
    gateway_ok,_=_local_health(8791)
    state=read_json(DATA/"remote_deploy_state.json")
    receipt=read_json(DATA/"remote_deploy_result.json")
    game=read_json(DATA/"game_mode_state.json")
    config=read_json(DATA/"config.json")
    trading=read_json(DATA/"trading_status.json")
    receipt_sha=str(receipt.get("installed_sha") or "").lower()
    state_sha=str(state.get("target_sha") or "").lower()
    game_on=game.get("active") is True or (
        config.get("light_mode") is True
        and config.get("light_mode_source")=="automatic_game_detection")
    models_paused=bool(game_on or config.get("light_mode"))
    version=str(core.get("version") or "")[:32] if core_ok else None
    # Exact reported state; this does not infer successful receipt on mere git HEAD.
    deploy_state=str(state.get("status") or "")[:40]
    if deploy_state not in {"launched","succeeded","failed","failed_unverified"}:
        deploy_state="none_recorded"
    result={
        "schema":1,
        "checked_at":now.isoformat(timespec="seconds"),
        "source":"tower_self_report",
        "installed_sha":head,
        "runtime_version":version,
        "update":{
            "state":deploy_state,
            "target_sha":state_sha if SHA.fullmatch(state_sha) else None,
            "receipt_matched_installed":bool(SHA.fullmatch(receipt_sha) and receipt_sha==head
                     and receipt.get("success") is True),
            "last_updater_exit_code":int(receipt["updater_exit_code"]) if isinstance(receipt.get("updater_exit_code"),int) else None,
            "last_updater_health_verified":receipt.get("health_verified") is True,
        },
        "services":{
            "core_health":core_ok,
            "bridge_port":bridge_ok,
            "gateway_port":gateway_ok,
            "workers":_worker_counts(),
        },
        "gaming":{
            "performance_mode":bool(game_on),
            "model_work_paused":models_paused,
        },
        "quant_feed_verified":trading.get("_verified") is True,
        "privacy":"allowlisted_status_only_no_private_logs",
    }
    return result


def _gh() -> tuple[str,dict[str,str]] | None:
    info=read_json(DATA/"github_identity.json")
    owner=str(info.get("owner") or "")
    config_dir=str(info.get("gh_config_dir") or "")
    if owner.casefold()!=OWNER.casefold() or not config_dir:
        return None
    config_path=Path(config_dir)
    if not config_path.is_absolute():
        return None
    gh=shutil.which("gh") or shutil.which("gh.exe")
    if not gh:
        gh_paths=[
            Path(os.environ.get("ProgramFiles",r"C:\Program Files"))/"GitHub CLI"/"gh.exe",
            Path(os.environ.get("LOCALAPPDATA",""))/"Programs"/"GitHub CLI"/"gh.exe",
        ]
        gh=next((str(p) for p in gh_paths if p.is_file()),None)
    if not gh:
        return None
    env=os.environ.copy()
    if ROOT.resolve() not in config_path.resolve().parents:
        # Do not consume the owner's default GitHub account or another
        # project's credential directory.
        return None
    env["GH_CONFIG_DIR"]=str(config_path)
    env["GH_HOST"]="github.com"
    env.pop("GH_ENTERPRISE_TOKEN",None)
    # Prevent an inherited token from overriding the dedicated GH config.
    env.pop("GH_TOKEN",None)
    env.pop("GITHUB_TOKEN",None)
    code,login=_run([gh,"api","user","--jq",".login"],env=env,timeout=12)
    if code or login.strip().casefold()!=OWNER.casefold():
        return None
    return gh,env


def _gh_json(gh: str,env: dict[str,str],args: list[str],
             *, data: dict | None=None) -> tuple[int,dict]:
    code,out=_run([gh,"api",*args],env=env,
                  input_data=json.dumps(data) if data is not None else None,timeout=20)
    try:
        response=json.loads(out) if out.strip() else {}
    except ValueError:
        response={}
    return code,response if isinstance(response,dict) else {}


def _private_repo(gh: str, env: dict[str,str]) -> bool:
    repo_path=f"repos/{DEST}"
    code,info=_gh_json(gh,env,[repo_path])
    if code:
        # Only create a private repo after a confirmed HTTP 404 response,
        # never after an ambiguous 401/403/429, unavailable auth, or timeout.
        status, raw=_run([gh,"api","--include",repo_path],env=env,timeout=12)
        if status==0 or not re.search(r"(?m)^HTTP/\S+\s+404\b",raw):
            return False
        code,info=_gh_json(gh,env,["-X","POST","user/repos","--input","-"],
            data={"name":"MylesTowerReceipts","private":True,"auto_init":True,
                  "description":"Private, sanitized Myles tower health receipts only."})
        if code:
            return False
    return bool(info.get("full_name")==DEST and info.get("private") is True
                and info.get("default_branch")=="main")

def publish(report: dict, gh: str, env: dict[str,str]) -> bool:
    if not _private_repo(gh,env):
        return False
    path=f"repos/{DEST}/contents/{REMOTE_FILE}"
    code,existing=_gh_json(gh,env,[path])
    if code:
        # A missing health.json is permitted on the first publication, but
        # auth failures must never be treated as a missing file.
        status, raw=_run([gh,"api","--include",path],env=env,timeout=12)
        if status==0 or not re.search(r"(?m)^HTTP/\S+\s+404\b",raw):
            return False
    existing_sha=str(existing.get("sha") or "")
    if existing_sha and not re.fullmatch(r"[0-9a-f]{40}",existing_sha):
        return False
    content=base64.b64encode(json.dumps(report,sort_keys=True,separators=(",",":")).encode("utf-8")).decode("ascii")
    payload={"message":"Tower private health receipt","content":content,"branch":"main"}
    if existing_sha:
        payload["sha"]=existing_sha
    code,response=_gh_json(gh,env,["-X","PUT",path,"--input","-"],data=payload)
    return code==0 and isinstance(response.get("content"),dict)


def tick() -> str:
    settings=read_json(ENABLED)
    if not (settings.get("enabled") is True and settings.get("auto_update") is True):
        return "disabled"
    old=read_json(ATTEMPT)
    now=utc_now()
    try:
        previous=dt.datetime.fromisoformat(str(old.get("at") or ""))
        if previous.tzinfo is not None and (now-previous).total_seconds()<240:
            return "throttled"
    except ValueError:
        pass
    # Record the attempt before remote work; failed credentials never hammer
    # GitHub at 5-minute intervals or cause repeated OAuth prompts.
    write_local(ATTEMPT,{"at":now.isoformat(),"status":"attempting"})
    try:
        report=snapshot(now)
        write_local(REPORT,report)
        identity=_gh()
        if identity is None:
            status="blocked_dedicated_github_auth"
        elif publish(report,*identity):
            status="published_private"
        else:
            status="blocked_private_repo_permissions"
    except Exception as exc:
        status="failed_"+type(exc).__name__
    write_local(ATTEMPT,{"at":now.isoformat(),"status":status})
    return status


if __name__=="__main__":
    status=tick()
    print("MYLES PRIVATE RECEIPT: "+status)
    raise SystemExit(0 if status in {"published_private","throttled","disabled"} else 2)
