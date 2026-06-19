from dataclasses import replace
import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi import HTTPException

from jarvis.api.app import (
    Mark3ExecutionPreviewRequest,
    Mark3ExecutionRequestApprovalRequest,
    Mark3LocalPairingChallengeRequest,
    Mark3LocalPairingVerifyRequest,
    Mark3Phase6VoiceSessionCancelRequest,
    Mark3Phase6VoiceSessionStartRequest,
    Mark3Phase6VoiceSessionTransitionRequest,
    Mark3SensorRuntimeOptInRequest,
    Mark3SensorRuntimeStartRequest,
    Mark3SensorRuntimeStopRequest,
    Mark3VoiceApprovalDecisionRequest,
    Mark3VoiceApprovalStartRequest,
    Mark3WakeRuntimeFixtureRequest,
    Mark3WakeRuntimeOptInRequest,
    create_app,
)
from jarvis.dashboard_event_stream import build_jarvis_event_snapshot
from jarvis.memory_brain_v2 import MemoryBrainV2Store
from jarvis.memory_brain_v3 import MemoryBrainV3
from jarvis.persistent_audit import PersistentAuditLedger
from jarvis.phase_2_local_assistant_runtime import ACTION_CATALOG
from jarvis.phase_6_voice_wake_sensor_runtime import (
    SensorRuntimeOptIn,
    VoiceProviderConfig,
    VoiceProviderRegistry,
    VoiceSessionManagerV2,
    WakeRuntimeOptIn,
)


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


class FakeHermesReadAdapter:
    def __init__(self, calls):
        self.calls = calls
        self.interruptions = []

    def run(self, message, **kwargs):
        self.calls.append({"message": message, "kwargs": kwargs})
        return {"success": True, "completed": True}

    def interrupt(self, reason):
        self.interruptions.append(reason)
        return True


def _make_app(tmp_path, monkeypatch):
    state_dir = tmp_path / "state"
    monkeypatch.setenv("JARVIS_LOCAL_STATE_DIR", str(state_dir))
    ledger = PersistentAuditLedger(base_dir=state_dir)
    memory = MemoryBrainV2Store(base_dir=state_dir, audit_ledger=ledger)
    calls = []
    app = create_app(
        adapter_factory=lambda: pytest.fail("legacy Hermes adapter must not be called"),
        hermes_runtime_adapter_factory=lambda _guard: FakeHermesReadAdapter(calls),
        persistent_audit_ledger=ledger,
        memory_brain_v2=memory,
    )
    return app, ledger, calls


def _route(app, path, method="GET"):
    return next(route for route in app.routes if route.path == path and method in getattr(route, "methods", set()))


def _preview(app, **payload):
    return _route(app, "/mark-3/execution/preview", "POST").endpoint(Mark3ExecutionPreviewRequest(**payload))


def _request_approval(app, preview_id):
    return _route(app, "/mark-3/execution/request-approval", "POST").endpoint(
        Mark3ExecutionRequestApprovalRequest(preview_id=preview_id, actor="David")
    )


def _pair_voice_device(app, *, public_identifier="phase6-phone", scope=None):
    scope = scope or ["voice_approval", "normal", "strong"]
    challenge = _route(app, "/mark-3/local-pairing/challenge", "POST").endpoint(
        Mark3LocalPairingChallengeRequest(
            display_name="David phone",
            public_identifier=public_identifier,
            channel="local_voice_device",
            scope=scope,
        )
    )
    return _route(app, "/mark-3/local-pairing/verify", "POST").endpoint(
        Mark3LocalPairingVerifyRequest(
            challenge_id=challenge["challenge_id"],
            nonce=challenge["nonce"],
            response_phrase=challenge["challenge_phrase"],
            public_identifier=public_identifier,
            display_name="David phone",
            scope=scope,
        )
    )


def _event_types(ledger):
    return {entry["event_type"] for entry in ledger.list_entries(limit=500)}


