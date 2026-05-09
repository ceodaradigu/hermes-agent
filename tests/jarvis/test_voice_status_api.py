import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import create_app
from jarvis.voice.base import VoiceSynthesisRequest, VoiceSynthesisResult
from jarvis.voice.gpt_sovits_adapter import GPTSoVITSAdapter


class NoNetworkHTTPClient:
    def post(self, *args, **kwargs):
        raise AssertionError("network call attempted")


class UnknownVoiceAdapter:
    def synthesize(self, request):
        return VoiceSynthesisResult(content_type="audio/wav", provider="unknown", audio_bytes=b"x", metadata={})


def _client(**kwargs):
    return TestClient(create_app(**kwargs))


def test_voice_status_default_mock_provider():
    client = _client()

    response = client.get("/voice/status")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["configured"] is True
    assert data["can_synthesize"] is True


def test_voice_status_gpt_sovits_with_ref_audio_can_synthesize_true():
    adapter = GPTSoVITSAdapter(
        base_url="http://127.0.0.1:9880",
        ref_audio_path="/tmp/ref.wav",
        prompt_text="texto secreto",
        prompt_lang="es",
        timeout_seconds=12.5,
        http_client=NoNetworkHTTPClient(),
    )
    client = _client(voice_adapter=adapter)

    response = client.get("/voice/status")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "gpt-sovits"
    assert data["configured"] is True
    assert data["can_synthesize"] is True
    assert data["details"]["has_ref_audio_path"] is True
    assert data["details"]["has_prompt_text"] is True
    assert data["details"]["prompt_lang"] == "es"
    assert data["details"]["timeout_seconds"] == 12.5
    assert data["details"]["base_url"] == "http://127.0.0.1:9880"
    assert "ref_audio_path" not in data["details"]
    assert "prompt_text" not in data["details"]


def test_voice_status_gpt_sovits_without_ref_audio_cannot_synthesize():
    adapter = GPTSoVITSAdapter(base_url="http://127.0.0.1:9880", ref_audio_path=None, http_client=NoNetworkHTTPClient())
    client = _client(voice_adapter=adapter)

    response = client.get("/voice/status")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "gpt-sovits"
    assert data["configured"] is True
    assert data["can_synthesize"] is False
    assert data["details"]["has_ref_audio_path"] is False


def test_voice_status_unknown_adapter_returns_unknown():
    client = _client(voice_adapter=UnknownVoiceAdapter())

    response = client.get("/voice/status")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "unknown"
    assert data["configured"] is False
    assert data["can_synthesize"] is False
    assert data["details"]["class_name"] == "UnknownVoiceAdapter"


def test_voice_status_does_not_make_network_calls():
    adapter = GPTSoVITSAdapter(base_url="http://127.0.0.1:9880", ref_audio_path="/tmp/ref.wav", http_client=NoNetworkHTTPClient())
    client = _client(voice_adapter=adapter)

    response = client.get("/voice/status")

    assert response.status_code == 200


def test_voice_tts_still_works_with_status_endpoint_present():
    client = _client()

    response = client.post("/voice/tts", json={"text": "hola mundo"})

    assert response.status_code == 200
    assert response.json()["provider"] == "mock"
