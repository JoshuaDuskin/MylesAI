from __future__ import annotations

import importlib.util
import json
import sys
import threading
import time
from pathlib import Path
from types import ModuleType
from typing import Any

from myles_common import ROOT, now_iso, load_config

CAPABILITY_DIR = ROOT / "capabilities"
CAPABILITY_DIR.mkdir(parents=True, exist_ok=True)
CAPABILITY_LOG = ROOT / "logs" / "capabilities.log"

# Modules are cached by file mtime so provider sessions/module state persist across
# tool calls and background ticks. v9.0.1 re-imported every plugin on every discovery.
_MODULE_CACHE: dict[str, tuple[int, ModuleType]] = {}
_CACHE_LOCK = threading.RLock()

_LAST_TICK: dict[str, float] = {}
_STARTUP_DONE: set[str] = set()
_BG_RUNNING: set[str] = set()
_BG_LOCK = threading.RLock()


def _log(text: str) -> None:
    try:
        CAPABILITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with CAPABILITY_LOG.open("a", encoding="utf-8") as f:
            f.write(f"[{now_iso()}] {text}\n")
    except Exception:
        pass


def _enabled() -> bool:
    return bool(load_config().get("capability_plugins_enabled", True))


def _load_module(path: Path) -> ModuleType:
    """Load a capability once and reload only when its source file changes."""
    key = str(path.resolve()).lower()
    mtime = int(path.stat().st_mtime_ns)

    with _CACHE_LOCK:
        cached = _MODULE_CACHE.get(key)
        if cached and cached[0] == mtime:
            return cached[1]

        # Stable module name per source path. Put it into sys.modules so provider
        # libraries that rely on module identity/session state behave normally.
        safe = "".join(c if c.isalnum() else "_" for c in path.stem)
        name = "myles_cap_" + safe
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load capability module {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _MODULE_CACHE[key] = (mtime, module)
        return module


def _descriptor(path: Path, mod: ModuleType) -> dict[str, Any]:
    defs = getattr(mod, "TOOL_DEFS", [])
    handlers = getattr(mod, "TOOLS", {})
    if not isinstance(defs, list) or not isinstance(handlers, dict):
        defs, handlers = [], {}

    names: list[str] = []
    valid_defs: list[dict[str, Any]] = []
    for d in defs:
        try:
            name = str(d["function"]["name"])
        except Exception:
            continue
        if not name or not callable(handlers.get(name)):
            continue
        names.append(name)
        valid_defs.append(d)

    tick = getattr(mod, "BACKGROUND_TICK", None)
    startup = getattr(mod, "STARTUP", None)
    interval = int(getattr(mod, "BACKGROUND_INTERVAL_SECONDS", 0) or 0)

    return {
        "module": mod,
        "definitions": valid_defs,
        "handlers": handlers,
        "tools": names,
        "description": str(getattr(mod, "DESCRIPTION", "") or ""),
        "auth": str(getattr(mod, "AUTH_KIND", "none") or "none"),
        "background": callable(tick) and interval > 0,
        "background_interval_seconds": interval,
        "startup_hook": callable(startup),
        "source": str(path),
    }


def discover_capabilities() -> dict[str, dict[str, Any]]:
    if not _enabled():
        return {}

    catalog: dict[str, dict[str, Any]] = {}
    for path in sorted(CAPABILITY_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            mod = _load_module(path)
            catalog[path.stem] = _descriptor(path, mod)
        except Exception as exc:
            catalog[path.stem] = {
                "error": f"{type(exc).__name__}: {exc}",
                "definitions": [],
                "handlers": {},
                "tools": [],
                "description": "",
                "auth": "unknown",
                "background": False,
                "background_interval_seconds": 0,
                "startup_hook": False,
                "source": str(path),
            }
    return catalog


def tool_definitions() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for cap_name, item in discover_capabilities().items():
        for d in item.get("definitions") or []:
            try:
                name = str(d["function"]["name"])
            except Exception:
                continue
            if name in seen:
                _log(f"duplicate tool name ignored: {name} from capability {cap_name}")
                continue
            seen.add(name)
            out.append(d)
    return out


def execute(tool_name: str, job_id: str, args: dict[str, Any]) -> str | None:
    matches: list[tuple[str, Any]] = []
    for cap_name, item in discover_capabilities().items():
        fn = (item.get("handlers") or {}).get(tool_name)
        if callable(fn):
            matches.append((cap_name, fn))

    if not matches:
        return None
    if len(matches) > 1:
        names = ", ".join(name for name, _ in matches)
        return f"TOOL_ERROR: capability tool name {tool_name!r} is duplicated by: {names}"

    cap_name, fn = matches[0]
    try:
        return str(fn(job_id=job_id, **args))
    except Exception as exc:
        _log(f"{cap_name}.{tool_name} failed: {type(exc).__name__}: {exc}")
        return f"TOOL_ERROR: capability {cap_name}.{tool_name} failed: {type(exc).__name__}: {exc}"


def run_startup_hooks() -> None:
    """Run each plugin startup hook once per core lifetime.

    Core startup invokes this function on a daemon thread, so slow provider setup
    cannot prevent the localhost API/Telegram runtime from coming online.
    """
    for name, item in discover_capabilities().items():
        if name in _STARTUP_DONE:
            continue
        fn = getattr(item.get("module"), "STARTUP", None)
        if not callable(fn):
            _STARTUP_DONE.add(name)
            continue
        try:
            fn()
            _STARTUP_DONE.add(name)
            _log(f"{name} startup hook completed")
        except Exception as exc:
            # A provider startup failure is isolated to that capability.
            _log(f"{name} startup hook failed: {type(exc).__name__}: {exc}")


def _background_runner(name: str, fn: Any) -> None:
    try:
        fn()
    except Exception as exc:
        _log(f"{name} background tick failed: {type(exc).__name__}: {exc}")
    finally:
        with _BG_LOCK:
            _BG_RUNNING.discard(name)


def run_background_ticks() -> None:
    """Schedule due provider background work without blocking the job monitor.

    A Ring/network/health provider call may take seconds or time out. v9.0.1 ran
    those calls inline on the same thread that dispatches/recover jobs. Here each
    due tick runs independently and only one tick per capability may run at once.
    """
    if not _enabled():
        return

    now = time.time()
    for name, item in discover_capabilities().items():
        if not item.get("background"):
            continue
        interval = max(1, int(item.get("background_interval_seconds") or 0))
        if now - _LAST_TICK.get(name, 0.0) < interval:
            continue

        fn = getattr(item.get("module"), "BACKGROUND_TICK", None)
        if not callable(fn):
            continue

        with _BG_LOCK:
            if name in _BG_RUNNING:
                continue
            _BG_RUNNING.add(name)
            _LAST_TICK[name] = now

        threading.Thread(
            target=_background_runner,
            args=(name, fn),
            name=f"myles-cap-{name}",
            daemon=True,
        ).start()


def status_json() -> str:
    catalog = discover_capabilities()
    safe: dict[str, Any] = {}
    for name, item in catalog.items():
        with _BG_LOCK:
            running = name in _BG_RUNNING
        safe[name] = {
            "tools": list(item.get("tools") or []),
            "description": item.get("description") or "",
            "auth": item.get("auth") or "none",
            "background": bool(item.get("background")),
            "background_interval_seconds": int(item.get("background_interval_seconds") or 0),
            "background_running": running,
            "startup_hook": bool(item.get("startup_hook")),
            "startup_completed": name in _STARTUP_DONE,
            "error": item.get("error"),
        }
    return json.dumps(safe, indent=2)
