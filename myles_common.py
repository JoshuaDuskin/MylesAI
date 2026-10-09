from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import ctypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

APP_VERSION = "10.2.1"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
WORKSPACES = ROOT / "workspaces"
UPDATES = ROOT / "self_updates"
BACKUPS = ROOT / "backups"
LOGS = ROOT / "logs"
SECRETS_PATH = DATA / "secrets.env"
for p in (DATA, WORKSPACES, UPDATES, BACKUPS, LOGS):
    p.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA / "myles.db"
CONFIG_PATH = DATA / "config.json"
PID_PATH = DATA / "core.pid"
RESTART_REQUEST = DATA / "restart.request"

DEFAULT_CONFIG = {
    "version": APP_VERSION,
    "model": "qwen3.5:9b",
    "ollama_url": "http://127.0.0.1:11434/api/chat",
    "core_host": "127.0.0.1",
    "core_port": 8766,
    "model_timeout_seconds": 180,
    "conversation_timeout_seconds": 120,
    "model_healthcheck_seconds": 30,
    "jev_enabled": False,
    "jev_url": "https://api.typesafe.ai/v1/systemone",
    "jev_model": "jev-latest",
    "jev_min_confidence": 0.60,
    "jev_timeout_seconds": 3,
    "tool_timeout_seconds": 1800,
    "max_agent_steps": 60,
    "max_conversation_steps": 6,
    "stall_no_heartbeat_seconds": 90,
    "stall_no_progress_seconds": 900,
    "max_recoveries": 8,
    "legacy_myles_root": "",
    "browser_headless": True,
    "browser_profile_dir": str(DATA / "browser_profile"),
    "telegram_enabled": False,
    "light_mode": False,
    "planner_retry_count": 3,
    "internal_retry_budget": 8,
    "capability_plugins_enabled": True,
    "pinetree_isolation_enabled": True,
    "blocked_project_terms": ["pinetree", "pinetreepayments", "pinetree-payments", "pinetree-payments.com", "app.pinetree-payments"],
}



def clean_model_text(value: str) -> str:
    """Remove model-private reasoning tags before anything can reach the owner."""
    text = str(value or "")
    # Qwen-family models can occasionally emit reasoning tags even when think=false.
    text = re.sub(r"(?is)<think>.*?</think>", "", text)
    text = re.sub(r"(?is)<analysis>.*?</analysis>", "", text)
    # Drop an unterminated private-reasoning tail rather than leaking it.
    text = re.sub(r"(?is)<think>.*$", "", text)
    text = re.sub(r"(?is)<analysis>.*$", "", text)
    return text.strip()

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_config() -> dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                cfg.update(saved)
        except Exception:
            pass
    cfg["version"] = APP_VERSION
    return cfg


def save_config(cfg: dict[str, Any]) -> None:
    cfg = dict(cfg)
    cfg["version"] = APP_VERSION
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    try:
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
    except OSError:
        return values
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_secrets() -> dict[str, str]:
    out = read_env_file(SECRETS_PATH)
    for key in ("MYLES_TELEGRAM_TOKEN", "MYLES_OWNER_ID", "MYLES_TELEGRAM_USER_ID", "TYPESAFE_API_KEY", "MYLES_JEV_API_KEY", "MYLES_JEV_URL"):
        value = os.environ.get(key, "").strip()
        if value:
            out[key] = value
    return out


def save_secrets(values: dict[str, str]) -> None:
    SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for key in ("MYLES_TELEGRAM_TOKEN", "MYLES_OWNER_ID", "TYPESAFE_API_KEY", "MYLES_JEV_API_KEY", "MYLES_JEV_URL"):
        value = str(values.get(key) or "").strip()
        if value:
            lines.append(f"{key}={value}")
    SECRETS_PATH.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    return con


def init_db() -> None:
    con = connect()
    try:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS jobs(
            id TEXT PRIMARY KEY,
            prompt TEXT NOT NULL,
            state TEXT NOT NULL,
            phase TEXT NOT NULL,
            created_at TEXT NOT NULL,
            started_at TEXT,
            updated_at TEXT NOT NULL,
            heartbeat_at TEXT,
            material_progress_at TEXT,
            runner_pid INTEGER,
            result TEXT,
            error TEXT,
            recovery_count INTEGER NOT NULL DEFAULT 0,
            workspace TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'desktop'
        );

        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            source TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            job_id TEXT
        );

        CREATE TABLE IF NOT EXISTS traces(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            ts TEXT NOT NULL,
            kind TEXT NOT NULL,
            tool TEXT,
            ok INTEGER,
            detail TEXT
        );

        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)
        con.commit()
    finally:
        con.close()


def add_message(source: str, role: str, content: str, job_id: str | None = None) -> int:
    con = connect()
    try:
        cur = con.execute(
            "INSERT INTO messages(ts,source,role,content,job_id) VALUES(?,?,?,?,?)",
            (now_iso(), source, role, content, job_id),
        )
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()


