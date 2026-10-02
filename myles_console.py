from __future__ import annotations

"""Compatibility entry point for the canonical MYLES owner console.

Importing this module is side-effect free; execution happens only when invoked
as a script. This keeps self-tests and tooling from accidentally opening a
second interactive console.
"""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "bin" / "myles_console_v074.py"


def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"Canonical MYLES console is missing: {TARGET}")
    runpy.run_path(str(TARGET), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
