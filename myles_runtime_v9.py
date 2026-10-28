from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

STOP_PATTERNS = (
    r"^\s*(stop|cancel|abort|quit|drop it|stop that|cancel that|stop the task|cancel the task|stop current work|cancel current work)\s*[.!]?\s*$",
    r"^\s*(please\s+)?(stop|cancel|abort)\s+(what you(?:'re| are) doing|the current task|current work|the current work|this task|that task|it)\s*[.!]?\s*$",
    r"^\s*(please\s+)?(?:stop|cancel|abort)\s+(?:the\s+)?(?:current\s+)?[a-z0-9][a-z0-9 _-]{0,60}\s+(?:task|job|work)\s*[.!]?\s*$",
)
STOP_ALL_PATTERNS = (
    r"\b(?:stop|cancel|abort|quit|clear|drop)\s+(?:all|every)\s+(?:(?:currently|current|running|active|pending|queued|queue)\s+)*(?:tasks?|jobs?|work|queues?)\b",
    r"\b(?:stop|cancel|abort|quit|clear|empty)\s+(?:the\s+)?(?:entire\s+)?(?:task\s+|job\s+)?queue\b",
    r"\b(?:stop|cancel|abort|quit)\s+(?:everything|all\s+of\s+it)\b",
    r"\b(?:stop|cancel|abort|quit)\s+(?:all\s+)?(?:running|active)\s+(?:tasks?|jobs?|work)\b",
    r"\b(?:stop|cancel|abort|quit)\s+current\s+(?:tasks|jobs)\b",
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
    "open", "close", "launch", "start", "run", "use", "press", "click",
    "quit", "terminate", "end", "shut down",
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
    "open", "close", "launch", "start", "run", "use", "press", "click",
    "quit", "terminate", "end", "shut down",
    "repair", "install", "download", "set up", "setup", "deploy", "host",
    "publish", "delete", "remove", "move", "rename", "update", "upgrade",
    "configure", "implement", "automate", "send", "grab", "snapshot",
    "redesign", "refresh", "improve", "polish", "add", "adjust", "tweak",
    "simplify", "rework", "redo",
    "check", "inspect", "investigate", "audit", "review", "verify",
    "look through", "go through", "look at",
)


def _strip_owner_action_framing(text: str) -> str:
    """Remove conversational wrappers while preserving the owner's command."""
    value = re.sub(r"\s+", " ", str(text or "").strip())
    value = value.replace("’", "'").replace("‘", "'")
    value = re.sub(r"[.!?]+$", "", value).strip()
    prefixes = (
        r"^(?:hey\s+)?myles\s*[,;:]?\s*",
        r"^please\s+",
        r"^would\s+you\s+mind\s+(?:please\s+)?",
        r"^(?:can|could|would|will)\s+you\s+(?:please\s+)?",
        r"^i\s+(?:want|need)\s+you\s+to\s+",
        r"^i(?:'d|\s+would)\s+like\s+you\s+to\s+",
        r"^go\s+ahead\s+and\s+",
        r"^do\s+me\s+a\s+favor\s+and\s+",
        r"^(?:let(?:'s|\s+us)|make\s+sure\s+you)\s+",
        r"^(?:just|actually)\s+",
    )
    for _ in range(5):
        previous = value
        for pattern in prefixes:
            value = re.sub(pattern, "", value, count=1, flags=re.I).strip()
        if value == previous:
            break
    return value


def app_launch_target(text: str) -> str:
    """Extract an app/surface target from ordinary owner launch language.

    This is deliberately app-agnostic. The Windows layer resolves the returned
    name against the live Start-menu registry instead of maintaining a catalog
    of every application the owner might install.
    """
    value = _strip_owner_action_framing(text)
    if not value or len(value) > 180:
        return ""

    match = re.match(
        r"(?is)^(?:open|launch|start|run|load|fir(?:e|ing)\s+up|pull(?:ing)?\s+up|bring(?:ing)?\s+up)\s+(?:up\s+)?(.+)$",
        value,
    )
    if not match:
        match = re.match(r"(?is)^(?:get\s+)?(.+?)\s+(?:open|opened)$", value)
    if not match:
        return ""
    target = match.group(1).strip()
    # Remove conversational tail modifiers without altering names in the middle.
    tail = r"\s+(?:instead|now|please|for\s+me|real\s+quick|on\s+(?:the\s+)?(?:tower|computer|pc))$"
    for _ in range(4):
        cleaned = re.sub(tail, "", target, count=1, flags=re.I).strip()
        if cleaned == target:
            break
        target = cleaned
    target = re.sub(r"(?i)^the\s+", "", target).strip()
    target = re.sub(r"(?i)\s+(?:app|application)$", "", target).strip()
    if target.casefold() in {"", "app", "application", "program", "it", "this", "that",
                              "windows", "open windows", "running apps", "running applications", "applications"}:
        return ""
    if any(marker in target.casefold() for marker in ("http://", "https://", " website", " file", " folder")):
        return ""
    return target if 2 <= len(target) <= 80 else ""


