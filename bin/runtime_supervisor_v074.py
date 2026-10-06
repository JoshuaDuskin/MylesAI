from __future__ import annotations

import ctypes
import datetime as dt
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
import traceback
import urllib.request
from pathlib import Path


CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0)
BELOW_NORMAL_PRIORITY_CLASS = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0x00004000)
ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "MylesAI"
DATA = ROOT / "data"
BIN = ROOT / "bin"
LOGS = ROOT / "logs"
QUANT = ROOT / "quant"
BRIDGE = ROOT / "dashboard_bridge"
REPO = ROOT / "dashboard_site"
VENV = ROOT / ".venv" / "Scripts"
PY = VENV / "python.exe"
PYW = VENV / "pythonw.exe"
DASHBOARD_REPO = "https://github.com/JoshuaDuskin/MylesAI.git"
LOG = LOGS / "runtime_supervisor_v074.log"
SUPERVISOR_PID_FILE = DATA / "runtime_supervisor_v074.pid"
# A filesystem lock is shared by elevated and non-elevated sessions. The
# Global/Local Windows mutex pair can split into two owners when the updater
# and owner console run at different privilege levels.
SUPERVISOR_LOCK_FILE = DATA / "runtime_supervisor_v074.lock"
CONFIG_FILE = DATA / "config.json"
GAME_STATE_FILE = DATA / "game_mode_state.json"
GAME_WATCHER = BIN / "game_mode_watch.py"
RESTART_REQUEST = DATA / "restart.request"
SUPERVISOR_STOP_FILE = DATA / "runtime_supervisor_v074.stop"

for directory in (DATA, BIN, LOGS):
    directory.mkdir(parents=True, exist_ok=True)

# On this Windows tower the preserved .venv is uv-backed. Launching its
# pythonw.exe legitimately creates a short interpreter chain where the venv
# launcher is the parent and the uv-managed CPython process owns this script.
# That is ONE logical supervisor, not two. Singleton ownership is enforced by
# the supervisor lock/PID files below; never relaunch based on sys.executable.

# STOP_MYLES.cmd reaches this same canonical supervisor entry point with "stop".
# Handle that command before trying to acquire the live supervisor lock.
if len(sys.argv) > 1 and str(sys.argv[1]).strip().lower() == "stop":
    try:
        SUPERVISOR_STOP_FILE.write_text(
            json.dumps({"requested_at": dt.datetime.now(dt.timezone.utc).isoformat(), "pid": os.getpid()}) + "\n",
            encoding="utf-8",
        )
    except Exception:
        sys.exit(2)
    deadline = time.time() + 40
    while time.time() < deadline and SUPERVISOR_PID_FILE.exists():
        time.sleep(0.5)
    sys.exit(0 if not SUPERVISOR_PID_FILE.exists() else 3)

