# Myles Control Center — OWNER LOCK

This repository is the owner's canonical production dashboard.

## Non-negotiable
- Continuous/self-improvement jobs MUST NOT redesign, rewrite, replace, commit, push, or publish this repository.
- Runtime status belongs on the authenticated tower bridge, not in Git commits.
- No generic admin templates, mock/random telemetry, fake prices, fake API endpoints, alternate Myles dashboards, or placeholder live balances.
- Preserve the dark mobile-first Control Center, phone bridge, chat, Tasks, Systems, Scalp Terminal, Auto Bot, Research, Funding, Positions, and Advanced views.
- Only an explicit owner-requested dashboard installer/task may modify production, and it must deliberately unlock the local Git protections for the verified publish, then re-lock them.
- PineTree remains off-limits to Myles.

## Canonical repository map
- Owner UI: `JoshuaDuskin/MylesDashboard`
- Quant/live trading source: `JoshuaDuskin/trading-dashboard`
- Live runtime/chat/trading telemetry: authenticated tower bridge
- Never create another Myles dashboard, control-center, progress, runtime-status, or live-status repository.

## Live trading invariants
- Never store or request the owner's wallet private key or seed phrase.
- GMX live execution uses a GMX one-click delegated subaccount key encrypted locally with Windows DPAPI.
- Arming LIVE and enabling LIVE Auto require a fresh signature from the configured owner wallet.
- Manual LIVE open, close, close-all, cancel, or cancel-all actions are permitted only during the explicit 8-hour owner-armed session and use the limited GMX one-click subaccount without repeated wallet prompts.
- LIVE Auto requires its own owner signature and may act only while the owner-armed session is active and only on validation-passing closed-candle Quant signals.
- Withdrawals are never delegated to Myles; withdrawals require an owner-wallet transaction signature.
- LIVE Auto defaults OFF and must remain separate from the paper Auto Bot toggle.
- Never silently raise the live margin, notional, leverage, position-count, stop-loss, or take-profit limits.
- LIVE risk-limit changes must be owner-signed with the exact new limits bound into the authorization message; do not accept unsigned or ambiguously signed limit changes.
- Never move funds merely because wallet setup succeeded. Setup must finish DISARMED.

## Live GMX execution invariants
- Owner custody only: never request, store, log, or commit the owner wallet private key or seed phrase.
- GMX one-click subaccount material is tower-local and Windows-DPAPI encrypted.
- Manual LIVE orders are allowed only while the explicit 8-hour owner-armed session is active.
- LIVE Auto requires a separate owner signature and only consumes closed-candle signals whose research validation passes.
- Any live-adapter restart fails closed: manual LIVE and LIVE Auto return to DISARMED/OFF.
- Withdrawals are never delegated; the owner wallet signs the USDC transfer.

## Owner-only production dashboard
- `JoshuaDuskin/MylesDashboard` is the single source of truth for the Myles production UI.
- Myles runtime, continuous improvement, owner jobs, autonomous jobs, tool jobs, PowerShell, browser automation, and GitHub tools MUST NEVER modify, redesign, replace, commit, push, publish, force-update, or create an alternative to this dashboard.
- Myles may inspect it read-only for diagnostics.
- Production dashboard releases are external owner-approved release operations only.
- Live runtime/chat/trading state belongs on the authenticated tower bridge, not a GitHub status repository.


## Owner-installed connection supervisor exception
- The external owner-installed connection supervisor may update **only** `bridge.json` when the public tower tunnel endpoint changes after restart.
- This narrow pointer update is not a dashboard redesign or status feed. It exists only so the immutable production UI can discover the authenticated tower bridge.
- The connection supervisor MUST NOT modify `index.html`, `AGENTS.md`, styling, layout, trading logic, status snapshots, or any other repository path after this owner-approved release.
- Myles jobs, continuous improvement, autonomous work, tools, and normal runtime activity remain read-only against this repository.
