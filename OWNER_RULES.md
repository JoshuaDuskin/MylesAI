# Myles owner rules

- Canonical source and public dashboard: `JoshuaDuskin/MylesAI`.
- PineTree and `Solana-wallet-bundler-` are separate systems; Myles must never read, write, execute against, authenticate to, or publish to them.
- Public task/status surfaces must expose summarized labels and verified progress only. Never publish raw owner prompts, credentials, private keys, or unredacted tool output.
- Quant telemetry must come from the canonical tower runtime and official GMX data surfaces. Missing, stale, partial, or game-paused data must be labeled honestly.
- Paper trading may run automatically, record real simulated fills, show wins/losses, and promote only candidates that pass the configured stress and walk-forward validation gates.
- Live execution remains owner-controlled: no private seed or owner key is stored, no funds are moved automatically, and every live path requires the configured wallet, owner authorization/signature, explicit ARM, and an explicit live order. Restart, expiry, failed verification, or missing data fails closed.
- Changes to the canonical runtime must preserve local runtime data, credentials, helpers, backups, and the live safety gates.
