from __future__ import annotations

import ctypes
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "MylesAI"
DATA = ROOT / "data"
LOGS = ROOT / "logs"
CONFIG_FILE = DATA / "config.json"
STATE_FILE = DATA / "game_mode_state.json"
LOG_FILE = LOGS / "game_mode_watch.log"
CHECK_SECONDS = 1.0
STATE_HEARTBEAT_SECONDS = 5.0
EXIT_GRACE_SECONDS = 20.0

DATA.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

WATCHER_FILE_LOCK = None
WATCHER_MUTEX = None
if os.name == "nt":
    # A Windows named mutex can split into Global and Local namespaces when
    # elevated and non-elevated launchers overlap. Hold an OS file lock too so
    # exactly one watcher survives across both privilege/session contexts.
    import msvcrt

    lock_path = DATA / "game_mode_watcher.lock"
    try:
        WATCHER_FILE_LOCK = lock_path.open("a+b")
        WATCHER_FILE_LOCK.seek(0, os.SEEK_END)
        if WATCHER_FILE_LOCK.tell() < 1:
            WATCHER_FILE_LOCK.write(b"0")
            WATCHER_FILE_LOCK.flush()
        WATCHER_FILE_LOCK.seek(0)
        msvcrt.locking(WATCHER_FILE_LOCK.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        try:
            if WATCHER_FILE_LOCK is not None:
                WATCHER_FILE_LOCK.close()
        except Exception:
            pass
        raise SystemExit(0)

    k32 = ctypes.windll.kernel32
    for mutex_name in ("Global\\MylesGameModeWatcher_v2", "Local\\MylesGameModeWatcher_v2"):
        handle = k32.CreateMutexW(None, False, mutex_name)
        if handle:
            WATCHER_MUTEX = handle
            if k32.GetLastError() == 183:
                raise SystemExit(0)
            break

# Exact names cover games whose install path may be hidden by anti-cheat launchers.
KNOWN_GAME_NAMES = {
    "fortniteclient-win64-shipping.exe",
    "fortniteclient-win64-shipping_be.exe",
    "fortniteclient-win64-shipping_eac_eos.exe",
    "valorant-win64-shipping.exe",
    "league of legends.exe",
    "rocketleague.exe",
    "gta5.exe",
    "rdr2.exe",
    "destiny2.exe",
    "haloinfinite.exe",
    "forzahorizon5.exe",
    "cs2.exe",
    "eldenring.exe",
    "overwatch.exe",
    "cod.exe",
    "minecraft.windows.exe",
}

# Generic detection handles most games installed through the common PC stores.
GAME_PATH_HINTS = (
    "\\steamapps\\common\\",
    "\\epic games\\",
    "\\xboxgames\\",
    "\\windowsapps\\",
    "\\microsoft games\\",
    "\\riot games\\",
    "\\ea games\\",
    "\\ubisoft\\",
    "\\gog galaxy\\games\\",
    "\\battle.net\\",
    "\\fortnite\\",
)

# Launchers/updaters/helpers should not trigger gaming performance mode by themselves.
EXCLUDED_PROCESS_NAMES = {
    "steam.exe",
    "steamwebhelper.exe",
    "epicgameslauncher.exe",
    "epicwebhelper.exe",
    "riotclientservices.exe",
    "riotclientux.exe",
    "riotclientuxrender.exe",
    "battle.net.exe",
    "agent.exe",
    "eadesktop.exe",
    "eabackgroundservice.exe",
    "upc.exe",
    "ubisoftconnect.exe",
    "goggalaxy.exe",
    "gamingservices.exe",
    "gamingservicesnet.exe",
    "crashreportclient.exe",
    "unrealcefsubprocess.exe",
    "easyanticheat.exe",
    "easyanticheat_eos.exe",
    "beservice.exe",
}

HEAVY_MYLES_PATTERNS = (
    re.compile(r"quant_service\.mjs", re.I),
    re.compile(r"gmx_live\.mjs", re.I),
    re.compile(r"copy_trader_service\.mjs", re.I),
    re.compile(r"simulate_first_batch\.py", re.I),
    re.compile(r"job_worker\.py", re.I),
    re.compile(r"ollama_llama_server(?:\.exe)?", re.I),
)


def log(message: object) -> None:
    try:
        with LOG_FILE.open("a", encoding="utf-8", errors="replace") as handle:
            handle.write(f"[{dt.datetime.now().isoformat()}] {message}\n")
    except Exception:
        pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def process_rows() -> list[dict[str, Any]]:
    """Read processes with a tasklist fallback when psutil cannot see game paths."""
    rows: list[dict[str, Any]] = []
    try:
        import psutil  # type: ignore

        for process in psutil.process_iter(["pid", "name", "exe", "cmdline", "memory_info"]):
            try:
                info = process.info
                rss = int(getattr(info.get("memory_info"), "rss", 0) or 0)
                rows.append(
                    {
                        "pid": int(info.get("pid") or 0),
                        "name": str(info.get("name") or ""),
                        "exe": str(info.get("exe") or ""),
                        "cmdline": " ".join(info.get("cmdline") or []),
                        "rss": rss,
                    }
                )
            except Exception:
                pass
    except Exception:
        rows = []

    # Windows can hide executable paths from a non-elevated psutil process. Add
    # exact process names from tasklist so Fortnite is still detected through
    # the Xbox app / Gaming Services launch path.
    known_seen = {str(row.get("name") or "").lower() for row in rows}
    if not any(name in known_seen for name in KNOWN_GAME_NAMES) and not any(name.startswith("fortniteclient-win64-shipping") and name.endswith(".exe") for name in known_seen):
        try:
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                text=True,
                capture_output=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
            for raw in (result.stdout or "").splitlines():
                line = raw.strip().strip('"')
                if not line:
                    continue
                parts = [p.strip('"') for p in line.split('","')]
                if not parts:
                    continue
                try:
                    pid = int(parts[1]) if len(parts) > 1 else 0
                except Exception:
                    pid = 0
                name = parts[0]
                if str(name).lower() in known_seen:
                    continue
                rows.append({"pid": pid, "name": name, "exe": "", "cmdline": "", "rss": 0})
        except Exception:
            pass
    return rows


def detect_game() -> dict[str, Any] | None:
    for row in process_rows():
        name = str(row.get("name") or "").lower()
        exe = str(row.get("exe") or "").lower()
        command = str(row.get("cmdline") or "").lower()
        pid = int(row.get("pid") or 0)
        rss = int(row.get("rss") or 0)

        if name in KNOWN_GAME_NAMES or (name.startswith("fortniteclient-win64-shipping") and name.endswith(".exe")):
            return {"pid": pid, "name": row.get("name") or name, "exe": row.get("exe") or "", "reason": "known_game_process"}

        if not exe:
            continue
        if name in EXCLUDED_PROCESS_NAMES:
            continue
        if any(skip in name for skip in ("launcher", "updater", "helper", "crash", "anticheat", "anti-cheat")):
            continue

        candidate_path = exe or command
        if any(hint in candidate_path for hint in GAME_PATH_HINTS):
            # Require a meaningful resident footprint for generic path-based detection.
            # This avoids switching modes for tiny store helpers and update stubs.
            if rss >= 200 * 1024 * 1024:
                return {"pid": pid, "name": row.get("name") or name, "exe": row.get("exe") or "", "reason": "game_install_path"}
    return None


def config_light_mode() -> bool:
    return bool(load_json(CONFIG_FILE).get("light_mode", False))


def set_config_light_mode(enabled: bool, source: str) -> None:
    cfg = load_json(CONFIG_FILE)
    cfg["light_mode"] = bool(enabled)
    if source:
        cfg["light_mode_source"] = source
    else:
        cfg.pop("light_mode_source", None)
    write_json_atomic(CONFIG_FILE, cfg)


def kill_tree(pid: int) -> None:
    if pid <= 0 or pid == os.getpid():
        return
    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=12,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception:
        pass


def stop_heavy_myles_processes() -> list[int]:
    stopped: list[int] = []
    for row in process_rows():
        pid = int(row.get("pid") or 0)
        command = " ".join([str(row.get("exe") or ""), str(row.get("cmdline") or "")])
        if pid <= 0 or pid == os.getpid():
            continue
        if any(rx.search(command) for rx in HEAVY_MYLES_PATTERNS):
            kill_tree(pid)
            stopped.append(pid)
    return stopped


def unload_ollama_models() -> list[str]:
    ollama = shutil.which("ollama.exe") or shutil.which("ollama")
    if not ollama:
        return []
    try:
        result = subprocess.run(
            [ollama, "ps"],
            text=True,
            capture_output=True,
            timeout=10,
            creationflags=CREATE_NO_WINDOW,
        )
        models: list[str] = []
        lines = [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]
        for line in lines[1:]:
            name = line.split()[0] if line.split() else ""
            if name and name.upper() != "NAME":
                models.append(name)
        for model in models:
            subprocess.run(
                [ollama, "stop", model],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
                creationflags=CREATE_NO_WINDOW,
            )
        return models
    except Exception:
        return []


def state_payload(
    active: bool,
    game: dict[str, Any] | None,
    *,
    pre_game_light_mode: bool,
    entered_at: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "active": bool(active),
        "automatic": True,
        "detected": bool(game),
        "status": "active" if active else "watching",
        "process": (game or {}).get("name"),
        "pid": (game or {}).get("pid"),
        "exe": (game or {}).get("exe"),
        "reason": (game or {}).get("reason") or ("game_process_detected" if active else "no_game_process"),
        "pre_game_light_mode": bool(pre_game_light_mode),
        "entered_at": entered_at,
        "last_checked_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
        "watcher_pid": os.getpid(),
    }


def main() -> int:
    prior = load_json(STATE_FILE)
    was_active = bool(prior.get("active"))
    pre_game_light = bool(prior.get("pre_game_light_mode", False))
    entered_at = str(prior.get("entered_at") or "") or None
    last_state_write = 0.0
    last_model_unload = 0.0
    last_game_seen = time.monotonic() if was_active else 0.0
    last_game = None

    log("automatic game-mode watcher started")

    while True:
        try:
            detected_game = detect_game()
            now = time.monotonic()
            if detected_game is not None:
                last_game_seen = now
                last_game = detected_game
            within_exit_grace = bool(was_active and last_game_seen and (now - last_game_seen) < EXIT_GRACE_SECONDS)
            game = detected_game or (last_game if within_exit_grace else None)
            active = game is not None

            if active and not was_active:
                pre_game_light = config_light_mode()
                entered_at = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
                set_config_light_mode(True, "automatic_game_detection")
                stopped = stop_heavy_myles_processes()
                models = unload_ollama_models()
                last_model_unload = now
                log(
                    f"game detected: {game.get('name')} pid={game.get('pid')}; "
                    f"gaming mode ON; stopped heavy pids={stopped}; unloaded models={models}"
                )
                write_json_atomic(
                    STATE_FILE,
                    state_payload(True, game, pre_game_light_mode=pre_game_light, entered_at=entered_at),
                )
                last_state_write = now

            elif active:
                # Enforce the mode continuously. This prevents a stale launcher or
                # supervisor copy from bringing a heavy worker back during a match.
                if not config_light_mode():
                    set_config_light_mode(True, "automatic_game_detection")
                stopped = stop_heavy_myles_processes()
                if stopped:
                    log(f"gaming mode enforcement stopped heavy pids={stopped}")
                if now - last_model_unload >= STATE_HEARTBEAT_SECONDS:
                    models = unload_ollama_models()
                    last_model_unload = now
                    if models:
                        log(f"gaming mode enforcement unloaded Ollama models={models}")
                if now - last_state_write >= STATE_HEARTBEAT_SECONDS:
                    write_json_atomic(
                        STATE_FILE,
                        state_payload(True, game, pre_game_light_mode=pre_game_light, entered_at=entered_at),
                    )
                    last_state_write = now

            elif was_active:
                # Restore the owner's pre-game manual light-mode preference.
                set_config_light_mode(pre_game_light, "manual" if pre_game_light else "")
                log(f"game exited; gaming mode OFF; restored pre-game light_mode={pre_game_light}")
                entered_at = None
                write_json_atomic(
                    STATE_FILE,
                    state_payload(False, None, pre_game_light_mode=pre_game_light, entered_at=None),
                )
                last_state_write = now

            elif now - last_state_write >= STATE_HEARTBEAT_SECONDS:
                # Do not touch manually selected light mode while no game is running.
                write_json_atomic(
                    STATE_FILE,
                    state_payload(False, None, pre_game_light_mode=config_light_mode(), entered_at=None),
                )
                last_state_write = now

            was_active = active
        except Exception as exc:
            log(f"watcher error: {type(exc).__name__}: {exc}")

        time.sleep(CHECK_SECONDS)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        if WATCHER_MUTEX is not None and os.name == "nt":
            try:
                ctypes.windll.kernel32.ReleaseMutex(WATCHER_MUTEX)
            except Exception:
                pass
        if WATCHER_FILE_LOCK is not None and os.name == "nt":
            try:
                WATCHER_FILE_LOCK.seek(0)
                msvcrt.locking(WATCHER_FILE_LOCK.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception:
                pass
            try:
                WATCHER_FILE_LOCK.close()
            except Exception:
                pass
