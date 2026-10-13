"""Read-only Windows acceptance tests for the actually installed MYLES tower.

Use --live-model to send one harmless local Ollama prompt, and --screen to
test a temporary, protected screenshot capture. Neither is enabled by default.
Does not click, type, install, deploy, trade, modify dashboard, or touch PineTree.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def probe_http(port: int, path: str = "/health") -> dict[str, Any]:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}{path}", timeout=4) as response:
            payload = json.load(response)
        if not isinstance(payload, dict):
            return {"ok": False, "reason": "endpoint returned non-object JSON"}
        return {"ok": bool(payload.get("ok", response.status < 400)),
                "port": port, "version": payload.get("version"),
                "endpoint": path}
    except Exception as exc:
        return {"ok": False, "port": port,
                "reason": type(exc).__name__}


def is_windows() -> bool:
    return os.name == "nt"


def windows_snapshot() -> dict[str, Any]:
    if os.name != "nt":
        return {"ok": False, "reason": "Windows-only probe"}
    try:
        from myles_windows import visible_windows
        windows = visible_windows()
        # No app titles or owner-specific process names written to JSON logs.
        return {"ok": bool(windows), "window_count": len(windows),
                "reason": "" if windows else "No visible interactive Windows session"}
    except Exception as exc:
        return {"ok": False, "reason": type(exc).__name__}


def git_head() -> str:
    try:
        result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                text=True, timeout=6, creationflags=NO_WINDOW)
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def run_acceptance(*, live_model: bool = False, screen: bool = False,
                   expected_head: str = "") -> dict[str, Any]:
    from myles_common import APP_VERSION, load_config
    from myles_model_runtime import model_health_dict
    details: dict[str, Any] = {}
    details["platform"] = {"ok": is_windows(), "windows": is_windows()}
    head = git_head()
    details["source"] = {
        "ok": bool(head and (not expected_head or head == expected_head.lower())),
        "installed_head": head, "version": APP_VERSION,
        "expected_head": expected_head,
    }
    details["core"] = probe_http(8766)
    details["bridge"] = probe_http(8790, "/dashboard/health")
    details["gateway"] = probe_http(8791, "/dashboard/health")
    details["desktop_windows"] = windows_snapshot()
    cfg = load_config()
    model = model_health_dict(cfg)
    details["ollama"] = {
        "ok": bool(model.get("available")), "model": model.get("model"),
        "supports_tools": bool(model.get("supports_tools")),
        "supports_vision": bool(model.get("supports_vision")),
        "reason": model.get("error_kind") or "",
    }
    if live_model:
        from myles_model_runtime import model_chat
        try:
            result = model_chat(cfg, [
                {"role":"system","content":"For this harmless offline acceptance check reply only MYLES_TEST_OK."},
                {"role":"user","content":"Return MYLES_TEST_OK, nothing else."},
            ], temperature=0.0, timeout=40)
            content = str((result.get("message") or {}).get("content") or "").strip()
            details["live_model"] = {
                "ok": content == "MYLES_TEST_OK",
                "reason": "" if content == "MYLES_TEST_OK" else "Model reply differed from exact marker",
            }
        except Exception as exc:
            details["live_model"] = {"ok": False, "reason": type(exc).__name__}
    else:
        details["live_model"] = {"ok": False, "skipped": True,
                                 "reason": "Use --live-model to execute this local test"}
    if screen:
        if os.name != "nt" or not model.get("supports_vision"):
            details["screen"] = {"ok": False, "reason": "Windows vision model unavailable"}
        else:
            from myles_windows import capture_desktop_png, visible_windows
            from myles_interactive import _protected
            try:
                windows = visible_windows()
                if _protected(windows):
                    details["screen"] = {"ok": False,
                                         "reason": "Protected project window visible; capture refused"}
                else:
                    with tempfile.TemporaryDirectory(prefix="myles_accept_screen_") as d:
                        path = Path(d) / "capture.png"
                        meta = capture_desktop_png(path)
                        good = path.is_file() and path.stat().st_size > 64
                        details["screen"] = {
                            "ok": good,
                            "width": meta.get("width"),
                            "height": meta.get("height"),
                            "reason": "" if good else "Capture was empty",
                        }
                        # Temp directory removes screenshot; only dimensions retained.
            except Exception as exc:
                details["screen"] = {"ok": False, "reason": type(exc).__name__}
    else:
        details["screen"] = {"ok": False, "skipped": True,
                             "reason": "Use --screen for a temporary local screenshot probe"}
    must_pass = ("platform", "source", "core", "bridge", "gateway", "desktop_windows", "ollama")
    required = list(must_pass)
    if live_model:
        required.append("live_model")
    if screen:
        required.append("screen")
    return {
        "schema": 1,
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "pass": all(details[name].get("ok") is True for name in required),
        "checks": details,
        "limitations": [
            "This is a live runtime observation, not proof every desktop action works.",
            "No mouse, keyboard, trades, PineTree or deployment commands are executed.",
            "An unloaded or locked interactive session can make desktop inspection unavailable.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="MYLES local Windows acceptance tests")
    p.add_argument("--live-model", action="store_true")
    p.add_argument("--screen", action="store_true")
    p.add_argument("--expected-head", default="")
    opts = p.parse_args(argv)
    report = run_acceptance(live_model=opts.live_model, screen=opts.screen,
                            expected_head=opts.expected_head)
    # This script intentionally does not write results outside the MYLES logs folder.
    path = ROOT / "logs" / "acceptance_windows_latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
