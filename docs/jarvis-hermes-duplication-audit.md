# JARVIS Hermes Duplication Audit

PR #134 avoids creating a parallel runtime architecture.

Reused components:

- `jarvis.mark_3_mission_loop.Mark3MissionLoop` for mission state, outcomes, evidence, and audit.
- `jarvis.runtime.hermes_adapter.HermesRuntimeAdapter` for Hermes sessions.
- `run_agent.AIAgent` for the actual agent runtime.
- Hermes `read_file` as the only tool exposed in this pilot.
- Existing approval records and context fingerprints for approval gating.

New code is limited to `jarvis/mark_3_hermes_runtime_bridge.py`, which performs candidate validation, exact-path guarding, one-shot Hermes invocation, outcome normalization, and session stop/timeout handling.

Not duplicated or introduced:

- no second executor
- no second tool registry
- no second filesystem abstraction
- no new approval framework
- no identity platform
- no complex grants
- no budget ledger
- no terminal/browser/network adapters
- no MCP/plugin execution path

The bridge is intentionally narrow. It demonstrates a safe vertical slice and leaves broader runtime decisions for after the real pilot.
