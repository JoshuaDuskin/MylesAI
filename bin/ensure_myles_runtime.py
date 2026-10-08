from __future__ import annotations

"""Windowless startup/recovery guardian for the canonical MYLES supervisor."""

import ctypes
import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0)
ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "MylesAI"
DATA = ROOT / "data"
LOGS = ROOT / "logs"
SUPERVISOR = ROOT / "bin" / "runtime_supervisor_v074.py"
PYTHONW = ROOT / ".venv" / "Scripts" / "pythonw.exe"
PID_FILE = DATA / "runtime_supervisor_v074.pid"
LOCK_FILE = DATA / "runtime_supervisor_v074.lock"
STATE_FILE = DATA / "runtime_guardian_state.json"
LOG_FILE = LOGS / "runtime_guardian.log"


def log(message: str) -> None:
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8", errors="replace") as handle:
            handle.write(f"[{dt.datetime.now().isoformat(timespec='seconds')}] {message}\n")
    except Exception:
        pass


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        process_query_limited_information = 0x1000
        still_active = 259
        handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, int(pid))
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            return bool(
                ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
                and int(code.value) == still_active
            )
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def supervisor_pid() -> int:
    for marker in (PID_FILE, LOCK_FILE):
        try:
            pid = int(marker.read_text(encoding="ascii", errors="ignore").strip())
            if pid_alive(pid):
                return pid
        except Exception:
            continue
    return 0


def endpoint_ok(url: str) -> bool:
    try:
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=4) as response:
            return 200 <= int(response.status) < 500
    except Exception:
        return False


def runtime_healthy() -> bool:
    return all(
        endpoint_ok(url)
        for url in (
            "http://127.0.0.1:8766/health",
            "http://127.0.0.1:8790/dashboard/health",
            "http://127.0.0.1:8791/dashboard/health",
        )
    )


def failure_count() -> int:
    try:
        return int(json.loads(STATE_FILE.read_text(encoding="utf-8-sig")).get("consecutive_failures") or 0)
    except Exception:
        return 0


def save_failure_count(count: int) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {
        "consecutive_failures": max(0, int(count)),
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(temporary, STATE_FILE)


def clear_stale_markers() -> None:
    if supervisor_pid():
        return
    for marker in (PID_FILE, LOCK_FILE):
        try:
            marker.unlink(missing_ok=True)
        except Exception:
            pass


def start_supervisor() -> int:
    if not SUPERVISOR.is_file() or not PYTHONW.is_file():
        log(f"Cannot start supervisor; source={SUPERVISOR.is_file()} pythonw={PYTHONW.is_file()}")
        return 0
    clear_stale_markers()
    process = subprocess.Popen(
        [str(PYTHONW), str(SUPERVISOR)],
        cwd=str(ROOT),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=(CREATE_NO_WINDOW | DETACHED_PROCESS) if os.name == "nt" else 0,
        close_fds=True,
    )
    log(f"Supervisor was absent; started launcher PID {process.pid}")
    return int(process.pid)


def stop_tree(pid: int) -> None:
    if pid <= 0:
        return
    try:
        subprocess.run(
            ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
            creationflags=CREATE_NO_WINDOW,
        )
        log(f"Drained unhealthy supervisor tree PID {pid}")
    except Exception as exc:
        log(f"Could not drain unhealthy supervisor tree PID {pid}: {type(exc).__name__}: {exc}")


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    owner = supervisor_pid()
    if not owner:
        start_supervisor()
        save_failure_count(0)
        return 0
    if runtime_healthy():
        save_failure_count(0)
        return 0

    failures = failure_count() + 1
    save_failure_count(failures)
    log(f"Supervisor exists but core/bridge/gateway health is incomplete (failure {failures} of 3)")
    if failures < 3:
        return 1

    stop_tree(owner)
    deadline = time.time() + 12
    while time.time() < deadline and pid_alive(owner):
        time.sleep(0.5)
    clear_stale_markers()
    start_supervisor()
    save_failure_count(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
