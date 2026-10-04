from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, quote, urlparse

ROOT = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "MylesAI"
CORE = "http://127.0.0.1:8766"
HOST = "127.0.0.1"
PORT = 8790
ALLOWED_ORIGINS = {
    "https://joshuaduskin.github.io",
    "http://127.0.0.1",
    "http://localhost",
}
MAX_BODY = 64 * 1024
RATE_WINDOW = 60.0
GET_LIMIT = 180
# The public gateway forwards authenticated requests from localhost.  A plain
# client-IP bucket therefore made phone + dashboard traffic share one limit.
# Keep a limit, but key authenticated traffic by a short hash of the owner
# token and allow normal owner interaction plus retries.
POST_LIMIT = 120
RATE: dict[str, deque[float]] = defaultdict(deque)
RATE_LOCK = threading.Lock()
TOKEN = ""
PAIR_CODE = ""
PAIR_EXPIRES = 0.0
PAIR_PINNED = False
PAIR_CODE_FILE: Path | None = None


def refresh_pair_state() -> None:
    """Reload the pinned/recovery pairing code without restarting the bridge."""
    global PAIR_CODE, PAIR_EXPIRES, PAIR_PINNED
    if PAIR_CODE_FILE is None:
        return
    try:
        pair_data = json.loads(PAIR_CODE_FILE.read_text(encoding="utf-8-sig"))
        code = str(pair_data.get("code") or "").strip().upper()
        expires = float(pair_data.get("expires_epoch") or 0)
        pinned = bool(pair_data.get("pinned", False))
        if code:
            # The owner explicitly uses one local tower pairing code indefinitely.
            # Keep this secret local; never publish it to GitHub or the dashboard feed.
            if not pinned:
                pair_data["pinned"] = True
                pair_data["expires_epoch"] = 0
                try:
                    tmp = PAIR_CODE_FILE.with_name(PAIR_CODE_FILE.name + ".tmp")
                    tmp.write_text(json.dumps(pair_data, indent=2) + "\\n", encoding="utf-8")
                    os.replace(tmp, PAIR_CODE_FILE)
                except Exception:
                    pass
            PAIR_CODE = code
            PAIR_EXPIRES = 0
            PAIR_PINNED = True
    except Exception:
        pass


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> Any:
    try:
        if not path.is_file() or path.stat().st_size > 2_000_000:
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def core_json(path: str, method: str = "GET", body: Any = None, timeout: float = 5.0) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json", "User-Agent": "MylesDashboardBridge/1.9"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(CORE + path, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                parsed = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                parsed = {"text": raw.decode("utf-8", errors="replace")}
            return resp.status, parsed
    except HTTPError as exc:
        raw = exc.read()
        try:
            parsed = json.loads(raw.decode("utf-8")) if raw else {"error": str(exc)}
        except Exception:
            parsed = {"error": raw.decode("utf-8", errors="replace") or str(exc)}
        return exc.code, parsed
    except (URLError, TimeoutError, OSError) as exc:
        return 599, {"error": str(exc)}


def find_runtime_status() -> dict[str, Any]:
    """Return only a recent local runtime snapshot.

    Repository-root status files were historical dashboard artifacts and must
    never bleed old versions/timestamps into the live tower response.
    """
    candidates = [
        ROOT / "data" / "public_status.json",
        ROOT / "data" / "dashboard_status.json",
        ROOT / "data" / "status.json",
        ROOT / "runtime" / "status.json",
    ]
    for path in candidates:
        data = load_json(path)
        if not isinstance(data, dict):
            continue
        stamp = data.get("generated_at") or data.get("updated_at") or data.get("timestamp") or data.get("time")
        if not stamp:
            continue
        try:
            if isinstance(stamp, (int, float)):
                epoch = float(stamp)
                if epoch < 100_000_000_000:
                    age = time.time() - epoch
                else:
                    age = time.time() - (epoch / 1000.0)
            else:
                epoch = datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).timestamp()
                age = time.time() - epoch
            if age < -300 or age > 300:
                continue
        except Exception:
            continue
        return data
    return {}


def find_game_mode_state() -> dict[str, Any]:
    state = load_json(ROOT / "data" / "game_mode_state.json")
    return state if isinstance(state, dict) else {}


def _trading_context() -> dict[str, Any]:
    path = ROOT / "data" / "trading_status.json"
    game_state = find_game_mode_state()
    cfg = load_json(ROOT / "quant" / "quant_config.json")
    try:
        poll_seconds = int((cfg or {}).get("poll_seconds") or 60)
    except Exception:
        poll_seconds = 60
    max_age = max(180, min(1800, poll_seconds * 3 + 60))
    ctx: dict[str, Any] = {
        "path": path,
        "game_state": game_state,
        "max_age_seconds": max_age,
        "file_present": path.is_file(),
        "age_seconds": None,
        "data": None,
    }
    if not path.is_file():
        return ctx
    try:
        ctx["age_seconds"] = round(max(0.0, time.time() - path.stat().st_mtime), 1)
    except Exception:
        ctx["age_seconds"] = None
    data = load_json(path)
    ctx["data"] = data if isinstance(data, dict) else None
    if isinstance(data, dict):
        generated_at = str(data.get("generated_at") or "").strip()
        if generated_at:
            try:
                parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                ctx["generated_age_seconds"] = round(max(0.0, time.time() - parsed.timestamp()), 1)
            except Exception:
                ctx["generated_age_seconds"] = None
        else:
            ctx["generated_age_seconds"] = None
    return ctx


