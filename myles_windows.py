from __future__ import annotations

"""Shared, verified Windows actions used by chat and durable jobs."""

import ctypes
import os
import subprocess
import time
from pathlib import Path


CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0)


def process_running(*names: str) -> bool:
    if os.name != "nt":
        return False
    try:
        completed = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=8,
            creationflags=CREATE_NO_WINDOW,
        )
        listing = str(completed.stdout or "").lower()
        return any(str(name or "").lower() in listing for name in names if name)
    except Exception:
        return False


def epic_launcher_executable() -> Path | None:
    candidates: list[Path] = []
    for root_name in ("ProgramFiles(x86)", "ProgramFiles"):
        root = str(os.environ.get(root_name) or "").strip()
        if root:
            candidates.append(
                Path(root)
                / "Epic Games"
                / "Launcher"
                / "Portal"
                / "Binaries"
                / "Win64"
                / "EpicGamesLauncher.exe"
            )
    return next((path for path in candidates if path.is_file()), None)


def _shell_open(target: str, parameters: str = "") -> tuple[bool, str]:
    try:
        result = int(
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "open",
                str(target),
                str(parameters) if parameters else None,
                None,
                1,
            )
        )
        return result > 32, f"ShellExecuteW={result}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def launch_fortnite_verified(timeout_seconds: int = 40) -> str:
    """Launch Fortnite through Epic and report only process-verified success."""
    if os.name != "nt":
        return "FORTNITE_LAUNCH_UNAVAILABLE: Windows launch is only supported on the tower."

    fortnite_processes = (
        "fortniteclient-win64-shipping.exe",
        "fortnitelauncher.exe",
        "fortniteclient-win64-shipping_eac_eos.exe",
    )
    if process_running(*fortnite_processes):
        return "FORTNITE_RUNNING: Fortnite is already running."

    uri = "com.epicgames.launcher://apps/Fortnite?action=launch&silent=true"
    requested, evidence = _shell_open(uri)
    launcher = epic_launcher_executable()
    if not requested and launcher:
        try:
            subprocess.Popen(
                [str(launcher), uri],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
                close_fds=True,
            )
            requested = True
            evidence = "EpicGamesLauncher.exe started with Fortnite URI"
        except Exception as exc:
            evidence = f"{type(exc).__name__}: {exc}"

    if not requested:
        return f"FORTNITE_LAUNCH_ERROR: Windows could not open the Epic Fortnite handler ({evidence})."

    deadline = time.time() + max(12, min(int(timeout_seconds), 55))
    resent = False
    while time.time() < deadline:
        if process_running(*fortnite_processes):
            return "FORTNITE_RUNNING: Fortnite process verified and is opening now."
        if not resent and process_running("epicgameslauncher.exe"):
            # The first URI can be consumed while Epic is cold-starting. Send it
            # once more after the launcher owns its registered protocol handler.
            time.sleep(2)
            _shell_open(uri)
            resent = True
        time.sleep(1)

    if process_running("epicgameslauncher.exe"):
        return (
            "FORTNITE_NOT_VERIFIED: Epic Games Launcher is open and received the "
            "Fortnite request, but no Fortnite process appeared. Epic may need a "
            "sign-in, update, or on-screen confirmation."
        )
    return "FORTNITE_NOT_VERIFIED: Windows accepted the launch request, but neither Epic nor Fortnite stayed open."