def desktop_action_request(text: str) -> dict[str, str] | None:
    """Recognize broad basic desktop actions without an application catalog."""
    value = _strip_owner_action_framing(text)
    if re.fullmatch(r"(?is)(?:what(?:'s| is) (?:still )?(?:open|running) and (?:flashing|blinking)(?: at me)?|what(?:'s| is) (?:flashing|blinking) at me)", value):
        return {"kind": "windows_attention"}
    if re.fullmatch(r"(?is)(?:what(?:'s| is| are) (?:still )?(?:open|running)(?: still)?|what (?:programs|apps|applications|windows) (?:are )?(?:open|running)(?: still)?|show(?: me)? (?:my |the )?(?:open |running )?(?:windows|applications|apps)(?: in detail)?|list (?:my |the )?(?:open |running )?(?:windows|applications|apps)(?: in detail)?)", value):
        return {"kind": "windows_detail" if value.endswith("in detail") else "windows"}
    status = re.fullmatch(r"(?is)is (.+?) (?:still )?(?:open|running)", value)
    if status and 1 < len(status.group(1)) <= 100:
        return {"kind": "app_status", "target": status.group(1)}
    if re.fullmatch(r"(?is)(?:show|go\s+to|open)\s+(?:the\s+)?desktop", value):
        return {"kind": "key", "keys": "WIN+D", "label": "Show desktop"}
    if re.fullmatch(r"(?is)(?:show(?: me)?|list|what are) (?:my |the )?(?:open |running )?(?:windows|applications|apps)", value):
        return {"kind": "windows"}
    if re.fullmatch(r"(?is)minimi[sz]e(?: the| this)?(?: current| active| focused)?(?: window| application| app)?", value):
        return {"kind": "minimize"}
    maximize = re.fullmatch(
        r"(?is)(?:maximize|expand)\s+(?:the\s+)?(.+?)(?:\s+window)?|"
        r"(?:put|make|set)\s+(?:the\s+)?(.+?)\s+(?:(?:in|to)\s+)?(?:full\s*screen|fullscreen|maximi[sz]ed)(?:\s+as\s+well)?"
    , value)
    if maximize:
        target = next((part for part in maximize.groups() if part), "").strip()
        if target and target.casefold() not in {"it", "this", "that", "the browser"}:
            return {"kind": "maximize", "target": target}
        if target.casefold() == "the browser":
            return {"kind": "maximize", "target": "Chrome"}
    if re.fullmatch(r"(?is)switch to (?:another|a different) (?:app|application|window)", value):
        return {"kind": "windows"}
    forced = re.fullmatch(r"(?is)force (?:close|quit|terminate) (.+)", value)
    if forced:
        return {"kind": "close", "target": forced.group(1), "force": True}
    launch = app_launch_target(text)
    if launch:
        return {"kind": "launch", "target": launch}
    if not value or len(value) > 500:
        return None

    def clean_target(raw: str) -> str:
        target = re.sub(r"(?i)^the\s+", "", raw.strip())
        target = re.sub(r"(?i)\s+(?:app|application|window)$", "", target).strip()
        target = re.sub(r"(?i)\s+(?:now|please|for\s+me)$", "", target).strip()
        return target if 1 < len(target) <= 100 and target.casefold() not in {"it", "this", "that"} else ""

    match = re.match(r"(?is)^(?:close|quit|exit|terminate|end|dismiss|shut\s+down)\s+(.+)$", value)
    if match and (target := clean_target(match.group(1))):
        return {"kind": "close", "target": target}
    match = re.match(r"(?is)^(?:focus|activate|switch\s+(?:over\s+)?to|bring\s+forward|go\s+to)\s+(.+)$", value)
    if match and (target := clean_target(match.group(1))):
        return {"kind": "focus", "target": target}
    match = re.match(r"(?is)^(?:bring|put)\s+(.+?)\s+(?:(?:to|in)\s+(?:the\s+)?front|forward)$", value)
    if match and (target := clean_target(match.group(1))):
        return {"kind": "focus", "target": target}
    match = re.match(r"(?is)^(?:press|hit|tap)\s+(.+?)(?:\s+key)?$", value)
    if match:
        keys = match.group(1).strip().upper()
        keys = re.sub(r"\s*\+\s*|\s+AND\s+", "+", keys)
        phrase_aliases = {
            "THE ENTER": "ENTER", "THE RETURN": "ENTER", "THE ESCAPE": "ESC",
            "THE ESC": "ESC", "THE SPACE BAR": "SPACE", "SPACE BAR": "SPACE",
            "THE TAB": "TAB", "WINDOWS KEY": "WIN",
        }
        keys = phrase_aliases.get(keys, keys).replace(" KEY", "")
        component_aliases = {"CONTROL": "CTRL", "WINDOWS": "WIN", "RETURN": "ENTER", "ESCAPE": "ESC"}
        if "+" not in keys:
            words = keys.split()
            known = {"CTRL", "CONTROL", "SHIFT", "ALT", "WIN", "WINDOWS", "ENTER", "RETURN", "TAB", "ESC", "ESCAPE", "DELETE"}
            if len(words) > 1 and all(word in known or len(word) == 1 for word in words):
                keys = "+".join(words)
        keys = "+".join(component_aliases.get(part, part) for part in keys.split("+"))
        if re.fullmatch(r"[A-Z0-9+]+", keys) and 1 <= len(keys) <= 40:
            return {"kind": "key", "keys": keys, "label": f"Press {keys}"}
    match = re.match(r"(?is)^type\s+(.+)$", value)
    if match:
        typed = match.group(1).strip()
        if len(typed) >= 2 and typed[0] == typed[-1] and typed[0] in {'"', "'"}:
            typed = typed[1:-1]
        if typed and len(typed) <= 8000:
            return {"kind": "type", "text": typed, "label": "Type into the focused control"}
    if re.match(r"(?is)^(?:click|double[- ]click|right[- ]click|select|choose|scroll|drag)\b", value):
        return {"kind": "visual", "label": value[:160]}
    return None

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
        r"\bi(?:'m| am)\s+(?:closing|opening|launching|starting|running|clicking|pressing|terminating|ending|shutting down|fixing|changing|updating)\b",
        r"\bget started on that\b",
        r"\bstart that now\b",
        r"\bget to work on\b",
    )
    return any(re.search(p, t, flags=re.I) for p in patterns)