def _trading_blockers(ctx: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if bool((ctx.get("game_state") or {}).get("active")):
        blockers.append("paused_game_mode")
    if not ctx.get("file_present"):
        blockers.append("missing_status_file")
        return blockers
    data = ctx.get("data")
    if not isinstance(data, dict):
        blockers.append("invalid_status_file")
        return blockers
    if ctx.get("age_seconds") is None or float(ctx.get("age_seconds") or 0) > float(ctx.get("max_age_seconds") or 180):
        blockers.append("stale_status_file")
    if ctx.get("generated_age_seconds") is None or float(ctx.get("generated_age_seconds") or 0) > float(ctx.get("max_age_seconds") or 180):
        blockers.append("stale_generated_at")
    engine = data.get("engine") if isinstance(data.get("engine"), dict) else {}
    if str(engine.get("status") or "").strip().lower() not in {"running", "degraded"}:
        blockers.append("quant_engine_not_running")
    if "gmx" not in str(engine.get("data_source") or "").lower():
        blockers.append("gmx_source_not_verified")
    if str(data.get("account_type") or "").strip().upper() != "SIMULATED PAPER":
        blockers.append("paper_account_not_verified")
    if str(data.get("mode") or "").strip().lower() != "paper":
        blockers.append("paper_mode_not_verified")
    return blockers


def trading_diagnostics() -> dict[str, Any]:
    ctx = _trading_context()
    data = ctx.get("data") if isinstance(ctx.get("data"), dict) else {}
    blockers = _trading_blockers(ctx)
    markets = data.get("markets") if isinstance(data.get("markets"), list) else []
    engine = data.get("engine") if isinstance(data.get("engine"), dict) else {}
    if blockers:
        status = blockers[0]
    elif not markets:
        status = "verified_degraded_no_markets"
    else:
        status = "verified"
    return {
        "status": status,
        "verified": not blockers,
        "detail": " · ".join(blockers) if blockers else (
            "Quant is publishing paper telemetry; awaiting GMX market marks." if not markets
            else f"Verified GMX paper telemetry for {len(markets)} markets."
        ),
        "file_present": bool(ctx.get("file_present")),
        "age_seconds": ctx.get("age_seconds"),
        "generated_age_seconds": ctx.get("generated_age_seconds"),
        "max_age_seconds": ctx.get("max_age_seconds"),
        "engine_status": engine.get("status"),
        "data_source": engine.get("data_source"),
        "markets_count": len(markets),
        "market_errors": data.get("market_errors") if isinstance(data.get("market_errors"), dict) else {},
        "game_mode_active": bool((ctx.get("game_state") or {}).get("active")),
    }


def find_trading_data() -> dict[str, Any]:
    """Return canonical paper telemetry, explicitly marked fresh, paused, or stale."""
    ctx = _trading_context()
    data = ctx.get("data")
    if not isinstance(data, dict):
        return {}
    if str(data.get("account_type") or "").strip().upper() != "SIMULATED PAPER":
        return {}
    if str(data.get("mode") or "").strip().lower() != "paper":
        return {}
    blockers = _trading_blockers(ctx)
    published = dict(data)
    published["_verified"] = not blockers
    published["_verified_source"] = "data/trading_status.json"
    published["_verified_age_seconds"] = round(
        max(float(ctx.get("age_seconds") or 0), float(ctx.get("generated_age_seconds") or 0)), 1
    )
    published["_verified_max_age_seconds"] = ctx.get("max_age_seconds")
    published["_blockers"] = blockers
    published["_telemetry_state"] = (
        "paused_game_mode" if "paused_game_mode" in blockers
        else "stale" if blockers
        else "live"
    )
    published["_degraded"] = bool(blockers) or not bool(published.get("markets"))
    return published


QUANT_DIR = ROOT / "quant"
QUANT_CONFIG = QUANT_DIR / "quant_config.json"
QUANT_STATE = ROOT / "data" / "quant_paper_state_v3.json"
QUANT_SCRIPT = QUANT_DIR / "quant_service.mjs"
LIVE_SCRIPT = QUANT_DIR / "gmx_live.mjs"
LIVE_STATUS = ROOT / "data" / "gmx_live_status.json"
COPY_SCRIPT = QUANT_DIR / "copy_trader_service.mjs"
COPY_STATUS = ROOT / "data" / "copy_trader_status.json"
COPY_CONFIG = ROOT / "data" / "copy_trader_config.json"
QUANT_MARKETS = ["BTC/USD", "ETH/USD", "SOL/USD", "XRP/USD", "TAO/USD"]
QUANT_PERIODS = ["1m", "5m", "15m", "1h", "4h", "1d"]


def fetch_quant_candles(symbol: str, period: str, limit: int = 240) -> dict[str, Any]:
    symbol = str(symbol or "").upper()
    period = str(period or "")
    if symbol not in QUANT_MARKETS:
        raise RuntimeError("Unsupported market")
    if period not in QUANT_PERIODS:
        raise RuntimeError("Unsupported candle period")
    limit = max(50, min(500, int(limit or 240)))
    token = symbol.split("/", 1)[0]
    bases = (
        "https://arbitrum-api.gmxinfra.io",
        "https://arbitrum-api-fallback.gmxinfra.io",
        "https://arbitrum-api-fallback.gmxinfra2.io",
    )
    errors: list[str] = []
    for base in bases:
        url = (
            f"{base}/prices/candles"
            f"?tokenSymbol={quote(token)}&period={quote(period)}&limit={limit}"
        )
        req = Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "MylesDashboardBridge/1.9"},
            method="GET",
        )
        try:
            with urlopen(req, timeout=10) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            rows = raw if isinstance(raw, list) else raw.get("candles", []) if isinstance(raw, dict) else []
            candles = []
            for row in rows:
                try:
                    if isinstance(row, list) and len(row) >= 5:
                        ts, op, hi, lo, cl = row[:5]
                    elif isinstance(row, dict):
                        ts, op, hi, lo, cl = row.get("timestamp"), row.get("open"), row.get("high"), row.get("low"), row.get("close")
                    else:
                        continue
                    item = {
                        "timestamp": int(float(ts)),
                        "open": float(op),
                        "high": float(hi),
                        "low": float(lo),
                        "close": float(cl),
                    }
                    if item["timestamp"] > 0 and min(item["open"], item["high"], item["low"], item["close"]) > 0:
                        candles.append(item)
                except Exception:
                    continue
            candles.sort(key=lambda x: x["timestamp"])
            if len(candles) < 2:
                raise RuntimeError("insufficient candle data")
            return {
                "ok": True,
                "symbol": symbol,
                "period": period,
                "source": "GMX Oracle /prices/candles",
                "source_host": base,
                "generated_at": now_iso(),
                "candles": candles,
            }
        except Exception as exc:
            errors.append(f"{base}: {exc}")
    raise RuntimeError("GMX candle request failed across all oracle hosts: " + " | ".join(errors))


def clamp_num(value: Any, low: float, high: float, fallback: float) -> float:
    try:
        n = float(value)
    except Exception:
        n = fallback
    return max(low, min(high, n))


