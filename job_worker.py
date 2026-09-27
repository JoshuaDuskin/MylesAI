from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any

from myles_common import (
    ROOT, WORKSPACES, load_config, init_db, get_job, set_job, trace,
    history_for_model, add_message, now_iso, traces_for_job, clean_model_text
)
import myles_tools as tools
import myles_capabilities as capabilities
from myles_runtime_v9 import (
    PlannerParseError, normalize_action_plan, parse_native_arguments,
    classify_tool_result,
)

TOOL_DEFS = [
    {"type":"function","function":{"name":"run_powershell","description":"Run a PowerShell command on the owner's Windows tower. Use this for local system work, package managers, process management, Windows settings, building software, testing software, and commands not covered by a narrower tool.","parameters":{"type":"object","properties":{"command":{"type":"string"},"timeout_seconds":{"type":"integer","minimum":1,"maximum":1800}},"required":["command"]}}},
    {"type":"function","function":{"name":"read_text_file","description":"Read a local text file.","parameters":{"type":"object","properties":{"path":{"type":"string"},"max_chars":{"type":"integer"}},"required":["path"]}}},
    {"type":"function","function":{"name":"write_text_file","description":"Create, replace, or append to a local text file.","parameters":{"type":"object","properties":{"path":{"type":"string"},"content":{"type":"string"},"append":{"type":"boolean"}},"required":["path","content"]}}},
    {"type":"function","function":{"name":"write_generated_file","description":"Generate and write a complete code/text file from concise instructions. Prefer this for HTML, code, scripts, documents, or content longer than a few hundred characters because the file body is generated outside the tool-call JSON envelope.","parameters":{"type":"object","properties":{"path":{"type":"string"},"instructions":{"type":"string"},"append":{"type":"boolean"},"max_chars":{"type":"integer"}},"required":["path","instructions"]}}},
    {"type":"function","function":{"name":"apply_text_patch","description":"Apply an exact deterministic text replacement to an existing file without regenerating the whole file.","parameters":{"type":"object","properties":{"path":{"type":"string"},"old_text":{"type":"string"},"new_text":{"type":"string"},"count":{"type":"integer"}},"required":["path","old_text","new_text"]}}},
    {"type":"function","function":{"name":"capability_status","description":"List installed Myles capability plugins and their tool/auth status. Use this for provider-specific integrations such as Ring, health/weight sources, or home automation.","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"list_directory","description":"List local files and folders.","parameters":{"type":"object","properties":{"path":{"type":"string"},"recursive":{"type":"boolean"},"max_items":{"type":"integer"}},"required":["path"]}}},
    {"type":"function","function":{"name":"download_file","description":"Download a URL to a local file.","parameters":{"type":"object","properties":{"url":{"type":"string"},"destination":{"type":"string"}},"required":["url","destination"]}}},
    {"type":"function","function":{"name":"web_fetch","description":"Fetch text/content from a public URL.","parameters":{"type":"object","properties":{"url":{"type":"string"},"max_chars":{"type":"integer"}},"required":["url"]}}},
    {"type":"function","function":{"name":"web_search","description":"Search the public web and return bounded source evidence. Use this for research/current public information inside a durable job before heavier browser automation.","parameters":{"type":"object","properties":{"query":{"type":"string"},"max_results":{"type":"integer","minimum":1,"maximum":8}},"required":["query"]}}},
    {"type":"function","function":{"name":"tool_inventory","description":"Return Myles's actual installed core and capability tool inventory. Use this instead of guessing what Myles can or cannot do.","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"github_pages_publish","description":"Publish a static web workspace to GitHub Pages using the GitHub identity that is actually authenticated on this tower. Never invents a GitHub username. Creates/retargets the repository, pushes main, configures Pages, and returns the public URL. Missing GitHub authentication is surfaced as an owner auth gate.","parameters":{"type":"object","properties":{"repo_path":{"type":"string"},"repo_name":{"type":"string"}},"required":["repo_path"]}}},
    {"type":"function","function":{"name":"configure_runtime_status_feed","description":"Configure a real sanitized public Myles runtime status feed for a dashboard repository. Use this when the owner asks a public dashboard to show live/real Myles task state. It writes status.json, publishes it under the dedicated JoshuaDuskin GitHub identity, and registers background push-on-change updates. Call this only after the dashboard files exist.","parameters":{"type":"object","properties":{"repo_path":{"type":"string"},"repo_name":{"type":"string"},"min_update_seconds":{"type":"integer","minimum":15,"maximum":300}},"required":["repo_path"]}}},
    {"type":"function","function":{"name":"git_command","description":"Run git in a repository.","parameters":{"type":"object","properties":{"repo_path":{"type":"string"},"args":{"type":"string"},"timeout_seconds":{"type":"integer"}},"required":["repo_path","args"]}}},
    {"type":"function","function":{"name":"install_python_packages","description":"Install Python packages into the Myles Python environment when a task needs them.","parameters":{"type":"object","properties":{"packages":{"type":"array","items":{"type":"string"}}},"required":["packages"]}}},
    {"type":"function","function":{"name":"system_status","description":"Read live tower time, machine, CPU, memory, disk and Ollama status.","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"browser_automation","description":"Automate a website using a persistent Chromium profile. It self-provisions Playwright/Chromium if needed. Do not bypass authentication or MFA; surface an owner gate when manual authentication is required.","parameters":{"type":"object","properties":{"url":{"type":"string"},"actions":{"type":"array","items":{"type":"object"}},"headless":{"type":"boolean"}},"required":["url","actions"]}}},
    {"type":"function","function":{"name":"notify_owner","description":"Send the owner a proactive message through the configured remote Myles channel (Telegram when configured).","parameters":{"type":"object","properties":{"message":{"type":"string"}},"required":["message"]}}},
    {"type":"function","function":{"name":"self_clone_candidate","description":"Create a safe candidate copy of Myles source before changing Myles himself.","parameters":{"type":"object","properties":{"description":{"type":"string"}}}}},
    {"type":"function","function":{"name":"self_verify_candidate","description":"Compile and run the self-test for a candidate Myles build.","parameters":{"type":"object","properties":{"candidate_path":{"type":"string"}},"required":["candidate_path"]}}},
    {"type":"function","function":{"name":"self_promote_candidate","description":"Promote a verified self-update candidate with automatic rollback backup and request a core restart.","parameters":{"type":"object","properties":{"candidate_path":{"type":"string"}},"required":["candidate_path"]}}},
]

SYSTEM = """You are Myles, the owner's local autonomous home/work AI running on his Windows tower.

Your job is to DO requested work with local tools, not merely describe how the owner could do it.
You have explicit owner authorization to use the tower's filesystem, PowerShell, Git, network, downloads, package managers, browser automation, and local development tools for ordinary owner-requested work.
Install dependencies when they are genuinely needed. Build applications and files in the job workspace unless the owner identifies another project path.
This tower uses Windows PowerShell 5.1 for run_powershell. Never use Bash/cmd boolean operators && or || there. Use separate PowerShell statements, $LASTEXITCODE checks, or the narrower git_command tool for Git operations.
Do not start local development/test servers on 0.0.0.0 or expose inbound LAN ports unless the owner explicitly requested LAN access. Prefer 127.0.0.1 for local previews. Public hosting should use outbound deployment APIs/CLIs rather than opening the tower to inbound traffic.
Never invent a GitHub account, organization, repository, or remote. A configured git remote is not proof that the remote repository exists. For static GitHub hosting, prefer github_pages_publish; it discovers the actually authenticated GitHub identity, creates/retargets the repository, pushes the correct branch, configures Pages, and verifies the public URL. If authentication is genuinely missing, surface the exact owner auth gate instead of looping.
Use evidence. Never claim you executed, changed, tested, downloaded, built, fixed, or completed something unless a tool result proves it.
If a tool fails, inspect the error and try a sensible repair. Do not treat an ordinary tool failure as an owner gate.
Authentication, MFA/2FA, legal consent, payments, and other steps that genuinely require the owner are owner gates; clearly say exactly what is needed.
Avoid irreversible/destructive actions unless the owner explicitly requested them. Preserve recoverable backups before self-updates or risky file replacement.
PineTree is a permanent protected boundary. Never read, inspect, modify, deploy, authenticate to, publish to, clone, fetch, push, browse, or otherwise touch anything PineTree-related, even if a future prompt asks you to. The tool layer will reject it.
Conversation and owner controls must not stop background work. Telegram and the optional local console are only interfaces to this same core. The owner should never need command syntax to talk to Myles.
Use ordinary conversational context. A question, explanation, complaint, or follow-up does not automatically request a new task. When a request is genuinely actionable, choose the smallest appropriate tool path; use web search for current public facts, local tools for tower/project work, and download/install tools only when the requested work actually needs them. Ask the owner only for authentication, MFA, consent, or a risky irreversible choice.

SELF-DEVELOPMENT:
If the owner asks you to improve or extend Myles himself, use self_clone_candidate first. Work only in that candidate, verify it with self_verify_candidate, and promote only a passing candidate with self_promote_candidate. Never live-edit the only running copy as the first step.

STATUS TRUTH:
RUNNING means the worker really exists and is producing fresh heartbeats. Completion means verified output exists. Do not say you are still working after this worker has ended.
For every background action job, you MUST use at least one real execution tool before giving a final answer. A text-only promise such as "I will build it", "let me start", or "I am working on it" is not work and must never be treated as completion.

LIVE/PUBLIC DASHBOARD TRUTH:
If the owner asks a public dashboard to show real/live Myles runtime or job state, static mock JavaScript is forbidden. Never use Math.random(), mock runtime objects, demo/sample/simulated task data, or comments claiming a fake structure represents live data. Build the page against a real sanitized data source and use configure_runtime_status_feed after the dashboard files exist. The public page should fetch the returned RAW_STATUS_URL (with cache-busting) rather than trying to call localhost from the owner's phone.

CONTINUOUS GITHUB POLICY: remote GitHub mutation is technically blocked for continuous jobs. Build/test locally; never create or publish dashboard/status repositories.\n\nThe current job workspace and recovery context are supplied below.

V9 EXECUTION CONTRACT:
The model decides WHAT action is needed; the runtime owns HOW actions are serialized, retried, persisted, resumed, and verified.
Prefer write_generated_file for creating HTML/code/scripts/documents or any large text file. Never stuff an entire large file into a JSON tool argument.
Provider-specific integrations belong in capability plugins. Use capability_status to inspect installed capabilities instead of inventing a provider API.
Malformed tool output, temporary network errors, timeouts, and ordinary command failures are internal recovery events, not owner gates.
Only authentication/MFA/consent that genuinely requires the owner may become an owner gate.
"""


SUMMARY_SYSTEM = """You are Myles writing the owner-facing result of completed work.
Rewrite the supplied worker result as one concise, natural summary in first person.
Use 1-4 short sentences or at most 4 compact bullets. State only verified work and results.
Do not mention execution bridge logs, internal tools, controller messages, previous context,
workspace details, phases, job IDs, model reasoning, prompts, JSON, or the phrase 'final deliverable'.
Do not paste raw logs, code, or large file contents. If an explicit path or URL is present,
preserve it briefly; never invent one. If completion is not actually verified, say that plainly.
Do not promise another report or say 'I'll message you when verified' after completion.
"""


def heartbeat(job_id: str, stop: threading.Event) -> None:
    while not stop.wait(10):
        try:
            set_job(job_id, heartbeat_at=now_iso())
        except Exception:
            pass


def call_ollama(job_id: str, messages: list[dict]) -> dict:
    cfg = load_config()
    last_error: Exception | None = None
    for attempt in range(1, 4):
        body = json.dumps({
            "model": cfg["model"],
            "messages": messages,
            "stream": False,
            "think": False,
            "tools": _all_tool_defs(),
            "options": {"temperature": 0.25},
            "keep_alive": "10m",
        }).encode("utf-8")
        req = urllib.request.Request(
            cfg["ollama_url"],
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        set_job(job_id, phase="model", heartbeat_at=now_iso())
        try:
            with urllib.request.urlopen(req, timeout=int(cfg["model_timeout_seconds"])) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
            trace(job_id, "model.retry", f"attempt={attempt} {type(exc).__name__}: {exc}"[:12000], ok=False)
            if attempt < 3:
                time.sleep(2 * attempt)
    raise RuntimeError(f"Local model call failed after internal retries: {type(last_error).__name__}: {last_error}")


def _needs_owner_summary(text: str) -> bool:
    low = str(text or "").lower()
    markers = (
        "execution bridge", "previous context", "final deliverable", "tool call",
        "controller", "completion check", "workspace", "internal log", "raw log",
        "current task:", "owner-locked", "v9 execution contract", "heartbeat age",
    )
    return len(text or "") > 700 or any(marker in low for marker in markers)


def compact_owner_summary(job_id: str, prompt: str, result: str) -> str:
    """Keep internal execution detail out of the owner conversation."""
    source = str(result or "").strip()
    if not source or not _needs_owner_summary(source):
        return source[:1200]
    cfg = load_config()
    messages = [
        {"role": "system", "content": SUMMARY_SYSTEM},
        {"role": "user", "content": f"OWNER REQUEST:\n{str(prompt)[:5000]}\n\nWORKER RESULT:\n{source[:12000]}"},
    ]
    body = json.dumps({
        "model": cfg["model"], "messages": messages, "stream": False,
        "think": False, "options": {"temperature": 0.15}, "keep_alive": "10m",
    }).encode("utf-8")
    req = urllib.request.Request(
        cfg["ollama_url"], data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=min(90, int(cfg["model_timeout_seconds"]))) as response:
            data = json.loads(response.read().decode("utf-8"))
        summary = clean_model_text(str((data.get("message") or {}).get("content") or "")).strip()
        if summary:
            trace(job_id, "owner.summary_compacted", summary[:12000])
            return summary[:1600]
    except Exception as exc:
        trace(job_id, "owner.summary_fallback", f"{type(exc).__name__}: {exc}"[:12000], ok=False)
    cleaned = re.sub(r"(?is)^(based on .*?(?:logs|context).*?:\s*)", "", source).strip()
    cleaned = re.sub(r"(?im)^\s*(execution bridge|previous context|final deliverable|completion check).*?$", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned[:1200]


def _all_tool_defs() -> list[dict]:
    return TOOL_DEFS + capabilities.tool_definitions()

def _tool_names() -> list[str]:
    return [d["function"]["name"] for d in _all_tool_defs()]

TOOL_NAMES = [d["function"]["name"] for d in TOOL_DEFS]

TOOL_ARGUMENT_GUIDE = """
run_powershell: {"command": string, "timeout_seconds": integer optional}
read_text_file: {"path": string, "max_chars": integer optional}
write_text_file: {"path": string, "content": string, "append": boolean optional}  # small content only
write_generated_file: {"path": string, "instructions": string, "append": boolean optional, "max_chars": integer optional}
apply_text_patch: {"path": string, "old_text": string, "new_text": string, "count": integer optional}
capability_status: {}
list_directory: {"path": string, "recursive": boolean optional, "max_items": integer optional}
download_file: {"url": string, "destination": string}
web_fetch: {"url": string, "max_chars": integer optional}
web_search: {"query": string, "max_results": integer optional}
tool_inventory: {}
git_command: {"repo_path": string, "args": string, "timeout_seconds": integer optional}
github_pages_publish: {"repo_path": string, "repo_name": string optional}
install_python_packages: {"packages": [string, ...]}
system_status: {}
browser_automation: {"url": string, "actions": [object, ...], "headless": boolean optional}
notify_owner: {"message": string}
self_clone_candidate: {"description": string optional}
self_verify_candidate: {"candidate_path": string}
self_promote_candidate: {"candidate_path": string}
"""


def call_execution_bridge(job_id: str, job_prompt: str, workspace: Path, last_text: str, recent_messages: list[dict]) -> tuple[str, dict]:
    """Choose one compact concrete action when native tool calling is absent.

    The fallback action planner never needs to carry a large file body. For
    code/HTML/document creation it should choose write_generated_file and pass
    only concise generation instructions. Malformed planner output is retried
    internally instead of failing the owner job.
    """
    cfg = load_config()
    recent = []
    for m in recent_messages[-10:]:
        role = str(m.get("role") or "")
        content = str(m.get("content") or "")
        if content:
            recent.append(f"{role.upper()}: {content[:3500]}")

    allowed = set(_tool_names())
    retries = max(2, min(int(cfg.get("planner_retry_count", 3)), 6))
    last_error = ""

    for attempt in range(1, retries + 1):
        prompt = f"""You are the compact action planner for Myles on the owner's Windows tower.

OWNER TASK:
{job_prompt}

JOB WORKSPACE:
{workspace}

LAST AGENT TEXT:
{last_text[:6000]}

RECENT EXECUTION CONTEXT:
{chr(10).join(recent)[-12000:]}

Choose exactly ONE concrete tool action that makes progress now.
Return ONE JSON object only. No prose, Markdown, code fences, or commentary.
NEVER put a whole HTML/code/script/document body inside JSON.
For creating or replacing substantial files, choose write_generated_file and put only concise instructions in arguments.instructions.
For small exact edits, choose apply_text_patch.
For provider-specific systems such as Ring, health/weight sources, or home automation, use capability_status if the needed capability is not obvious.
Authentication/MFA is the only normal reason to involve the owner.
PineTree is permanently off-limits.

Allowed tools: {', '.join(sorted(allowed))}
Argument shapes:
{TOOL_ARGUMENT_GUIDE}

Required shape:
{{"tool":"one_allowed_tool_name","arguments":{{...}}}}

Attempt {attempt}/{retries}. Previous parser issue: {last_error or 'none'}.
"""
        body = json.dumps({
            "model": cfg["model"],
            "messages": [{"role": "system", "content": prompt}],
            "stream": False,
            "think": False,
            "format": "json",
            "options": {"temperature": 0.0},
            "keep_alive": "10m",
        }).encode("utf-8")
        req = urllib.request.Request(
            cfg["ollama_url"], data=body, method="POST", headers={"Content-Type": "application/json"}
        )
        set_job(job_id, phase="action_planner", heartbeat_at=now_iso())
        try:
            with urllib.request.urlopen(req, timeout=int(cfg["model_timeout_seconds"])) as r:
                data = json.loads(r.read().decode("utf-8"))
            raw = clean_model_text(str((data.get("message") or {}).get("content") or ""))
            name, args = normalize_action_plan(raw, allowed)

            if name == "write_text_file" and len(str(args.get("content") or "")) > 1000:
                path = str(args.get("path") or "")
                excerpt = str(args.get("content") or "")[:900]
                name = "write_generated_file"
                args = {
                    "path": path,
                    "instructions": (
                        "Create the complete artifact the agent intended. The original attempted "
                        "content began with this excerpt; reproduce the intended result faithfully "
                        "without Markdown fences:\\n" + excerpt
                    ),
                    "append": bool(args.get("append", False)),
                }

            trace(job_id, "action_planner.plan", json.dumps({"tool": name, "arguments": args})[:12000], tool=name)
            return name, args
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            trace(job_id, "action_planner.retry", f"attempt={attempt} {last_error}"[:12000], ok=False)

    raise PlannerParseError(f"compact action planner failed after {retries} internal retries: {last_error}")


def _looks_like_unfinished_promise(text: str) -> bool:
    t = str(text or "").strip().lower()
    markers = (
        "i'll ", "i will ", "let me ", "i'm going to ", "i am going to ",
        "now i need to", "next i need to", "next, i", "i need to create",
        "i need to write", "i need to set up", "i need to setup", "start by ",
        "then i'll ", "then i will ", "working on it", "i'm working on",
    )
    return any(m in t for m in markers)


def _task_requires_mutation(prompt: str) -> bool:
    t = str(prompt or "").lower()
    words = (
        "build", "create", "make", "write", "edit", "modify", "change", "fix",
        "repair", "install", "download", "set up", "setup", "deploy", "host",
        "publish", "delete", "remove", "move", "rename", "update", "upgrade",
        "configure", "add ", "implement", "code ",
    )
    return any(w in t for w in words)


def _prompt_requires_artifact(prompt: str) -> bool:
    t = str(prompt or "").lower()
    build_words = ("build", "create", "make", "write", "implement", "code", "generate")
    artifact_words = (
        "dashboard", "website", "web interface", "web page", "html", "css", "javascript",
        "script", "app", "application", "file", "document", "report", "project", "page",
    )
    return any(w in t for w in build_words) and any(w in t for w in artifact_words)


def _prompt_requires_public_url(prompt: str) -> bool:
    t = str(prompt or "").lower()
    return any(w in t for w in (
        "host", "hosting", "deploy", "publish", "public url", "provide the url",
        "give me the url", "free domain", "domain", "on the internet", "github pages",
        "netlify", "vercel", "accessible via url",
    ))


def _prompt_is_static_web_task(prompt: str) -> bool:
    t = str(prompt or "").lower()
    return any(w in t for w in ("dashboard", "website", "web interface", "web page", "html"))


def _workspace_artifacts(workspace: Path) -> list[Path]:
    out: list[Path] = []
    try:
        for path in workspace.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(workspace)
            parts = {part.lower() for part in rel.parts}
            if ".git" in parts or "__pycache__" in parts:
                continue
            if path.name.startswith("."):
                continue
            try:
                if path.stat().st_size <= 0:
                    continue
            except OSError:
                continue
            out.append(path)
    except Exception:
        pass
    return out


def _clean_url_candidate(raw: str) -> str:
    url = str(raw or "").strip()
    # Model prose often wraps URLs in Markdown bold/backticks or punctuation.
    url = url.lstrip("`*_~<([{")
    url = url.rstrip("`*_~.,;:!?)\\]}>\"'")
    return url

def _extract_http_urls(text: str) -> list[str]:
    source = str(text or "")
    found: list[str] = []

    # Prefer Markdown-link targets when present.
    for match in re.findall(r"\[[^\]]*\]\((https?://[^)\s]+)\)", source, flags=re.I):
        found.append(match)

    # Also collect bare URLs, then normalize common Markdown punctuation.
    found.extend(re.findall(r"https?://[^\s<>\"']+", source, flags=re.I))

    cleaned: list[str] = []
    for raw in found:
        url = _clean_url_candidate(raw)
        if url and url not in cleaned:
            cleaned.append(url)
    return cleaned

def _verified_public_url_from_traces(job_id: str) -> str:
    """Return a URL already proven reachable by a successful publish tool."""
    for row in traces_for_job(job_id, 120):
        if str(row.get("tool") or "") != "github_pages_publish":
            continue
        if int(row.get("ok") or 0) != 1:
            continue
        detail = str(row.get("detail") or "")
        m_url = re.search(r"(?m)^PUBLIC_URL=(https?://\S+)\s*$", detail)
        m_status = re.search(r"(?m)^HTTP_STATUS=(\d{3})\s*$", detail)
        if not m_url or not m_status:
            continue
        status = int(m_status.group(1))
        if 200 <= status < 400:
            return _clean_url_candidate(m_url.group(1))
    return ""

def _augment_final_with_verified_evidence(job_id: str, prompt: str, text: str) -> str:
    result = clean_model_text(text)
    if _prompt_requires_public_url(prompt) and not _extract_http_urls(result):
        verified = _verified_public_url_from_traces(job_id)
        if verified:
            result = (result.rstrip() + f"\n\nPublic URL: {verified}").strip()
    return result

def _prompt_explicitly_forbids_fake_data(prompt: str) -> bool:
    t = str(prompt or "").lower()
    return any(marker in t for marker in (
        "no sample", "no fake", "no placeholder", "not sample",
        "not fake", "not placeholder", "real runtime", "real myles",
        "real current", "real job state",
    ))

FAKE_ARTIFACT_MARKERS = (
    "simulated real-time", "simulated realtime", "simulate the fetch",
    "simulate the data", "simulating", "simulation", "sample project",
    "sample data", "demo data", "demonstration data", "project a", "project b",
    "placeholder percentage", "placeholder data", "fake data", "mock data",
    "mock runtime", "mockresponse", "getmockruntimestate", "getmock",
    "math.random(", "for demonstration", "would hit the internal api",
    "would hit the actual endpoint", "in a real myles environment",
    "since we are generating static content",
)

def _fake_markers_in_text(text: str) -> list[str]:
    low = str(text or "").lower()
    return [marker for marker in FAKE_ARTIFACT_MARKERS if marker in low]

def _obvious_fake_artifact_evidence(artifacts: list[Path]) -> list[str]:
    hits: list[str] = []
    for path in artifacts:
        if path.suffix.lower() not in {".html", ".htm", ".js", ".json", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        markers = _fake_markers_in_text(text)
        if markers:
            hits.append(f"{path.name}:{markers[0]}")
    return hits

def _prompt_requires_live_runtime_data(prompt: str) -> bool:
    t = str(prompt or "").lower()
    return any(marker in t for marker in (
        "real runtime", "real myles", "real job state", "real current",
        "live myles", "live runtime", "real-time myles", "realtime myles",
        "real-time runtime", "realtime runtime", "live dashboard",
        "auto-refresh", "auto refresh",
    ))

def _successful_runtime_status_feed(job_id: str) -> str:
    for row in traces_for_job(job_id, 160):
        if str(row.get("tool") or "") != "configure_runtime_status_feed":
            continue
        if int(row.get("ok") or 0) != 1:
            continue
        detail = str(row.get("detail") or "")
        m = re.search(r"(?m)^RAW_STATUS_URL=(https?://\S+)\s*$", detail)
        if m:
            return _clean_url_candidate(m.group(1))
    return ""

def _artifact_has_real_live_source(artifacts: list[Path]) -> bool:
    for path in artifacts:
        if path.suffix.lower() not in {".html", ".htm", ".js"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        low = text.lower()
        # A public dashboard must actually fetch/stream data. Merely defining a
        # function named fetchStatus is not evidence.
        if re.search(r"\bfetch\s*\(", text, flags=re.I) or "new eventsource(" in low or "new websocket(" in low:
            if "localhost" not in low and "127.0.0.1" not in low:
                return True
    return False

def _artifact_references_status_feed(artifacts: list[Path], feed_url: str) -> bool:
    target = str(feed_url or "").strip()
    if not target:
        return False
    for path in artifacts:
        if path.suffix.lower() not in {".html", ".htm", ".js", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if target in text:
            return True
    return False

def _verify_public_page_contract(job_id: str, url: str, prompt: str) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": "Myles-PublicArtifactVerifier/9.3.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read(250000)
            status = int(getattr(r, "status", 200) or 200)
            ctype = str(r.headers.get("Content-Type", ""))
        text = raw.decode("utf-8", errors="replace")
        if not (200 <= status < 400):
            return False, f"public page returned HTTP {status}"
        if _prompt_explicitly_forbids_fake_data(prompt):
            markers = _fake_markers_in_text(text)
            if markers:
                detail = "public page still contains fake/sample/simulated logic: " + ", ".join(markers[:6])
                trace(job_id, "completion.public_contract", detail, tool="http_verify", ok=False)
                return False, detail
        if _prompt_requires_live_runtime_data(prompt):
            low = text.lower()
            if not (re.search(r"\bfetch\s*\(", text, flags=re.I) or "new eventsource(" in low or "new websocket(" in low):
                detail = "public page does not contain a real network data binding for live runtime state"
                trace(job_id, "completion.public_contract", detail, tool="http_verify", ok=False)
                return False, detail
            if "localhost" in low or "127.0.0.1" in low:
                detail = "public page attempts to use localhost for live data, which cannot work from the owner's phone"
                trace(job_id, "completion.public_contract", detail, tool="http_verify", ok=False)
                return False, detail
            feed_url = _successful_runtime_status_feed(job_id)
            if feed_url and feed_url not in text:
                detail = "public page is not bound to the verified sanitized Myles runtime status feed"
                trace(job_id, "completion.public_contract", detail, tool="http_verify", ok=False)
                return False, detail
        trace(job_id, "completion.public_contract", f"url={url} status={status} content_type={ctype}", tool="http_verify", ok=True)
        return True, f"url={url} status={status}"
    except Exception as exc:
        detail = f"public page contract check failed: {type(exc).__name__}: {exc}"
        trace(job_id, "completion.public_contract", detail, tool="http_verify", ok=False)
        return False, detail


def _verify_public_url(job_id: str, url: str) -> tuple[bool, str]:
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False, "not a valid public HTTP(S) URL"
        host = (parsed.hostname or "").lower()
        if host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"} or host.endswith(".local"):
            return False, "URL is local-only, not a public deployment"
        req = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": "Myles-CompletionVerifier/8.3.5"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            status = int(getattr(r, "status", 200) or 200)
            final_url = str(getattr(r, "url", url) or url)
            ok = 200 <= status < 400
            detail = f"url={url} status={status} final_url={final_url}"
            trace(job_id, "completion.url_verify", detail, tool="http_verify", ok=ok)
            return ok, detail
    except Exception as exc:
        detail = f"url={url} error={type(exc).__name__}: {exc}"
        trace(job_id, "completion.url_verify", detail, tool="http_verify", ok=False)
        return False, detail


def _looks_truncated(text: str) -> bool:
    t = str(text or "").strip().lower()
    if not t:
        return True
    tails = (" at", " at:", " to", " with", " for", " and", " or", " because", " then", ":")
    return any(t.endswith(x) for x in tails)


def completion_gaps(job_id: str, prompt: str, workspace: Path, final_text: str) -> list[str]:
    """Deterministic acceptance checks before a job may become COMPLETED.

    Tool success proves activity, not completion. This verifier combines workspace
    evidence, already-verified tool results, and the owner's explicit anti-fake
    constraints before allowing a terminal success.
    """
    gaps: list[str] = []
    text = clean_model_text(final_text)

    if not text:
        gaps.append("final answer is empty")
    if _looks_like_unfinished_promise(text):
        gaps.append("final answer still describes future work instead of a completed result")
    if _looks_truncated(text):
        gaps.append("final answer appears truncated/incomplete")

    artifacts = _workspace_artifacts(workspace)
    if _prompt_requires_artifact(prompt) and not artifacts:
        gaps.append("requested artifact is missing from the job workspace")

    if _prompt_explicitly_forbids_fake_data(prompt) and artifacts:
        fake_hits = _obvious_fake_artifact_evidence(artifacts)
        if fake_hits:
            gaps.append(
                "artifact contains obvious sample/simulated/placeholder data despite the owner requiring real data: "
                + ", ".join(fake_hits[:8])
            )

    if _prompt_requires_live_runtime_data(prompt):
        if not _artifact_has_real_live_source(artifacts):
            gaps.append("live runtime dashboard has no real non-local network data binding")
        if _prompt_requires_public_url(prompt):
            feed_url = _successful_runtime_status_feed(job_id)
            if not feed_url:
                gaps.append("public live Myles dashboard has no verified sanitized runtime status feed")
            elif not _artifact_references_status_feed(artifacts, feed_url):
                gaps.append("dashboard artifact does not reference the verified sanitized runtime status feed URL")

    if _prompt_requires_public_url(prompt):
        if _prompt_is_static_web_task(prompt):
            names = {p.name.lower() for p in artifacts}
            has_web_entry = "index.html" in names or "package.json" in names
            if not has_web_entry:
                gaps.append("hosted web task has no deployable entrypoint (index.html or package.json) in the workspace")

        # A successful publisher result with HTTP_STATUS=2xx/3xx is stronger
        # evidence than model prose. Reuse it instead of forcing the model to
        # restate a URL perfectly on every step.
        proven = _verified_public_url_from_traces(job_id)
        verified_url = ""
        if proven:
            verified_url = proven
        else:
            urls = _extract_http_urls(text)
            if not urls:
                gaps.append("task requires hosting/public access but no verified public HTTP(S) URL exists")
            else:
                failures: list[str] = []
                for url in urls[:4]:
                    ok, detail = _verify_public_url(job_id, url)
                    if ok:
                        verified_url = url
                        break
                    failures.append(detail)
                if not verified_url:
                    gaps.append("no public URL passed an HTTP reachability check: " + " | ".join(failures)[:1800])

        if verified_url and (_prompt_explicitly_forbids_fake_data(prompt) or _prompt_requires_live_runtime_data(prompt)):
            ok, detail = _verify_public_page_contract(job_id, verified_url, prompt)
            if not ok:
                gaps.append(detail)

    return gaps


# MYLES_REMOTE_GITHUB_HARD_LOCK_v3
LEGACY_MYLES_REPOS = {
    "myles-controlcenter", "myleslivestatus", "m83-dashboard", "my-dashboard",
    "progress-dashboard", "myles-dashboard", "myles-ai-dashboard", "myles-ecosystem",
}


# MYLES_DUPLICATE_REPOSITORY_HARD_BLOCK_v4
_CANONICAL_MYLES_REPOS = {
    "joshuaduskin/mylesdashboard",
    "joshuaduskin/trading-dashboard",
}
_DASHBOARD_REPO_WORDS = (
    "dashboard", "controlcenter", "control-center", "control_center",
    "progress", "runtime-status", "runtime_status", "livestatus", "live-status",
    "status-dashboard", "status_dashboard", "ecosystem",
)

def _looks_like_duplicate_myles_repo_creation(name: str, args: dict) -> bool:
    lname=str(name or "").strip().lower()
    try: payload=json.dumps(args or {},ensure_ascii=False).lower()
    except Exception: payload=str(args or {}).lower()
    normalized=payload.replace(".git","")
    if any(canon in normalized for canon in _CANONICAL_MYLES_REPOS): return False
    has_myles="myles" in payload
    dashboardish=any(word in payload for word in _DASHBOARD_REPO_WORDS)
    if lname=="run_powershell":
        cmd=str((args or {}).get("command") or "").lower()
        creates=bool(re.search(r"\b(gh\s+repo\s+create|git\s+init|git\s+clone)\b",cmd,flags=re.I))
        return creates and ("myles" in cmd) and any(word in cmd for word in _DASHBOARD_REPO_WORDS)
    if "github" in lname and any(x in lname for x in ("create","new","fork","publish")):
        return has_myles and dashboardish
    if lname=="github_pages_publish": return has_myles and dashboardish
    return False

def _owner_repo_policy_refusal(job_id: str, name: str, args: dict) -> str | None:
    try:
        job = get_job(job_id) or {}
    except Exception:
        job = {}
    source = str(job.get("source") or "").strip().lower()
    lname = str(name or "").strip().lower()

    if _looks_like_duplicate_myles_repo_creation(name, args):
        return (
            "TOOL_REFUSED CANONICAL_REPO_POLICY: duplicate Myles dashboard/status repositories are forbidden. "
            "Use JoshuaDuskin/MylesDashboard for the owner UI, JoshuaDuskin/trading-dashboard for Quant source, "
            "and the authenticated tower bridge for live state."
        )
    try:
        payload = json.dumps(args or {}, ensure_ascii=False).lower()
    except Exception:
        payload = str(args or {}).lower()

    legacy_ref = any(repo in payload for repo in LEGACY_MYLES_REPOS)
    is_remote_mutator = (
        lname == "github_pages_publish"
        or ("github" in lname and not any(read in lname for read in ("read", "get", "fetch", "search", "status", "list", "inventory")))
    )

    if legacy_ref and (is_remote_mutator or lname == "run_powershell" or "browser" in lname):
        return "TOOL_REFUSED OWNER_REPO_LOCK: legacy Myles dashboard/status repositories are retired and read-only."

    if source != "continuous":
        return None

    if lname == "github_pages_publish":
        return "TOOL_REFUSED OWNER_REPO_LOCK: continuous jobs cannot publish GitHub Pages or create/update dashboard repositories."

    if "github" in lname and not any(read in lname for read in ("read", "get", "fetch", "search", "status", "list", "inventory")):
        return "TOOL_REFUSED OWNER_REPO_LOCK: continuous jobs cannot mutate GitHub."

    if "browser" in lname and ("github.com" in payload or "github" in payload):
        return "TOOL_REFUSED OWNER_REPO_LOCK: continuous jobs cannot automate GitHub mutations in a browser."

    if lname == "run_powershell":
        command = str((args or {}).get("command") or "")
        patterns = (
            r"\bgit\s+push\b",
            r"\bgit\s+remote\s+set-url\b",
            r"\bgh\s+repo\s+(create|delete|archive|rename|fork)\b",
            r"\bgh\s+api\b.*(?:-x|--method)\s*(post|put|patch|delete)\b",
            r"api\.github\.com.*\b(post|put|patch|delete)\b",
        )
        if any(re.search(p, command, flags=re.I | re.S) for p in patterns):
            return "TOOL_REFUSED OWNER_REPO_LOCK: continuous jobs cannot perform remote Git/GitHub mutations."

    return None


def execute_tool(job_id: str, name: str, args: dict) -> str:
    set_job(job_id, phase=f"tool:{name}", heartbeat_at=now_iso())
    policy_refusal = _owner_repo_policy_refusal(job_id, name, args)
    if policy_refusal:
        trace(job_id, "tool.refused", policy_refusal, tool=name, ok=False)
        return policy_refusal
    try:
        if getattr(tools, "_contains_pinetree_reference")(args):
            refused = getattr(tools, "_pinetree_refusal")(name, "tool arguments contain a protected PineTree reference")
            trace(job_id, "tool.refused", refused, tool=name, ok=False)
            return refused
    except Exception:
        pass

    if name == "tool_inventory":
        inventory = []
        for definition in _all_tool_defs():
            fn_info = definition.get("function") or {}
            inventory.append({
                "name": str(fn_info.get("name") or ""),
                "description": str(fn_info.get("description") or ""),
            })
        out = json.dumps({"version": load_config().get("version"), "tools": inventory}, indent=2)
        trace(job_id, "tool.result", out[:20000], tool=name, ok=True)
        return out

    if name == "capability_status":
        out = capabilities.status_json()
        trace(job_id, "tool.result", out[:12000], tool=name, ok=True)
        return out

    fn = getattr(tools, name, None)
    if not fn:
        plugin_result = capabilities.execute(name, job_id, args)
        if plugin_result is not None:
            trace(job_id, "tool.result", str(plugin_result)[:12000], tool=name, ok=True)
            return str(plugin_result)
        return f"TOOL_ERROR: unknown tool {name}"
    try:
        return str(fn(job_id=job_id, **args))
    except TypeError:
        try:
            return str(fn(job_id))
        except Exception as exc:
            return f"TOOL_ERROR {type(exc).__name__}: {exc}"
    except Exception as exc:
        trace(job_id, "tool.result", f"{type(exc).__name__}: {exc}", tool=name, ok=False)
        return f"TOOL_ERROR {type(exc).__name__}: {exc}"


SAFE_INTERNAL_RETRY_TOOLS = {
    "web_fetch",
    "web_search",
    "system_status",
    "capability_status",
    "download_file",
    "github_pages_publish",
}

def execute_with_internal_retry(job_id: str, name: str, args: dict) -> tuple[str, Any]:
    """Execute one tool action and internally retry safe transient failures.

    Non-idempotent arbitrary shell/browser actions are never blindly replayed.
    """
    cfg = load_config()
    attempts = max(1, min(int(cfg.get("internal_retry_budget", 3)), 3))
    result = ""
    outcome = None

    for attempt in range(1, attempts + 1):
        result = execute_tool(job_id, name, args)
        outcome = classify_tool_result(result)

        if outcome.ok or outcome.owner_gate or outcome.refused:
            return result, outcome

        if not outcome.retryable or name not in SAFE_INTERNAL_RETRY_TOOLS or attempt >= attempts:
            return result, outcome

        trace(
            job_id,
            "tool.internal_retry",
            f"tool={name} attempt={attempt}/{attempts} kind={outcome.kind}"[:12000],
            tool=name,
            ok=False,
        )
        time.sleep(min(2 * attempt, 5))

    return result, outcome


def unload_model() -> None:
    cfg = load_config()
    try:
        subprocess.run(
            ["ollama", "stop", cfg["model"]],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        pass


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    job_id = sys.argv[1]
    init_db()
    job = get_job(job_id)
    if not job:
        return 3

    workspace = Path(job["workspace"])
    workspace.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()
    recovery_count = int(job.get("recovery_count") or 0)
    set_job(
        job_id,
        state="running",
        phase="starting",
        runner_pid=pid,
        started_at=now_iso(),
        heartbeat_at=now_iso(),
        error=None,
    )
    trace(job_id, "worker.started", f"pid={pid} recovery_count={recovery_count}")

    stop = threading.Event()
    hb = threading.Thread(target=heartbeat, args=(job_id, stop), daemon=True)
    hb.start()

    previous = traces_for_job(job_id, 12)
    recovery_note = ""
    if recovery_count:
        recovery_note = (
            f"\nRECOVERY #{recovery_count}: Continue this same owner job from the most advanced verified "
            f"state already present in {workspace}. Do not restart completed work. Inspect existing files/evidence first.\n"
        )

    context = (
        SYSTEM
        + f"\nJOB_ID: {job_id}\n"
        + f"WORKSPACE: {workspace}\n"
        + f"MYLES_ROOT: {ROOT}\n"
        + f"LEGACY_MYLES_ROOT: {load_config().get('legacy_myles_root','')}\n"
        + recovery_note
        + "\nRECENT JOB EVIDENCE:\n"
        + json.dumps(previous, indent=2)[-12000:]
    )

    messages = [{"role": "system", "content": context}]
    messages.extend(history_for_model(18))
    if not messages or messages[-1].get("content") != job["prompt"]:
        messages.append({"role": "user", "content": job["prompt"]})

    try:
        final = ""
        tool_calls_made = 0
        tool_calls_succeeded = 0
        mutating_tool_succeeded = 0
        bridge_calls = 0
        cfg = load_config()
        for step in range(1, int(cfg["max_agent_steps"]) + 1):
            set_job(job_id, phase="model", heartbeat_at=now_iso())
            trace(job_id, "agent.step", f"{step}/{cfg['max_agent_steps']}")
            data = call_ollama(job_id, messages)
            msg = data.get("message") or {}
            content = clean_model_text(str(msg.get("content") or ""))
            calls = msg.get("tool_calls") or []

            assistant_msg = {"role": "assistant", "content": content}
            if calls:
                assistant_msg["tool_calls"] = calls
            messages.append(assistant_msg)

            if calls:
                for call in calls:
                    fn = call.get("function") or {}
                    name = str(fn.get("name") or "")
                    args = parse_native_arguments(fn.get("arguments") or {})
                    if name not in set(_tool_names()) or args is None:
                        trace(
                            job_id,
                            "native_tool.invalid",
                            json.dumps({"name": name, "arguments": fn.get("arguments")}, default=str)[:12000],
                            tool=name or None,
                            ok=False,
                        )
                        messages.append({
                            "role": "user",
                            "content": (
                                "Your previous native tool call was malformed or selected an unknown tool. "
                                "Retry with one valid tool call. Use write_generated_file for substantial file content."
                            ),
                        })
                        continue
                    trace(job_id, "tool.request", json.dumps({"name": name, "args": args})[:10000], tool=name)
                    result, outcome = execute_with_internal_retry(job_id, name, args)
                    if outcome.owner_gate:
                        message = str(result).split("OWNER_AUTH_REQUIRED:", 1)[1].strip()
                        set_job(job_id, state="blocked_auth", phase="awaiting_owner_auth", runner_pid=None, heartbeat_at=now_iso(), error=None, result=None)
                        trace(job_id, "job.blocked_auth", message[:12000])
                        source = job.get("source") or "desktop"
                        auth_text = "I need one authentication step from you before I can continue: " + message
                        add_message(source, "assistant", auth_text, job_id)
                        if source == "continuous" and load_config().get("telegram_enabled"):
                            add_message("telegram", "assistant", auth_text, job_id)
                        return 0
                    tool_calls_made += 1
                    ok = outcome.ok
                    if ok:
                        tool_calls_succeeded += 1
                        if name in {"run_powershell", "write_text_file", "write_generated_file", "apply_text_patch", "download_file", "git_command", "github_pages_publish", "configure_runtime_status_feed", "install_python_packages", "browser_automation", "self_clone_candidate", "self_promote_candidate"}:
                            mutating_tool_succeeded += 1
                    messages.append({"role": "tool", "content": result})
                continue

            if content:
                # Native tool calling is preferred, but a successful tool proves only activity.
                # Before accepting prose as the final answer, run deterministic acceptance checks
                # against the original owner request, workspace artifacts, and (when requested)
                # the actual public deployment URL.
                candidate = _augment_final_with_verified_evidence(
                    job_id,
                    job["prompt"],
                    clean_model_text(content),
                )
                gaps = completion_gaps(job_id, job["prompt"], workspace, candidate)
                needs_bridge = (
                    tool_calls_made == 0
                    or tool_calls_succeeded == 0
                    or bool(gaps)
                    or _looks_like_unfinished_promise(candidate)
                    or (_task_requires_mutation(job["prompt"]) and mutating_tool_succeeded == 0)
                )
                if needs_bridge:
                    bridge_calls += 1
                    if bridge_calls > int(cfg["max_agent_steps"]):
                        raise RuntimeError("Execution bridge exceeded the maximum action steps before completion criteria were satisfied.")
                    if gaps:
                        gap_text = "; ".join(gaps)
                        trace(job_id, "completion.rejected", gap_text[:12000], ok=False)
                    else:
                        gap_text = "native tool execution evidence is still insufficient"
                    trace(job_id, "agent.native_tool_missing", candidate[:10000])
                    bridge_input = candidate + "\n\nCOMPLETION CHECK FAILED: " + gap_text
                    try:
                        name, args = call_execution_bridge(job_id, job["prompt"], workspace, bridge_input, messages)
                    except PlannerParseError as exc:
                        trace(job_id, "action_planner.exhausted", str(exc)[:12000], ok=False)
                        messages.append({
                            "role": "user",
                            "content": (
                                "The compact action planner had an internal formatting failure. "
                                "Do not stop the owner job. Continue from existing evidence and emit one native tool call if possible. "
                                "For substantial files use write_generated_file instead of embedding file content in JSON."
                            ),
                        })
                        continue
                    result, outcome = execute_with_internal_retry(job_id, name, args)
                    if outcome.owner_gate:
                        message = str(result).split("OWNER_AUTH_REQUIRED:", 1)[1].strip()
                        set_job(job_id, state="blocked_auth", phase="awaiting_owner_auth", runner_pid=None, heartbeat_at=now_iso(), error=None, result=None)
                        trace(job_id, "job.blocked_auth", message[:12000])
                        source = job.get("source") or "desktop"
                        auth_text = "I need one authentication step from you before I can continue: " + message
                        add_message(source, "assistant", auth_text, job_id)
                        if source == "continuous" and load_config().get("telegram_enabled"):
                            add_message("telegram", "assistant", auth_text, job_id)
                        return 0
                    tool_calls_made += 1
                    ok = outcome.ok
                    if ok:
                        tool_calls_succeeded += 1
                        if name in {"run_powershell", "write_text_file", "write_generated_file", "apply_text_patch", "download_file", "git_command", "github_pages_publish", "configure_runtime_status_feed", "install_python_packages", "browser_automation", "self_clone_candidate", "self_promote_candidate"}:
                            mutating_tool_succeeded += 1
                    messages.append({
                        "role": "user",
                        "content": (
                            f"EXECUTION_BRIDGE actually ran tool {name}. Result follows:\n{result}\n"
                            f"Previous completion gaps: {gap_text}\n"
                            "Continue the same owner task from this verified evidence. "
                            "Do not declare completion until every requested deliverable is actually present and verifiable. "
                            "If hosting/deployment was requested, return the real public URL only after it is reachable."
                        ),
                    })
                    continue
                final = candidate
                trace(job_id, "completion.accepted", "deterministic completion criteria satisfied", ok=True)
                break

        if not final:
            # Hitting one execution slice limit is not the same as task failure. If real
            # progress exists, preserve the same workspace and automatically continue the
            # owner job instead of dropping it with an unhelpful RuntimeError.
            current = get_job(job_id) or job
            count = int(current.get("recovery_count") or 0) + 1
            max_recoveries = int(cfg.get("max_recoveries", 4))
            if count <= max_recoveries and (tool_calls_succeeded > 0 or current.get("material_progress_at")):
                set_job(
                    job_id,
                    state="pending",
                    phase="continuing_unverified",
                    runner_pid=None,
                    heartbeat_at=now_iso(),
                    recovery_count=count,
                    error=None,
                )
                trace(
                    job_id,
                    "job.continuation_queued",
                    f"Verified completion not reached in this execution slice; continuing automatically from existing workspace. continuation={count}/{max_recoveries}",
                )
                return 0
            raise RuntimeError("Execution ended without a verified final answer.")

        if tool_calls_made == 0 or tool_calls_succeeded == 0:
            raise RuntimeError("Execution produced no verified tool evidence; refusing to mark the task complete.")
        if _task_requires_mutation(job["prompt"]) and mutating_tool_succeeded == 0:
            raise RuntimeError("The task required a real change, but no mutating execution tool succeeded.")

        owner_final = compact_owner_summary(job_id, job["prompt"], final)
        set_job(
            job_id,
            state="completed",
            phase="completed",
            result=owner_final,
            runner_pid=None,
            heartbeat_at=now_iso(),
        )
        trace(job_id, "job.completed", owner_final[:12000])
        source = job.get("source") or "desktop"
        if source != "continuous":
            add_message(source, "assistant", owner_final, job_id)
            if source != "telegram" and load_config().get("telegram_enabled"):
                add_message("telegram", "assistant", owner_final, job_id)
        return 0

    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        current = get_job(job_id) or job
        cfg = load_config()
        count = int(current.get("recovery_count") or 0) + 1
        max_recoveries = int(cfg.get("max_recoveries", 8))
        low = error.lower()
        internally_retryable = any(marker in low for marker in (
            "invalid json", "malformed json", "planner", "local model call failed",
            "timeout", "timed out", "connection", "temporar",
        ))
        if internally_retryable and count <= max_recoveries:
            set_job(
                job_id,
                state="pending",
                phase="auto_recovery_internal",
                error=None,
                runner_pid=None,
                heartbeat_at=now_iso(),
                recovery_count=count,
            )
            trace(
                job_id,
                "job.internal_recovery_queued",
                f"{error} recovery={count}/{max_recoveries}"[:12000],
                ok=False,
            )
            return 0

        set_job(
            job_id,
            state="failed",
            phase="failed",
            error=error,
            runner_pid=None,
            heartbeat_at=now_iso(),
        )
        trace(job_id, "job.failed", error + "\n" + traceback.format_exc())
        source = job.get("source") or "desktop"
        failure = clean_model_text(f"I hit a real execution failure on that task: {error}")
        if source != "continuous":
            add_message(source, "assistant", failure, job_id)
            if source != "telegram" and load_config().get("telegram_enabled"):
                add_message("telegram", "assistant", failure, job_id)
        return 1
    finally:
        stop.set()


if __name__ == "__main__":
    raise SystemExit(main())
