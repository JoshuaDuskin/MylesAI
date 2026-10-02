from __future__ import annotations

import compileall
import base64
import json
import hashlib
import threading
import os
import re
import shutil
import smtplib
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from myles_common import (
    ROOT, DATA, WORKSPACES, UPDATES, BACKUPS, APP_VERSION,
    load_config, now_iso, set_job, trace, add_message, clean_model_text,
    list_jobs, active_job, job_truth, get_setting, set_setting
)


PINETREE_BLOCK_TERMS = (
    "pinetree",
    "pinetreepayments",
    "pinetree-payments",
    "pinetree-payments.com",
    "app.pinetree-payments",
)

def _contains_pinetree_reference(value: Any) -> bool:
    try:
        if isinstance(value, dict):
            return any(_contains_pinetree_reference(k) or _contains_pinetree_reference(v) for k, v in value.items())
        if isinstance(value, (list, tuple, set)):
            return any(_contains_pinetree_reference(v) for v in value)
        s = str(value or "").lower()
    except Exception:
        return False
    return any(term in s for term in PINETREE_BLOCK_TERMS)

def _pinetree_refusal(tool: str, detail: str = "") -> str:
    extra = f" ({detail})" if detail else ""
    return (
        "REFUSED: PineTree isolation is enabled. Myles is permanently blocked from "
        f"reading, writing, executing against, authenticating to, publishing to, or otherwise touching PineTree resources via {tool}{extra}."
    )

def _guard_pinetree(tool: str, *values: Any) -> str | None:
    cfg = load_config()
    if not bool(cfg.get("pinetree_isolation_enabled", True)):
        # v8.3.8 intentionally defaults this ON; config cannot silently disable it.
        pass
    if any(_contains_pinetree_reference(v) for v in values):
        return _pinetree_refusal(tool)
    return None

def _repo_remote_text(repo: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "remote", "-v"], cwd=str(repo),
            capture_output=True, text=True, errors="replace", timeout=20,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return (proc.stdout or "") + "\n" + (proc.stderr or "")
    except Exception:
        return ""

def _expand(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path))).resolve()