def load_quant_config() -> dict[str, Any]:
    data = load_json(QUANT_CONFIG)
    return data if isinstance(data, dict) else {}


def save_quant_config(payload: Any) -> dict[str, Any]:
    current = load_quant_config()
    incoming = payload.get("config") if isinstance(payload, dict) and isinstance(payload.get("config"), dict) else payload
    if not isinstance(incoming, dict):
        raise ValueError("config object required")

    cfg = dict(current)
    cfg["schema_version"] = 3
    cfg["venue"] = "GMX"
    cfg["chain_id"] = 42161
    timeframe = str(incoming.get("timeframe", cfg.get("timeframe", "1h")))
    cfg["timeframe"] = timeframe if timeframe in QUANT_PERIODS else "1h"
    cfg["history_limit"] = int(clamp_num(incoming.get("history_limit", cfg.get("history_limit", 3000)), 300, 10000, 3000))
    cfg["poll_seconds"] = int(clamp_num(incoming.get("poll_seconds", cfg.get("poll_seconds", 60)), 30, 900, 60))
    cfg["starting_equity"] = clamp_num(incoming.get("starting_equity", cfg.get("starting_equity", 10000)), 100, 10_000_000, 10000)

    existing_markets = cfg.get("market_settings") if isinstance(cfg.get("market_settings"), dict) else {}
    incoming_markets = incoming.get("market_settings") if isinstance(incoming.get("market_settings"), dict) else {}
    market_settings: dict[str, Any] = {}
    for symbol in QUANT_MARKETS:
        old = existing_markets.get(symbol) if isinstance(existing_markets.get(symbol), dict) else {}
        new = incoming_markets.get(symbol) if isinstance(incoming_markets.get(symbol), dict) else {}
        strategy = str(new.get("paper_strategy", old.get("paper_strategy", "trend_momentum")))
        if strategy not in {"scalp_trend", "trend_momentum", "mean_reversion"}:
            strategy = "trend_momentum"
        market_settings[symbol] = {
            "enabled": bool(new.get("enabled", old.get("enabled", True))),
            "paper_strategy": strategy,
            "auto_trade_enabled": bool(new.get("auto_trade_enabled", old.get("auto_trade_enabled", True))),
        }
    if not any(v["enabled"] for v in market_settings.values()):
        raise ValueError("At least one research market must remain enabled")
    cfg["market_settings"] = market_settings

    risk_old = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}
    risk_new = incoming.get("risk") if isinstance(incoming.get("risk"), dict) else {}
    cfg["risk"] = {
        "max_risk_per_trade_pct": clamp_num(risk_new.get("max_risk_per_trade_pct", risk_old.get("max_risk_per_trade_pct", .5)), .05, 5, .5),
        "max_notional_leverage": clamp_num(risk_new.get("max_notional_leverage", risk_old.get("max_notional_leverage", 1.5)), .1, 5, 1.5),
        "stop_loss_pct": clamp_num(risk_new.get("stop_loss_pct", risk_old.get("stop_loss_pct", 1.5)), .25, 15, 1.5),
        "take_profit_pct": clamp_num(risk_new.get("take_profit_pct", risk_old.get("take_profit_pct", 3)), .25, 40, 3),
        "max_daily_loss_pct": clamp_num(risk_new.get("max_daily_loss_pct", risk_old.get("max_daily_loss_pct", 2)), .25, 20, 2),
        "max_drawdown_pct": clamp_num(risk_new.get("max_drawdown_pct", risk_old.get("max_drawdown_pct", 8)), .5, 40, 8),
        "max_concurrent_positions": int(clamp_num(risk_new.get("max_concurrent_positions", risk_old.get("max_concurrent_positions", 2)), 1, 5, 2)),
        "max_market_allocation_pct": clamp_num(risk_new.get("max_market_allocation_pct", risk_old.get("max_market_allocation_pct", 35)), 5, 100, 35),
    }

    costs_old = cfg.get("research_costs") if isinstance(cfg.get("research_costs"), dict) else {}
    costs_new = incoming.get("research_costs") if isinstance(incoming.get("research_costs"), dict) else {}
    cfg["research_costs"] = {
        "position_fee_bps_per_side": clamp_num(costs_new.get("position_fee_bps_per_side", costs_old.get("position_fee_bps_per_side", 6)), 0, 100, 6),
        "slippage_bps_per_side": clamp_num(costs_new.get("slippage_bps_per_side", costs_old.get("slippage_bps_per_side", 5)), 0, 300, 5),
        "impact_bps_per_side": clamp_num(costs_new.get("impact_bps_per_side", costs_old.get("impact_bps_per_side", 20)), 0, 1000, 20),
        "holding_cost_bps_per_day": clamp_num(costs_new.get("holding_cost_bps_per_day", costs_old.get("holding_cost_bps_per_day", 5)), 0, 300, 5),
    }

    val_old = cfg.get("validation") if isinstance(cfg.get("validation"), dict) else {}
    val_new = incoming.get("validation") if isinstance(incoming.get("validation"), dict) else {}
    cfg["validation"] = {
        "min_trades": int(clamp_num(val_new.get("min_trades", val_old.get("min_trades", 12)), 1, 500, 12)),
        "max_drawdown_pct": clamp_num(val_new.get("max_drawdown_pct", val_old.get("max_drawdown_pct", 12)), 1, 60, 12),
        "min_walk_forward_positive_pct": clamp_num(val_new.get("min_walk_forward_positive_pct", val_old.get("min_walk_forward_positive_pct", 50)), 0, 100, 50),
        "min_base_return_pct": clamp_num(val_new.get("min_base_return_pct", val_old.get("min_base_return_pct", 0)), -100, 500, 0),
        "min_stress_return_pct": clamp_num(val_new.get("min_stress_return_pct", val_old.get("min_stress_return_pct", -3)), -100, 500, -3),
        "stress_cost_multiplier": clamp_num(val_new.get("stress_cost_multiplier", val_old.get("stress_cost_multiplier", 2.5)), 1, 10, 2.5),
    }

    # MYLES_INDEPENDENT_RESEARCH_BOT_CONFIG_V01060
    # Preserve owner-selected paper and research controls independently. The old
    # bridge rebuilt only three paper keys and silently discarded research config.
    paper_old = cfg.get("paper") if isinstance(cfg.get("paper"), dict) else {}
    paper_new = incoming.get("paper") if isinstance(incoming.get("paper"), dict) else {}
    paper = dict(paper_old)
    paper.update(paper_new)
    paper["enabled"] = bool(paper_new.get("enabled", paper_old.get("enabled", True)))
    paper["auto_trading_enabled"] = bool(paper_new.get("auto_trading_enabled", paper_old.get("auto_trading_enabled", True)))
    paper["adaptive_strategy_selection"] = bool(paper_new.get("adaptive_strategy_selection", paper_old.get("adaptive_strategy_selection", True)))
    paper["emergency_stop"] = bool(paper_new.get("emergency_stop", paper_old.get("emergency_stop", False)))
    paper["entry_cooldown_bars"] = int(clamp_num(paper_new.get("entry_cooldown_bars", paper_old.get("entry_cooldown_bars", 0)), 0, 50, 0))
    cfg["paper"] = paper

    research_old = cfg.get("research_exploration") if isinstance(cfg.get("research_exploration"), dict) else {}
    research_new = incoming.get("research_exploration") if isinstance(incoming.get("research_exploration"), dict) else {}
    research = dict(research_old)
    research.update(research_new)
    research["enabled"] = bool(research_new.get("enabled", research_old.get("enabled", True)))
    research["continuous_market_research_enabled"] = bool(research_new.get("continuous_market_research_enabled", research_old.get("continuous_market_research_enabled", True)))
    research["paper_lab_enabled"] = bool(research_new.get("paper_lab_enabled", research_old.get("paper_lab_enabled", True)))
    research["tournament_enabled"] = bool(research_new.get("tournament_enabled", research_old.get("tournament_enabled", True)))
    research["entry_cooldown_bars"] = int(clamp_num(research_new.get("entry_cooldown_bars", research_old.get("entry_cooldown_bars", paper["entry_cooldown_bars"])), 0, 50, paper["entry_cooldown_bars"]))
    research["interval_seconds"] = int(clamp_num(research_new.get("interval_seconds", research_old.get("interval_seconds", 900)), 120, 3600, 900))
    cfg["research_exploration"] = research

    cfg["strategies"] = {
        "scalp_trend": {"enabled": bool((incoming.get("strategies") or {}).get("scalp_trend", {}).get("enabled", True))},
        "trend_momentum": {"enabled": bool((incoming.get("strategies") or {}).get("trend_momentum", {}).get("enabled", True))},
        "mean_reversion": {"enabled": bool((incoming.get("strategies") or {}).get("mean_reversion", {}).get("enabled", True))},
    }
    cfg["live_execution"] = {
        "enabled": False,
        "signing_enabled": False,
        "reason": "Live execution remains hard-locked until owner review, forward-paper validation, and a dedicated execution wallet are complete.",
    }
    QUANT_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUANT_CONFIG.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    tmp.replace(QUANT_CONFIG)
    return cfg


