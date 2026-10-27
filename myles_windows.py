from __future__ import annotations

"""Native, verified Windows actions shared by chat and durable jobs.

This module deliberately avoids command shells and generated helper scripts.
Interactive desktop work must not flash console windows.
"""

import ctypes
from ctypes import wintypes
import json
import os
import re
import struct
import subprocess
import time
import zlib
from pathlib import Path


_START_APPS_CACHE: tuple[float, list[dict[str, str]]] = (0.0, [])


def _normalized_app_name(value: str) -> str:
    name = re.sub(r"\s+", " ", str(value or "").strip())
    name = re.sub(r"(?i)^(?:the\s+)", "", name)
    name = re.sub(r"(?i)\s+(?:app|application|program)$", "", name).strip()
    name = re.sub(r"(?i)\.exe$", "", name)
    return "ChatGPT" if re.sub(r"\s+", "", name).casefold() == "chatgpt" else name


def _native_process_rows() -> list[tuple[int, str]]:
    """Enumerate processes through Win32 without creating a child process."""
    if os.name != "nt":
        return []

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32 = ctypes.windll.kernel32
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    invalid = ctypes.c_void_p(-1).value
    if not snapshot or int(snapshot) == invalid:
        return []
    rows: list[tuple[int, str]] = []
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        ok = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            rows.append((int(entry.th32ProcessID), str(entry.szExeFile)))
            ok = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return rows


def process_running(*names: str) -> bool:
    """Check exact executable names without invoking a console program."""
    wanted = {Path(str(name)).name.casefold() for name in names if str(name or "").strip()}
    if os.name != "nt" or not wanted:
        return False
    try:
        import psutil  # type: ignore
        for process in psutil.process_iter(["name"]):
            try:
                if str(process.info.get("name") or "").casefold() in wanted:
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return any(name.casefold() in wanted for _pid, name in _native_process_rows())


def epic_launcher_executable() -> Path | None:
    candidates: list[Path] = []
    for root_name in ("ProgramFiles(x86)", "ProgramFiles"):
        root = str(os.environ.get(root_name) or "").strip()
        if root:
            candidates.append(Path(root) / "Epic Games" / "Launcher" / "Portal" / "Binaries" / "Win64" / "EpicGamesLauncher.exe")
    return next((path for path in candidates if path.is_file()), None)


def _shell_open(target: str, parameters: str = "") -> tuple[bool, str]:
    try:
        result = int(ctypes.windll.shell32.ShellExecuteW(None, "open", str(target), str(parameters) if parameters else None, None, 1))
        return result > 32, f"ShellExecuteW={result}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _process_name(pid: int) -> str:
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenProcess.restype = wintypes.HANDLE
    handle = kernel32.OpenProcess(0x1000, False, int(pid))
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return Path(buffer.value).name
        return ""
    finally:
        kernel32.CloseHandle(handle)


def visible_windows() -> list[dict[str, object]]:
    """Return real visible top-level windows using Win32 enumeration."""
    if os.name != "nt":
        return []
    user32 = ctypes.windll.user32
    rows: list[dict[str, object]] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def collect(hwnd, _lparam):
        try:
            if not user32.IsWindowVisible(hwnd):
                return True
            cloaked = wintypes.DWORD()
            if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked)) == 0 and cloaked.value:
                return True
            length = int(user32.GetWindowTextLengthW(hwnd))
            if length <= 0:
                return True
            title = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title, length + 1)
            if not title.value.strip():
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            rows.append({"Id": int(pid.value), "ProcessName": _process_name(int(pid.value)), "MainWindowTitle": title.value, "Handle": int(hwnd)})
        except Exception:
            pass
        return True

    user32.EnumWindows(collect, 0)
    return rows


def _meaningful_tokens(value: str) -> list[str]:
    ignored = {"app", "application", "program", "the", "microsoft", "windows", "please"}
    return [token for token in re.findall(r"[a-z0-9]+", value.casefold()) if len(token) >= 2 and token not in ignored]


