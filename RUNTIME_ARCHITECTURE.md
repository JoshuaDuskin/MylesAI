# Myles local runtime boundary

Myles has one authoritative Windows runtime and one canonical repository:
`JoshuaDuskin/MylesAI`. Files under `legacy_archive/` are historical only.

## Process ownership

`START_MYLESAI.cmd` opens one visible owner console and ensures one hidden
`bin/runtime_supervisor_v074.py` is running. The supervisor owns the durable
services and restarts missing components without opening extra consoles.
`bin/ensure_myles_runtime.py` is launched directly by `pythonw.exe` at per-user
logon and by a hidden five-minute recovery task. It never creates a PowerShell
or Command Prompt window, restarts an absent supervisor immediately, and only
drains an unhealthy supervisor after three consecutive failed checks.

```text
START_MYLESAI.cmd
  ├─ visible: bin/myles_console_v074.py
  └─ hidden: bin/runtime_supervisor_v074.py
       ├─ myles_core.py                 127.0.0.1:8766
       │   ├─ resilient Qwen/Ollama conversation runtime
       │   ├─ optional privacy-safe TypeSafe Jev decision adapter
       │   ├─ durable job monitor / job_worker.py
       │   ├─ Telegram conversation loop
       │   └─ capability/plugin hooks
       ├─ dashboard_bridge.py           127.0.0.1:8790
       ├─ public_gateway_v074.py        127.0.0.1:8791
       ├─ game_mode_watch.py
       ├─ quant/quant_service.mjs
       ├─ quant/gmx_live.mjs
       ├─ quant/copy_trader_service.mjs
       └─ public tunnel to gateway 8791
```

Root `runtime_supervisor.py` and `myles_console.py` are import-safe
compatibility entry points only. `setup_myles.py` and `restart_helper.py`
are retired guards/shims and do not own runtime startup.

## Conversation and decision path

Ordinary conversation stays in the conversation lane. Explicit owner actions may
start or modify durable jobs; questions, venting, feedback, and context do not.
The local model runtime discovers an installed Ollama model, prefers Qwen, starts
Ollama when it is absent, and degrades to truthful natural replies while it
recovers instead of returning a controller error.

TypeSafe Jev is an optional typed decision coprocessor, never the conversational
brain. When enabled and locally credentialed, it receives only boolean and
bucketed abstract routing state through the official System One Choice contract.
It never receives owner text, conversation history, memory, files, credentials,
or tool output. Low confidence, timeout, missing credentials, or schema failure
preserves the local rules/Qwen decision.

Background actions run through the durable job worker and verified tools. Work
is not marked complete without real tool evidence. Safe transient failures retry
internally; durable jobs resume in their existing workspace. Owner interaction
is reserved for authentication, MFA, consent, or a risky irreversible choice.

Stop/cancel commands pass through a hard deterministic gate before desktop or
model routing. A global stop disables continuous work, terminates current
workers, cancels queued/recovering/auth-blocked jobs, and revokes their worker
leases. Pending jobs are atomically claimed so only one monitor can launch them.

Every tool attempt writes a bounded typed record to the SQLite evidence ledger,
including provenance, outcome class, limitations, and a digest. Unverified
requested effects are recorded separately as unknowns. Model prose is not
evidence and cannot override either ledger.

Each durable job also has one agent session, an optional bounded plan, and
durable tool-call records. The model receives a compact authoritative snapshot
of the session, plan, recent calls, evidence IDs, and open unknowns on each
worker slice. Context compaction preserves the system contract and newest
working turns within a fixed budget rather than allowing old chatter or tool
logs to crowd out the current task.

## Continuous learning boundary

MYLES may improve reusable tools, recovery logic, prompts, and candidate
strategies, but it may not silently rewrite the live runtime. Runtime
self-improvements are cloned, verified, and promoted through the supervisor's
restart-and-rollback contract. Quant research continuously evaluates the full
enabled market-by-strategy matrix, records evaluator faults, uses stressed-cost
and walk-forward gates, and remains paper-only until the owner separately arms
live execution.

## Dashboard data path

The public dashboard is root `index.html` on GitHub Pages. It discovers the
current tower endpoint and read-only credential from `bridge.json`, then reads:

```text
iPhone browser
  -> public tunnel
  -> public gateway :8791
  -> authenticated private bridge :8790
  -> Myles core :8766 + local Quant telemetry
```

The dashboard never invents health, Quant, or GMX values. Live state comes from
the authenticated tower gateway. Legacy Git-backed polling/status publishers
and static snapshots are rejected.

