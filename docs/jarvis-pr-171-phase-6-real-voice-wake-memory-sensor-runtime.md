# PR #171 - Phase 6 Real Voice, Wake, Memory & Sensor Runtime

Date: 2026-06-19

## Summary

Phase 6 turns the Phase 5 voice/wake/memory/sensor readiness into a local
runtime pilot contract. It keeps the core boundary intact:

```text
JARVIS governs, classifies risk, asks approval, audits, stops and controls.
Hermes executes only behind existing JARVIS-governed execution paths.
```

This phase does not add `/execute`, shell-freeform execution, direct frontend
Hermes calls, hidden microphone/camera use, continuous transcription by default,
raw audio/video storage by default, model downloads, provider installs, money
movement, deploy, email sending, or public exposure.

## What Is Real

- `VoiceProviderRegistry` reports honest provider status for browser STT/TTS,
  faster-whisper, whisper.cpp, Silero VAD, openWakeWord, Piper and Wyoming.
- `VoiceSessionManagerV2` provides a real in-memory lifecycle for:
  `idle`, `listening`, `transcribing`, `thinking`, `speaking`,
  `awaiting_approval`, `awaiting_spoken_challenge`, `cancelled`, `error`.
- Voice session v2 supports manual push-to-talk starts, wake-started sessions,
  redacted transcript metadata, cancellation, timeout and stop-global.
- `WakeRuntimeOptIn` provides a real opt-in/manual transcript fixture runtime.
  It can start a voice session but cannot approve or execute.
- Phase 5 spoken approval was hardened for Phase 6 with active voice session
  checks, wake-only rejection, Spanish bounded phrases and challenge enforcement.
- `MemoryBrainV3` wraps the existing SQLite-backed Memory Brain v2 store with
  review, compaction preview and influence explanation contracts.
- `SensorRuntimeOptIn` provides metadata-only opt-in, active state, stop/cancel
  and local-retention delete controls for microphone, camera, screen context,
  audio recording, video recording and wake metadata.
- `/mark-3/dashboard/status`, `/mark-3/dashboard/events`, SSE and `/jarvis`
  expose Phase 6 provider/session/wake/sensor/memory state without raw media or
  secrets.

## What Remains Readiness

- openWakeWord is not started as a real microphone listener.
- Silero VAD, faster-whisper, whisper.cpp, Piper and Wyoming are not executed.
- Browser Web Speech API remains a client-side/manual fallback; backend reports
  it as `client_side_unknown`.
- No heavy models are downloaded and no provider dependencies are installed.
- Sensor runtime controls metadata only. Actual camera/microphone capture remains
  browser-local/manual and must use visible opt-in controls.
- Voice approval is testable through transcript fixtures. Real STT-to-approval
  audio evidence is not stored and is not required.
- Memory compaction is preview-only; no summarized memory is auto-applied.

## Endpoints

New Phase 6 endpoints:

- `GET /mark-3/phase-6/status`
- `POST /mark-3/phase-6/stop-global`
- `GET /mark-3/voice-providers/status`
- `GET /mark-3/voice-session-v2/status`
- `POST /mark-3/voice-session-v2/start`
- `POST /mark-3/voice-session-v2/transition`
- `POST /mark-3/voice-session-v2/cancel`
- `GET /mark-3/wake-runtime/status`
- `POST /mark-3/wake-runtime/opt-in`
- `POST /mark-3/wake-runtime/fixture`
- `GET /mark-3/sensor-runtime/status`
- `POST /mark-3/sensor-runtime/opt-in`
- `POST /mark-3/sensor-runtime/start`
- `POST /mark-3/sensor-runtime/stop`
- `POST /mark-3/sensor-runtime/delete`
- `GET /mark-3/memory-brain-v3/status`
- `GET /mark-3/memory-brain-v3/review`
- `GET /mark-3/memory-brain-v3/compaction-preview`
- `GET /mark-3/memory-brain-v3/influence`

Hardened Phase 5 spoken approval endpoints remain:

- `GET /mark-3/voice-approval/status`
- `POST /mark-3/voice-approval/start`
- `POST /mark-3/voice-approval/decision`

## Spoken Approval Rules

Normal spoken approval accepts:

- `JARVIS, autorizo`
- `JARVIS, confirmo`
- `JARVIS, apruebo esta acción`
- `JARVIS, autorizo con límite de X euros` only when `X` is within the approval
  session's configured euro cap.
- `JARVIS, autorizo durante X minutos` only when `X` fits within the approval
  session TTL.

Deny/cancel phrases:

- `JARVIS, cancela`
- `JARVIS, deniega`

Required gates:

- active voice session;
- when `voice_session_id` is supplied, active session is verified server-side
  against Voice Session Manager v2 and the client-supplied active flag is not
  trusted;
- when `voice_session_id` is absent, legacy/direct Phase 5 control-plane
  compatibility may use `voice_session_active=true`; this is not a real browser
  microphone session and still cannot bypass trusted device, readback,
  challenge, expiry, anti-replay, revoke state or audit;