def _matching_visible_windows(requested: str) -> list[dict[str, object]]:
    requested = _normalized_app_name(requested)
    tokens = _meaningful_tokens(requested)
    if not tokens:
        return []
    matches: list[dict[str, object]] = []
    for row in visible_windows():
        title = str(row.get("MainWindowTitle") or "").casefold()
        process = Path(str(row.get("ProcessName") or "")).stem.casefold()
        if _normalized_app_name(requested).casefold() == "xbox":
            if process == "xboxpcapp" or (process == "applicationframehost" and title.strip() == "xbox"):
                matches.append(row)
            continue
        process_match = re.sub(r"[^a-z0-9]", "", requested.casefold()) == re.sub(r"[^a-z0-9]", "", process)
        title_match = all(token in title for token in tokens)
        browser_host = process in {"chrome", "msedge", "firefox", "brave", "opera", "vivaldi"}
        requested_is_browser = any(token in {"chrome", "edge", "firefox", "brave", "opera", "vivaldi"} for token in tokens)
        if process_match or (title_match and (not browser_host or requested_is_browser)):
            matches.append(row)
    return matches


def desktop_operation(action: str, target: str = "", *, window_handle: int = 0,
                      force: bool = False, timeout: float = 3.0) -> dict:
    """Bounded native owner operations. Never discard a document or terminate a process."""
    if os.name != "nt":
        return {"ok": False, "state": "unavailable", "reply": "Windows desktop control requires the Windows tower."}
    try:
        rows = visible_windows()
        if action == "windows":
            return {"ok": True, "state": "observed", "windows": rows,
                    "reply": "Open windows:\n" + ("\n".join(f"{x['MainWindowTitle']} — {x['ProcessName']} (window {x['Handle']})" for x in rows) or "No visible application windows.")}
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.IsWindow.argtypes = [wintypes.HWND]
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        matches = _matching_visible_windows(target) if target else rows if window_handle else [r for r in rows if r['Handle'] == int(user32.GetForegroundWindow() or 0)]
        if window_handle:
            matches = [r for r in matches if r['Handle'] == int(window_handle)]
        if not matches:
            return {"ok": False, "state": "not_found", "reply": f"No matching visible window for {target or 'the current application'}. No action was performed."}
        if len(matches) != 1:
            return {"ok": False, "state": "choice_required", "windows": matches,
                    "reply": "More than one window matches. Specify its full title or window number:\n" + "\n".join(f"{r['MainWindowTitle']} (window {r['Handle']})" for r in matches)}
        row = matches[0]; hwnd = int(row['Handle']); pid = int(row['Id'])
        current = next((r for r in visible_windows() if r['Handle'] == hwnd and r['Id'] == pid), None)
        if not current:
            return {"ok": False, "state": "changed", "reply": "The target window changed before execution. No action was performed."}
        if force:
            return {"ok": False, "state": "confirmation_required", "window": row,
                    "reply": "Force termination could discard unsaved work. It requires separate owner confirmation; I have not terminated anything. Save or close the application's prompt first."}
        if action == "focus":
            ok = _activate_window(row)
            return {"ok": ok, "state": "focused" if ok else "permission_denied", "window": row,
                    "reply": f"Focused {row['MainWindowTitle']}." if ok else "Windows did not allow this window to become the foreground application."}
        if action == "minimize":
            user32.ShowWindow(hwnd, 6)
            ok = bool(user32.IsIconic(hwnd))
            return {"ok": ok, "state": "minimized" if ok else "not_verified", "window": row,
                    "reply": f"Minimized {row['MainWindowTitle']}." if ok else "Windows did not verify the window was minimized."}
        if action != "close":
            return {"ok": False, "state": "unsupported", "reply": "This desktop action is not supported by the current runtime."}
        if not user32.PostMessageW(hwnd, 0x0010, 0, 0):
            return {"ok": False, "state": "permission_denied", "reply": f"Windows rejected the close request (error {ctypes.get_last_error()}). The application was not verified closed."}
        deadline = time.monotonic() + min(10, max(0.1, timeout))
        while time.monotonic() < deadline:
            after = visible_windows()
            if not user32.IsWindow(hwnd):
                remaining = [r for r in _matching_visible_windows(target) if r['Handle'] != hwnd] if target else []
                return {"ok": True, "state": "window_closed", "window": row, "remaining_windows": remaining,
                        "reply": f"Closed the {row['MainWindowTitle']} window." + (" Other matching windows remain open." if remaining else "")}
            time.sleep(.1)
        return {"ok": False, "state": "waiting_on_application", "window": row,
                "reply": "The window is still open. It may be waiting for unsaved-work confirmation or be unresponsive. I have not forced it closed or discarded anything."}
    except Exception as exc:
        return {"ok": False, "state": "tool_error", "reply": f"Windows desktop operation failed: {type(exc).__name__}. No closure was verified."}


def _tap_key(vk: int) -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, 0x0002, 0)


