# Myles local runtime boundary

Myles has one authoritative local runtime. The folders in the archive are not
independent launchers.

## Process ownership

`START_MYLESAI.cmd` opens the one visible owner console and starts the hidden
`runtime_supervisor.py`. The supervisor owns `myles_core.py`; the core owns the
local HTTP API, Telegram polling, capability hooks, job monitor, and workers.
Workers are hidden child processes and write to `logs/worker.log`. The visible
console is only a conversation surface and may be closed without stopping the
supervisor.

```text
START_MYLESAI.cmd
  ├─ visible: myles_console.py
  └─ hidden: runtime_supervisor.py
       └─ hidden: myles_core.py
            ├─ hidden: job_worker.py (one owner job at a time)
            ├─ Telegram conversation loop
            ├─ capability/plugin hooks
            └─ localhost API on 127.0.0.1:8766
```

There is no Startup VBS launcher. `setup_myles.py` is retired. The runtime is
started deliberately from one named command file, so a repair or a reboot does
not create duplicate cores or flashing command windows.

## State boundaries

- `data/`: database, config, secrets, PID files, restart/stop requests.
- `logs/`: supervisor, core, worker, capability, and restart evidence.
- `workspaces/`: durable task artifacts; generated work is never treated as
  the live runtime until verification promotes it.
- `backups/`: recoverable pre-change copies.
- `capabilities/`: optional provider modules; a missing module is reported as
  unavailable, not invented as working.
- `self_updates/`: candidate runtime updates before promotion and rollback.

The supplied ZIP did not contain the live contents of several state/plugin
directories. The installer preserves existing live data and copies only the
verified runtime files and the specifically repaired generated artifacts.

## Conversation and work contract

Normal conversation stays conversational. A direct request to build, fix,
inspect, audit, investigate, or change something enters the durable owner-job
lane. The worker persists the prompt, phase, heartbeat, tool evidence, result,
and failure state. Completion requires evidence; a model sentence alone cannot
claim that a file, deployment, URL, or task exists.

Ordinary failures are retried or recovered locally. OAuth, MFA, payment/security
consent, and genuinely owner-only gates are the exceptions that can be surfaced
to the owner. PineTree remains excluded at the application/tool boundary.
