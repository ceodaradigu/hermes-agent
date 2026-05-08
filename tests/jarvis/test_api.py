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
