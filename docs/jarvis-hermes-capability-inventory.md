# JARVIS Hermes Capability Inventory

PR #134 exposes one Hermes-backed capability to JARVIS:

| Capability | Status | Notes |
| --- | --- | --- |
| `hermes.file.read` | Pilot only | Local `read_file` for one exact approved file. |
| filesystem write | Blocked | No `write_file`, `patch`, broad directories, or globs. |
| terminal/code execution | Blocked | No shell, subprocess, or execute-code bridge. |
| browser/web/network | Blocked | No browser, web search, web extract, MCP, plugins, or network adapters. |
| memory/todo/delegation | Blocked | No memory tools, todo tools, or `delegate_task`. |
| money/email/deploy | Blocked | No Stripe, email, deploy, production, or external operations. |

The purpose is to prove the JARVIS to Hermes bridge using the real `HermesRuntimeAdapter` and `AIAgent` path while keeping the runtime surface auditable and reversible.

Future capabilities must be reviewed after the controlled pilot. This document should not be read as approval for general Hermes execution.
