from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import create_app
from jarvis.voice.base import VoiceSynthesisResult
from jarvis.voice.storage import VoiceAudioStorage


class RecordingVoiceAdapter:
    def __init__(self, audio_bytes: bytes | None = b"abc", audio_path: Path | None = None):
        self.calls = []
        self.audio_bytes = audio_bytes
        self.audio_path = audio_path

    def synthesize(self, request):
        self.calls.append(request)
        return VoiceSynthesisResult(
            content_type=f"audio/{request.output_format}",
            provider="recording",
            audio_bytes=self.audio_bytes,
            audio_path=self.audio_path,
            duration_seconds=1.0,
            metadata={"ok": True},
        )




def test_voice_audio_storage_init_does_not_create_base_dir(tmp_path):
    base_dir = tmp_path / "voice_storage_base"

    VoiceAudioStorage(base_dir=base_dir)

    assert not base_dir.exists()
def test_voice_audio_storage_creates_directory_on_save(tmp_path):
    base = tmp_path / "nested" / "voice_outputs"
    storage = VoiceAudioStorage(base)
    assert not base.exists()

    storage.save_audio(b"data", "wav")

    assert base.exists()


@pytest.mark.parametrize("fmt", ["wav", "mp3", "ogg"])
def test_voice_audio_storage_saves_supported_formats(tmp_path, fmt):
    storage = VoiceAudioStorage(tmp_path)
    saved = Path(storage.save_audio(b"data", fmt))
    assert saved.exists()
    assert saved.suffix == f".{fmt}"


def test_voice_audio_storage_rejects_invalid_format(tmp_path):
    storage = VoiceAudioStorage(tmp_path)
    with pytest.raises(ValueError, match="unsupported output_format"):
        storage.save_audio(b"data", "flac")


def test_voice_audio_storage_generated_path_stays_inside_base_dir(tmp_path):
    storage = VoiceAudioStorage(tmp_path)
    saved = Path(storage.save_audio(b"data", "wav")).resolve()
    assert tmp_path.resolve() in saved.parents


def test_voice_audio_storage_disallows_traversal_in_base_dir(tmp_path):
    blocked = tmp_path / "missing" / ".." / "outside"
    with pytest.raises(ValueError, match="invalid output path"):
        VoiceAudioStorage(blocked).save_audio(b"data", "wav")


def test_voice_tts_save_audio_false_does_not_write(tmp_path):
    adapter = RecordingVoiceAdapter(audio_bytes=b"hello")
    base_dir = tmp_path / "voice_storage_base"
    storage = VoiceAudioStorage(base_dir)
    client = TestClient(create_app(voice_adapter=adapter, voice_audio_storage=storage))

    response = client.post("/voice/tts", json={"text": "hola", "save_audio": False})

    assert response.status_code == 200
    assert response.json()["audio_path"] is None
    assert not base_dir.exists()


def test_voice_tts_save_audio_true_writes_and_returns_audio_path(tmp_path):
    adapter = RecordingVoiceAdapter(audio_bytes=b"hello")
    storage = VoiceAudioStorage(tmp_path)
    client = TestClient(create_app(voice_adapter=adapter, voice_audio_storage=storage))

    response = client.post("/voice/tts", json={"text": "hola", "save_audio": True, "output_format": "wav"})

    assert response.status_code == 200
    data = response.json()
    assert "audio_bytes" not in data
    assert data["audio_path"]
    assert Path(data["audio_path"]).exists()


def test_voice_tts_no_audio_bytes_does_not_fail_and_uses_adapter_audio_path(tmp_path):
    existing = tmp_path / "existing.wav"
    existing.write_bytes(b"x")
    adapter = RecordingVoiceAdapter(audio_bytes=None, audio_path=existing)
    client = TestClient(create_app(voice_adapter=adapter, voice_audio_storage=VoiceAudioStorage(tmp_path / "store")))

    response = client.post("/voice/tts", json={"text": "hola", "save_audio": True})

    assert response.status_code == 200
    assert response.json()["audio_path"] == str(existing)


def test_voice_tts_denied_or_pending_approval_do_not_save(tmp_path):
    adapter = RecordingVoiceAdapter(audio_bytes=b"hello")
    base_dir = tmp_path / "voice_storage_base"
    client = TestClient(create_app(voice_adapter=adapter, voice_audio_storage=VoiceAudioStorage(base_dir)))

    denied = client.post("/voice/tts", json={"text": "rm -rf /", "save_audio": True})
    pending = client.post("/voice/tts", json={"text": "leer .env", "save_audio": True})

    assert denied.status_code == 403
    assert pending.status_code == 200
    assert pending.json()["status"] == "pending_approval"
    assert not base_dir.exists()


def test_injected_storage_is_used(tmp_path):
    class StubStorage:
        def __init__(self):
            self.calls = []

        def save_audio(self, audio_bytes: bytes, output_format: str) -> str:
            self.calls.append((audio_bytes, output_format))
            return "custom/path.wav"

    adapter = RecordingVoiceAdapter(audio_bytes=b"hello")
    storage = StubStorage()
    client = TestClient(create_app(voice_adapter=adapter, voice_audio_storage=storage))

    response = client.post("/voice/tts", json={"text": "hola", "save_audio": True})

    assert response.status_code == 200
    assert response.json()["audio_path"] == "custom/path.wav"
    assert storage.calls == [(b"hello", "wav")]
