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
