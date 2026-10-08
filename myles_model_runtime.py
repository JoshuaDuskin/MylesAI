from __future__ import annotations

"""Resilient local model runtime and optional Jev decision coprocessor.

Myles keeps conversation, memory, task text, files, and credentials local.
Jev receives only an abstract decision envelope and is never the language model.
"""

import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ModelRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelHealth:
    available: bool
    model: str = ""
    endpoint: str = ""
    recovered: bool = False
    error_kind: str = ""
    detail: str = ""


_LAST_HEALTH = ModelHealth(False, error_kind="not_checked", detail="Model runtime has not been checked.")
_LAST_CHECK_EPOCH = 0.0


def _json_request(url: str, payload: dict[str, Any] | None = None, *, timeout: int = 15, headers: dict[str, str] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request_headers = {"Accept": "application/json"}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    request_headers.update(headers or {})
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET", headers=request_headers)
    with urllib.request.urlopen(req, timeout=max(2, int(timeout))) as response:
        return json.loads(response.read().decode("utf-8"))


def _ollama_base(cfg: dict[str, Any]) -> str:
    configured = str(cfg.get("ollama_url") or "http://127.0.0.1:11434/api/chat").strip()
    parsed = urllib.parse.urlparse(configured)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "http://127.0.0.1:11434"
    return f"{parsed.scheme}://{parsed.netloc}"


def _ollama_chat_url(cfg: dict[str, Any]) -> str:
    return _ollama_base(cfg) + "/api/chat"


def _ollama_candidates() -> list[Path]:
    rows: list[Path] = []
    found = shutil.which("ollama.exe") or shutil.which("ollama")
    if found:
        rows.append(Path(found))
    local = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles")
    for raw in (
        Path(local) / "Programs" / "Ollama" / "ollama.exe" if local else None,
        Path(program_files) / "Ollama" / "ollama.exe" if program_files else None,
    ):
        if raw and raw not in rows:
            rows.append(raw)
    return [path for path in rows if path.is_file()]


def _installed_models(cfg: dict[str, Any]) -> list[str]:
    data = _json_request(_ollama_base(cfg) + "/api/tags", timeout=5)
    rows = data.get("models") if isinstance(data, dict) else []
    return [
        str(row.get("name") or row.get("model") or "").strip()
        for row in rows if isinstance(row, dict) and str(row.get("name") or row.get("model") or "").strip()
    ]


def _model_rank(name: str) -> tuple[int, int, str]:
    low = name.lower()
    if any(term in low for term in ("embed", "nomic", "clip")):
        return (-1000, 0, low)
    family = 0
    if "qwen" in low:
        family = 50
    elif "llama" in low:
        family = 40
    elif "mistral" in low or "mixtral" in low:
        family = 30
    elif "gemma" in low:
        family = 20
    size = 0
    match = re.search(r"(\d+(?:\.\d+)?)b\b", low)
    if match:
        size = min(100, int(float(match.group(1)) * 2))
    return (family + size, size, low)


def select_model(cfg: dict[str, Any], installed: list[str]) -> str:
    configured = str(cfg.get("model") or "").strip()
    aliases = {name.split(":", 1)[0]: name for name in installed}
    if configured in installed:
        return configured
    if configured and configured.split(":", 1)[0] in aliases:
        return aliases[configured.split(":", 1)[0]]
    ranked = sorted(installed, key=_model_rank, reverse=True)
    return ranked[0] if ranked and _model_rank(ranked[0])[0] > -1000 else ""


def ensure_model_runtime(cfg: dict[str, Any], *, force: bool = False) -> ModelHealth:
    global _LAST_HEALTH, _LAST_CHECK_EPOCH
    now = time.time()
    if not force and now - _LAST_CHECK_EPOCH < 10 and _LAST_HEALTH.available:
        return _LAST_HEALTH
    _LAST_CHECK_EPOCH = now
    endpoint = _ollama_base(cfg)
    try:
        installed = _installed_models(cfg)
        selected = select_model(cfg, installed)
        if not selected:
            _LAST_HEALTH = ModelHealth(False, endpoint=endpoint, error_kind="no_chat_model", detail="Ollama is online but no compatible chat model is installed.")
            return _LAST_HEALTH
        _LAST_HEALTH = ModelHealth(True, model=selected, endpoint=endpoint)
        return _LAST_HEALTH
    except Exception as first_error:
        if os.name != "nt":
            _LAST_HEALTH = ModelHealth(False, endpoint=endpoint, error_kind="ollama_unreachable", detail=f"{type(first_error).__name__}: {first_error}")
            return _LAST_HEALTH

    executable = next(iter(_ollama_candidates()), None)
    if not executable:
        _LAST_HEALTH = ModelHealth(False, endpoint=endpoint, error_kind="ollama_missing", detail="Ollama executable was not found.")
        return _LAST_HEALTH
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        subprocess.Popen(
            [str(executable), "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                installed = _installed_models(cfg)
                selected = select_model(cfg, installed)
                if selected:
                    _LAST_HEALTH = ModelHealth(True, model=selected, endpoint=endpoint, recovered=True)
                    return _LAST_HEALTH
            except Exception:
                time.sleep(0.75)
    except Exception as exc:
        _LAST_HEALTH = ModelHealth(False, endpoint=endpoint, error_kind="ollama_start_failed", detail=f"{type(exc).__name__}: {exc}")
        return _LAST_HEALTH
    _LAST_HEALTH = ModelHealth(False, endpoint=endpoint, error_kind="ollama_start_timeout", detail="Ollama did not become ready within 20 seconds.")
    return _LAST_HEALTH


def model_chat(
    cfg: dict[str, Any],
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    json_mode: bool = False,
    temperature: float = 0.2,
    timeout: int | None = None,
) -> dict[str, Any]:
    health = ensure_model_runtime(cfg)
    if not health.available:
        raise ModelRuntimeError(f"{health.error_kind}: {health.detail}")

    request_timeout = timeout or int(cfg.get("conversation_timeout_seconds", 120))
    last_error: BaseException | None = None
    for attempt in range(2):
        payload: dict[str, Any] = {
            "model": health.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {"temperature": float(temperature)},
            "keep_alive": "0" if bool(cfg.get("light_mode")) else "10m",
        }
        if tools:
            payload["tools"] = tools
        if json_mode:
            payload["format"] = "json"
        try:
            return _json_request(
                _ollama_chat_url(cfg),
                payload,
                timeout=request_timeout,
            )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:800]
            last_error = ModelRuntimeError(f"ollama_http_{exc.code}: {detail}")
            # A client/schema failure will not be repaired by restarting Ollama.
            if exc.code < 500 or attempt:
                raise last_error from exc
        except Exception as exc:
            last_error = exc
            if attempt:
                break

        # A refused/reset connection is common after sleep or an Ollama update.
        # Recover the service, select the model that is actually installed, and
        # replay this exact owner turn once instead of throwing the stale error.
        health = ensure_model_runtime(cfg, force=True)
        if not health.available:
            raise ModelRuntimeError(f"{health.error_kind}: {health.detail}") from last_error

    raise ModelRuntimeError(
        f"ollama_chat_failed_after_recovery: {type(last_error).__name__}: {last_error}"
    ) from last_error


def model_health_dict(cfg: dict[str, Any], *, refresh: bool = False) -> dict[str, Any]:
    health = ensure_model_runtime(cfg, force=refresh)
    return {
        "available": health.available,
        "model": health.model,
        "endpoint": health.endpoint,
        "recovered": health.recovered,
        "error_kind": health.error_kind,
        "detail": health.detail[:500],
    }


def fallback_conversation(raw: str, status: str = "", *, model_error: str = "") -> str:
    text = re.sub(r"\s+", " ", str(raw or "").strip())
    low = text.lower()
    if re.fullmatch(r"(yo+|hey+|hi+|hello+|sup|what'?s up)[.!? ]*", low):
        return "Hey — I’m here. What’s up?"
    if re.fullmatch(r"(thanks|thank you|appreciate it)[.! ]*", low):
        return "You got it."
    if re.search(r"\bhow are you\b", low):
        return "I’m here and ready. What’s up?"
    if re.search(r"\bwhat (?:are you|you) doing\b|\bstatus\b", low) and status:
        return status
    if "?" in text:
        return "I couldn’t answer that cleanly just now. Try me again in a second."
    return "I heard you. I couldn’t process that cleanly just now, so I didn’t turn it into a task."


def abstract_decision_state(raw: str, proposed_intent: str, *, has_active: bool, has_recent_cancelled: bool) -> dict[str, Any]:
    """Return a privacy-minimized decision envelope; never include owner text."""
    low = str(raw or "").lower()
    return {
        "schema_version": 1,
        "proposed_intent": proposed_intent,
        "has_active_task": bool(has_active),
        "has_recent_cancelled_task": bool(has_recent_cancelled),
        "is_question": "?" in raw,
        "word_count_bucket": min(8, max(0, len(raw.split()) // 4)),
        "has_explicit_stop_phrase": bool(re.search(r"\b(stop|cancel|abort|drop it)\b", low)),
        "has_explicit_action_verb": bool(re.search(r"\b(open|launch|start|build|create|install|download|fix|change|update|test|run)\b", low)),
        "has_negative_stop": bool(re.search(r"\b(don't|do not|never)\s+(stop|cancel)\b", low)),
    }


def verify_with_jev(
    raw: str,
    proposed_intent: str,
    *,
    has_active: bool,
    has_recent_cancelled: bool,
    cfg: dict[str, Any],
    secrets: dict[str, str],
) -> tuple[str, dict[str, Any]]:
    """Optionally verify a local route with TypeSafe Jev using abstract state only.

    This uses the official System One Choice contract. Jev never receives the
    owner's message, memory, files, credentials, or tool output. It is a
    fail-open decision coprocessor: any missing key, timeout, schema error, or
    low-confidence answer preserves the local Qwen/rules decision.
    """
    enabled = bool(cfg.get("jev_enabled"))
    url = str(
        cfg.get("jev_url")
        or secrets.get("MYLES_JEV_URL")
        or "https://api.typesafe.ai/v1/systemone"
    ).strip()
    api_key = str(
        secrets.get("TYPESAFE_API_KEY")
        or secrets.get("MYLES_JEV_API_KEY")
        or ""
    ).strip()
    model = str(cfg.get("jev_model") or "jev-latest").strip()
    minimum_confidence = max(0.0, min(1.0, float(cfg.get("jev_min_confidence", 0.60))))
    meta = {
        "enabled": enabled,
        "configured": bool(url and api_key),
        "used": False,
        "decision": "local",
        "provider": "typesafe_jev",
        "privacy_mode": "abstract_state_only",
    }
    if not enabled or not url or not api_key:
        return proposed_intent, meta

    envelope = abstract_decision_state(
        raw,
        proposed_intent,
        has_active=has_active,
        has_recent_cancelled=has_recent_cancelled,
    )
    allowed = {
        "accept", "chat", "lookup", "local_lookup", "feedback", "start",
        "modify", "status", "stop", "replace", "resume", "light_on", "light_off",
    }
    criteria = {
        "accept": "The proposed local intent is already the safest accurate route.",
        "chat": "Ordinary conversation or a question; do not create a background task.",
        "lookup": "A factual lookup that does not mutate owner state.",
        "local_lookup": "A read-only lookup of local state.",
        "feedback": "Behavior correction or preference feedback, not a new job.",
        "start": "A clear new action request when no existing task should be modified.",
        "modify": "A clear change to the active or most recent owner-requested task.",
        "status": "A request for status, progress, or explanation only.",
        "stop": "An explicit request to stop or cancel active work.",
        "replace": "An explicit request to replace active work with a different task.",
        "resume": "An explicit request to continue previously stopped work.",
        "light_on": "An explicit request to turn a light on.",
        "light_off": "An explicit request to turn a light off.",
    }
    payload = {
        "model": model,
        "state": envelope,
        "questions": {
            "intent": {
                "type": "choice",
                "instructions": (
                    "Choose the safest owner-intent route from abstract state only. "
                    "Prefer chat for casual conversation; never infer a destructive "
                    "or mutating action without an explicit action signal."
                ),
                "criteria": criteria,
            }
        },
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = _json_request(
            url,
            payload,
            timeout=int(cfg.get("jev_timeout_seconds", 3)),
            headers=headers,
        )
        answer = (
            (response.get("answers") or {}).get("intent")
            or (response.get("choices") or {}).get("intent")
            or {}
        )
        decision = str(answer.get("choice") or "").strip().lower()
        confidence = float(answer.get("confidence", 0.0) or 0.0)
        if decision not in allowed:
            raise ValueError("invalid Jev Choice answer")
        if confidence < minimum_confidence:
            meta.update({
                "decision": "local_low_confidence",
                "confidence": confidence,
                "model": str(response.get("model") or model),
            })
            return proposed_intent, meta
        meta.update({
            "used": True,
            "decision": decision,
            "confidence": confidence,
            "model": str(response.get("model") or model),
        })
        return (proposed_intent if decision == "accept" else decision), meta
    except Exception as exc:
        meta.update({
            "error": f"{type(exc).__name__}: {exc}"[:500],
            "decision": "local_fallback",
        })
        return proposed_intent, meta