def recent_messages(limit: int = 40) -> list[dict[str, Any]]:
    con = connect()
    try:
        rows = con.execute(
            "SELECT id,ts,source,role,content,job_id FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        rows.reverse()
        return [dict(r) for r in rows]
    finally:
        con.close()


def messages_after(message_id: int, source: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    con = connect()
    try:
        if source:
            rows = con.execute(
                "SELECT id,ts,source,role,content,job_id FROM messages WHERE id>? AND source=? ORDER BY id LIMIT ?",
                (int(message_id), source, int(limit)),
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT id,ts,source,role,content,job_id FROM messages WHERE id>? ORDER BY id LIMIT ?",
                (int(message_id), int(limit)),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def latest_message_id() -> int:
    con = connect()
    try:
        row = con.execute("SELECT COALESCE(MAX(id),0) AS id FROM messages").fetchone()
        return int(row["id"] if row else 0)
    finally:
        con.close()


def history_for_model(limit: int = 24) -> list[dict[str, str]]:
    rows = recent_messages(limit)
    out: list[dict[str, str]] = []
    for r in rows:
        role = r["role"]
        if role not in ("user", "assistant"):
            continue
        out.append({"role": role, "content": str(r["content"])})
    return out


def trace(job_id: str, kind: str, detail: str = "", tool: str | None = None, ok: bool | None = None) -> None:
    con = connect()
    try:
        con.execute(
            "INSERT INTO traces(job_id,ts,kind,tool,ok,detail) VALUES(?,?,?,?,?,?)",
            (job_id, now_iso(), kind, tool, None if ok is None else int(bool(ok)), detail[:20000]),
        )
        con.commit()
    finally:
        con.close()


def set_job(job_id: str, **fields: Any) -> None:
    if not fields:
        return
    fields["updated_at"] = now_iso()
    cols = list(fields.keys())
    sql = "UPDATE jobs SET " + ", ".join(f"{c}=?" for c in cols) + " WHERE id=?"
    vals = [fields[c] for c in cols] + [job_id]
    con = connect()
    try:
        con.execute(sql, vals)
        con.commit()
    finally:
        con.close()


def get_job(job_id: str) -> dict[str, Any] | None:
    con = connect()
    try:
        row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None
    finally:
        con.close()


def list_jobs(limit: int = 30) -> list[dict[str, Any]]:
    con = connect()
    try:
        rows = con.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def active_job() -> dict[str, Any] | None:
    con = connect()
    try:
        row = con.execute(
            "SELECT * FROM jobs WHERE state IN ('running','recovering') ORDER BY created_at LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
    finally:
        con.close()


def next_pending_job() -> dict[str, Any] | None:
    con = connect()
    try:
        row = con.execute(
            "SELECT * FROM jobs WHERE state='pending' ORDER BY created_at LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
    finally:
        con.close()


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    if os.name != "nt":
        try:
            os.kill(int(pid), 0)
            return True
        except Exception:
            return False
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return False
        return code.value == 259
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def parse_ts(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).timestamp()
    except Exception:
        return None


def age_seconds(value: str | None) -> int | None:
    ts = parse_ts(value)
    if ts is None:
        return None
    return max(0, int(time.time() - ts))


def traces_for_job(job_id: str, limit: int = 30) -> list[dict[str, Any]]:
    con = connect()
    try:
        rows = con.execute(
            "SELECT * FROM traces WHERE job_id=? ORDER BY id DESC LIMIT ?", (job_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def job_truth(job: dict[str, Any]) -> dict[str, Any]:
    cfg = load_config()
    pid = job.get("runner_pid")
    live = pid_alive(pid)
    hb_age = age_seconds(job.get("heartbeat_at"))
    progress_age = age_seconds(job.get("material_progress_at"))
    state = job.get("state")
    truth_state = state
    reasons: list[str] = []

    if state == "running":
        if not live:
            truth_state = "stalled"
            reasons.append("worker process is not alive")
        elif hb_age is None or hb_age > int(cfg["stall_no_heartbeat_seconds"]):
            truth_state = "stalled"
            reasons.append(f"heartbeat age is {hb_age}s")
        else:
            started_age = age_seconds(job.get("started_at")) or 0
            limit = int(cfg["stall_no_progress_seconds"])
            if started_age > limit and (progress_age is None or progress_age > limit):
                truth_state = "stalled"
                reasons.append(f"no verified executor progress for >{limit}s")

    return {
        **job,
        "live_worker": live,
        "heartbeat_age_seconds": hb_age,
        "progress_age_seconds": progress_age,
        "truth_state": truth_state,
        "stall_reasons": reasons,
    }


def set_setting(key: str, value: str) -> None:
    con = connect()
    try:
        con.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        con.commit()
    finally:
        con.close()


def get_setting(key: str, default: str = "") -> str:
    con = connect()
    try:
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default
    finally:
        con.close()
