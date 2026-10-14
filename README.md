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


## v10.14 — same-repository tower health, NO second repository

The existing signed-in owner's five-minute auto-deployment poll also runs
`bin/tower_health_issue.py` after checking for CI-approved updates. It uses
the **same** `JoshuaDuskin/MylesAI` repository, editing only the body of
[Issue #49](https://github.com/JoshuaDuskin/MylesAI/issues/49).
Editing an issue **does not create a Git commit**, trigger deployment, or
change source code.

Because `MylesAI` is a **public** GitHub repository, the issue only
receives an extremely limited, explicitly allowlisted **public** report:
installed commit SHA, observed core version and health, two local service
ports, recent verified Quant-feed flag, non-sensitive worker counts (or
null if inaccessible), and whether the private, locally stored deployment
receipt matches the installed commit. It never uploads raw receipts, log
contents, private tasks, trading balances, wallets, game activity, IPs,
pairing codes, tokens, credentials, file paths or host/user names.

Reporting is independent from CI/update decisions, skips active gaming,
and is rate-limited to at most one attempt every nine minutes. Reports
are stale 20 minutes after their timestamp and must never be treated as
a verified live tower status after that point. The reporter requires the
*already configured* dedicated GitHub CLI profile from
`data/github_identity.json` authenticated as `JoshuaDuskin`, plus
permission to edit Issue #49. It NEVER falls back to Windows' default
GitHub token or uses another project's credentials. If dedicated GH auth
or issue-edit permissions are missing, it records a local failure but does
not publish anything or weaken authentication. No new repo or scheduled
task is created. This is **sanitized reporting**, not private remote-shell
access; a successful report is not a benchmark of game FPS or hardware.

To verify from ChatGPT, fetch GitHub Issue #49 and check that its marker,
`reported_at` freshness, `installed_commit`, and locally observed health
are all consistent with the latest approved GitHub main release.


### v10.14.1 verification correction

Quant feed health in Issue #49 is computed using the existing gateway's
`local_trading_snapshot()` validator, which checks source, paper mode,
engine, file/record freshness and generated timestamps. The raw Quant file
does not itself contain the gateway's `_verified` metadata. The status
publisher also bypasses environment HTTP proxies for the local core probe.


### v10.14.2 — verified GitHub owner authorization fallback

The tower reporter prefers the dedicated Myles GitHub CLI configuration. If
that profile is not present or no longer authorized, it can use a previously
signed-in **JoshuaDuskin** GitHub CLI profile after confirming the actual
GitHub API identity is exactly `JoshuaDuskin`. It strips inherited GitHub
token/config environment values, never uses a configured PineTree identity,
and writes exclusively the existing MylesAI Issue #49. No new repository,
OAuth bypass, unattended token creation or credential exposure. If neither
profile is authorized to edit the issue, reporting fails closed and remains
local until the tower account is authorized.


## v10.15.0 — measurable live-model and REA baseline

The owner-authorized existing five-minute tower updater launches **one**
windowless, lower-impact intelligence baseline per installed commit, only
on the signed-in Windows tower during a verified idle/non-gaming period.
There is no new task scheduler, model install, data reset, PineTree access,
wallet action, trading execution or remote shell. Game Mode also terminates
this explicitly identified MYLES benchmark worker if Fortnite launches.

The benchmark tests the **actually installed** Ollama model (not a mocked
hosted model): conversational recall/corrections, uncertainty, arithmetic,
and harmless mock-tool selection. The tool definitions are not connected to
real side effects. It requests `keep_alive: 0` to release model residency.
Then it executes the pinned REA 6.4.0 `doctor` and, if available, static
analysis of a tiny REA fixture inside the existing MylesAI repository.
No private target, game executable, Muse or Grok service is inspected.
REA failure/timeout stays explicitly unverified, not a success. The probe
never reveals proprietary model weights or internals.

Full benchmark results are stored locally in
`data/intelligence_baseline_latest.json`. The existing same-repo GitHub
Issue #49 reporter may publish **only** boolean capability flags, number
of passing test cases, status, and REA outcome kinds; no model responses,
chat, screenshots, user files, hardware identifiers, credentials, wallet
values or raw REA records are published. A successful GitHub CI test alone
does **not** mean this Windows baseline has executed. The user can see the
actual local results only after a true tower run and a report check-in.

Real benchmarks are necessary before changing the installed default local
model or introducing optional hosted-model credentials. PineTree remains
isolated and live trading remains OFF.


## v10.15.1 — one-click GitHub check-in authorization

GitHub CI and the existing unattended updater can read **public** source
without logging into GitHub, but publishing sanitized results to public
Issue #49 requires owner-approved GitHub **write** credentials on Windows.
The existing GitHub connection in ChatGPT does not authorize the Windows
computer. When the tower's dedicated GitHub CLI is not yet authorized, the
owner can double-click `CONNECT_TOWER_REPORTING.cmd` inside the existing
`%LOCALAPPDATA%\MylesAI` installation. No PowerShell or new repository.
GitHub CLI opens its official browser/device approval. The only accepted
identity is exactly JoshuaDuskin; `public_repo` scope is requested because
writing a public issue requires it. Credentials stay in the owner's isolated
`data/github_cli_tower` CLI store and are never written into the public repo,
issue, model prompts, dashboard, logs or chat. A previous local GitHub identity
is preserved for rollback. The script checks the same Issue #49, then attempts
an authentic tower report and announces CONNECTED only after GitHub confirms
the write. If GitHub CLI is missing or authorization is declined, it fails
closed; it never uses PineTree credentials or creates another repository.
This one-time owner approval cannot be manufactured by GitHub CI.


## v10.15.2 — fix interrupted CI update receipts and unblock real REA tests

The v10.15.1 Windows updater's general process cleanup could kill the
**PowerShell parent receipt writer** when its command line included the
canonical Myles directory. The installed commit and services could be
healthy while `remote_deploy_state.json` stayed `launched` indefinitely,
blocking the intelligence benchmark.

The updater now explicitly protects only the identified, fixed-purpose
`remote_deploy_apply.ps1` parent PID during the source switch. If the
*already-installed* old updater kills this wrapper on the first upgrade,
the new auto-update poller can recover **without faking the missing receipt**.
It requires at least five minutes elapsed, wrapper confirmed exited, exact
canonical installed commit, matching successful GitHub main push CI, and
real healthy core/bridge/gateway/verified Quant evidence. It then records
`installed_verified_post_restart` with a separate verification source,
not `succeeded`, because original wrapper exit code remains unavailable.
Issue #49 exposes both the independent post-restart verification and the
truth about whether the original receipt exists. No existing trading account,
paper history, pairing, local data or PineTree project is touched.

After this verifiable transition, the existing unattended benchmark may
run the actual installed Ollama model and pinned REA against only its
repository-owned fixture, while idle and off-game. This is not a claim that
these runtime benchmarks have passed before the tower reports results.


### v10.15.3 — evidence-backed phone chat and complete replies

Phone requests like “Give me report” and “With the background job” now read
the durable job database rather than trust a small-model paraphrase. Replies
state the actual worker, phase and verified result or failure and never
launch a new job merely to report. Cut-off model sentences are rejected
before saving. Continuous-job status no longer asserts “running normally”
without checking live worker truth. REA remains a separate **software
analysis instrument**, not a model or automatic integration: diagnostic
fixture tests do not count as research on Grok/Muse behavior.
