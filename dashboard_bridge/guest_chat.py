"""Separate chat-only guest identity for one invited household member.

Never grants the Myles owner token, shared chat, jobs, desktop, filesystem,
wallet, dashboard configuration or trading control. Explicit owner invite,
one-time short code, revocable hashed guest credential, private guest history.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import secrets
import sys
import threading
import time
import uuid
from pathlib import Path

ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "MylesAI"
DATA = ROOT / "data"
AUTH = DATA / "guest_chat_auth.json"
HISTORY = DATA / "guest_chat_history.json"
LOCK = threading.RLock()
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
MAX_TEXT = 2500
MAX_HISTORY = 60


def read(path: Path) -> dict:
    try:
        if path.stat().st_size > 200_000:
            return {}
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def digest(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def make_invite() -> dict:
    """Must be called ONLY after owner-token authorization at HTTP bridge."""
    with LOCK:
        code = "".join(secrets.choice(ALPHABET) for _ in range(8))
        old = read(AUTH)
        # An invitation replaces an earlier unused code, not an existing chat.
        save(AUTH, {**old, "invite_hash": digest(code),
                   "invite_expires": int(time.time()) + 1200})
        return {"ok": True, "code": code, "expires_in_minutes": 20,
                "role": "guest_chat_only"}


def exchange(code: str) -> dict | None:
    with LOCK:
        obj = read(AUTH)
        candidate = str(code or "").strip().upper()
        if (len(candidate) != 8 or not obj.get("invite_hash")
                or int(obj.get("invite_expires") or 0) < time.time()
                or not hmac.compare_digest(digest(candidate), str(obj.get("invite_hash")))):
            return None
        token = secrets.token_urlsafe(36)
        obj.pop("invite_hash", None)
        obj.pop("invite_expires", None)
        obj["guest_token_hash"] = digest(token)
        obj["paired_at"] = int(time.time())
        save(AUTH, obj)
        return {"ok": True, "token": token, "role": "guest_chat_only"}


def is_guest(token: str) -> bool:
    candidate = str(token or "")
    if len(candidate) < 32 or len(candidate) > 256:
        return False
    expected = str(read(AUTH).get("guest_token_hash") or "")
    return bool(expected and hmac.compare_digest(digest(candidate), expected))


def revoke() -> dict:
    """Called only by owner endpoint; blocks existing token and unused invites."""
    with LOCK:
        obj = read(AUTH)
        for key in ("guest_token_hash", "invite_hash", "invite_expires", "paired_at"):
            obj.pop(key, None)
        save(AUTH, obj)
        return {"ok": True, "guest_revoked": True}


def messages() -> dict:
    with LOCK:
        rows = read(HISTORY).get("messages") or []
        if not isinstance(rows, list):
            rows = []
        return {"ok": True, "role": "guest_chat_only",
                "messages": rows[-MAX_HISTORY:]}


def send(text: str) -> tuple[int, dict]:
    prompt = str(text or "").strip()
    if not prompt or len(prompt) > MAX_TEXT:
        return 400, {"ok": False, "error": "Message must be 1–2500 characters"}
    # No owner's conversations, owner task status or tools are ever assembled
    # into the guest context. The model is a purely text-only service.
    from datetime import datetime, timezone
    from myles_game_guard import game_is_active
    if game_is_active():
        return 503, {"ok": False, "error": "Conversation is paused while the tower is gaming"}
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    with LOCK:
        existing = messages()["messages"]
        context = [{"role": "system", "content":
            "You are Myles, a helpful general conversation assistant for a "
            "household guest. You can chat, answer questions, explain ideas and "
            "help write things. You have NO permission or tools to operate the "
            "owner's computer, applications, jobs, private files, other chats, "
            "financial or trading accounts, settings, memory, or dashboard. "
            "Do not claim to have accessed or changed any of them. If asked "
            "to perform actions on the tower or disclose owner's information, "
            "say that guest access is chat-only."}]
        for item in existing[-18:]:
            role = item.get("role")
            if role in {"user", "assistant"}:
                context.append({"role": role, "content": str(item.get("content") or "")[:MAX_TEXT]})
        context.append({"role": "user", "content": prompt})
        try:
            from myles_common import load_config
            from myles_model_runtime import model_chat
            from myles_conversation import unfinished_model_reply
            result = model_chat(load_config(), context, tools=None,
                                temperature=0.3, timeout=70)
            reply = str((result.get("message") or {}).get("content") or "").strip()
            if unfinished_model_reply(result, reply):
                return 503, {"ok": False, "error": "The local model response was incomplete; please retry"}
            reply = reply[:MAX_TEXT]
        except Exception:
            return 503, {"ok": False, "error": "The local conversation model is unavailable"}
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        updated = (existing + [
            {"role": "user", "content": prompt, "at": stamp},
            {"role": "assistant", "content": reply, "at": stamp},
        ])[-MAX_HISTORY:]
        save(HISTORY, {"messages": updated})
        return 200, {"ok": True, "role": "guest_chat_only",
                     "reply": reply, "messages": updated}
