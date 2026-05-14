import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import create_app


def _client(**kwargs):
    return TestClient(create_app(**kwargs))


def test_feedback_get_starts_empty():
    client = _client()

    response = client.get("/voice/runtime/feedback")

    assert response.status_code == 200
    assert response.json() == {"feedback": [], "feedback_count": 0}


def test_feedback_post_stores_correction():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
            "correction_note": "Cuando hablo de probar un nicho, normalmente quiero validación primero.",
            "preferred_next_step": "Crear misión de validación antes de crear landing.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["feedback_count"] == 1
    assert data["applied_persistently"] is False
    assert data["feedback"]["original_text"] == "monta algo para probar este nicho"
    assert data["feedback"]["interpreted_intent"] == "create_asset"
    assert data["feedback"]["corrected_intent"] == "create_mission"
    assert data["feedback"]["applied_persistently"] is False
    assert data["feedback"]["requires_review"] is True


def test_feedback_preview_returns_review_only_without_storing_feedback():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback/preview",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
            "correction_note": "Cuando hablo de probar un nicho, normalmente quiero una misión de validación primero.",
            "preferred_next_step": "Crear misión de validación antes de crear landing.",
        },
    )
    feedback_after = client.get("/voice/runtime/feedback")
    status_after = client.get("/voice/runtime/status")

    assert response.status_code == 200
    data = response.json()
    assert data["applied"] is False
    assert data["requires_review"] is True
    assert data["feedback_count"] == 0
    assert data["preview"]["applied"] is False
    assert data["preview"]["requires_review"] is True
    assert data["preview"]["corrected_intent"] == "create_mission"
    assert data["preview"]["suggested_alias"] == "probar este nicho"
    assert feedback_after.json() == {"feedback": [], "feedback_count": 0}
    assert status_after.json()["feedback_count"] == 0
    assert status_after.json()["applied_feedback_count"] == 0


def test_feedback_preview_accepts_empty_optional_fields_without_storing_feedback():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback/preview",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": None,
            "corrected_intent": "create_mission",
            "correction_note": None,
            "preferred_next_step": "",
        },
    )

    assert response.status_code == 200
    assert response.json()["preview"]["corrected_intent"] == "create_mission"
    assert response.json()["feedback_count"] == 0
    assert client.get("/voice/runtime/feedback").json() == {"feedback": [], "feedback_count": 0}


def test_feedback_get_lists_corrections():
    client = _client()
    client.post(
        "/voice/runtime/feedback",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
        },
    )

    response = client.get("/voice/runtime/feedback")

    assert response.status_code == 200
    data = response.json()
    assert data["feedback_count"] == 1
    assert data["feedback"][0]["corrected_intent"] == "create_mission"


def test_feedback_delete_clears_corrections():
    client = _client()
    client.post(
        "/voice/runtime/feedback",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
        },
    )

    response = client.delete("/voice/runtime/feedback")
    after = client.get("/voice/runtime/feedback")

    assert response.status_code == 200
    assert response.json() == {"feedback_count": 0}
    assert after.json() == {"feedback": [], "feedback_count": 0}


def test_feedback_post_without_original_text_returns_400():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback",
        json={
            "original_text": "   ",
            "corrected_intent": "create_mission",
        },
    )

    assert response.status_code == 400
    assert "original_text must be non-empty" in response.json()["detail"]


def test_feedback_post_without_corrected_intent_returns_400():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback",
        json={
            "original_text": "monta algo para probar este nicho",
            "corrected_intent": "   ",
        },
    )

    assert response.status_code == 400
    assert "corrected_intent must be non-empty" in response.json()["detail"]


def test_feedback_preview_missing_original_text_returns_400():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback/preview",
        json={
            "corrected_intent": "create_mission",
        },
    )

    assert response.status_code == 400
    assert "original_text must be non-empty" in response.json()["detail"]


def test_feedback_preview_blank_original_text_returns_400():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback/preview",
        json={
            "original_text": "   ",
            "corrected_intent": "create_mission",
        },
    )

    assert response.status_code == 400
    assert "original_text must be non-empty" in response.json()["detail"]


def test_feedback_preview_missing_corrected_intent_returns_400():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback/preview",
        json={
            "original_text": "monta algo para probar este nicho",
        },
    )

    assert response.status_code == 400
    assert "corrected_intent must be non-empty" in response.json()["detail"]


def test_feedback_preview_blank_corrected_intent_returns_400():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback/preview",
        json={
            "original_text": "monta algo para probar este nicho",
            "corrected_intent": "   ",
        },
    )

    assert response.status_code == 400
    assert "corrected_intent must be non-empty" in response.json()["detail"]


def test_feedback_post_still_stores_after_preview():
    client = _client()
    client.post(
        "/voice/runtime/feedback/preview",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
        },
    )

    response = client.post(
        "/voice/runtime/feedback",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
        },
    )

    assert response.status_code == 200
    assert response.json()["feedback_count"] == 1
    assert client.get("/voice/runtime/feedback").json()["feedback_count"] == 1
    assert client.get("/voice/runtime/status").json()["applied_feedback_count"] == 0


