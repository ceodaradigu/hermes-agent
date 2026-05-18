import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import create_app
from jarvis.voice import UserUnderstandingMemoryStatus


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


def test_memory_snapshot_get_empty_store():
    client = _client()

    response = client.get("/voice/runtime/memory/snapshot")

    assert response.status_code == 200
    data = response.json()
    assert data["persisted"] is False
    assert data["snapshot"]["persisted"] is False
    assert data["snapshot"]["proposal_count"] == 0
    assert data["snapshot"]["proposals"] == []


def test_memory_snapshot_get_includes_created_proposal_count():
    client = _client()
    proposal = _create_proposal(client)

    response = client.get("/voice/runtime/memory/snapshot")

    assert response.status_code == 200
    snapshot = response.json()["snapshot"]
    assert snapshot["proposal_count"] == 1
    assert snapshot["proposals"][0]["id"] == proposal["id"]


def test_memory_snapshot_import_with_dict_imports_proposals():
    source = _client()
    proposal = _create_proposal(source)
    snapshot = source.get("/voice/runtime/memory/snapshot").json()["snapshot"]
    target = _client()

    response = target.post(
        "/voice/runtime/memory/snapshot/import",
        json={"snapshot": snapshot},
    )

    assert response.status_code == 200
    assert response.json() == {
        "imported_count": 1,
        "memory_proposal_count": 1,
        "persisted": False,
        "applied_to_runtime": False,
    }
    imported = target.get(f"/voice/runtime/memory/proposals/{proposal['id']}")
    assert imported.status_code == 200


def test_memory_snapshot_import_with_json_string_imports_proposals():
    source = _client()
    _create_proposal(source)
    snapshot = source.get("/voice/runtime/memory/snapshot").json()["snapshot"]
    target = _client()

    response = target.post(
        "/voice/runtime/memory/snapshot/import",
        json={"snapshot": json.dumps(snapshot)},
    )

    assert response.status_code == 200
    assert response.json()["imported_count"] == 1
    assert response.json()["memory_proposal_count"] == 1


def test_memory_snapshot_import_merge_keeps_existing_proposals_by_default():
    source = _client()
    source_proposal = _create_proposal(source)
    snapshot = source.get("/voice/runtime/memory/snapshot").json()["snapshot"]
    target = _client()
    existing_proposal = _create_proposal(
        target,
        original_text="consulta el estado",
        corrected_intent="query_status",
        suggested_alias="consulta estado",
    )

    response = target.post(
        "/voice/runtime/memory/snapshot/import",
        json={"snapshot": snapshot},
    )

    assert response.status_code == 200
    assert response.json()["memory_proposal_count"] == 2
    assert target.get(f"/voice/runtime/memory/proposals/{source_proposal['id']}").status_code == 200
    assert target.get(f"/voice/runtime/memory/proposals/{existing_proposal['id']}").status_code == 200


def test_memory_snapshot_import_replace_replaces_existing_proposals():
    source = _client()
    source_proposal = _create_proposal(source)
    snapshot = source.get("/voice/runtime/memory/snapshot").json()["snapshot"]
    target = _client()
    existing_proposal = _create_proposal(
        target,
        original_text="consulta el estado",
        corrected_intent="query_status",
        suggested_alias="consulta estado",
    )

    response = target.post(
        "/voice/runtime/memory/snapshot/import",
        json={"snapshot": snapshot, "replace": True},
    )

    assert response.status_code == 200
    assert response.json()["memory_proposal_count"] == 1
    assert target.get(f"/voice/runtime/memory/proposals/{source_proposal['id']}").status_code == 200
    assert target.get(f"/voice/runtime/memory/proposals/{existing_proposal['id']}").status_code == 404


def test_memory_snapshot_import_rejects_persisted_true():
    source = _client()
    _create_proposal(source)
    snapshot = source.get("/voice/runtime/memory/snapshot").json()["snapshot"]
    snapshot["persisted"] = True
    target = _client()

    response = target.post(
        "/voice/runtime/memory/snapshot/import",
        json={"snapshot": snapshot},
    )

    assert response.status_code == 400
    assert "Persisted memory snapshots" in response.json()["detail"]
    assert target.get("/voice/runtime/memory/proposals").json()["memory_proposal_count"] == 0


def test_memory_snapshot_import_rejects_invalid_format():
    client = _client()

    missing = client.post("/voice/runtime/memory/snapshot/import", json={})
    invalid_json = client.post(
        "/voice/runtime/memory/snapshot/import",
        json={"snapshot": "{invalid json"},
    )
    invalid_shape = client.post(
        "/voice/runtime/memory/snapshot/import",
        json={"snapshot": {"version": 1, "exported_at": "2026-05-18T00:00:00Z"}},
    )
    path_input = client.post(
        "/voice/runtime/memory/snapshot/import",
        json={"path": "/tmp/snapshot.json"},
    )

    assert missing.status_code == 400
    assert invalid_json.status_code == 400
    assert invalid_shape.status_code == 400
    assert path_input.status_code == 400


