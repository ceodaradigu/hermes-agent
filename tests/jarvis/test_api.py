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


def test_create_mission_valid():
    client, _adapter = _make_client()
    response = client.post("/missions", json={"objective": "lanzar operación de afiliados"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "draft"
    assert payload["objective"] == "lanzar operación de afiliados"


def test_create_mission_empty_objective_rejected():
    client, _adapter = _make_client()
    response = client.post("/missions", json={"objective": "   "})
    assert response.status_code == 400




def test_create_mission_does_not_execute_hermes():
    client, adapter = _make_client()
    response = client.post("/missions", json={"objective": "solo crear misión"})
    assert response.status_code == 200
    assert adapter.calls == 0


def test_add_step_empty_prompt_returns_400():
    client, _adapter = _make_client()
    mission = client.post("/missions", json={"objective": "objetivo"}).json()
    response = client.post(f"/missions/{mission['mission_id']}/steps", json={"prompt": "   "})
    assert response.status_code == 400


def test_add_step_empty_agent_returns_400():
    client, _adapter = _make_client()
    mission = client.post("/missions", json={"objective": "objetivo"}).json()
    response = client.post(
        f"/missions/{mission['mission_id']}/steps",
        json={"prompt": "investigar nicho", "agent": "   "},
    )
    assert response.status_code == 400

def test_list_and_get_missions():
    client, _adapter = _make_client()
    created = client.post("/missions", json={"objective": "mission A"}).json()
    response = client.get("/missions")
    assert response.status_code == 200
    assert any(m["mission_id"] == created["mission_id"] for m in response.json())

    get_response = client.get(f"/missions/{created['mission_id']}")
    assert get_response.status_code == 200
    assert get_response.json()["mission_id"] == created["mission_id"]


def test_get_nonexistent_mission_returns_404():
    client, _adapter = _make_client()
    response = client.get("/missions/missing-id")
    assert response.status_code == 404


def test_add_step_allowed_executes_hermes_once():
    client, adapter = _make_client()
    mission = client.post("/missions", json={"objective": "objetivo"}).json()

    response = client.post(
        f"/missions/{mission['mission_id']}/steps",
        json={"prompt": "investigar nicho rentable", "agent": "hermes"},
    )
    assert response.status_code == 200
    payload = response.json()
    step = payload["steps"][0]
    assert step["status"] == "completed"
    assert step["policy_decision"] == "allowed"
    assert payload["status"] == "running"
    assert adapter.calls == 1


def test_add_step_requires_approval_does_not_execute_hermes():
    client, adapter = _make_client()
    mission = client.post("/missions", json={"objective": "objetivo"}).json()

    response = client.post(f"/missions/{mission['mission_id']}/steps", json={"prompt": "leer .env"})
    assert response.status_code == 200
    payload = response.json()
    step = payload["steps"][0]
    assert step["status"] == "pending_approval"
    assert step["approval_request_id"]
    assert step["approval_request_id"] in payload["approvals"]
    assert payload["status"] == "pending_approval"
    assert adapter.calls == 0


def test_add_step_denied_does_not_execute_hermes():
    client, adapter = _make_client()
    mission = client.post("/missions", json={"objective": "objetivo"}).json()

    response = client.post(f"/missions/{mission['mission_id']}/steps", json={"prompt": "rm -rf /"})
    assert response.status_code == 200
    payload = response.json()
    step = payload["steps"][0]
    assert step["status"] == "failed"
    assert step["policy_decision"] == "denied"
    assert step["policy_reason"]
    assert payload["status"] == "blocked"
    assert adapter.calls == 0


def test_mission_metrics_updated():
    client, _adapter = _make_client()
    mission = client.post("/missions", json={"objective": "objetivo"}).json()
    mission_id = mission["mission_id"]

    client.post(f"/missions/{mission_id}/steps", json={"prompt": "investigar keyword"})
    client.post(f"/missions/{mission_id}/steps", json={"prompt": "leer .env"})
    response = client.post(f"/missions/{mission_id}/steps", json={"prompt": "rm -rf /"})

    metrics = response.json()["metrics"]
    assert metrics["steps_total"] == 3
    assert metrics["steps_completed"] == 1
    assert metrics["steps_pending_approval"] == 1
    assert metrics["steps_failed"] == 1


def test_cancel_mission_and_block_new_steps():
    client, _adapter = _make_client()
    mission = client.post("/missions", json={"objective": "objetivo"}).json()
    mission_id = mission["mission_id"]

    cancel = client.post(f"/missions/{mission_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"

    add_step = client.post(f"/missions/{mission_id}/steps", json={"prompt": "investigar nicho"})
    assert add_step.status_code == 400


def test_add_step_to_missing_mission_returns_404():
    client, _adapter = _make_client()
    response = client.post("/missions/missing-id/steps", json={"prompt": "hola"})
    assert response.status_code == 404


def test_pending_approval_mission_stays_pending_after_allowed_step():
    client, adapter = _make_client()
    mission = client.post("/missions", json={"objective": "objetivo"}).json()
    mission_id = mission["mission_id"]

    first = client.post(f"/missions/{mission_id}/steps", json={"prompt": "leer .env"})
    assert first.status_code == 200
    assert first.json()["status"] == "pending_approval"

    second = client.post(f"/missions/{mission_id}/steps", json={"prompt": "investigar keyword"})
    assert second.status_code == 200
    payload = second.json()
    assert payload["status"] == "pending_approval"
    assert adapter.calls == 1

