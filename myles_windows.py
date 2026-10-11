from __future__ import annotations

"""Shared, verified Windows actions used by chat and durable jobs."""

import ctypes
import json
import os
import re
import subprocess
import time
from pathlib import Path


CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0)

APP_ALIASES = {
    "xbox": {
        "start_names": ("Xbox",),
        "processes": ("XboxPcApp.exe", "XboxApp.exe", "GamingApp.exe"),
        "window_terms": ("xbox",),
        "uris": ("xbox://",),
    },
    "epic games launcher": {
        "start_names": ("Epic Games Launcher",),
        "processes": ("EpicGamesLauncher.exe",),
        "window_terms": ("epic games",),
    },
    "notepad": {
        "start_names": ("Notepad",),
        "processes": ("notepad.exe",),
        "window_terms": ("notepad",),
    },
    "calculator": {
        "start_names": ("Calculator",),
        "processes": ("CalculatorApp.exe", "Calculator.exe"),
        "window_terms": ("calculator",),
        "uris": ("calculator:",),
    },
    "settings": {
        "start_names": ("Settings",),
        "processes": ("SystemSettings.exe",),
        "window_terms": ("settings",),
        "uris": ("ms-settings:",),
    },
}


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


def _powershell_json(script: str, timeout: int = 12) -> object:
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        creationflags=CREATE_NO_WINDOW,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "PowerShell failed").strip())
    raw = str(completed.stdout or "").strip()
    return json.loads(raw) if raw else []


def visible_windows() -> list[dict[str, object]]:
    """Return process-backed visible windows without showing a console."""
    if os.name != "nt":
        return []
    script = (
        "@(Get-Process | Where-Object {$_.MainWindowHandle -ne 0 -and $_.MainWindowTitle} | "
        "Select-Object Id,ProcessName,MainWindowTitle) | ConvertTo-Json -Compress"
    )
    try:
        data = _powershell_json(script)
        rows = data if isinstance(data, list) else [data]
        return [row for row in rows if isinstance(row, dict)]
    except Exception:
        return []


def _normalized_app_name(value: str) -> str:
    name = re.sub(r"\s+", " ", str(value or "").strip())
    name = re.sub(r"(?i)^(?:the\s+)", "", name)
    name = re.sub(r"(?i)\s+(?:app|application)$", "", name).strip()
    return name


def _start_apps() -> list[dict[str, str]]:
    if os.name != "nt":
        return []
    try:
        data = _powershell_json("@(Get-StartApps | Select-Object Name,AppID) | ConvertTo-Json -Compress")
        rows = data if isinstance(data, list) else [data]
        return [
            {"Name": str(row.get("Name") or ""), "AppID": str(row.get("AppID") or "")}
            for row in rows if isinstance(row, dict) and row.get("Name") and row.get("AppID")
        ]
    except Exception:
        return []


def _match_start_app(requested: str, aliases: tuple[str, ...]) -> dict[str, str] | None:
    wanted = [requested, *aliases]
    wanted_low = [value.casefold() for value in wanted if value]
    apps = _start_apps()
    for candidate in apps:
        if candidate["Name"].casefold() in wanted_low:
            return candidate
    ranked: list[tuple[int, dict[str, str]]] = []
    for candidate in apps:
        low = candidate["Name"].casefold()
        scores = [
            2 if low.startswith(value + " ") or low.endswith(" " + value) else 1
            for value in wanted_low if len(value) >= 3 and value in low
        ]
        if scores:
            ranked.append((max(scores), candidate))
    ranked.sort(key=lambda item: (-item[0], len(item[1]["Name"])))
    return ranked[0][1] if ranked else None


def launch_app_verified(app_name: str, timeout_seconds: int = 20) -> str:
    """Launch a Start-menu app and report success only with process/window evidence."""
    if os.name != "nt":
        return "DESKTOP_APP_LAUNCH_UNAVAILABLE: Windows launch is only supported on the tower."
    requested = _normalized_app_name(app_name)
    if not requested or requested.casefold() in {"app", "application", "program", "it", "this"}:
        return "DESKTOP_APP_LAUNCH_ERROR: A specific application name is required."

    key = requested.casefold()
    alias = APP_ALIASES.get(key, {})
    expected_processes = tuple(alias.get("processes", ()))
    window_terms = tuple(alias.get("window_terms", (requested.casefold(),)))
    before_windows = visible_windows()
    before_pids = {int(row.get("Id") or 0) for row in before_windows}

    if expected_processes and process_running(*expected_processes):
        return f"DESKTOP_APP_LAUNCH_VERIFIED: {requested} is already running; process evidence matched {', '.join(expected_processes)}."
    for row in before_windows:
        title = str(row.get("MainWindowTitle") or "").casefold()
        if any(term.casefold() in title for term in window_terms if term):
            return f"DESKTOP_APP_LAUNCH_VERIFIED: {requested} is already open; visible window={row.get('MainWindowTitle')}."

    matched = _match_start_app(requested, tuple(alias.get("start_names", ())))
    launched = False
    method = ""
    evidence = ""
    if matched:
        launched, evidence = _shell_open("shell:AppsFolder\\" + matched["AppID"])
        method = f"Start app {matched['Name']}"
    if not launched:
        for uri in tuple(alias.get("uris", ())):
            launched, evidence = _shell_open(uri)
            method = f"registered URI {uri}"
            if launched:
                break
    if not launched:
        launched, evidence = _shell_open(requested)
        method = f"Windows shell target {requested}"
    if not launched:
        return f"DESKTOP_APP_LAUNCH_ERROR: Windows could not launch {requested} ({evidence})."

    deadline = time.time() + max(5, min(int(timeout_seconds), 45))
    while time.time() < deadline:
        if expected_processes and process_running(*expected_processes):
            return f"DESKTOP_APP_LAUNCH_VERIFIED: Opened {requested} via {method}; process evidence matched {', '.join(expected_processes)}."
        for row in visible_windows():
            title = str(row.get("MainWindowTitle") or "")
            process_name = str(row.get("ProcessName") or "")
            pid = int(row.get("Id") or 0)
            if any(term.casefold() in title.casefold() for term in window_terms if term):
                return f"DESKTOP_APP_LAUNCH_VERIFIED: Opened {requested} via {method}; visible window={title}."
            if matched and pid not in before_pids and matched["Name"].casefold() in (title + " " + process_name).casefold():
                return f"DESKTOP_APP_LAUNCH_VERIFIED: Opened {requested} via {method}; new visible process={process_name}."
        time.sleep(1)
    return (
        f"DESKTOP_APP_LAUNCH_NOT_VERIFIED: Windows accepted the request for {requested} via {method}, "
        "but no matching process or visible window appeared. The app may require sign-in, an update, or a visible confirmation."
    )


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
