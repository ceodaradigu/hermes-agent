# Mark 3 Hermes Runtime Integration Smoke

PR #134 implements a minimal governed vertical slice:

`Mark3MissionLoop candidate -> governed validation -> HermesRuntimeAdapter -> AIAgent -> read_file -> outcome/evidence -> Mission Loop`

This is not a general execution platform. The only supported operation is an exact local file read:

- tool: `read_file`
- action type: `filesystem_read`
- capability: `hermes.file.read`
- backend: `local`
- scope: one exact regular file

The bridge requires an existing approved, unexpired approval record whose action and fingerprint match the candidate. The API does not create approvals and does not accept payload fields such as `approved=true` or `actor=operator` as authorization.

The operational endpoints are:

- `GET /mark-3/hermes-runtime/status`
- `POST /mark-3/hermes-runtime/execute-read`
- `GET /mark-3/hermes-runtime/sessions/{session_id}`
- `POST /mark-3/hermes-runtime/sessions/{session_id}/stop`

`execute-read` and `stop` require an internal authorization callback injected by the application. Without it they return `503 operator authorization channel not configured`.

Blocked in PR #134:

- writes, patching, broad directory reads, globs, and `search_files`
- terminal, browser, network, MCP/plugins, memory tools, todo tools, and subagents
- money, email, deploy, production operations, and provider cost attestation
- general grants, identity platform, budget ledger, and distributed execution

Evidence records only observed runtime facts: requested tool, path fingerprint, observed result/error, duration, and interruption state. Evidence is marked verified only when the test/fake adapter demonstrates the exact guarded call.

Timeout and stop cancellation are cooperative. The bridge requests `interrupt()` once and waits only for a short bounded grace period. If the worker does not cooperate, the session is returned as `cancellation_pending` or `timeout_interrupt_pending` with `worker_alive=true` and `forced_cancellation_available=false`; PR #134 does not forcibly kill runtime workers.