def _type_unicode(text: str) -> tuple[bool, str]:
    """Type Unicode with the native, correctly-sized Windows INPUT union.

    On 64-bit Windows SendInput rejects an INPUT structure whose union omits
    MOUSEINPUT (the largest union arm).  Returning the accepted event count
    prevents a failed type operation from being mistaken for a launch.
    """
    user32 = ctypes.windll.user32

    ULONG_PTR = ctypes.c_size_t

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", ctypes.c_long), ("dy", ctypes.c_long),
            ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", INPUT_UNION)]

    raw = str(text).encode("utf-16-le", errors="surrogatepass")
    inputs: list[INPUT] = []
    for index in range(0, len(raw), 2):
        code_unit = int.from_bytes(raw[index:index + 2], "little")
        inputs.append(INPUT(type=1, ki=KEYBDINPUT(0, code_unit, 0x0004, 0, 0)))
        inputs.append(INPUT(type=1, ki=KEYBDINPUT(0, code_unit, 0x0004 | 0x0002, 0, 0)))
    if not inputs:
        return True, "no characters requested"
    events = (INPUT * len(inputs))(*inputs)
    sent = int(user32.SendInput(len(inputs), events, ctypes.sizeof(INPUT)))
    return sent == len(inputs), f"Windows accepted {sent}/{len(inputs)} keyboard events"


def _hidden_process_options() -> dict[str, object]:
    if os.name != "nt":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
        "startupinfo": startupinfo,
    }


def _installed_start_apps() -> list[dict[str, str]]:
    """Read Windows' app catalog without showing Start, cmd, or PowerShell."""
    global _START_APPS_CACHE
    cached_at, cached = _START_APPS_CACHE
    if cached and time.time() - cached_at < 300:
        return cached
    script = (
        "$ErrorActionPreference='Stop'; "
        "@(Get-StartApps | ForEach-Object { [pscustomobject]@{Name=$_.Name;AppID=$_.AppID} }) "
        "| ConvertTo-Json -Compress"
    )
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, errors="replace", timeout=12,
            **_hidden_process_options(),
        )
        if proc.returncode != 0:
            return cached
        payload = json.loads(proc.stdout or "[]")
        if isinstance(payload, dict):
            payload = [payload]
        rows = [
            {"name": str(row.get("Name") or "").strip(), "app_id": str(row.get("AppID") or "").strip()}
            for row in payload if isinstance(row, dict) and row.get("Name") and row.get("AppID")
        ]
        if rows:
            _START_APPS_CACHE = (time.time(), rows)
            return rows
    except Exception:
        pass
    return cached


def _best_start_app(requested: str) -> dict[str, str] | None:
    wanted = _normalized_app_name(requested).casefold()
    tokens = _meaningful_tokens(wanted)
    ranked: list[tuple[int, int, dict[str, str]]] = []
    for row in _installed_start_apps():
        name = _normalized_app_name(row.get("name", "")).casefold()
        if not name:
            continue
        if name == wanted:
            score = 100
        elif name.startswith(wanted + " ") or wanted.startswith(name + " "):
            score = 80
        elif tokens and all(token in name for token in tokens):
            score = 60
        else:
            continue
        ranked.append((score, -len(name), row))
    return max(ranked, default=(0, 0, None), key=lambda item: (item[0], item[1]))[2]


def _activate_window(row: dict[str, object]) -> bool:
    """Success requires the requested window to become the foreground window."""
    hwnd = int(row.get("Handle") or 0)
    if not hwnd:
        return False
    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.ShowWindow(hwnd, 9)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    for _ in range(5):
        if int(user32.GetForegroundWindow() or 0) == hwnd:
            return True
        time.sleep(0.1)
    return False


def _open_start_menu() -> str:
    if os.name != "nt":
        return "DESKTOP_APP_LAUNCH_UNAVAILABLE: Windows launch is only supported on the tower."
    before = int(ctypes.windll.user32.GetForegroundWindow() or 0)
    _tap_key(0x5B)
    time.sleep(0.8)
    after = int(ctypes.windll.user32.GetForegroundWindow() or 0)
    if after and after != before:
        return "DESKTOP_APP_LAUNCH_VERIFIED: Opened the Windows Start menu and observed a foreground-surface change."
    return "DESKTOP_APP_LAUNCH_NOT_VERIFIED: Windows key was sent, but the Start surface was not observed."