def start_quant_once(backtest_only: bool = False) -> int | None:
    if bool(find_game_mode_state().get("active")):
        return None
    if not QUANT_SCRIPT.is_file():
        return None
    node = shutil.which("node") or shutil.which("node.exe")
    if not node:
        return None
    args = [node, str(QUANT_SCRIPT), "--backtest-only" if backtest_only else "--once"]
    proc = subprocess.Popen(
        args, cwd=str(QUANT_DIR),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return proc.pid


def run_quant_manual(payload: dict[str, Any]) -> dict[str, Any]:
    if not QUANT_SCRIPT.is_file():
        raise RuntimeError("Quant service is not installed")
    node = shutil.which("node") or shutil.which("node.exe")
    if not node:
        raise RuntimeError("Node.js is not available")
    raw = json.dumps(payload, separators=(",", ":"))
    proc = subprocess.run(
        [node, str(QUANT_SCRIPT), "--manual-order", raw],
        cwd=str(QUANT_DIR), capture_output=True, text=True, timeout=150,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    lines = [x.strip() for x in (proc.stdout or "").splitlines() if x.strip()]
    if proc.returncode != 0:
        detail = (proc.stderr or "").strip()
        try:
            err = json.loads(detail.splitlines()[-1]) if detail else {}
            if isinstance(err, dict) and err.get("error"):
                detail = str(err["error"])
        except Exception:
            pass
        raise RuntimeError(detail or f"Quant manual action failed with exit code {proc.returncode}")
    if not lines:
        raise RuntimeError("Quant manual action returned no response")
    try:
        result = json.loads(lines[-1])
    except Exception as exc:
        raise RuntimeError(f"Quant manual action returned invalid JSON: {exc}")
    if not isinstance(result, dict) or not result.get("ok"):
        raise RuntimeError(str(result.get("error") if isinstance(result, dict) else result))
    return result


def run_live_cli(flag: str, payload: dict[str, Any] | None = None, timeout: int = 180) -> dict[str, Any]:
    if not LIVE_SCRIPT.is_file():
        raise RuntimeError("GMX live adapter is not installed")
    node = shutil.which("node") or shutil.which("node.exe")
    if not node:
        raise RuntimeError("Node.js is not available")
    args = [node, str(LIVE_SCRIPT), flag]
    if payload is not None:
        args.append(json.dumps(payload, separators=(",", ":")))
    proc = subprocess.run(
        args, cwd=str(QUANT_DIR), capture_output=True, text=True, timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    out_lines = [x.strip() for x in (proc.stdout or "").splitlines() if x.strip()]
    err_lines = [x.strip() for x in (proc.stderr or "").splitlines() if x.strip()]
    raw = out_lines[-1] if out_lines else (err_lines[-1] if err_lines else "")
    try:
        result = json.loads(raw) if raw else {}
    except Exception:
        result = {"ok": False, "error": raw or f"Live adapter exit {proc.returncode}"}
    if proc.returncode != 0 or not isinstance(result, dict) or result.get("ok") is False:
        raise RuntimeError(str(result.get("error") if isinstance(result, dict) else raw) or f"Live adapter exit {proc.returncode}")
    return result


def run_copy_cli(flag: str, payload: dict[str, Any] | None = None, timeout: int = 240) -> dict[str, Any]:
    if not COPY_SCRIPT.is_file():
        raise RuntimeError("Copy-trader service is not installed")
    node = shutil.which("node") or shutil.which("node.exe")
    if not node:
        raise RuntimeError("Node.js is not available")
    args = [node, str(COPY_SCRIPT), flag]
    if payload is not None:
        args.append(json.dumps(payload, separators=(",", ":")))
    proc = subprocess.run(
        args, cwd=str(QUANT_DIR), capture_output=True, text=True, timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    lines = [x.strip() for x in ((proc.stdout or "") + "\n" + (proc.stderr or "")).splitlines() if x.strip()]
    raw = lines[-1] if lines else ""
    try:
        result = json.loads(raw) if raw else {}
    except Exception:
        result = {"ok": False, "error": raw or f"Copy service exit {proc.returncode}"}
    if proc.returncode != 0 or not isinstance(result, dict) or result.get("ok") is False:
        raise RuntimeError(str(result.get("error") if isinstance(result, dict) else raw) or f"Copy service exit {proc.returncode}")
    return result


def copy_status() -> dict[str, Any]:
    cached = load_json(COPY_STATUS)
    out = cached if isinstance(cached, dict) else {"ok": True, "version": "0.9.0", "generated_at": None, "candidates": [], "qualified": [], "signals": [], "selected_accounts": []}
    cfg = load_json(COPY_CONFIG)
    live = load_json(LIVE_STATUS)
    cfg = cfg if isinstance(cfg, dict) else out.get("config") if isinstance(out.get("config"), dict) else {}
    live = live if isinstance(live, dict) else {}
    auth = live.get("copy_trading") if isinstance(live.get("copy_trading"), dict) else {}
    active = bool(cfg.get("live_copy_enabled") and live.get("armed") and auth.get("enabled") and float(auth.get("authorized_until") or 0) > time.time())
    return {**out, "config": cfg, "live_copy_enabled": active, "mode": "owner_authorized_live_copy" if active else "paper_shadow_copy"}


def live_status() -> dict[str, Any]:
    cached = load_json(LIVE_STATUS)
    try:
        if isinstance(cached, dict) and LIVE_STATUS.is_file() and (time.time() - LIVE_STATUS.stat().st_mtime) < 25:
            return cached
    except Exception:
        pass
    try:
        return run_live_cli("--status", timeout=45)
    except Exception as exc:
        if isinstance(cached, dict):
            return {**cached, "ok": False, "stale": True, "error": str(exc)}
        return {"ok": False, "version": "0.6.2", "setup_complete": False, "armed": False, "error": str(exc)}


def system_metrics() -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        usage = shutil.disk_usage(ROOT.anchor or str(ROOT))
        out["disk_free_gb"] = round(usage.free / (1024 ** 3), 1)
        out["disk_total_gb"] = round(usage.total / (1024 ** 3), 1)
    except Exception:
        pass
    try:
        import psutil  # type: ignore
        out["cpu_percent"] = psutil.cpu_percent(interval=0.15)
        vm = psutil.virtual_memory()
        out["memory_percent"] = vm.percent
        out["memory_used_gb"] = round(vm.used / (1024 ** 3), 1)
        out["memory_total_gb"] = round(vm.total / (1024 ** 3), 1)
        out["uptime_seconds"] = int(time.time() - psutil.boot_time())
    except Exception:
        pass
    status, tags = http_json("http://127.0.0.1:11434/api/tags", timeout=0.4)
    if status == 200 and isinstance(tags, dict):
        models = tags.get("models") or []
        if isinstance(models, list):
            out["ollama_models"] = [m.get("name") if isinstance(m, dict) else str(m) for m in models][:20]
            if out["ollama_models"]:
                out["model"] = out["ollama_models"][0]
    return out


def http_json(url: str, timeout: float = 5.0) -> tuple[int, Any]:
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "MylesDashboardBridge/1.9"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw.decode("utf-8")) if raw else {}
    except Exception as exc:
        return 599, {"error": str(exc)}


def _task_label(value: Any, limit: int = 110) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    low = text.lower()
    if "continuous improvement cycle" in low or "owner-locked dashboard" in low:
        return "Run verified continuous improvement"
    if "quant" in low and any(word in low for word in ("gmx", "trading", "game mode")):
        return "Repair dashboard, game mode, and Quant feeds"
    first = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0].strip()
    label = first or "Owner task"
    return label if len(label) <= limit else label[: limit - 1].rstrip(" ,.;:-") + "…"


def _public_job(job: dict[str, Any]) -> dict[str, Any]:
    source = str(job.get("source") or "owner")
    label = _task_label(job.get("label") or job.get("title") or job.get("prompt"))
    state = str(job.get("truth_state") or job.get("state") or "")
    if source == "continuous":
        summary = "Working through the next verified improvement cycle."
    elif state.lower() in {"completed", "done", "success"}:
        summary = f"Completed {label}."
    elif state.lower() in {"failed", "error", "blocked"}:
        summary = f"Work stopped while handling {label}."
    elif state.lower() in {"pending", "queued", "waiting"}:
        summary = f"Queued: {label}."
    else:
        summary = f"Working on {label}."
    return {
        key: value for key, value in {
            "id": job.get("id"),
            "label": label,
            "summary": summary,
            "source": source,
            "state": state,
            "phase": job.get("phase"),
            "phase_display": job.get("phase_display"),
            "created_at": job.get("created_at"),
            "started_at": job.get("started_at"),
            "updated_at": job.get("updated_at"),
            "completed_at": job.get("completed_at"),
            "heartbeat_at": job.get("heartbeat_at"),
            "last_verified_progress_at": job.get("material_progress_at") or job.get("last_verified_progress_at"),
            "worker_alive": job.get("live_worker") if "live_worker" in job else job.get("worker_alive"),
            "error": _task_label(job.get("error"), 180) if job.get("error") else None,
        }.items() if value is not None
    }


def normalize_jobs(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(payload, list):
        rows = [x for x in payload if isinstance(x, dict)]
    elif isinstance(payload, dict):
        for key in ("jobs", "items", "tasks"):
            value = payload.get(key)
            if isinstance(value, list):
                rows = [x for x in value if isinstance(x, dict)]
                break
    return [_public_job(row) for row in rows]


def build_status() -> dict[str, Any]:
    base = find_runtime_status()
    if not isinstance(base, dict):
        base = {}
    result = dict(base)
    result["schema_version"] = 4
    result["generated_at"] = now_iso()

    health_code, health = core_json("/health", timeout=1.5)
    if not isinstance(health, dict):
        health = {}
    existing_myles = result.get("myles") if isinstance(result.get("myles"), dict) else {}
    myles = dict(existing_myles)
    myles["online"] = health_code == 200 and health.get("ok", True) is not False
    if health.get("version"):
        myles["version"] = health["version"]
    if health.get("status"):
        myles["status"] = health["status"]
    result["myles"] = myles
    if health.get("status") and not result.get("status"):
        result["status"] = health["status"]

    jobs_code, jobs_payload = core_json("/api/jobs", timeout=1.5)
    jobs = normalize_jobs(jobs_payload) if jobs_code == 200 else []
    if jobs:
        running = next((j for j in jobs if str(j.get("state", "")).lower() in {"running", "active", "working"}), None)
        pending = [j for j in jobs if str(j.get("state", "")).lower() in {"pending", "queued", "waiting"}]
        completed = [j for j in jobs if str(j.get("state", "")).lower() in {"completed", "done", "success"}]
        failed = [j for j in jobs if str(j.get("state", "")).lower() in {"failed", "error", "blocked"}]
        if running:
            result["current_task"] = result.get("current_task") or running
        result["queue"] = pending[:30]
        result["recent_completed"] = sorted(completed, key=lambda j: str(j.get("updated_at") or j.get("completed_at") or j.get("created_at") or ""), reverse=True)[:30]
        result["recent_failures"] = sorted(failed, key=lambda j: str(j.get("updated_at") or j.get("created_at") or ""), reverse=True)[:20]

    # Pull live public/runtime state directly from core when available so the
    # dashboard does not depend on GitHub snapshots for owner controls.
    public_code, public_payload = core_json("/api/public-status", timeout=1.5)
    if public_code == 200 and isinstance(public_payload, dict):
        for key in ("continuous_program", "current_task", "queue", "game_mode", "game_mode_detail", "activity", "model", "runtime"):
            if key in public_payload:
                result[key] = public_payload[key]

    capabilities_code, capabilities_payload = core_json("/api/capabilities", timeout=1.0)
    capability_payload_is_useful = False
    if isinstance(capabilities_payload, list):
        capability_payload_is_useful = bool(capabilities_payload)
    elif isinstance(capabilities_payload, dict):
        capability_payload_is_useful = any(
            bool(capabilities_payload.get(key))
            for key in ("capabilities", "tools", "items", "providers", "checks")
        )
    if capabilities_code == 200 and capability_payload_is_useful:
        result["capabilities"] = capabilities_payload
    else:
        # Older cores do not expose /api/capabilities.  The dashboard must
        # still show the real reachable surfaces instead of an empty card.
        # These are derived from the checks above and local installed files;
        # no capability is reported as working merely because it is named.
        node_ready = bool(shutil.which("node") or shutil.which("node.exe"))
        quant_ready = QUANT_SCRIPT.is_file() and node_ready
        result["capabilities"] = [
            {
                "name": "Myles core API",
                "status": "working" if health_code == 200 else "offline",
                "detail": "Health and owner runtime endpoints",
            },
            {
                "name": "Tasks and tool routing",
                "status": "working" if jobs_code == 200 else "offline",
                "detail": "Queue, current work, and completion history",
            },
            {
                "name": "Quant paper bot",
                "status": "ready" if quant_ready else "unavailable",
                "detail": "Paper configuration and simulated execution",
            },
            {
                "name": "Automatic backtests",
                "status": "ready" if quant_ready else "unavailable",
                "detail": "Fresh strategy validation from the Trading Bot page",
            },
            {
                "name": "GMX market data",
                "status": "ready" if quant_ready else "unavailable",
                "detail": "Read-only market candles; live money remains locked",
            },
            {
                "name": "Phone chat bridge",
                "status": "working" if TOKEN else "pair required",
                "detail": "One-time pairing stores the phone authorization locally",
            },
        ]

    result["system"] = {**(result.get("system") if isinstance(result.get("system"), dict) else {}), **system_metrics()}

    game_state = find_game_mode_state()
    if not game_state:
        game_state = {
            "schema_version": 2,
            "active": False,
            "automatic": True,
            "detected": False,
            "status": "watcher_offline",
            "reason": "game_mode_state.json is not being updated by the watcher",
        }
    else:
        last_checked = str(game_state.get("last_checked_at") or "")
        if last_checked:
            try:
                checked_at = datetime.fromisoformat(last_checked.replace("Z", "+00:00")).timestamp()
                if time.time() - checked_at > 15:
                    game_state = dict(game_state)
                    game_state["status"] = "stale"
                    game_state["reason"] = "game-mode watcher heartbeat is stale"
            except Exception:
                pass
    result["game_mode_state"] = game_state
    result["game_mode"] = bool(game_state.get("active"))
    result["light_mode"] = bool(game_state.get("active")) or bool(result.get("light_mode"))
    existing_detail = result.get("game_mode_detail") if isinstance(result.get("game_mode_detail"), dict) else {}
    result["game_mode_detail"] = {
        **existing_detail,
        **game_state,
        "active": bool(game_state.get("active")),
        "automatic": bool(game_state.get("automatic", True)),
        "detected": bool(game_state.get("detected")),
    }

    result["trading_diagnostics"] = trading_diagnostics()
    trading = find_trading_data()
    if trading:
        result["trading"] = trading
    else:
        result.pop("trading", None)

    result.setdefault("bridge", {})
    if isinstance(result["bridge"], dict):
        result["bridge"]["online"] = True
        result["bridge"]["local_port"] = PORT
    return result


def authorized(handler: BaseHTTPRequestHandler) -> bool:
    if not TOKEN:
        return False
    auth = handler.headers.get("Authorization", "")
    alt = handler.headers.get("X-Myles-Token", "")
    supplied = auth[7:].strip() if auth.lower().startswith("bearer ") else alt.strip()
    return bool(supplied) and constant_time_equal(supplied, TOKEN)


def constant_time_equal(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a.encode(), b.encode()):
        result |= x ^ y
    return result == 0


def rate_ok(client: str, is_post: bool) -> bool:
    limit = POST_LIMIT if is_post else GET_LIMIT
    now = time.monotonic()
    with RATE_LOCK:
        q = RATE[client]
        while q and q[0] < now - RATE_WINDOW:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True


def send_to_myles(text: str) -> tuple[int, Any, str]:
    candidates = [
        # Native Myles owner-message ingress. This is the same core path used
        # by local console/dashboard input and ultimately handle_owner_message().
        ("/api/send", {"text": text, "source": "dashboard"}),
        # Compatibility fallbacks for older experimental builds.
        ("/api/messages", {"message": text, "text": text, "source": "dashboard"}),
        ("/api/chat", {"message": text, "text": text, "source": "dashboard"}),
        ("/chat", {"message": text, "text": text, "source": "dashboard"}),
    ]
    diagnostics = []
    for path, body in candidates:
        code, payload = core_json(path, method="POST", body=body, timeout=90.0)
        diagnostics.append(f"{path}:{code}")
        if 200 <= code < 300:
            return code, payload, path
        if code not in {400, 404, 405, 415, 422, 599}:
            return code, payload, path
    return 502, {"error": "Myles did not expose a compatible dashboard chat POST route", "attempts": diagnostics}, ""


class Handler(BaseHTTPRequestHandler):
    server_version = "MylesDashboardBridge/1.9"

    def log_message(self, fmt: str, *args: Any) -> None:
        line = f"[{now_iso()}] {self.client_address[0]} {fmt % args}\n"
        try:
            log = ROOT / "logs" / "dashboard_bridge.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def cors(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED_ORIGINS or origin.startswith("http://127.0.0.1:") or origin.startswith("http://localhost:"):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Authorization, X-Myles-Token, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")

    def json_response(self, code: int, payload: Any) -> None:
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(code)
        self.cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def deny(self, code: int = 401, message: str = "Unauthorized") -> None:
        self.json_response(code, {"ok": False, "error": message})

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.cors()
        self.end_headers()

    def preflight(self, is_post: bool = False) -> bool:
        origin = self.headers.get("Origin", "")
        if origin and origin not in ALLOWED_ORIGINS and not origin.startswith("http://127.0.0.1:") and not origin.startswith("http://localhost:"):
            self.deny(403, "Origin not allowed")
            return False
        auth = self.headers.get("Authorization", "")
        alt = self.headers.get("X-Myles-Token", "")
        supplied = auth[7:].strip() if auth.lower().startswith("bearer ") else alt.strip()
        identity = self.client_address[0]
        if supplied:
            identity = "owner:" + hashlib.sha256(supplied.encode("utf-8")).hexdigest()[:24]
        if not rate_ok(identity, is_post):
            self.deny(429, "Rate limit exceeded")
            return False
        if not authorized(self):
            self.deny(401, "Pairing token required")
            return False
        return True

    def do_GET(self) -> None:  # noqa: N802
        if not self.preflight(False):
            return
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/dashboard/health":
            # Bridge health is intentionally independent from Myles core health.
            # A temporary Myles restart must not make Cloudflare/tunnel verification
            # falsely report that the bridge itself is down.
            code, health = core_json("/health", timeout=4.0)
            self.json_response(
                200,
                {
                    "ok": True,
                    "bridge": {"ok": True, "version": "1.8", "time": now_iso()},
                    "myles": {
                        "ok": code == 200 and (not isinstance(health, dict) or health.get("ok", True) is not False),
                        "http_status": code,
                        "data": health if isinstance(health, dict) else {},
                    },
                },
            )
            return
        if path == "/dashboard/status":
            self.json_response(200, build_status())
            return
        if path == "/dashboard/messages":
            code, data = core_json("/api/messages", timeout=6.0)
            if code == 200:
                self.json_response(200, data)
            else:
                self.json_response(502, {"error": "Could not read Myles message history", "core_status": code, "detail": data})
            return
        if path == "/dashboard/quant/config":
            self.json_response(200, {"ok": True, "config": load_quant_config(), "markets": QUANT_MARKETS, "periods": QUANT_PERIODS})
            return
        if path == "/dashboard/quant/live/status":
            self.json_response(200, live_status())
            return
        if path == "/dashboard/quant/copy/status":
            self.json_response(200, copy_status())
            return
        if path == "/dashboard/quant/candles":
            try:
                symbol = (query.get("symbol") or ["BTC/USD"])[0]
                period = (query.get("period") or ["1m"])[0]
                try:
                    limit = int((query.get("limit") or ["240"])[0])
                except Exception:
                    limit = 240
                self.json_response(200, fetch_quant_candles(symbol, period, limit))
            except Exception as exc:
                self.deny(400, str(exc))
            return
        self.deny(404, "Unknown dashboard bridge route")

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/dashboard/pair":
            refresh_pair_state()
            origin = self.headers.get("Origin", "")
            if origin and origin not in ALLOWED_ORIGINS and not origin.startswith("http://127.0.0.1:") and not origin.startswith("http://localhost:"):
                self.deny(403, "Origin not allowed")
                return
            if not rate_ok(self.client_address[0] + ":pair", True):
                self.deny(429, "Too many pairing attempts")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0 or length > 4096:
                self.deny(400, "Invalid pairing body")
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception:
                self.deny(400, "Invalid JSON")
                return
            code = str(payload.get("code") or "").strip().upper() if isinstance(payload, dict) else ""
            if not PAIR_CODE:
                self.deny(410, "Pairing code unavailable. Generate a new code on the tower.")
                return
            if not PAIR_PINNED and (not PAIR_EXPIRES or time.time() > PAIR_EXPIRES):
                self.deny(410, "Pairing code expired. Generate a new code on the tower.")
                return
            if not constant_time_equal(code, PAIR_CODE):
                time.sleep(0.35)
                self.deny(401, "Pairing code is incorrect")
                return
            self.json_response(200, {"ok": True, "token": TOKEN, "paired_at": now_iso()})
            return
        if not self.preflight(True):
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            self.deny(400, "Invalid request body size")
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self.deny(400, "Invalid JSON")
            return
        if not isinstance(payload, dict):
            self.deny(400, "JSON object required")
            return

        if path == "/dashboard/control/game-mode":
            enabled = bool(payload.get("enabled"))
            cfg_path = ROOT / "data" / "config.json"
            cfg = load_json(cfg_path)
            if not isinstance(cfg, dict):
                cfg = {}
            cfg["light_mode"] = enabled
            cfg["light_mode_source"] = "manual_dashboard" if enabled else ""
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = cfg_path.with_name(cfg_path.name + ".tmp")
            tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            os.replace(tmp, cfg_path)
            game_state = find_game_mode_state()
            detected = bool(game_state.get("active"))
            self.json_response(200, {
                "ok": True,
                "requested": enabled,
                "active": detected or enabled,
                "automatic_game_detected": detected,
                "detail": "Game detected; automatic performance mode remains active." if detected and not enabled else "Gaming performance mode updated.",
            })
            return

        if path == "/dashboard/control/continuous":
            enabled = bool(payload.get("enabled"))
            code, result = core_json("/api/control/continuous", method="POST", body={"enabled": enabled}, timeout=12.0)
            if 200 <= code < 300:
                self.json_response(200, result)
            else:
                self.json_response(502, {"error": "Myles core rejected the continuous-improvement control", "detail": result})
            return

        if path.startswith("/dashboard/quant/live/"):
            try:
                route = path.removeprefix("/dashboard/quant/live/")
                if route == "setup/begin":
                    result = run_live_cli("--setup-begin", payload, timeout=90)
                elif route == "setup/finish":
                    result = run_live_cli("--setup-finish", payload, timeout=90)
                elif route == "arm":
                    result = run_live_cli("--arm", payload, timeout=60)
                elif route == "copy-auth":
                    result = run_live_cli("--copy-auth", payload, timeout=60)
                    try:
                        run_live_cli("--status", timeout=45)
                    except Exception:
                        pass
                elif route == "order":
                    result = run_live_cli("--order", payload, timeout=180)
                elif route == "approve":
                    result = run_live_cli("--build-approve", timeout=60)
                elif route == "withdraw":
                    result = run_live_cli("--build-withdraw", payload, timeout=60)
                else:
                    self.deny(404, "Unknown live trading route")
                    return
                self.json_response(200, result)
            except Exception as exc:
                self.deny(400, str(exc))
            return

        if path.startswith("/dashboard/quant/copy/"):
            try:
                route = path.removeprefix("/dashboard/quant/copy/")
                if route == "discover":
                    result = run_copy_cli("--discover", timeout=300)
                elif route == "config":
                    result = run_copy_cli("--config", payload, timeout=60)
                else:
                    self.deny(404, "Unknown copy-trader route")
                    return
                self.json_response(200, result)
            except Exception as exc:
                self.deny(400, str(exc))
            return

        if path == "/dashboard/quant/config":
            try:
                cfg = save_quant_config(payload)
                pid = start_quant_once(backtest_only=False)
                self.json_response(200, {"ok": True, "config": cfg, "quant_pid": pid, "paused_for_game": bool(find_game_mode_state().get("active"))})
            except Exception as exc:
                self.deny(400, str(exc))
            return

        if path == "/dashboard/quant/action":
            action = str(payload.get("action") or "").strip().lower()
            try:
                cfg = load_quant_config()
                if action == "run_backtests":
                    pid = start_quant_once(backtest_only=True)
                    if not pid:
                        raise RuntimeError("Could not start Quant validation process")
                    self.json_response(202, {"ok": True, "action": action, "pid": pid})
                    return
                if action == "reset_paper":
                    if QUANT_STATE.exists():
                        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        archived = QUANT_STATE.with_name(f"quant_paper_state_v3_before_reset_{stamp}.json")
                        QUANT_STATE.replace(archived)
                    pid = start_quant_once(backtest_only=False)
                    self.json_response(200, {"ok": True, "action": action, "pid": pid})
                    return
                if action in {"emergency_stop", "resume_paper"}:
                    cfg.setdefault("paper", {})["emergency_stop"] = action == "emergency_stop"
                    cfg = save_quant_config({"config": cfg})
                    pid = start_quant_once(backtest_only=False)
                    self.json_response(200, {"ok": True, "action": action, "pid": pid, "emergency_stop": cfg["paper"]["emergency_stop"]})
                    return
                self.deny(400, "Unknown Quant action")
            except Exception as exc:
                self.deny(500, str(exc))
            return

        if path == "/dashboard/quant/manual":
            try:
                action = str(payload.get("action") or "").strip().lower()
                if action not in {"open", "close", "close_all"}:
                    self.deny(400, "Manual paper action must be open, close, or close_all")
                    return
                result = run_quant_manual(payload)
                self.json_response(200, result)
            except Exception as exc:
                self.deny(400, str(exc))
            return

        if path != "/dashboard/messages":
            self.deny(404, "Unknown dashboard bridge route")
            return
        text = payload.get("message") or payload.get("text") or payload.get("prompt")
        if not isinstance(text, str) or not text.strip():
            self.deny(400, "Message text required")
            return
        text = text.strip()
        if len(text) > 6000:
            self.deny(400, "Message is too long")
            return
        code, data, route = send_to_myles(text)
        if 200 <= code < 300:
            if isinstance(data, dict):
                data = {**data, "bridge_route": route}
            self.json_response(200, data)
        else:
            self.json_response(code if code < 600 else 502, data)


def main() -> None:
    global TOKEN, PORT, PAIR_CODE, PAIR_EXPIRES, PAIR_PINNED, PAIR_CODE_FILE
    parser = argparse.ArgumentParser(description="Authenticated phone-to-tower bridge for Myles Dashboard")
    parser.add_argument("--token-file", required=True)
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--pair-code-file")
    args = parser.parse_args()
    PORT = args.port
    token_path = Path(args.token_file)
    TOKEN = token_path.read_text(encoding="utf-8").strip()
    if len(TOKEN) < 24:
        raise SystemExit("Pairing token is missing or too short")
    if args.pair_code_file:
        PAIR_CODE_FILE = Path(args.pair_code_file)
        refresh_pair_state()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    print(json.dumps({"ok": True, "listen": f"http://{HOST}:{PORT}", "core": CORE, "time": now_iso()}), flush=True)
    server.serve_forever(poll_interval=0.5)


if __name__ == "__main__":
    main()
