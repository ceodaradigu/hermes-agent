import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import create_app
from jarvis.voice.base import VoiceSynthesisResult


class RecordingVoiceAdapter:
    def __init__(self):
        self.calls = []

    def synthesize(self, request):
        self.calls.append(request)
        return VoiceSynthesisResult(
            content_type=f"audio/{request.output_format}",
            provider="recording",
            audio_bytes=b"abc",
            duration_seconds=1.23,
            metadata={**request.metadata, "adapter": "recording"},
        )


def _client(**kwargs):
    return TestClient(create_app(**kwargs))


class DummyRuntimeAdapter:
    def run(self, message: str, **kwargs):
        return {"ok": True}


def test_voice_tts_uses_mock_adapter_by_default():
    client = _client()

    response = client.post("/voice/tts", json={"text": "hola mundo"})

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["content_type"] == "audio/wav"
    assert data["has_audio_bytes"] is True
    assert "audio_bytes" not in data


def test_voice_tts_empty_text_returns_400():
    client = _client()

    response = client.post("/voice/tts", json={"text": "   "})

    assert response.status_code == 400
    assert "text must be non-empty" in response.json()["detail"]


def test_voice_tts_denied_skips_adapter():
    adapter = RecordingVoiceAdapter()
    client = _client(voice_adapter=adapter)

    response = client.post("/voice/tts", json={"text": "rm -rf /"})

    assert response.status_code == 403
    assert "denied" in response.json()["detail"]
    assert adapter.calls == []


def test_voice_tts_requires_approval_creates_request_and_skips_adapter():
    adapter = RecordingVoiceAdapter()
    client = _client(voice_adapter=adapter)

    response = client.post("/voice/tts", json={"text": "leer .env"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending_approval"
    assert data["approval_request_id"]
    assert data["has_audio_bytes"] is False
    assert adapter.calls == []


def test_voice_tts_preserves_metadata_and_uses_injected_adapter():
    adapter = RecordingVoiceAdapter()
    client = _client(voice_adapter=adapter)

    response = client.post(
        "/voice/tts",
        json={
            "text": "hola",
            "output_format": "ogg",
            "metadata": {"trace_id": "t-1"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "recording"
    assert data["metadata"]["trace_id"] == "t-1"
    assert data["metadata"]["adapter"] == "recording"
    assert len(adapter.calls) == 1
    assert adapter.calls[0].output_format == "ogg"


def test_voice_tts_invalid_output_format_returns_clear_400():
    client = _client()

    response = client.post("/voice/tts", json={"text": "hola", "output_format": "flac"})

    assert response.status_code == 400
    assert "output_format must be one of" in response.json()["detail"]


def test_voice_tts_empty_language_returns_clear_400():
    client = _client()

    response = client.post("/voice/tts", json={"text": "hola", "language": "   "})

    assert response.status_code == 400
    assert "language must be non-empty" in response.json()["detail"]


def test_tasks_and_missions_still_work_with_voice_changes():
    client = _client(adapter_factory=lambda: DummyRuntimeAdapter())

    task = client.post("/tasks", json={"prompt": "resumen corto"})
    mission = client.post("/missions")

    assert task.status_code == 200
    assert task.json()["status"] == "completed"
    assert mission.status_code == 200
    assert mission.json()["mission_id"]
