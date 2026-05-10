import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import create_app
from jarvis.voice.base import VoiceSynthesisResult
from jarvis.voice.storage import VoiceAudioStorage


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


class FailingVoiceAdapter:
    def __init__(self, exc):
        self.exc = exc
        self.calls = []

    def synthesize(self, request):
        self.calls.append(request)
        raise self.exc


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


def test_voice_tts_adapter_runtime_error_returns_503():
    adapter = FailingVoiceAdapter(RuntimeError("Failed to connect to GPT-SoVITS service"))
    client = _client(voice_adapter=adapter)

    response = client.post("/voice/tts", json={"text": "hola"})

    assert response.status_code == 503
    assert response.json()["detail"] == "Failed to connect to GPT-SoVITS service"
    assert len(adapter.calls) == 1


def test_voice_tts_adapter_value_error_returns_400():
    adapter = FailingVoiceAdapter(ValueError("bad config"))
    client = _client(voice_adapter=adapter)

    response = client.post("/voice/tts", json={"text": "hola"})

    assert response.status_code == 400
    assert response.json()["detail"] == "bad config"
    assert len(adapter.calls) == 1


def test_voice_tts_adapter_unexpected_error_returns_generic_502():
    adapter = FailingVoiceAdapter(Exception("boom"))
    client = _client(voice_adapter=adapter)

    response = client.post("/voice/tts", json={"text": "hola"})

    assert response.status_code == 502
    assert response.json()["detail"] == "voice synthesis failed"
    assert "boom" not in response.text
    assert len(adapter.calls) == 1


def test_voice_tts_sanitizes_sensitive_metadata_keys():
    adapter = RecordingVoiceAdapter()
    client = _client(voice_adapter=adapter)

    response = client.post(
        "/voice/tts",
        json={
            "text": "hola",
            "metadata": {
                "source": "unit-test",
                "ref_audio_path": "/tmp/ref.wav",
                "prompt_text": "texto sensible",
                "api_key": "abc",
                "access_token": "def",
                "db_password": "ghi",
                "client_secret": "jkl",
                "output_path": "/tmp/out.wav",
            },
        },
    )

    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata["source"] == "unit-test"
    assert metadata["adapter"] == "recording"
    assert "ref_audio_path" not in metadata
    assert "prompt_text" not in metadata
    assert "api_key" not in metadata
    assert "access_token" not in metadata
    assert "db_password" not in metadata
    assert "client_secret" not in metadata
    assert "output_path" not in metadata


def test_voice_tts_sanitizes_adapter_added_sensitive_metadata():
    class SensitiveMetadataAdapter:
        def synthesize(self, request):
            return VoiceSynthesisResult(
                content_type="audio/wav",
                provider="sensitive",
                audio_bytes=b"abc",
                metadata={
                    "source": request.metadata["source"],
                    "base_url": "http://127.0.0.1:9880",
                    "ref_audio_path": "/tmp/ref.wav",
                    "prompt_text": "texto sensible",
                    "prompt_lang": "es",
                    "service_token": "secret-token",
                    "password": "secret-password",
                },
            )

    client = _client(voice_adapter=SensitiveMetadataAdapter())

    response = client.post("/voice/tts", json={"text": "hola", "metadata": {"source": "unit-test"}})

    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata == {"source": "unit-test", "prompt_lang": "es"}


def test_voice_tts_sanitizing_does_not_remove_response_audio_path(tmp_path):
    adapter = RecordingVoiceAdapter()
    storage = VoiceAudioStorage(tmp_path)
    client = _client(voice_adapter=adapter, voice_audio_storage=storage)

    response = client.post(
        "/voice/tts",
        json={
            "text": "hola",
            "save_audio": True,
            "metadata": {"source": "unit-test", "ref_audio_path": "/tmp/ref.wav"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["audio_path"]
    assert data["has_audio_bytes"] is True
    assert data["metadata"] == {"source": "unit-test", "adapter": "recording"}


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
