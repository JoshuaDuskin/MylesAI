from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from myles_common import connect, now_iso


UNTRUSTED_TOOLS = {"web_fetch", "web_search", "browser_automation", "rea_analyze_javascript_application"}


@dataclass(frozen=True)
class Provenance:
    source: str
    untrusted_content: bool = False


@dataclass(frozen=True)
class EvidenceRecord:
    job_id: str
    tool: str
    attempt: int
    ok: bool
    outcome: str
    arguments: dict[str, Any] = field(default_factory=dict)
    result: str = ""
    provenance: Provenance = field(default_factory=lambda: Provenance("local_tool"))
    limitations: tuple[str, ...] = ()


def _safe_json(value: Any, limit: int) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        text = json.dumps(str(value), ensure_ascii=False)
    return text[:limit]


def provenance_for_tool(tool: str) -> Provenance:
    name = str(tool or "")
    return Provenance(source=name or "unknown_tool", untrusted_content=name in UNTRUSTED_TOOLS)


def record_tool_evidence(record: EvidenceRecord) -> int:
    """Persist a bounded, typed tool result independently of model narration."""
    result = str(record.result or "")[:20000]
    arguments_json = _safe_json(record.arguments, 12000)
    provenance_json = _safe_json(asdict(record.provenance), 2000)
    limitations_json = _safe_json(list(record.limitations), 4000)
    digest = hashlib.sha256(
        (record.tool + "\0" + arguments_json + "\0" + result).encode("utf-8", errors="replace")
    ).hexdigest()
    con = connect()
    try:
        cur = con.execute(
            "INSERT INTO evidence(job_id,ts,tool,attempt,ok,outcome,arguments_json,result_text,"
            "provenance_json,limitations_json,digest) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                record.job_id, now_iso(), record.tool, max(1, int(record.attempt)),
                int(bool(record.ok)), record.outcome, arguments_json, result,
                provenance_json, limitations_json, digest,
            ),
        )
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()


def record_unknown(job_id: str, question: str, evidence_id: int | None = None) -> int:
    con = connect()
    try:
        cur = con.execute(
            "INSERT INTO unknowns(job_id,ts,question,status,evidence_id) VALUES(?,?,?,?,?)",
            (str(job_id), now_iso(), str(question)[:4000], "open", evidence_id),
        )
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()


def evidence_for_job(job_id: str, limit: int = 100) -> list[dict[str, Any]]:
    con = connect()
    try:
        rows = con.execute(
            "SELECT * FROM evidence WHERE job_id=? ORDER BY id DESC LIMIT ?",
            (str(job_id), max(1, min(int(limit), 500))),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()
