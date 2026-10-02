from __future__ import annotations

"""Compatibility entry point for the canonical MYLES runtime supervisor.

Command arguments are preserved in sys.argv for the canonical supervisor.
Importing this module does not start a runtime.
"""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "bin" / "runtime_supervisor_v074.py"


def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"Canonical MYLES supervisor is missing: {TARGET}")
    runpy.run_path(str(TARGET), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