def stop_request_scope(text: str) -> str | None:
    """Return ``all`` or ``current`` only for an explicit owner cancellation.

    Global cancellation language is intentionally recognized inside a longer
    correction (for example, "I told you to stop all tasks") because it must
    outrank desktop verbs and follow-up routing. Questions about why something
    stopped are not cancellation commands.
    """
    t = normalize_text(text)
    # Negative-stop language must never be treated as stop.
    if re.search(r"\b(?:don'?t|do not|never)\s+stop\b", t):
        return None
    if re.match(r"^(?:why|how|when|what)\b", t) and "?" in str(text or ""):
        return None
    if any(re.search(p, t, flags=re.I) for p in STOP_ALL_PATTERNS):
        return "all"
    if any(re.search(p, t, flags=re.I) for p in STOP_PATTERNS):
        return "current"
    embedded_current = (
        r"\b(?:i\s+(?:said|told|asked)\s+you\s+to\s+|please\s+)"
        r"(?:stop|cancel|abort)\s+(?:what you(?:'re| are) doing|the current task|current work|this task|that task|it)\b"
    )
    return "current" if re.search(embedded_current, t, flags=re.I) else None


def explicit_stop_requested(text: str) -> bool:
    return stop_request_scope(text) is not None

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
    stop_scope = stop_request_scope(text)
    if stop_scope:
        return "stop_all" if stop_scope == "all" else "stop"
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
    if upper.startswith((
        "DESKTOP_APP_LAUNCH_ERROR:",
        "DESKTOP_APP_LAUNCH_NOT_VERIFIED:",
        "DESKTOP_APP_LAUNCH_UNAVAILABLE:",
        "FORTNITE_LAUNCH_ERROR:",
        "FORTNITE_NOT_VERIFIED:",
        "FORTNITE_LAUNCH_UNAVAILABLE:",
    )):
        return ToolOutcome("not_verified", False)
    if '"MARKER": "DESKTOP_APP_CLOSE_FAILED"' in upper:
        return ToolOutcome("not_verified", False)
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
