from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any

from myles_common import connect, now_iso


@dataclass(frozen=True)
class AgentSession:
    id: str
    job_id: str
    goal: str
    model: str
    status: str
    revision: int


@dataclass(frozen=True)
class PlanStep:
    id: str
    title: str
    status: str = "pending"
    evidence_ids: tuple[int, ...] = ()
    unknowns: tuple[int, ...] = ()


@dataclass(frozen=True)
class ToolCallHandle:
    id: str
    job_id: str
    tool: str
    attempt: int
    fingerprint: str


def _bounded(value: Any, limit: int) -> str:
    try:
        out = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        out = str(value)
    return out[:limit]


def ensure_session(job_id: str, goal: str, model: str) -> AgentSession:
    session_id = "sess_" + hashlib.sha256(str(job_id).encode()).hexdigest()[:24]
    con = connect()
    try:
        con.execute(
            "INSERT OR IGNORE INTO agent_sessions(id,job_id,goal,model,status,revision,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (session_id, str(job_id), str(goal)[:8000], str(model)[:200], "active", 0, now_iso(), now_iso()),
        )
        con.execute(
            "UPDATE agent_sessions SET goal=?,model=?,status='active',updated_at=? WHERE id=?",
            (str(goal)[:8000], str(model)[:200], now_iso(), session_id),
        )
        con.commit()
        row = con.execute("SELECT * FROM agent_sessions WHERE id=?", (session_id,)).fetchone()
        return AgentSession(session_id, str(row["job_id"]), str(row["goal"]), str(row["model"]), str(row["status"]), int(row["revision"]))
    finally:
        con.close()


def _normalise_steps(steps: Any) -> list[dict[str, Any]]:
    if not isinstance(steps, list):
        return []
    out: list[dict[str, Any]] = []
    for index, raw in enumerate(steps[:20], 1):
        if isinstance(raw, str):
            title = raw.strip()
            status = "pending"
        elif isinstance(raw, dict):
            title = str(raw.get("title") or raw.get("step") or "").strip()
            status = str(raw.get("status") or "pending").lower()
        else:
            continue
        if not title:
            continue
        if status not in {"pending", "active", "completed", "blocked", "cancelled"}:
            status = "pending"
        out.append({"id": f"step_{index}", "title": title[:500], "status": status})
    return out


def update_plan(job_id: str, action: str, steps: Any = None, current_step: int | None = None) -> dict[str, Any]:
    action = str(action or "read").lower()
    con = connect()
    try:
        row = con.execute("SELECT * FROM agent_plans WHERE job_id=?", (str(job_id),)).fetchone()
        current = json.loads(str(row["steps_json"])) if row else []
        if not isinstance(current, list):
            current = []
        if action in {"create", "replace"}:
            current = _normalise_steps(steps)
        elif action == "advance" and current:
            index = max(0, min(len(current) - 1, int(current_step or 1) - 1))
            for i, item in enumerate(current):
                if item.get("status") == "active":
                    item["status"] = "completed" if i < index else item.get("status", "pending")
            current[index]["status"] = "active"
        elif action == "complete" and current:
            for item in current:
                item["status"] = "completed"
        state = "active"
        if current and all(item.get("status") == "completed" for item in current):
            state = "completed"
        elif any(item.get("status") == "blocked" for item in current):
            state = "blocked"
        revision = int(row["revision"] if row else 0) + (1 if action != "read" else 0)
        if row:
            if action != "read":
                con.execute(
                    "UPDATE agent_plans SET steps_json=?,state=?,revision=?,updated_at=? WHERE job_id=?",
                    (_bounded(current, 16000), state, revision, now_iso(), str(job_id)),
                )
        else:
            con.execute(
                "INSERT INTO agent_plans(job_id,steps_json,state,revision,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (str(job_id), _bounded(current, 16000), state, revision, now_iso(), now_iso()),
            )
        con.commit()
        return {"job_id": str(job_id), "state": state, "revision": revision, "steps": current}
    finally:
        con.close()


