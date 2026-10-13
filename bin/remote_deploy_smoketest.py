"""One-time local read-only confidence check after owner enables tower updates.

Never fetches executable instructions or launches UPDATE_TOWER.ps1. Returns a
clear pass/fail signal for installed SHA, CI access and opt-in configuration.
"""
from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "MylesAI"
FLAG = ROOT / "data" / "remote_deploy_enabled.json"
EXPECTED_ORIGIN = "https://github.com/JoshuaDuskin/MylesAI.git"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def git(*args: str) -> str:
    p = subprocess.run(["git","-C",str(ROOT),*args],text=True,
                       stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                       timeout=10,creationflags=NO_WINDOW)
    return p.stdout.strip() if p.returncode == 0 else ""


def probe() -> dict:
    from bin.verified_release import verify_ci
    try:
        cfg = json.loads(FLAG.read_text(encoding="utf-8-sig"))
    except (ValueError,OSError):
        cfg = {}
    installed = git("rev-parse", "HEAD").lower()
    canonical = git("remote", "get-url", "origin") == EXPECTED_ORIGIN
    opted_in = cfg.get("enabled") is True and cfg.get("auto_update") is True
    approved, reason = False, ""
    if installed and canonical:
        try:
            approved = verify_ci(installed)
        except Exception as exc:
            reason = "CI metadata unavailable: " + type(exc).__name__
    if not approved and not reason:
        reason = "installed source has no verified successful GitHub main push CI"
    return {"ready": bool(canonical and opted_in and approved),
            "canonical_remote": canonical, "auto_update_enabled": opted_in,
            "installed_sha": installed, "ci_approved": approved,
            "reason": reason}


if __name__ == "__main__":
    status = probe()
    print("MYLES UNATTENDED UPDATE PROBE: " +
          ("READY" if status["ready"] else "NEEDS ATTENTION"))
    print(json.dumps(status, indent=2))
    raise SystemExit(0 if status["ready"] else 2)