def test_voice_provider_registry_reports_honest_status_without_fake_readiness():
    status = VoiceProviderRegistry(VoiceProviderConfig()).status()

    assert status["schema_version"] == "jarvis.voice_provider_registry.v1"
    assert status["diagnostics"]["no_fake_provider_success"] is True
    assert status["diagnostics"]["ready_provider_count"] == 0
    assert status["state"]["model_download_performed"] is False
    assert status["state"]["provider_install_performed"] is False
    assert status["state"]["external_api_calls_enabled"] is False

    providers = status["providers"]
    assert providers["browser_speech_recognition"]["status"] == "client_side_unknown"
    assert providers["browser_speech_synthesis"]["browser_client_side"] is True
    for provider in providers.values():
        assert provider["ready"] is False
        assert provider["network_required"] is False
        assert provider["external_provider"] is False
        assert provider["raw_audio_persistence"] is False
        assert provider["hidden_sensor_activation"] is False
        assert provider["model_download_performed"] is False


def test_voice_session_manager_v2_lifecycle_redacts_transcripts_and_stops():
    manager = VoiceSessionManagerV2(default_timeout_seconds=30)

    started = manager.start_manual(device_id="device-local", source="push_to_talk")
    session_id = started["session"]["session_id"]
    assert started["session"]["state"] == "listening"
    assert started["session"]["raw_audio_stored"] is False

    transcribing = manager.transition(
        session_id,
        "transcribing",
        transcript="JARVIS mi token sk-test no debe aparecer",
        reason="fixture transcript",
    )
    summary = transcribing["session"]["transcript_summary"]
    assert summary["raw_text_included"] is False
    assert summary["contains_sensitive_marker"] is True
    serialized = json.dumps(transcribing, sort_keys=True).lower()
    assert "sk-test" not in serialized

    awaiting = manager.await_approval(
        session_id,
        approval_id="approval-1",
        challenge_id="challenge-1",
        strong_challenge_required=True,
    )
    assert awaiting["session"]["state"] == "awaiting_spoken_challenge"
    assert manager.is_active(session_id) is True

    cancelled = manager.cancel(session_id, reason="operator cancel")
    assert cancelled["session"]["active"] is False
    assert cancelled["session"]["state"] == "cancelled"
    assert manager.stop_global()["stopped_session_ids"] == []


def test_wake_runtime_opt_in_fixture_starts_session_but_never_approves():
    manager = VoiceSessionManagerV2()
    wake = WakeRuntimeOptIn(session_manager=manager)

    disabled = wake.handle_fixture_transcript(transcript="hola jarvis autorizo", confidence=0.99)
    assert disabled["session_started"] is False
    assert disabled["approval_granted"] is False

    wake.configure(enabled=True, phrase="hola jarvis")
    started = wake.handle_fixture_transcript(transcript="Hola Jarvis, revisa estado", confidence=0.99)
    assert started["wake_phrase_detected"] is True
    assert started["session_started"] is True
    assert started["approval_granted"] is False
    assert started["wake_phrase_can_approve"] is False
    assert manager.status()["state"]["active_session_count"] == 1


def test_sensor_runtime_defaults_off_requires_opt_in_and_stop_cancel():
    runtime = SensorRuntimeOptIn()
    status = runtime.status()

    assert status["state"]["defaults_off"] is True
    assert status["state"]["recording_active"] is False
    for sensor in status["sensors"].values():
        assert sensor["opted_in"] is False
        assert sensor["active"] is False

    with pytest.raises(ValueError, match="opt-in"):
        runtime.start(sensor_type="microphone")

    opted = runtime.set_opt_in(sensor_type="microphone", enabled=True, reason="manual test")
    assert opted["sensor"]["opted_in"] is True
    started = runtime.start(sensor_type="microphone", reason="manual test")
    assert started["sensor"]["active"] is True
    assert started["sensor"]["visible_indicator"] is True
    stopped = runtime.stop(sensor_type="all", reason="stop test")
    assert "microphone" in stopped["stopped_sensor_types"]
    assert stopped["status"]["state"]["active_sensor_count"] == 0


