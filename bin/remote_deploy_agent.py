"""Opt-in GitHub-main deployment poller; never accepts remote shell commands."""
from __future__ import annotations
import datetime as dt
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "MylesAI"
DATA, LOGS = ROOT / "data", ROOT / "logs"
CANONICAL = "https://github.com/JoshuaDuskin/MylesAI.git"
REQUEST_PATH = ".myles-deploy/request.json"
STATE = DATA / "remote_deploy_state.json"
RESULT = DATA / "remote_deploy_result.json"
ENABLED = DATA / "remote_deploy_enabled.json"
LOG = LOGS / "remote_deploy.log"
APPLY = ROOT / "bin" / "remote_deploy_apply.ps1"
SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
ID_RE = re.compile(r"[A-Za-z0-9_-]{12,64}\Z")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def log(message: str) -> None:
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"[{now()}] {message[:600]}\n")
    except OSError:
        pass


def read_json(path: Path) -> dict:
    try:
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
        return obj if isinstance(obj, dict) else {}
    except (OSError, ValueError):
        return {}


def write_json(path: Path, value: dict) -> None:
    import uuid
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def git(*args: str, timeout: int = 30) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        timeout=timeout, creationflags=NO_WINDOW, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"git {args[0]} returned {result.returncode}")
    return result.stdout.strip()


def lock():
    DATA.mkdir(parents=True, exist_ok=True)
    handle = (DATA / "remote_deploy_poll.lock").open("a+b")
    try:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            if handle.read(1) != b"1":
                handle.seek(0)
                handle.write(b"1")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def validate(req: dict, head: str, parent: str, changed: str, instant: dt.datetime) -> str:
    if req.get("action") == "idle":
        return "idle"
    if req.get("schema") != 1 or req.get("action") != "update":
        return "invalid schema/action"
    if set(req) != {"schema", "action", "request_id", "target_sha", "requested_at"}:
        return "unexpected request fields"
    if not isinstance(req.get("request_id"), str) or not ID_RE.fullmatch(req["request_id"]):
        return "invalid request identifier"
    target = req.get("target_sha")
    if not isinstance(target, str) or not SHA_RE.fullmatch(target):
        return "invalid target SHA"
    if not SHA_RE.fullmatch(head) or parent != target:
        return "request is not direct descendant of target commit"
    if changed.splitlines() != [REQUEST_PATH]:
        return "request commit changes other files"
    try:
        value = dt.datetime.fromisoformat(str(req["requested_at"]).replace("Z", "+00:00"))
        if value.tzinfo is None:
            return "timezone missing"
        age = (instant - value.astimezone(dt.timezone.utc)).total_seconds()
        if age < -300 or age > 86400:
            return "request expired"
    except (TypeError, ValueError, OverflowError, KeyError):
        return "invalid timestamp"
    return ""


def process_running(pid: int) -> bool:
    """Conservatively assume a wrapper still lives if its state is unknown."""
    try:
        pid = int(pid)
        if pid <= 0:
            return True
        if os.name == "nt":
            import ctypes
            kernel = ctypes.windll.kernel32
            handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
            if not handle:
                return True  # Access denied cannot prove a process ended.
            try:
                return int(kernel.WaitForSingleObject(handle, 0)) != 0
            finally:
                kernel.CloseHandle(handle)
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except (OSError, ValueError, TypeError):
        return True


def idle_gate() -> str:
    if read_json(DATA / "config.json").get("light_mode") is True:
        return "light mode"
    if read_json(DATA / "game_mode_state.json").get("active") is True:
        return "game running"
    try:
        with urllib.request.urlopen("http://127.0.0.1:8766/api/jobs", timeout=3) as res:
            jobs = json.load(res).get("jobs", [])
        if any(str(j.get("state", "")).lower() in
               {"running", "starting", "paused_for_game", "blocked_auth"}
               for j in jobs if isinstance(j, dict)):
            return "owner task active"
    except Exception:
        # A deployment can repair an unhealthy old core.
        pass
    return ""


