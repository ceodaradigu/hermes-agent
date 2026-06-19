# PR #170 - Phase 5 Local Controller, Trusted Identity, Pairing & Voice Approval

Date: 2026-06-19

## Summary

PR #170 turns Phase 4 readiness into a safer local foundation for controller
status, persistent trusted identity, hardened local pairing, governed spoken
permission, triple approval identity gates, notifications readiness, and the
`/jarvis` cockpit view.

The architecture remains the same:

```text
JARVIS governs, classifies risk, asks approval, audits, stops and controls.
Hermes executes only behind existing JARVIS-governed execution paths.
```

This phase does not add an unsafe `/execute` route, does not allow free shell
from UI, does not expose a public port, does not start Telegram/mobile remote
execution, and does not make wake phrase approval possible.

## What Is Real

- `Phase5LocalControllerTrustedIdentityVoiceApprovalControlPlane` extends the
  Phase 4 control plane without duplicating Hermes.
- Persistent trusted device identity uses local SQLite through
  `Phase5IdentityStore`.
- Device public identifiers and fingerprint material are hashed before storage.
- Revoked devices remain revoked across process restart and cannot be silently
  re-trusted by import/deserialization.
- Local pairing uses a short-lived challenge, nonce, exact phrase, exact scope,
  public identifier binding, one-time use, failed attempt tracking, lockout, and
  audit events.
- Voice approval is transcript-fixture testable and metadata-only by default.
- Spoken approval requires an active voice approval session, trusted non-revoked
  device, exact readback, matching challenge/phrase, matching scope/cost/action,
  expiration check, anti-replay check, policy/approval gateway decision, and
  audit.
- Triple approval checks persistent trusted identity, exact action id, optional
  scope fingerprint, exact expected channel, current challenge, no replay, and
  audit-chain validity before delegating to the existing triple approval logic.
- `/mark-3/dashboard/status`, `/mark-3/dashboard/events`, and `/jarvis` expose
  Phase 5 state as cockpit/readiness cards, not a dense admin dashboard.
- `scripts/local/jarvis-local-controller-dev.py` provides a manual local-only
  controller helper for status, opt-in, start/stop intent, kill switch, register
  and heartbeat flows.

## What Remains Readiness

- Native tray is not installed in this phase. The status is explicitly
  `readiness_only_not_installed`.
- The dev controller script records safe local intents; it does not install a
  background daemon, autostart entry, or OS tray.
- Local notifications are readiness contracts and persisted metadata events, not
  OS-native push notifications.
- Telegram/mobile remain notification/readiness concepts only. They do not
  approve or execute.
- Voice approval consumes text transcripts for tests and control-plane
  integration. Real STT/wake/VAD/TTS engines are not wired here.
- Raw audio evidence is not stored. If future evidence storage is added, it must
  be explicit opt-in, local-only, and audited.

## Endpoints

New or hardened Phase 5 endpoints:

- `GET /mark-3/phase-5/status`
- `POST /mark-3/local-controller/opt-in`
- `POST /mark-3/local-controller/start-request`
- `POST /mark-3/local-controller/kill-switch`
- `POST /mark-3/trusted-devices/import-preview`
- `GET /mark-3/local-pairing/status`
- `POST /mark-3/local-pairing/challenge`
- `POST /mark-3/local-pairing/verify`
- `GET /mark-3/voice-approval/status`
- `POST /mark-3/voice-approval/start`
- `POST /mark-3/voice-approval/decision`
- `GET /mark-3/notifications/status`

Existing Phase 4/3 routes remain in force and still block public exposure,
direct Hermes, remote execution, free shell, and wake approval.

## Trusted Device Rules

A trusted device record contains:

- `device_id`
- `display_name`
- `channel_type`
- hashed public identifier
- hashed fingerprint material
- trust status
- created/last-seen/revoked timestamps
- revocation reason
- approval capabilities and exact scope
- redacted metadata

Rules:

- trust is created only by backend-controlled bootstrap, exact local controller
  verification, exact terminal challenge, or consumed local pairing challenge;
- memory/user preference cannot mark a device trusted;
- deserialization/import is preview-only and cannot create trust, approval,
  execution or Hermes capability;
- revoked devices stay revoked across restart;
- secrets/tokens/password/audio/transcript/raw metadata keys are redacted.

## Local Pairing Rules

Local pairing creates a one-time challenge with:

- `challenge_id`
- nonce
- exact `challenge_phrase`
- exact scope
- public identifier hash
- expiration
- failed-attempt counter
- lockout after repeated bad attempts
- audit metadata

Pairing cannot approve, cannot execute, cannot call Hermes, and cannot create an
approve-all-forever device. The created device is local-only and limited to the
scope/capabilities bound into the challenge.

