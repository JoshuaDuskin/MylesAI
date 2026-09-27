from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from myles_common import APP_VERSION, ROOT, load_config

cfg = load_config()
BASE = f"http://{cfg['core_host']}:{cfg['core_port']}"


def request(path: str, method: str = "GET", payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def ensure_supervisor() -> None:
    if os.environ.get("MYLES_SUPERVISOR_STARTED") == "1":
        return
    supervisor = ROOT / "runtime_supervisor.py"
    if not supervisor.exists():
        return
    python = Path(sys.executable)
    candidate = python.with_name("pythonw.exe") if os.name == "nt" else python
    executable = candidate if candidate.exists() else python
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    try:
        subprocess.Popen(
            [str(executable), str(supervisor)],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
    except Exception:
        # The existing core may already be healthy; wait_for_core will report
        # the actual state instead of claiming that a supervisor started.
        pass


def wait_for_core(timeout_seconds: int = 45):
    deadline = time.time() + timeout_seconds
    announced = False
    while time.time() < deadline:
        try:
            return request("/health")
        except Exception:
            if not announced:
                print("Starting the hidden Myles core...", flush=True)
                announced = True
            time.sleep(0.5)
    return None


def main() -> int:
    print("=" * 62)
    print(f" MYLES {APP_VERSION} — CONSOLE")
    print("=" * 62)
    print("This window is only an interface. Closing it does not stop Myles.")
    print("Talk to Myles normally. Type quit only when you want to close this console.")
    print("")

    ensure_supervisor()
    health = wait_for_core()
    if not health:
        print("Myles core is not reachable after 45 seconds.")
        print(f"Check {ROOT / 'logs' / 'supervisor.log'} and {ROOT / 'logs' / 'core.log'}.")
        return 1
    print(health.get("status", "Myles online."))

    while True:
        try:
            text = input("\nYou > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("")
            return 0
        if not text:
            continue
        if text.lower() in {"quit", "exit", "close"}:
            return 0
        try:
            result = request("/api/send", "POST", {"text": text})
            print("\nMyles > " + str(result.get("reply", result)))
        except Exception as exc:
            print(f"\nMyles > Core request failed: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
