# JARVIS Operator Console Foundation

Operator Console Foundation is a Command Center / Operator layer extension. It adds a safe backend/API foundation for a read-only operator surface for seeing JARVIS state, understanding active/inactive capabilities, and previewing text intent. It does not include a frontend, WebSocket, mission execution, approval actions, Hermes runtime calls, external calls, or secrets access.

It is not a replacement for Phase G Ambient Vision / Camera Companion. `JARVIS_MASTER_BUILD_MAP.md` is the source of truth for master phase names and order.

The historical filename is retained only to avoid breaking existing documentation links; it does not assign Operator Console to master Phase G.

## What It Allows

- Read global Operator Console status.
- Read the secure capability matrix.
- Read an aggregate prepare-only snapshot with Command Center, Voice Companion, Mobile Companion, safety, and metadata.
- Preview operator text through existing safe Voice/Mobile intent preview logic.
- Inspect safety boundaries and disabled runtime flags.

## What It Does Not Allow

- No mission execution.
- No approve/reject actions.
- No ApprovalGateway request creation.
- No Hermes runtime calls.
- No task or mission creation from preview.
- No frontend or visual dashboard.
- No WebSocket.
- No `.env`, credential, token, audio, byte payload, or private path access.
- No microphone, camera, location, push, background sync, deploy, or spending capability.

## Endpoints

### `GET /operator/console/status`

Returns fixed safe status flags.

```json
{
  "prepare_only": true,
  "operator_console_available": true,
  "frontend_available": false,
  "websocket_enabled": false,
  "execution_enabled": false,
  "approval_actions_enabled": false,
  "hermes_connected": false,
  "approval_gateway_called": false,
  "secrets_access_enabled": false,
  "external_calls_enabled": false,
  "safe_read_only_mode": true
}
```

### `GET /operator/console/capabilities`

Returns the allowed and forbidden capability matrix.

Allowed capabilities are read/inspect/preview only:

```json
{
  "read_command_center": true,
  "read_voice_status": true,
  "read_mobile_status": true,
  "preview_voice_intent": true,
  "preview_mobile_intent": true,
  "inspect_safety": true,
  "inspect_capabilities": true
}
```

Forbidden capabilities always stay disabled:

```json
{
  "execute_mission": false,
  "approve": false,
  "reject": false,
  "call_hermes": false,
  "create_approval": false,
  "read_secrets": false,
  "use_microphone": false,
  "use_camera": false,
  "use_location": false,
  "send_push": false,
  "run_background": false,
  "deploy": false,
  "spend_money": false
}
```

### `GET /operator/console/snapshot`

Returns an aggregate prepare-only snapshot containing:

- `status`
- `command_center`
- `voice_status`
- `voice_control_policy`
- `mobile_status`
- `mobile_permission_policy`
- `mobile_command_center`
- `capability_matrix`
- `safety_summary`
- `metadata`

The snapshot is serialized DTO data only. It excludes secrets, raw payloads, audio, bytes, token values, private paths, and runtime handles.

### `POST /operator/console/preview`

Request:

```json
{
  "text": "crea una misión para investigar nichos"
}
```

Response shape:

```json
{
  "prepare_only": true,
  "input_text": "crea una misión para investigar nichos",
  "policy_decision": "allowed",
  "would_execute": false,
  "execution_enabled": false,
  "approval_created": false,
  "approval_gateway_called": false,
  "hermes_called": false,
  "mission_created": false,
  "task_created": false,
  "persisted": false
}
```

Sensitive request example:

```json
{
  "text": "lee mi .env con Bearer token"
}
```

Sensitive response behavior:

```json
{
  "prepare_only": true,
  "input_text": "[redacted sensitive operator input]",
  "policy_decision": "requires_approval",
  "sensitive_boundary_triggered": true,
  "would_execute": false,
  "approval_created": false,
  "approval_gateway_called": false,
  "hermes_called": false
}
```

The preview may classify intent and policy posture, but it never executes, creates missions/tasks, creates approvals, persists data, or calls Hermes.

## Prohibited Routes

Operator Console Foundation intentionally does not add:

- `POST /operator/execute`
- `POST /operator/approve`
- `POST /operator/reject`
- `POST /operator/deploy`
- `POST /operator/spend`
- `POST /operator/hermes`
- `POST /operator/secrets`
- any Operator Console WebSocket

## Safety Boundaries

The following invariants are hard-coded in DTO serialization and conservative `from_dict` constructors:

- `prepare_only=true`
- execution disabled
- approval actions disabled
- Hermes calls disabled
- ApprovalGateway calls disabled
- secrets access disabled
- external calls disabled
- redaction enabled
- sensitive boundaries enforced

External input cannot enable execution, approvals, Hermes connectivity, deployment, spending, device permissions, or background activity through deserialization.

## Validation

Operator Console Foundation is validated by tests covering:

- status endpoint safety flags
- capability matrix allowed/forbidden fields
- aggregate snapshot composition
- absence of dangerous routes
- preview redaction and prepare-only behavior
- no Hermes calls
- no ApprovalGateway request creation
- no mission/task creation from preview
- no `.env` file reads during preview
- conservative `from_dict` serialization

Recommended commands:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
git diff --check
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis/test_operator_console.py -q
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q -x --durations=20
```