def test_memory_brain_v3_compaction_and_influence_never_grant_permission(tmp_path):
    store = MemoryBrainV2Store(base_dir=tmp_path / ".jarvis")
    memory = store.propose_project(
        project="JARVIS Phase 6",
        summary="voice wake memory sensor runtime pilot",
        provenance={"source": "test", "evidence_state": "provided"},
        reason_to_remember="Track Phase 6 pilot scope.",
        influence_summary="Explains dashboard phase status.",
    )
    store.review_memory(memory["memory_id"])
    store.approve_memory(memory["memory_id"])
    store.activate_memory(memory["memory_id"], reason="Use as explanatory context only.")

    v3 = MemoryBrainV3(store)
    status = v3.status()
    compaction = v3.compaction_preview()
    influence = v3.influence_explanation(memory["memory_id"])

    assert status["schema_version"] == "jarvis.memory_brain_v3.v1"
    assert status["state"]["compaction_preview_available"] is True
    assert compaction["status"] == "preview_only_not_applied"
    assert compaction["rules"]["permission_effect"] == "none"
    assert influence["permission_effect"]["grants_permission"] is False
    assert influence["permission_effect"]["can_dispatch_hermes"] is False


def test_phase_6_api_dashboard_events_and_frontend_contract(tmp_path, monkeypatch):
    app, _ledger, calls = _make_app(tmp_path, monkeypatch)
    routes = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}
    for path in (
        "/mark-3/phase-6/status",
        "/mark-3/voice-providers/status",
        "/mark-3/voice-session-v2/status",
        "/mark-3/wake-runtime/status",
        "/mark-3/sensor-runtime/status",
        "/mark-3/memory-brain-v3/status",
    ):
        assert (path, "GET") in routes

    session = _route(app, "/mark-3/voice-session-v2/start", "POST").endpoint(
        Mark3Phase6VoiceSessionStartRequest(source="push_to_talk")
    )
    session_id = session["session"]["session_id"]
    transitioned = _route(app, "/mark-3/voice-session-v2/transition", "POST").endpoint(
        Mark3Phase6VoiceSessionTransitionRequest(session_id=session_id, state="thinking", transcript="hola")
    )
    assert transitioned["session"]["state"] == "thinking"
    cancelled = _route(app, "/mark-3/voice-session-v2/cancel", "POST").endpoint(
        Mark3Phase6VoiceSessionCancelRequest(session_id=session_id)
    )
    assert cancelled["session"]["state"] == "cancelled"

    wake_opted = _route(app, "/mark-3/wake-runtime/opt-in", "POST").endpoint(Mark3WakeRuntimeOptInRequest(enabled=True))
    assert wake_opted["status"]["state"]["enabled"] is True
    wake = _route(app, "/mark-3/wake-runtime/fixture", "POST").endpoint(
        Mark3WakeRuntimeFixtureRequest(transcript="Hola Jarvis, abre sesion", confidence=0.99)
    )
    assert wake["session_started"] is True
    assert wake["approval_granted"] is False

    sensor_opted = _route(app, "/mark-3/sensor-runtime/opt-in", "POST").endpoint(
        Mark3SensorRuntimeOptInRequest(sensor_type="microphone", enabled=True)
    )
    assert sensor_opted["sensor"]["opted_in"] is True
    sensor_started = _route(app, "/mark-3/sensor-runtime/start", "POST").endpoint(
        Mark3SensorRuntimeStartRequest(sensor_type="microphone")
    )
    assert sensor_started["sensor"]["active"] is True
    stopped = _route(app, "/mark-3/sensor-runtime/stop", "POST").endpoint(Mark3SensorRuntimeStopRequest())
    assert stopped["status"]["state"]["active_sensor_count"] == 0

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    assert dashboard["phase_6_status"]["source_endpoint"] == "/mark-3/phase-6/status"
    assert dashboard["voice_provider_registry"]["diagnostics"]["no_fake_provider_success"] is True
    assert dashboard["voice_session_v2"]["privacy"]["raw_audio_stored"] is False
    assert dashboard["wake_runtime"]["rules"]["wake_phrase_can_approve"] is False
    assert dashboard["sensor_runtime"]["safety"]["no_hidden_microphone"] is True
    assert dashboard["memory_brain_v3"]["safety"]["memory_never_grants_permission"] is True
    assert dashboard["memory_brain"]["compaction"]["status"] == "contract_only"
    assert dashboard["memory_brain"]["phase_6_compaction_preview"]["status"] == "preview_only_not_applied"
    assert dashboard["memory_brain"]["phase_6_compaction_preview"]["permission_effect"] == "none"
    assert dashboard["memory_brain_v3"]["compaction"]["status"] == "preview_only_not_applied"
    assert dashboard["memory_brain_v3"]["compaction"]["risk_downgrade_allowed"] is False
    assert dashboard["memory_brain_v3_compaction"]["status"] == "preview_only_not_applied"
    assert dashboard["memory_brain"]["forget_delete"]["status"] == "future_gated"
    assert dashboard["memory_brain"]["phase_6_forget_delete"]["status"] == "audited_store"
    assert dashboard["memory_brain"]["phase_6_forget_delete"]["permission_effect"] == "none"

    snapshot = build_jarvis_event_snapshot(dashboard_status=dashboard, generated_at="2026-06-19T00:00:00+00:00")
    event_types = {event["event_type"] for event in snapshot["events"]}
    assert {
        "phase_6_state",
        "voice_provider_state",
        "wake_runtime_state",
        "sensor_runtime_state",
        "memory_brain_v3_state",
        "spoken_approval_state",
    } <= event_types
    serialized = json.dumps(snapshot, sort_keys=True).lower()
    for forbidden in ("raw_audio_bytes", "audio_bytes", "frame_bytes", "image_bytes", "video_bytes", "password", "api_key", "bearer "):
        assert forbidden not in serialized

    frontend = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            WEB / "src/lib/api.ts",
            WEB / "src/components/jarvis/JarvisPresenceShell.tsx",
            WEB / "src/components/jarvis/JarvisSideRail.tsx",
        )
    )
    assert "phase_6_status" in frontend
    assert "jarvis-phase-6-runtime" in frontend
    assert "HermesRuntimeAdapter" not in frontend
    assert 'fetchJSON("/execute"' not in frontend
    assert calls == []


