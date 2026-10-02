from __future__ import annotations

"""Compatibility entry point for the canonical MYLES owner console."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "bin" / "myles_console_v074.py"

if not TARGET.exists():
    raise SystemExit(f"Canonical MYLES console is missing: {TARGET}")

runpy.run_path(str(TARGET), run_name="__main__")
