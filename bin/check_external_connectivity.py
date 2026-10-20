"""Read-only external check from GitHub-hosted runner.

A 401 from /dashboard/health proves a reachable authentication boundary:
never include published read tokens, pairing codes, or owner authorization.
A stale GitHub Issue #49 is reported as stale rather than inferred downtime.
"""
from __future__ import annotations

import datetime as dt
import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.github.com/repos/JoshuaDuskin/MylesAI/issues/49"
ROOT = Path(__file__).resolve().parents[1]
AGENT = {"User-Agent": "MylesExternalHealth/1", "Accept": "application/vnd.github+json"}


def fetch_json(url: str, timeout: int = 9) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=timeout) as response:
        return json.load(response)


def bridge_endpoint() -> str:
    config = json.loads((ROOT / "bridge.json").read_text(encoding="utf-8"))
    endpoint = str(config.get("url") or config.get("bridge_url") or "").rstrip("/")
    parts = urllib.parse.urlsplit(endpoint)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("Bridge URL must be a credential-free HTTPS origin")
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        raise ValueError("Bridge URL may not include a path, query or fragment")
    return endpoint


def report():
    messages = []
    endpoint = bridge_endpoint()
    host = urllib.parse.urlsplit(endpoint).hostname or ""
    messages.append("Published endpoint category: " +
                    ("Tailscale ts.net" if host.endswith(".ts.net") else "HTTPS"))
    try:
        info = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        messages.append("External DNS: resolved (" + str(len(info)) + " records)")
    except OSError as exc:
        messages.append("External DNS: FAILED (" + type(exc).__name__ + ")")
        info = []
    if info:
        request = urllib.request.Request(endpoint + "/dashboard/health",
                                         headers={"User-Agent": "MylesExternalHealth/1"})
        try:
            with urllib.request.urlopen(request, timeout=9) as response:
                code = response.status
        except urllib.error.HTTPError as exc:
            code = exc.code
        except Exception as exc:
            code = 0
            messages.append("External HTTPS: FAILED (" + type(exc).__name__ + ")")
        if code:
            messages.append("External HTTPS: reachable; HTTP " + str(code))
            if code in (401, 403):
                messages.append("Authentication boundary: challenge enforced")
            elif code == 200:
                messages.append("Authentication boundary: RECHECK PUBLIC HEALTH ENDPOINT")
    try:
        issue = fetch_json(API)
        body = str(issue.get("body") or "")
        marker = "~~~json\n"
        if marker not in body:
            raise ValueError("No public tower health payload")
        telemetry = json.loads(body.split(marker, 1)[1].split("\n~~~", 1)[0])
        ts = dt.datetime.fromisoformat(str(telemetry.get("reported_at")).replace("Z", "+00:00"))
        age = (dt.datetime.now(dt.timezone.utc) - ts.astimezone(dt.timezone.utc)).total_seconds()
        current = fetch_json("https://api.github.com/repos/JoshuaDuskin/MylesAI/branches/main")
        main_sha = current["commit"]["sha"]
        tower_sha = str(telemetry.get("installed_commit") or "")
        messages.append("Tower report: " + ("FRESH" if age < 1200 else "STALE") +
                        " (" + str(max(0, int(age // 60))) + " minutes old)")
        messages.append("Installed SHA matches main: " +
                        ("yes" if tower_sha == main_sha else "no"))
        messages.append("Note: old check-ins cannot establish the tower's present state")
    except Exception as exc:
        messages.append("Tower status comparison: unavailable (" + type(exc).__name__ + ")")
    return messages


def main():
    messages = report()
    output = "# External Myles connectivity (read-only)\n\n" + \
             "\n".join("- " + item for item in messages) + "\n"
    import os
    print(output)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write(output)
    # Do not fail release validation because a home tower is offline.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
