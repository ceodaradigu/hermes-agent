import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import create_app


def _client(**kwargs):
    return TestClient(create_app(**kwargs))


def test_voice_runtime_status_returns_initial_state():
    client = _client()

    response = client.get("/voice/runtime/status")

    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False
    assert data["mode"] == "off"
    assert data["frontend_required"] is False
    assert data["input_language"] == "es"
    assert data["output_language"] == "es"
    assert data["wake_words"] == ["jarvis", "hola jarvis"]
    assert data["feedback_count"] == 0
    assert data["applied_feedback_count"] == 0


def test_voice_runtime_start_enables_wake_word_mode():
    client = _client()

    response = client.post("/voice/runtime/start")

    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert data["mode"] == "wake_word"


def test_voice_runtime_stop_disables_and_enters_off_mode():
    client = _client()
    client.post("/voice/runtime/start")

    response = client.post("/voice/runtime/stop")

    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False
    assert data["mode"] == "off"


def test_voice_runtime_mode_accepts_listening():
    client = _client()

    response = client.post("/voice/runtime/mode", json={"mode": "listening"})

    assert response.status_code == 200
    assert response.json()["mode"] == "listening"


def test_voice_runtime_mode_rejects_invalid_mode():
    client = _client()

    response = client.post("/voice/runtime/mode", json={"mode": "invalid"})

    assert response.status_code == 400
    assert "Invalid voice runtime mode" in response.json()["detail"]


def test_voice_runtime_control_sleep_phrase_changes_to_wake_word():
    client = _client()
    client.post("/voice/runtime/mode", json={"mode": "listening"})

    response = client.post("/voice/runtime/control", json={"text": "jarvis no escuches"})

    assert response.status_code == 200
    data = response.json()
    assert data["recognized"] is True
    assert data["result"]["action"] == "wake_word_only"
    assert data["state"]["mode"] == "wake_word"


def test_voice_runtime_control_wake_phrase_changes_to_listening():
    client = _client()

    response = client.post("/voice/runtime/control", json={"text": "hola jarvis"})

    assert response.status_code == 200
    data = response.json()
    assert data["recognized"] is True
    assert data["result"]["action"] == "listen_briefly"
    assert data["state"]["mode"] == "listening"


def test_voice_runtime_control_still_works_after_intent_router_changes():
    client = _client()

    response = client.post("/voice/runtime/control", json={"text": "hola jarvis"})

    assert response.status_code == 200
    assert response.json()["recognized"] is True


def test_voice_runtime_transcript_stores_last_transcript():
    client = _client()

    response = client.post("/voice/runtime/transcript", json={"text": "crea una landing para X"})

    assert response.status_code == 200
    data = response.json()
    assert data["result"]["status"] == "pending"
    assert data["result"]["intent"] == "create_asset"
    assert data["result"]["executed"] is False
    assert data["state"]["last_transcript"] == "crea una landing para X"
    assert data["state"]["last_intent"] == data["result"]


def test_voice_runtime_transcript_does_not_create_real_tasks():
    client = _client()

    response = client.post("/voice/runtime/transcript", json={"text": "crea una landing para X"})
    tasks = client.get("/tasks")
    missions = client.get("/missions")

    assert response.status_code == 200
    assert tasks.status_code == 200
    assert missions.status_code == 200
    assert tasks.json() == []
    assert missions.json() == []


def test_voice_runtime_endpoints_do_not_require_frontend_open():
    client = _client()

    response = client.get("/voice/runtime/status")

    assert response.status_code == 200
    assert response.json()["frontend_required"] is False


def test_voice_tts_still_works_with_mock_provider():
    client = _client()

    response = client.post("/voice/tts", json={"text": "hola mundo"})

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["has_audio_bytes"] is True


def test_voice_tts_mock_still_works_after_intent_router_changes():
    client = _client()

    response = client.post("/voice/tts", json={"text": "hola jarvis"})

    assert response.status_code == 200
    assert response.json()["provider"] == "mock"
