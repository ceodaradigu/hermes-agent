import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import create_app


def _client(**kwargs):
    return TestClient(create_app(**kwargs))


def _create_proposal(client, **overrides):
    payload = {
        "original_text": "monta algo para probar este nicho",
        "corrected_intent": "create_mission",
        "suggested_alias": "probar este nicho",
        "reason": "Regla revisada por David",
        "source": "user_reviewed_feedback",
        "applied_persistently": False,
    }
    payload.update(overrides)
    response = client.post("/voice/runtime/memory/proposals/from-applied-feedback", json=payload)
    assert response.status_code == 200
    return response.json()["proposal"]


def test_memory_proposals_get_starts_empty():
    client = _client()

    response = client.get("/voice/runtime/memory/proposals")

    assert response.status_code == 200
    assert response.json() == {"proposals": [], "memory_proposal_count": 0}


def test_memory_proposal_from_applied_feedback_creates_proposed_inactive_proposal():
    client = _client()

    response = client.post(
        "/voice/runtime/memory/proposals/from-applied-feedback",
        json={
            "original_text": "monta algo para probar este nicho",
            "corrected_intent": "create_mission",
            "suggested_alias": "probar este nicho",
            "reason": "Regla revisada por David",
            "source": "user_reviewed_feedback",
            "applied_persistently": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["memory_proposal_count"] == 1
    assert data["applied_persistently"] is False
    assert data["proposal"]["status"] == "proposed"
    assert data["proposal"]["active"] is False
    assert data["proposal"]["alias"] == "probar este nicho"
    assert data["proposal"]["target_intent"] == "create_mission"


def test_runtime_status_includes_memory_proposal_count():
    client = _client()
    _create_proposal(client)

    response = client.get("/voice/runtime/status")

    assert response.status_code == 200
    assert response.json()["memory_proposal_count"] == 1


def test_memory_proposal_get_by_id_returns_proposal():
    client = _client()
    proposal = _create_proposal(client)

    response = client.get(f"/voice/runtime/memory/proposals/{proposal['id']}")

    assert response.status_code == 200
    assert response.json()["proposal"]["id"] == proposal["id"]


def test_memory_proposal_get_unknown_id_returns_404():
    client = _client()

    response = client.get("/voice/runtime/memory/proposals/unknown")

    assert response.status_code == 404
    assert response.json()["detail"] == "memory proposal not found"


def test_memory_proposal_review_changes_status():
    client = _client()
    proposal = _create_proposal(client)

    response = client.post(f"/voice/runtime/memory/proposals/{proposal['id']}/review")

    assert response.status_code == 200
    data = response.json()["proposal"]
    assert data["status"] == "reviewed"
    assert data["active"] is False


def test_memory_proposal_approve_non_sensitive_changes_approved_active():
    client = _client()
    proposal = _create_proposal(client)

    response = client.post(f"/voice/runtime/memory/proposals/{proposal['id']}/approve")

    assert response.status_code == 200
    data = response.json()["proposal"]
    assert data["status"] == "approved"
    assert data["active"] is True
    assert data["approved_by"] == "David"


def test_memory_proposal_approve_sensitive_returns_400_and_does_not_activate():
    client = _client()
    proposal = _create_proposal(
        client,
        original_text="usa el password del .env",
        corrected_intent="requires_approval",
        suggested_alias="password del .env",
    )

    response = client.post(f"/voice/runtime/memory/proposals/{proposal['id']}/approve")
    after = client.get(f"/voice/runtime/memory/proposals/{proposal['id']}").json()["proposal"]

    assert response.status_code == 400
    assert "Sensitive memory proposals" in response.json()["detail"]
    assert after["sensitive"] is True
    assert after["status"] == "proposed"
    assert after["active"] is False


def test_memory_proposal_disable_changes_disabled_inactive():
    client = _client()
    proposal = _create_proposal(client)
    client.post(f"/voice/runtime/memory/proposals/{proposal['id']}/approve")

    response = client.post(
        f"/voice/runtime/memory/proposals/{proposal['id']}/disable",
        json={"reason": "Ya no aplica."},
    )

    assert response.status_code == 200
    data = response.json()["proposal"]
    assert data["status"] == "disabled"
    assert data["active"] is False
    assert data["reason"] == "Ya no aplica."


def test_memory_proposal_delete_changes_deleted_inactive():
    client = _client()
    proposal = _create_proposal(client)
    client.post(f"/voice/runtime/memory/proposals/{proposal['id']}/approve")

    response = client.delete(f"/voice/runtime/memory/proposals/{proposal['id']}")

    assert response.status_code == 200
    data = response.json()["proposal"]
    assert data["status"] == "deleted"
    assert data["active"] is False


def test_memory_proposals_clear_removes_all_proposals():
    client = _client()
    _create_proposal(client)

    response = client.delete("/voice/runtime/memory/proposals")
    after = client.get("/voice/runtime/memory/proposals")

    assert response.status_code == 200
    assert response.json() == {"memory_proposal_count": 0}
    assert after.json() == {"proposals": [], "memory_proposal_count": 0}


def test_approving_memory_proposal_does_not_change_transcript_classification():
    client = _client()
    before = client.post(
        "/voice/runtime/transcript",
        json={"text": "monta algo para probar este nicho"},
    ).json()["result"]
    proposal = _create_proposal(client, corrected_intent="query_status")

    approve = client.post(f"/voice/runtime/memory/proposals/{proposal['id']}/approve")
    after = client.post(
        "/voice/runtime/transcript",
        json={"text": "monta algo para probar este nicho"},
    ).json()["result"]

    assert approve.status_code == 200
    assert after["intent"] == before["intent"]
    assert after["status"] == before["status"]
    assert "reviewed_feedback_applied" not in after["user_context_signals"]


def test_memory_proposals_are_not_persistent_between_new_voice_runtime_instances():
    client = _client()
    _create_proposal(client)

    fresh_client = _client()

    assert client.get("/voice/runtime/memory/proposals").json()["memory_proposal_count"] == 1
    assert fresh_client.get("/voice/runtime/memory/proposals").json() == {
        "proposals": [],
        "memory_proposal_count": 0,
    }


def test_voice_tts_mock_still_works_with_memory_proposals_api_present():
    client = _client()

    response = client.post("/voice/tts", json={"text": "hola mundo"})

    assert response.status_code == 200
    assert response.json()["provider"] == "mock"
