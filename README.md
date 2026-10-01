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
