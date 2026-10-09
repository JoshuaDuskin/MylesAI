from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

STOP_PATTERNS = (
    r"^\s*(stop|cancel|abort|quit|drop it|stop that|cancel that|stop the task|cancel the task|stop current work|cancel current work)\s*[.!]?\s*$",
    r"^\s*(please\s+)?(stop|cancel|abort)\s+(what you(?:'re| are) doing|the current task|current work|the current work|this task|that task|it)\s*[.!]?\s*$",
)
RESUME_PATTERNS = (
    r"\b(?:don'?t|do not)\s+stop\b",
    r"\bkeep\s+going\b",
    r"\bcontinue\b",
    r"\bresume\b",
    r"\bcarry\s+on\b",
)
STATUS_MARKERS = (
    "what are you doing",
    "what're you doing",
    "what are you working on",
    "what's happening",
    "what happened",
    "progress",
    "status",
    "still running",
    "still working",
    "are you working",
    "are you trying",
    "you trying",
    "did it finish",
    "is it finished",
    "is it done",
    "how's it going",
    "hows it going",
)
ACTION_HINTS = (
    "build", "create", "make", "write", "edit", "modify", "change", "fix",
    "repair", "install", "download", "set up", "setup", "deploy", "host",
    "publish", "delete", "remove", "move", "rename", "update", "upgrade",
    "configure", "implement", "test", "inspect", "investigate", "automate",
    "check", "find", "send", "grab", "snapshot", "monitor",
    "redesign", "refresh", "improve", "polish", "add", "adjust", "tweak",
    "simplify", "rework", "redo",
    "audit", "review", "verify",
    "look through", "go through", "look at",
)
TOOL_ALIASES = {
    "powershell": "run_powershell",
    "shell": "run_powershell",
    "write_file": "write_text_file",
    "read_file": "read_text_file",
    "list_files": "list_directory",
    "fetch_url": "web_fetch",
    "git": "git_command",
    "github_pages": "github_pages_publish",
    "generate_file": "write_generated_file",
    "write_generated": "write_generated_file",
    "patch_file": "apply_text_patch",
}

class PlannerParseError(RuntimeError):
    pass

@dataclass(frozen=True)
class ToolOutcome:
    kind: str
    ok: bool
    retryable: bool = False
    owner_gate: bool = False
    refused: bool = False

def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())

def likely_action_request(text: str) -> bool:
    t = normalize_text(text)
    if not t:
        return False
    return any(re.search(rf"\b{re.escape(h)}\b", t) for h in ACTION_HINTS)

BEHAVIOR_FEEDBACK_PATTERNS = (
    r"\bi\s+didn'?t\s+ask\b",
    r"\bi\s+wasn'?t\s+asking\b",
    r"\bi(?:'m| am)\s+just\s+(?:talking|saying|asking)\b",
    r"\bis there anything you need to (?:fix|change|do)\b",
    r"\bwhat do you need to (?:fix|change|do)\b",
    r"\bwhy are you (?:sending|giving|creating|making)\b",
    r"\bthis should (?:just )?be a quick\b",
    r"\bthat should (?:just )?be a quick\b",
    r"\bshould(?:'ve| have) been a quick\b",
    r"\bnot (?:a|the) (?:whole )?(?:job|task)\b",
    r"\bdon'?t (?:make|turn) (?:this|that|everything) into (?:a )?(?:job|task)\b",
    r"\bstop (?:making|turning) (?:this|that|everything) into (?:a )?(?:job|task)\b",
    r"\bwhy (?:did|are) you (?:start|starting|create|creating) (?:a )?(?:job|task)\b",
    r"\bjust (?:answer|tell me|look it up|search it|google it)\b",
    r"\bno need (?:for|to make) (?:a )?(?:job|task)\b",
    r"\bi(?:'m| am) (?:not )?asking you to (?:build|change|modify|edit|fix) anything\b",
)


