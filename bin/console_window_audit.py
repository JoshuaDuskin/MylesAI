"""Read the existing *local* supervisor console log and produce a PUBLIC-safe aggregate.

NEVER publish raw console audit entries: they contain local paths, CLI
arguments and potentially credentials. Output keys and values are allowlisted.
"""
from __future__ import annotations
import datetime as dt
import os
import re
from pathlib import Path

ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home()/"AppData"/"Local"))/"MylesAI"
AUDIT = ROOT/"logs"/"console_spawn_audit.log"
KNOWN = {"cmd.exe","powershell.exe","pwsh.exe","windowsterminal.exe",
         "wt.exe","conhost.exe","openconsole.exe","python.exe","uv.exe",
         "node.exe","git.exe"}
SOURCE_MATCHES = (
    ("update_child", ("remote_deploy_apply.ps1","update_tower.ps1")),
    ("update_poll", ("remote_deploy_agent.py",)),
    ("worker_tool", ("job_worker.py","run_powershell")),
    ("runtime_supervisor", ("runtime_supervisor_v074.py",)),
    ("runtime_guardian", ("ensure_myles_runtime.py",)),
    ("game_watcher", ("game_mode_watch.py",)),
    ("dashboard_bridge", ("dashboard_bridge.py",)),
    ("network_tunnel", ("cloudflared", "tailscale")),
)


def _category(line: str) -> str:
    value = line.lower()
    for name, markers in SOURCE_MATCHES:
        if any(word in value for word in markers):
            return name
    # Supervisor records a bounded ancestry chain. Classify known parents
    # without exporting their command lines, paths, or process identifiers.
    ancestry = re.search(r"\\bancestry=(.+)$", line, flags=re.IGNORECASE)
    if ancestry:
        parent_names = re.findall(
            r"<-\\s*\\d+:([a-zA-Z0-9._-]{1,40}):", ancestry.group(1))
        for name in parent_names:
            lower = name.lower()
            if lower in {"powershell.exe", "pwsh.exe", "cmd.exe"}:
                return "shell_parent"
            if lower in {"python.exe", "pythonw.exe", "node.exe", "git.exe"}:
                return "runtime_child"
    return "unclassified_myles_child"


def _tail(path: Path, limit=250_000) -> str:
    try:
        with path.open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size-limit))
            raw = handle.read(limit)
        if size > limit:
            raw = raw.partition(b"\n")[2]
        return raw.decode("utf-8",errors="replace")
    except OSError:
        return ""


def recent_summary(at: dt.datetime | None = None, *, path: Path | None = None) -> dict:
    """Only fixed labels/counts leave the tower; no commands/paths/PIDs."""
    at = at or dt.datetime.now()
    if at.tzinfo is not None:
        at = at.astimezone().replace(tzinfo=None)
    log = _tail(path or AUDIT)
    if not log:
        return {"status":"no_audit_log"}
    events = []
    for line in log.splitlines():
        if "myles_owned=True" not in line or "owner_console_excluded" in line:
            continue
        ts = re.match(r"^\[([0-9T:.\-+]+)\]",line)
        exe = re.search(r"\bname=([a-zA-Z0-9._-]{1,40})",line)
        hidden = re.search(r"\bhidden_windows=(\d{1,5})",line)
        if not (ts and exe and hidden):
            continue
        try:
            when = dt.datetime.fromisoformat(ts.group(1))
            if when.tzinfo is not None:
                when = when.astimezone().replace(tzinfo=None)
            age = (at-when).total_seconds()
        except (ValueError,OverflowError):
            continue
        if not 0 <= age <= 3600:
            continue
        executable=exe.group(1).lower()
        if executable not in KNOWN:
            continue
        events.append((when, executable, min(1000,int(hidden.group(1))), _category(line)))
    if not events:
        return {"status":"no_recent_myles_console_events"}
    events.sort(key=lambda x:x[0])
    last = events[-1]
    # Public-safe aggregates reveal which trusted source category is creating
    # visible console windows; never leak raw command lines or local paths.
    from collections import Counter
    visible_categories = Counter(x[3] for x in events if x[2] > 0)
    visible_executables = Counter(x[1] for x in events if x[2] > 0)
    return {"status":"events_observed",
            "myles_console_process_launches_last_hour":min(9999,len(events)),
            "visible_windows_suppressed_last_hour":min(9999,sum(x[2] for x in events)),
            "suppressed_source_counts":{k:min(9999,int(v))
                                        for k,v in sorted(visible_categories.items())},
            "suppressed_executable_counts":{k:min(9999,int(v))
                                            for k,v in sorted(visible_executables.items())},
            "last_executable_category":last[1],
            "last_source_category":last[3],
            "last_observed_at":last[0].isoformat(timespec="seconds")}