## Quant data path

`quant/quant_service.mjs` writes the canonical paper telemetry to
`data/trading_status.json`. GMX oracle requests use the primary Arbitrum
oracle host plus official fallback hosts. The dashboard bridge only marks Quant
verified when the telemetry is fresh, identifies itself as SIMULATED PAPER, and
reports a GMX data source.

Gaming Performance Mode may intentionally stop heavy Quant/GMX workers. In
that state the dashboard should show the pause rather than claim a feed failure.

## State boundaries

- `data/`: database, config, secrets, pairing/read credentials, PID/lock files,
  restart requests, game mode state, and trading telemetry.
- `logs/`: supervisor, core, bridge, gateway, Quant, and repair evidence.
- `workspaces/`: durable owner-task workspaces.
- `backups/`: recoverable pre-change and self-update copies.
- `capabilities/`: optional provider modules.
- `self_updates/`: candidate runtime updates before promotion.

These paths are local-only and are preserved by `UPDATE_TOWER.ps1`.

## Verification contract

`UPDATE_TOWER.ps1` and `FINALIZE_TOWER.ps1` do not pass merely because a
process exists or a port is listening. They verify fresh gateway status and,
unless Gaming Performance Mode is active, verified Quant telemetry with actual
GMX market rows.

Self-updates use a restart request owned by the supervisor. The supervisor
clears the request before starting the replacement core, verifies health, and
restores the recorded backup if the promoted candidate cannot come back healthy.

## 10.7 assisted mode (source only until next owner tower update)

Explicit read-only requests to inspect a text file, list a directory, or inspect open application windows can run inside the conversational agent turn. Tool authorization checks the current owner request, target, path grounding, secret paths, and PineTree isolation. Each observation has a session, tool-call lifecycle, bounded output, and retained evidence ID. Repeated calls are blocked and the per-turn budget is bounded. All mutations, shell commands, installs, desktop interactions and autonomy remain on the existing durable-job lane. This change does not install itself or change PineTree, the dashboard, or live trading.

## 10.8 assisted visual inspection and verified focus

Owner-requested screen inspection requires Ollama-advertised vision and an interactive Windows desktop. A PNG is captured into a private temporary file, validated by digest/size, attached to the same local model conversation, and removed immediately. Evidence stores only metadata, never image bytes. Protected PineTree windows block capture. A request to focus an already-open window now executes immediately only for one uniquely matching window and with actual foreground verification. Click, type, installs and broad automation remain durable jobs. No tower deployment occurs when this repository source is changed.

## 10.9 pull-only deployment

Opt-in scheduled Windows owner task polls verified canonical GitHub main requests. Explicit, fresh, exact-parent, single-file requests can invoke only the built-in backup-and-recovery updater. Gaming and owner-work gates defer deployments. No inbound service, generic command runner, dashboard modification, PineTree change, wallet signing or live-trading activity is introduced. Logs/receipts remain local.

## 10.10 REA-derived behavioral verification

The behavior replay suite encodes owner-intent scenarios (ordinary speech, questions,
read-only inspection, direct window focus, navigation and adverse tool repetition)
using observable input/output contracts instead of guessing hosted agent internals.
Pure, fast desktop navigation keys are now sent in the foreground conversation
with an allowlist and verified app focus; this proves OS input-event delivery,
not the resulting UI state. Generic typing and clicks remain tracked background
jobs with observation and verification. The conversation tool loop permits at
most one background job per turn and refuses repeated side-effect tools; worker
launch failures can no longer be described as RUNNING. No PineTree/dashboard
or live-trading changes.

## 10.11 context and visual proof

The owner conversation takes up to 120 stored recent turns, prioritizes the
latest conversation, and selectively recalls relevant older messages within a
bounded local-model context. Historical messages never authorize actions. Transient read-only
inspection failures get at most one guarded retry; mutating tools are never
blindly replayed.
Conversation tool calls are bounded and exceptions remain explicit unverified
outcomes. The worker no longer treats two screenshots plus input delivery as
proof the owner's requested desktop state changed. A local vision comparison
must report a specific, high-confidence visible effect; failures stay unknown.
Full-desktop screenshots are refused when a protected PineTree window is visible.
Windows acceptance diagnostics are read-only by default; live model calls are
explicit opt-in. Generic model-selected coordinate clicks now require a valid
before-action screenshot and use a local before/after vision comparison. A click
or screenshot alone never satisfies visual-effect completion. No dashboard or
trading changes.