def behavior_feedback_request(text: str) -> bool:
    """Owner is correcting Myles's behavior, not asking to mutate the last artifact.

    Feedback must never be auto-promoted to a follow-up job merely because recent
    conversation involved a project. This is especially important for messages
    like "that should have been a quick search, not a whole job".
    """
    t = normalize_text(text)
    if not t:
        return False
    if any(re.search(p, t, flags=re.I) for p in BEHAVIOR_FEEDBACK_PATTERNS):
        return True
    # Catch compact corrections around the durable-job boundary without making
    # every complaint a special control command.
    if ("job" in t or "task" in t) and any(
        phrase in t
        for phrase in (
            "quick search", "quick lookup", "google search", "just answer",
            "too much", "whole fucking", "whole damn", "doesn't need",
            "does not need", "shouldn't need", "should not need",
        )
    ):
        return True
    return False

STRONG_ACTION_VERBS = (
    "build", "create", "make", "write", "edit", "modify", "change", "fix",
    "repair", "install", "download", "set up", "setup", "deploy", "host",
    "publish", "delete", "remove", "move", "rename", "update", "upgrade",
    "configure", "implement", "automate", "send", "grab", "snapshot",
    "redesign", "refresh", "improve", "polish", "add", "adjust", "tweak",
    "simplify", "rework", "redo",
    "check", "inspect", "investigate", "audit", "review", "verify",
    "look through", "go through", "look at",
)

INFORMATIONAL_PREFIXES = (
    "how do ", "how can ", "how would ", "what is ", "what are ",
    "why ", "where ", "when ", "who ", "is ", "are ", "do ", "does ",
    "did ", "should ", "explain ", "tell me how ", "show me how ", "teach me ",
)


def natural_question(text: str) -> bool:
    """Separate questions from imperative work requests."""
    raw = str(text or "").strip()
    t = normalize_text(raw)
    if not t:
        return False
    action = "|".join(re.escape(v) for v in STRONG_ACTION_VERBS)
    explicit_action_question = re.match(
        rf"^(?:can|could|would|will)\s+you\s+(?:please\s+)?(?:{action})\b", t
    )
    if explicit_action_question:
        return False
    return "?" in raw or any(t.startswith(prefix) for prefix in INFORMATIONAL_PREFIXES)

def strong_action_request(text: str) -> bool:
    """High-confidence owner instruction to actually do work.

    This is intentionally narrower than likely_action_request. It prevents long
    imperative tasks containing words such as "progress" or "status" from being
    hijacked by the deterministic status controller.
    """
    t = normalize_text(text)
    if not t:
        return False
    if natural_question(text):
        return False

    verb_pattern = "|".join(re.escape(v) for v in STRONG_ACTION_VERBS)
    if re.match(rf"^(?:please\s+)?(?:{verb_pattern})\b", t):
        return True
    if re.match(rf"^(?:can|could|would|will)\s+you\s+(?:please\s+)?(?:{verb_pattern})\b", t):
        return True
    if re.match(rf"^(?:i\s+(?:want|need)\s+you\s+to|go\s+ahead\s+and)\s+(?:{verb_pattern})\b", t):
        return True
    return False


FOLLOWUP_REFERENCE_MARKERS = (
    " the site", " the page", " the dashboard", " the design", " the app",
    " same one", " same thing", " what you built", " what you made",
    " what you were working on", " what you're working on",
)

SELF_CAPABILITY_PATTERNS = (
    r"\badd\s+(?:the\s+)?tools?\s+to\s+(?:your|myles(?:'s)?)\s+(?:kit|toolbox|setup)\b",
    r"\b(?:add|install|set up|get)\s+(?:yourself\s+)?(?:a\s+|the\s+)?(?:tool|tools|capability|capabilities|plugin|plugins|package|packages)\b",
    r"\b(?:give|add)\s+yourself\s+(?:a\s+)?(?:tool|tools|capability|capabilities)\b",
    r"\b(?:improve|upgrade|fix)\s+(?:your|myles(?:'s)?)\s+(?:tools|tooling|capabilities|lookup|search)\b",
)

def self_capability_request(text: str) -> bool:
    """True when the owner is asking Myles to improve/provision Myles itself.

    These are real system changes, but they are never edits to the most recent
    project workspace merely because the sentence contains pronouns such as
    "it" in "look it up".
    """
    t = normalize_text(text)
    if not t:
        return False
    return any(re.search(p, t, flags=re.I) for p in SELF_CAPABILITY_PATTERNS)

