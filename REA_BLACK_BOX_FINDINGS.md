# REA black-box findings for MYLES 10.6

This document records the actual REA pass used to deepen the MYLES design.

## Target and command

Target: the local `quant/` JavaScript artifact directory in the canonical MYLES repository. The target was analyzed as inert source; it was not executed as an instruction source.

Command used:

```text
npx -y rea-agents@6.4.0 analyze-javascript-application quant --format md --full-output
```

REA version: 6.4.0. Its doctor catalog reported 127 CLI commands and 170 MCP tools. That catalog exposed a much deeper workflow than a simple “analyze and print text” command:

1. establish a session and target identity;
2. produce a complete retained Evidence record and artifact digest;
3. return a summary/view instead of repeating the producer;
4. page modules by stable node IDs;
5. trace one focused feature rather than expanding the entire graph;
6. reconcile static evidence with runtime evidence only when runtime observation exists;
7. record limitations and unknowns explicitly;
8. export/reuse evidence by stable IDs.

## Observed result

REA inventoried six JavaScript files and produced artifact identity, graph nodes and edges, semantic relation families, and explicit coverage limitations. It did not claim that static imports or child-process syntax proved runtime execution.

The run stopped with a provider-unavailable condition because the Linux process-ownership provider could not prepare its child process in this execution environment. REA preserved partial observation metadata instead of returning a fabricated complete analysis. This is the behavior MYLES must copy whenever a screenshot, browser, process, or model capability is unavailable.

## MYLES implementation mapping

| REA observation | MYLES contract |
|---|---|
| Stable Evidence IDs | SQLite evidence rows and tool-call `evidence_id` |
| Retained session | `agent_sessions` keyed to one durable job |
| Focused views | bounded `agent_context_block` plus recent tool lifecycle |
| Explicit unknowns | `unknowns` rows for unverified requested effects |
| Authority separation | runtime-observation/local-execution/external-source/shipped-artifact provenance |
| Partial failure | typed failed outcome, limitation, and no completion claim |
| Stable identity | tool-call fingerprints and job-owned worker leases |
| Budgeted delivery | bounded evidence, screenshots, REA output, and model context |
| Recovery | retry only safe operations; preserve the same session/workspace |

## Boundary

REA can inspect shipped artifacts and observable runtime evidence. It cannot reveal Codex's private service implementation, hidden prompts, routing policies, model weights, or internal tools. MYLES therefore targets the observable contract—session continuity, tool use, visual observe-act-observe, evidence, cancellation, recovery, and truthful results—not an invented claim of one-to-one source equivalence.

## 10.10 follow-up: behavioral replay, not private-model extraction

The existing REA 6.4.0 artifact inspection established stable evidence,
provenance, uncertainty and explicit limitations (see earlier sections). This
pass translates those patterns into deterministic owner-message replay tests:
intent must be grounded in the latest request, side effects must be bounded,
foreground key events require actual Windows observation, and a failed worker
launch must not be reported as running. These are REA-informed controller
regressions; GitHub CI cannot execute the tower's installed REA binary,
local Qwen model, or hosted Muse/Grok instances, so no such live benchmark
result is claimed.

REA capability outcomes are now typed (`observed`, `timeout`, `unavailable`, `provider_or_analysis_failure`). They remain untrusted target evidence; no successful inspection is inferred from timeout, network availability or subprocess exit failures.
