Myles v9.1.1 - audited autonomy foundation

Key corrections after the v9.0.1 full-runtime audit:
- Long imperative tasks cannot be misclassified as STATUS just because their desired output contains words such as "progress" or "status".
- High-confidence action requests bypass model routing; the exact owner wording becomes the job prompt.
- Ambiguous semantic routing receives the exact latest owner message and has internal JSON retries.
- The local API port is bound before Telegram starts, preventing duplicate cores from creating competing Telegram pollers.
- Capability modules are cached so provider sessions/state persist.
- Provider background ticks no longer block the core job monitor.
- Safe transient tools use bounded internal retry; non-idempotent shell/browser actions are never blindly replayed.
- Completion verification reuses verified publish-tool evidence and correctly strips Markdown around URLs.
- Explicit no-fake/no-sample requests reject obvious simulated/sample artifacts.
- Self-update candidates include the full v9 runtime and failed self-updates can roll back after a health-check failure.
- PineTree remains blocked at the built-in task/tool layer.

Preserved:
- Telegram secrets/configuration
- DB/history
- workspaces
- browser profile
- isolated JoshuaDuskin GitHub profile
- capability plugins
- backups

Important security boundary:
The PineTree deny rules are an application-level boundary inside Myles. Arbitrary locally installed Python/plugin code runs with the Windows user's permissions. True non-bypassable PineTree isolation requires OS/account/credential separation.

v9.4 lookup/self-provisioning corrections:
- Weather parser strips day words from location tails and expands US state abbreviations.
- Direct weather geocoding tries normalized and city-only variants, then bounded web evidence.
- Self-capability requests are routed to a fresh Myles workspace, never the previous project.
- Generic pronouns such as "look it up" no longer falsely attach to the previous artifact.
