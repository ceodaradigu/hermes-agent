import pytest

from jarvis.voice.base import VoiceSynthesisRequest
from jarvis.voice.mock_adapter import MockVoiceAdapter


def test_voice_synthesis_request_defaults():
    req = VoiceSynthesisRequest(text="hola")
    assert req.voice_id is None
    assert req.language == "es"
    assert req.output_format == "wav"
    assert req.metadata == {}


def test_mock_adapter_returns_mock_provider():
    result = MockVoiceAdapter().synthesize(VoiceSynthesisRequest(text="hola"))
    assert result.provider == "mock"


def test_mock_adapter_does_not_require_external_apis():
    adapter = MockVoiceAdapter()
    result = adapter.synthesize(VoiceSynthesisRequest(text="prueba"))
    assert result.audio_bytes
    assert result.metadata["mock"] is True


def test_empty_text_is_rejected():
    with pytest.raises(ValueError, match="text must be a non-empty string"):
        VoiceSynthesisRequest(text="")


@pytest.mark.parametrize("fmt", ["wav", "mp3", "ogg"])
def test_output_format_allowed(fmt):
    req = VoiceSynthesisRequest(text="hola", output_format=fmt)
    assert req.output_format == fmt


def test_invalid_output_format_rejected():
    with pytest.raises(ValueError, match="output_format must be one of"):
        VoiceSynthesisRequest(text="hola", output_format="flac")


def test_empty_language_rejected():
    with pytest.raises(ValueError, match="language must be a non-empty string"):
        VoiceSynthesisRequest(text="hola", language="")


def test_metadata_is_preserved():
    metadata = {"request_id": "abc123", "source": "test"}
    result = MockVoiceAdapter().synthesize(VoiceSynthesisRequest(text="hola", metadata=metadata))
    assert result.metadata["request_id"] == "abc123"
    assert result.metadata["source"] == "test"