def poll() -> int:
    if read_json(ENABLED).get("enabled") is not True:
        return 0
    held = lock()
    if held is None:
        return 0
    try:
        state = read_json(STATE)
        if state.get("status") == "launched":
            receipt = read_json(RESULT)
            if receipt.get("request_id") == state.get("request_id"):
                status = "succeeded" if receipt.get("success") is True else "failed"
                write_json(STATE, {**state, "status": status,
                                   "finished_at": now(),
                                   "installed_sha": receipt.get("installed_sha"),
                                   "health_verified": receipt.get("health_verified"),
                                   "updater_exit_code": receipt.get("updater_exit_code")})
                log(f"request {state.get('request_id')} {status}")
            # Never relaunch this ID; a crashed wrapper is marked unverified
            # after two hours so a separate, newer owner request can recover.
            if receipt.get("request_id") != state.get("request_id"):
                try:
                    launched = dt.datetime.fromisoformat(str(state["started_at"]))
                    if ((dt.datetime.now(dt.timezone.utc) - launched.astimezone(dt.timezone.utc)).total_seconds() > 7200
                            and state.get("wrapper_pid") and not process_running(state["wrapper_pid"])):
                        write_json(STATE, {**state, "status": "failed_unverified",
                                           "finished_at": now(), "reason": "receipt missing after two hours"})
                        log("remote update timed out without a verified receipt")
                except (KeyError, ValueError, TypeError, OverflowError):
                    pass
            return 0
        git("fetch", "--no-tags", CANONICAL, "refs/heads/main")
        head = git("rev-parse", "FETCH_HEAD").lower()
        req = json.loads(git("show", "FETCH_HEAD:" + REQUEST_PATH))
        if not isinstance(req, dict) or req.get("action") == "idle":
            return 0
        rid = req.get("request_id")
        if not isinstance(rid, str) or not ID_RE.fullmatch(rid):
            log("invalid request ID ignored")
            return 0
        if state.get("request_id") == rid:
            return 0
        parents = git("rev-list", "--parents", "-n", "1", head).split()
        parent = parents[1].lower() if len(parents) == 2 else ""
        changed = git("diff", "--name-only", parent, head) if parent else ""
        reason = validate(req, head, parent, changed, dt.datetime.now(dt.timezone.utc))
        if reason:
            if state.get("rejected_id") != rid:
                write_json(STATE, {**state, "rejected_id": rid,
                                   "rejected_reason": reason, "rejected_at": now()})
                log(f"refused {rid}: {reason}")
            return 0
        blocker = idle_gate()
        if blocker:
            if state.get("deferred_id") != rid:
                write_json(STATE, {**state, "deferred_id": rid,
                                   "deferred_reason": blocker, "deferred_at": now()})
                log(f"deferred {rid}: {blocker}")
            return 0
        if os.name != "nt" or not APPLY.is_file():
            log("Windows update wrapper not installed")
            return 1
        write_json(STATE, {"request_id": rid, "status": "launched",
                           "target_sha": req["target_sha"], "marker_sha": head,
                           "started_at": now()})
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        try:
            process = subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-WindowStyle", "Hidden", "-File", str(APPLY),
                 "-RequestId", rid, "-ExpectedHead", head],
                cwd=str(ROOT), stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                startupinfo=si, creationflags=NO_WINDOW, close_fds=True)
        except OSError as exc:
            write_json(STATE, {"request_id": rid, "status": "failed",
                               "reason": "could not launch fixed updater",
                               "failed_at": now(), "marker_sha": head})
            log(f"wrapper launch failed: {type(exc).__name__}")
            return 1
        write_json(STATE, {"request_id": rid, "status": "launched",
                           "target_sha": req["target_sha"], "marker_sha": head,
                           "started_at": now(), "wrapper_pid": int(process.pid)})
        log(f"launched approved deployment {rid} pid={process.pid}")
        return 0
    except Exception as exc:
        log(f"poll failed: {type(exc).__name__}: {str(exc)[:180]}")
        return 1
    finally:
        held.close()


if __name__ == "__main__":
    raise SystemExit(poll())
