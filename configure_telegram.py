from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from myles_common import ROOT, PID_PATH, load_config, save_config, load_secrets, save_secrets


def api(token: str, method: str, data: dict | None = None, timeout: int = 20) -> dict:
    payload = urllib.parse.urlencode(data or {}).encode("utf-8")
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def stop_core() -> None:
    if os.name != "nt":
        return
    supervisor = ROOT / "runtime_supervisor.py"
    if supervisor.exists():
        subprocess.run(
            [sys.executable, str(supervisor), "stop"],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    time.sleep(1)


def start_core() -> None:
    py = Path(sys.executable)
    pyw = py.with_name("pythonw.exe") if os.name == "nt" else py
    exe = pyw if pyw.exists() else py
    supervisor = ROOT / "runtime_supervisor.py"
    subprocess.Popen(
        [str(exe), str(supervisor)],
        cwd=str(ROOT),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def main() -> int:
    print("=" * 64)
    print(" MYLES v9.7 - TELEGRAM SETUP")
    print("=" * 64)
    print("Telegram is only the remote conversation channel. Myles still runs locally.")
    print()

    existing = load_secrets()
    token = str(existing.get("MYLES_TELEGRAM_TOKEN") or "").strip()
    owner = str(existing.get("MYLES_OWNER_ID") or existing.get("MYLES_TELEGRAM_USER_ID") or "").strip()

    if token:
        print("Existing Telegram bot token found. It will be reused.")
    else:
        token = input("Paste the Telegram bot token: ").strip()
    if not token:
        print("No token supplied. Nothing changed.")
        return 2

    try:
        me = api(token, "getMe")
        if not me.get("ok"):
            raise RuntimeError("Telegram rejected the token")
        bot_name = ((me.get("result") or {}).get("username") or "Myles bot")
        print(f"Bot verified: @{bot_name}")
    except Exception as exc:
        print(f"Token verification failed: {type(exc).__name__}: {exc}")
        return 3

    if owner and owner.isdigit():
        print("Existing owner Telegram ID found. It will be reused.")
    else:
        owner = input("Your numeric Telegram user ID (leave blank to detect it): ").strip()
        if not owner:
            print("Send any message to the Myles bot in Telegram now, then press Enter here.")
            input()
            try:
                updates = api(token, "getUpdates", {"timeout": 1})
                candidates = []
                for u in updates.get("result") or []:
                    m = u.get("message") or {}
                    f = m.get("from") or {}
                    if f.get("id"):
                        candidates.append(str(f["id"]))
                if candidates:
                    owner = candidates[-1]
                    print("Owner ID detected.")
            except Exception as exc:
                print(f"Could not detect owner ID: {type(exc).__name__}: {exc}")

    if not owner.isdigit():
        print("A numeric owner ID is required so nobody else can control Myles.")
        return 4

    save_secrets({"MYLES_TELEGRAM_TOKEN": token, "MYLES_OWNER_ID": owner})
    cfg = load_config()
    cfg["telegram_enabled"] = True
    save_config(cfg)

    print("Telegram saved. Restarting Myles...")
    stop_core()
    start_core()
    print("Done. Send Myles a normal message in Telegram. No slash command is required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