def pid_is_alive(pid: int) -> bool:
    """Check a PID without ever signaling or terminating it.

    On Windows os.kill(pid, 0) is unsafe because non-console signals are routed
    through TerminateProcess. The old lock check could therefore kill the
    supervisor it was only trying to inspect.
    """
    if pid <= 0:
        return False
    if os.name == "nt":
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid)
        )
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return int(code.value) == STILL_ACTIVE
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def acquire_shared_instance_lock():
    """Own one cross-privilege supervisor lock for this Windows user."""
    for _ in range(30):
        try:
            descriptor = os.open(
                str(SUPERVISOR_LOCK_FILE),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
            os.write(descriptor, str(os.getpid()).encode("ascii"))
            return descriptor
        except FileExistsError:
            try:
                owner_pid = int(SUPERVISOR_LOCK_FILE.read_text(encoding="ascii").strip())
            except Exception:
                owner_pid = 0
            if owner_pid and owner_pid != os.getpid() and pid_is_alive(owner_pid):
                return None
            try:
                SUPERVISOR_LOCK_FILE.unlink(missing_ok=True)
            except Exception:
                pass
            time.sleep(0.1)
    return None


shared_lock_fd = acquire_shared_instance_lock()
if shared_lock_fd is None:
    sys.exit(0)
try:
    SUPERVISOR_STOP_FILE.unlink(missing_ok=True)
except Exception:
    pass

# The filesystem lock above is the single authoritative instance guard.
# A Windows Global mutex can survive through a launcher/interpreter process
# split and incorrectly block a clean restart, so it is intentionally unused.
mutex = None


def log(message: object) -> None:
    try:
        with LOG.open("a", encoding="utf-8", errors="replace") as handle:
            handle.write(f"[{dt.datetime.now().isoformat()}] {message}\n")
    except Exception:
        pass



def log_exception(context: str, exc: BaseException) -> None:
    """Persist hidden-runtime failures so pythonw never fails silently."""
    try:
        log(f"{context}: {type(exc).__name__}: {exc}")
        log(traceback.format_exc().rstrip())
    except Exception:
        pass

def run(args, cwd: Path | None = None, env: dict | None = None, timeout: int = 90):
    try:
        return subprocess.run(
            [str(item) for item in args],
            cwd=str(cwd) if cwd else None,
            env=env,
            text=True,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
            creationflags=CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except Exception as exc:
        log(f"command failed: {args} ({exc})")
        return None


def hidden_popen(args, cwd: Path | None = None, stdout_path: Path | None = None, stderr_path: Path | None = None, *, low_priority: bool = False):
    stdout_handle = stdout_path.open("ab") if stdout_path else subprocess.DEVNULL
    stderr_handle = stderr_path.open("ab") if stderr_path else subprocess.DEVNULL
    try:
        flags = (CREATE_NO_WINDOW | DETACHED_PROCESS | (BELOW_NORMAL_PRIORITY_CLASS if low_priority else 0)) if os.name == "nt" else 0
        return subprocess.Popen(
            [str(item) for item in args],
            cwd=str(cwd) if cwd else None,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            creationflags=flags,
            close_fds=True,
        )
    except Exception as exc:
        log(f"process start failed: {args} ({exc})")
        return None
    finally:
        if hasattr(stdout_handle, "close"):
            stdout_handle.close()
        if hasattr(stderr_handle, "close"):
            stderr_handle.close()


def http_json(url: str, headers: dict | None = None, timeout: int = 5) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json", **(headers or {})})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        value = json.loads(raw) if raw.strip() else {}
        return value if isinstance(value, dict) else {}


def http_ok(url: str, headers: dict | None = None, timeout: int = 5) -> bool:
    try:
        return http_json(url, headers, timeout).get("ok", True) is not False
    except Exception:
        return False


def process_rows():
    try:
        import psutil

        rows = []
        for process in psutil.process_iter(["pid", "cmdline"]):
            try:
                rows.append((int(process.info["pid"]), " ".join(process.info.get("cmdline") or [])))
            except Exception:
                pass
        return rows
    except Exception:
        return []


def matching_process_rows(pattern: str):
    rx = re.compile(pattern, re.I)
    return [(pid, command) for pid, command in process_rows() if rx.search(command or "")]


def has(pattern: str) -> bool:
    return bool(matching_process_rows(pattern))


def keep_one_process(pattern: str, label: str) -> bool:
    """Keep exactly one direct worker process for a script; retire duplicates."""
    rows = sorted(matching_process_rows(pattern), key=lambda row: row[0])
    if not rows:
        return False
    keep_pid = rows[0][0]
    for pid, _command in rows[1:]:
        if pid <= 0 or pid == os.getpid():
            continue
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=8,
                    creationflags=CREATE_NO_WINDOW,
                )
            else:
                os.kill(pid, 15)
            log(f"retired duplicate {label} pid={pid}; kept pid={keep_pid}")
        except Exception as exc:
            log(f"duplicate {label} cleanup failed pid={pid}: {exc}")
    return True


def light_mode_active() -> bool:
    """Use the same light_mode flag as the Myles core and automatic game watcher."""
    try:
        value = json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig", errors="replace"))
        return bool(value.get("light_mode")) if isinstance(value, dict) else False
    except Exception:
        return False


def start_game_watcher() -> None:
    if not GAME_WATCHER.exists() or not PYW.exists():
        return

    # Retire old restored watcher revisions. There must be exactly one canonical
    # watcher making game-mode decisions.
    legacy_rx = re.compile(r"game_mode_watch_v\d+\.py", re.I)
    for pid, command in process_rows():
        if pid <= 0 or pid == os.getpid() or not legacy_rx.search(command or ""):
            continue
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=8,
                    creationflags=CREATE_NO_WINDOW,
                )
            else:
                os.kill(pid, 15)
            log(f"retired legacy game-mode watcher pid={pid}")
        except Exception:
            pass

    canonical_pattern = re.escape(str(GAME_WATCHER))
    if has(canonical_pattern):
        return
    hidden_popen(
        [PYW, GAME_WATCHER],
        cwd=BIN,
        stdout_path=LOGS / "game_mode_watch_startup.out.log",
        stderr_path=LOGS / "game_mode_watch_startup.err.log",
    )
    log("automatic canonical game-mode watcher restart requested")


