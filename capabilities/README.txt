Myles v9.1 capability modules

A capability is a provider-specific Python module in this directory.

Supported exports:
- TOOL_DEFS: OpenAI/Ollama-style function definitions.
- TOOLS: dict mapping tool names to callables(job_id=..., **args).
- DESCRIPTION: short description.
- AUTH_KIND: none, oauth, api_key, device_login, etc.
- STARTUP: optional no-argument startup hook.
- BACKGROUND_TICK: optional no-argument background hook.
- BACKGROUND_INTERVAL_SECONDS: cadence for BACKGROUND_TICK.

v9.1 runtime behavior:
- Capability modules are cached and keep module/session state until their source file changes.
- Background ticks are scheduled off the core job-monitor thread so a slow provider cannot freeze job dispatch/recovery.
- Only one background tick per capability runs at a time.
- Duplicate tool names are rejected/ignored rather than silently shadowing another provider.
- capability_plugins_enabled=false disables discovery/execution.
- Provider authentication/MFA should return:
  OWNER_AUTH_REQUIRED: <exact owner step>
- Ordinary provider/network failures should return:
  TOOL_ERROR: <concrete failure>

Security note:
Capability modules are trusted local Python code. The built-in PineTree guards protect Myles' standard tool layer, but arbitrary plugin code is not an OS sandbox. If PineTree must be cryptographically/OS-level inaccessible to Myles, run Myles under a separate Windows identity and use GitHub credentials that cannot access PineTree.
