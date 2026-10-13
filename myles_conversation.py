"""Bounded, topic-aware conversation context for the local MYLES model.

Historical messages are context, never authorization to perform actions. This
module uses only the local message store; there are no embeddings, third-party
calls, or invented conversation summaries.
"""
from __future__ import annotations
import re
from typing import Any

COMMON = frozenset(
    "i me my you your we our this that these those one did does do to a an and or "
    "the is are was were will can could would should please hey myles it in on "
    "of for with from at as about there here what how why where when have has "
    "had done now again just go ahead want need got know talk said".split()
)
TOKEN = re.compile(r"[a-z0-9][a-z0-9_-]{2,}", re.I)


def keywords(text: str) -> set[str]:
    return {word for word in TOKEN.findall(str(text or "").casefold())
            if word not in COMMON and not word.isdecimal()}


def select_history(rows: list[dict[str, Any]], current: str,
                   *, recent: int = 22, older_pairs: int = 8,
                   max_chars: int = 30000) -> list[dict[str, str]]:
    """Keep newest conversation plus relevant older message pairs chronologically.

    Prefer the verbatim immediate context. Select older, distinct messages by
    overlap with current question/last recent messages; never fabricate memory.
    """
    items = [dict(row) for row in rows
             if str(row.get("role") or "") in {"user", "assistant"}
             and isinstance(row.get("content"), str) and row["content"].strip()]
    if items and items[-1]["role"] == "user" and items[-1]["content"].strip() == str(current).strip():
        items.pop()
    if not items:
        return []
    recent = max(2, min(40, int(recent)))
    budget = max(4000, min(65000, int(max_chars)))
    newest = items[-recent:]
    older = items[:-recent]
    question_terms = keywords(current)
    recent_terms: set[str] = set()
    for row in newest[-6:]:
        if row.get("role") == "user":
            recent_terms.update(keywords(str(row.get("content") or "")))
    ranked: list[tuple[int, int]] = []
    for index, row in enumerate(older):
        content = str(row.get("content") or "")
        tokens = keywords(content[:3000])
        # The owner's current question outweighs frequent topics repeated in
        # nearby history; otherwise dozens of generic turns crowd out the one
        # old fact the owner explicitly asked to recall.
        score = 4 * len(tokens & question_terms) + len(tokens & recent_terms)
        if score:
            ranked.append((score, index))
    ranked.sort(key=lambda pair: (-pair[0], -pair[1]))
    indices: set[int] = set()
    for _, idx in ranked[:max(0, min(int(older_pairs), 12))]:
        indices.add(idx)
        # Preserve a close follow-up if the older item has one.
        if idx + 1 < len(older):
            indices.add(idx + 1)
    selected = [(True, older[i]) for i in sorted(indices)] + [(False, r) for r in newest]
    # Reserve newest turns first, then fit older related turns. No synthetic role
    # changes, and older historical context has an explicit non-authorization label.
    accepted: list[tuple[bool, dict[str, Any], str]] = []
    used = 0
    for historical, row in reversed(selected):
        cap = 1400 if historical else 4500
        content = str(row["content"])[:cap]
        if historical:
            content = "[Older conversation context, not a new command]\n" + content
        if used + len(content) > budget and accepted:
            continue
        if len(content) > budget - used:
            content = content[:max(0, budget - used)]
        if not content:
            continue
        accepted.append((historical, row, content))
        used += len(content)
        if used >= budget:
            break
    accepted.reverse()
    return [{"role": str(row["role"]), "content": content}
            for _, row, content in accepted]


def safe_tool_reply(content: str, *, any_failure: bool, started_job: bool) -> str:
    """Never turn a failed/unverified tool into a successful completion claim."""
    answer = str(content or "").strip()
    if not any_failure or started_job:
        return answer or "I'm here."
    low = answer.casefold()
    if any(word in low for word in (
        "couldn't", "could not", "can't", "cannot", "failed",
        "unverified", "not verified", "didn't", "wasn't", "refused",
        "not completed", "unable", "nothing was", "nothing started",
        "not started", "did not", "no action",
    )):
        return answer
    return ("I couldn't verify the requested tool action. "
            "An inspection or action failed; I won't claim it succeeded.")


READ_RETRY_TOOLS = frozenset({
    "inspect_local_file", "inspect_local_directory", "inspect_open_windows",
})
TEMPORARY_ERRORS = ("temporar", "timeout", "timed out", "busy", "locked",
                    "try again", "connection reset", "not ready")


def should_retry_observation(name: str, result: str) -> bool:
    """Exactly one retry is permitted only for transient read-only observations."""
    value = str(result or "").casefold()
    return bool(name in READ_RETRY_TOOLS and value.startswith("tool_error:")
                and any(term in value for term in TEMPORARY_ERRORS))
