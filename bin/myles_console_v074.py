from __future__ import annotations

import ctypes
import json
import os
import sys
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("LOCALAPPDATA", "")) / "MylesAI"
DATA = ROOT / "data"
BASE = "http://127.0.0.1:8766"
DASHBOARD = "https://joshuaduskin.github.io/MylesDashboard/"
MUTEX = "Local\\MylesOwnerConsole_v074"
STOP = threading.Event()
SEEN: set[int] = set()
PRINT_LOCK = threading.Lock()

# One visible console only.
k32 = ctypes.windll.kernel32
mutex = k32.CreateMutexW(None, False, MUTEX)
if k32.GetLastError() == 183:
    sys.exit(0)

try:
    k32.SetConsoleTitleW("Myles")
except Exception:
    pass

# Enable ANSI without shelling out to cmd.exe.
try:
    h = k32.GetStdHandle(-11)
    mode = ctypes.c_uint32()
    if k32.GetConsoleMode(h, ctypes.byref(mode)):
        k32.SetConsoleMode(h, mode.value | 0x0004)
except Exception:
    pass

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
except Exception:
    pass

RESET="\x1b[0m"; BOLD="\x1b[1m"; DIM="\x1b[2m"
CYAN="\x1b[96m"; BLUE="\x1b[94m"; GREEN="\x1b[92m"; YELLOW="\x1b[93m"; RED="\x1b[91m"; WHITE="\x1b[97m"; GRAY="\x1b[90m"

ART = [
" __  __ __   __ _      _____ ____",
"|  \\/  |\\ \\ / /| |    | ____/ ___|",
"| |\\/| | \\ V / | |    |  _| \\___ \\",
"| |  | |  | |  | |___ | |___ ___) |",
"|_|  |_|  |_|  |_____||_____|____/",
]


def clear_screen():
    # ANSI clear avoids spawning cmd.exe / cls.
    print("\x1b[2J\x1b[H", end="", flush=True)