def followup_action_request(text: str) -> bool:
    """Detect natural follow-up work requests even when they do not start with a verb."""
    raw = str(text or "").strip()
    t = normalize_text(raw)
    if not t:
        return False

    if natural_question(raw):
        return False
    if re.match(r"^(?:can|could|would)\s+you\s+(?:tell|show|explain)\b", t):
        return False
    if explicit_stop_requested(raw):
        return False
    if behavior_feedback_request(raw):
        return False
    if self_capability_request(raw):
        return False

    verbs = "|".join(re.escape(v) for v in STRONG_ACTION_VERBS)

    if re.search(rf"\b(?:i\s+(?:told|asked)\s+you\s+to|you\s+need\s+to|i\s+need\s+you\s+to)\s+(?:{verbs})\b", t):
        return True

    clauses = [c.strip(" ,:-") for c in re.split(r"[.!?;]+", t) if c.strip()]
    soft_prefix = re.compile(
        r"^(?:ok(?:ay)?|alright|all right|yeah|yes|yep|good|great|"
        r"it looks good|that looks good|looks good|also|but|and)\b[\s,:-]*"
    )
    for clause in clauses:
        c = clause
        for _ in range(3):
            newer = soft_prefix.sub("", c, count=1)
            if newer == c:
                break
            c = newer.strip()
        if re.match(rf"^(?:please\s+)?(?:{verbs})\b", c):
            return True

    if re.search(rf"\b(?:{verbs})\s+(?:it|that|this|the\s+(?:site|page|dashboard|design|app))\b", t):
        return True
    return False

def refers_to_previous_result(text: str) -> bool:
    """Detect an actual artifact/result reference, not any generic pronoun.

    v9.3 used markers such as plain " it", so a sentence like
    "add the tools to your kit so you can look it up" could accidentally attach
    itself to the previous dashboard workspace. References now require an
    artifact noun or an edit-style verb around the pronoun.
    """
    t = " " + normalize_text(text)
    if any(marker in t for marker in FOLLOWUP_REFERENCE_MARKERS):
        return True
    if re.search(
        r"\b(?:fix|redesign|refresh|improve|polish|adjust|tweak|rework|redo|edit|modify|change|update|make)\s+(?:it|that|this)\b",
        t,
    ):
        return True
    if re.search(
        r"\b(?:add|put|include)\b.{0,80}\b(?:to|on|into)\s+(?:it|that|this)\b",
        t,
    ):
        return True
    return False

def execution_promise_text(text: str) -> bool:
    """Detect prose that claims future computer work without execution evidence."""
    t = normalize_text(text)
    patterns = (
        r"\bi(?:'ll| will)\s+(?:start|build|fix|change|update|redesign|refresh|work|do|make|edit|modify|handle)\b",
        r"\blet me\s+(?:start|get started|work on|build|fix|change|update|redesign|refresh)\b",
        r"\bi(?:'m| am)\s+going to\s+(?:start|build|fix|change|update|redesign|refresh|work|do|make)\b",
        r"\bget started on that\b",
        r"\bstart that now\b",
        r"\bget to work on\b",
    )
    return any(re.search(p, t, flags=re.I) for p in patterns)

def explicit_stop_requested(text: str) -> bool:
    t = normalize_text(text)
    # Negative-stop language must never be treated as stop.
    if re.search(r"\b(?:don'?t|do not|never)\s+stop\b", t):
        return False
    return any(re.search(p, t, flags=re.I) for p in STOP_PATTERNS)

def explicit_resume_requested(text: str) -> bool:
    t = normalize_text(text)
    return any(re.search(p, t, flags=re.I) for p in RESUME_PATTERNS)

def looks_like_status_request(text: str, *, has_active: bool = False) -> bool:
    """Return True only for high-confidence status questions/commands.

    A long build/fix request is never a status request merely because its desired
    output contains fields named "progress" or "status".
    """
    raw = str(text or "").strip()
    t = normalize_text(raw)
    if not t or strong_action_request(raw):
        return False

    words = t.split()
    short = len(words) <= 20
    questionish = "?" in raw or t.startswith((
        "what ", "how ", "is ", "are ", "did ", "has ", "have ",
        "show me ", "give me ", "check ", "tell me ",
    ))

    direct_phrases = (
        "what are you doing", "what're you doing", "what are you working on",
        "what's happening", "what happened", "still running", "still working",
        "are you working", "are you trying", "you trying", "did it finish",
        "is it finished", "is it done", "you about done", "almost done",
        "about done", "how's it going", "hows it going",
    )
    if any(m in t for m in direct_phrases) and (short or questionish):
        return True

    # Bare progress/status requests are status; mentions inside a build spec are not.
    if any(m in t for m in ("progress", "status")) and short and questionish:
        return True
    if t in {"progress", "status", "current status", "task status", "current progress"}:
        return True

    if has_active and questionish and short and any(
        w in t for w in ("again", "trying", "working", "running", "doing")
    ):
        return True
    return False

