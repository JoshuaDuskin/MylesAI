# Retired MYLES repository archive

This directory preserves the current source snapshots from the retired MYLES repositories before deletion.

Canonical active repository: `JoshuaDuskin/MylesAI`

Dashboard Pages host: `https://joshuaduskin.github.io/MylesAI/`

## Archived repositories

| Repository | Final captured head / state | Archive note |
|---|---|---|
| progress-dashboard | `901f16be2a575107c86d8929d6e4b804ac9f2671` | Full current source copied |
| MylesDashboard | `3b17ddff286c3bfbbeac7eb7a33304e4cd9f24f2` | Full current source copied; legacy bridge credential redacted |
| myles-dashboard | `654ae211051273bf2ad7f35b5e8e0032512ece0e` | Source copied; generated status state omitted by SHA |
| Myles-AI-Dashboard | `1b47af45e3b50f879f0b2415ccea82139a3c1cbf` | Full current source copied |
| Myles-ControlCenter | `a092f9c01df3106c3d8c2e2d201f4740848676f2` | Full current source copied |
| trading-dashboard | `a448832a9a4c75f273b4197436f25b6867dea02f` | Full current source copied |
| MylesLiveStatus | repository deleted during consolidation | Current README/index reconstructed exactly from identical blob SHAs; generated status state omitted |
| Myles-Ecosystem | `0367653720e8780bff4c4f94188c9c390f949b11` | Full current source copied |
| M83-dashboard | `a0ffdc5e327a61b310809af814ed68923d448f7b` | Source copied; generated status state omitted by SHA |
| my-dashboard | `43f56af14a05a4753df8e5d676ad539412f6146b` | Full current source copied |
| tower-bridge | `89047d92aad9ca29a6bf1c3048061fb6b50144ae` | Full current source copied |
| M83-20260926-223024-c06164 | repository deleted during consolidation | Retirement README recovered; unique legacy index metadata recorded, source no longer retrievable after deletion |

## What is intentionally not preserved as active source

Generated runtime state, credentials, pair codes, tokens, databases, PIDs, and status snapshots are not active source code and are not copied into the canonical runtime.

The legacy archive must never be imported or executed automatically. It is historical reference only.

## Deletion rule

After this archive branch is merged into `main`, the surviving retired repositories above can be deleted without removing the canonical MYLES source. The Solana wallet bundler is intentionally separate and must not be deleted as part of MYLES cleanup.