def start_tool_call(job_id: str, tool: str, args: dict[str, Any], attempt: int) -> ToolCallHandle:
    call_id = "call_" + uuid.uuid4().hex
    args_json = _bounded(args or {}, 12000)
    fingerprint = hashlib.sha256((str(tool) + "\0" + args_json).encode()).hexdigest()
    con = connect()
    try:
        con.execute(
            "INSERT INTO tool_calls(id,job_id,tool,attempt,state,args_json,fingerprint,started_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (call_id, str(job_id), str(tool), max(1, int(attempt)), "running", args_json, fingerprint, now_iso(), now_iso()),
        )
        con.commit()
    finally:
        con.close()
    return ToolCallHandle(call_id, str(job_id), str(tool), max(1, int(attempt)), fingerprint)


def finish_tool_call(handle: ToolCallHandle, *, ok: bool, outcome: str, result: str, evidence_id: int | None = None) -> None:
    con = connect()
    try:
        con.execute(
            "UPDATE tool_calls SET state=?,ok=?,outcome=?,result_text=?,evidence_id=?,finished_at=?,updated_at=? WHERE id=?",
            ("succeeded" if ok else "failed", int(bool(ok)), str(outcome)[:100], str(result or "")[:20000], evidence_id, now_iso(), now_iso(), handle.id),
        )
        con.commit()
    finally:
        con.close()


def cancel_open_tool_calls(job_ids: list[str]) -> None:
    ids = [str(value) for value in job_ids if str(value)]
    if not ids:
        return
    placeholders = ",".join("?" for _ in ids)
    con = connect()
    try:
        con.execute(
            f"UPDATE tool_calls SET state='cancelled',outcome='cancelled',updated_at=? "
            f"WHERE job_id IN ({placeholders}) AND state='running'",
            [now_iso(), *ids],
        )
        con.commit()
    finally:
        con.close()


def agent_context_block(job_id: str, max_chars: int = 18000) -> str:
    con = connect()
    try:
        session = con.execute("SELECT * FROM agent_sessions WHERE job_id=?", (str(job_id),)).fetchone()
        plan = con.execute("SELECT * FROM agent_plans WHERE job_id=?", (str(job_id),)).fetchone()
        calls = con.execute(
            "SELECT id,tool,attempt,state,ok,outcome,evidence_id FROM tool_calls WHERE job_id=? ORDER BY started_at DESC LIMIT 16",
            (str(job_id),),
        ).fetchall()
        unknowns = con.execute(
            "SELECT id,question,status,evidence_id FROM unknowns WHERE job_id=? ORDER BY id DESC LIMIT 12",
            (str(job_id),),
        ).fetchall()
    finally:
        con.close()
    payload = {
        "session": dict(session) if session else None,
        "plan": {
            "state": str(plan["state"]),
            "revision": int(plan["revision"]),
            "steps": json.loads(str(plan["steps_json"])),
        } if plan else None,
        "recent_tool_calls": [dict(row) for row in calls],
        "open_unknowns": [dict(row) for row in unknowns if str(row["status"]) == "open"],
    }
    return "AGENT SESSION STATE (authoritative runtime metadata; do not invent beyond it):\n" + _bounded(payload, max_chars)


def compact_messages(messages: list[dict[str, Any]], max_chars: int = 70000) -> list[dict[str, Any]]:
    """Keep the system contract and newest working context inside a hard budget."""
    if not messages:
        return []
    budget = max(16000, int(max_chars))
    system = messages[:1]
    tail = messages[1:]
    # Keep recent turns, but preserve a tool result's role/call shape and image.
    selected: list[dict[str, Any]] = []
    used = len(json.dumps(system, ensure_ascii=False, default=str))
    for raw in reversed(tail):
        item = dict(raw)
        if isinstance(item.get("content"), str) and len(item["content"]) > 12000:
            item["content"] = item["content"][:12000] + "\n[older content bounded]"
        # Local screenshots are bounded separately by the vision image-byte
        # budget; counting base64 characters as text would drop the entire
        # user request and recent agent context before sending Ollama images.
        # Keep the exact encoded image unchanged while using a fixed estimate
        # for text-context compaction accounting.
        meter = dict(item)
        if "images" in meter:
            images = meter.pop("images")
            meter["_image_count"] = len(images) if isinstance(images, list) else 0
        size = len(json.dumps(meter, ensure_ascii=False, default=str)) + 1200 * int(meter.get("_image_count", 0))
        if selected and used + size > budget:
            break
        selected.append(item)
        used += size
    selected.reverse()
    omitted = max(0, len(tail) - len(selected))
    if omitted:
        marker = {"role": "user", "content": f"[context manager retained the newest turns; omitted={omitted}]"}
        return system + [marker] + selected
    return system + selected
