from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "MylesAI"
DATA = ROOT / "data"
LOCAL = "http://127.0.0.1:8790"
PORT = 8791
TOKEN_FILE = DATA / "dashboard_bridge_token.txt"
READ_FILE = DATA / "dashboard_public_read_token.txt"
LOG_FILE = ROOT / "logs" / "public_gateway_v074.log"
DIRECT_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

SENSITIVE = (
    "token",
    "secret",
    "password",
    "private_key",
    "privatekey",
    "mnemonic",
    "seed",
    "api_key",
    "apikey",
    "authorization",
    "credential",
    "pair_code",
    "paircode",
)
PRIVATE_COLLECTIONS = {"messages", "conversation", "history", "chat_history"}


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def owner_token() -> str:
    return read_file(TOKEN_FILE)


def read_token() -> str:
    return read_file(READ_FILE)


def log_error(message: str) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8", errors="replace") as handle:
            handle.write(message + "\n")
    except Exception:
        pass


def scrub(value, key: str = ""):
    if isinstance(value, dict):
        output = {}
        for name, child in value.items():
            lower = str(name).lower()
            if lower in PRIVATE_COLLECTIONS:
                continue
            if any(marker in lower for marker in SENSITIVE):
                continue
            output[name] = scrub(child, lower)
        return output
    if isinstance(value, list):
        return [scrub(child, key) for child in value]
    return value


