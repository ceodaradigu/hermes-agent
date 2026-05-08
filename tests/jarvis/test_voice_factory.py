import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api import app as api_app
from jarvis.api.app import create_app
from jarvis.voice import GPTSoVITSAdapter, MockVoiceAdapter, create_voice_adapter_from_env


def test_factory_without_env_returns_mock():
    adapter = create_voice_adapter_from_env({})
    assert isinstance(adapter, MockVoiceAdapter)


def test_factory_mock_provider_returns_mock():
    adapter = create_voice_adapter_from_env({"JARVIS_VOICE_PROVIDER": "mock"})
    assert isinstance(adapter, MockVoiceAdapter)


def test_factory_gpt_sovits_provider_returns_gpt_sovits():
    adapter = create_voice_adapter_from_env({"JARVIS_VOICE_PROVIDER": "gpt-sovits"})
    assert isinstance(adapter, GPTSoVITSAdapter)


def test_factory_gpt_sovits_reads_base_url_from_env():
    adapter = create_voice_adapter_from_env(
        {"JARVIS_VOICE_PROVIDER": "gpt-sovits", "JARVIS_GPT_SOVITS_BASE_URL": "http://localhost:9999"}
    )
    assert adapter.base_url == "http://localhost:9999"


def test_factory_gpt_sovits_reads_ref_audio_path_from_env():
    adapter = create_voice_adapter_from_env(
        {"JARVIS_VOICE_PROVIDER": "gpt-sovits", "JARVIS_GPT_SOVITS_REF_AUDIO_PATH": "/tmp/ref.wav"}
    )
    assert adapter.ref_audio_path == "/tmp/ref.wav"


def test_factory_gpt_sovits_reads_prompt_text_from_env():
    adapter = create_voice_adapter_from_env(
        {"JARVIS_VOICE_PROVIDER": "gpt-sovits", "JARVIS_GPT_SOVITS_PROMPT_TEXT": "hola prompt"}
    )
    assert adapter.prompt_text == "hola prompt"


def test_factory_gpt_sovits_reads_prompt_lang_from_env():
    adapter = create_voice_adapter_from_env(
        {"JARVIS_VOICE_PROVIDER": "gpt-sovits", "JARVIS_GPT_SOVITS_PROMPT_LANG": "en"}
    )
    assert adapter.prompt_lang == "en"


def test_factory_gpt_sovits_reads_timeout_seconds_from_env():
    adapter = create_voice_adapter_from_env(
        {"JARVIS_VOICE_PROVIDER": "gpt-sovits", "JARVIS_GPT_SOVITS_TIMEOUT_SECONDS": "12.5"}
    )
    assert adapter.timeout_seconds == 12.5


def test_factory_unknown_provider_raises_value_error():
    with pytest.raises(ValueError, match="Unknown JARVIS_VOICE_PROVIDER"):
        create_voice_adapter_from_env({"JARVIS_VOICE_PROVIDER": "invalid"})


def test_factory_invalid_timeout_raises_value_error():
    with pytest.raises(ValueError, match="JARVIS_GPT_SOVITS_TIMEOUT_SECONDS"):
        create_voice_adapter_from_env(
            {"JARVIS_VOICE_PROVIDER": "gpt-sovits", "JARVIS_GPT_SOVITS_TIMEOUT_SECONDS": "oops"}
        )


def test_factory_does_not_make_network_calls():
    adapter = create_voice_adapter_from_env({"JARVIS_VOICE_PROVIDER": "gpt-sovits"})
    assert isinstance(adapter, GPTSoVITSAdapter)


def test_create_app_uses_factory_when_voice_adapter_not_injected(monkeypatch):
    marker = MockVoiceAdapter()

    def fake_factory(env=None):
        return marker

    monkeypatch.setattr(api_app, "create_voice_adapter_from_env", fake_factory)
    app = create_app()

    assert app.state.voice_adapter is marker


def test_create_app_respects_injected_voice_adapter(monkeypatch):
    injected = MockVoiceAdapter()

    def fail_factory(env=None):
        raise AssertionError("factory should not be used when voice_adapter is injected")

    monkeypatch.setattr(api_app, "create_voice_adapter_from_env", fail_factory)

    app = create_app(voice_adapter=injected)
    client = TestClient(app)

    response = client.post("/voice/tts", json={"text": "hola"})

    assert response.status_code == 200
    assert app.state.voice_adapter is injected