def test_spoken_approval_v2_requires_active_session_and_accepts_bounded_spanish_phrases(tmp_path, monkeypatch):
    app, ledger, calls = _make_app(tmp_path, monkeypatch)
    paired = _pair_voice_device(app)
    device_id = paired["device"]["device_id"]
    preview = _preview(app, intent="Read safe file", action_key="repo.file.read_safe", inputs={"path": "README.md"})
    envelope = _request_approval(app, preview["preview_id"])

    with pytest.raises(HTTPException) as no_session:
        _route(app, "/mark-3/voice-approval/start", "POST").endpoint(
            Mark3VoiceApprovalStartRequest(
                approval_id=envelope["approval_id"],
                device_id=device_id,
                readback_text=envelope["readback_text"],
                voice_session_active=False,
            )
        )
    assert no_session.value.status_code == 400

    with pytest.raises(HTTPException) as wake_only:
        _route(app, "/mark-3/voice-approval/start", "POST").endpoint(
            Mark3VoiceApprovalStartRequest(
                approval_id=envelope["approval_id"],
                device_id=device_id,
                readback_text=envelope["readback_text"],
                opened_by_wake_only=True,
            )
        )
    assert wake_only.value.status_code == 400

    with pytest.raises(HTTPException) as inactive_session:
        _route(app, "/mark-3/voice-approval/start", "POST").endpoint(
            Mark3VoiceApprovalStartRequest(
                approval_id=envelope["approval_id"],
                device_id=device_id,
                voice_session_id="voice-session-not-active",
                readback_text=envelope["readback_text"],
            )
        )
    assert inactive_session.value.status_code == 400

    voice_session = _route(app, "/mark-3/voice-session-v2/start", "POST").endpoint(
        Mark3Phase6VoiceSessionStartRequest(device_id=device_id, source="push_to_talk")
    )
    voice_session_id = voice_session["session"]["session_id"]
    session = _route(app, "/mark-3/voice-approval/start", "POST").endpoint(
        Mark3VoiceApprovalStartRequest(
            approval_id=envelope["approval_id"],
            device_id=device_id,
            voice_session_id=voice_session_id,
            readback_text=envelope["readback_text"],
            cost_summary="max 50 euros",
            cost_limit_eur=50,
            duration_seconds=120,
        )
    )
    accepted = _route(app, "/mark-3/voice-approval/decision", "POST").endpoint(
        Mark3VoiceApprovalDecisionRequest(
            session_id=session["session_id"],
            device_id=device_id,
            transcript="JARVIS, autorizo con limite de 25 euros",
            readback_text=envelope["readback_text"],
            action_id=envelope["action_id"],
            cost_summary="max 50 euros",
        )
    )
    assert accepted["decision"] == "accepted"
    assert accepted["transcript_stored"] is False

    replay = _route(app, "/mark-3/voice-approval/decision", "POST").endpoint(
        Mark3VoiceApprovalDecisionRequest(
            session_id=session["session_id"],
            device_id=device_id,
            transcript="JARVIS, autorizo con limite de 25 euros",
            readback_text=envelope["readback_text"],
            cost_summary="max 50 euros",
        )
    )
    assert replay["decision"] == "replay_rejected"
    assert calls == []
    assert {"voice_approval_session_started", "voice_approval_accepted", "voice_approval_replay_rejected"} <= _event_types(ledger)