def stop_heavy_background() -> None:
    """Keep CPU/GPU-heavy Myles workers down for the entire gaming session."""
    patterns = (
        re.compile(r"quant_service\.mjs", re.I),
        re.compile(r"gmx_live\.mjs", re.I),
        re.compile(r"copy_trader_service\.mjs", re.I),
        re.compile(r"simulate_first_batch\.py", re.I),
        re.compile(r"job_worker\.py", re.I),
    )
    for pid, command in process_rows():
        if pid <= 0 or pid == os.getpid():
            continue
        if not any(rx.search(command or "") for rx in patterns):
            continue
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=12,
                    creationflags=CREATE_NO_WINDOW,
                )
            else:
                os.kill(pid, 15)
            log(f"gaming/light mode stopped heavy pid={pid}")
        except Exception:
            pass


def stop_runtime_children() -> None:
    """Stop only processes that belong to the canonical Myles runtime."""
    patterns = (
        re.compile(r"myles_core\.py", re.I),
        re.compile(r"dashboard_bridge\.py", re.I),
        re.compile(r"public_gateway_v074\.py", re.I),
        re.compile(r"quant_service\.mjs", re.I),
        re.compile(r"gmx_live\.mjs", re.I),
        re.compile(r"copy_trader_service\.mjs", re.I),
        re.compile(r"game_mode_watch\.py", re.I),
        re.compile(r"cloudflared.*8791", re.I),
    )
    for pid, command in process_rows():
        if pid <= 0 or pid == os.getpid() or not any(rx.search(command or "") for rx in patterns):
            continue
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=12,
                    creationflags=CREATE_NO_WINDOW,
                )
            else:
                os.kill(pid, 15)
            log(f"stopped Myles runtime child pid={pid}")
        except Exception as exc:
            log(f"could not stop Myles runtime child pid={pid}: {exc}")


def _stop_core_only() -> None:
    rx = re.compile(r"myles_core\.py", re.I)
    for pid, command in process_rows():
        if pid <= 0 or pid == os.getpid() or not rx.search(command or ""):
            continue
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=12,
                    creationflags=CREATE_NO_WINDOW,
                )
            else:
                os.kill(pid, 15)
        except Exception:
            pass


