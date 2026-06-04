import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import MobileIntentPreviewRequest, create_app
from jarvis.mobile.companion import (
    MobileCommandCenterSnapshot,
    MobileCompanionPermissionPolicy,
    MobileCompanionStatus,
    MobileIntentPreview,
)
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


class DummyAdapter:
    def __init__(self):
        self.calls = 0

    def run(self, message: str, **kwargs):
        self.calls += 1
        raise AssertionError("Hermes must not be called by Mobile Companion")


def _client():
    adapter = DummyAdapter()
    app = create_app(adapter_factory=lambda: adapter)
    return TestClient(app), adapter


def _route_endpoint(app, path):
    for route in app.routes:
        if route.path == path:
            return route.endpoint
    raise AssertionError(f"route not found: {path}")


def _expected_status():
    return {
        "prepare_only": True,
        "mobile_available": False,
        "native_app_connected": False,
        "push_enabled": False,
        "background_sync_enabled": False,
        "location_enabled": False,
        "contacts_enabled": False,
        "camera_enabled": False,
        "microphone_enabled": False,
        "execution_enabled": False,
        "approval_actions_enabled": False,
        "requires_approval_for_sensitive_actions": True,
    }


def _expected_permissions():
    return {
        "prepare_only": True,
        "can_read_command_center": True,
        "can_preview_intent": True,
        "can_execute": False,
        "can_approve": False,
        "can_reject": False,
        "can_use_location": False,
        "can_use_contacts": False,
        "can_use_camera": False,
        "can_use_microphone": False,
        "can_receive_push": False,
        "can_run_background": False,
    }


def _assert_preview_never_executes(payload):
    assert payload["prepare_only"] is True
    assert payload["would_execute"] is False
    assert payload["execution_enabled"] is False
    assert payload["approval_created"] is False
    assert payload["approval_gateway_called"] is False
    assert payload["hermes_called"] is False
    assert payload["mobile_action_allowed"] is False


def test_mobile_companion_status_endpoint_is_prepare_only():
    client, adapter = _client()

    response = client.get("/mobile/companion/status")

    assert response.status_code == 200
    assert response.json() == _expected_status()
    assert adapter.calls == 0


def test_mobile_companion_status_from_dict_forces_safe_placeholder():
    status = MobileCompanionStatus.from_dict(
        {
            "prepare_only": False,
            "mobile_available": True,
            "native_app_connected": True,
            "push_enabled": True,
            "background_sync_enabled": True,
            "location_enabled": True,
            "contacts_enabled": True,
            "camera_enabled": True,
            "microphone_enabled": True,
            "execution_enabled": True,
            "approval_actions_enabled": True,
            "requires_approval_for_sensitive_actions": False,
        }
    )

    assert status.to_dict() == _expected_status()


def test_mobile_companion_permissions_endpoint_returns_safe_policy():
    client, adapter = _client()

    response = client.get("/mobile/companion/permissions")

    assert response.status_code == 200
    assert response.json() == _expected_permissions()
    assert adapter.calls == 0


def test_mobile_companion_permission_policy_from_dict_forces_safe_policy():
    policy = MobileCompanionPermissionPolicy.from_dict(
        {
            "prepare_only": False,
            "can_execute": True,
            "can_approve": True,
            "can_reject": True,
            "can_use_location": True,
            "can_use_contacts": True,
            "can_use_camera": True,
            "can_use_microphone": True,
            "can_receive_push": True,
            "can_run_background": True,
        }
    )

    assert policy.to_dict() == _expected_permissions()


def test_mobile_command_center_endpoint_returns_mobile_safe_snapshot(monkeypatch):
    def fail_approval(*args, **kwargs):
        raise AssertionError("ApprovalGateway must not be called by Mobile Command Center")

    def fail_hermes(*args, **kwargs):
        raise AssertionError("HermesRuntimeAdapter must not be called by Mobile Command Center")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail_approval)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail_hermes, raising=False)

    client, adapter = _client()
    response = client.get("/mobile/command-center")
    payload = response.json()
    serialized = response.text.lower()

    assert response.status_code == 200
    assert payload["prepare_only"] is True
    assert payload["mobile_status"] == _expected_status()
    assert payload["permission_policy"] == _expected_permissions()
    assert payload["safety"]["execution_enabled"] is False
    assert payload["safety"]["approval_actions_enabled"] is False
    assert payload["safety"]["hermes_connected"] is False
    assert payload["safety"]["approval_gateway_called"] is False
    assert payload["capabilities"]["read_command_center"] is True
    assert payload["capabilities"]["preview_intent"] is True
    assert payload["capabilities"]["execute"] is False
    assert payload["capabilities"]["approve"] is False
    assert payload["capabilities"]["reject"] is False
    assert payload["capabilities"]["push"] is False
    assert payload["capabilities"]["background_sync"] is False
    assert payload["capabilities"]["location"] is False
    assert payload["capabilities"]["contacts"] is False
    assert payload["capabilities"]["camera"] is False
    assert payload["capabilities"]["microphone"] is False
    assert payload["metadata"]["prepare_only"] is True
    assert payload["metadata"]["mobile_available"] is False
    assert adapter.calls == 0
    for forbidden in (
        ".env",
        "api_key",
        "apikey",
        "secret",
        "token",
        "password",
        "credential",
        "authorization",
        "audio_path",
        "audio_bytes",
        "base_url",
        "prompt_text",
    ):
        assert forbidden not in serialized


