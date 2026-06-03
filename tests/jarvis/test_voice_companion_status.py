import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from fastapi.testclient import TestClient

from jarvis.api.app import create_app
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter
from jarvis.voice.companion import VoiceCompanionStatus


class DummyAdapter:
    def __init__(self):
        self.calls = 0

    def run(self, message: str, **kwargs):
        self.calls += 1
        raise AssertionError("Hermes must not be called by Voice Companion status")


def _client():
    adapter = DummyAdapter()
    app = create_app(adapter_factory=lambda: adapter)
    return TestClient(app), adapter


def _expected_status():
    return {
        "prepare_only": True,
        "voice_available": False,
        "microphone_enabled": False,
        "wake_word_enabled": False,
        "recording_enabled": False,
        "streaming_enabled": False,
        "auto_start_enabled": False,
        "execution_enabled": False,
        "approval_required_for_sensitive_actions": True,
    }


def test_voice_companion_status_is_prepare_only():
    status = VoiceCompanionStatus.placeholder()

    assert status.to_dict() == _expected_status()


def test_voice_companion_status_from_dict_forces_safe_placeholder():
    status = VoiceCompanionStatus.from_dict(
        {
            "prepare_only": False,
            "voice_available": True,
            "microphone_enabled": True,
            "wake_word_enabled": True,
            "recording_enabled": True,
            "streaming_enabled": True,
            "auto_start_enabled": True,
            "execution_enabled": True,
            "approval_required_for_sensitive_actions": False,
        }
    )

    assert status.to_dict() == _expected_status()


def test_voice_companion_status_endpoint_is_read_only_and_does_not_call_runtime_bridges(monkeypatch):
    def fail_approval(*args, **kwargs):
        raise AssertionError("ApprovalGateway must not be called by Voice Companion status")

    def fail_hermes(*args, **kwargs):
        raise AssertionError("HermesRuntimeAdapter must not be called by Voice Companion status")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail_approval)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail_hermes, raising=False)

    client, adapter = _client()
    before_tasks = client.get("/tasks")
    before_missions = client.get("/missions")

    response = client.get("/voice/companion/status")

    after_tasks = client.get("/tasks")
    after_missions = client.get("/missions")

    assert response.status_code == 200
    assert response.json() == _expected_status()
    assert before_tasks.json() == []
    assert after_tasks.json() == []
    assert before_missions.json() == []
    assert after_missions.json() == []
    assert adapter.calls == 0


def test_voice_companion_status_endpoint_has_no_post_route():
    client, _ = _client()

    response = client.post("/voice/companion/status")

    assert response.status_code == 405


def test_voice_companion_status_endpoint_does_not_open_env_file_or_expose_sensitive_routes(monkeypatch):
    opened_paths = []
    original_open = open

    def tracking_open(path, *args, **kwargs):
        opened_paths.append(str(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", tracking_open)

    client, _ = _client()
    response = client.get("/voice/companion/status")
    serialized = response.text.lower()
    routes = [route.path.lower() for route in client.app.routes]

    assert response.status_code == 200
    assert not any(path.endswith(".env") or "/.env" in path for path in opened_paths)
    for forbidden in (
        ".env",
        "api_key",
        "apikey",
        "secret",
        "token",
        "password",
        "credential",
        "authorization",
        "audio_path",
        "audio_bytes",
        "ref_audio",
        "base_url",
        "prompt_text",
    ):
        assert forbidden not in serialized
    assert "/voice/companion/status" in routes
    assert "/voice/companion/audio" not in routes
    assert "/voice/companion/record" not in routes
    assert "/voice/companion/stream" not in routes
    assert "/voice/companion/execute" not in routes
