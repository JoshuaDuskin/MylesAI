"""Cheap shared game-active gate. No process scanning on the hot request path."""
from __future__ import annotations

import json
from pathlib import Path
from myles_common import DATA


def _read(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def game_is_active() -> bool:
    state = _read(DATA / "game_mode_state.json")
    if state.get("active") is True:
        return True
    cfg = _read(DATA / "config.json")
    return bool(cfg.get("light_mode") is True
                and cfg.get("light_mode_source") == "automatic_game_detection")
