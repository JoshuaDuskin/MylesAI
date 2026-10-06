from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from myles_common import (
    APP_VERSION, ROOT, WORKSPACES, PID_PATH, RESTART_REQUEST,
    init_db, load_config, save_config, load_secrets, connect, now_iso, add_message,
    recent_messages, messages_after, latest_message_id, history_for_model,
    get_job, list_jobs, next_pending_job, active_job,
    set_job, trace, job_truth, set_setting, get_setting, clean_model_text,
)

import myles_capabilities as capabilities
import myles_tools as tools
import myles_quick as quick
from myles_runtime_v9 import (
    deterministic_control, explicit_stop_requested, explicit_resume_requested,
    looks_like_status_request, likely_action_request, strong_action_request,
    natural_question,
    followup_action_request, refers_to_previous_result, execution_promise_text,
    behavior_feedback_request, self_capability_request, compact_task_signature,
)
from myles_model_runtime import (
    fallback_conversation, model_chat, model_health_dict, verify_with_jev,
)

CORE_LOG = ROOT / "logs" / "core.log"
WORKER_LOG = ROOT / "logs" / "worker.log"
STOP = threading.Event()
CHAT_BUSY = threading.Event()

CONVERSATION_TOOLS = [
    {"type":"function","function":{"name":"start_background_job","description":"Start real work on the owner's Windows tower in the background. Use this when the owner is asking Myles to actually do, fix, build, inspect, install, download, change, test, automate, or investigate something on the computer or a project. Do not use this for ordinary conversation or questions that only need an answer.","parameters":{"type":"object","properties":{"prompt":{"type":"string","description":"A complete standalone description of the work to perform."}},"required":["prompt"]}}},
    {"type":"function","function":{"name":"get_current_work","description":"Read the truthful current Myles task status. Use when the owner asks what Myles is doing, whether something finished, progress, or current work.","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"stop_current_work","description":"Stop the current owner task. Use when the owner clearly asks Myles to stop, cancel, abort, or drop the work currently running.","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"launch_fortnite","description":"Open Fortnite on the owner Windows tower through the installed Epic Games Launcher.","parameters":{"type":"object","properties":{},"additionalProperties":False}}},
    {"type":"function","function":{"name":"set_light_mode","description":"Turn light/gaming mode on or off. Only use this when the owner clearly asks Myles to reduce or resume heavy background work while gaming or doing something latency-sensitive. Do not infer it from a casual mention of a game.","parameters":{"type":"object","properties":{"enabled":{"type":"boolean"}},"required":["enabled"]}}},
]

CONVERSATION_SYSTEM = """
CANONICAL PROJECT RESOLUTION:
- The owner's one Myles production dashboard is JoshuaDuskin/MylesAI.
- The Quant source repository is JoshuaDuskin/MylesAI.
- Live runtime/chat/trading telemetry comes from the authenticated tower bridge, not a GitHub status repository.
- Never create another Myles dashboard/control-center/progress/runtime-status/live-status repository.
- Before proposing or creating any repository, check whether the project already exists and reuse its canonical repository.
- A request to improve/fix/update "the dashboard" always means JoshuaDuskin/MylesAI unless the owner explicitly names another non-Myles project.
# MYLES_CANONICAL_REPOSITORY_RESOLUTION_v4

IDENTITY / VOICE:
- You are Myles. Speak about yourself to the owner in first person: I, me, my, I'm, I'll, I can.
- Never say "Myles is working" or "Myles can do that" when Myles means you. Say "I'm working" / "I can do that".
- Third-person "Myles" is only for a quoted UI/log label or a separate artifact/process whose proper name is Myles.
# MYLES_FIRST_PERSON_OWNER_RULE_v3


IDENTITY / VOICE:
- You are Myles. When speaking to the owner about yourself, always use first person: I, me, my, I'm, I'll, I can, I am working.
- Do not refer to yourself in third person as "Myles" (for example, "Myles is working", "Myles can do that", or "Myles has a task") unless you are quoting a UI/log label or explicitly referring to a separate artifact/process whose proper name is Myles.
- If the owner asks what you are doing, say "I'm working on..." rather than "Myles is working on...".

# MYLES_FIRST_PERSON_OWNER_RULE_v2
You are Myles, the owner's local personal AI on his Windows tower.

The owner talks to you normally. Treat ordinary language as ordinary conversation. Do not require slash commands, special prefixes, task IDs, or canned command syntax.

You have four conversation-level tools:
- start_background_job: launch real computer/project work without blocking the conversation.
- get_current_work: truthfully inspect current work/progress.
- stop_current_work: cancel the current owner task.
- set_light_mode: hold heavy queued work when the owner explicitly wants lightweight/gaming behavior.

IMPORTANT BEHAVIOR:
- If the owner is chatting, asking a normal question, venting, making a comment, or giving context, answer naturally. Do NOT create a task just because he sent a message.
- A question is not an instruction. "What are you doing?", "Why did that happen?", "Is there anything you need?", and "Can you explain that?" stay conversational unless the owner explicitly asks you to perform an action.
- Never use a word like "fix", "check", "look", or "report" in a quoted question or complaint as proof that the owner requested work.
- If the owner asks you to actually do something on the tower or in a project, call start_background_job.
- If the owner asks you to add/install/improve Myles's own tools or capabilities, that is a Myles self-capability task. It must use a fresh task/workspace, never the previous project's workspace. After the tool returns, acknowledge naturally. If the tool says RUNNING, you may say the work has started. If it says QUEUED, say it is queued, not running. Do not dump internal tracking IDs unless they are useful or he asks.
- If he asks what you are doing or whether something is finished, call get_current_work instead of guessing from memory.
- If he asks you to stop the current work, call stop_current_work. If he says to stop one thing and do another, you may call stop_current_work and then start_background_job in the same turn.
- A casual statement like 'I'm playing Fortnite' is context, not a command. Only change light mode if the owner clearly wants work reduced/paused.
- Be conversational, warm, direct, and natural. Routine replies should usually be one or two compact paragraphs. Do not sound like a robotic task manager, dump internal prompts/JSON/job IDs, or narrate routing unless the owner asks.
- Never claim computer work was completed unless the background worker produced verified evidence.
"""


ROUTER_SYSTEM = """You are the invisible semantic controller for Myles, a local personal AI.
Classify the owner's LATEST message using the recent conversation context. Do not answer the owner.
Return ONLY one JSON object with keys: intent, task.

Valid intent values:
- chat: ordinary conversation, timeless questions that can be answered without external lookup, comments, venting, context.
- lookup: a quick read-only public-information lookup that should be answered now, not turned into a durable background job. Examples: weather, a current public fact, a simple web search.
- local_lookup: a read-only lookup of a local Myles artifact, file, folder, report, result, or prior task output. Use this for natural questions such as where a report/result was put. Do not answer with generic runtime status.
- feedback: the owner is correcting how Myles behaved or explaining that something should have been handled differently. Feedback itself is not a new computer task.
- start: owner wants Myles to actually do/build/fix/change/install/download/test/inspect/investigate something on the tower or a project.
- modify: owner wants to revise, redesign, improve, fix, or add to a result/task already discussed or just completed. Reconstruct a standalone task from context.
- status: owner asks what Myles is doing, progress, whether work finished, or current task state.
- stop: owner explicitly asks to stop/cancel/drop the current work and does not request replacement work.
- replace: owner explicitly asks to stop/cancel the current work AND start different work.
- resume: owner says not to stop, keep going, continue, resume, or otherwise clearly wants a recently-cancelled task continued.
- light_on: owner explicitly asks to reduce/pause heavy background work for gaming/latency.
- light_off: owner explicitly asks to resume normal/heavy work.

For start, modify, or replace, task MUST be a complete standalone instruction reconstructed from context.
Examples: 'Yes please build it' after discussion of a web dashboard is start, and task must describe that dashboard, not merely 'build it'. If Myles just asked whether to check current work status and the owner says 'yes', classify as status.
Do not classify a casual mention of gaming as light_on.
CRITICAL: Weather/current-info/search questions are lookup, not start, unless the owner explicitly asks to build/change/install/automate something.
CRITICAL: A correction such as "that should have been a quick search, not a whole job" is feedback, not modify/start.
CRITICAL: "Add the tools to your kit so you can look it up" means improve Myles itself. It is start, never modify of the previous artifact.
CRITICAL: Never classify a question such as "you trying that again?", "are you still working?", or "what happened?" as stop.
CRITICAL: Never classify negative-stop language such as "don't stop" or "do not stop" as stop.
CRITICAL: Questions and conversational corrections never become start/modify just because they contain an action word. Only an explicit imperative or direct request to perform work may create a job.
Never claim anything executed; this controller only classifies.
"""