def launch_app_verified(app_name: str, timeout_seconds: int = 20) -> str:
    """Launch any installed app and verify a matching visible window.

    Windows' installed-app catalog is the primary generic mechanism.  Search
    keyboard automation is only a fallback, and it is always dismissed if the
    launch cannot be verified.
    """
    if os.name != "nt":
        return "DESKTOP_APP_LAUNCH_UNAVAILABLE: Windows launch is only supported on the tower."
    requested = _normalized_app_name(app_name)
    if not requested or requested.casefold() in {"app", "application", "program", "it", "this"}:
        return "DESKTOP_APP_LAUNCH_ERROR: A specific application name is required."
    if requested.casefold() in {"start", "start menu", "windows start menu"}:
        return _open_start_menu()
    existing = _matching_visible_windows(requested)
    if existing and _activate_window(existing[0]):
        return f"DESKTOP_APP_LAUNCH_VERIFIED: {requested} is already visibly open; window={existing[0].get('MainWindowTitle')}."

    before_pids = {int(row.get("Id") or 0) for row in visible_windows()}
    deadline = time.time() + max(5, min(int(timeout_seconds), 45))
    catalog_match = _best_start_app(requested)
    launch_evidence = ""
    if catalog_match:
        launched, launch_evidence = _shell_open("shell:AppsFolder\\" + catalog_match["app_id"])
        launch_evidence = f"StartApps={catalog_match['name']!r}; {launch_evidence}"
        if not launched:
            catalog_match = None
    if not catalog_match:
        _tap_key(0x5B)
        time.sleep(0.7)
        typed, type_evidence = _type_unicode(requested)
        if not typed:
            _tap_key(0x1B)
            return f"DESKTOP_APP_LAUNCH_ERROR: Windows Search typing failed ({type_evidence})."
        time.sleep(0.8)
        _tap_key(0x0D)
        launch_evidence = f"Windows Search; {type_evidence}"
    while time.time() < deadline:
        matches = _matching_visible_windows(requested)
        if matches:
            row = next((item for item in matches if int(item.get("Id") or 0) not in before_pids), matches[0])
            if not _activate_window(row):
                time.sleep(0.75)
                continue
            return f"DESKTOP_APP_LAUNCH_VERIFIED: Opened {requested}; visible window={row.get('MainWindowTitle')}; process={row.get('ProcessName')}; method={launch_evidence}."
        time.sleep(0.75)
    if not catalog_match:
        _tap_key(0x1B)
    return f"DESKTOP_APP_LAUNCH_NOT_VERIFIED: Windows received the launch request for {requested!r} ({launch_evidence}), but no matching visible application window appeared. MYLES must inspect the screen or report the blocker; it must not claim success."


def close_xbox_verified(timeout_seconds: int = 10) -> str:
    """Close only Xbox app windows normally; leave games and tray processes alone."""
    if os.name != "nt":
        return "DESKTOP_APP_CLOSE_UNAVAILABLE: Windows is required."
    windows = _matching_visible_windows("Xbox")
    if not windows:
        return "DESKTOP_APP_CLOSE_ALREADY_CLOSED: Xbox has no visible app window."
    user32 = ctypes.windll.user32
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    for row in windows:
        hwnd = int(row.get("Handle") or 0)
        if hwnd:
            user32.PostMessageW(hwnd, 0x0010, 0, 0)
    deadline = time.time() + max(1, min(int(timeout_seconds), 20))
    while time.time() < deadline:
        if not _matching_visible_windows("Xbox"):
            return "DESKTOP_APP_CLOSE_VERIFIED: Xbox app windows closed."
        time.sleep(0.25)
    return "DESKTOP_APP_CLOSE_NOT_VERIFIED: Xbox still has a visible app window."


def _fortnite_visible() -> dict[str, object] | None:
    actual_names = {"fortniteclient-win64-shipping.exe", "fortniteclient-win64-shipping_be.exe"}
    for row in visible_windows():
        process_name = str(row.get("ProcessName") or "").casefold()
        if process_name in actual_names:
            return row
    return None



# Only the actual Fortnite game client is in scope. Do not terminate the
# Xbox app, Epic Launcher, anti-cheat service or any similarly named process.
FORTNITE_CLIENT_EXES = frozenset({
    "fortniteclient-win64-shipping.exe",
    "fortniteclient-win64-shipping_be.exe",
})


def _fortnite_client_pids() -> set[int]:
    return {int(pid) for pid, name in _native_process_rows()
            if int(pid) > 0 and str(name).casefold() in FORTNITE_CLIENT_EXES}


def _fortnite_client_still_present() -> bool:
    return bool(_fortnite_client_pids() or process_running(*FORTNITE_CLIENT_EXES)
                or _fortnite_visible())