def test_runtime_status_includes_feedback_count():
    client = _client()
    client.post(
        "/voice/runtime/feedback",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
        },
    )

    response = client.get("/voice/runtime/status")

    assert response.status_code == 200
    assert response.json()["feedback_count"] == 1


def test_apply_reviewed_feedback_creates_applied_rule():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback/apply-reviewed",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
            "correction_note": "Cuando hablo de probar un nicho, normalmente quiero una misión de validación primero.",
            "preferred_next_step": "Crear misión de validación antes de crear landing.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["applied_feedback_count"] == 1
    assert data["applied_persistently"] is False
    assert data["applied_rule"]["corrected_intent"] == "create_mission"
    assert data["applied_rule"]["suggested_alias"] == "probar este nicho"
    assert data["applied_rule"]["applied_persistently"] is False
    assert client.get("/voice/runtime/status").json()["applied_feedback_count"] == 1


def test_applied_feedback_get_lists_rules():
    client = _client()
    client.post(
        "/voice/runtime/feedback/apply-reviewed",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
        },
    )

    response = client.get("/voice/runtime/feedback/applied")

    assert response.status_code == 200
    data = response.json()
    assert data["applied_feedback_count"] == 1
    assert data["applied_persistently"] is False
    assert data["applied_rules"][0]["corrected_intent"] == "create_mission"


def test_applied_feedback_delete_clears_rules():
    client = _client()
    client.post(
        "/voice/runtime/feedback/apply-reviewed",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
        },
    )

    response = client.delete("/voice/runtime/feedback/applied")
    after = client.get("/voice/runtime/feedback/applied")

    assert response.status_code == 200
    assert response.json() == {"applied_feedback_count": 0, "applied_persistently": False}
    assert after.json()["applied_rules"] == []
    assert after.json()["applied_feedback_count"] == 0


def test_apply_reviewed_feedback_without_original_text_returns_400():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback/apply-reviewed",
        json={
            "original_text": "   ",
            "corrected_intent": "create_mission",
        },
    )

    assert response.status_code == 400
    assert "original_text must be non-empty" in response.json()["detail"]


def test_apply_reviewed_feedback_without_corrected_intent_returns_400():
    client = _client()

    response = client.post(
        "/voice/runtime/feedback/apply-reviewed",
        json={
            "original_text": "monta algo para probar este nicho",
            "corrected_intent": "   ",
        },
    )

    assert response.status_code == 400
    assert "corrected_intent must be non-empty" in response.json()["detail"]


def test_feedback_add_does_not_create_applied_rule():
    client = _client()

    client.post(
        "/voice/runtime/feedback",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
        },
    )

    assert client.get("/voice/runtime/feedback/applied").json()["applied_feedback_count"] == 0
    result = client.post("/voice/runtime/transcript", json={"text": "monta algo para probar este nicho"}).json()
    assert result["result"]["intent"] == "create_asset"


def test_apply_reviewed_feedback_corrects_matching_transcript():
    client = _client()
    client.post(
        "/voice/runtime/feedback/apply-reviewed",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
        },
    )

    response = client.post("/voice/runtime/transcript", json={"text": "monta algo para probar este nicho"})

    assert response.status_code == 200
    data = response.json()
    assert data["result"]["status"] == "pending"
    assert data["result"]["intent"] == "create_mission"
    assert data["result"]["executed"] is False
    assert data["result"]["approval_required"] is False
    assert data["result"]["user_context_signals"]["reviewed_feedback_applied"] is True
    assert data["state"]["applied_feedback_count"] == 1


def test_sensitive_transcript_requires_approval_even_with_applied_rule():
    client = _client()
    client.post(
        "/voice/runtime/feedback/apply-reviewed",
        json={
            "original_text": "monta algo para probar este nicho",
            "interpreted_intent": "create_asset",
            "corrected_intent": "create_mission",
        },
    )

    response = client.post(
        "/voice/runtime/transcript",
        json={"text": "monta algo para probar este nicho y usa el password del .env"},
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "requires_approval"
    assert result["intent"] == "requires_approval"
    assert result["approval_required"] is True
    assert result["executed"] is False
    assert "reviewed_feedback_applied" not in result["user_context_signals"]


def test_runtime_transcript_still_works_with_feedback_api_present():
    client = _client()

    response = client.post("/voice/runtime/transcript", json={"text": "crea una landing para afiliados"})

    assert response.status_code == 200
    assert response.json()["result"]["intent"] == "create_asset"
    assert response.json()["result"]["executed"] is False


def test_voice_tts_mock_still_works_with_feedback_api_present():
    client = _client()

    response = client.post("/voice/tts", json={"text": "hola mundo"})

    assert response.status_code == 200
    assert response.json()["provider"] == "mock"
