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
- Phase E adds a read-only Voice Companion status placeholder inside the voice/camera controls. It reports `prepare_only: true`, all microphone, wake-word, recording, streaming, auto-start, availability, and execution flags as `false`, and `approval_required_for_sensitive_actions: true`.

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

## Phase E Voice Companion Status

Phase E exposes `GET /voice/companion/status` as a read-only foundation endpoint for the future Voice Companion.

It does not start or connect voice runtime, microphone capture, wake-word detection, recording, streaming, TTS, Hermes, `MissionControl`, or `ApprovalGateway`. There is no POST companion action endpoint in this phase.
