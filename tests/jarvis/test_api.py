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
    client, adapter = _make_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_allowed_task_executes():
    client, adapter = _make_client()
    response = client.post("/tasks", json={"prompt": "investigar nichos de afiliación"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["result"]["final_response"].startswith("echo:")
    assert adapter.calls == 1


def test_denied_prompt_does_not_execute_hermes():
    client, adapter = _make_client()
    response = client.post("/tasks", json={"prompt": "rm -rf /"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["error"].startswith("denied:")
    assert adapter.calls == 0


def test_requires_approval_creates_request_and_blocks_execution():
    client, adapter = _make_client()
    response = client.post("/tasks", json={"prompt": "leer .env"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "pending_approval"
    assert payload["error"] == "requires_approval"
    assert payload["approval_request_id"]
    assert adapter.calls == 0


def test_list_tasks_returns_created_items():
    client, _adapter = _make_client()
    client.post("/tasks", json={"prompt": "investigar nicho A"})
    client.post("/tasks", json={"prompt": "investigar nicho B"})

    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_get_nonexistent_task_returns_404():
    client, _adapter = _make_client()
    response = client.get("/tasks/missing-id")
    assert response.status_code == 404