def deterministic_control(text: str, *, has_active: bool, has_recent_cancelled: bool = False) -> str | None:
    if explicit_resume_requested(text) and has_recent_cancelled and not has_active:
        return "resume"
    if explicit_stop_requested(text):
        return "stop"
    if looks_like_status_request(text, has_active=has_active):
        return "status"
    return None
def _strip_fence(text: str) -> str:
    t = str(text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.I)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()

def parse_json_object(raw: str) -> dict[str, Any]:
    text = _strip_fence(raw)
    candidates = [text]
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        sliced = text[start:end+1]
        if sliced != text:
            candidates.append(sliced)

    last_error: Exception | None = None
    for candidate in candidates:
        for strict in (True, False):
            try:
                obj = json.loads(candidate, strict=strict)
                if isinstance(obj, dict):
                    return obj
            except Exception as exc:
                last_error = exc
    raise PlannerParseError("model output did not contain a parseable JSON object") from last_error

def normalize_action_plan(raw: str, allowed_tools: set[str]) -> tuple[str, dict[str, Any]]:
    plan = parse_json_object(raw)
    tool_value = plan.get("tool")
    args = plan.get("arguments")

    if isinstance(tool_value, dict):
        if args is None:
            args = tool_value.get("arguments") or tool_value.get("args")
        tool_value = tool_value.get("name") or tool_value.get("tool")

    fn = plan.get("function")
    if not tool_value and isinstance(fn, dict):
        tool_value = fn.get("name")
        if args is None:
            args = fn.get("arguments") or fn.get("args")

    if not tool_value:
        tool_value = plan.get("name")

    tool = TOOL_ALIASES.get(str(tool_value or "").strip(), str(tool_value or "").strip())

    if args is None:
        args = plan.get("args")

    if isinstance(args, str):
        try:
            parsed = json.loads(args, strict=False)
            args = parsed if isinstance(parsed, dict) else None
        except Exception:
            args = None

    if not isinstance(args, dict):
        reserved = {"tool", "name", "function", "arguments", "args"}
        args = {k: v for k, v in plan.items() if k not in reserved}

    if tool not in allowed_tools:
        raise PlannerParseError(f"planner selected unknown tool: {tool!r}")
    return tool, args

def parse_native_arguments(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            obj = json.loads(value, strict=False)
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None

def classify_tool_result(result: str) -> ToolOutcome:
    t = str(result or "").lstrip()
    upper = t.upper()
    if upper.startswith("OWNER_AUTH_REQUIRED:"):
        return ToolOutcome("auth", False, owner_gate=True)
    if upper.startswith("REFUSED:") or upper.startswith("REFUSED_PINETREE:"):
        return ToolOutcome("refused", False, refused=True)
    if upper.startswith("TIMEOUT"):
        return ToolOutcome("timeout", False, retryable=True)
    if upper.startswith("TOOL_ERROR") or upper.startswith("ERROR:"):
        retry_markers = (
            "temporar", "timeout", "timed out", "connection", "network",
            "rate limit", "busy", "locked", "try again", "not ready",
        )
        low = t.lower()
        return ToolOutcome("error", False, retryable=any(m in low for m in retry_markers))
    if "exit_code=" in t:
        m = re.search(r"exit_code=(-?\d+)", t)
        if m and int(m.group(1)) != 0:
            return ToolOutcome("process_error", False)
    return ToolOutcome("ok", True)

def compact_task_signature(text: str) -> str:
    t = normalize_text(text)
    t = re.sub(r"[^a-z0-9\s]+", " ", t)
    words = [w for w in t.split() if w not in {
        "the","a","an","please","for","to","and","of","my","this","that","it"
    }]
    return " ".join(words[:80])
