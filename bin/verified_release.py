"""CI-verified releases: public GitHub workflow status only, no executable requests.

Fetches GitHub's first-party Actions API over TLS. Rejects pending, failed,
skipped or mismatched runs; never trusts commit messages, issue comments, README
text or arbitrary URLs as commands to execute on the tower.
"""
from __future__ import annotations

import json
import re
import urllib.request
from typing import Any

REPO = "JoshuaDuskin/MylesAI"
WORKFLOW = "validate-runtime.yml"
API = ("https://api.github.com/repos/" + REPO +
       "/actions/workflows/" + WORKFLOW +
       "/runs?branch=main&event=push&per_page=20")
SHA = re.compile(r"[0-9a-f]{40}\Z")


def approved_run(target_sha: str, payload: dict[str, Any]) -> bool:
    if not isinstance(target_sha, str) or not SHA.fullmatch(target_sha):
        return False
    if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
        return False
    for row in payload["workflow_runs"][:20]:
        if not isinstance(row, dict):
            continue
        owner = (row.get("repository") or {})
        if not isinstance(owner, dict):
            continue
        if (
            str(row.get("head_sha") or "").lower() == target_sha
            and row.get("event") == "push"
            and row.get("status") == "completed"
            and row.get("conclusion") == "success"
            and row.get("head_branch") == "main"
            and row.get("path") == ".github/workflows/validate-runtime.yml"
            and owner.get("full_name") == REPO
        ):
            return True
    return False


def verify_ci(target_sha: str) -> bool:
    if not isinstance(target_sha, str) or not SHA.fullmatch(target_sha):
        return False
    request = urllib.request.Request(
        API,
        headers={"Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "MylesAI-Owner-Tower-CI-Update/1"},
    )
    with urllib.request.urlopen(request, timeout=15) as reply:
        # Bound content independently from potentially malicious headers.
        data = reply.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError("CI metadata exceeds size limit")
    return approved_run(target_sha, json.loads(data))


def candidate_allowed(
    target_sha: str, installed_sha: str, state: dict[str, Any],
    green: bool, fast_forward: bool,
) -> tuple[bool, str]:
    """Pure decision, so CI and dry-run tests cannot trigger a Windows update."""
    if not isinstance(target_sha, str) or not SHA.fullmatch(target_sha):
        return False, "invalid GitHub main commit"
    if not isinstance(installed_sha, str) or not SHA.fullmatch(installed_sha):
        return False, "installed source identity unavailable"
    if target_sha == installed_sha:
        return False, "already installed"
    if not fast_forward:
        return False, "new main is not descendant of installed commit"
    if not green:
        return False, "matching GitHub main push CI is not successful"
    if state.get("request_id") == "ci_" + target_sha and state.get("status") in {
        "launched", "succeeded", "failed", "failed_unverified",
    }:
        return False, "this exact source was already attempted"
    return True, "CI-approved release"
