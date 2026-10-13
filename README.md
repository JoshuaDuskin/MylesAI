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

The runtime also supports process/window-verified generic Windows app launch,
deterministic cancellation/replacement, and an Ollama capability check for the
selected model's tool and vision support. See `AGENT_STACK_AUDIT.md` for the
file-by-file agent architecture, verified capabilities, and provider gaps.

## Owner-enabled remote deployment

One-time bootstrap on the Windows tower installs the current source, then run `ENABLE_REMOTE_DEPLOY.ps1`. This creates a hidden five-minute scheduled task using the existing signed-in owner account. The agent polls the canonical GitHub `main` branch and recognizes only a fresh update request committed directly on top of the target source commit. The request commit must change only `.myles-deploy/request.json`; request IDs cannot replay. There is **no inbound port or remote shell**. It defers while gaming or owner work is active and starts the existing backed-up `UPDATE_TOWER.ps1` via a fixed, noninteractive wrapper. State and logs stay on the tower. `DISABLE_REMOTE_DEPLOY.ps1` turns it off. It does not deploy merely because source code was pushed to GitHub.

## Owner-enabled unattended tower updates (v10.12)

The GitHub deployment-request marker is no longer needed. Run the existing
installer once after updating tower source: `ENABLE_REMOTE_DEPLOY.ps1` writes
`data/remote_deploy_enabled.json` with `auto_update=true` and recreates the
existing hidden five-minute Windows scheduled poll task. The poller considers
only exact GitHub `main` commits with passing **push** CI on the canonical
`Validate MYLES Runtime` workflow. It never executes text from issues,
commit messages, README files or other remote inputs. A failed, pending or
missing CI verdict is treated as unapproved. Only descendants of the installed
commit qualify.

The backed-up local updater installs the exact verified SHA, not whatever
happens to be the most recent `main` at execution time. It defers while
gaming/light mode or owner tasks are active, avoids reattempting an already
failed SHA, and writes receipts locally under `data/remote_deploy_result.json`
and `data/remote_deploy_state.json`. The task operates while signed into
Windows. You can opt out with `DISABLE_REMOTE_DEPLOY.ps1`.

This is authorized **deployment** access, not a remote desktop or arbitrary
PowerShell shell. The ChatGPT session cannot inspect private local receipts
without a separate authenticated link. GitHub write access is a release
authority; restrict who may merge to main and require CI.

## v10.13 Fortnite priority mode

The canonical watcher checks process state every 2 seconds (rather than every
second), unloads the local Ollama model when gameplay starts, and periodically
re-enforces heavy worker cleanup without a per-second process-kill scan. Only
processes under the canonical MylesAI root are eligible for worker cleanup.
Fortnite temporarily pauses Quant, GMX, copy research, model inference and
both queued/active owner background jobs. Quick status/cancel commands remain
available without loading Qwen. Work resumes after the game exits. The
CI-approved updater already defers during gameplay. This is a targeted Myles
resource fix; network ping, graphics driver or GPU bottlenecks can also cause lag.


## v10.14 — private live tower deployment receipts (owner reporting)

The existing five-minute `MylesAI Remote Deploy Poll` also attempts a
read-only health report after each normal auto-update poll, except during
detected gameplay. No new scheduled tasks or inbound ports.

The **only** permitted destination is
`JoshuaDuskin/MylesTowerReceipts`. The tower requires an existing *dedicated*
Myles `GH_CONFIG_DIR` under the canonical local Myles directory, authenticated
as exactly `JoshuaDuskin`. If authorized, it creates the repository as
**private** using GitHub's authenticated API (only after a confirmed HTTP 404)
and publishes `health.json` on the private `main` branch. If authentication
is absent, creation fails, or the destination is not private, reporting stops.

The health file contains an allowlisted observation only: collection
timestamp, locally installed Git SHA, healthy Myles core/version, bridge and
gateway port reachability, local Quant/GMX/copy-worker process counts where
available, game/light-mode flags, Quant feed verification flag, and limited
update receipt state/health. It never includes original private receipts,
local source paths, chat, pairing credentials, environment values, API keys,
wallet data, trading balances, task text, errors, arbitrary command output,
or raw logs. The private GitHub repository is *not* the dashboard and is
never part of the updater's GitHub source selection.

**Access and trust:** The connected ChatGPT GitHub account must be granted
read access to the new private repository; this may require one user-authorized
GitHub App permissions adjustment. ChatGPT can then query current
`health.json` and compare its installed SHA with release CI, while checking
its freshness. An installed SHA or passing health endpoint alone cannot
prove that game FPS, every worker, and all performance goals are optimized.
A missing/stale receipt is reported as unknown, not a successful update.
