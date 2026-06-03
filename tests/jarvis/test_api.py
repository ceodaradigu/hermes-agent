import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import create_app


class DummyAdapter:
    def __init__(self):
        self.calls = 0

    def run(self, message: str, **kwargs):
        self.calls += 1
        return {"final_response": f"echo:{message}", "messages": []}


def _make_client():
    adapter = DummyAdapter()
    app = create_app(adapter_factory=lambda: adapter)
    return TestClient(app), adapter


def test_health_ok():
    client, _ = _make_client()
    response = client.get("/health")
    assert response.status_code == 200


def test_command_center_returns_prepare_only_placeholder_snapshot(monkeypatch):
    client, adapter = _make_client()

    def fail_approval(*args, **kwargs):
        raise AssertionError("ApprovalGateway must not be called by read-only Command Center API")

    monkeypatch.setattr("jarvis.policy.approval_gateway.ApprovalGateway.create_request", fail_approval)

    response = client.get("/command-center")
    payload = response.json()

    assert response.status_code == 200
    assert payload["prepare_only"] is True
    assert payload["execution_enabled"] is False
    assert payload["approval_enabled"] is False
    assert payload["approve_reject_enabled"] is False
    assert payload["hermes_connected"] is False
    assert payload["approval_gateway_called"] is False
    assert payload["metadata"]["prepare_only"] is True
    assert payload["metadata"]["execution_enabled"] is False
    assert payload["metadata"]["approval_enabled"] is False
    assert payload["metadata"]["approve_reject_enabled"] is False
    assert payload["metadata"]["hermes_connected"] is False
    assert payload["metadata"]["approval_gateway_called"] is False
    assert payload["missions"] == []
    assert payload["approvals"] == []
    assert payload["audit_timeline"] == []
    assert payload["agents"] == []
    assert payload["risk_budget_panels"] == []
    assert payload["hermes_payloads"] == []
    assert payload["devices"] == [
        {
            "device_id": "device-placeholder",
            "label": "Device runtime not connected",
            "trusted": False,
            "online": False,
            "approval_capable": False,
            "status": "placeholder",
        }
    ]
    assert payload["voice_camera_controls"]["voice_status"] == "placeholder"
    assert payload["voice_camera_controls"]["camera_status"] == "placeholder"
    assert payload["voice_camera_controls"]["can_start_voice"] is False
    assert payload["voice_camera_controls"]["can_start_camera"] is False
    assert payload["voice_camera_controls"]["can_record"] is False
    assert payload["cost_roi_summary"]["roi_status"] == "placeholder"
    assert payload["safety_indicator"]["policy_engine_boundary"]
    assert adapter.calls == 0


def test_command_center_does_not_expose_audio_env_or_credentials():
    client, _ = _make_client()

    response = client.get("/command-center")
    serialized = response.text.lower()

    assert response.status_code == 200
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
        "ref_audio",
        "base_url",
        "prompt_text",
    ):
        assert forbidden not in serialized


def test_command_center_get_does_not_create_missions_or_execute_runtime():
    client, adapter = _make_client()

    before = client.get("/missions")
    response = client.get("/command-center")
    after = client.get("/missions")

    assert before.status_code == 200
    assert response.status_code == 200
    assert after.status_code == 200
    assert before.json() == []
    assert after.json() == []
    assert adapter.calls == 0


def test_command_center_has_no_post_action_endpoint():
    client, _ = _make_client()

    response = client.post("/command-center")

    assert response.status_code == 405


def test_create_allowed_task_executes():
    client, adapter = _make_client()
    response = client.post("/tasks", json={"prompt": "investigar nichos de afiliación"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert adapter.calls == 1


def test_create_and_get_mission():
    client, _ = _make_client()
    created = client.post("/missions")
    assert created.status_code == 200
    mission_id = created.json()["mission_id"]

    fetched = client.get(f"/missions/{mission_id}")
    assert fetched.status_code == 200
    assert fetched.json()["mission_id"] == mission_id


def test_allowed_mission_step_executes_hermes_once():
    client, adapter = _make_client()
    mission_id = client.post("/missions").json()["mission_id"]

    response = client.post(f"/missions/{mission_id}/steps", json={"prompt": "haz un resumen breve"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["step"]["status"] == "completed"
    assert payload["mission"]["status"] == "completed"
    assert adapter.calls == 1


def test_denied_mission_step_blocks_mission_and_skips_hermes():
    client, adapter = _make_client()
    mission_id = client.post("/missions").json()["mission_id"]

    response = client.post(f"/missions/{mission_id}/steps", json={"prompt": "rm -rf /"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["step"]["status"] == "denied"
    assert payload["mission"]["status"] == "blocked"
    assert adapter.calls == 0


def test_requires_approval_step_creates_request_and_keeps_pending_approval():
    client, adapter = _make_client()
    mission_id = client.post("/missions").json()["mission_id"]

    response = client.post(f"/missions/{mission_id}/steps", json={"prompt": "leer .env"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["step"]["status"] == "pending_approval"
    assert payload["step"]["approval_request_id"]
    assert payload["mission"]["status"] == "pending_approval"
    assert adapter.calls == 0


def test_list_missions_and_cancel():
    client, _ = _make_client()
    mission_id = client.post("/missions").json()["mission_id"]

    listed = client.get("/missions")
    assert listed.status_code == 200
    assert any(item["mission_id"] == mission_id for item in listed.json())

    cancelled = client.post(f"/missions/{mission_id}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