def run_process(job_id: str, argv: list[str], timeout: int, cwd: str | None = None) -> str:
    set_job(job_id, phase="tool", heartbeat_at=now_iso())
    p = subprocess.Popen(
        argv,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    start = time.time()
    while p.poll() is None:
        set_job(job_id, heartbeat_at=now_iso())
        if time.time() - start > timeout:
            try:
                p.kill()
            except Exception:
                pass
            out, err = p.communicate()
            return f"TIMEOUT after {timeout}s\nSTDOUT:\n{out}\nSTDERR:\n{err}"[-40000:]
        time.sleep(2)
    out, err = p.communicate()
    return f"exit_code={p.returncode}\nSTDOUT:\n{out}\nSTDERR:\n{err}"[-40000:]


def run_powershell(job_id: str, command: str, timeout_seconds: int = 1800) -> str:
    cfg = load_config()
    timeout = max(1, min(int(timeout_seconds), int(cfg["tool_timeout_seconds"])))
    command = str(command or "")
    refused = _guard_pinetree("run_powershell", command)
    if refused:
        trace(job_id, "tool.refused", refused, tool="run_powershell", ok=False)
        return refused
    # GitHub/Git mutations must use guarded narrow tools, not arbitrary shell access.
    if re.search(r"(?i)\bgh(?:\.exe)?\s+", command) or re.search(r"(?i)\bgit(?:\.exe)?\s+(push|clone|remote\s+(add|set-url)|fetch|pull)\b", command):
        out = "REFUSED: Git/GitHub mutation through run_powershell is disabled by the PineTree isolation boundary. Use git_command or github_pages_publish, which enforce repository/account guards."
        trace(job_id, "tool.refused", out, tool="run_powershell", ok=False)
        return out
    # Myles runs Windows PowerShell 5.1. Bash/cmd boolean separators repeatedly caused
    # real jobs to burn execution steps without doing work. Fail fast with a repair hint
    # so the agent can re-plan using PowerShell syntax or the narrower git_command tool.
    if "||" in command or "&&" in command:
        out = (
            "TOOL_ERROR: run_powershell uses Windows PowerShell 5.1, which does not support "
            "the shell operators '||' or '&&'. Use separate PowerShell statements with "
            "$LASTEXITCODE / if (...) blocks, or use git_command for Git operations."
        )
        trace(job_id, "tool.result", out, tool="run_powershell", ok=False)
        return out
    trace(job_id, "tool.start", command[:5000], tool="run_powershell")
    out = run_process(
        job_id,
        ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        timeout,
    )
    ok = "exit_code=0" in out
    trace(job_id, "tool.result", out, tool="run_powershell", ok=ok)
    if ok:
        set_job(job_id, material_progress_at=now_iso())
    return out


def read_text_file(job_id: str, path: str, max_chars: int = 80000) -> str:
    refused = _guard_pinetree("read_text_file", path)
    if refused:
        trace(job_id, "tool.refused", refused, tool="read_text_file", ok=False)
        return refused
    p = _expand(path)
    data = p.read_text(encoding="utf-8", errors="replace")
    out = f"PATH={p}\nSIZE={p.stat().st_size}\nCONTENT:\n{data[:max(100, min(int(max_chars), 200000))]}"
    trace(job_id, "tool.result", out, tool="read_text_file", ok=True)
    set_job(job_id, material_progress_at=now_iso())
    return out


def write_text_file(job_id: str, path: str, content: str, append: bool = False) -> str:
    refused = _guard_pinetree("write_text_file", path)
    if refused:
        trace(job_id, "tool.refused", refused, tool="write_text_file", ok=False)
        return refused
    p = _expand(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a" if append else "w", encoding="utf-8") as f:
        f.write(content)
    out = f"PATH={p}\nEXISTS={p.exists()}\nSIZE={p.stat().st_size}"
    trace(job_id, "tool.result", out, tool="write_text_file", ok=True)
    set_job(job_id, material_progress_at=now_iso())
    return out



def write_generated_file(
    job_id: str,
    path: str,
    instructions: str,
    append: bool = False,
    max_chars: int = 250000,
) -> str:
    """Generate file content as plain model text, then write it directly.

    Large HTML/code/text never has to survive a JSON tool argument. The action
    planner sends only a path + concise instructions; this tool performs the
    content-generation call separately and writes the returned bytes itself.
    """
    refused = _guard_pinetree("write_generated_file", path, instructions)
    if refused:
        trace(job_id, "tool.refused", refused, tool="write_generated_file", ok=False)
        return refused

    p = _expand(path)
    cfg = load_config()
    existing = ""
    if append and p.exists():
        try:
            existing = p.read_text(encoding="utf-8", errors="replace")[-12000:]
        except Exception:
            existing = ""

    system = (
        "You are a deterministic file-content generator inside Myles. "
        "Return ONLY the exact file content requested. Do not explain it. "
        "Do not output JSON. Do not emit private reasoning tags. "
        "Do not wrap the answer in Markdown code fences."
    )
    user = (
        f"DESTINATION: {p}\n"
        f"MODE: {'append' if append else 'replace'}\n"
        f"INSTRUCTIONS:\n{str(instructions or '').strip()}\n"
    )
    if existing:
        user += "\nEXISTING FILE TAIL FOR CONTINUITY:\n" + existing

    last_error = ""
    content = ""
    for attempt in range(1, 4):
        body = json.dumps({
            "model": cfg["model"],
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "think": False,
            "options": {"temperature": 0.15},
            "keep_alive": "10m",
        }).encode("utf-8")
        req = urllib.request.Request(
            cfg["ollama_url"],
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        trace(job_id, "tool.start", f"path={p} append={append} attempt={attempt}", tool="write_generated_file")
        try:
            with urllib.request.urlopen(req, timeout=int(cfg.get("model_timeout_seconds", 180))) as r:
                data = json.loads(r.read().decode("utf-8"))
            content = clean_model_text(str((data.get("message") or {}).get("content") or ""))
            if content:
                break
            last_error = "empty content"
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            trace(job_id, "tool.retry", f"write_generated_file attempt={attempt} {last_error}"[:12000], tool="write_generated_file", ok=False)
            if attempt < 3:
                time.sleep(2 * attempt)

    if not content:
        out = f"TOOL_ERROR: file generator failed after internal retries: {last_error or 'empty content'}"
        trace(job_id, "tool.result", out, tool="write_generated_file", ok=False)
        return out

    # Strip a single outer Markdown code fence if the local model ignored the
    # instruction, while leaving the actual file content untouched.
    stripped = content.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            content = "\n".join(lines[1:-1])

    limit = max(1000, min(int(max_chars), 500000))
    if len(content) > limit:
        out = (
            f"TOOL_ERROR: generated content exceeded the configured limit "
            f"({len(content)} > {limit}). Split the artifact into smaller files/parts."
        )
        trace(job_id, "tool.result", out, tool="write_generated_file", ok=False)
        return out

    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a" if append else "w", encoding="utf-8") as f:
        f.write(content)
    out = f"PATH={p}\nEXISTS={p.exists()}\nSIZE={p.stat().st_size}\nGENERATED_CONTENT_WRITTEN=true"
    trace(job_id, "tool.result", out, tool="write_generated_file", ok=True)
    set_job(job_id, material_progress_at=now_iso())
    return out


def apply_text_patch(job_id: str, path: str, old_text: str, new_text: str, count: int = 1) -> str:
    """Apply a deterministic exact-text patch without regenerating a whole file."""
    refused = _guard_pinetree("apply_text_patch", path, old_text, new_text)
    if refused:
        trace(job_id, "tool.refused", refused, tool="apply_text_patch", ok=False)
        return refused
    p = _expand(path)
    if not p.exists():
        return f"TOOL_ERROR: file does not exist: {p}"
    data = p.read_text(encoding="utf-8", errors="replace")
    if old_text not in data:
        return "TOOL_ERROR: old_text was not found exactly in the target file."
    n = max(1, min(int(count), 100))
    updated = data.replace(old_text, new_text, n)
    p.write_text(updated, encoding="utf-8")
    out = f"PATH={p}\nPATCHED=true\nREPLACEMENTS={min(n, data.count(old_text))}\nSIZE={p.stat().st_size}"
    trace(job_id, "tool.result", out, tool="apply_text_patch", ok=True)
    set_job(job_id, material_progress_at=now_iso())
    return out


def list_directory(job_id: str, path: str, recursive: bool = False, max_items: int = 500) -> str:
    refused = _guard_pinetree("list_directory", path)
    if refused:
        trace(job_id, "tool.refused", refused, tool="list_directory", ok=False)
        return refused
    p = _expand(path)
    it = p.rglob("*") if recursive else p.iterdir()
    rows = []
    limit = max(1, min(int(max_items), 2000))
    for i, item in enumerate(it):
        if i >= limit:
            rows.append("...TRUNCATED...")
            break
        try:
            st = item.stat()
            rows.append(
                f"{'DIR ' if item.is_dir() else 'FILE'} {item} "
                f"size={st.st_size} modified={datetime.fromtimestamp(st.st_mtime).isoformat(timespec='seconds')}"
            )
        except Exception as exc:
            rows.append(f"ERROR {item}: {exc}")
    out = f"PATH={p}\nEXISTS={p.exists()}\n" + "\n".join(rows)
    trace(job_id, "tool.result", out, tool="list_directory", ok=True)
    set_job(job_id, material_progress_at=now_iso())
    return out


def download_file(job_id: str, url: str, destination: str) -> str:
    refused = _guard_pinetree("download_file", url, destination)
    if refused:
        trace(job_id, "tool.refused", refused, tool="download_file", ok=False)
        return refused
    p = _expand(destination)
    p.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Myles/9.7.0"})
    with urllib.request.urlopen(req, timeout=120) as r, p.open("wb") as f:
        shutil.copyfileobj(r, f)
    out = f"DOWNLOADED={url}\nPATH={p}\nSIZE={p.stat().st_size}"
    trace(job_id, "tool.result", out, tool="download_file", ok=True)
    set_job(job_id, material_progress_at=now_iso())
    return out



def web_search(job_id: str, query: str, max_results: int = 5) -> str:
    """Reusable read-only public web search for background jobs."""
    refused = _guard_pinetree("web_search", query)
    if refused:
        trace(job_id, "tool.refused", refused, tool="web_search", ok=False)
        return refused
    from myles_quick import web_search as _quick_web_search
    trace(job_id, "tool.start", str(query)[:4000], tool="web_search")
    result = _quick_web_search(str(query or ""), max_results=max_results)
    if result.evidence:
        out = "SEARCH_EVIDENCE:\n" + result.evidence
        trace(job_id, "tool.result", out[:12000], tool="web_search", ok=True)
        set_job(job_id, material_progress_at=now_iso())
        return out
    out = "TOOL_ERROR: " + (result.error or "web search returned no usable evidence")
    trace(job_id, "tool.result", out[:12000], tool="web_search", ok=False)
    return out


def web_fetch(job_id: str, url: str, max_chars: int = 60000) -> str:
    refused = _guard_pinetree("web_fetch", url)
    if refused:
        trace(job_id, "tool.refused", refused, tool="web_fetch", ok=False)
        return refused
    req = urllib.request.Request(url, headers={"User-Agent": f"Mozilla/5.0 Myles/{APP_VERSION}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read(max(1000, min(int(max_chars), 200000)))
        ctype = r.headers.get("Content-Type", "")
    text = raw.decode("utf-8", errors="replace")
    out = f"URL={url}\nCONTENT_TYPE={ctype}\nCONTENT:\n{text}"
    trace(job_id, "tool.result", out, tool="web_fetch", ok=True)
    set_job(job_id, material_progress_at=now_iso())
    return out


def git_command(job_id: str, repo_path: str, args: str, timeout_seconds: int = 900) -> str:
    refused = _guard_pinetree("git_command", repo_path, args)
    if refused:
        trace(job_id, "tool.refused", refused, tool="git_command", ok=False)
        return refused
    p = _expand(repo_path)
    remotes = _repo_remote_text(p)
    if _contains_pinetree_reference(remotes):
        refused = _pinetree_refusal("git_command", "repository remote is PineTree-related")
        trace(job_id, "tool.refused", refused, tool="git_command", ok=False)
        return refused
    try:
        import shlex
        parsed = shlex.split(str(args), posix=False)
        argv = ["git", *parsed]
    except Exception:
        return "TOOL_ERROR: invalid git arguments."
    if not parsed:
        return "TOOL_ERROR: empty git arguments."

    verb = str(parsed[0]).lower()
    remote_mutation = verb in {"push", "pull", "fetch"}
    remote_config = verb == "remote" and any(str(x).lower() in {"add", "set-url"} for x in parsed[1:3])

    # Any GitHub network mutation must belong to Myles' dedicated GitHub account.
    if remote_mutation or remote_config:
        owner, _, _ = _dedicated_github_identity()
        if not owner:
            out = "OWNER_AUTH_REQUIRED: Myles dedicated GitHub identity is not configured. PineTree and owner-personal credentials are not allowed."
            trace(job_id, "tool.refused", out, tool="git_command", ok=False)
            return out
        all_text = (remotes + "\n" + str(args)).lower()
        if "github.com" in all_text and f"github.com/{owner.lower()}/" not in all_text:
            out = (
                "REFUSED: GitHub mutation is restricted to Myles' dedicated GitHub account "
                f"({owner}). Other GitHub owners are outside Myles' boundary."
            )
            trace(job_id, "tool.refused", out, tool="git_command", ok=False)
            return out

    trace(job_id, "tool.start", f"repo={p} git {args}", tool="git_command")
    timeout = max(1, min(int(timeout_seconds), int(load_config()["tool_timeout_seconds"])))

    if remote_mutation:
        gh = _find_gh()
        if not gh:
            out = "TOOL_ERROR: GitHub CLI is required for isolated Git authentication."
            trace(job_id, "tool.result", out, tool="git_command", ok=False)
            return out
        login, gh_env, _ = _github_cli_identity(gh)
        if not login or not gh_env:
            out = "OWNER_AUTH_REQUIRED: Myles dedicated GitHub CLI profile is not authenticated."
            trace(job_id, "tool.result", out, tool="git_command", ok=False)
            return out
        git_env = _git_auth_env_from_gh(gh, gh_env)
        if not git_env:
            out = "OWNER_AUTH_REQUIRED: Myles dedicated GitHub token is unavailable for isolated Git access."
            trace(job_id, "tool.result", out, tool="git_command", ok=False)
            return out
        code, stdout, stderr = _capture(argv, cwd=str(p), timeout=timeout, env=git_env)
        out = f"exit_code={code}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"[-40000:]
    else:
        out = run_process(job_id, argv, timeout, cwd=str(p))

    ok = "exit_code=0" in out
    trace(job_id, "tool.result", out, tool="git_command", ok=ok)
    if ok:
        set_job(job_id, material_progress_at=now_iso())
    return out



def _find_gh() -> str | None:
    candidates = [
        shutil.which("gh"),
        str(Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "GitHub CLI" / "gh.exe"),
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "GitHub CLI" / "gh.exe"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(Path(candidate))
    return None


def _capture(
    argv: list[str],
    cwd: str | None = None,
    timeout: int = 120,
    input_text: str | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    proc = subprocess.run(
        argv,
        cwd=cwd,
        input=input_text,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        env=env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return int(proc.returncode), str(proc.stdout or ""), str(proc.stderr or "")


def _dedicated_github_identity() -> tuple[str, str, str]:
    """Return (owner, email, config_dir) for the dedicated Myles GitHub profile."""
    identity_path = DATA / "github_identity.json"
    try:
        data = json.loads(identity_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return "", "", ""
    owner = str(data.get("owner") or "").strip()
    email = str(data.get("email") or "").strip()
    config_dir = str(data.get("gh_config_dir") or "").strip()
    if not owner or not config_dir or _contains_pinetree_reference(owner) or _contains_pinetree_reference(email):
        return "", "", ""
    return owner, email, config_dir


def _github_cli_identity(gh: str) -> tuple[str, dict[str, str] | None, str]:
    """Resolve only the dedicated Myles GitHub CLI profile.

    The default GitHub CLI profile and Windows Git Credential Manager are intentionally
    ignored so PineTree or owner-personal credentials cannot be reused by Myles.
    """
    expected_owner, _, config_dir = _dedicated_github_identity()
    if not expected_owner or not config_dir:
        return "", None, "none"
    env = os.environ.copy()
    env["GH_CONFIG_DIR"] = config_dir
    code, _, _ = _capture([gh, "auth", "status", "-h", "github.com"], timeout=30, env=env)
    if code != 0:
        return "", env, "none"
    code, login, _ = _capture([gh, "api", "user", "--jq", ".login"], timeout=30, env=env)
    login = login.strip() if code == 0 else ""
    if not login or _contains_pinetree_reference(login):
        return "", env, "none"
    if login.lower() != expected_owner.lower():
        return "", env, "identity-mismatch"
    return login, env, "dedicated-gh-profile"


def _git_auth_env_from_gh(gh: str, gh_env: dict[str, str]) -> dict[str, str] | None:
    """Create an in-memory Git HTTPS auth environment from the isolated gh profile.

    The token is never written to Myles config, a Git remote, or a command line.
    """
    code, token, _ = _capture([gh, "auth", "token", "-h", "github.com"], timeout=30, env=gh_env)
    token = token.strip() if code == 0 else ""
    if not token:
        return None
    basic = base64.b64encode(("x-access-token:" + token).encode("utf-8")).decode("ascii")
    env = os.environ.copy()
    env.update(gh_env)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.extraHeader"
    env["GIT_CONFIG_VALUE_0"] = "Authorization: Basic " + basic
    return env



MYLES_DASHBOARD_CANONICAL_REPO = "MylesAI"

def _canonical_myles_dashboard_repo_name(value: str) -> str:
    """Collapse Myles dashboard/control-center aliases to one canonical repo.

    This prevents autonomous iterations from spawning MylesDashboard,
    myles-dashboard, Myles-ControlCenter, Myles-AI-Dashboard, etc.
    """
    raw = str(value or "").strip()
    low = re.sub(r"[^a-z0-9]+", "", raw.lower())
    if low in {
        "mylesdashboard",
        "mylescontroldashboard",
        "mylescontrolcenter",
        "mylesaidashboard",
        "mylesprogressdashboard",
        "progressdashboard",
    }:
        return MYLES_DASHBOARD_CANONICAL_REPO
    if "myles" in low and ("dashboard" in low or "controlcenter" in low):
        return MYLES_DASHBOARD_CANONICAL_REPO
    return raw or "progress-dashboard"


def github_pages_publish(job_id: str, repo_path: str, repo_name: str = "progress-dashboard") -> str:
    """Publish a static workspace through Myles' dedicated GitHub identity.

    Never invents or reuses an owner/PineTree GitHub identity. Missing dedicated authentication is
    returned as an explicit owner-auth gate rather than an ordinary execution failure.
    """
    refused = _guard_pinetree("github_pages_publish", repo_path, repo_name)
    if refused:
        trace(job_id, "tool.refused", refused, tool="github_pages_publish", ok=False)
        return refused
    workspace = _expand(repo_path)
    remotes = _repo_remote_text(workspace)
    if _contains_pinetree_reference(remotes):
        refused = _pinetree_refusal("github_pages_publish", "workspace has a PineTree-related Git remote")
        trace(job_id, "tool.refused", refused, tool="github_pages_publish", ok=False)
        return refused
    if not workspace.is_dir():
        return f"TOOL_ERROR: repository path does not exist: {workspace}"
    if not (workspace / "index.html").exists():
        return f"TOOL_ERROR: GitHub Pages publishing requires index.html in {workspace}"

    gh = _find_gh()
    if not gh:
        winget = shutil.which("winget")
        if winget:
            trace(job_id, "tool.start", "Installing GitHub CLI for current user", tool="github_pages_publish")
            code, out, err = _capture([
                winget, "install", "--id", "GitHub.cli", "-e", "--scope", "user", "--silent",
                "--accept-source-agreements", "--accept-package-agreements",
            ], timeout=600)
            trace(job_id, "tool.result", f"winget exit={code}\n{out}\n{err}"[-12000:], tool="github_pages_publish", ok=(code == 0))
            gh = _find_gh()
        if not gh:
            return "TOOL_ERROR: GitHub CLI is not installed and automatic user-scope installation did not succeed."

    login, gh_env, auth_source = _github_cli_identity(gh)
    if not login:
        return (
            "OWNER_AUTH_REQUIRED: Myles dedicated GitHub profile is missing, signed out, or does not match github_identity.json. "
            "PineTree and owner-personal GitHub credentials are intentionally ignored. Run the Myles dedicated GitHub setup once."
        )
    trace(job_id, "github.auth_reused", f"account={login} source={auth_source}", tool="github_pages_publish", ok=True)

    repo_name = _canonical_myles_dashboard_repo_name(repo_name)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", str(repo_name or "progress-dashboard")).strip("-.") or "progress-dashboard"
    full = f"{login}/{safe_name}"

    # Normalize local repository and branch deterministically.
    if not (workspace / ".git").exists():
        code, out, err = _capture(["git", "init"], cwd=str(workspace), timeout=60)
        if code != 0:
            return f"TOOL_ERROR: git init failed: {(out+err)[-2000:]}"
    code, out, err = _capture(["git", "branch", "-M", "main"], cwd=str(workspace), timeout=60)
    if code != 0:
        return f"TOOL_ERROR: could not normalize branch to main: {(out+err)[-2000:]}"

    # Ensure files are committed before publishing.
    _capture(["git", "add", "-A"], cwd=str(workspace), timeout=60)
    code, out, err = _capture(["git", "diff", "--cached", "--quiet"], cwd=str(workspace), timeout=60)
    if code == 1:
        ccode, cout, cerr = _capture(["git", "commit", "-m", "Update progress dashboard"], cwd=str(workspace), timeout=120)
        if ccode != 0:
            # Configure only this repository with Myles' dedicated identity; never modify global Git config.
            identity_owner, identity_email, _ = _dedicated_github_identity()
            _capture(["git", "config", "user.name", identity_owner or "Myles"], cwd=str(workspace), timeout=30)
            _capture(["git", "config", "user.email", identity_email or "myles@localhost"], cwd=str(workspace), timeout=30)
            ccode, cout, cerr = _capture(["git", "commit", "-m", "Update progress dashboard"], cwd=str(workspace), timeout=120)
            if ccode != 0:
                return f"TOOL_ERROR: git commit failed: {(cout+cerr)[-3000:]}"

    # Create the repository under the authenticated user if it does not already exist.
    exists_code, _, _ = _capture([gh, "repo", "view", full, "--json", "nameWithOwner"], timeout=45, env=gh_env)
    if exists_code != 0:
        ccode, cout, cerr = _capture([gh, "repo", "create", full, "--public", "--description", "Myles progress dashboard"], timeout=120, env=gh_env)
        if ccode != 0:
            combined = (cout + "\n" + cerr).strip()
            low = combined.lower()
            if any(x in low for x in ("authentication", "unauthorized", "forbidden", "requires authentication", "resource not accessible", "insufficient")):
                return "OWNER_AUTH_REQUIRED: The existing GitHub credential was found, but GitHub says it lacks permission to create the repository. " + combined[-1800:]
            return f"TOOL_ERROR: could not create GitHub repository {full}: {combined[-4000:]}"

    remote = f"https://github.com/{full}.git"
    rcode, rout, rerr = _capture(["git", "remote", "get-url", "origin"], cwd=str(workspace), timeout=30)
    if rcode == 0:
        code, out, err = _capture(["git", "remote", "set-url", "origin", remote], cwd=str(workspace), timeout=30)
    else:
        code, out, err = _capture(["git", "remote", "add", "origin", remote], cwd=str(workspace), timeout=30)
    if code != 0:
        return f"TOOL_ERROR: could not configure GitHub remote: {(out+err)[-2000:]}"

    git_auth_env = _git_auth_env_from_gh(gh, gh_env or os.environ.copy())
    if not git_auth_env:
        return "OWNER_AUTH_REQUIRED: Myles dedicated GitHub profile exists but its token could not be read for an isolated push. Re-authenticate the Myles-only GitHub profile."
    code, out, err = _capture(["git", "push", "-u", "origin", "main"], cwd=str(workspace), timeout=300, env=git_auth_env)
    if code != 0:
        combined = (out + "\n" + err).strip()
        if "authentication" in combined.lower() or "permission" in combined.lower() or "403" in combined:
            return "OWNER_AUTH_REQUIRED: Myles dedicated GitHub account requires renewed authorization. " + combined[-2000:]
        return f"TOOL_ERROR: git push failed for {full}: {combined[-4000:]}"

    # Configure GitHub Pages from main:/ using the REST API through authenticated gh.
    payload = json.dumps({"source": {"branch": "main", "path": "/"}})
    pcode, pout, perr = _capture([gh, "api", "--method", "POST", f"repos/{full}/pages", "--input", "-"], timeout=60, input_text=payload, env=gh_env)
    if pcode != 0:
        combined = (pout + "\n" + perr)
        # Existing Pages sites return a conflict. Update their source instead.
        ucode, uout, uerr = _capture([gh, "api", "--method", "PUT", f"repos/{full}/pages", "--input", "-"], timeout=60, input_text=payload, env=gh_env)
        if ucode != 0 and not any(x in combined.lower() for x in ("already exists", "409")):
            return f"TOOL_ERROR: repository pushed, but GitHub Pages configuration failed: {(combined + uout + uerr)[-5000:]}"

    # Ask GitHub for the canonical Pages URL, then wait briefly for first publish.
    code, page_url, err = _capture([gh, "api", f"repos/{full}/pages", "--jq", ".html_url"], timeout=45, env=gh_env)
    page_url = page_url.strip() if code == 0 else ""
    if not page_url:
        page_url = f"https://{login}.github.io/{safe_name}/"

    http_status = "pending"
    for _ in range(12):
        try:
            req = urllib.request.Request(page_url, headers={"User-Agent": "Myles/9.7.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                status = int(getattr(response, "status", 0) or 0)
            if 200 <= status < 400:
                http_status = str(status)
                break
        except Exception:
            pass
        time.sleep(5)

    out = (
        f"GITHUB_LOGIN={login}\nREPOSITORY={full}\nREPO_URL=https://github.com/{full}\n"
        f"PUBLIC_URL={page_url}\nHTTP_STATUS={http_status}\nAUTH_SOURCE={auth_source}\n"
        "The repository was created/updated only under a dedicated non-PineTree GitHub CLI identity. PineTree credentials and repositories are hard-blocked."
    )
    trace(job_id, "tool.result", out, tool="github_pages_publish", ok=True)
    set_job(job_id, material_progress_at=now_iso())
    return out



_STATUS_FEED_LOCK = threading.RLock()

def _sanitize_public_status_text(value: Any, max_chars: int = 220) -> str:
    """Redact obvious private material before anything is published publicly."""
    text = str(value or "")
    # Paths, URLs, email addresses, long token-like strings, and secret assignments.
    text = re.sub(r"(?i)\b[A-Z]:\\[^\r\n]*", "[local path]", text)
    text = re.sub(r"https?://\S+", "[url]", text)
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[email]", text)
    text = re.sub(
        r"(?i)\b(token|secret|password|passwd|api[_-]?key|authorization|cookie|credential|private[_-]?key)\b\s*[:=]?\s*\S*",
        r"\1=[redacted]",
        text,
    )
    text = re.sub(r"\b[A-Za-z0-9_\-]{28,}\b", "[redacted]", text)
    for term in PINETREE_BLOCK_TERMS:
        text = re.sub(re.escape(term), "[protected]", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max(20, int(max_chars))]

def _friendly_public_task_label(prompt: str) -> str:
    text = str(prompt or "").strip()
    if "Owner's new instruction:" in text:
        text = text.split("Owner's new instruction:", 1)[1].strip()
    if "Owner instruction:" in text:
        text = text.split("Owner instruction:", 1)[1].strip()

    low = text.lower()
    if "overnight" in low and any(x in low for x in ("improv", "work continuously", "work nonstop")):
        return "Overnight Myles self-improvement"
    if "add the tools to your kit" in low or ("improve myles" in low and "tool" in low):
        return "Improve Myles's tools and capabilities"
    if "dashboard" in low and any(x in low for x in ("provide the url", "give me the url", "public url", "dashboard url")):
        return "Share the Myles dashboard link"
    if "dashboard" in low and any(x in low for x in ("redesign", "modern", "navigation", "control center")):
        return "Improve the Myles Control Center"
    if "continuous improvement cycle" in low or "owner-locked dashboard" in low:
        if any(x in low for x in ("quant", "gmx", "trading", "game mode")):
            return "Repair dashboard, game mode, and Quant feeds"
        return "Run verified continuous improvement"

    text = re.sub(r"(?is)^continue from and modify the existing result.*?owner's new instruction:\s*", "", text).strip()
    text = re.sub(r"\s+", " ", text)
    first = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0].strip()
    return _sanitize_public_status_text(first or text, 110) or "Owner task"

def _friendly_public_task_summary(
    prompt: str,
    *,
    source: str = "",
    completed: bool = False,
    failed: bool = False,
) -> str:
    """Return a compact public-safe task summary; never expose the raw prompt."""
    text = str(prompt or "").strip().lower()
    label = _friendly_public_task_label(prompt)
    if "continuous improvement cycle" in text or "owner-locked dashboard" in text:
        return "Verified continuous-improvement work is running; details stay summarized."
    if source == "continuous":
        return "Working through the next verified improvement cycle."
    if failed:
        return f"Task failed after working on {label}."
    if completed:
        return f"Completed {label}."
    return f"Working on {label}."

def _friendly_public_phase(value: Any) -> str:
    phase = str(value or "").strip()
    low = phase.lower()
    if low.startswith("tool:"):
        return "Using tools"
    mapping = {
        "model": "Planning / reasoning",
        "planning": "Planning",
        "queued": "Waiting in queue",
        "verifying": "Verifying result",
        "verify": "Verifying result",
        "recovery": "Recovering",
        "recovering": "Recovering",
        "owner_resume": "Resuming",
        "running": "Working",
    }
    return mapping.get(low, phase or "Working")

def _runtime_public_snapshot() -> dict[str, Any]:
    """Build a narrow, public-safe snapshot of real Myles operational state."""
    jobs = list_jobs(100)
    active = active_job()
    pending = [j for j in jobs if str(j.get("state") or "") == "pending"]
    completed = next((j for j in jobs if str(j.get("state") or "") == "completed"), None)
    failed = next((j for j in jobs if str(j.get("state") or "") == "failed"), None)

    current = None
    if active:
        truth = job_truth(active)
        prompt = str(active.get("prompt") or "")
        source = "continuous" if str(active.get("source") or "") == "continuous" else "owner"
        current = {
            "id": str(active.get("id") or ""),
            "label": _friendly_public_task_label(prompt),
            "summary": _friendly_public_task_summary(prompt, source=source),
            "source": source,
            "state": _sanitize_public_status_text(truth.get("truth_state") or active.get("state") or "", 40),
            "phase": _sanitize_public_status_text(active.get("phase") or "", 80),
            "phase_display": _sanitize_public_status_text(_friendly_public_phase(active.get("phase")), 80),
            "started_at": active.get("started_at"),
            "updated_at": active.get("updated_at"),
            "heartbeat_at": active.get("heartbeat_at"),
            "last_verified_progress_at": active.get("material_progress_at"),
            "worker_alive": bool(truth.get("live_worker")),
            "heartbeat_age_seconds": truth.get("heartbeat_age_seconds"),
            "progress_age_seconds": truth.get("progress_age_seconds"),
        }

    queued_tasks = []
    for job in sorted(pending, key=lambda j: str(j.get("created_at") or ""))[:12]:
        prompt = str(job.get("prompt") or "")
        source = "continuous" if str(job.get("source") or "") == "continuous" else "owner"
        queued_tasks.append({
            "id": str(job.get("id") or ""),
            "label": _friendly_public_task_label(prompt),
            "summary": _friendly_public_task_summary(prompt, source=source),
            "source": source,
            "state": "QUEUED",
            "created_at": job.get("created_at"),
        })

    continuous = {
        "enabled": get_setting("continuous.enabled", "0") == "1",
        "cycle": int(get_setting("continuous.cycle", "0") or "0"),
        "consecutive_failures": int(get_setting("continuous.consecutive_failures", "0") or "0"),
        "last_job_id": get_setting("continuous.last_job_id", ""),
        "next_spawn_epoch": int(get_setting("continuous.next_spawn_epoch", "0") or "0"),
        "mode": "idle-time continuous improvement",
    }

    cfg = load_config()
    game_state: dict[str, Any] = {}
    try:
        raw_game = json.loads((DATA / "game_mode_state.json").read_text(encoding="utf-8-sig", errors="replace"))
        if isinstance(raw_game, dict):
            game_state = raw_game
    except Exception:
        pass
    game_active = bool(game_state.get("active")) or bool(cfg.get("light_mode"))
    game_detail = {
        "active": game_active,
        "automatic": bool(game_state.get("active") and game_state.get("automatic")),
        "detected": bool(game_state.get("detected")),
        "status": game_state.get("status") or ("watching" if game_state else "watcher_offline"),
        "process": game_state.get("process"),
        "pid": game_state.get("pid"),
        "exe": game_state.get("exe"),
        "reason": game_state.get("reason"),
        "entered_at": game_state.get("entered_at"),
        "last_checked_at": game_state.get("last_checked_at"),
        "watcher_pid": game_state.get("watcher_pid"),
        "source": cfg.get("light_mode_source") or ("automatic_game_detection" if game_state.get("active") else "manual"),
    }

    return {
        "schema_version": 4,
        "generated_at": now_iso(),
        "myles": {"version": APP_VERSION, "online": True},
        "continuous_program": continuous,
        "game_mode": game_active,
        "game_mode_detail": game_detail,
        "current_task": current,
        "queue_count": len(pending),
        "queue": queued_tasks,
        "queued_tasks": queued_tasks,
        "last_completed": (
            {
                "id": str(completed.get("id") or ""),
                "label": _friendly_public_task_label(str(completed.get("prompt") or "")),
                "summary": _friendly_public_task_summary(str(completed.get("prompt") or ""), completed=True),
                "completed_at": completed.get("updated_at"),
            } if completed else None
        ),
        "last_failure": (
            {
                "id": str(failed.get("id") or ""),
                "label": _friendly_public_task_label(str(failed.get("prompt") or "")),
                "summary": _friendly_public_task_summary(str(failed.get("prompt") or ""), failed=True),
                "error": _sanitize_public_status_text(failed.get("error") or "Execution failed", 220),
                "failed_at": failed.get("updated_at"),
            } if failed else None
        ),
    }


def _status_snapshot_stable_hash(snapshot: dict[str, Any]) -> str:
    stable = json.loads(json.dumps(snapshot))
    stable.pop("generated_at", None)
    current = stable.get("current_task")
    if isinstance(current, dict):
        current.pop("heartbeat_age_seconds", None)
        current.pop("progress_age_seconds", None)
        current.pop("updated_at", None)
        current.pop("heartbeat_at", None)
    raw = json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _status_feed_git_push(repo: Path) -> str:
    refused = _guard_pinetree("runtime_status_feed", str(repo), _repo_remote_text(repo))
    if refused:
        return refused

    gh = _find_gh()
    if not gh:
        return "TOOL_ERROR: GitHub CLI is required for the public runtime status feed."
    login, gh_env, _ = _github_cli_identity(gh)
    if not login or not gh_env:
        return "OWNER_AUTH_REQUIRED: Myles dedicated GitHub CLI profile is not authenticated."

    git_auth_env = _git_auth_env_from_gh(gh, gh_env)
    if not git_auth_env:
        return "OWNER_AUTH_REQUIRED: Myles dedicated GitHub token is unavailable for isolated Git access."

    code, out, err = _capture(["git", "add", "--", "status.json"], cwd=str(repo), timeout=60)
    if code != 0:
        return f"TOOL_ERROR: could not stage status.json: {(out+err)[-2000:]}"

    code, _, _ = _capture(["git", "diff", "--cached", "--quiet"], cwd=str(repo), timeout=60)
    if code == 0:
        return "STATUS_FEED_NO_CHANGE"
    if code != 1:
        return "TOOL_ERROR: could not inspect status feed Git diff."

    identity_owner, identity_email, _ = _dedicated_github_identity()
    _capture(["git", "config", "user.name", identity_owner or "Myles"], cwd=str(repo), timeout=30)
    _capture(["git", "config", "user.email", identity_email or "myles@localhost"], cwd=str(repo), timeout=30)
    code, out, err = _capture(
        ["git", "commit", "-m", "Update Myles runtime status"],
        cwd=str(repo), timeout=120
    )
    if code != 0:
        return f"TOOL_ERROR: status feed commit failed: {(out+err)[-2500:]}"

    code, out, err = _capture(
        ["git", "push", "origin", "main"],
        cwd=str(repo), timeout=240, env=git_auth_env
    )
    if code != 0:
        return f"TOOL_ERROR: status feed push failed: {(out+err)[-3500:]}"
    return "STATUS_FEED_PUSHED"

def configure_runtime_status_feed(
    job_id: str,
    repo_path: str,
    repo_name: str = "MylesAI",
    min_update_seconds: int = 20,
) -> str:
    """Configure a real sanitized public status feed for a Myles dashboard.

    The feed is outbound-only: Myles writes status.json in the dashboard repo and
    pushes only when meaningful state changes. Public pages can poll the raw JSON.
    """
    refused = _guard_pinetree("configure_runtime_status_feed", repo_path, repo_name)
    if refused:
        trace(job_id, "tool.refused", refused, tool="configure_runtime_status_feed", ok=False)
        return refused

    repo = _expand(repo_path)
    if not repo.exists():
        return f"TOOL_ERROR: dashboard repository path does not exist: {repo}"

    owner, _, _ = _dedicated_github_identity()
    if not owner:
        return "OWNER_AUTH_REQUIRED: Myles dedicated GitHub identity is not configured."

    repo_name = _canonical_myles_dashboard_repo_name(repo_name or MYLES_DASHBOARD_CANONICAL_REPO)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", str(repo_name)).strip("-") or MYLES_DASHBOARD_CANONICAL_REPO
    snapshot = _runtime_public_snapshot()
    status_path = repo / "status.json"
    status_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    # Publish/update the repo first so index.html + status.json share the same verified identity.
    published = github_pages_publish(job_id, str(repo), safe_name)
    outcome = str(published)
    if outcome.upper().startswith(("TOOL_ERROR", "OWNER_AUTH_REQUIRED", "REFUSED")):
        return outcome

    set_setting("status_feed.enabled", "1")
    set_setting("status_feed.repo_path", str(repo))
    set_setting("status_feed.repo_name", safe_name)
    set_setting("status_feed.min_update_seconds", str(max(5, min(int(min_update_seconds), 120))))
    set_setting("status_feed.force_refresh_seconds", "60")
    set_setting("status_feed.last_hash", _status_snapshot_stable_hash(snapshot))
    set_setting("status_feed.last_push_epoch", str(int(time.time())))

    raw_url = f"https://raw.githubusercontent.com/{owner}/{safe_name}/main/status.json"
    verified_raw = False
    verify_error = ""
    for attempt in range(1, 9):
        try:
            req = urllib.request.Request(
                raw_url + f"?v={int(time.time())}",
                headers={"User-Agent": f"Myles/{APP_VERSION}"},
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                payload = json.loads(response.read(200000).decode("utf-8", errors="replace"))
            if isinstance(payload, dict) and int(payload.get("schema_version") or 0) in {1, 2, 3, 4}:
                verified_raw = True
                break
            verify_error = "status.json did not contain the expected schema"
        except Exception as exc:
            verify_error = f"{type(exc).__name__}: {exc}"
        if attempt < 8:
            time.sleep(3)

    if not verified_raw:
        set_setting("status_feed.enabled", "0")
        return (
            "TOOL_ERROR: dashboard repository was published, but the public sanitized "
            f"runtime status feed could not be verified at {raw_url}: {verify_error}"
        )

    set_setting("status_feed.raw_url", raw_url)
    trace(
        job_id,
        "tool.result",
        f"STATUS_FEED_CONFIGURED=1\nRAW_STATUS_URL={raw_url}\nRAW_STATUS_VERIFIED=1\n{published}"[:12000],
        tool="configure_runtime_status_feed",
        ok=True,
    )
    set_job(job_id, material_progress_at=now_iso())
    return (
        "STATUS_FEED_CONFIGURED=1\n"
        f"RAW_STATUS_URL={raw_url}\n"
        "RAW_STATUS_VERIFIED=1\n"
        "UPDATE_MODE=push-on-meaningful-state-change\n"
        f"MIN_UPDATE_SECONDS={get_setting('status_feed.min_update_seconds','20')}\n"
        + published
    )

_STATUS_FEED_THREAD_LOCK = threading.RLock()
_STATUS_FEED_THREAD: threading.Thread | None = None

def runtime_status_feed_tick() -> None:
    """Push the canonical public status feed. Safe to run off the core monitor thread."""
    if get_setting("status_feed.enabled", "0") != "1":
        return

    with _STATUS_FEED_LOCK:
        try:
            repo_raw = get_setting("status_feed.repo_path", "")
            if not repo_raw:
                return
            repo = _expand(repo_raw)
            if not repo.exists() or not (repo / ".git").exists():
                set_setting("status_feed.last_error", "Configured repo path is unavailable.")
                return

            # The Myles status feed has one canonical public home.
            configured_name = _canonical_myles_dashboard_repo_name(
                get_setting("status_feed.repo_name", MYLES_DASHBOARD_CANONICAL_REPO)
            )
            if configured_name != MYLES_DASHBOARD_CANONICAL_REPO:
                configured_name = MYLES_DASHBOARD_CANONICAL_REPO
            set_setting("status_feed.repo_name", configured_name)

            refused = _guard_pinetree("runtime_status_feed", str(repo), _repo_remote_text(repo))
            if refused:
                set_setting("status_feed.enabled", "0")
                set_setting("status_feed.last_error", refused)
                return

            min_seconds = max(5, int(get_setting("status_feed.min_update_seconds", "8") or "8"))
            force_seconds = max(30, int(get_setting("status_feed.force_refresh_seconds", "60") or "60"))
            now = int(time.time())
            last_push = int(get_setting("status_feed.last_push_epoch", "0") or "0")
            if now - last_push < min_seconds:
                return

            snapshot = _runtime_public_snapshot()
            digest = _status_snapshot_stable_hash(snapshot)
            changed = digest != get_setting("status_feed.last_hash", "")
            active_or_queued = bool(snapshot.get("current_task")) or int(snapshot.get("queue_count") or 0) > 0
            force_due = active_or_queued and (now - last_push >= force_seconds)

            if not changed and not force_due:
                return

            (repo / "status.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
            result = _status_feed_git_push(repo)
            if result in {"STATUS_FEED_PUSHED", "STATUS_FEED_NO_CHANGE"}:
                set_setting("status_feed.last_hash", digest)
                set_setting("status_feed.last_push_epoch", str(now))
                set_setting("status_feed.last_success_at", now_iso())
                set_setting("status_feed.last_error", "")
            else:
                set_setting("status_feed.last_error", _sanitize_public_status_text(result, 400))
        except Exception as exc:
            set_setting("status_feed.last_error", f"{type(exc).__name__}: {_sanitize_public_status_text(exc, 320)}")

def runtime_status_feed_tick_async() -> None:
    """Never let Git/GitHub status publishing block job dispatch or recovery."""
    global _STATUS_FEED_THREAD
    if get_setting("status_feed.enabled", "0") != "1":
        return
    with _STATUS_FEED_THREAD_LOCK:
        if _STATUS_FEED_THREAD and _STATUS_FEED_THREAD.is_alive():
            return
        _STATUS_FEED_THREAD = threading.Thread(
            target=runtime_status_feed_tick,
            name="MylesStatusFeed",
            daemon=True,
        )
        _STATUS_FEED_THREAD.start()


def install_python_packages(job_id: str, packages: list[str]) -> str:
    if not packages:
        return "No packages requested."
    argv = [sys.executable, "-m", "pip", "install", *packages]
    trace(job_id, "tool.start", json.dumps(packages), tool="install_python_packages")
    out = run_process(job_id, argv, 1800)
    ok = "exit_code=0" in out
    trace(job_id, "tool.result", out, tool="install_python_packages", ok=ok)
    if ok:
        set_job(job_id, material_progress_at=now_iso())
    return out


def system_status(job_id: str) -> str:
    cmd = r"""
$ErrorActionPreference='SilentlyContinue'
$o=[ordered]@{}
$o.time=(Get-Date).ToString('o')
$o.computer=$env:COMPUTERNAME
$o.user=$env:USERNAME
$o.os=(Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,LastBootUpTime)
$o.cpu=(Get-CimInstance Win32_Processor | Select-Object Name,LoadPercentage)
$o.memory=(Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory)
$o.disk=(Get-PSDrive -Name C | Select-Object Used,Free)
try { $o.ollama=((Invoke-RestMethod http://127.0.0.1:11434/api/tags -TimeoutSec 3).models.name -join ',') } catch { $o.ollama='offline' }
$o | ConvertTo-Json -Depth 5
"""
    return run_powershell(job_id, cmd, 30)


def _ensure_playwright(job_id: str) -> str | None:
    try:
        import playwright.sync_api  # noqa
        return None
    except Exception:
        out = install_python_packages(job_id, ["playwright"])
        if "exit_code=0" not in out:
            return "Playwright package install failed:\n" + out
        out2 = run_process(job_id, [sys.executable, "-m", "playwright", "install", "chromium"], 1800)
        if "exit_code=0" not in out2:
            return "Chromium install failed:\n" + out2
        return None


def browser_automation(job_id: str, url: str, actions: list[dict[str, Any]], headless: bool | None = None) -> str:
    refused = _guard_pinetree("browser_automation", url, actions)
    if refused:
        trace(job_id, "tool.refused", refused, tool="browser_automation", ok=False)
        return refused
    err = _ensure_playwright(job_id)
    if err:
        trace(job_id, "tool.result", err, tool="browser_automation", ok=False)
        return err

    from playwright.sync_api import sync_playwright

    cfg = load_config()
    if headless is None:
        headless = bool(cfg.get("browser_headless", True))
    profile = Path(cfg.get("browser_profile_dir") or (DATA / "browser_profile"))
    profile.mkdir(parents=True, exist_ok=True)
    results = []

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=headless,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        results.append(f"GOTO {page.url}")

        for action in actions[:50]:
            set_job(job_id, heartbeat_at=now_iso(), phase="tool:browser")
            kind = str(action.get("type", "")).lower()
            selector = action.get("selector")
            if kind == "click":
                page.locator(selector).click(timeout=30000)
                results.append(f"CLICK {selector}")
            elif kind == "fill":
                page.locator(selector).fill(str(action.get("value", "")), timeout=30000)
                results.append(f"FILL {selector}")
            elif kind == "press":
                page.locator(selector).press(str(action.get("key", "Enter")), timeout=30000)
                results.append(f"PRESS {selector} {action.get('key','Enter')}")
            elif kind == "wait":
                page.wait_for_timeout(int(action.get("ms", 1000)))
                results.append(f"WAIT {action.get('ms',1000)}ms")
            elif kind == "text":
                text = page.locator(selector).inner_text(timeout=30000)
                results.append(f"TEXT {selector}: {text[:8000]}")
            elif kind == "screenshot":
                dest = _expand(str(action.get("path") or (WORKSPACES / job_id / "browser.png")))
                dest.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(dest), full_page=bool(action.get("full_page", True)))
                results.append(f"SCREENSHOT {dest}")
            elif kind == "goto":
                page.goto(str(action.get("url")), wait_until="domcontentloaded", timeout=90000)
                results.append(f"GOTO {page.url}")
            else:
                results.append(f"SKIP unknown action {kind}")

        results.append(f"FINAL_URL {page.url}")
        ctx.close()

    out = "\n".join(results)
    trace(job_id, "tool.result", out, tool="browser_automation", ok=True)
    set_job(job_id, material_progress_at=now_iso())
    return out


def _send_email(subject: str, body: str, target: str) -> str:
    cfg = load_config()
    if not cfg.get("smtp_enabled"):
        return "SMTP is not configured."
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["smtp_username"]
    msg["To"] = target
    msg.set_content(body)
    with smtplib.SMTP(cfg["smtp_host"], int(cfg.get("smtp_port", 587)), timeout=30) as s:
        s.starttls()
        s.login(cfg["smtp_username"], cfg["smtp_password"])
        s.send_message(msg)
    return f"Sent to {target}"


def notify_owner(job_id: str, message: str, channel: str = "auto") -> str:
    text = str(message or "").strip()
    if not text:
        return "No message supplied."
    cfg = load_config()
    if cfg.get("telegram_enabled"):
        add_message("telegram", "assistant", text, job_id)
        out = "Queued owner notification for Telegram."
    else:
        add_message("system", "assistant", text, job_id)
        out = "Saved owner notification locally; Telegram is not configured."
    trace(job_id, "tool.result", out, tool="notify_owner", ok=True)
    return out

def self_clone_candidate(job_id: str, description: str = "") -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = UPDATES / f"candidate_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    include = [
        "myles_common.py", "myles_runtime_v9.py", "myles_capabilities.py", "myles_quick.py",
        "myles_tools.py", "job_worker.py", "myles_core.py",
        "myles_console.py", "configure_telegram.py", "restart_helper.py",
        "self_test.py", "README.txt",
    ]
    copied = []
    for name in include:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, dest / name)
            copied.append(name)
    (dest / "CANDIDATE.json").write_text(json.dumps({
        "created_at": now_iso(),
        "from_version": APP_VERSION,
        "description": description,
        "files": copied,
    }, indent=2), encoding="utf-8")
    out = f"CANDIDATE_PATH={dest}\nFILES={copied}"
    trace(job_id, "tool.result", out, tool="self_clone_candidate", ok=True)
    set_job(job_id, material_progress_at=now_iso())
    return out


def self_verify_candidate(job_id: str, candidate_path: str) -> str:
    p = _expand(candidate_path)
    if not p.is_dir() or UPDATES not in p.parents:
        return "REFUSED: candidate must be inside the Myles self_updates directory."

    required = {
        "myles_common.py", "myles_runtime_v9.py", "myles_capabilities.py", "myles_quick.py",
        "myles_tools.py", "job_worker.py", "myles_core.py",
        "restart_helper.py", "self_test.py",
    }
    missing = sorted(name for name in required if not (p / name).exists())
    if missing:
        out = "compile_ok=False\nmissing_required_runtime_files=" + ",".join(missing)
        trace(job_id, "tool.result", out, tool="self_verify_candidate", ok=False)
        return out

    ok_compile = compileall.compile_dir(str(p), quiet=1)
    test = p / "self_test.py"
    if not test.exists():
        out = f"compile_ok={ok_compile}\nself_test.py missing"
        trace(job_id, "tool.result", out, tool="self_verify_candidate", ok=False)
        return out
    proc = subprocess.run(
        [sys.executable, str(test)],
        cwd=str(p),
        capture_output=True,
        text=True,
        timeout=120,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    out = f"compile_ok={ok_compile}\nself_test_exit={proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    ok = ok_compile and proc.returncode == 0
    trace(job_id, "tool.result", out, tool="self_verify_candidate", ok=ok)
    if ok:
        set_job(job_id, material_progress_at=now_iso())
    return out[-40000:]


def self_promote_candidate(job_id: str, candidate_path: str) -> str:
    p = _expand(candidate_path)
    verify = self_verify_candidate(job_id, str(p))
    if "compile_ok=True" not in verify or "self_test_exit=0" not in verify:
        return "PROMOTION BLOCKED: candidate verification failed.\n" + verify

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUPS / f"pre_self_update_{stamp}"
    backup.mkdir(parents=True, exist_ok=True)

    candidate_files = [
        f for f in p.iterdir()
        if f.is_file() and f.name not in {"CANDIDATE.json"}
    ]
    for src in candidate_files:
        dst = ROOT / src.name
        if dst.exists():
            shutil.copy2(dst, backup / dst.name)

    for src in candidate_files:
        shutil.copy2(src, ROOT / src.name)

    request = DATA / "restart.request"
    request.write_text(json.dumps({
        "requested_at": now_iso(),
        "job_id": job_id,
        "candidate": str(p),
        "backup": str(backup),
    }, indent=2), encoding="utf-8")

    out = f"PROMOTED candidate={p}\nBACKUP={backup}\nRESTART_REQUESTED={request}"
    trace(job_id, "tool.result", out, tool="self_promote_candidate", ok=True)
    set_job(job_id, material_progress_at=now_iso())
    return out