SPEAK_SYSTEM = CONVERSATION_SYSTEM + """
IDENTITY OVERRIDE: Speak about yourself in first person. Say "I'm working on it", never "Myles is working on it" when referring to yourself.
# MYLES_FIRST_PERSON_SPEAK_RULE_v3


IDENTITY OVERRIDE: Speak about yourself in first person. Say 'I am working on it' / 'I can do that'; never say 'Myles is working on it' / 'Myles can do that' when Myles means you.
# MYLES_FIRST_PERSON_SPEAK_RULE_v2


A deterministic controller has already interpreted the latest owner message.
You will be given CONTROLLER_RESULT. Treat it as ground truth.
If it says a task is RUNNING, you may say it started. If it says QUEUED, say queued.
If it says there is no task, do not imply one exists.
Never invent progress, files, URLs, hosting, completion, or tool use that are not present in CONTROLLER_RESULT. PineTree is permanently isolated from Myles; never create or resume PineTree work. If LIVE_EXECUTION_STATE is present, never contradict it. Casual conversation can stay casual, but do not say there are no active tasks when the live state says work is running or queued.
Do not output <think>, <analysis>, or private reasoning.
"""


def log(text: str) -> None:
    line = f"[{now_iso()}] {text}"
    try:
        with CORE_LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def create_job(
    prompt: str,
    source: str,
    *,
    record_user: bool = True,
    reuse_workspace: str | Path | None = None,
) -> dict[str, Any]:

    # MYLES_CONTINUOUS_DASHBOARD_OWNER_LOCK_v3
    if str(source or "").strip().lower() == "continuous":
        hard_rule = (
            "\n\nOWNER-LOCKED REPOSITORIES (MANDATORY): Continuous/self-improvement jobs may not mutate remote GitHub at all. "
            "Do not publish GitHub Pages, push Git commits, create/rename/archive/delete repositories, or use browser automation to change GitHub. "
            "JoshuaDuskin/MylesAI is the one canonical owner dashboard and is read-only to continuous work. "
            "JoshuaDuskin/MylesAI is Quant source and is also read-only to continuous work. "
            "Legacy dashboard repositories must never be revived or replaced. Live runtime/status data belongs on the authenticated tower bridge, not GitHub commits."
        )
        if "OWNER-LOCKED REPOSITORIES (MANDATORY)" not in str(prompt or ""):
            prompt = str(prompt or "") + hard_rule
    # MYLES_CONTINUOUS_DASHBOARD_OWNER_LOCK_v2
    if str(source or "").strip().lower() == "continuous":
        dashboard_lock = (
            "\n\nOWNER-LOCKED DASHBOARD (MANDATORY): "
            "JoshuaDuskin/MylesAI is production owner UI. "
            "During continuous/self-improvement work you may inspect its health/status only. "
            "Do NOT redesign, edit, write, commit, push, publish, force-update, replace, clone-and-push, "
            "or otherwise mutate that repository or its GitHub Pages production UI. "
            "Do NOT create a replacement dashboard repository. "
            "Dashboard changes require an explicit owner-requested dashboard task outside continuous improvement. "
            "Runtime status must flow through the live tower bridge, not Git commits. "
            "Treat any failure to modify the dashboard as the intended owner lock, not as an error to bypass."
        )
        if "OWNER-LOCKED DASHBOARD (MANDATORY)" not in str(prompt or ""):
            prompt = str(prompt or "") + dashboard_lock
    job_id = "M83-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    if reuse_workspace:
        workspace = Path(reuse_workspace).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
    else:
        workspace = WORKSPACES / job_id
        workspace.mkdir(parents=True, exist_ok=True)
    now = now_iso()
    con = connect()
    try:
        con.execute(
            """INSERT INTO jobs(id,prompt,state,phase,created_at,updated_at,recovery_count,workspace,source)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (job_id, prompt, "pending", "queued", now, now, 0, str(workspace), source),
        )
        con.commit()
    finally:
        con.close()
    if record_user:
        add_message(source, "user", prompt, job_id)
    trace(job_id, "job.created", f"source={source}")
    if reuse_workspace:
        trace(job_id, "job.workspace_reused", f"workspace={workspace}")
    return get_job(job_id) or {}


def _terminate_pid(pid: int | None) -> None:
    if not pid:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception:
            pass
    else:
        try:
            os.kill(int(pid), 9)
        except Exception:
            pass


def start_job(job: dict[str, Any]) -> None:
    job_id = job["id"]
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    WORKER_LOG.parent.mkdir(parents=True, exist_ok=True)
    out = open(WORKER_LOG, "a", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "job_worker.py"), job_id],
        cwd=str(ROOT), stdout=out, stderr=out, creationflags=flags,
    )
    set_job(job_id, state="running", phase="launching", runner_pid=proc.pid, heartbeat_at=now_iso())
    trace(job_id, "worker.launched", f"pid={proc.pid}")


def _owner_job_summary(job: dict[str, Any]) -> str:
    """Translate internal job prompts into concise owner-facing language."""
    source = str(job.get("source") or "").lower()
    if source == "continuous":
        return "a continuous-improvement cycle focused on making Myles faster, more reliable, and easier to use"
    prompt = re.sub(r"\s+", " ", str(job.get("prompt") or "")).strip()
    if "Owner's new instruction:" in prompt:
        prompt = prompt.split("Owner's new instruction:", 1)[1].strip()
    return _human_task_label(prompt, 220)


def status_text() -> str:
    active = active_job()
    cfg = load_config()
    light = bool(cfg.get("light_mode"))
    jobs = list_jobs(30)
    pending = [j for j in jobs if j.get("state") == "pending"]
    if not active:
        if pending:
            nxt = pending[0]
            extra = " Heavy queued work is being held because light mode is on." if light else ""
            return (
                f"No active worker. {len(pending)} owner task(s) queued.\n"
                f"Next queued task: {_owner_job_summary(nxt)}"
                + extra
            )
        blocked = next((j for j in jobs if j.get("state") == "blocked_auth"), None)
        if blocked:
            return (
                "I am waiting on one owner authentication step before I can continue.\n"
                f"Blocked task: {_owner_job_summary(blocked)}\n"
                f"Phase: {blocked.get('phase')}"
            )
        latest_terminal = next((j for j in jobs if j.get("state") in {"failed", "completed", "cancelled"}), None)
        tail = ""
        if latest_terminal and latest_terminal.get("state") == "failed":
            tail = f" Last task failed: {str(latest_terminal.get('error') or 'unknown error')[:500]}"
        elif latest_terminal and latest_terminal.get("state") == "completed":
            tail = f" Last completed task: {_owner_job_summary(latest_terminal)}"
        continuous_tail = ""
        if _continuous_enabled():
            continuous_tail = " Continuous improvement is enabled and will start the next cycle automatically."
        return "I'm online. No owner task is currently running." + tail + continuous_tail + (" Light mode is on." if light else "")
    t = job_truth(active)
    if str(active.get("source") or "").lower() == "continuous":
        return (
            "I'm currently working on a continuous-improvement cycle focused on making Myles "
            "faster, more reliable, and easier to use. It's running normally, and no owner task "
            "is queued behind it."
        )
    reasons = "; ".join(t.get("stall_reasons") or [])
    return (
        f"Current work: {_owner_job_summary(active)}\n"
        f"State: {t['truth_state']}\n"
        f"Phase: {t.get('phase')}\n"
        f"Worker alive: {t.get('live_worker')}\n"
        f"Heartbeat age: {t.get('heartbeat_age_seconds')}s\n"
        f"Verified progress age: {t.get('progress_age_seconds')}s\n"
        f"Queued behind it: {len(pending)}\n"
        + (f"Stall evidence: {reasons}\n" if reasons else "")
        + ("Light mode is on.\n" if light else "")
    ).strip()


def cancel_job(job_id: str) -> str:
    job = get_job(job_id)
    if not job:
        return "That task was not found."
    _terminate_pid(job.get("runner_pid"))
    set_job(job_id, state="cancelled", phase="cancelled", runner_pid=None, heartbeat_at=now_iso())
    trace(job_id, "job.cancelled", "Cancelled by owner control.")
    return "Stopped the current task."


def recover_job(job_id: str, reason: str = "Owner requested recovery") -> str:
    cfg = load_config()
    job = get_job(job_id)
    if not job:
        return "That task was not found."
    _terminate_pid(job.get("runner_pid"))
    count = int(job.get("recovery_count") or 0) + 1
    if count > int(cfg["max_recoveries"]):
        set_job(job_id, state="failed", phase="recovery_limit", runner_pid=None, error="Recovery limit reached.")
        return "That task reached its automatic recovery limit."
    set_job(job_id, state="pending", phase="recovering", runner_pid=None, heartbeat_at=None, started_at=None, recovery_count=count, error=None)
    trace(job_id, "job.recovery.requested", reason)
    return f"Retrying the same task from its existing workspace (attempt {count})."


def _conversation_call(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """One resilient local-model call with installed-model discovery and recovery."""
    return model_chat(
        load_config(),
        messages,
        tools=CONVERSATION_TOOLS,
        temperature=0.35,
    )


def _router_call(raw: str) -> dict[str, Any]:
    """Classify an ambiguous owner message without making router failure fatal."""
    cfg = load_config()
    history = history_for_model(14)
    if history and history[-1].get("role") == "user" and str(history[-1].get("content") or "").strip() == str(raw or "").strip():
        history = history[:-1]

    last_error = ""
    for attempt in range(1, 3):
        messages = [{"role": "system", "content": ROUTER_SYSTEM}] + history + [
            {"role": "user", "content": str(raw or "").strip()}
        ]
        if attempt > 1:
            messages.append({
                "role": "system",
                "content": "Return exactly one JSON object with keys intent and task. No prose or Markdown.",
            })
        try:
            data = model_chat(cfg, messages, json_mode=True, temperature=0.0)
            content = clean_model_text(str((data.get("message") or {}).get("content") or ""))
            route = json.loads(content)
            if not isinstance(route, dict):
                raise ValueError("router result was not an object")
            intent = str(route.get("intent") or "chat").strip().lower()
            allowed = {"chat", "lookup", "local_lookup", "feedback", "start", "modify", "status", "stop", "replace", "resume", "light_on", "light_off", "continuous_on", "continuous_off"}
            if intent not in allowed:
                intent = "chat"
            return {"intent": intent, "task": str(route.get("task") or "").strip()}
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            log(f"semantic router retry attempt={attempt} error={last_error}")

    log(f"semantic router unavailable; safe chat fallback: {last_error}")
    return {"intent": "chat", "task": "", "_router_error": last_error}


PINETREE_BLOCK_TERMS = ("pinetree", "pinetreepayments", "pinetree-payments", "pinetree-payments.com", "app.pinetree-payments")

def _pinetree_clause_is_exclusion(clause: str) -> bool:
    low = str(clause or "").lower()
    positions = [low.find(term) for term in PINETREE_BLOCK_TERMS if term in low]
    if not positions:
        return True
    pos = min(p for p in positions if p >= 0)
    before = low[max(0, pos - 260):pos]
    after = low[pos:pos + 220]
    negative_before = (
        "do not", "don't", "never", "must not", "may not", "cannot", "can't",
        "without", "avoid", "avoiding", "exclude", "excluding", "block",
        "blocking", "forbid", "forbidding", "isolate", "isolating", "no "
    )
    negative_after = (
        "forbidden", "blocked", "isolated", "off-limits", "off limits",
        "excluded", "never allowed", "must not be accessed"
    )
    return any(marker in before for marker in negative_before) or any(
        marker in after for marker in negative_after
    )

def _is_pinetree_task(text: str) -> bool:
    low = str(text or "").lower()
    if not any(term in low for term in PINETREE_BLOCK_TERMS):
        return False
    normalized = low.replace("\r", "\n")
    for sep in (".", "!", "?", ";"):
        normalized = normalized.replace(sep, "\n")
    for clause in (part.strip() for part in normalized.split("\n") if part.strip()):
        if not any(term in clause for term in PINETREE_BLOCK_TERMS):
            continue
        if _pinetree_clause_is_exclusion(clause):
            continue
        return True
    return False

def _pinetree_task_refusal() -> str:
    return "REFUSED_PINETREE: PineTree is permanently isolated from Myles. No PineTree task was created and no PineTree resource was touched."


def _latest_reusable_job() -> dict[str, Any] | None:
    """Most recent owner job whose existing workspace can be refined."""
    jobs = list_jobs(50)
    # A follow-up while work is active should stay attached to that same workspace
    # even if the first artifact has not been written yet.
    for job in jobs:
        state = str(job.get("state") or "")
        workspace = Path(str(job.get("workspace") or ""))
        if state in {"running", "recovering", "pending"} and workspace.exists():
            return job
    for job in jobs:
        state = str(job.get("state") or "")
        workspace = Path(str(job.get("workspace") or ""))
        if state in {"completed", "failed", "cancelled"} and workspace.exists():
            try:
                if any(workspace.iterdir()):
                    return job
            except Exception:
                continue
    return None

def _standalone_followup_task(raw: str, parent: dict[str, Any] | None) -> str:
    instruction = str(raw or "").strip()
    if not parent:
        return instruction
    previous = str(parent.get("prompt") or "").strip()
    return (
        "Continue from and modify the existing result in the previous Myles workspace. "
        f"Previous owner task: {previous}\n"
        f"Owner's new instruction: {instruction}\n"
        "Preserve working parts, apply the requested changes to the existing result, "
        "and re-run all original verification requirements that still apply."
    )

def _followup_parent(raw: str) -> dict[str, Any] | None:
    if not refers_to_previous_result(raw):
        return None
    return _latest_reusable_job()

def _self_capability_task(raw: str) -> str:
    instruction = str(raw or "").strip()
    return (
        "Improve Myles's own local capability/tooling, not any previous project artifact. "
        "Use a fresh Myles workspace and inspect the installed tool/capability stack first. "
        "Prefer existing built-in or read-only mechanisms before adding dependencies. "
        "If a legitimate dependency is required, install it at user scope when possible, "
        "wire it into Myles as a reusable capability/tool rather than a one-off script, "
        "and regression-test the behavior that triggered this request. "
        "Ordinary tool/dependency failures are Myles's problem to recover from; only surface "
        "a genuine owner authentication/2FA/security-consent gate. PineTree is permanently off-limits.\n"
        f"Owner instruction: {instruction}"
    )

def _start_task(prompt: str, source: str, *, reuse_workspace: str | Path | None = None) -> str:
    prompt = str(prompt or "").strip()
    if str(source or "") != "continuous":
        _preempt_continuous_for_owner()
    if not prompt:
        return "ERROR: no task description was supplied."
    if _is_pinetree_task(prompt):
        return _pinetree_task_refusal()

    signature = compact_task_signature(prompt)
    for existing in list_jobs(50):
        if str(existing.get("state") or "") not in {"running", "pending", "recovering", "blocked_auth"}:
            continue
        if compact_task_signature(str(existing.get("prompt") or "")) == signature:
            state = str(existing.get("state") or "").upper()
            return f"task_id={existing.get('id')} state={state} task={prompt} existing=true"

    job = create_job(prompt, source, record_user=False, reuse_workspace=reuse_workspace)
    cfg = load_config()
    if not active_job() and not bool(cfg.get("light_mode")):
        start_job(job)
        # Re-read actual state after spawning; never infer it from intent.
        actual = get_job(str(job.get("id"))) or job
        state = str(actual.get("state") or "").upper()
        return f"task_id={job.get('id')} state={state} task={prompt}"
    return f"task_id={job.get('id')} state=QUEUED task={prompt}"


def _speak_to_owner(controller_result: str) -> str:
    cfg = load_config()
    messages: list[dict[str, Any]] = [{"role": "system", "content": SPEAK_SYSTEM}]
    messages.extend(history_for_model(18))
    messages.append({"role": "system", "content": "CONTROLLER_RESULT:\n" + controller_result})
    data = model_chat(cfg, messages, temperature=0.35)
    return clean_model_text(str((data.get("message") or {}).get("content") or ""))


def _human_task_label(value: str, limit: int = 120) -> str:
    """Short owner-facing task label; never dump a whole engineering prompt."""
    text = re.sub(r"\s+", " ", str(value or "").strip())
    text = re.sub(r"(?i)^(?:please\s+|can you\s+|could you\s+|would you\s+)", "", text).strip()
    first = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0].strip()
    label = first or text or "that task"
    if len(label) > limit:
        label = label[: max(20, limit - 1)].rstrip(" ,.;:-") + "…"
    return label


def _summarize_search_evidence(question: str, evidence: str) -> str:
    cfg = load_config()
    system = (
        "You are Myles answering a quick public-information lookup. "
        "Answer ONLY from the supplied search evidence. Be concise and natural. "
        "No Markdown headings, no tables, no JSON, no task narration, and no promises of future work. "
        "If the evidence is insufficient or conflicting, say that briefly instead of guessing."
    )
    body = json.dumps({
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"QUESTION:\n{question}\n\nSEARCH EVIDENCE:\n{evidence[:18000]}"},
        ],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.15},
        "keep_alive": "0" if bool(cfg.get("light_mode")) else "10m",
    }).encode("utf-8")
    req = urllib.request.Request(
        cfg["ollama_url"], data=body, method="POST", headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=min(60, int(cfg.get("conversation_timeout_seconds", 120)))) as r:
        data = json.loads(r.read().decode("utf-8"))
    return clean_model_text(str((data.get("message") or {}).get("content") or ""))


def _quick_lookup_answer(raw: str) -> str:
    result = quick.quick_lookup(raw)
    if result.answer:
        return result.answer
    if result.evidence:
        try:
            answer = _summarize_search_evidence(raw, result.evidence)
            if answer:
                return answer
        except Exception as exc:
            log(f"quick lookup summary error: {type(exc).__name__}: {exc}")
        # Evidence is still more honest than converting the lookup into a durable job.
        first = result.evidence.split("\n\n", 1)[0].strip()
        return first or "I found search results, but couldn't summarize them cleanly."
    detail = result.error or "The quick lookup did not return usable data."
    return f"I couldn't finish that quick lookup right now. {detail}"


def _local_location_request(raw: str) -> bool:
    """Recognize ordinary questions asking where a local artifact lives."""
    t = re.sub(r"\s+", " ", str(raw or "").strip().lower())
    location_words = (
        "where did you put", "where is the", "where's the", "where can i find",
        "which folder", "which file", "what file", "show me where", "locate", "find the",
    )
    artifact_words = (
        "report", "backtest", "back test", "result", "output", "file", "folder",
        "document", "dashboard", "workspace",
    )
    return any(word in t for word in location_words) and any(word in t for word in artifact_words)


def _local_artifact_answer(raw: str) -> str:
    """Give a verified local path for a report/result question, when one exists."""
    roots = [ROOT / name for name in ("data", "quant", "workspaces", "logs")]
    suffixes = {".json", ".csv", ".md", ".txt", ".html", ".log", ".xlsx"}
    wanted = ("report", "backtest", "back test", "result", "output")
    matches: list[Path] = []
    seen: set[str] = set()
    for base in roots:
        if not base.exists():
            continue
        try:
            for path in base.rglob("*"):
                if len(matches) >= 12:
                    break
                if not path.is_file() or path.suffix.lower() not in suffixes:
                    continue
                if any(part.lower() in {".venv", "backups", "node_modules"} for part in path.parts):
                    continue
                label = path.name.lower()
                if not any(word in label for word in wanted):
                    continue
                key = str(path).lower()
                if key not in seen:
                    seen.add(key)
                    matches.append(path)
        except OSError as exc:
            log(f"local artifact scan skipped {base}: {type(exc).__name__}: {exc}")
    latest = next((job for job in list_jobs(50)
                   if any(word in str(job.get("prompt") or "").lower() for word in wanted)), None)
    if matches:
        lines = ["I found these local report/result files:"]
        lines.extend(f"- {path}" for path in matches)
        return "\n".join(lines)
    if latest:
        summary = re.sub(r"\s+", " ", str(latest.get("prompt") or "")).strip()
        return (
            "I can verify that the latest related task was recorded, but I cannot verify a separate "
            "report file in the local data folders. The task summary says the results were intended "
            f"for the trading dashboard: {summary[:300]}"
        )
    return "I couldn't verify a local report or result file from the current Myles folders and task history."


def _behavior_feedback_reply(raw: str) -> str:
    low = str(raw or "").lower()
    if any(x in low for x in ("quick search", "google search", "quick lookup", "not a whole", "not a job", "not a task")):
        return "Yeah. That should stay a quick lookup, not become a background job. I didn't start a new task from this message."
    return "Got it. That's feedback on how I handled it, not a new task. I didn't start another job."


def _telegram_plain_text(value: str) -> str:
    """Telegram transport is plain text; strip common Markdown noise."""
    text = clean_model_text(str(value or ""))
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"(?m)^\s*[*+]\s+", "• ", text)
    return text.strip()


def _conversation_tool(name: str, args: dict[str, Any], source: str) -> str:
    if name == "launch_fortnite":
        return "STARTED task=Open Fortnite state=RUNNING tool=launch_fortnite"
    if name == "start_background_job":
        prompt = str(args.get("prompt") or "").strip()
        if not prompt:
            return "ERROR: no task description was supplied."
        if _is_pinetree_task(prompt):
            return _pinetree_task_refusal()
        job = create_job(prompt, source, record_user=False)
        cfg = load_config()
        # Start immediately when the execution lane is free so conversational claims
        # like "I started it" correspond to a real worker, not merely a DB row.
        if not active_job() and not bool(cfg.get("light_mode")):
            start_job(job)
            return f"STARTED task_id={job.get('id')} state=RUNNING task={prompt}"
        return f"STARTED task_id={job.get('id')} state=QUEUED task={prompt}"
    if name == "get_current_work":
        return status_text()
    if name == "stop_current_work":
        active = active_job()
        return cancel_job(active["id"]) if active else "Nothing is actively running."
    if name == "set_light_mode":
        cfg = load_config()
        enabled = bool(args.get("enabled"))
        cfg["light_mode"] = enabled
        save_config(cfg)
        return "Light mode is on; heavy queued work will wait." if enabled else "Light mode is off; normal queued work can run."
    return f"ERROR: unknown conversation tool {name}"


def _latest_cancelled_job() -> dict[str, Any] | None:
    for job in list_jobs(50):
        if str(job.get("state") or "") == "cancelled":
            return job
    return None


def _resume_cancelled_job(job: dict[str, Any] | None) -> str:
    if not job:
        return "There is no recently cancelled task to resume."
    if _is_pinetree_task(str(job.get("prompt") or "")):
        return "That cancelled task referenced PineTree and cannot be resumed."
    set_job(
        str(job["id"]),
        state="pending",
        phase="owner_resume",
        runner_pid=None,
        heartbeat_at=None,
        started_at=None,
        error=None,
    )
    trace(str(job["id"]), "job.owner_resume", "Owner explicitly resumed the cancelled task.")
    return f"Resuming the same task from its existing workspace: {str(job.get('prompt') or '')[:600]}"


def _latest_blocked_auth_job() -> dict[str, Any] | None:
    for job in list_jobs(50):
        if str(job.get("state") or "") == "blocked_auth":
            return job
    return None


def _owner_affirms_auth_resume(raw: str) -> bool:
    t = str(raw or "").strip().lower()
    phrases = ("done", "authorized", "authenticated", "logged in", "signed in", "try again", "continue", "resume", "fixed")
    return any(p in t for p in phrases)




CANONICAL_MYLES_DASHBOARD_URL = "https://joshuaduskin.github.io/MylesAI/"

def _dashboard_url_request(raw: str) -> bool:
    t = re.sub(r"\s+", " ", str(raw or "").strip().lower())
    if "dashboard" not in t and "control center" not in t:
        return False
    wants_link = any(x in t for x in ("url", "link", "where is", "where's", "open it", "view it", "send me"))
    mutating = any(x in t for x in ("build", "create", "redesign", "fix", "change", "edit", "update", "deploy", "publish"))
    return wants_link and not mutating

def _dashboard_url_reply() -> str:
    return f"Myles Control Center: {CANONICAL_MYLES_DASHBOARD_URL}"


def _capability_report_request(raw: str) -> bool:
    t = re.sub(r"\s+", " ", str(raw or "").strip().lower())
    phrases = (
        "what can you do",
        "what all can you do",
        "what tools do you have",
        "what tools are available",
        "what are your capabilities",
        "what capabilities do you have",
        "tell me your capabilities",
        "do you have internet",
        "can you access the internet",
        "can you search the web",
        "can you modify your own code",
        "can you update yourself",
        "do you remember conversations",
        "can you remember conversations",
    )
    return any(p in t for p in phrases)


def _capability_truth_report() -> str:
    plugin_catalog = capabilities.discover_capabilities()
    plugin_names = [name for name, item in plugin_catalog.items() if not item.get("error")]

    github_identity = "not configured"
    identity_path = ROOT / "data" / "github_identity.json"
    try:
        identity = json.loads(identity_path.read_text(encoding="utf-8-sig"))
        owner = str(identity.get("owner") or identity.get("login") or "").strip()
        if owner:
            github_identity = owner
    except Exception:
        pass

    lines = [
        f"I'm Myles {APP_VERSION}. Here's what is actually wired into this runtime:",
        "",
        "• Conversation: natural Telegram/local chat, quick weather and public web lookups, truthful task/status controls.",
        "• Internet: yes for public read-only lookup/fetch, downloads, and browser automation. Authentication or 2FA still needs you when a site requires it.",
        "• Tower access: files, folders, PowerShell, processes, system status, downloads, Git, and persistent Chromium browser automation.",
        "• Packages/tools: I can install Python packages and self-provision browser dependencies when a task needs them.",
        f"• GitHub: isolated Myles GitHub identity is {github_identity}; GitHub Pages publishing and verified public status feeds are built in.",
        "• Self-development: I can clone a safe candidate of my own runtime, modify it, run compile/regression checks, promote only a passing build, and keep a rollback backup.",
        "• Persistence: local conversation/job history is stored in Myles's database and recent history is reused across turns. This is persistent history, not perfect human-like long-term semantic memory.",
        f"• Capability plugins: {', '.join(plugin_names) if plugin_names else 'framework ready; no provider-specific plugins currently installed'}. Ring/health/home integrations become available when their provider plugin and required authentication are configured.",
        "• Background work: durable jobs, heartbeats, retries, continuation, verification, and proactive Telegram completion/failure messages.",
        "• Safety boundary: PineTree is permanently blocked from Myles at the application/tool layer.",
        "",
        "If you ask me to use a capability I don't have yet, I can build/install a reusable Myles capability instead of pretending it already exists.",
    ]
    return "\n".join(lines)



CONTINUOUS_DEFAULT_MISSION = """
OWNER-LOCKED DASHBOARD: Continuous improvement must never modify, commit, push, publish, replace, or create alternatives to JoshuaDuskin/MylesAI. Inspect health/status only. # MYLES_CONTINUOUS_MISSION_DASHBOARD_LOCK_v2
Continuously improve Myles and the owner's personal Myles ecosystem.
Each cycle must choose ONE highest-value concrete improvement, implement it safely, test it, verify it, and finish the cycle so the next cycle can choose again.

Priorities:
1. Make Myles faster: reduce unnecessary model calls, redundant planning, repeated discovery, blocking work, and slow simple-query paths.
2. Make Myles more natural and communicative: normal human conversation, concise routine replies, truthful progress, no raw prompts/JSON/internal noise unless asked.
3. Improve autonomy and recovery: inspect recent failures/logs/traces, diagnose root causes, add reusable recovery patterns, try alternate tools/approaches, and treat ordinary failures as Myles's problem.
4. Improve reusable tools/capabilities: web, browser, files, PowerShell, Git/GitHub, packages, system work, provider plugins, and accurate tool inventory.
5. OWNER-LOCKED DASHBOARD: inspect health/status only; never modify or publish any dashboard repository during continuous improvement.
6. Advance the personal trading research system safely: strategy framework, backtesting, paper trading/simulation, market-data handling, risk controls, logging, comparison, analytics, and private dashboard integration. Never place real-money trades or expose financial secrets publicly.
7. Improve continuity: use stored job/message history and failure evidence intelligently instead of making the owner repeat himself.
8. Keep the runtime stable: candidate -> compile/tests -> verification -> promote -> health check -> rollback if unhealthy.

Rules:
- PineTree is permanently off-limits. Never read, inspect, authenticate to, modify, deploy, test, or otherwise touch any PineTree resource.
- Do not invent results, progress, live data, URLs, trading performance, or completed work.
- Do not ask the owner about ordinary errors. Search, inspect docs, install legitimate user-scope dependencies, retry intelligently, or choose another approach.
- Only surface genuine owner-only gates such as OAuth, 2FA, payment/security consent, or a serious unrecoverable condition.
- Do not spam Telegram with routine cycle completions. Keep a local evidence trail.
"""


def _continuous_enable_request(raw: str) -> bool:
    t = re.sub(r"\s+", " ", str(raw or "").strip().lower())
    if not t:
        return False
    if any(x in t for x in ("don't stop", "do not stop", "never stop")) and any(
        x in t for x in ("working on yourself", "improving yourself", "self-improvement")
    ):
        return True
    markers = (
        "work nonstop",
        "work continuously",
        "keep working on yourself",
        "keep improving yourself",
        "continuous self-improvement",
        "continuous improvement",
        "work on yourself tonight",
        "work on yourself overnight",
        "keep working overnight",
        "keep yourself busy tonight",
    )
    return any(x in t for x in markers)


def _continuous_disable_request(raw: str) -> bool:
    t = re.sub(r"\s+", " ", str(raw or "").strip().lower())
    if "don't stop" in t or "do not stop" in t or "never stop" in t:
        return False
    markers = (
        "stop continuous improvement",
        "stop continuous work",
        "stop working on yourself",
        "stop improving yourself",
        "stop the overnight work",
        "stop overnight improvement",
        "turn off continuous improvement",
        "disable continuous improvement",
    )
    return any(x in t for x in markers)


def _continuous_enabled() -> bool:
    return get_setting("continuous.enabled", "0") == "1"


def _continuous_mission() -> str:
    return get_setting("continuous.mission", "") or CONTINUOUS_DEFAULT_MISSION


def _continuous_status_text() -> str:
    enabled = _continuous_enabled()
    cycle = int(get_setting("continuous.cycle", "0") or "0")
    last_job_id = get_setting("continuous.last_job_id", "")
    failures = int(get_setting("continuous.consecutive_failures", "0") or "0")
    if not enabled:
        return "Continuous improvement is off."
    active = active_job()
    if active and str(active.get("source") or "") == "continuous":
        truth = job_truth(active)
        return (
            "I'm working on a continuous-improvement cycle right now. "
            "My focus is making myself faster, more reliable, and easier to use. "
            "The cycle is running normally."
        )
    if last_job_id:
        last = get_job(last_job_id)
        if last:
            return (
                "I'm using continuous improvement during idle time. "
                "My last cycle finished, and I'll start another when no owner task is waiting."
            )
    return "I'm set to use idle time for continuous improvement when no owner task is waiting."


def _continuous_enable(owner_instruction: str = "") -> str:
    mission = CONTINUOUS_DEFAULT_MISSION
    instruction = str(owner_instruction or "").strip()
    if instruction:
        mission += "\n\nOwner's standing instruction that enabled this program:\n" + instruction
    set_setting("continuous.enabled", "1")
    set_setting("continuous.mission", mission)
    set_setting("continuous.consecutive_failures", "0")
    set_setting("continuous.last_terminal_seen", "")
    set_setting("continuous.next_spawn_epoch", "0")
    return (
        "I'm set to keep improving myself during idle time—faster responses, better reliability, "
        "better tools, clearer communication, and safe trading research—until you tell me to stop."
    )


def _continuous_disable(cancel_running: bool = True) -> str:
    set_setting("continuous.enabled", "0")
    if cancel_running:
        active = active_job()
        if active and str(active.get("source") or "") == "continuous":
            _terminate_pid(active.get("runner_pid"))
            set_job(
                str(active["id"]),
                state="cancelled",
                phase="continuous_program_stopped",
                runner_pid=None,
                heartbeat_at=now_iso(),
                error=None,
            )
            trace(str(active["id"]), "continuous.stopped", "Continuous program stopped by owner.")
    for job in list_jobs(80):
        if str(job.get("source") or "") == "continuous" and str(job.get("state") or "") == "pending":
            set_job(
                str(job["id"]),
                state="cancelled",
                phase="continuous_program_stopped",
                runner_pid=None,
                heartbeat_at=now_iso(),
                error=None,
            )
    return "Continuous improvement is off. I stopped its background work."


def _notify_owner_telegram(text: str) -> None:
    if not load_config().get("telegram_enabled"):
        return
    add_message("telegram", "assistant", clean_model_text(text), None)


def _continuous_cycle_prompt(cycle: int, last_job: dict[str, Any] | None = None) -> str:
    last_note = ""
    if last_job:
        last_note = (
            "\nPREVIOUS CONTINUOUS CYCLE:\n"
            f"State: {last_job.get('state')}\n"
            f"Phase: {last_job.get('phase')}\n"
            f"Error: {str(last_job.get('error') or '')[:1200]}\n"
            f"Result: {str(last_job.get('result') or '')[:1800]}\n"
        )
    return (
        f"[CONTINUOUS IMPROVEMENT CYCLE {cycle}]\n"
        + _continuous_mission()
        + last_note
        + """
THIS CYCLE:
- Inspect the current Myles runtime, recent logs/traces/job history, current tools, canonical dashboard, and relevant personal trading workspace evidence.
- Pick ONE highest-value improvement that is not already verified complete.
- If the previous cycle failed, prioritize understanding and overcoming that failure rather than repeating the same action.
- Make the change through a safe candidate/test/promote workflow when changing Myles itself.
- For dashboard work, use only JoshuaDuskin/MylesAI and real sanitized state.
- For trading work, stay in research/backtest/paper/simulation/risk-control territory; never place a real-money trade.
- Produce verifiable evidence and stop this cycle after that concrete improvement is complete. The runtime will automatically create the next cycle.
"""
    )


def _continuous_program_tick() -> None:
    """Keep the standing improvement mission moving whenever owner work is idle."""
    if not _continuous_enabled():
        return
    if bool(load_config().get("light_mode")) or CHAT_BUSY.is_set():
        return
    if active_job():
        return

    jobs = list_jobs(100)
    pending_owner = [
        j for j in jobs
        if str(j.get("state") or "") == "pending"
        and str(j.get("source") or "") != "continuous"
    ]
    if pending_owner:
        return

    pending_cont = [
        j for j in jobs
        if str(j.get("state") or "") == "pending"
        and str(j.get("source") or "") == "continuous"
    ]
    if pending_cont:
        return

    last_id = get_setting("continuous.last_job_id", "")
    last = get_job(last_id) if last_id else None
    seen = get_setting("continuous.last_terminal_seen", "")
    failures = int(get_setting("continuous.consecutive_failures", "0") or "0")

    if last and str(last.get("state") or "") in {"completed", "failed", "cancelled"} and seen != str(last.get("id")):
        state = str(last.get("state") or "")
        phase = str(last.get("phase") or "")
        if state == "completed":
            failures = 0
        elif state == "failed":
            failures += 1
        elif state == "cancelled" and phase not in {"preempted_for_owner", "continuous_program_stopped"}:
            failures += 1
        set_setting("continuous.consecutive_failures", str(failures))
        set_setting("continuous.last_terminal_seen", str(last.get("id")))
        set_setting("continuous.next_spawn_epoch", str(int(time.time()) + (10 if failures == 0 else min(60, 15 * failures))))

    if failures >= 5:
        set_setting("continuous.enabled", "1")
        set_setting("continuous.consecutive_failures", "0")
        set_setting("continuous.next_spawn_epoch", str(int(time.time()) + 300))
        _notify_owner_telegram(
            "The last five improvement cycles failed verification. "
            "I reset the retry budget and will resume after a five-minute recovery pause; "
            "the normal runtime remains online."
        )
        return

    next_epoch = int(get_setting("continuous.next_spawn_epoch", "0") or "0")
    if int(time.time()) < next_epoch:
        return

    cycle = int(get_setting("continuous.cycle", "0") or "0") + 1
    prompt = _continuous_cycle_prompt(cycle, last)
    job = create_job(prompt, "continuous", record_user=False)
    jid = str(job.get("id") or "")
    set_setting("continuous.cycle", str(cycle))
    set_setting("continuous.last_job_id", jid)
    set_setting("continuous.last_spawn_epoch", str(int(time.time())))
    set_setting("continuous.next_spawn_epoch", "0")
    trace(jid, "continuous.cycle.created", f"cycle={cycle}")


def _preempt_continuous_for_owner() -> None:
    """Real owner work outranks the standing continuous-improvement lane."""
    active = active_job()
    if not active or str(active.get("source") or "") != "continuous":
        return
    _terminate_pid(active.get("runner_pid"))
    set_job(
        str(active["id"]),
        state="cancelled",
        phase="preempted_for_owner",
        runner_pid=None,
        heartbeat_at=now_iso(),
        error=None,
    )
    trace(str(active["id"]), "continuous.preempted", "Preempted by explicit owner project work.")
    set_setting("continuous.next_spawn_epoch", str(int(time.time()) + 15))


def _direct_fortnite_launch() -> str:
    if os.name != "nt":
        return "Fortnite launch is only available on the Windows tower."
    uri = "com.epicgames.launcher://apps/Fortnite?action=launch&silent=true"
    try:
        subprocess.Popen(["cmd.exe", "/c", "start", "", uri], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return "Fortnite launch requested through Epic Games Launcher."
    except Exception as exc:
        return f"Fortnite could not be launched: {type(exc).__name__}: {exc}"


def handle_owner_message(text: str, source: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    if not raw:
        return {"kind": "chat", "reply": ""}

    if re.search(r"\b(?:open|launch|start)\s+fortnite\b", raw, re.I):
        add_message(source, "user", raw, None)
        final = _direct_fortnite_launch()
        message_id = add_message(source, "assistant", final, None)
        return {"kind": "conversation", "reply": final, "message_id": message_id}

    # Authentication is the one normal owner gate. When the owner confirms it is done,
    # resume the same blocked job/workspace instead of creating a duplicate task.
    blocked = _latest_blocked_auth_job()
    if blocked and _owner_affirms_auth_resume(raw):
        add_message(source, "user", raw, None)
        if _is_pinetree_task(str(blocked.get("prompt") or "")):
            set_job(str(blocked["id"]), state="cancelled", phase="cancelled_pinetree_isolation", runner_pid=None, heartbeat_at=None, error="Cancelled by PineTree isolation boundary.")
            final = "That blocked task referenced PineTree, so it was cancelled instead of resumed. PineTree is permanently isolated from Myles."
            message_id = add_message(source, "assistant", final, str(blocked["id"]))
            return {"kind": "conversation", "reply": final, "message_id": message_id, "job_id": str(blocked["id"])}
        set_job(str(blocked["id"]), state="pending", phase="resuming_after_auth", runner_pid=None, heartbeat_at=None, error=None)
        final = "Got it. I'm resuming the same task from the existing workspace now."
        message_id = add_message(source, "assistant", final, str(blocked["id"]))
        return {"kind": "conversation", "reply": final, "message_id": message_id, "job_id": str(blocked["id"])}

    add_message(source, "user", raw, None)
    CHAT_BUSY.set()
    started_job: str | None = None
    try:
        active_now = active_job()
        cancelled_now = _latest_cancelled_job()
        if _continuous_disable_request(raw):
            forced = None
            route = {"intent": "continuous_off", "task": ""}
        elif _continuous_enable_request(raw):
            forced = None
            route = {"intent": "continuous_on", "task": raw}
        else:
            forced = deterministic_control(
                raw,
                has_active=bool(active_now),
                has_recent_cancelled=bool(cancelled_now),
            )
            if forced:
                route = {"intent": forced, "task": ""}
            else:
                route = None

        if route is None:
            if _dashboard_url_request(raw):
                    route = {"intent": "dashboard_url", "task": ""}
            elif _capability_report_request(raw):
                route = {"intent": "capabilities", "task": ""}
            elif behavior_feedback_request(raw):
                route = {"intent": "feedback", "task": ""}
            elif _local_location_request(raw):
                route = {"intent": "local_lookup", "task": ""}
            elif quick.looks_like_quick_public_lookup(raw):
                route = {"intent": "lookup", "task": ""}
            elif self_capability_request(raw):
                # A request to improve Myles itself is real work, but it is NEVER a
                # modification of the last dashboard/project workspace.
                route = {"intent": "start", "task": _self_capability_task(raw)}
            elif strong_action_request(raw) and not natural_question(raw):
                parent = _followup_parent(raw)
                route = {
                    "intent": "modify" if parent else "start",
                    "task": _standalone_followup_task(raw, parent) if parent else raw,
                }
            elif followup_action_request(raw) and not natural_question(raw):
                parent = _followup_parent(raw) or _latest_reusable_job()
                route = {
                    "intent": "modify" if parent else "start",
                    "task": _standalone_followup_task(raw, parent) if parent else raw,
                }
            else:
                route = _router_call(raw)

        intent = route["intent"]
        task = str(route.get("task") or "").strip()
        if forced is None and intent not in {"continuous_on", "continuous_off", "dashboard_url", "capabilities"}:
            local_intent = intent
            intent, jev_meta = verify_with_jev(
                raw,
                local_intent,
                has_active=bool(active_now),
                has_recent_cancelled=bool(cancelled_now),
                cfg=load_config(),
                secrets=load_secrets(),
            )
            log(
                "decision route "
                f"local={local_intent} final={intent} "
                f"jev_used={bool(jev_meta.get('used'))} jev_decision={jev_meta.get('decision')}"
            )

        # Conversational corrections always outrank an action verb such as
        # "fix" inside a question. This prevents messages like "I didn't ask
        # for that report" from becoming new background jobs.
        if behavior_feedback_request(raw):
            intent = "feedback"
            task = ""

        # A semantic router is still useful for ambiguous language, but it may not
        # demote an obvious imperative action into chat/status.
        if (
            not behavior_feedback_request(raw)
            and not _local_location_request(raw)
            and not quick.looks_like_quick_public_lookup(raw)
            and (self_capability_request(raw) or strong_action_request(raw) or followup_action_request(raw))
            and intent in {"chat", "status"}
        ):
            if self_capability_request(raw):
                intent = "start"
                task = _self_capability_task(raw)
            else:
                parent = _followup_parent(raw) if refers_to_previous_result(raw) else None
                if parent or followup_action_request(raw):
                    parent = parent or _latest_reusable_job()
                    intent = "modify" if parent else "start"
                    task = _standalone_followup_task(raw, parent) if parent else raw
                else:
                    intent = "start"
                    task = raw

        # The language model is never allowed to stop work unless the owner's
        # latest message contains an explicit stop command. This prevents normal
        # conversation/questions from becoming destructive control actions.
        if intent in {"stop", "replace"} and not explicit_stop_requested(raw):
            intent = "status" if looks_like_status_request(raw, has_active=bool(active_now)) else "chat"
            task = ""
        if intent == "resume" and not explicit_resume_requested(raw):
            intent = "chat"

        log(f"semantic route source={source} intent={intent} forced={forced or ''} task={task[:500]}")

        if intent == "continuous_on":
            result = _continuous_enable(task or raw)
            controller = "OWNER_ACTION=continuous_on\n" + result
        elif intent == "continuous_off":
            result = _continuous_disable()
            controller = "OWNER_ACTION=continuous_off\n" + result
        elif intent == "dashboard_url":
            result = _dashboard_url_reply()
            controller = "OWNER_ACTION=dashboard_url\n" + result
        elif intent == "capabilities":
            result = _capability_truth_report()
            controller = "OWNER_ACTION=capabilities\n" + result
        elif intent == "lookup":
            result = _quick_lookup_answer(raw)
            controller = "OWNER_ACTION=lookup\n" + result
        elif intent == "local_lookup":
            result = _local_artifact_answer(raw)
            controller = "OWNER_ACTION=local_lookup\n" + result
        elif intent == "feedback":
            result = _behavior_feedback_reply(raw)
            controller = "OWNER_ACTION=feedback\n" + result
        elif intent == "start":
            result = _start_task(task or raw, source)
            if result.startswith("task_id="):
                started_job = result.split("task_id=", 1)[1].split(" ", 1)[0]
            controller = "OWNER_ACTION=start\n" + result
        elif intent == "modify":
            parent = _followup_parent(raw) or _latest_reusable_job()
            standalone = task or _standalone_followup_task(raw, parent)
            reuse = str(parent.get("workspace")) if parent and parent.get("workspace") else None
            result = _start_task(standalone, source, reuse_workspace=reuse)
            if result.startswith("task_id="):
                started_job = result.split("task_id=", 1)[1].split(" ", 1)[0]
            controller = (
                "OWNER_ACTION=modify\n"
                + (f"REUSED_WORKSPACE={reuse}\n" if reuse else "")
                + result
            )
        elif intent == "replace":
            active = active_job()
            stopped = cancel_job(active["id"]) if active else "Nothing was actively running."
            result = _start_task(task or raw, source)
            if result.startswith("task_id="):
                started_job = result.split("task_id=", 1)[1].split(" ", 1)[0]
            controller = "OWNER_ACTION=replace\nSTOP_RESULT=" + stopped + "\nSTART_RESULT=" + result
        elif intent == "status":
            controller = "OWNER_ACTION=status\n" + status_text()
        elif intent == "stop":
            active = active_job()
            if active and str(active.get("source") or "") == "continuous":
                set_setting("continuous.enabled", "0")
            result = cancel_job(active["id"]) if active else "Nothing is actively running."
            controller = "OWNER_ACTION=stop\n" + result
        elif intent == "resume":
            result = _resume_cancelled_job(_latest_cancelled_job())
            controller = "OWNER_ACTION=resume\n" + result
        elif intent == "light_on":
            cfg = load_config(); cfg["light_mode"] = True; save_config(cfg)
            controller = "OWNER_ACTION=light_on\nLight mode is on; heavy queued work will wait."
        elif intent == "light_off":
            cfg = load_config(); cfg["light_mode"] = False; save_config(cfg)
            controller = "OWNER_ACTION=light_off\nLight mode is off; normal queued work can run."
        else:
            controller = (
                "OWNER_ACTION=chat\nNo computer task was created or changed.\n"
                "LIVE_EXECUTION_STATE:\n" + status_text()
            )

        # Start/replace acknowledgements are deterministic. The language model is not
        # allowed to embellish a newly-created job with invented progress, hosting, files,
        # URLs, or other work that has not happened yet.
        if intent in {"start", "modify", "replace"}:
            running = "state=RUNNING" in controller
            queued = "state=QUEUED" in controller
            if "REFUSED_PINETREE:" in controller:
                final = "PineTree is permanently isolated from Myles. I did not create a task or touch any PineTree resource."
            elif running:
                label = _human_task_label(task or raw)
                if intent == "modify":
                    final = f"I’m on it — I’ll post a concise verified summary when it’s finished. ({label})"
                else:
                    final = f"I’m on it — I’ll post a concise verified summary when it’s finished. ({label})"
            elif queued:
                label = _human_task_label(task or raw)
                if intent == "modify":
                    final = f"Queued the update: {label}"
                else:
                    final = f"Queued: {label}"
            else:
                final = "I accepted the request, but I could not verify that the execution worker started."
        else:
            # Status/control answers are deterministic. The language model must not
            # paraphrase away a failure, queued job, dead worker, or heartbeat state.
            if intent == "continuous_on":
                final = result
            elif intent == "continuous_off":
                final = result
            elif intent == "dashboard_url":
                final = result
            elif intent == "capabilities":
                final = result
            elif intent == "lookup":
                final = result
            elif intent == "local_lookup":
                final = result
            elif intent == "feedback":
                final = result
            elif intent == "status":
                final = status_text()
            elif intent == "stop":
                final = result
            elif intent == "resume":
                final = result
            elif intent == "light_on":
                final = "Light mode is on; heavy queued work will wait."
            elif intent == "light_off":
                final = "Light mode is off; normal queued work can run."
            else:
                final = _speak_to_owner(controller)
                if not final:
                    final = "I'm here."

                # Truth firewall: Myles may not promise future computer work unless
                # a real background job was created.
                if execution_promise_text(final):
                    if likely_action_request(raw) or followup_action_request(raw):
                        parent = _followup_parent(raw) or (_latest_reusable_job() if followup_action_request(raw) else None)
                        standalone = _standalone_followup_task(raw, parent) if parent else raw
                        reuse = str(parent.get("workspace")) if parent and parent.get("workspace") else None
                        result = _start_task(standalone, source, reuse_workspace=reuse)
                        if result.startswith("task_id="):
                            started_job = result.split("task_id=", 1)[1].split(" ", 1)[0]
                        if "state=RUNNING" in result:
                            final = "Started. I created a real background task for that request instead of just saying I would."
                        elif "state=QUEUED" in result:
                            final = "Queued. I created a real task for that request instead of just saying I would."
                        elif "REFUSED_PINETREE:" in result:
                            final = "PineTree is permanently isolated from Myles. I did not create that task."
                        else:
                            final = "I understood the work request, but I could not verify that a background task was created, so I won't pretend it started."
                    else:
                        final = "I haven't started a computer task from that message, so I won't claim that I'm working on one."
    except Exception as exc:
        error_text = f"{type(exc).__name__}: {exc}"
        log(f"conversation error: {error_text}")
        set_setting("conversation.last_error", error_text[:1000])
        set_setting("conversation.last_error_at", now_iso())
        final = fallback_conversation(raw, status_text(), model_error=error_text)
    finally:
        CHAT_BUSY.clear()

    final = clean_model_text(final)
    message_id = add_message(source, "assistant", final, started_job)
    return {"kind": "conversation", "reply": final, "message_id": message_id, "job_id": started_job}

def _telegram_credentials() -> tuple[str, int]:
    secrets = load_secrets()
    token = str(secrets.get("MYLES_TELEGRAM_TOKEN") or "").strip()
    raw = str(secrets.get("MYLES_OWNER_ID") or secrets.get("MYLES_TELEGRAM_USER_ID") or "").strip()
    owner_id = int(raw) if raw.isdigit() else 0
    return token, owner_id


def _telegram_api(token: str, method: str, data: dict[str, Any] | None = None, timeout: int = 40) -> dict[str, Any]:
    payload = urllib.parse.urlencode({k: v for k, v in (data or {}).items() if v is not None}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}", data=payload, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _telegram_send(token: str, chat_id: int, text: str) -> None:
    text = _telegram_plain_text(str(text or ""))
    if not text:
        return
    chunks = [text[i:i+3800] for i in range(0, len(text), 3800)] or [""]
    for chunk in chunks:
        _telegram_api(token, "sendMessage", {"chat_id": chat_id, "text": chunk}, timeout=30)


def _flush_telegram_outbox(token: str) -> None:
    chat_raw = get_setting("telegram.last_chat_id", "0")
    if not chat_raw.isdigit() or int(chat_raw) <= 0:
        return
    chat_id = int(chat_raw)
    last_raw = get_setting("telegram.last_sent_message_id", "")
    if not last_raw:
        set_setting("telegram.last_sent_message_id", str(latest_message_id()))
        return
    last = int(last_raw) if last_raw.isdigit() else 0
    rows = messages_after(last, source="telegram", limit=100)
    for row in rows:
        mid = int(row["id"])
        if row.get("role") == "assistant":
            _telegram_send(token, chat_id, str(row.get("content") or ""))
        set_setting("telegram.last_sent_message_id", str(mid))


def telegram_loop() -> None:
    token, owner_id = _telegram_credentials()
    if not token or not owner_id:
        log("Telegram is not configured; remote chat worker not started.")
        return
    cfg = load_config()
    cfg["telegram_enabled"] = True
    save_config(cfg)
    if not get_setting("telegram.last_sent_message_id", ""):
        set_setting("telegram.last_sent_message_id", str(latest_message_id()))
    offset_raw = get_setting("telegram.update_offset", "")
    if offset_raw.isdigit():
        offset = int(offset_raw)
    else:
        # First v8.3 start: acknowledge any stale backlog without replaying old owner messages as fresh commands.
        try:
            bootstrap = _telegram_api(token, "getUpdates", {"timeout": 0}, timeout=10)
            ids = [int(u.get("update_id") or 0) for u in (bootstrap.get("result") or [])]
            offset = (max(ids) + 1) if ids else 0
            set_setting("telegram.update_offset", str(offset))
        except Exception:
            offset = 0
    log(f"Telegram worker starting for owner id {owner_id}.")

    while not STOP.is_set():
        try:
            _flush_telegram_outbox(token)
            data = _telegram_api(token, "getUpdates", {"offset": offset, "timeout": 20, "allowed_updates": json.dumps(["message"])}, timeout=30)
            for update in data.get("result") or []:
                uid = int(update.get("update_id") or 0)
                if uid >= offset:
                    offset = uid + 1
                    set_setting("telegram.update_offset", str(offset))
                message = update.get("message") or {}
                user = message.get("from") or {}
                chat = message.get("chat") or {}
                text = str(message.get("text") or "").strip()
                if not text or int(user.get("id") or 0) != owner_id:
                    continue
                chat_id = int(chat.get("id") or 0)
                if not chat_id:
                    continue
                set_setting("telegram.last_chat_id", str(chat_id))
                handle_owner_message(text, "telegram")
                _flush_telegram_outbox(token)
        except Exception as exc:
            log(f"telegram error: {type(exc).__name__}: {exc}")
            STOP.wait(5)


def _pause_active_job_for_light_mode(job: dict[str, Any]) -> None:
    """Pause heavy owner/continuous work without losing its durable queue entry."""
    job_id = str(job.get("id") or "")
    if not job_id:
        return
    _terminate_pid(job.get("runner_pid"))
    set_job(
        job_id,
        state="pending",
        phase="paused_for_game",
        runner_pid=None,
        heartbeat_at=None,
        started_at=None,
        error=None,
    )
    trace(job_id, "job.paused_for_game", "Automatic/manual light mode paused background execution.")


def monitor_loop() -> None:
    while not STOP.wait(3):
        try:
            cfg = load_config()
            light = bool(cfg.get("light_mode"))
            active = active_job()

            if light:
                # Gaming/latency mode is intentionally minimal. Do not run
                # capability ticks, status-feed publishing, continuous improvement,
                # or any durable job worker while the owner is gaming.
                if active:
                    _pause_active_job_for_light_mode(active)
                if RESTART_REQUEST.exists():
                    log("restart request detected during light mode; supervisor will perform verified restart")
                    STOP.set()
                    threading.Thread(target=lambda: (time.sleep(1), os._exit(0)), daemon=True).start()
                continue

            capabilities.run_background_ticks()
            # Built-in sanitized public status feed is nonessential during gaming
            # and therefore only runs in normal mode.
            try:
                tools.runtime_status_feed_tick_async()
            except Exception as exc:
                log(f"status feed tick error: {type(exc).__name__}: {exc}")

            active = active_job()
            if active:
                t = job_truth(active)
                if t["truth_state"] == "stalled":
                    reason = "; ".join(t["stall_reasons"]) or "execution truth marked it stalled"
                    recover_job(active["id"], reason=f"Automatic recovery: {reason}")
                continue

            if not CHAT_BUSY.is_set():
                _continuous_program_tick()
                pending = next_pending_job()
                if pending:
                    start_job(pending)

            if RESTART_REQUEST.exists():
                # The hidden runtime supervisor owns candidate restart, health
                # verification, and rollback. The core only exits cleanly so
                # the supervisor can replace it without a second launcher.
                log("restart request detected; supervisor will perform verified restart")
                STOP.set()
                threading.Thread(target=lambda: (time.sleep(1), os._exit(0)), daemon=True).start()
        except Exception as exc:
            log(f"monitor error: {type(exc).__name__}: {exc}")


class MylesHTTPServer(ThreadingHTTPServer):
    """Single local control server.

    Binding this socket happens before Telegram/capability workers start. A second
    Myles process therefore exits before it can create a duplicate Telegram poller.
    """
    allow_reuse_address = True
    daemon_threads = True


class ApiHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log("HTTP " + (fmt % args))

    def _dashboard_origin(self) -> str:
        origin = str(self.headers.get("Origin") or "").rstrip("/")
        allowed = {
            "https://joshuaduskin.github.io",
            "http://127.0.0.1:8766",
            "http://localhost:8766",
        }
        return origin if origin in allowed else ""

    def _cors_headers(self) -> None:
        origin = self._dashboard_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")

    def _send(self, code: int, data: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self._cors_headers()
        self.end_headers()

    def _json(self, code: int, obj: Any):
        self._send(code, json.dumps(obj, indent=2).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/health":
            token, owner_id = _telegram_credentials()
            return self._json(200, {
                "ok": True,
                "version": APP_VERSION,
                "pid": os.getpid(),
                "time": now_iso(),
                "telegram_configured": bool(token and owner_id),
                "light_mode": bool(load_config().get("light_mode")),
                "model_runtime": model_health_dict(load_config()),
                "decision_adapter": {
                    "jev_enabled": bool(load_config().get("jev_enabled")),
                    "jev_configured": bool(load_config().get("jev_url") or load_secrets().get("MYLES_JEV_URL")),
                    "privacy_mode": "abstract_state_only",
                },
                "last_conversation_error": get_setting("conversation.last_error", ""),
                "last_conversation_error_at": get_setting("conversation.last_error_at", ""),
                "status": status_text(),
            })
        if path == "/api/messages":
            return self._json(200, {"messages": recent_messages(120)})
        if path == "/api/public-status":
            return self._json(200, tools._runtime_public_snapshot())
        if path == "/api/jobs":
            return self._json(200, {"jobs": [job_truth(j) for j in list_jobs(50)]})
        if path == "/api/capabilities":
            try:
                return self._json(200, json.loads(capabilities.status_json()))
            except Exception as exc:
                return self._json(500, {"error": f"{type(exc).__name__}: {exc}"})
        if path.startswith("/api/job/"):
            jid = path.rsplit("/", 1)[-1]
            job = get_job(jid)
            return self._json(200 if job else 404, job_truth(job) if job else {"error": "not found"})
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        n = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
        except Exception:
            return self._json(400, {"error": "invalid json"})
        if path == "/api/control/shutdown":
            # Server is bound to localhost only. This endpoint exists so future
            # upgrades can stop Myles cleanly without killing processes first.
            self._json(200, {"ok": True, "status": "shutting_down"})
            STOP.set()
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return

        if path == "/api/control/continuous":
            enabled = bool(body.get("enabled"))
            message = _continuous_enable("Dashboard owner control") if enabled else _continuous_disable(cancel_running=True)
            return self._json(200, {
                "ok": True,
                "enabled": _continuous_enabled(),
                "status": _continuous_status_text(),
                "message": message,
            })

        if path == "/api/send":
            text = str(body.get("text") or "").strip()
            source = str(body.get("source") or "console")[:32]
            if not text:
                return self._json(400, {"error": "text required"})
            return self._json(200, handle_owner_message(text, source))
        return self._json(404, {"error": "not found"})


def main() -> int:
    init_db()
    cfg = load_config()

    # Acquire the single-instance localhost port BEFORE starting Telegram or
    # capability hooks. This prevents a duplicate process from creating a second
    # Telegram getUpdates poller and causing HTTP 409 conflicts.
    try:
        server = MylesHTTPServer((cfg["core_host"], int(cfg["core_port"])), ApiHandler)
    except OSError as exc:
        log(f"Myles core {APP_VERSION} refused duplicate startup: {type(exc).__name__}: {exc}")
        return 12

    PID_PATH.write_text(str(os.getpid()), encoding="utf-8")
    log(f"Myles core {APP_VERSION} starting pid={os.getpid()}")

    threading.Thread(target=monitor_loop, name="myles-monitor", daemon=True).start()
    threading.Thread(target=telegram_loop, name="myles-telegram", daemon=True).start()
    # Plugin startup hooks are isolated from core availability. A slow provider
    # login/device probe can no longer prevent Myles from coming online.
    threading.Thread(
        target=capabilities.run_startup_hooks,
        name="myles-capability-startup",
        daemon=True,
    ).start()

    try:
        server.serve_forever(poll_interval=.5)
    finally:
        STOP.set()
        server.server_close()
        try:
            PID_PATH.unlink(missing_ok=True)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