def _terminate_exact_fortnite_client(pid: int) -> bool:
    """Target one confirmed game client, not Xbox/Epic/launcher children."""
    if os.name != "nt" or not isinstance(pid, int) or pid <= 0:
        return False
    # psutil confirms the executable identity from the existing process handle.
    try:
        import psutil
        proc = psutil.Process(pid)
        if str(proc.name()).casefold() not in FORTNITE_CLIENT_EXES:
            return False
        proc.terminate()
        return True
    except ImportError:
        pass
    except (OSError, PermissionError, Exception):
        # A rejected kill is not grounds to kill by PID without verification.
        return False
    # Native fallback checks the actual image held open, including PID reuse.
    try:
        kernel = ctypes.windll.kernel32
        kernel.OpenProcess.restype = wintypes.HANDLE
        handle = kernel.OpenProcess(0x0001 | 0x1000, False, int(pid))
        if not handle:
            return False
        try:
            size = wintypes.DWORD(32768)
            image = ctypes.create_unicode_buffer(size.value)
            if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)):
                return False
            if Path(image.value).name.casefold() not in FORTNITE_CLIENT_EXES:
                return False
            return bool(kernel.TerminateProcess(handle, 0))
        finally:
            kernel.CloseHandle(handle)
    except Exception:
        return False


