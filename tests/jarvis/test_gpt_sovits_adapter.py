import pytest

from jarvis.voice.base import VoiceSynthesisRequest
from jarvis.voice.gpt_sovits_adapter import GPTSoVITSAdapter


class FakeHTTPClient:
    def __init__(self, *, status=200, headers=None, body=b"AUDIO", error=None):
        self.status = status
        self.headers = headers if headers is not None else {"Content-Type": "audio/wav"}
        self.body = body
        self.error = error
        self.calls = []

    def post(self, url, json_payload, timeout):
        self.calls.append({"url": url, "json_payload": json_payload, "timeout": timeout})
        if self.error:
            raise self.error
        return self.status, self.headers, self.body


def test_builds_payload_and_uses_tts_url():
    client = FakeHTTPClient()
    adapter = GPTSoVITSAdapter(
        base_url="http://127.0.0.1:9880",
        ref_audio_path="/tmp/ref.wav",
        prompt_text="hola prompt",
        prompt_lang="es",
        timeout_seconds=12.5,
        http_client=client,
    )
    request = VoiceSynthesisRequest(text="hola", language="es", output_format="wav")

    result = adapter.synthesize(request)

    assert client.calls[0]["url"] == "http://127.0.0.1:9880/tts"
    assert client.calls[0]["timeout"] == 12.5
    assert client.calls[0]["json_payload"] == {
        "text": "hola",
        "text_lang": "es",
        "ref_audio_path": "/tmp/ref.wav",
        "prompt_text": "hola prompt",
        "prompt_lang": "es",
        "media_type": "wav",
        "streaming_mode": False,
    }
    assert result.provider == "gpt-sovits"


def test_returns_result_and_preserves_metadata():
    client = FakeHTTPClient(headers={"Content-Type": "audio/ogg"}, body=b"OGG")
    adapter = GPTSoVITSAdapter(ref_audio_path="/tmp/ref.wav", http_client=client)
    request = VoiceSynthesisRequest(text="hola", output_format="ogg", metadata={"trace_id": "abc"})

    result = adapter.synthesize(request)

    assert result.provider == "gpt-sovits"
    assert result.audio_bytes == b"OGG"
    assert result.content_type == "audio/ogg"
    assert result.metadata["trace_id"] == "abc"
    assert result.metadata["base_url"] == "http://127.0.0.1:9880"
    assert result.metadata["ref_audio_path"] == "/tmp/ref.wav"
    assert result.metadata["prompt_lang"] == "es"


def test_ref_audio_path_can_come_from_request_metadata():
    client = FakeHTTPClient()
    adapter = GPTSoVITSAdapter(http_client=client)
    request = VoiceSynthesisRequest(text="hola", metadata={"ref_audio_path": "/tmp/from-metadata.wav"})

    adapter.synthesize(request)

    assert client.calls[0]["json_payload"]["ref_audio_path"] == "/tmp/from-metadata.wav"


def test_error_when_ref_audio_path_missing():
    adapter = GPTSoVITSAdapter(http_client=FakeHTTPClient())
    request = VoiceSynthesisRequest(text="hola")

    with pytest.raises(ValueError, match="ref_audio_path is required"):
        adapter.synthesize(request)


def test_error_when_base_url_empty():
    adapter = GPTSoVITSAdapter(base_url="", ref_audio_path="/tmp/ref.wav", http_client=FakeHTTPClient())

    with pytest.raises(ValueError, match="base_url must be a non-empty string"):
        adapter.synthesize(VoiceSynthesisRequest(text="hola"))


def test_error_when_prompt_lang_empty():
    adapter = GPTSoVITSAdapter(prompt_lang="", ref_audio_path="/tmp/ref.wav", http_client=FakeHTTPClient())

    with pytest.raises(ValueError, match="prompt_lang must be a non-empty string"):
        adapter.synthesize(VoiceSynthesisRequest(text="hola"))


def test_http_400_error_includes_service_message():
    client = FakeHTTPClient(status=400, body=b'{"message":"bad request from service"}')
    adapter = GPTSoVITSAdapter(ref_audio_path="/tmp/ref.wav", http_client=client)

    with pytest.raises(RuntimeError, match="bad request from service"):
        adapter.synthesize(VoiceSynthesisRequest(text="hola"))


@pytest.mark.parametrize("exc", [TimeoutError("timeout"), OSError("connection refused")])
def test_connection_errors_are_wrapped(exc):
    client = FakeHTTPClient(error=exc)
    adapter = GPTSoVITSAdapter(ref_audio_path="/tmp/ref.wav", http_client=client)

    with pytest.raises(RuntimeError, match="Failed to connect to GPT-SoVITS service"):
        adapter.synthesize(VoiceSynthesisRequest(text="hola"))
