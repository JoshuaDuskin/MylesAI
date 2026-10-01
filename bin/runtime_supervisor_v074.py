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
import urllib.request
from pathlib import Path


CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0)
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

for directory in (DATA, BIN, LOGS):
    directory.mkdir(parents=True, exist_ok=True)

mutex = None
if os.name == "nt":
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Local\\MylesRuntimeSupervisor_v074")
    if ctypes.windll.kernel32.GetLastError() == 183:
        sys.exit(0)


def log(message: object) -> None:
    try:
        with LOG.open("a", encoding="utf-8", errors="replace") as handle:
            handle.write(f"[{dt.datetime.now().isoformat()}] {message}\n")
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


def hidden_popen(args, cwd: Path | None = None, stdout_path: Path | None = None, stderr_path: Path | None = None):
    stdout_handle = stdout_path.open("ab") if stdout_path else subprocess.DEVNULL
    stderr_handle = stderr_path.open("ab") if stderr_path else subprocess.DEVNULL
    try:
        flags = CREATE_NO_WINDOW | DETACHED_PROCESS if os.name == "nt" else 0
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


def has(pattern: str) -> bool:
    rx = re.compile(pattern, re.I)
    return any(rx.search(command or "") for _, command in process_rows())


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
    if quant_script.exists() and not has(r"quant_service\.mjs"):
        hidden_popen([node, quant_script], cwd=QUANT, stdout_path=LOGS / "quant_startup.out.log", stderr_path=LOGS / "quant_startup.err.log")
        log("quant restart requested")
    if gmx_script.exists() and not has(r"gmx_live\.mjs"):
        hidden_popen([node, gmx_script, "--daemon"], cwd=QUANT, stdout_path=LOGS / "gmx_live_startup.out.log", stderr_path=LOGS / "gmx_live_startup.err.log")
    if copy_script.exists() and not has(r"copy_trader_service\.mjs"):
        hidden_popen([node, copy_script, "--daemon"], cwd=QUANT, stdout_path=LOGS / "copy_trader_startup.out.log", stderr_path=LOGS / "copy_trader_startup.err.log")
        log("gmx restart requested")


def start_services(owner: str, read: str) -> None:
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
        return old
    tailscale_url = ensure_tailscale_funnel(read)
    if tailscale_url:
        if tailscale_url != old:
            log("public URL changed to Tailscale Funnel; publishing bridge manifest: " + str(publish_bridge(tailscale_url, read)))
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


log("supervisor started")
try:
    while True:
        owner = owner_token()
        read = read_token()
        start_core()
        start_services(owner, read)
        if http_ok("http://127.0.0.1:8791/dashboard/health", {"X-Myles-Read": read}):
            ensure_tunnel(read)
        lock_repo()
        time.sleep(30)
finally:
    if mutex is not None:
        try:
            ctypes.windll.kernel32.ReleaseMutex(mutex)
        except Exception:
            pass