def http_json(path: str, method: str = "GET", body=None, timeout: int = 60):
    data = None
    headers = {"Accept":"application/json", "User-Agent":"MylesOwnerConsole/0.7.4"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", errors="replace")
        return json.loads(raw) if raw.strip() else {}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return {}


def health():
    try:
        d = http_json("/health", timeout=4)
        return d if isinstance(d, dict) and d.get("ok") else None
    except Exception:
        return None


def public_status():
    try:
        d = http_json("/api/public-status", timeout=5)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def messages():
    try:
        d = http_json("/api/messages", timeout=5)
        rows = d.get("messages", []) if isinstance(d, dict) else []
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def compact(value, limit=82):
    s = " ".join(str(value or "").split())
    return s if len(s) <= limit else s[:limit-1] + "…"


def elapsed_since(value):
    if not value:
        return "—"
    try:
        d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        now = datetime.now(d.tzinfo)
        secs = max(0, int((now - d).total_seconds()))
        h, rem = divmod(secs, 3600); m, s = divmod(rem, 60)
        if h: return f"{h}h {m}m"
        if m: return f"{m}m {s}s"
        return f"{s}s"
    except Exception:
        return "—"


def current_info(s: dict):
    task = s.get("current_task") if isinstance(s, dict) else None
    queue = s.get("queue") if isinstance(s, dict) else []
    queue = queue if isinstance(queue, list) else []
    game = bool(s.get("game_mode") or s.get("gaming")) if isinstance(s, dict) else False
    if isinstance(task, dict) and task:
        phase = str(task.get("phase_display") or task.get("phase") or task.get("state") or "working")
        raw_state = str(task.get("state") or "running").lower()
        if "wait" in raw_state or "auth" in phase.lower() or "2fa" in phase.lower():
            state = "WAITING"
        else:
            state = "WORKING"
        nxt = queue[0] if queue else None
        next_title = "Nothing queued"
        if isinstance(nxt, dict):
            next_title = nxt.get("label") or nxt.get("title") or nxt.get("prompt") or "Queued task"
        return {
            "state": state,
            "task": task.get("label") or task.get("title") or task.get("prompt") or "Owner task",
            "phase": phase,
            "elapsed": elapsed_since(task.get("started_at")),
            "activity": task.get("last_action") or task.get("last_tool") or phase,
            "queue": len(queue),
            "next": next_title,
        }
    return {"state":"GAMING" if game else "IDLE", "task":"Ready for you.", "phase":"Idle", "elapsed":"—", "activity":"—", "queue":len(queue), "next":"Nothing queued"}


def render_header():
    h = health(); s = public_status(); info = current_info(s)
    q = load_json(DATA / "trading_status.json")
    g = load_json(DATA / "gmx_live_status.json")
    eng = q.get("engine") or {} if isinstance(q, dict) else {}
    clear_screen()
    print(CYAN + BOLD + ("="*100) + RESET)
    for row in ART:
        print(BLUE + BOLD + "  " + row + RESET)
    print(DIM + "  OWNER AI  •  LOCAL RUNTIME  •  TELEGRAM  •  DASHBOARD  •  TRADING" + RESET)
    print(CYAN + BOLD + ("="*100) + RESET)
    if h:
        state_color = GREEN if info["state"] in ("IDLE","GAMING") else CYAN
        print(f" {state_color}{BOLD}{info['state']:<8}{RESET}  {WHITE}Myles v{h.get('version','?')}{RESET}  {GRAY}PID {h.get('pid','?')}{RESET}")
    else:
        print(f" {YELLOW}{BOLD}STARTING{RESET}  waiting for the local runtime")
    print(GRAY + ("-"*100) + RESET)
    print(f" {GRAY}TASK     {RESET}{WHITE}{compact(info['task'],86)}{RESET}")
    print(f" {GRAY}PHASE    {RESET}{CYAN}{compact(info['phase'],32)}{RESET}   {GRAY}ELAPSED{RESET} {WHITE}{info['elapsed']}{RESET}")
    print(f" {GRAY}ACTIVITY {RESET}{WHITE}{compact(info['activity'],70)}{RESET}")
    print(f" {GRAY}QUEUE    {RESET}{WHITE}{info['queue']}{RESET}   {GRAY}NEXT{RESET} {WHITE}{compact(info['next'],68)}{RESET}")
    print(GRAY + ("-"*100) + RESET)
    if eng:
        print(f" {GRAY}QUANT    {RESET}{GREEN if str(eng.get('status','')).lower()=='running' else YELLOW}{str(eng.get('status','?')).upper()}{RESET}  v{eng.get('version','?')}  {WHITE}{str(q.get('mode','?')).upper()}{RESET}  equity {WHITE}{q.get('equity','—')}{RESET}")
    else:
        print(f" {GRAY}QUANT    {RESET}{YELLOW}status unavailable{RESET}")
    print(f" {GRAY}GMX      {RESET}{RED if not g.get('armed') else GREEN}{'DISARMED / SAFE' if not g.get('armed') else 'ARMED'}{RESET}   auto {'ON' if g.get('auto_enabled') else 'OFF'}")
    print(CYAN + ("-"*100) + RESET)
    print(DIM + " Talk normally.  Stop = stop current owner work.  /status  /dashboard  /clear  /quit" + RESET)
    print(CYAN + BOLD + ("="*100) + RESET)
    print()


def mark_existing():
    for m in messages():
        try: SEEN.add(int(m.get("id")))
        except Exception: pass


def background_messages():
    while not STOP.wait(2.5):
        for m in messages():
            try: mid = int(m.get("id"))
            except Exception: continue
            if mid in SEEN: continue
            SEEN.add(mid)
            role = str(m.get("role") or "").lower()
            source = str(m.get("source") or "")
            content = str(m.get("content") or "").strip()
            if not content or role != "assistant" or source == "console": continue
            with PRINT_LOCK:
                print(f"\n{CYAN}{BOLD}MYLES >{RESET} {content}\n")
                print(f"{WHITE}{BOLD}YOU   >{RESET} ", end="", flush=True)


def send_with_thinking(text: str):
    box = {"done":False, "data":None, "error":None}
    def work():
        try: box["data"] = http_json("/api/send", method="POST", body={"text":text,"source":"console"}, timeout=180)
        except Exception as e: box["error"] = e
        finally: box["done"] = True
    threading.Thread(target=work, daemon=True).start()
    frames = ["Thinking   ","Thinking.  ","Thinking.. ","Thinking..."]
    i=0
    while not box["done"]:
        with PRINT_LOCK:
            print(f"\r{CYAN}{BOLD}MYLES >{RESET} {DIM}{frames[i%len(frames)]}{RESET}", end="", flush=True)
        i += 1; time.sleep(.32)
    with PRINT_LOCK:
        print("\r" + (" "*64) + "\r", end="", flush=True)
    if box["error"]: raise box["error"]
    return box["data"] if isinstance(box["data"], dict) else {}


def main():
    end=time.time()+45
    while time.time()<end and not health(): time.sleep(1)
    render_header(); mark_existing()
    threading.Thread(target=background_messages, daemon=True).start()
    while True:
        try: text=input(f"{WHITE}{BOLD}YOU   >{RESET} ").strip()
        except (EOFError, KeyboardInterrupt): print(); break
        if not text: continue
        low=text.lower()
        if low in {"/quit","quit","exit"}: break
        if low in {"/clear","clear"}: render_header(); continue
        if low in {"/status","status"}: render_header(); continue
        if low=="/dashboard": webbrowser.open(DASHBOARD); print(f"{CYAN}{BOLD}MYLES >{RESET} Opened the dashboard."); continue
        try:
            d=send_with_thinking(text)
            mid=d.get("message_id")
            if mid is not None:
                try: SEEN.add(int(mid))
                except Exception: pass
            reply=str(d.get("reply") or "").strip(); job=d.get("job_id")
            if reply: print(f"{CYAN}{BOLD}MYLES >{RESET} {reply}")
            elif job: print(f"{CYAN}{BOLD}MYLES >{RESET} Started {job}. I’ll keep working in the background.")
            else: print(f"{CYAN}{BOLD}MYLES >{RESET} Request accepted.")
        except Exception as e:
            print(f"{YELLOW}{BOLD}MYLES >{RESET} Local runtime reconnecting ({type(e).__name__}).")
    STOP.set()
    try: k32.ReleaseMutex(mutex)
    except Exception: pass

if __name__ == "__main__":
    main()