def request_local(path: str, method: str = "GET", body: bytes | None = None, headers: dict | None = None, timeout: int = 15):
    request_headers = {"Accept": "application/json", "User-Agent": "MylesPublicGateway/0.7.5"}
    request_headers.update(headers or {})
    token = owner_token()
    if token:
        request_headers["X-Myles-Token"] = token
        request_headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(LOCAL + path, data=body, headers=request_headers, method=method)
    try:
        # Never send 127.0.0.1 through a machine-wide HTTP proxy. A proxy can
        # turn a healthy local bridge into a misleading 502 Bad Gateway.
        with DIRECT_OPENER.open(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()
    except Exception as error:
        log_error(f"private bridge request failed for {path}: {type(error).__name__}: {error}")
        payload = json.dumps({"ok": False, "error": "private bridge unavailable"}).encode("utf-8")
        return 502, {"Content-Type": "application/json"}, payload


def request_core(path: str, timeout: int = 8):
    request = urllib.request.Request(
        "http://127.0.0.1:8766" + path,
        headers={"Accept": "application/json", "User-Agent": "MylesPublicGateway/0.7.4"},
    )
    try:
        with DIRECT_OPENER.open(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except Exception as error:
        log_error(f"core fallback request failed for {path}: {type(error).__name__}: {error}")
        return 599, b"{}"


def parse_json(raw: bytes):
    try:
        value = json.loads(raw.decode("utf-8", errors="replace")) if raw else {}
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def local_trading_snapshot():
    path = DATA / "trading_status.json"
    try:
        if not path.is_file() or path.stat().st_size > 2_000_000:
            return None, {"status": "missing_status_file", "verified": False}
        value = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        if not isinstance(value, dict):
            return None, {"status": "invalid_status_file", "verified": False}
        if str(value.get("account_type") or "").upper() != "SIMULATED PAPER" or str(value.get("mode") or "").lower() != "paper":
            return None, {"status": "paper_identity_invalid", "verified": False}
        stamp = str(value.get("generated_at") or "").strip()
        if not stamp:
            return None, {"status": "missing_generated_at", "verified": False}
        generated = datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
        age = max(0.0, time.time() - generated)
        file_age = max(0.0, time.time() - path.stat().st_mtime)
        max_age = 300.0
        engine = value.get("engine") if isinstance(value.get("engine"), dict) else {}
        engine_ok = str(engine.get("status") or "").lower() in {"running", "degraded"}
        source_ok = "gmx" in str(engine.get("data_source") or "").lower()
        if age > max_age or file_age > max_age or not engine_ok or not source_ok:
            return None, {
                "status": "stale_or_unverified",
                "verified": False,
                "age_seconds": round(max(age, file_age), 1),
                "engine_status": engine.get("status"),
                "data_source": engine.get("data_source"),
            }
        published = dict(value)
        published["_verified"] = True
        published["_verified_source"] = "data/trading_status.json"
        published["_verified_age_seconds"] = round(max(age, file_age), 1)
        published["_verified_max_age_seconds"] = max_age
        published["_blockers"] = []
        published["_telemetry_state"] = "live"
        return published, {
            "status": "verified",
            "verified": True,
            "age_seconds": published["_verified_age_seconds"],
            "engine_status": engine.get("status"),
            "data_source": engine.get("data_source"),
            "markets_count": len(value.get("markets") or []) if isinstance(value.get("markets"), list) else 0,
        }
    except Exception as error:
        return None, {"status": "read_error", "verified": False, "detail": f"{type(error).__name__}: {error}"}


def fallback_status():
    code, raw = request_core("/api/public-status")
    value = parse_json(raw)
    if code != 200 or not value:
        code, raw = request_core("/health")
        value = parse_json(raw)
    if not value:
        return 502, {"ok": False, "error": "Myles status is unavailable"}
    payload = scrub(value)
    payload["schema_version"] = max(4, int(payload.get("schema_version") or 0))
    payload["generated_at"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    payload.setdefault("ok", code == 200)
    payload.setdefault("myles", {})
    if isinstance(payload["myles"], dict):
        payload["myles"].setdefault("online", code == 200)
    trading, diagnostics = local_trading_snapshot()
    payload["trading_diagnostics"] = diagnostics
    if trading:
        payload["trading"] = scrub(trading)
    else:
        payload.pop("trading", None)
    payload["bridge"] = {"online": False, "fallback": "core-read"}
    return 200 if code == 200 else 502, payload


def owner_read_ok(headers) -> bool:
    expected = owner_token()
    if not expected:
        return False
    supplied = headers.get("X-Myles-Token", "") or headers.get("x-myles-token", "")
    if not supplied:
        authorization = headers.get("Authorization", "") or headers.get("authorization", "")
        supplied = authorization.removeprefix("Bearer ").strip()
    return supplied == expected


def public_read_ok(headers) -> bool:
    expected = read_token()
    supplied = headers.get("X-Myles-Read", "") or headers.get("x-myles-read", "")
    return bool(expected and supplied == expected)


class Handler(BaseHTTPRequestHandler):
    server_version = "MylesGateway/0.7.5"

    def log_message(self, fmt, *args):
        return

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Myles-Token, X-Myles-Read")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Cache-Control", "no-store")

    def send_json(self, status: int, value, content_type: str = "application/json"):
        raw = value if isinstance(value, bytes) else json.dumps(value, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.cors()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def public_status(self):
        if not (public_read_ok(self.headers) or owner_read_ok(self.headers)):
            self.send_json(401, {"ok": False, "error": "read token required"})
            return
        status, response_headers, raw = request_local(self.path, "GET", None, None, 15)
        if self.path.startswith("/dashboard/health") and status >= 500:
            core_code, core_raw = request_core("/health")
            health = scrub(parse_json(core_raw))
            self.send_json(
                200,
                {
                    "ok": True,
                    "gateway": {"ok": True, "version": "0.7.5"},
                    "bridge": {"ok": False, "fallback": "core-health", "private_status": status},
                    "myles": {"ok": core_code == 200, "data": health},
                },
            )
            return
        if self.path.startswith("/dashboard/status") and status >= 500:
            fallback_code, fallback = fallback_status()
            self.send_json(fallback_code, fallback)
            return
        try:
            value = parse_json(raw)
            raw = json.dumps(scrub(value), separators=(",", ":")).encode("utf-8")
        except Exception:
            pass
        self.send_json(status, raw, response_headers.get("Content-Type", "application/json"))

    def proxy(self):
        # The public URL is read-only by default. Pairing is protected by the
        # bridge's one-time code; every other private route needs the owner token.
        if self.path.startswith("/dashboard/pair"):
            allowed = True
        else:
            allowed = owner_read_ok(self.headers)
        if not allowed:
            self.send_json(401, {"ok": False, "error": "owner token required"})
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(length) if length else None
        forwarded = {}
        for name in ("Authorization", "X-Myles-Token", "Content-Type", "Accept"):
            if self.headers.get(name):
                forwarded[name] = self.headers.get(name)
        status, response_headers, raw = request_local(self.path, self.command, body, forwarded, 190)
        self.send_json(status, raw, response_headers.get("Content-Type", "application/json"))

    def do_GET(self):
        if self.path.startswith("/dashboard/health") or self.path.startswith("/dashboard/status") or self.path.startswith("/api/public-status"):
            return self.public_status()
        return self.proxy()

    def do_POST(self):
        return self.proxy()

    def do_PUT(self):
        return self.proxy()

    def do_DELETE(self):
        return self.proxy()


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