def test_spoken_approval_v2_strong_challenge_still_required(tmp_path, monkeypatch):
    app, _ledger, calls = _make_app(tmp_path, monkeypatch)
    high_contract = replace(ACTION_CATALOG["jarvis.phase.status"], risk_level="high", approval_required="strong")
    monkeypatch.setitem(ACTION_CATALOG, "jarvis.phase.status", high_contract)
    paired = _pair_voice_device(app, public_identifier="phase6-strong-phone")
    device_id = paired["device"]["device_id"]
    preview = _preview(app, intent="Strong phase status", action_key="jarvis.phase.status")
    envelope = _request_approval(app, preview["preview_id"])
    voice_session = _route(app, "/mark-3/voice-session-v2/start", "POST").endpoint(
        Mark3Phase6VoiceSessionStartRequest(device_id=device_id, source="push_to_talk")
    )
    session = _route(app, "/mark-3/voice-approval/start", "POST").endpoint(
        Mark3VoiceApprovalStartRequest(
            approval_id=envelope["approval_id"],
            device_id=device_id,
            voice_session_id=voice_session["session"]["session_id"],
            readback_text=envelope["readback_text"],
            cost_summary="unknown; operator review required",
        )
    )
    assert session["expected_challenge"].startswith("JARVIS, confirmo ")

    denied = _route(app, "/mark-3/voice-approval/decision", "POST").endpoint(
        Mark3VoiceApprovalDecisionRequest(
            session_id=session["session_id"],
            device_id=device_id,
            transcript="JARVIS, autorizo durante 1 minutos",
            readback_text=envelope["readback_text"],
            cost_summary="unknown; operator review required",
        )
    )
    assert denied["decision"] == "denied"
    assert denied["reason"] == "spoken_confirmation_phrase_mismatch"

    accepted = _route(app, "/mark-3/voice-approval/decision", "POST").endpoint(
        Mark3VoiceApprovalDecisionRequest(
            session_id=session["session_id"],
            device_id=device_id,
            transcript=session["expected_challenge"],
            readback_text=envelope["readback_text"],
            cost_summary="unknown; operator review required",
        )
    )
    assert accepted["decision"] == "accepted"
    assert calls == []
