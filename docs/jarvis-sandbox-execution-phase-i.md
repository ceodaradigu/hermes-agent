# JARVIS Sandbox Execution - Phase I

Phase I adds a complete prepare-only Sandbox Execution foundation. It models a
future isolated executor, conservative policy, command plans, mandatory dry-run
results, filesystem scope checks, secret detection, rollback previews, and
audit previews.

There is no real executor in this phase. No endpoint runs a command, shell,
subprocess, tool, rollback, install, network request, Hermes action, or
ApprovalGateway action.

## What It Allows

- Inspect a disabled Sandbox Execution status.
- Inspect the default-deny execution policy.
- Prepare a redacted command plan.
- Evaluate command text with a mandatory dry-run preview.
- Detect requests involving dangerous commands, secrets, network, installs,
  production, or a working directory outside the empty allowlist.
- Preview rollback requirements and audit records without executing or
  persisting them.
- Inspect prepare-only Sandbox Execution snapshots in Command Center and
  Operator Console.

## Safety Model

- `prepare_only`, mandatory dry-run, filesystem scope enforcement, secret
  scanning, rollback, and audit requirements cannot be disabled by external
  input.
- `sandbox_available`, `executor_connected`, and `execution_enabled` remain
  `false`.
- The allowed working-root list is empty. A requested working directory is
  therefore outside scope and blocked.
- Network, production, and install actions are blocked by default.
- Production, secrets, and installs require a future strong-approval flow, but
  strong approval alone would not enable execution in this phase.
- Commands containing secret-like markers are fully redacted before appearing
  in plans, dry-run warnings, rollback previews, or audit previews.
- Rollback and audit are previews only. No files or persistent records are
  created or changed.

## Endpoints

### Read-only snapshots

- `GET /sandbox/execution/status`
- `GET /sandbox/execution/policy`

The status is disabled by default:

```json
{
  "prepare_only": true,
  "sandbox_available": false,
  "executor_connected": false,
  "execution_enabled": false,
  "dry_run_required": true,
  "filesystem_scope_enforced": true,
  "secret_scan_enabled": true,
  "network_access_enabled": false,
  "production_access_enabled": false,
  "install_commands_enabled": false,
  "rollback_required": true,
  "audit_required": true,
  "hermes_connected": false,
  "approval_gateway_called": false
}
```

### Command plan and mandatory dry-run

- `POST /sandbox/command/plan`
- `POST /sandbox/command/dry-run`

Example request:

```json
{
  "command": "python -m pytest tests/jarvis -q",
  "working_directory": ""
}
```

The plan records the safe command text and classification, but always returns
`would_execute=false` and `execution_enabled=false`. The dry-run reports risk,
scope, secret scan, network, production, install, approval, rollback-preview,
and audit-preview decisions without calling an executor.

A secret-like request is redacted and blocked:

```json
{
  "command": "[redacted sensitive sandbox command]",
  "requested_secret_access": true,
  "would_execute": false,
  "execution_enabled": false,
  "requires_strong_approval": true,
  "blocked": true
}
```

### Rollback and audit previews

- `POST /sandbox/rollback/preview`
- `POST /sandbox/audit/preview`

Rollback preview describes whether a future action appears reversible or
irreversible and whether a rollback plan is required. It never performs a
rollback. Audit preview returns a redacted, non-persistent representation of a
future execution audit record.

## What It Does Not Allow

Phase I does not allow real command execution, shell access, subprocesses,
filesystem reads or writes, `.env` or secret reads, broad network access,
production access, installs, deploys, Hermes calls, real
`ApprovalGateway.create_request`, mission/task creation, persistence,
WebSockets, sockets, or background work.

The following routes are intentionally absent:

- `POST /sandbox/execute`
- `POST /sandbox/run`
- `POST /sandbox/shell`
- `POST /sandbox/install`
- `POST /sandbox/network`
- `POST /sandbox/production`

## Why Execution Is Not Enabled Yet

The repository does not contain a merged and validated JARVIS sandbox executor
with isolation, filesystem boundaries, time and network limits, secret
protection, rollback handling, and execution audit guarantees. Enabling real
execution before those controls exist would violate the Phase I safety
boundary. This foundation provides the contracts and policy decisions needed
to review such an executor later without exposing a premature execution path.
