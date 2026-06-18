import json

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import create_app
from jarvis.dashboard_event_stream import build_jarvis_event_snapshot


def _dashboard_payload():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    route = next(route for route in app.routes if route.path == "/mark-3/dashboard/status")
    return route.endpoint(), app


def test_dashboard_status_includes_conversational_brain_voice_session_and_wake_architecture():
    payload, app = _dashboard_payload()
    routes = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}

    assert ("/mark-3/conversational-brain/status", "GET") in routes
    assert ("/voice-runtime/session-status", "GET") in routes

    brain = payload["conversational_brain"]
    assert brain["schema_version"] == "jarvis.conversational_brain_bridge.v2"
    assert brain["state"]["mode"] == "local_deterministic_bridge"
    assert brain["state"]["llm_called"] is False
    assert brain["state"]["external_provider_called"] is False
    assert brain["state"]["memory_autosave_enabled"] is False
    assert brain["state"]["hermes_dispatch_allowed"] is False
    assert brain["sample_analysis"]["human_response"]
    assert brain["sample_analysis"]["intent_detected"]
    assert brain["sample_analysis"]["hermes_dispatch_allowed"] is False

    voice_session = payload["voice_session"]
    assert voice_session["schema_version"] == "jarvis.voice_session_manager.v1"
    assert voice_session["state"]["current_state"] == "idle"
    assert voice_session["state"]["wake_listening_state"] in {"wake_listening_available", "wake_listening_disabled"}
    assert voice_session["privacy"]["raw_audio_sent_to_backend"] is False
    assert voice_session["privacy"]["transcript_persistence"] is False
    assert voice_session["privacy"]["background_transcription"] is False
    assert voice_session["privacy"]["always_on_stt"] is False
    assert voice_session["privacy"]["microphone_auto_start"] is False
    assert voice_session["separation"]["hermes_execution"]["dispatch_allowed"] is False
    assert voice_session["approval_policy"]["wake_phrase_cannot_approve"] is True
    assert voice_session["approval_policy"]["wake_phrase_cannot_execute"] is True

    wake = payload["wake_architecture"]
    assert wake["provider_contract"] == "openWakeWord"
    assert wake["auto_start"] is False
    assert wake["activation_endpoint_enabled"] is False
    assert wake["ephemeral_buffer_contract"]["in_memory_only"] is True
    assert wake["ephemeral_buffer_contract"]["persisted"] is False
    assert wake["no_transcription_until_valid_activation"] is True
    assert wake["no_approval"] is True
    assert wake["no_execution"] is True


def test_dashboard_event_stream_includes_only_safe_brain_voice_session_metadata():
    payload, _ = _dashboard_payload()
    snapshot = build_jarvis_event_snapshot(dashboard_status=payload, generated_at="2026-06-18T00:00:00+00:00")
    events = {event["event_type"]: event for event in snapshot["events"]}

    assert "brain_state" in events
    assert "voice_session_state" in events
    assert events["brain_state"]["payload"]["llm_called"] is False
    assert events["brain_state"]["payload"]["external_provider_called"] is False
    assert events["brain_state"]["payload"]["hermes_dispatch_allowed"] is False
    assert events["voice_session_state"]["payload"]["raw_audio_sent_to_backend"] is False
    assert events["voice_session_state"]["payload"]["transcript_persistence"] is False
    assert events["voice_session_state"]["payload"]["always_on_stt"] is False
    assert events["voice_session_state"]["payload"]["microphone_auto_start"] is False
    assert events["voice_session_state"]["payload"]["hermes_dispatch_allowed"] is False

    serialized = json.dumps(snapshot, sort_keys=True).lower()
    forbidden_fragments = (
        "riff",
        "audio_bytes",
        "raw_audio_bytes",
        "frame_bytes",
        "image_bytes",
        "video_bytes",
        "password",
        "api_key",
        "private_key",
        "cookie",
        "bearer ",
        "shell_command",
        "command_to_execute",
        "execute_payload",
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized
    assert '"can_execute": true' not in serialized
    assert '"stream_can_execute": true' not in serialized
