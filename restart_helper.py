"""Retired compatibility entry point for the old direct core restarter.

The old helper could become a second Myles owner and open an extra Python
process. Verified restart and rollback now belong exclusively to
``runtime_supervisor.py``. This shim never starts the core; it only leaves a
clear message for old shortcuts or manually-invoked callers.
"""

from __future__ import annotations


def main() -> int:
    print(
        "restart_helper.py is retired; start or stop Myles with "
        "START_MYLESAI.cmd and STOP_MYLES.cmd."
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