def _wait_for_core_offline(timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not http_ok("http://127.0.0.1:8766/health", timeout=1):
            return True
        time.sleep(0.5)
    return not http_ok("http://127.0.0.1:8766/health", timeout=1)


def _wait_for_core_health(timeout: float = 45.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if http_ok("http://127.0.0.1:8766/health", timeout=2):
            return True
        time.sleep(1)
    return False


def _restore_backup(backup: Path) -> int:
    if not backup.is_dir():
        return 0
    restored = 0
    for src in backup.iterdir():
        if not src.is_file():
            continue
        shutil.copy2(src, ROOT / src.name)
        restored += 1
    return restored


def _request_core_shutdown() -> None:
    try:
        request = urllib.request.Request(
            "http://127.0.0.1:8766/api/control/shutdown",
            data=b"{}",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=4):
            pass
    except Exception:
        pass


def _restart_for_update() -> bool:
    """Consume a promoted self-update request, verify it, and roll back on failure."""
    if not RESTART_REQUEST.exists():
        return False
    try:
        payload = json.loads(RESTART_REQUEST.read_text(encoding="utf-8-sig", errors="replace"))
        payload = payload if isinstance(payload, dict) else {}
    except Exception:
        payload = {}
    backup_raw = str(payload.get("backup") or "").strip()
    backup = Path(backup_raw) if backup_raw else None
    log(f"RESTART_REQUEST detected candidate={payload.get('candidate') or 'unknown'}")

    _request_core_shutdown()
    if not _wait_for_core_offline(20):
        _stop_core_only()
        _wait_for_core_offline(8)

    # Remove the request before starting the replacement core so the new core
    # cannot see the same request and immediately exit again.
    try:
        RESTART_REQUEST.unlink(missing_ok=True)
    except Exception as exc:
        log(f"could not clear restart request: {exc}")

    start_core()
    if _wait_for_core_health(45):
        log("candidate restart passed health check")
        return True

    log("candidate restart failed health check")
    _stop_core_only()
    _wait_for_core_offline(8)
    restored = _restore_backup(backup) if backup else 0
    if restored <= 0:
        log("rollback unavailable: backup was missing or empty")
        return True

    log(f"restored {restored} file(s) from rollback backup {backup}")
    start_core()
    if _wait_for_core_health(45):
        log("rollback passed health check")
    else:
        log("rollback failed health check")
    return True


def stop_stale_tunnels() -> None:
    """Stop only cloudflared processes owned by the Myles 8791 tunnel."""
    try:
        import psutil

        for process in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                command = " ".join(process.info.get("cmdline") or [])
                name = str(process.info.get("name") or "")
                if name.lower() == "cloudflared.exe" and re.search(r"(?:127\.0\.0\.1:)?8791(?:\s|$)", command, re.I):
                    process.terminate()
            except Exception:
                pass
    except Exception:
        pass


def owner_token() -> str:
    try:
        return (DATA / "dashboard_bridge_token.txt").read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def read_token() -> str:
    path = DATA / "dashboard_public_read_token.txt"
    try:
        token = path.read_text(encoding="utf-8", errors="replace").strip()
        if len(token) >= 32:
            return token
    except Exception:
        pass
    token = secrets.token_urlsafe(36)
    path.write_text(token + "\n", encoding="utf-8")
    return token


def start_ollama_service() -> None:
    """Keep the local conversation provider available; model residency stays game-managed."""
    if http_ok("http://127.0.0.1:11434/api/tags", timeout=3):
        return
    candidates = [
        shutil.which("ollama.exe"),
        shutil.which("ollama"),
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"),
        str(Path(os.environ.get("ProgramFiles", "")) / "Ollama" / "ollama.exe"),
    ]
    executable = next((Path(x) for x in candidates if x and Path(x).is_file()), None)
    if not executable or has(r"ollama(?:\.exe)?\s+serve"):
        return
    hidden_popen(
        [executable, "serve"],
        cwd=executable.parent,
        stdout_path=LOGS / "ollama_startup.out.log",
        stderr_path=LOGS / "ollama_startup.err.log",
    )
    log("Ollama conversation service restart requested")


def start_core() -> None:
    if http_ok("http://127.0.0.1:8766/health"):
        return
    candidates = (ROOT / "myles_core.py", ROOT / "runtime" / "myles_core.py")
    core = next((candidate for candidate in candidates if candidate.exists()), None)
    if core and PY.exists() and not has(r"myles_core\.py"):
        hidden_popen([PYW, core], cwd=core.parent, stdout_path=LOGS / "myles_core_startup.out.log", stderr_path=LOGS / "myles_core_startup.err.log")
        log("core restart requested")


def start_quant() -> None:
    node_candidates = [
        shutil.which("node.exe"),
        shutil.which("node"),
        Path(os.environ.get("ProgramFiles", "")) / "nodejs" / "node.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "nodejs" / "node.exe",
    ]
    node = next((Path(item) for item in node_candidates if item and Path(item).exists()), None)
    if not node:
        return
    quant_script = QUANT / "quant_service.mjs"
    gmx_script = QUANT / "gmx_live.mjs"
    copy_script = QUANT / "copy_trader_service.mjs"
    if quant_script.exists() and not keep_one_process(r"quant_service\.mjs", "Quant worker"):
        hidden_popen([node, quant_script], cwd=QUANT, stdout_path=LOGS / "quant_startup.out.log", stderr_path=LOGS / "quant_startup.err.log", low_priority=True)
        log("quant restart requested")
    if gmx_script.exists() and not keep_one_process(r"gmx_live\.mjs.*--daemon", "GMX daemon"):
        hidden_popen([node, gmx_script, "--daemon"], cwd=QUANT, stdout_path=LOGS / "gmx_live_startup.out.log", stderr_path=LOGS / "gmx_live_startup.err.log", low_priority=True)
        log("gmx restart requested")
    if copy_script.exists() and not keep_one_process(r"copy_trader_service\.mjs.*--daemon", "copy research daemon"):
        hidden_popen([node, copy_script, "--daemon"], cwd=QUANT, stdout_path=LOGS / "copy_trader_startup.out.log", stderr_path=LOGS / "copy_trader_startup.err.log", low_priority=True)
        log("copy research restart requested")


def start_services(owner: str, read: str) -> None:
    if light_mode_active():
        stop_heavy_background()
    else:
        start_quant()
    owner_headers = {"X-Myles-Token": owner, "Authorization": f"Bearer {owner}"} if owner else {}
    if owner and not http_ok("http://127.0.0.1:8790/dashboard/health", owner_headers):
        bridge_script = BRIDGE / "dashboard_bridge.py"
        if bridge_script.exists() and not has(r"dashboard_bridge\.py"):
            hidden_popen(
                [PYW, bridge_script, "--token-file", DATA / "dashboard_bridge_token.txt", "--pair-code-file", DATA / "dashboard_pair_code.json", "--port", "8790"],
                cwd=BRIDGE,
                stdout_path=LOGS / "dashboard_bridge_startup.out.log",
                stderr_path=LOGS / "dashboard_bridge_startup.err.log",
            )
            log("bridge restart requested")
    if not http_ok("http://127.0.0.1:8791/dashboard/health", {"X-Myles-Read": read}):
        gateway = BIN / "public_gateway_v074.py"
        if gateway.exists() and not has(r"public_gateway_v074\.py"):
            interpreter = PYW if PYW.exists() else PY
            hidden_popen(
                [interpreter, gateway],
                cwd=BIN,
                stdout_path=LOGS / "public_gateway_startup.out.log",
                stderr_path=LOGS / "public_gateway.err.log",
            )
            log("public gateway restart requested")


def tunnel_state() -> str:
    try:
        value = json.loads((DATA / "tunnel_state.json").read_text(encoding="utf-8", errors="replace"))
        url = str(value.get("url") or "").rstrip("/")
        if url.startswith("https://") and (".trycloudflare.com" in url or ".ts.net" in url):
            return url
    except Exception:
        pass
    return ""


def cloudflared_path() -> Path | None:
    candidates = [
        shutil.which("cloudflared.exe"),
        BIN / "cloudflared.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "cloudflared" / "cloudflared.exe",
        Path(os.environ.get("ProgramFiles", "")) / "cloudflared" / "cloudflared.exe",
    ]
    return next((Path(item) for item in candidates if item and Path(item).exists()), None)


def tailscale_path() -> Path | None:
    candidates = [
        shutil.which("tailscale.exe"),
        Path(os.environ.get("ProgramFiles", "")) / "Tailscale" / "tailscale.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Tailscale" / "tailscale.exe",
        Path(os.environ.get("LocalAppData", "")) / "Tailscale" / "tailscale.exe",
    ]
    return next((Path(item) for item in candidates if item and Path(item).exists()), None)


def ensure_tailscale_funnel(read: str) -> str:
    tailscale = tailscale_path()
    if not tailscale:
        return ""
    result = run([tailscale, "funnel", "--yes", "--bg", "8791"], timeout=30)
    if not result or result.returncode != 0:
        return ""
    status = run([tailscale, "funnel", "status"], timeout=20)
    text = ((status.stdout if status else "") + "\n" + (status.stderr if status else ""))
    if not re.search(r"https://[a-z0-9.-]+\.ts\.net", text, re.I):
        json_status = run([tailscale, "funnel", "status", "--json"], timeout=20)
        text += "\n" + ((json_status.stdout if json_status else "") + "\n" + (json_status.stderr if json_status else ""))
    match = re.search(r"https://[a-z0-9.-]+\.ts\.net", text, re.I)
    if not match:
        return ""
    url = match.group(0).rstrip("/")
    if not http_ok(url + "/dashboard/health", {"X-Myles-Read": read}, 15):
        return ""
    (DATA / "tunnel_state.json").write_text(json.dumps({"url": url, "provider": "tailscale", "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}, indent=2) + "\n", encoding="utf-8")
    return url


def ensure_dashboard_checkout() -> bool:
    """Keep the dashboard deployment checkout on the canonical MylesAI repo."""
    git = shutil.which("git.exe") or shutil.which("git")
    if not git:
        return False
    try:
        if (REPO / ".git").exists():
            origin = run([git, "-C", REPO, "remote", "get-url", "origin"], timeout=30)
            current = ((origin.stdout if origin else "") or "").strip()
            if "JoshuaDuskin/MylesAI.git" not in current:
                stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
                legacy = ROOT / f"dashboard_site_legacy_{stamp}"
                REPO.replace(legacy)
                log(f"retired legacy dashboard checkout to {legacy}")
        if not (REPO / ".git").exists():
            clone = run([git, "clone", "--depth", "1", "--filter=blob:none", DASHBOARD_REPO, REPO], cwd=ROOT, timeout=180)
            if not clone or clone.returncode != 0:
                return False
        for args in (("remote", "set-url", "origin", DASHBOARD_REPO), ("fetch", "origin", "main"), ("checkout", "main"), ("pull", "--ff-only", "origin", "main")):
            result = run([git, "-C", REPO, *args], timeout=120)
            if not result or result.returncode != 0:
                return False
        return True
    except Exception as exc:
        log(f"dashboard checkout repair failed: {exc}")
        return False


def bridge_manifest_matches(url: str, read: str) -> bool:
    """Return True only when the deployment manifest matches live tower state."""
    if not ensure_dashboard_checkout():
        return False
    try:
        value = json.loads((REPO / "bridge.json").read_text(encoding="utf-8", errors="replace"))
        manifest_url = str(value.get("url") or value.get("bridge_url") or "").rstrip("/")
        manifest_read = str(value.get("read_token") or "").strip()
        return manifest_url == str(url or "").rstrip("/") and manifest_read == str(read or "").strip()
    except Exception:
        return False


def publish_bridge(url: str, read: str) -> bool:
    if not ensure_dashboard_checkout():
        return False
    git = shutil.which("git.exe") or shutil.which("git")
    if not git:
        return False
    try:
        status = run([git, "-C", REPO, "status", "--porcelain"])
        dirty = status.stdout.splitlines() if status else []
        if any(not re.search(r"(?:bridge\.json|index\.html)\s*$", row) for row in dirty):
            return False
        if not dirty:
            for args in (("fetch", "origin", "main"), ("checkout", "main"), ("pull", "--ff-only", "origin", "main")):
                result = run([git, "-C", REPO, *args], timeout=120)
                if not result or result.returncode != 0:
                    return False
        payload = {"url": url, "bridge_url": url, "read_token": read, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        (REPO / "bridge.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        if not run([git, "-C", REPO, "add", "--", "bridge.json"]):
            return False
        diff = run([git, "-C", REPO, "diff", "--cached", "--quiet"])
        # Unlock only this dedicated deployment checkout for the bridge publish.
        unlock = run([git, "-C", REPO, "remote", "set-url", "--push", "origin", DASHBOARD_REPO], timeout=30)
        if not unlock or unlock.returncode != 0:
            return False
        env = os.environ.copy()
        env["MYLES_DASHBOARD_OWNER_UNLOCK"] = "1"
        if diff and diff.returncode == 1:
            commit = run([git, "-C", REPO, "commit", "-m", "Refresh live Myles bridge"], env=env)
            if not commit or commit.returncode != 0:
                return False
            push = run([git, "-C", REPO, "push", "origin", "main"], env=env, timeout=120)
            if not push or push.returncode != 0:
                return False
        return True
    except Exception as exc:
        log(f"bridge publish failed: {exc}")
        return False
    finally:
        run([git, "-C", REPO, "remote", "set-url", "--push", "origin", "owner-locked://MylesAI"], timeout=30)


def ensure_tunnel(read: str) -> str:
    old = tunnel_state()
    if old and http_ok(old + "/dashboard/health", {"X-Myles-Read": read}, 8):
        if not bridge_manifest_matches(old, read):
            log("bridge manifest stale; publishing current tower endpoint")
            publish_bridge(old, read)
        return old
    tailscale_url = ensure_tailscale_funnel(read)
    if tailscale_url:
        if tailscale_url != old or not bridge_manifest_matches(tailscale_url, read):
            log("publishing current Tailscale bridge manifest: " + str(publish_bridge(tailscale_url, read)))
        return tailscale_url
    cloudflared = cloudflared_path()
    if not cloudflared:
        return old
    # A dead quick tunnel can leave cloudflared.exe alive. Reusing that process
    # keeps bridge.json pinned to an endpoint that can never recover.
    if has(r"cloudflared.*8791"):
        stop_stale_tunnels()
        time.sleep(2)
    output = LOGS / "cloudflared_v074.out.log"
    error = LOGS / "cloudflared_v074.err.log"
    # Do not rediscover a dead URL left in an earlier append-only log.
    for path in (output, error):
        try:
            path.write_text("", encoding="utf-8")
        except Exception as exc:
            log(f"could not reset tunnel log {path}: {exc}")
    process_args = [cloudflared, "tunnel", "--url", "http://127.0.0.1:8791", "--no-autoupdate", "--loglevel", "info"]
    # Let cloudflared choose its transport here; some edges reject forced
    # http2 even though the local gateway is healthy.
    process = hidden_popen(
        process_args,
            cwd=ROOT,
        stdout_path=output,
        stderr_path=error,
    )
    if not process:
        return old
    pattern = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.I)
    deadline = time.time() + 75
    url = ""
    text = ""
    while time.time() < deadline:
        try:
            text = output.read_text(encoding="utf-8", errors="replace") + "\n" + error.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
        match = pattern.search(text)
        if match:
            url = match.group(0).rstrip("/")
            break
        time.sleep(1)
    if not url:
        log("cloudflared did not publish a URL; stderr tail: " + error.read_text(encoding="utf-8", errors="replace")[-2000:])
        return old
    if not http_ok(url + "/dashboard/health", {"X-Myles-Read": read}, 12):
        log("new quick tunnel URL failed public health; refusing to publish it")
        stop_stale_tunnels()
        return old
    (DATA / "tunnel_state.json").write_text(json.dumps({"url": url, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}, indent=2) + "\n", encoding="utf-8")
    if url != old:
        log("public URL changed; publishing bridge manifest: " + str(publish_bridge(url, read)))
    return url


def lock_repo() -> None:
    git = shutil.which("git.exe") or shutil.which("git")
    if git and ensure_dashboard_checkout():
        run([git, "-C", REPO, "remote", "set-url", "--push", "origin", "owner-locked://MylesAI"], timeout=30)


SUPERVISOR_PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
log(f"supervisor started pid={os.getpid()}")
try:
    while True:
        if SUPERVISOR_STOP_FILE.exists():
            log("supervisor stop request detected")
            break
        # Keep each cycle independently recoverable. A watcher, bridge, tunnel,
        # or git failure must not terminate the supervisor that owns the tower.
        try:
            _restart_for_update()
            start_game_watcher()
        except Exception as exc:
            log_exception("game-mode watcher cycle failed", exc)
        try:
            owner = owner_token()
            read = read_token()
            start_ollama_service()
            start_core()
            gaming = light_mode_active()
            start_services(owner, read)
            if http_ok("http://127.0.0.1:8791/dashboard/health", {"X-Myles-Read": read}):
                ensure_tunnel(read)
            if not gaming:
                lock_repo()
        except Exception as exc:
            log_exception("supervisor service cycle failed", exc)
        for _ in range(30):
            if SUPERVISOR_STOP_FILE.exists():
                break
            time.sleep(1)
finally:
    try:
        if SUPERVISOR_STOP_FILE.exists():
            stop_runtime_children()
    except Exception as exc:
        log_exception("runtime child shutdown failed", exc)
    try:
        SUPERVISOR_STOP_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    try:
        if SUPERVISOR_PID_FILE.exists() and SUPERVISOR_PID_FILE.read_text(encoding="utf-8", errors="ignore").strip() == str(os.getpid()):
            SUPERVISOR_PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    if mutex is not None:
        try:
            ctypes.windll.kernel32.ReleaseMutex(mutex)
        except Exception:
            pass
    try:
        os.close(shared_lock_fd)
    except Exception:
        pass
    try:
        if SUPERVISOR_LOCK_FILE.read_text(encoding="ascii").strip() == str(os.getpid()):
            SUPERVISOR_LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass
