import json

import pytest

from jarvis.api.app import create_app
from jarvis.dashboard_event_stream import ALLOWED_EVENT_TYPES, build_jarvis_event_snapshot, encode_sse_event


def _dashboard_route(app, path):
    for route in app.routes:
        if route.path == path:
            return route
    raise AssertionError(f"missing {path} route")


def test_jarvis_dashboard_event_snapshot_contains_required_read_only_events():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    status_route = _dashboard_route(app, "/mark-3/dashboard/status")
    status = status_route.endpoint()

    snapshot = build_jarvis_event_snapshot(dashboard_status=status, generated_at="2026-06-18T00:00:00+00:00")

    assert snapshot["schema_version"] == "jarvis.dashboard.events.v1"
    assert snapshot["snapshot_id"]
    assert snapshot["stream"]["read_only"] is True
    assert snapshot["stream"]["allowed_methods"] == ["GET"]
    assert snapshot["stream"]["schema_version"] == "jarvis.dashboard.events.v1"
    assert snapshot["stream"]["heartbeat_enabled"] is True
    assert snapshot["stream"]["disconnect_safe"] is True
    assert snapshot["heartbeat"]["event_type"] == "heartbeat"
    assert snapshot["heartbeat"]["schema_version"] == "jarvis.dashboard.events.v1"
    assert snapshot["heartbeat"]["event_id"]
    assert snapshot["stream"]["no_secrets"] is True
    assert snapshot["stream"]["no_raw_audio"] is True
    assert snapshot["stream"]["no_camera_frames"] is True
    event_types = {event["event_type"] for event in snapshot["events"]}
    for event_type in (
        "voice_state",
        "wake_state",
        "tts_state",
        "hermes_state",
        "approval_state",
        "mission_state",
        "camera_state",
        "recording_state",
        "memory_state",
        "risk_state",
        "execution_state",
        "audit_event",
        "sensor_ledger_state",
        "policy_state",
    ):
        assert event_type in event_types

    for event in snapshot["events"]:
        assert event["schema_version"] == "jarvis.dashboard.events.v1"
        assert event["event_id"]
        assert event["id"] == event["event_id"]
        assert event["created_at"] == "2026-06-18T00:00:00+00:00"
        assert event["event_type"] in ALLOWED_EVENT_TYPES
        assert event["source"]
        assert event["risk_level"]
        assert event["read_only"] is True
        assert event["can_execute"] is False
        assert event["stream_can_execute"] is False
        assert event["secret_free"] is True
        assert event["raw_audio_included"] is False
        assert event["camera_frames_included"] is False

    events = {event["event_type"]: event for event in snapshot["events"]}
    assert "running_sessions" in events["hermes_state"]["payload"]
    assert "session_count" in events["hermes_state"]["payload"]
    assert events["recording_state"]["source"] == "/jarvis/browser-audio-recorder"
    assert events["recording_state"]["payload"]["raw_audio_recording_enabled"] is True
    assert events["recording_state"]["payload"]["raw_audio_sent_to_backend"] is False
    assert events["camera_state"]["payload"]["video_recording_available"] == "browser_local_opt_in"
    assert events["camera_state"]["payload"]["video_recording_active"] is False
    assert events["camera_state"]["payload"]["video_recording_permission_requested"] is False
    assert events["camera_state"]["payload"]["video_recording_blob_ready"] is False
    assert events["camera_state"]["payload"]["video_download_available_after_stop"] is True
    assert events["camera_state"]["payload"]["video_delete_available_after_stop"] is True
    assert events["camera_state"]["payload"]["raw_video_sent_to_backend"] is False
    assert events["camera_state"]["payload"]["no_backend_upload"] is True
    assert events["memory_state"]["payload"]["visible_brain"] is True
    assert "outcome_count" in events["memory_state"]["payload"]
    assert events["doctor_state"]["source"] == "/mark-3/local-doctor/status"
    assert "ffmpeg_available" in events["doctor_state"]["payload"]
    assert "openwakeword_available" in events["doctor_state"]["payload"]
    assert events["sensor_ledger_state"]["payload"]["metadata_only"] is True
    assert events["sensor_ledger_state"]["payload"]["no_raw_audio"] is True
    assert events["sensor_ledger_state"]["payload"]["no_camera_frames"] is True
    assert events["policy_state"]["payload"]["jarvis_governs"] is True
    assert events["policy_state"]["payload"]["hermes_executes"] is True
    assert events["policy_state"]["payload"]["wake_phrase_never_approves"] is True


def test_jarvis_dashboard_event_routes_are_get_only_and_do_not_add_mutations():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    routes = {
        (route.path, method)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }

    assert ("/mark-3/dashboard/events", "GET") in routes
    assert ("/mark-3/dashboard/events/stream", "GET") in routes
    for route in (
        ("/mark-3/dashboard/events", "POST"),
        ("/mark-3/dashboard/events", "PUT"),
        ("/mark-3/dashboard/events", "DELETE"),
        ("/mark-3/dashboard/events/stream", "POST"),
        ("/mark-3/dashboard/events/stream", "PUT"),
        ("/mark-3/dashboard/events/stream", "DELETE"),
        ("/mark-3/dashboard/events/execute", "POST"),
        ("/mark-3/dashboard/events/approve", "POST"),
        ("/jarvis/events/execute", "POST"),
    ):
        assert route not in routes


def test_jarvis_dashboard_event_sse_encoder_is_json_and_read_only():
    payload = {
        "generated_at": "2026-06-18T00:00:00+00:00",
        "stream": {"read_only": True},
        "events": [],
    }

    encoded = encode_sse_event("jarvis_event_snapshot", payload)

    assert encoded.startswith("event: jarvis_event_snapshot\n")
    assert "\nid: " in encoded
    assert "\ndata: " in encoded
    assert encoded.endswith("\n\n")
    data_line = next(line for line in encoded.splitlines() if line.startswith("data: "))
    assert json.loads(data_line.removeprefix("data: ")) == payload


def test_jarvis_dashboard_event_snapshot_redacts_sensitive_payload_keys():
    snapshot = build_jarvis_event_snapshot(
        dashboard_status={
            "timeline": [{"event": "safe"}],
            "voice_core": {"state": {"current_state": "preview"}},
        },
        generated_at="2026-06-18T00:00:00+00:00",
    )

    for event in snapshot["events"]:
        serialized = json.dumps(event, sort_keys=True).lower()
        assert "audio_bytes" not in serialized
        assert "image_bytes" not in serialized
        assert "camera_frames_included\": true" not in serialized
        assert "raw_audio_included\": true" not in serialized
