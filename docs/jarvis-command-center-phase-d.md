# JARVIS Command Center Phase D

Phase D introduces a backend/UI-ready view model for the future JARVIS Command Center.

This is a prepare-only layer. It does not create a frontend, endpoint, runtime, websocket, scheduler, mission executor, approval action, or Hermes connection.

## Implemented

- `CommandCenterViewModel`
- `MissionDashboardView`
- `ApprovalQueueView`
- `AuditTimelineView`
- `AgentStatusView`
- `RiskAndBudgetPanelView`
- `HermesPayloadView`
- `DeviceStatusView` placeholder
- `VoiceCameraControlsView` placeholder
- `CostRoiSummaryView` placeholder
- `SafetyIndicatorView`

The view model can be assembled from already prepared mission, approval, audit, budget, Hermes bridge, and agent registry contracts.

## Safety Boundaries

- The Command Center view model is read-only.
- It cannot approve or reject approvals.
- It cannot execute missions.
- It cannot call Hermes.
- It cannot call `ApprovalGateway`.
- It cannot mutate `MissionState`.
- It does not read secrets or environment files.
- Hermes payload views redact raw `inputs` and `metadata`.
- Device, voice, camera, and ROI panels are placeholders until later phases define trusted-device and runtime controls.
- Phase E adds a complete prepare-only Voice Companion foundation inside the voice/camera controls. It reports safe status, safe control policy, and a transcript preview capability. All microphone, wake-word, recording, streaming, auto-start, approval-creation, Hermes, and execution flags remain disabled.

`PolicyEngine` and `ApprovalGateway` remain authoritative. A future visual UI may render this model, but any action buttons must route through separate policy, approval, strong-approval, and audit flows.

## Phase D.1 Read-Only API

Phase D.1 exposes the prepared view model through `GET /command-center`.

The endpoint returns a serialized `CommandCenterViewModel` with safe empty placeholders when no trusted store is connected. It is read-only: it does not create missions, execute Hermes, call `ApprovalGateway`, approve, reject, open a WebSocket, read secrets, or connect voice/camera/audio runtime.

The response repeats the core safety flags at the top level and in `metadata`:

- `prepare_only: true`
- `execution_enabled: false`
- `approval_enabled: false`
- `approve_reject_enabled: false`
- `hermes_connected: false`
- `approval_gateway_called: false`

## Phase E Voice Companion Foundation

Phase E exposes a safe foundation for the future Voice Companion:

- `GET /voice/companion/status`
- `GET /voice/companion/control-policy`
- `POST /voice/companion/preview`

`POST /voice/companion/preview` is allowed in this phase because it is preview-only. It accepts a simulated transcript as text, classifies the intent with local deterministic components, applies `PolicyEngine`, redacts sensitive transcript output, and returns what would happen in a future runtime.

The policy is safe by default:

- `prepare_only: true`
- `microphone_requested: false`
- `wake_word_requested: false`
- `recording_requested: false`
- `streaming_requested: false`
- `auto_start_requested: false`
- `execution_requested: false`
- `requires_approval_for_activation: true`
- `activation_enabled: false`

The preview response always includes:

- `prepare_only: true`
- `would_execute: false`
- `execution_enabled: false`
- `approval_created: false`
- `approval_gateway_called: false`
- `hermes_called: false`

Example request:

```json
{
  "text": "crea una misión para investigar nichos"
}
```

Example safe response:

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
  "sensitive_boundary_triggered": false,
  "reason": "Matched a local create-mission or investigation phrase.",
  "warnings": []
}
```

Example sensitive request:

```json
{
  "text": "lee mi .env"
}
```

Example redacted response:

```json
{
  "prepare_only": true,
  "input_text": "[redacted sensitive transcript]",
  "intent": "requires_approval",
  "policy_decision": "requires_approval",
  "would_execute": false,
  "execution_enabled": false,
  "approval_created": false,
  "approval_gateway_called": false,
  "hermes_called": false,
  "sensitive_boundary_triggered": true,
  "reason": "Policy preview requires human approval before any future execution.",
  "warnings": ["Sensitive boundary detected; transcript redacted and execution remains disabled."]
}
```

Phase E does not start or connect voice runtime, microphone capture, wake-word detection, recording, streaming, TTS, Hermes, `MissionControl`, task creation, or `ApprovalGateway`. It does not read `.env`, secrets, credentials, or external services. There is no `POST /voice/companion/control`, start, stop, listen, record, stream, execute, approval, or activation endpoint in this phase.
