from __future__ import annotations

"""The one hidden owner of the Myles core process.

The supervisor owns only the local core, keeps its output in a persistent log,
prevents duplicate supervisors, restarts a crashed core with bounded recovery,
and never opens a console window. The visible conversation window is separate.
"""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from myles_common import ROOT, DATA, LOGS, RESTART_REQUEST, load_config, pid_alive


SUPERVISOR_PID = DATA / "supervisor.pid"
SUPERVISOR_LOCK = DATA / "supervisor.lock"
STOP_REQUEST = DATA / "supervisor.stop"
SUPERVISOR_LOG = LOGS / "supervisor.log"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


def log(message: str) -> None:
    LOGS.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] {message}\n"
    with SUPERVISOR_LOG.open("a", encoding="utf-8") as handle:
        handle.write(line)


def _read_pid(path: Path) -> int:
    try:
        value = int(path.read_text(encoding="utf-8").strip())
        return value if value > 0 else 0
    except Exception:
        return 0


def _acquire_lock() -> bool:
    DATA.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(str(SUPERVISOR_LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii"))
            os.close(fd)
            return True
        except FileExistsError:
            existing = _read_pid(SUPERVISOR_PID)
            if existing and pid_alive(existing):
                return False
            try:
                SUPERVISOR_LOCK.unlink(missing_ok=True)
            except Exception:
                return False
    return False


def _release_lock() -> None:
    try:
        SUPERVISOR_LOCK.unlink(missing_ok=True)
    except Exception:
        pass


def _pythonw() -> Path:
    python = Path(sys.executable)
    candidate = python.with_name("pythonw.exe") if os.name == "nt" else python
    return candidate if candidate.exists() else python


def _health_url() -> str:
    cfg = load_config()
    return f"http://{cfg['core_host']}:{int(cfg['core_port'])}/health"


def core_healthy() -> bool:
    try:
        with urllib.request.urlopen(_health_url(), timeout=2) as response:
            body = json.loads(response.read().decode("utf-8"))
        return bool(body.get("ok"))
    except Exception:
        return False


def _start_core() -> tuple[subprocess.Popen, object]:
    log_handle = SUPERVISOR_LOG.open("a", encoding="utf-8")
    flags = CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    proc = subprocess.Popen(
        [str(_pythonw()), str(ROOT / "myles_core.py")],
        cwd=str(ROOT),
        stdout=log_handle,
        stderr=log_handle,
        creationflags=flags,
    )
    log(f"core started pid={proc.pid}")
    return proc, log_handle


def _stop_process(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=8)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _close_log(handle: object | None) -> None:
    if handle is not None:
        try:
            handle.close()
        except Exception:
            pass


def _request_core_shutdown() -> None:
    try:
        req = urllib.request.Request(
            _health_url().rsplit("/health", 1)[0] + "/api/control/shutdown",
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3):
            pass
    except Exception:
        pass


def _wait_for_health(timeout_seconds: int = 35) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if core_healthy():
            return True
        time.sleep(0.5)
    return False


def _wait_for_core_offline(timeout_seconds: int = 15) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not core_healthy():
            return True
        time.sleep(0.25)
    return not core_healthy()


def _restore_backup(backup: Path) -> None:
    if not backup.is_dir():
        raise RuntimeError(f"rollback backup is missing: {backup}")
    for source in backup.iterdir():
        if source.is_file():
            shutil.copy2(source, ROOT / source.name)


def _restart_for_update(
    proc: subprocess.Popen | None,
    log_handle: object | None,
) -> tuple[subprocess.Popen | None, object | None, bool]:
    """Restart a promoted candidate and roll back if its health check fails."""
    try:
        request = json.loads(RESTART_REQUEST.read_text(encoding="utf-8"))
    except Exception as exc:
        log(f"restart request unreadable: {type(exc).__name__}: {exc}")
        return None, None, False

    # The candidate core must not see its own restart request. If it did, its
    # monitor loop would immediately exit again and every promoted candidate
    # would fail its health check. Keep the request in memory while this
    # supervisor owns the candidate/rollback transaction.
    RESTART_REQUEST.unlink(missing_ok=True)

    _stop_process(proc)
    _close_log(log_handle)
    if proc is None and core_healthy():
        _request_core_shutdown()
    if not _wait_for_core_offline():
        log("candidate restart blocked: existing core did not go offline")
        backup_raw = str(request.get("backup") or "").strip()
        if backup_raw:
            try:
                _restore_backup(Path(backup_raw))
                log("candidate restart blocked; promoted files restored from backup")
            except Exception as exc:
                log(f"candidate restart blocked and backup restore failed: {type(exc).__name__}: {exc}")
        return None, None, False

    candidate, candidate_log = _start_core()
    if candidate.poll() is None and _wait_for_health():
        RESTART_REQUEST.unlink(missing_ok=True)
        log(f"candidate restart passed health check pid={candidate.pid}")
        return candidate, candidate_log, True

    log(f"candidate restart failed health check pid={candidate.pid}; rolling back")
    _stop_process(candidate)
    _close_log(candidate_log)
    backup_raw = str(request.get("backup") or "").strip()
    if not backup_raw:
        log("rollback blocked: restart request had no backup")
        return None, None, False
    try:
        _restore_backup(Path(backup_raw))
    except Exception as exc:
        log(f"rollback restore failed: {type(exc).__name__}: {exc}")
        return None, None, False

    rollback, rollback_log = _start_core()
    if rollback.poll() is None and _wait_for_health():
        RESTART_REQUEST.unlink(missing_ok=True)
        log(f"rollback passed health check pid={rollback.pid}")
        return rollback, rollback_log, True
    log("rollback also failed health check; supervisor stopped for safety")
    _stop_process(rollback)
    _close_log(rollback_log)
    return None, None, False


def request_stop() -> int:
    STOP_REQUEST.parent.mkdir(parents=True, exist_ok=True)
    STOP_REQUEST.write_text(str(time.time()), encoding="utf-8")
    try:
        req = urllib.request.Request(
            _health_url().rsplit("/health", 1)[0] + "/api/control/shutdown",
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3):
            pass
    except Exception:
        pass
    deadline = time.time() + 15
    while time.time() < deadline and (core_healthy() or pid_alive(_read_pid(SUPERVISOR_PID))):
        time.sleep(0.25)
    log("stop requested")
    return 0


def status() -> int:
    supervisor_pid = _read_pid(SUPERVISOR_PID)
    print(json.dumps({
        "supervisor_pid": supervisor_pid,
        "supervisor_alive": pid_alive(supervisor_pid),
        "core_online": core_healthy(),
        "log": str(SUPERVISOR_LOG),
    }, indent=2))
    return 0


def run() -> int:
    if not _acquire_lock():
        log("duplicate supervisor request ignored")
        return 0

    try:
        STOP_REQUEST.unlink(missing_ok=True)
    except Exception:
        pass

    SUPERVISOR_PID.parent.mkdir(parents=True, exist_ok=True)
    SUPERVISOR_PID.write_text(str(os.getpid()), encoding="utf-8")
    proc: subprocess.Popen | None = None
    log_handle = None
    restart_times: list[float] = []
    try:
        log("supervisor online")
        while not STOP_REQUEST.exists():
            if RESTART_REQUEST.exists():
                proc, log_handle, restart_ok = _restart_for_update(proc, log_handle)
                if not restart_ok:
                    break

            if proc is not None and proc.poll() is not None:
                log(f"core exited code={proc.returncode}")
                proc = None
                _close_log(log_handle)
                log_handle = None

            if proc is None and not core_healthy():
                now = time.time()
                restart_times = [stamp for stamp in restart_times if now - stamp < 600]
                if len(restart_times) >= 8:
                    log("core restart limit reached; supervisor stopped for safety")
                    break
                restart_times.append(now)
                proc, log_handle = _start_core()

            time.sleep(2)
    finally:
        _stop_process(proc)
        _close_log(log_handle)
        try:
            if _read_pid(SUPERVISOR_PID) == os.getpid():
                SUPERVISOR_PID.unlink(missing_ok=True)
        except Exception:
            pass
        _release_lock()
        log("supervisor offline")
    return 0


if __name__ == "__main__":
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "run"
    raise SystemExit(request_stop() if command == "stop" else status() if command == "status" else run())
