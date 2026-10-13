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
    return re.sub(r"(?i)\s+(?:app|application|program)$", "", name).strip()


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
    tokens = _meaningful_tokens(requested)
    if not tokens:
        return []
    matches: list[dict[str, object]] = []
    for row in visible_windows():
        title = str(row.get("MainWindowTitle") or "").casefold()
        process = Path(str(row.get("ProcessName") or "")).stem.casefold()
        process_match = any(token in process for token in tokens)
        title_match = all(token in title for token in tokens)
        browser_host = process in {"chrome", "msedge", "firefox", "brave", "opera", "vivaldi"}
        requested_is_browser = any(token in {"chrome", "edge", "firefox", "brave", "opera", "vivaldi"} for token in tokens)
        if process_match or (title_match and (not browser_host or requested_is_browser)):
            matches.append(row)
    return matches


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


def _activate_window(row: dict[str, object]) -> None:
    hwnd = int(row.get("Handle") or 0)
    if not hwnd:
        return
    user32 = ctypes.windll.user32
    user32.ShowWindow(hwnd, 9)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)


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
    if existing:
        _activate_window(existing[0])
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
            _activate_window(row)
            return f"DESKTOP_APP_LAUNCH_VERIFIED: Opened {requested}; visible window={row.get('MainWindowTitle')}; process={row.get('ProcessName')}; method={launch_evidence}."
        time.sleep(0.75)
    if not catalog_match:
        _tap_key(0x1B)
    return f"DESKTOP_APP_LAUNCH_NOT_VERIFIED: Windows received the launch request for {requested!r} ({launch_evidence}), but no matching visible application window appeared. MYLES must inspect the screen or report the blocker; it must not claim success."


def _fortnite_visible() -> dict[str, object] | None:
    actual_names = {"fortniteclient-win64-shipping.exe", "fortniteclient-win64-shipping_be.exe"}
    for row in visible_windows():
        process_name = str(row.get("ProcessName") or "").casefold()
        if process_name in actual_names:
            return row
    return None


def launch_fortnite_verified(timeout_seconds: int = 40) -> str:
    """Request Fortnite through Epic, but succeed only on a visible game client."""
    if os.name != "nt":
        return "FORTNITE_LAUNCH_UNAVAILABLE: Windows launch is only supported on the tower."
    current = _fortnite_visible()
    if current:
        return f"FORTNITE_RUNNING: Visible Fortnite game window verified; process={current.get('ProcessName')}."
    uri = "com.epicgames.launcher://apps/Fortnite?action=launch&silent=true"
    requested, evidence = _shell_open(uri)
    launcher = epic_launcher_executable()
    if not requested and launcher:
        requested, evidence = _shell_open(str(launcher), uri)
    if not requested:
        return f"FORTNITE_LAUNCH_ERROR: Windows could not open the Epic Fortnite handler ({evidence})."
    deadline = time.time() + max(12, min(int(timeout_seconds), 55))
    resent = False
    while time.time() < deadline:
        current = _fortnite_visible()
        if current:
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