def test_memory_snapshot_import_rejects_sensitive_active_or_approved_proposal():
    source = _client()
    _create_proposal(
        source,
        original_text="usa el password del .env",
        corrected_intent="requires_approval",
        suggested_alias="password del .env",
    )
    snapshot = source.get("/voice/runtime/memory/snapshot").json()["snapshot"]
    snapshot["proposals"][0]["status"] = "approved"
    snapshot["proposals"][0]["active"] = True
    snapshot["active_count"] = 1
    target = _client()

    response = target.post(
        "/voice/runtime/memory/snapshot/import",
        json={"snapshot": snapshot},
    )

    assert response.status_code == 400
    assert "Sensitive memory proposals" in response.json()["detail"]
    assert target.get("/voice/runtime/memory/proposals").json()["memory_proposal_count"] == 0


def test_memory_snapshot_import_does_not_change_transcript_classification_or_apply_runtime_memory():
    source = _client()
    proposal = _create_proposal(source, corrected_intent="query_status")
    source.post(f"/voice/runtime/memory/proposals/{proposal['id']}/approve")
    snapshot = source.get("/voice/runtime/memory/snapshot").json()["snapshot"]
    target = _client()
    before = target.post(
        "/voice/runtime/transcript",
        json={"text": "monta algo para probar este nicho"},
    ).json()["result"]

    response = target.post(
        "/voice/runtime/memory/snapshot/import",
        json={"snapshot": snapshot},
    )
    after = target.post(
        "/voice/runtime/transcript",
        json={"text": "monta algo para probar este nicho"},
    ).json()["result"]
    status = target.get("/voice/runtime/status").json()

    assert response.status_code == 200
    assert after["intent"] == before["intent"]
    assert after["status"] == before["status"]
    assert "reviewed_feedback_applied" not in after["user_context_signals"]
    assert status["applied_feedback_count"] == 0
    assert status["memory_proposal_count"] == 1


def test_memory_local_save_endpoint_writes_snapshot_and_audit_log(tmp_path):
    client = _client()
    proposal = _create_proposal(client)

    response = client.post(
        "/voice/runtime/memory/local/save",
        json={"base_dir": str(tmp_path / ".jarvis"), "create_backup": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["persisted"] is True
    assert data["applied_to_runtime"] is False
    assert data["result"]["persisted"] is True
    assert data["result"]["backup_path"] is None
    snapshot_path = tmp_path / ".jarvis" / "user_understanding" / "memory_proposals.snapshot.json"
    audit_path = tmp_path / ".jarvis" / "user_understanding" / "audit_log.jsonl"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    audit_event = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[-1])
    assert snapshot["persisted"] is True
    assert snapshot["proposals"][0]["id"] == proposal["id"]
    assert audit_event["event"] == "memory_snapshot_saved"
    assert audit_event["persisted"] is True


def test_memory_local_save_endpoint_rejects_empty_base_dir():
    client = _client()

    response = client.post(
        "/voice/runtime/memory/local/save",
        json={"base_dir": "   "},
    )

    assert response.status_code == 400
    assert "base_dir must not be empty" in response.json()["detail"]


def test_memory_local_save_endpoint_rejects_null_byte_base_dir():
    client = _client()

    response = client.post(
        "/voice/runtime/memory/local/save",
        json={"base_dir": "memory\u0000root"},
    )

    assert response.status_code == 400
    assert "null bytes" in response.json()["detail"]


def test_memory_local_save_endpoint_rejects_sensitive_active_or_approved(tmp_path):
    client = _client()
    proposal = _create_proposal(
        client,
        original_text="usa el password del .env",
        corrected_intent="requires_approval",
        suggested_alias="password del .env",
    )
    runtime_proposal = client.app.state.voice_runtime.get_memory_proposal(proposal["id"])
    runtime_proposal.status = UserUnderstandingMemoryStatus.APPROVED
    runtime_proposal.active = True

    response = client.post(
        "/voice/runtime/memory/local/save",
        json={"base_dir": str(tmp_path / ".jarvis")},
    )

    assert response.status_code == 400
    assert "Sensitive active or approved" in response.json()["detail"]
    assert not (tmp_path / ".jarvis").exists()


def test_memory_local_save_does_not_change_transcript_or_create_tasks_or_missions(tmp_path):
    client = _client()
    before = client.post(
        "/voice/runtime/transcript",
        json={"text": "monta algo para probar este nicho"},
    ).json()["result"]
    proposal = _create_proposal(client, corrected_intent="query_status")
    client.post(f"/voice/runtime/memory/proposals/{proposal['id']}/approve")
    last_transcript = client.get("/voice/runtime/status").json()["last_transcript"]

    response = client.post(
        "/voice/runtime/memory/local/save",
        json={"base_dir": str(tmp_path / ".jarvis")},
    )
    after = client.post(
        "/voice/runtime/transcript",
        json={"text": "monta algo para probar este nicho"},
    ).json()["result"]

    assert response.status_code == 200
    assert after["intent"] == before["intent"]
    assert after["status"] == before["status"]
    assert "reviewed_feedback_applied" not in after["user_context_signals"]
    assert client.get("/tasks").json() == []
    assert client.get("/missions").json() == []
    assert last_transcript == "monta algo para probar este nicho"
