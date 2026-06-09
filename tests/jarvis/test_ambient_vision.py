import os

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.ambient_vision.companion import (
    AmbientVisionPrivacyPolicy,
    AmbientVisionSessionPreview,
    AmbientVisionStatus,
    AmbientVisionStopControl,
)
from jarvis.api.app import AmbientVisionSessionPreviewRequest, InMemoryTaskStore, create_app
from jarvis.mission_control import MissionControl
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Ambient Vision")


class DirectResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class DirectClient:
    def __init__(self, app):
        self.app = app

    def get(self, path):
        endpoint = _endpoint(self.app, path, "GET")
        return DirectResponse(200, endpoint())

    def post(self, path, json=None):
        endpoint = _endpoint(self.app, path, "POST")
        return DirectResponse(200, endpoint(AmbientVisionSessionPreviewRequest(**(json or {}))))


def _app():
    return create_app(adapter_factory=FailAdapter)


def _client():
    return DirectClient(_app())


def _endpoint(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def test_ambient_vision_status_endpoint_is_safe_by_default():
    response = _client().get("/ambient-vision/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload == {
        "prepare_only": True,
        "vision_available": False,
        "camera_connected": False,
        "camera_active": False,
        "recording_enabled": False,
        "streaming_enabled": False,
        "continuous_watch_enabled": False,
        "face_analysis_enabled": False,
        "person_analysis_enabled": False,
        "external_vision_calls_enabled": False,
        "image_storage_enabled": False,
        "execution_enabled": False,
        "hard_stop_available": True,
        "privacy_redaction_enabled": True,
        "requires_approval_for_sensitive_capture": True,
    }


def test_ambient_vision_privacy_policy_endpoint_is_safe_by_default():
    response = _client().get("/ambient-vision/privacy-policy")
    payload = response.json()

    assert response.status_code == 200
    assert payload["prepare_only"] is True
    assert payload["camera_requires_explicit_start"] is True
    assert payload["visible_indicator_required"] is True
    assert payload["no_recording_by_default"] is True
    assert payload["no_streaming_by_default"] is True
    assert payload["no_face_analysis_by_default"] is True
    assert payload["no_person_analysis_by_default"] is True
    assert payload["no_retention_by_default"] is True
    assert payload["no_external_uploads"] is True
    assert "no mires" in payload["hard_stop_phrase"].lower()
    assert payload["sensitive_capture_requires_strong_approval"] is True


def test_ambient_vision_session_preview_is_prepare_only():
    response = _client().post(
        "/ambient-vision/session-preview",
        json={
            "camera_requested": True,
            "recording_requested": True,
            "streaming_requested": True,
            "continuous_watch_requested": True,
            "face_analysis_requested": True,
            "person_analysis_requested": True,
            "external_vision_requested": True,
            "image_storage_requested": True,
            "sensitive_capture_requested": True,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["prepare_only"] is True
    assert payload["session_requested"] is True
    assert payload["would_start_camera"] is False
    assert payload["would_record"] is False
    assert payload["would_stream"] is False
    assert payload["would_store_images"] is False
    assert payload["would_call_external_vision"] is False
    assert payload["would_analyze_people"] is False
    assert payload["would_execute"] is False
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["privacy_boundary_triggered"] is True


def test_ambient_vision_empty_request_does_not_report_requested_session():
    preview = AmbientVisionSessionPreview.from_request({}).to_dict()

    assert preview["session_requested"] is False
    assert preview["approval_required"] is False
    assert preview["strong_approval_required"] is False
    assert preview["privacy_boundary_triggered"] is False


def test_ambient_vision_empty_api_request_does_not_report_requested_session():
    response = _client().post("/ambient-vision/session-preview", json={})

    assert response.status_code == 200
    assert response.json()["session_requested"] is False


@pytest.mark.parametrize(
    "request_data",
    [
        {"session_requested": True},
        {"camera_requested": True},
        {"recording_requested": True},
        {"streaming_requested": True},
        {"face_analysis_requested": True},
        {"person_analysis_requested": True},
        {"image_storage_requested": True},
        {"external_vision_requested": True},
    ],
)
def test_ambient_vision_real_requested_capability_reports_requested_session(request_data):
    preview = AmbientVisionSessionPreview.from_request(request_data).to_dict()

    assert preview["session_requested"] is True


def test_ambient_vision_from_dict_preserves_requested_session_without_enabling_actions():
    preview = AmbientVisionSessionPreview.from_dict(
        {
            "session_requested": True,
            "would_start_camera": True,
            "would_record": True,
            "would_stream": True,
            "would_store_images": True,
            "would_call_external_vision": True,
            "would_analyze_people": True,
            "would_execute": True,
        }
    ).to_dict()

    assert preview["session_requested"] is True
    for key in (
        "would_start_camera",
        "would_record",
        "would_stream",
        "would_store_images",
        "would_call_external_vision",
        "would_analyze_people",
        "would_execute",
    ):
        assert preview[key] is False


def test_ambient_vision_session_preview_has_no_side_effects(monkeypatch):
    app = _app()

    def fail(*args, **kwargs):
        raise AssertionError("Ambient Vision preview attempted a forbidden side effect")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail, raising=False)
    monkeypatch.setattr(MissionControl, "create_mission", fail)
    monkeypatch.setattr(InMemoryTaskStore, "create", fail)
    monkeypatch.setattr(os, "getenv", fail)
    monkeypatch.setattr(os.environ, "get", fail)
    monkeypatch.setattr("builtins.open", fail)

    endpoint = _endpoint(app, "/ambient-vision/session-preview", "POST")
    payload = endpoint(
        AmbientVisionSessionPreviewRequest(
            camera_requested=True,
            recording_requested=True,
            streaming_requested=True,
            external_vision_requested=True,
        )
    )

    assert payload["would_start_camera"] is False
    assert payload["would_record"] is False
    assert payload["would_stream"] is False
    assert payload["would_store_images"] is False
    assert payload["would_call_external_vision"] is False
    assert payload["would_execute"] is False


def test_ambient_vision_empty_session_preview_has_no_side_effects(monkeypatch):
    app = _app()

    def fail(*args, **kwargs):
        raise AssertionError("Empty Ambient Vision preview attempted a forbidden side effect")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail, raising=False)
    monkeypatch.setattr(MissionControl, "create_mission", fail)
    monkeypatch.setattr(InMemoryTaskStore, "create", fail)
    monkeypatch.setattr(os, "getenv", fail)
    monkeypatch.setattr(os.environ, "get", fail)
    monkeypatch.setattr("builtins.open", fail)

    endpoint = _endpoint(app, "/ambient-vision/session-preview", "POST")
    payload = endpoint(AmbientVisionSessionPreviewRequest())

    assert payload["session_requested"] is False
    assert payload["would_start_camera"] is False
    assert payload["would_record"] is False
    assert payload["would_stream"] is False
    assert payload["would_store_images"] is False
    assert payload["would_call_external_vision"] is False
    assert payload["would_analyze_people"] is False
    assert payload["would_execute"] is False


def test_ambient_vision_stop_control_endpoint_is_prepare_only():
    response = _client().get("/ambient-vision/stop-control")
    payload = response.json()

    assert response.status_code == 200
    assert payload == {
        "prepare_only": True,
        "hard_stop_available": True,
        "hard_stop_phrase": "no mires",
        "camera_stop_would_execute": False,
        "active_session_required": False,
        "execution_enabled": False,
        "audit_required": True,
    }


@pytest.mark.parametrize(
    "path",
    [
        "/ambient-vision/start",
        "/ambient-vision/stop",
        "/ambient-vision/record",
        "/ambient-vision/stream",
        "/ambient-vision/analyze-face",
        "/ambient-vision/analyze-person",
        "/ambient-vision/upload",
    ],
)
def test_ambient_vision_dangerous_routes_do_not_exist(path):
    routes = {(route.path, method) for route in _app().routes for method in route.methods}

    assert (path, "POST") not in routes
    assert (path, "GET") not in routes


def test_command_center_and_operator_console_expose_prepare_only_ambient_vision():
    client = _client()
    command_center = client.get("/command-center").json()
    operator_console = client.get("/operator/console/snapshot").json()

    controls = command_center["voice_camera_controls"]
    assert command_center["prepare_only"] is True
    assert command_center["metadata"]["ambient_vision"] == "prepare_only"
    assert controls["can_start_camera"] is False
    assert controls["can_record"] is False
    assert controls["ambient_vision_status"]["prepare_only"] is True
    assert controls["ambient_vision_status"]["camera_active"] is False
    assert controls["ambient_vision_privacy_policy"]["visible_indicator_required"] is True
    assert controls["ambient_vision_stop_control"]["hard_stop_available"] is True

    assert operator_console["prepare_only"] is True
    assert operator_console["capability_matrix"]["read_ambient_vision_status"] is True
    assert operator_console["capability_matrix"]["use_camera"] is False
    assert operator_console["ambient_vision_status"]["camera_active"] is False
    assert operator_console["ambient_vision_privacy_policy"]["no_external_uploads"] is True
    assert operator_console["ambient_vision_stop_control"]["camera_stop_would_execute"] is False


def test_ambient_vision_deserialization_cannot_enable_forbidden_capabilities():
    hostile = {
        "prepare_only": False,
        "vision_available": True,
        "camera_connected": True,
        "camera_active": True,
        "recording_enabled": True,
        "streaming_enabled": True,
        "continuous_watch_enabled": True,
        "face_analysis_enabled": True,
        "person_analysis_enabled": True,
        "external_vision_calls_enabled": True,
        "image_storage_enabled": True,
        "execution_enabled": True,
        "hard_stop_available": False,
        "privacy_redaction_enabled": False,
        "requires_approval_for_sensitive_capture": False,
        "would_start_camera": True,
        "would_record": True,
        "would_stream": True,
        "would_store_images": True,
        "would_call_external_vision": True,
        "would_analyze_people": True,
        "would_execute": True,
        "camera_stop_would_execute": True,
    }

    status = AmbientVisionStatus.from_dict(hostile).to_dict()
    policy = AmbientVisionPrivacyPolicy.from_dict(hostile).to_dict()
    preview = AmbientVisionSessionPreview.from_dict(hostile).to_dict()
    stop = AmbientVisionStopControl.from_dict(hostile).to_dict()

    assert status["prepare_only"] is True
    for key in (
        "vision_available",
        "camera_connected",
        "camera_active",
        "recording_enabled",
        "streaming_enabled",
        "continuous_watch_enabled",
        "face_analysis_enabled",
        "person_analysis_enabled",
        "external_vision_calls_enabled",
        "image_storage_enabled",
        "execution_enabled",
    ):
        assert status[key] is False
    assert policy["no_external_uploads"] is True
    assert policy["visible_indicator_required"] is True
    for key in (
        "would_start_camera",
        "would_record",
        "would_stream",
        "would_store_images",
        "would_call_external_vision",
        "would_analyze_people",
        "would_execute",
    ):
        assert preview[key] is False
    assert preview["session_requested"] is False
    assert stop["camera_stop_would_execute"] is False
    assert stop["execution_enabled"] is False


def test_ambient_vision_direct_construction_cannot_enable_forbidden_capabilities():
    status = AmbientVisionStatus(
        prepare_only=False,
        camera_connected=True,
        camera_active=True,
        recording_enabled=True,
        streaming_enabled=True,
        continuous_watch_enabled=True,
        face_analysis_enabled=True,
        person_analysis_enabled=True,
        external_vision_calls_enabled=True,
        image_storage_enabled=True,
        execution_enabled=True,
        hard_stop_available=False,
        privacy_redaction_enabled=False,
        requires_approval_for_sensitive_capture=False,
    )
    policy = AmbientVisionPrivacyPolicy(
        visible_indicator_required=False,
        no_recording_by_default=False,
        no_external_uploads=False,
        hard_stop_phrase="disabled",
    )
    stop = AmbientVisionStopControl(
        hard_stop_available=False,
        hard_stop_phrase="disabled",
        camera_stop_would_execute=True,
        execution_enabled=True,
        audit_required=False,
    )

    assert status.camera_active is False
    assert status.recording_enabled is False
    assert status.streaming_enabled is False
    assert status.external_vision_calls_enabled is False
    assert status.execution_enabled is False
    assert status.hard_stop_available is True
    assert policy.visible_indicator_required is True
    assert policy.no_recording_by_default is True
    assert policy.no_external_uploads is True
    assert policy.hard_stop_phrase == "no mires"
    assert stop.hard_stop_available is True
    assert stop.camera_stop_would_execute is False
    assert stop.execution_enabled is False
    assert stop.audit_required is True