## Voice Approval Rules

Accepted Spanish phrases for normal voice approval:

- `JARVIS, autorizo`
- `JARVIS, confirmo`
- `JARVIS, apruebo esta acción`

Deny/cancel phrases:

- `JARVIS, cancela`
- `JARVIS, deniega`

Wake-only phrases such as `JARVIS` or `hola JARVIS` are explicitly rejected.

For high risk or strong approval, the generic Spanish phrases are not enough.
The session issues an exact challenge such as `JARVIS, confirmo ABC123`; the
spoken transcript must match that challenge after normalization.

Voice approval never downgrades risk. It never bypasses PolicyEngine or
ApprovalGateway; it only calls the existing approval decision path after all
voice gates pass.

## Threat Model

Mitigations implemented in this phase:

- frontend claim spoofing: backend stores hashed persistent identifiers and does
  not trust arbitrary frontend device claims;
- replayed pairing: pairing challenges are one-time and nonce-bound;
- brute-force pairing: failed attempts are counted and locked out;
- stale pairing: challenges expire;
- revoked identity reuse: revoked devices remain revoked in SQLite;
- wake phrase abuse: wake phrase alone is not an approval;
- fuzzy voice approval: risky approvals require exact readback and exact
  challenge;
- transcript replay: consumed voice approvals are rejected;
- audit tampering: triple approval verifies the persistent audit hash chain;
- remote escalation: pairing and notifications explicitly set remote execution
  and remote approval to false.

Remaining risks:

- device fingerprinting is a v1 public identifier/hash contract, not a hardware
  attestation implementation;
- no native keychain/TPM/Secure Enclave binding yet;
- no OS-native tray permissions model yet;
- no real STT/VAD/wake runtime validation in this phase;
- SQLite file protection depends on the local filesystem/user account.

## External Research

Network research was available. These projects were inspected for patterns and
future integration fit:

- [pystray](https://github.com/moses-palmer/pystray), LGPL-3.0: useful tray
  pattern, rejected for this phase because native tray install/autostart was not
  safe to finish honestly.
- [Tauri](https://github.com/tauri-apps/tauri), Apache-2.0/MIT: future desktop
  shell/tray candidate, rejected for this Python/API macro-phase to avoid
  adding a new runtime surface.
- [openWakeWord](https://github.com/dscripka/openWakeWord), Apache-2.0: future
  wake detector candidate, rejected here because wake detection must not imply
  approval and real audio runtime is out of scope.
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp), MIT: future local STT
  candidate, rejected here because this phase only needs transcript fixtures.
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper), MIT: future STT
  candidate, rejected here for the same reason.
- [Piper](https://github.com/rhasspy/piper), MIT on the inspected repo, with
  development moved notice: future local TTS candidate, not adopted here.
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot),
  GPL-3.0/LGPL-3.0 files visible: rejected for this phase because Telegram must
  remain notification/readiness only and the licensing/runtime surface needs a
  separate decision.

No external library code or dependency was adopted in PR #170.

## Manual Validation

1. Start the API locally with the normal project command.
2. Confirm no unsafe route exists: `/execute` and `/jarvis/execute` must be
   absent.
3. Open `GET /mark-3/phase-5/status` and verify local-only, no-autostart,
   kill-switch, trusted identity, pairing and voice gates.
4. Run `python scripts/local/jarvis-local-controller-dev.py status`.
5. Run opt-in/start-request/kill-switch commands from the script and confirm
   they record intent without starting hidden background behavior.
6. Create a local pairing challenge, verify it once, then verify it again and
   confirm the replay is rejected.
7. Trigger three bad pairing attempts and confirm rate limiting.
8. Create a normal pending approval, start a voice session with the paired
   device, verify `JARVIS` alone is rejected, then verify `JARVIS, autorizo`
   approves the pending approval.
9. Create a strong approval, confirm generic approval is denied, then confirm
   the exact spoken challenge is accepted.
10. Revoke the paired device and confirm voice approval start is blocked.
11. Verify terminal and local controller, request triple approval, then revoke a
    channel and confirm persistent identity readiness blocks completion.
12. Open `/jarvis` and confirm Phase 5 appears as presence/cockpit state, not as
    direct Hermes controls.

## Next Macro-Phase

Recommended PR #171:

- native tray implementation with explicit opt-in installer/uninstaller;
- OS-native local notifications;
- stronger local device attestation/key storage;
- real local voice runtime integration using a selected STT/VAD/TTS stack;
- signed pairing payloads or key exchange;
- browser/device enrollment UX;
- manual pilot checklist on David's machine with restart/revoke/audio privacy
  validation.
