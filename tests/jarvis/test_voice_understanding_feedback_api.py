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
