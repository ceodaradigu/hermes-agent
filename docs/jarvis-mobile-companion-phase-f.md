# JARVIS Mobile Companion Foundation - Phase F

Phase F adds a prepare-only Mobile Companion surface for future mobile clients.
It does not build a native app and does not enable mobile actions.

## What It Allows

- Read a safe Mobile Companion status.
- Read a safe mobile permission policy.
- Read a reduced Command Center snapshot for mobile UI experiments.
- Submit text for an intent preview.

All responses are small, serializable, and mobile-safe. They do not include
secrets, private paths, audio bytes, raw payloads, or runtime credentials.

## Endpoints

### `GET /mobile/companion/status`

Returns the default disabled mobile runtime posture:

```json
{
  "prepare_only": true,
  "mobile_available": false,
  "native_app_connected": false,
  "push_enabled": false,
  "background_sync_enabled": false,
  "location_enabled": false,
  "contacts_enabled": false,
  "camera_enabled": false,
  "microphone_enabled": false,
  "execution_enabled": false,
  "approval_actions_enabled": false,
  "requires_approval_for_sensitive_actions": true
}
```

### `GET /mobile/companion/permissions`

Returns the mobile permission policy:

```json
{
  "prepare_only": true,
  "can_read_command_center": true,
  "can_preview_intent": true,
  "can_execute": false,
  "can_approve": false,
  "can_reject": false,
  "can_use_location": false,
  "can_use_contacts": false,
  "can_use_camera": false,
  "can_use_microphone": false,
  "can_receive_push": false,
  "can_run_background": false
}
```

### `GET /mobile/command-center`

Returns a reduced projection of the Command Center view with counts,
high-level status, safe capabilities, and safety metadata. It does not expose
mission payloads, approval action bodies, Hermes command inputs, audit text,
audio fields, or paths.

### `POST /mobile/intent/preview`

Request:

```json
{
  "text": "crea una misión para investigar nichos"
}
```

Response:

```json
{
  "prepare_only": true,
  "input_text": "crea una misión para investigar nichos",
  "intent": "create_mission",
  "policy_decision": "allowed",
  "would_execute": false,
  "execution_enabled": false,
  "approval_created": false,
  "approval_gateway_called": false,
  "hermes_called": false,
  "mobile_action_allowed": false,
  "sensitive_boundary_triggered": false,
  "warnings": []
}
```

Sensitive input is redacted and marked as requiring approval or denied:

```json
{
  "prepare_only": true,
  "input_text": "[redacted sensitive mobile input]",
  "intent": "requires_approval",
  "policy_decision": "requires_approval",
  "would_execute": false,
  "execution_enabled": false,
  "approval_created": false,
  "approval_gateway_called": false,
  "hermes_called": false,
  "mobile_action_allowed": false,
  "sensitive_boundary_triggered": true,
  "warnings": ["Sensitive mobile preview details were redacted; execution remains disabled."]
}
```

The mobile preview uses the existing Voice Companion textual intent preview
classifier so mobile and voice surfaces share the same prepare-only intent
categories. The mobile DTO is separate and keeps mobile-specific safety flags.

## What It Does Not Allow

Phase F does not provide:

- Native mobile application code.
- Push notifications.
- Background sync.
- Location or GPS access.
- Contacts access.
- Camera or microphone access.
- Tracking.
- Task creation.
- Mission creation.
- Hermes runtime calls.
- ApprovalGateway request creation.
- Approve or reject actions.
- Credential or `.env` reads.

The following routes are intentionally absent:

- `POST /mobile/execute`
- `POST /mobile/approve`
- `POST /mobile/reject`
- `POST /mobile/push`
- `POST /mobile/location`
- `POST /mobile/background-sync`
- `POST /mobile/track`

## Safety Boundaries

- All Mobile Companion DTOs force `prepare_only=true`.
- Deserialization cannot enable execution, approvals, push, background sync,
  location, contacts, camera, or microphone capabilities.
- Intent preview is deterministic and in-memory only.
- No mobile endpoint persists data.
- No mobile endpoint calls Hermes.
- No mobile endpoint calls `ApprovalGateway.create_request`.