def test_mobile_intent_preview_endpoint_returns_prepare_only_allowed_preview():
    client, adapter = _client()

    response = client.post("/mobile/intent/preview", json={"text": "crea una misión para investigar nichos"})
    payload = response.json()

    assert response.status_code == 200
    _assert_preview_never_executes(payload)
    assert payload["input_text"] == "crea una misión para investigar nichos"
    assert payload["intent"] == "create_mission"
    assert payload["policy_decision"] == "allowed"
    assert payload["sensitive_boundary_triggered"] is False
    assert adapter.calls == 0


def test_mobile_intent_preview_with_normal_text_never_executes():
    client, _ = _client()

    response = client.post("/mobile/intent/preview", json={"text": "hazme una landing para afiliados"})
    payload = response.json()

    assert response.status_code == 200
    _assert_preview_never_executes(payload)
    assert payload["intent"] == "create_asset"
    assert payload["policy_decision"] == "allowed"


@pytest.mark.parametrize(
    "text,forbidden",
    [
        ("lee mi .env", ".env"),
        ("usa api key abc123", "api key"),
        ("Authorization: Bearer token abc123", "bearer"),
        ("revisa mis credenciales para esta tarea", "credenciales"),
        ("revisa mi dni para esta tarea", "dni"),
        ("revisa datos del banco", "banco"),
        ("comprueba mi tarjeta", "tarjeta"),
    ],
)
def test_mobile_intent_preview_redacts_sensitive_text_and_requires_approval_or_denies(text, forbidden):
    client, _ = _client()

    response = client.post("/mobile/intent/preview", json={"text": text})
    payload = response.json()
    serialized = response.text.lower()

    assert response.status_code == 200
    _assert_preview_never_executes(payload)
    assert payload["input_text"] == "[redacted sensitive mobile input]"
    assert payload["sensitive_boundary_triggered"] is True
    assert payload["policy_decision"] in {"requires_approval", "denied"}
    assert payload["intent"] in {"requires_approval", "denied"}
    assert forbidden not in serialized
    assert "abc123" not in serialized


@pytest.mark.parametrize(
    "marker",
    [
        "api_key",
        "private_key",
        "access_key",
        "refresh_token",
        "client_secret",
        "api-key",
        "private-key",
        "bearer_token",
    ],
)
def test_mobile_intent_preview_redacts_separator_variant_credentials_without_side_effects(monkeypatch, marker):
    def fail_approval(*args, **kwargs):
        raise AssertionError("ApprovalGateway.create_request must not be called by Mobile Companion preview")

    def fail_hermes(*args, **kwargs):
        raise AssertionError("HermesRuntimeAdapter.run must not be called by Mobile Companion preview")

    def fail_create_mission(*args, **kwargs):
        raise AssertionError("MissionControl.create_mission must not be called by Mobile Companion preview")

    def fail_create_task(*args, **kwargs):
        raise AssertionError("InMemoryTaskStore.create must not be called by Mobile Companion preview")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail_approval)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail_hermes, raising=False)
    monkeypatch.setattr("jarvis.mission_control.MissionControl.create_mission", fail_create_mission)
    monkeypatch.setattr("jarvis.api.app.InMemoryTaskStore.create", fail_create_task)

    adapter = DummyAdapter()
    app = create_app(adapter_factory=lambda: adapter)
    endpoint = _route_endpoint(app, "/mobile/intent/preview")
    before_tasks = app.state.task_store.list()
    before_missions = app.state.mission_control.list_missions()

    payload = endpoint(MobileIntentPreviewRequest(text=f"revisa este {marker} abc123"))
    serialized_input = json.dumps(payload["input_text"]).lower()

    assert marker.lower() not in serialized_input
    assert "abc123" not in serialized_input
    assert payload["input_text"] == "[redacted sensitive mobile input]"
    assert payload["sensitive_boundary_triggered"] is True
    assert payload["policy_decision"] in {"requires_approval", "denied"}
    _assert_preview_never_executes(payload)
    assert app.state.task_store.list() == before_tasks == []
    assert app.state.mission_control.list_missions() == before_missions == []
    assert adapter.calls == 0