- trusted non-revoked device scoped for `voice_approval`;
- exact readback;
- exact action/scope/cost context;
- expiration;
- anti-replay;
- metadata-only audit;
- wake phrase alone never approves;
- voice never downgrades risk.

For strong/high-risk approvals, generic Spanish phrases and bounded phrases are
not enough. The exact challenge phrase generated for that session is required.
Critical/double/triple policy remains governed by existing approval gates; voice
does not become an approve-all channel.

## Voice And Wake Privacy Rules

- no hidden microphone;
- no continuous transcription by default;
- no raw audio storage by default;
- no backend microphone start;
- wake opt-in is explicit and visible;
- wake opens a session only;
- wake never approves and never executes;
- stop-global cancels active voice/wake/sensor sessions.

## Memory Rules

- memory can store entity, project, decision, preference, fact and contradiction
  records through Memory Brain v2;
- every memory keeps provenance, confidence, sensitivity and explanation fields;
- sensitive memory requires explicit request/review/approval;
- secrets and credentials are rejected;
- forgotten/deleted memory is excluded from active influence;
- compaction is preview-only in this phase;
- the legacy dashboard `memory_brain.compaction.status` remains
  `contract_only` and `memory_brain.forget_delete.status` remains
  `future_gated`; Phase 6 preview/delete capability is exposed separately under
  Memory Brain v3 / Phase 6 fields;
- memory never grants permission, approves actions, dispatches Hermes or
  downgrades risk.

## Sensor Rules

- microphone, camera, screen context, audio recording, video recording and wake
  metadata default off;
- opt-in is required before start;
- visible indicator is required when active;
- stop/cancel is supported;
- local retention delete is modeled;
- no hidden camera;
- no hidden microphone;
- no biometric/person identification by default;
- no cloud upload;
- metadata-only audit by default.

## External Research

Network research was available. Repos and docs inspected:

- [dscripka/openWakeWord](https://github.com/dscripka/openWakeWord),
  Apache-2.0: useful wake provider candidate. Adopted only as a readiness
  provider contract; rejected runtime start/model download for this PR.
- [snakers4/silero-vad](https://github.com/snakers4/silero-vad), MIT visible in
  repo metadata: useful VAD candidate; adopted only as diagnostics/readiness.
- [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp), MIT: useful
  local STT binary candidate; adopted only as binary/model readiness checks.
- [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper), MIT:
  useful Python STT candidate; rejected default execution because model loading
  can download or require heavy local assets.
- [openai/whisper](https://github.com/openai/whisper), MIT: reference STT
  implementation; not adopted because faster-whisper/whisper.cpp are better
  pilot targets.
- [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl), GPL-3.0 in
  current repo name/surface: useful local TTS reference but not adopted due
  license/runtime review needs.
- [OHF-Voice/wyoming](https://github.com/OHF-Voice/wyoming), MIT: useful local
  assistant protocol candidate; adopted only as disabled local protocol hook.
- [MDN Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API):
  browser STT/TTS fallback reference; kept client-side/manual.

No external code was copied.

## Manual Validation

1. Start the local API normally.
2. Confirm `/execute` and `/jarvis/execute` are absent.
3. Open `GET /mark-3/phase-6/status`.
4. Confirm provider diagnostics show no fake readiness and no model downloads.
5. Start a manual voice session with `POST /mark-3/voice-session-v2/start`.
6. Transition it through `transcribing`, `thinking`, `speaking`, then cancel it.
7. Enable wake opt-in with `POST /mark-3/wake-runtime/opt-in`.
8. Send `Hola Jarvis, revisa estado` to `/mark-3/wake-runtime/fixture` and
   confirm a session starts but `approval_granted=false`.
9. Pair a local voice device through the Phase 5 pairing endpoints.
10. Create a normal pending approval, start voice approval, and approve with
    `JARVIS, autorizo con límite de 25 euros` only when the session cap allows it.
11. Create a strong approval and confirm generic/bounded phrases are denied;
    only the exact generated challenge is accepted.
12. Use `/mark-3/sensor-runtime/opt-in`, `/start`, `/stop` and `/delete` and
    confirm status stays metadata-only.
13. Open `/jarvis` and verify the Phase 6 folded rail shows provider/session,
    wake, sensor and memory v3 state.
14. Confirm dashboard events include `phase_6_state`, `voice_provider_state`,
    `wake_runtime_state`, `sensor_runtime_state`, `memory_brain_v3_state` and
    `spoken_approval_state` without raw audio, frames or secrets.

## Next Recommended Macro-Phase

PR #172 should be a manual local voice pilot on David's machine:

- choose one STT path (`whisper.cpp` or `faster-whisper`) and one TTS path
  (Piper or browser-only);
- require explicit model paths, no auto-download;
- run a real push-to-talk audio file/microphone test under visible opt-in;
- connect VAD/wake only after false-positive and privacy validation;
- add manual evidence capture for provider latency/accuracy without raw audio
  persistence by default;
- keep spoken approval transcript-fixture-compatible for tests.
