# JARVIS Ambient Vision / Camera Companion - Phase G

Phase G adds a complete prepare-only Ambient Vision foundation. It defines safe
camera/vision contracts, privacy policy, simulated session preview, hard-stop
control, API endpoints, and read-only Command Center / Operator Console
integration.

No endpoint connects to a camera or vision runtime.

## What It Allows

- Inspect the disabled Ambient Vision status.
- Inspect the camera privacy policy.
- Preview metadata for a simulated future visual session.
- Inspect the `"no mires"` hard-stop contract.
- Render a required visible camera-active indicator as a policy contract.
- Show prepare-only Ambient Vision placeholders in Command Center and Operator
  Console.

## Endpoints

### `GET /ambient-vision/status`

Returns a safe disabled posture. Camera, recording, streaming, continuous
watch, face/person analysis, external calls, image storage, and execution are
all disabled.

### `GET /ambient-vision/privacy-policy`

Returns the privacy contract:

```json
{
  "prepare_only": true,
  "camera_requires_explicit_start": true,
  "visible_indicator_required": true,
  "no_recording_by_default": true,
  "no_streaming_by_default": true,
  "no_face_analysis_by_default": true,
  "no_person_analysis_by_default": true,
  "no_retention_by_default": true,
  "no_external_uploads": true,
  "hard_stop_phrase": "no mires",
  "sensitive_capture_requires_strong_approval": true
}
```

### `POST /ambient-vision/session-preview`

This endpoint accepts only boolean metadata describing a simulated request:

```json
{
  "camera_requested": true,
  "recording_requested": false,
  "streaming_requested": false,
  "sensitive_capture_requested": false
}
```

It never starts a camera. A normal future camera request is marked as requiring
approval. Requests for recording, streaming, continuous watch, image storage,
external vision, face/person analysis, or sensitive capture trigger the
privacy boundary and require future strong approval:

```json
{
  "prepare_only": true,
  "session_requested": true,
  "would_start_camera": false,
  "would_record": false,
  "would_stream": false,
  "would_store_images": false,
  "would_call_external_vision": false,
  "would_analyze_people": false,
  "would_execute": false,
  "approval_required": true,
  "strong_approval_required": true,
  "privacy_boundary_triggered": true,
  "reason": "Ambient Vision session preview is prepare-only; no camera, recording, streaming, storage, external vision, approval, Hermes, mission, task, or execution path is enabled.",
  "warnings": [
    "Sensitive visual capability requested; future activation would require strong approval and remains disabled."
  ]
}
```

The preview is deterministic and in-memory only. It does not create a real
approval request.

### `GET /ambient-vision/stop-control`

Returns the hard-stop contract. `"no mires"` is the required stop phrase. In
this prepare-only phase there is no active session and no stop execution path.
A future real stop must be immediate and audited.

## Privacy Boundaries

- Camera start must always be explicit.
- A visible camera-active indicator is mandatory for any future runtime.
- Recording and streaming are disabled by default.
- Continuous watch is disabled.
- Face and person analysis are disabled by default.
- Image retention is disabled by default.
- External uploads and external vision calls are disabled.
- Privacy redaction is enabled as a contract.
- Sensitive capture requires strong approval in a future runtime.
- `"no mires"` represents an always-available hard stop.

## What It Does Not Allow

Phase G does not provide real camera or webcam access, video recording,
streaming, WebSockets, continuous surveillance, face/person analysis, image
storage, image uploads, external vision services, Hermes calls, mission/task
creation, execution, real approval creation, credential access, `.env` reads,
or local file reads.

The following routes are intentionally absent:

- `POST /ambient-vision/start`
- `POST /ambient-vision/stop`
- `POST /ambient-vision/record`
- `POST /ambient-vision/stream`
- `POST /ambient-vision/analyze-face`
- `POST /ambient-vision/analyze-person`
- `POST /ambient-vision/upload`