def test_mobile_intent_preview_has_no_side_effects_or_runtime_calls(monkeypatch):
    def fail_approval(*args, **kwargs):
        raise AssertionError("ApprovalGateway.create_request must not be called by Mobile Companion preview")

    def fail_hermes(*args, **kwargs):
        raise AssertionError("HermesRuntimeAdapter.run must not be called by Mobile Companion preview")

    def fail_create_mission(*args, **kwargs):
        raise AssertionError("MissionControl.create_mission must not be called by Mobile Companion preview")

    def fail_create_task(*args, **kwargs):
        raise AssertionError("InMemoryTaskStore.create must not be called by Mobile Companion preview")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail_approval)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail_hermes, raising=False)
    monkeypatch.setattr("jarvis.mission_control.MissionControl.create_mission", fail_create_mission)
    monkeypatch.setattr("jarvis.api.app.InMemoryTaskStore.create", fail_create_task)

    client, adapter = _client()
    before_tasks = client.get("/tasks").json()
    before_missions = client.get("/missions").json()

    response = client.post("/mobile/intent/preview", json={"text": "lee mi .env"})

    assert response.status_code == 200
    assert client.get("/tasks").json() == before_tasks == []
    assert client.get("/missions").json() == before_missions == []
    assert adapter.calls == 0


def test_mobile_intent_preview_does_not_open_env_file(monkeypatch):
    opened_paths = []
    original_open = open

    def tracking_open(path, *args, **kwargs):
        opened_paths.append(str(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", tracking_open)

    client, _ = _client()
    response = client.post("/mobile/intent/preview", json={"text": "lee mi .env"})

    assert response.status_code == 200
    assert not any(path.endswith(".env") or "/.env" in path for path in opened_paths)


@pytest.mark.parametrize(
    "path",
    [
        "/mobile/execute",
        "/mobile/approve",
        "/mobile/reject",
        "/mobile/push",
        "/mobile/location",
        "/mobile/background-sync",
        "/mobile/track",
    ],
)
def test_mobile_companion_has_no_dangerous_routes(path):
    client, _ = _client()

    response = client.post(path)

    assert response.status_code == 404
    assert path not in [route.path for route in client.app.routes]


def test_command_center_remains_prepare_only_with_mobile_capability_marker():
    client, adapter = _client()

    response = client.get("/command-center")
    payload = response.json()

    assert response.status_code == 200
    assert payload["prepare_only"] is True
    assert payload["execution_enabled"] is False
    assert payload["approval_enabled"] is False
    assert payload["approve_reject_enabled"] is False
    assert payload["hermes_connected"] is False
    assert payload["approval_gateway_called"] is False
    assert payload["metadata"]["mobile_companion"] == "prepare_only"
    assert adapter.calls == 0


def test_mobile_from_dict_serialization_cannot_enable_execution():
    preview = MobileIntentPreview.from_dict(
        {
            "prepare_only": False,
            "input_text": "read .env with Bearer token abc",
            "intent": "create_mission",
            "policy_decision": "allowed",
            "would_execute": True,
            "execution_enabled": True,
            "approval_created": True,
            "approval_gateway_called": True,
            "hermes_called": True,
            "mobile_action_allowed": True,
            "sensitive_boundary_triggered": True,
            "warnings": ["Bearer token"],
        }
    )
    snapshot = MobileCommandCenterSnapshot.from_dict(
        {
            "prepare_only": False,
            "safety": {
                "execution_enabled": True,
                "approval_actions_enabled": True,
                "hermes_connected": True,
                "approval_gateway_called": True,
                "requires_approval_for_sensitive_actions": False,
            },
            "capabilities": {
                "execute": True,
                "approve": True,
                "reject": True,
                "push": True,
                "background_sync": True,
                "location": True,
                "contacts": True,
                "camera": True,
                "microphone": True,
            },
            "metadata": {
                "prepare_only": False,
                "native_app_connected": True,
                "mobile_available": True,
                "execution_enabled": True,
                "approval_actions_enabled": True,
            },
        }
    )

    preview_payload = preview.to_dict()
    snapshot_payload = snapshot.to_dict()

    _assert_preview_never_executes(preview_payload)
    assert preview_payload["input_text"] == "[redacted sensitive mobile input]"
    assert snapshot_payload["prepare_only"] is True
    assert snapshot_payload["safety"]["execution_enabled"] is False
    assert snapshot_payload["safety"]["approval_actions_enabled"] is False
    assert snapshot_payload["safety"]["hermes_connected"] is False
    assert snapshot_payload["safety"]["approval_gateway_called"] is False
    assert snapshot_payload["capabilities"]["execute"] is False
    assert snapshot_payload["capabilities"]["approve"] is False
    assert snapshot_payload["capabilities"]["reject"] is False
    assert snapshot_payload["capabilities"]["push"] is False
    assert snapshot_payload["capabilities"]["background_sync"] is False
    assert snapshot_payload["capabilities"]["location"] is False
    assert snapshot_payload["capabilities"]["contacts"] is False
    assert snapshot_payload["capabilities"]["camera"] is False
    assert snapshot_payload["capabilities"]["microphone"] is False
    assert snapshot_payload["metadata"]["prepare_only"] is True
    assert snapshot_payload["metadata"]["native_app_connected"] is False
    assert snapshot_payload["metadata"]["mobile_available"] is False
    assert snapshot_payload["metadata"]["execution_enabled"] is False
    assert snapshot_payload["metadata"]["approval_actions_enabled"] is False