def close_fortnite_verified(timeout_seconds: int = 12) -> str:
    """Execute explicit owner CLOSE even during Game Mode, without model/worker.

    Attempt WM_CLOSE on verified game windows first, then terminate only
    confirmed Fortnite client executables. Success requires actual disappearance.
    """
    if os.name != "nt":
        return "FORTNITE_CLOSE_UNAVAILABLE: Windows tower required."
    targets = _fortnite_client_pids()
    if not targets:
        if _fortnite_client_still_present():
            return "FORTNITE_CLOSE_NOT_VERIFIED: Game detected but its exact process could not be identified safely."
        return "FORTNITE_NOT_RUNNING: No Fortnite game client is running."
    try:
        user32 = ctypes.windll.user32
        for row in visible_windows():
            if (int(row.get("Id") or 0) in targets
                    and str(row.get("ProcessName") or "").casefold() in FORTNITE_CLIENT_EXES):
                hwnd = int(row.get("Handle") or 0)
                if hwnd:
                    user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
    except Exception:
        pass
    grace_end = time.monotonic() + min(5, max(1, int(timeout_seconds) // 2))
    while time.monotonic() < grace_end:
        if not _fortnite_client_still_present():
            return "FORTNITE_CLOSED_VERIFIED: Fortnite game client has exited."
        time.sleep(0.3)
    # Explicit "close Fortnite" authorizes targeting the game client itself,
    # but not force-closing Xbox, other games, game launchers, or services.
    for pid in _fortnite_client_pids() & targets:
        _terminate_exact_fortnite_client(pid)
    deadline = time.monotonic() + min(6, max(1, int(timeout_seconds) // 2))
    while time.monotonic() < deadline:
        if not _fortnite_client_still_present():
            return "FORTNITE_CLOSED_VERIFIED: Fortnite game client has exited."
        time.sleep(0.3)
    return "FORTNITE_CLOSE_NOT_VERIFIED: Fortnite is still running or Windows denied closing its verified game process."

def launch_fortnite_verified(timeout_seconds: int = 40) -> str:
    """Launch the installed Fortnite edition and verify its foreground game window."""
    if os.name != "nt":
        return "FORTNITE_LAUNCH_UNAVAILABLE: Windows launch is only supported on the tower."
    current = _fortnite_visible()
    if current and _activate_window(current):
        return f"FORTNITE_RUNNING: Visible Fortnite game window verified; process={current.get('ProcessName')}."
    uri = "com.epicgames.launcher://apps/Fortnite?action=launch&silent=true"
    installed = _best_start_app("Fortnite")
    if installed and _normalized_app_name(installed["name"]).casefold() == "fortnite":
        requested, evidence = _shell_open("shell:AppsFolder\\" + installed["app_id"])
    else:
        requested, evidence = _shell_open(uri)
    launcher = epic_launcher_executable()
    if not requested and launcher:
        requested, evidence = _shell_open(str(launcher), uri)
    if not requested:
        return f"FORTNITE_LAUNCH_ERROR: Windows could not open the Epic Fortnite handler ({evidence})."
    deadline = time.time() + max(12, min(int(timeout_seconds), 75))
    resent = False
    while time.time() < deadline:
        current = _fortnite_visible()
        if current and _activate_window(current):
            return f"FORTNITE_RUNNING: Visible Fortnite game window verified; process={current.get('ProcessName')}."
        if not resent and process_running("epicgameslauncher.exe"):
            time.sleep(2)
            _shell_open(uri)
            resent = True
        time.sleep(1)
    helpers = [name for name in ("epicgameslauncher.exe", "fortnitelauncher.exe", "fortniteclient-win64-shipping_eac_eos.exe") if process_running(name)]
    helper_text = ", ".join(helpers) if helpers else "none"
    return "FORTNITE_NOT_VERIFIED: The launch request ran, but no visible Fortnite game client appeared. " + f"Launcher/helper processes are progress, not success (observed: {helper_text}). MYLES must inspect the screen next."


def capture_desktop_png(destination: Path) -> dict[str, object]:
    """Capture the virtual desktop with GDI and write a PNG without a shell."""
    if os.name != "nt":
        raise RuntimeError("desktop capture is only available on Windows")
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    # ctypes otherwise assumes 32-bit integer arguments for untyped Win32
    # functions. GDI handles are pointer-sized; on 64-bit Windows that default
    # raises OverflowError/ArgumentError before a screenshot can be captured.
    user32.SetProcessDPIAware.argtypes = []
    user32.SetProcessDPIAware.restype = wintypes.BOOL
    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.GetSystemMetrics.restype = ctypes.c_int
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.GetDC.restype = wintypes.HDC
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.ReleaseDC.restype = ctypes.c_int
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.BitBlt.argtypes = [
        wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD,
    ]
    gdi32.BitBlt.restype = wintypes.BOOL
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteObject.restype = wintypes.BOOL
    gdi32.DeleteDC.argtypes = [wintypes.HDC]
    gdi32.DeleteDC.restype = wintypes.BOOL
    user32.SetProcessDPIAware()
    left, top = int(user32.GetSystemMetrics(76)), int(user32.GetSystemMetrics(77))
    width, height = int(user32.GetSystemMetrics(78)), int(user32.GetSystemMetrics(79))
    if width <= 0 or height <= 0:
        raise RuntimeError(f"invalid virtual-screen bounds {left},{top} {width}x{height}")

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long), ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long), ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]

    gdi32.GetDIBits.argtypes = [
        wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
        ctypes.c_void_p, ctypes.POINTER(BITMAPINFO), wintypes.UINT,
    ]
    gdi32.GetDIBits.restype = ctypes.c_int
    screen_dc = user32.GetDC(None)
    memory_dc = gdi32.CreateCompatibleDC(screen_dc)
    bitmap = gdi32.CreateCompatibleBitmap(screen_dc, width, height)
    if not screen_dc or not memory_dc or not bitmap:
        raise RuntimeError("GDI desktop-capture allocation failed")
    old_object = gdi32.SelectObject(memory_dc, bitmap)
    try:
        if not gdi32.BitBlt(memory_dc, 0, 0, width, height, screen_dc, left, top, 0x40CC0020):
            raise RuntimeError("GDI BitBlt failed")
        info = BITMAPINFO()
        info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        info.bmiHeader.biWidth, info.bmiHeader.biHeight = width, -height
        info.bmiHeader.biPlanes, info.bmiHeader.biBitCount, info.bmiHeader.biCompression = 1, 32, 0
        size = width * height * 4
        buffer = (ctypes.c_ubyte * size)()
        if not gdi32.GetDIBits(memory_dc, bitmap, 0, height, buffer, ctypes.byref(info), 0):
            raise RuntimeError("GDI GetDIBits failed")
        pixels = bytearray(buffer)
        blue = pixels[0::4]
        pixels[0::4], pixels[2::4] = pixels[2::4], blue
        pixels[3::4] = b"\xff" * (width * height)
        stride = width * 4
        scanlines = b"".join(b"\x00" + pixels[offset:offset + stride] for offset in range(0, len(pixels), stride))

        def chunk(kind: bytes, payload: bytes) -> bytes:
            body = kind + payload
            return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

        png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(scanlines, 6)) + chunk(b"IEND", b"")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(png)
    finally:
        if old_object:
            gdi32.SelectObject(memory_dc, old_object)
        if bitmap:
            gdi32.DeleteObject(bitmap)
        if memory_dc:
            gdi32.DeleteDC(memory_dc)
        if screen_dc:
            user32.ReleaseDC(None, screen_dc)
    return {"left": left, "top": top, "width": width, "height": height, "path": str(destination)}
