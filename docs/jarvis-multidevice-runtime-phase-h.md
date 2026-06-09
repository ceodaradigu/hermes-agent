# JARVIS Multi-device Runtime - Phase H

Phase H adds a complete prepare-only foundation for coordinating future JARVIS
device surfaces without creating a distributed execution path. It defines safe
contracts for device identity, capability declarations, registry snapshots,
pairing/revoke previews, device approval-channel previews, sync previews, and
notification-routing previews.

There is no real multi-device runtime, pairing, trusted device, approval,
notification, sync, socket, WebSocket, persistence, or background process in
this phase.

## What It Allows

- Inspect a disabled Multi-device Runtime status.
- Inspect an empty, non-persistent device registry snapshot.
- Inspect a conservative placeholder capability profile.
- Preview whether pairing, revoke, approval-channel, sync, or notification
  routing was requested.
- Show prepare-only Multi-device Runtime status in Command Center and Operator
  Console.
- Model future desktop, mobile, watch, glasses, tablet, and unknown device
  types without trusting them.

## Safety Model

- A represented device is not a paired device.
- A paired device would not automatically become trusted.
- A trusted device would only enable an authorized channel; it would never
  substitute for `PolicyEngine`, `ApprovalGateway`, or strong approval.
- Sensitive approvals from a future authorized device require an exact action,
  challenge, scope, expiration, and audit correlation.
- No device can approve all actions forever. `approve_all_forever_allowed` is
  always `false`.
- External input cannot enable trust, approve/reject, execution, microphone,
  camera, location, notifications, sync, push, WebSocket, or background work.
- Snapshots contain no secrets, tokens, passphrases, pairing codes, or private
  identifiers.

## Endpoints

### Read-only snapshots

- `GET /devices/runtime/status`
- `GET /devices/registry`
- `GET /devices/capabilities`

The runtime status is disabled by default:

```json
{
  "prepare_only": true,
  "runtime_available": false,
  "device_registry_enabled": false,
  "trusted_devices_enabled": false,
  "pairing_enabled": false,
  "revoke_enabled": false,
  "approval_from_device_enabled": false,
  "sync_enabled": false,
  "notification_routing_enabled": false,
  "websocket_enabled": false,
  "background_runtime_enabled": false,
  "execution_enabled": false,
  "hermes_connected": false,
  "approval_gateway_called": false
}
```

The registry is empty and non-persistent. The capability endpoint returns one
safe placeholder profile that can view status and preview intent, but cannot
request or perform approvals, execute, use sensors, or receive notifications.

### Pairing preview

`POST /devices/pairing/preview`

```json
{
  "device_id": "phone-1",
  "device_type": "mobile",
  "pairing_requested": true
}
```

The response records only that pairing was requested. It does not pair or
trust the device and does not create a pairing code:

```json
{
  "prepare_only": true,
  "device_id": "phone-1",
  "device_type": "mobile",
  "pairing_requested": true,
  "would_pair_device": false,
  "device_trusted_after_preview": false,
  "pairing_code_created": false,
  "strong_approval_required": true,
  "approval_gateway_called": false,
  "execution_enabled": false,
  "reason": "Device pairing preview is prepare-only; no device is paired or trusted.",
  "warnings": ["Pairing requires a future explicit strong-approval flow."]
}
```

### Revoke preview

`POST /devices/revoke/preview` records a revoke request but does not remove or
mutate a device. A future real revoke must be audited.

### Approval-channel preview

`POST /devices/approval-channel/preview` models a future authorized approval
channel. It never trusts the device, creates an approval, approves, rejects, or
executes. Strong approval and a challenge remain required, including on mobile,
watch, glasses, tablet, or desktop.

### Sync and notification previews

- `POST /devices/sync/preview`
- `POST /devices/notifications/preview`

These endpoints return deterministic snapshots only. They do not persist
state, start background sync, route notifications, send push, or make external
calls.

## What It Does Not Allow

Phase H does not allow real pairing, trusted-device registration, revoke,
approve/reject, approve-all-forever, execution, Hermes calls, real
`ApprovalGateway.create_request`, mission/task creation, push notifications,
background sync, WebSockets, sockets, external calls, secret access, `.env`
reads, or persistence.

The following routes are intentionally absent:

- `POST /devices/pair`
- `POST /devices/revoke`
- `POST /devices/approve`
- `POST /devices/reject`
- `POST /devices/execute`
- `POST /devices/push`

## Relationship To Existing Surfaces

- **Mobile Companion:** supplies a future device surface, but remains
  prepare-only and cannot receive push, approve, or execute.
- **Voice Companion:** voice cannot bypass device trust or strong approval.
- **Ambient Vision:** camera capability remains disabled and cannot be enabled
  by a device capability declaration.
- **Command Center:** exposes only a disabled Multi-device Runtime status marker.
- **Operator Console:** aggregates the disabled status and empty registry for
  inspection; it cannot pair, revoke, approve, sync, notify, or execute.
