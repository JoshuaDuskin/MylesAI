"""Bounded, owner-authorized read-only tools for a live Myles conversation."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from myles_common import ROOT, load_config
from myles_agent_contracts import ensure_session, start_tool_call, finish_tool_call
from myles_evidence import EvidenceRecord, Provenance, record_tool_evidence, record_unknown


ASSISTED_TOOLS = [
    {"type": "function", "function": {
        "name": "inspect_local_file",
        "description": "Read an explicitly requested local text file now. Read only, bounded, protected project/secrets blocked. Report evidence, not an imagined file.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "inspect_local_directory",
        "description": "List an explicitly requested folder now; read-only, nonrecursive, max 80 items.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "inspect_open_windows",
        "description": "Inspect visible Windows app/window titles on the tower now, without clicking or changing anything.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
]
TOOL_NAMES = frozenset(x["function"]["name"] for x in ASSISTED_TOOLS)
READ_PATTERN = re.compile(
    r"\b(read|inspect|view|show|list|look at|look inside|what(?:'s| is| are| files| windows)|"
    r"which files|which windows|open windows|folder contents|directory contents|"
    r"check the contents|check what(?:'s| is))\b", re.I)
TARGET_PATTERN = re.compile(
    r"\b(files?|folders?|directories|directory|windows?|apps?|applications?|"
    r"logs?|scripts?|configs?|documents?|contents?|source code)\b", re.I)
MUTATION_PATTERN = re.compile(
    r"\b(write|edit|modify|delete|remove|wipe|clear|change|replace|install|execute|"
    r"run|restart|stop|start|build|create|fix|repair|deploy|publish|download|"
    r"send|close|kill|launch)\b", re.I)
SENSITIVE_PATTERN = re.compile(
    r"(^|[/\\._-])(\.env|\.ssh|secrets?|passwords?|credentials?|private[-_]?keys?|"
    r"api[-_]?keys?|tokens?|auth|wallet|browser[-_]?profile|hosts\.yml)([/\\._-]|$)", re.I)
SENSITIVE_LINE = re.compile(
    r"(?im)^(\s*(?:export\s+)?[\x22\x27]?[A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PRIVATE_KEY|"
    r"API_KEY|CLIENT_SECRET)[A-Z0-9_]*[\x22\x27]?\s*[:=]\s*).+$")
TEXT_EXTENSIONS = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".json",
                   ".md", ".txt", ".log", ".yaml", ".yml", ".toml", ".ini",
                   ".csv", ".html", ".css", ".ps1", ".cmd", ".bat", ".xml"}


def read_only_intent(text: str) -> bool:
    raw = str(text or "")
    return bool(READ_PATTERN.search(raw) and TARGET_PATTERN.search(raw)
                and not MUTATION_PATTERN.search(raw))


def _path(value: Any) -> Path | None:
    raw = str(value or "").strip().strip('"')
    if not raw or len(raw) > 1024:
        return None
    try:
        p = Path(os.path.expandvars(os.path.expanduser(raw)))
        return (p if p.is_absolute() else ROOT / p).resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return None


def _safe(path: Path, as_file: bool) -> bool:
    lower = str(path).lower()
    excluded = tuple(str(x).lower() for x in load_config().get(
        "blocked_project_terms", ["pinetree", "pinetreepayments"]))
    if any(s and s in lower for s in (*excluded, "pinetree")):
        return False
    if SENSITIVE_PATTERN.search(str(path)):
        return False
    return not as_file or path.suffix.lower() in TEXT_EXTENSIONS


def authorized(name: str, request: str, args: dict[str, Any]) -> bool:
    if name not in TOOL_NAMES or not isinstance(args, dict) or not read_only_intent(request):
        return False
    raw = str(request).lower()
    if name == "inspect_open_windows":
        return bool(re.search(r"\b(windows?|apps?|applications?)\b", raw))
    if name == "inspect_local_directory":
        if not re.search(r"\b(files?|folders?|directories|directory|contents?)\b", raw):
            return False
    elif not re.search(r"\b(files?|logs?|scripts?|configs?|documents?|contents?|code)\b", raw):
        return False
    p = _path(args.get("path"))
    if p is None or not _safe(p, as_file=name == "inspect_local_file"):
        return False
    # Repository paths or specifically named owner locations only.
    if p == ROOT or ROOT in p.parents:
        return True
    return len(p.name) >= 3 and p.name.lower() in raw


def _observe(name: str, args: dict[str, Any], turn_id: str) -> tuple[str, bool]:
    if name == "inspect_open_windows":
        from myles_tools import desktop_windows
        out = str(desktop_windows(turn_id))
        return out[:12000], not out.startswith("TOOL_ERROR:")
    p = _path(args.get("path"))
    if p is None or not _safe(p, as_file=name == "inspect_local_file"):
        return "TOOL_REFUSED: protected or unsupported path.", False
    if name == "inspect_local_file":
        if not p.is_file():
            return f"TOOL_ERROR: file not found: {p}", False
        size = p.stat().st_size
        if size > 2_000_000:
            return f"TOOL_ERROR: file exceeds read limit: {p}", False
        text = p.read_text(encoding="utf-8", errors="replace")[:12000]
        text = SENSITIVE_LINE.sub(r"\1[REDACTED]", text)
        return f"FILE_OBSERVED={p} BYTES={size}\nCONTENT:\n{text}", True
    if not p.is_dir():
        return f"TOOL_ERROR: directory not found: {p}", False
    items = []
    for item in p.iterdir():
        if len(items) >= 80:
            items.append("...TRUNCATED...")
            break
        if _safe(item, as_file=False):
            items.append(("DIR " if item.is_dir() else "FILE ") + item.name)
    return f"DIRECTORY_OBSERVED={p}\n" + "\n".join(items), True


def execute(name: str, args: dict[str, Any], turn_id: str, request: str) -> str:
    """Each observation gets a durable tool lifecycle and evidence ID."""
    if not authorized(name, request, args):
        return "TOOL_REFUSED: no owner authorization for this inspection target."
    try:
        ensure_session(turn_id, request, str(load_config().get("model") or "unknown"))
        handle = start_tool_call(turn_id, name, args, 1)
    except Exception as exc:
        return f"TOOL_ERROR: could not establish evidence session: {type(exc).__name__}"
    ok, eid = False, None
    result = "TOOL_ERROR: observation never executed."
    try:
        result, ok = _observe(name, args, turn_id)
    except (OSError, ValueError, UnicodeError) as exc:
        result = f"TOOL_ERROR: {type(exc).__name__}: {exc}"
    except Exception as exc:
        result = f"TOOL_ERROR: inspection failed: {type(exc).__name__}"
    try:
        eid = record_tool_evidence(EvidenceRecord(
            job_id=turn_id, tool=name, attempt=1, ok=ok,
            outcome="observed" if ok else "not_verified",
            arguments=args, result=result,
            provenance=Provenance(source=name, authority="runtime-observation" if name == "inspect_open_windows" else "local-observation", untrusted_content=True),
            limitations=("Observation only; no system changes made.",),
        ))
        if not ok:
            record_unknown(turn_id, f"Inspection by {name} was not verified.", eid)
    except Exception:
        ok, result = False, "TOOL_ERROR: unable to retain observation evidence."
    finally:
        try:
            finish_tool_call(handle, ok=ok, outcome="observed" if ok else "not_verified",
                             result=result, evidence_id=eid)
        except Exception:
            ok, result = False, "TOOL_ERROR: lifecycle finalization failed."
    return f"EVIDENCE_ID={eid if eid is not None else 'none'}\n{result}"
