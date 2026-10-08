# MylesAI

This is the **single canonical source repository for MYLES**.

It owns:
- MYLES core/runtime and owner console
- dashboard/control center (`index.html` + `bridge.json`)
- authenticated tower bridge and public gateway
- Quant research, paper trading, copy research, and GMX execution code
- game mode / runtime supervision
- maintenance and self-update code

## Repository policy

Do not create or resume separate MYLES dashboard, status, bridge, control-center, trading-dashboard, or M83 repositories.

Historical repositories may remain temporarily for rollback/history, but they are not sources of truth and must not be used by the runtime.

The Solana wallet bundler is a separate product and is intentionally excluded from this repository.

## Runtime location

The tower runtime remains under:

`%LOCALAPPDATA%\MylesAI`

Runtime state, credentials, logs, databases, generated workspaces, and secrets are local-only and are excluded from Git.

## Dashboard

Canonical GitHub Pages dashboard: https://joshuaduskin.github.io/MylesAI/

All retired MYLES repositories are preserved under `legacy_archive/` for historical reference and are not runtime dependencies.

## Updating the tower

Use `UPDATE_TOWER.cmd` on the Windows tower, or run `UPDATE_TOWER.ps1` with Windows PowerShell.

The updater backs up the current Git state, preserves local runtime data/dependencies/credentials and tower-only files, syncs tracked source to `main`, rotates exposed bridge credentials while preserving the existing 8-character pairing code, restarts the canonical v0.74 runtime, and verifies the core/dashboard/Quant processes.

The updater also installs the canonical hidden runtime guardian at Windows
logon and on a five-minute recovery schedule, so a reboot or an unexpected
supervisor exit does not leave the phone dashboard offline.

The guardian runs through `pythonw.exe`, not a recurring PowerShell window.
MYLES durable jobs can inspect the real desktop, focus visible applications,
capture screenshots for local vision reasoning, and perform verified mouse and
keyboard actions. Desktop screenshots remain local to the tower.
