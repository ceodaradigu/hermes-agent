import json
import re
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import create_app
from jarvis.dashboard_event_stream import build_jarvis_event_snapshot
from jarvis.voice_runtime_pack import VOICE_RUNTIME_STATES, VoiceRuntimePack


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
JARVIS_COMPONENTS = WEB / "src/components/jarvis"
JARVIS_HOOKS = WEB / "src/hooks/jarvis"
JARVIS_PAGE = WEB / "src/pages/JarvisCommandCenterPage.tsx"
VOICE_PACK = ROOT / "jarvis/voice_runtime_pack.py"
DOC = ROOT / "docs/jarvis-pr-163-voice-runtime-pack.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _jarvis_ui_source() -> str:
    paths = [JARVIS_PAGE, WEB / "src/lib/api.ts"]
    paths.extend(sorted(JARVIS_COMPONENTS.glob("*.ts")))
    paths.extend(sorted(JARVIS_COMPONENTS.glob("*.tsx")))
    paths.extend(sorted(JARVIS_HOOKS.glob("*.ts")))
    return "\n".join(_read(path) for path in paths)


def _route(app, path: str, method: str = "GET"):
    return next(route for route in app.routes if route.path == path and method in getattr(route, "methods", set()))


def test_voice_runtime_pack_status_declares_required_state_and_security_defaults():
    status = VoiceRuntimePack().status()

    assert status["schema_version"] == "jarvis.voice_runtime_pack.v1"
    assert status["runtime_id"] == "jarvis-local-manual-voice-runtime-pack"
    assert status["mode"] == "local_manual_browser_voice_control_plane"
    assert status["enabled"] is True
    assert status["manual_push_to_talk_enabled"] is True
    assert status["current_state"] == "idle"
    assert status["supported_states"] == list(VOICE_RUNTIME_STATES)
    for state in (
        "idle",
        "listening",
        "transcribing",
        "thinking",
        "speaking",
        "cancelled",
        "stopped",
        "error",
        "approval_required",
        "wake_listening_available",
        "wake_listening_disabled",
    ):
        assert state in status["supported_states"]

    assert status["can_interrupt"] is True
    assert status["can_cancel"] is True
    assert status["raw_audio_sent_to_backend"] is False
    assert status["transcript_persistence"] is False
    assert status["voice_approval_enabled"] is False
    assert status["wake_phrase_can_approve"] is False
    assert status["wake_phrase_can_execute"] is False
    assert status["hermes_dispatch_allowed"] is False
    assert status["read_only"] is True


def test_provider_contracts_are_browser_client_side_or_disabled_local(monkeypatch):
    monkeypatch.setattr("jarvis.voice_runtime_pack._python_module_available", lambda _name: False)
    monkeypatch.setattr("jarvis.voice_runtime_pack._any_binary_available", lambda _names: False)
    status = VoiceRuntimePack().status()
    providers = status["provider_architecture"]

    browser_stt = providers["stt_providers"]["browser_speech_recognition"]
    browser_tts = providers["tts_providers"]["browser_speech_synthesis"]
    assert browser_stt["browser_client_side"] is True
    assert browser_stt["detection_location"] == "browser"
    assert browser_stt["status"] == "client_side_unknown"
    assert browser_stt["network_required"] is False
    assert browser_stt["external_provider"] is False
    assert browser_stt["raw_audio_persistence"] is False
    assert browser_tts["browser_client_side"] is True
    assert browser_tts["detection_location"] == "browser"
    assert browser_tts["status"] == "client_side_unknown"
    assert browser_tts["network_required"] is False
    assert browser_tts["external_provider"] is False

    for provider in status["local_stt_provider_status"].values():
        assert provider["enabled"] is False
        assert provider["status"] == "missing"
        assert provider["requires_model"] is True
        assert provider["model_available"] is False
        assert provider["network_required"] is False
        assert provider["external_provider"] is False
        assert provider["raw_audio_persistence"] is False

    for provider in status["local_tts_provider_status"].values():
        assert provider["enabled"] is False
        assert provider["status"] == "missing"
        assert provider["network_required"] is False
        assert provider["external_provider"] is False

    assert providers["no_provider_install_performed"] is True
    assert providers["no_model_download_performed"] is True


def test_voice_runtime_pack_endpoint_dashboard_and_events_are_read_only_and_secret_free():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    routes = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}

    assert ("/mark-3/voice-runtime/status", "GET") in routes
    assert all((method, "/mark-3/voice-runtime/status") not in {(m, p) for p, m in routes} for method in ("POST", "PUT", "DELETE"))
    status = _route(app, "/mark-3/voice-runtime/status").endpoint()
    assert status["raw_audio_sent_to_backend"] is False
    assert status["transcript_persistence"] is False
    assert status["voice_approval_enabled"] is False
    assert status["wake_phrase_can_approve"] is False
    assert status["wake_phrase_can_execute"] is False
    assert status["hermes_dispatch_allowed"] is False

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    assert dashboard["voice_runtime_pack"]["schema_version"] == "jarvis.voice_runtime_pack.v1"
    assert dashboard["voice_runtime_pack"]["raw_audio_sent_to_backend"] is False
    assert dashboard["voice_runtime_pack"]["transcript_persistence"] is False
    assert dashboard["voice_runtime_pack"]["provider_architecture"]["stt_providers"]["browser_speech_recognition"]["browser_client_side"] is True
    assert dashboard["local_doctor"]["state"]["voice_runtime_pack_endpoint"] is True
    assert dashboard["local_doctor"]["safety"]["no_voice_provider_install"] is True
    assert dashboard["local_doctor"]["safety"]["no_voice_model_download"] is True

    snapshot = build_jarvis_event_snapshot(dashboard_status=dashboard, generated_at="2026-06-19T00:00:00+00:00")
    events = {event["event_type"]: event for event in snapshot["events"]}
    assert "voice_runtime_state" in events
    assert events["voice_runtime_state"]["source"] == "/mark-3/voice-runtime/status"
    assert events["voice_runtime_state"]["payload"]["raw_audio_sent_to_backend"] is False
    assert events["voice_runtime_state"]["payload"]["transcript_persistence"] is False
    assert events["voice_runtime_state"]["payload"]["voice_approval_enabled"] is False
    assert events["voice_runtime_state"]["payload"]["wake_phrase_can_approve"] is False
    assert events["voice_runtime_state"]["payload"]["wake_phrase_can_execute"] is False
    assert events["voice_runtime_state"]["payload"]["hermes_dispatch_allowed"] is False

    serialized = json.dumps(snapshot, sort_keys=True).lower()
    for fragment in (
        "audio_bytes",
        "raw_audio_bytes",
        "frame_bytes",
        "image_bytes",
        "video_bytes",
        "password",
        "api_key",
        "private_key",
        "cookie",
        "bearer ",
        "command_to_execute",
        "execute_payload",
    ):
        assert fragment not in serialized
    assert '"can_execute": true' not in serialized
    assert '"stream_can_execute": true' not in serialized


def test_frontend_voice_loop_stop_interrupt_visual_mapping_and_credential_block_remain_safe():
    source = _jarvis_ui_source()
    loop = _read(JARVIS_HOOKS / "useLocalVoiceLoop.ts")
    shell = _read(JARVIS_COMPONENTS / "JarvisPresenceShell.tsx")
    smart_bar = _read(JARVIS_COMPONENTS / "JarvisSmartBar.tsx")
    utils = _read(JARVIS_COMPONENTS / "utils.ts")

    for marker in (
        "cancelBrowserSpeechOutput",
        "ttsQueueRef",
        "drainLocalTtsQueue",
        "isLikelyTtsEcho",
        'setLocalVoiceState("cancelled")',
        'setLocalVoiceState("stopped")',
        "canInterrupt",
        "canCancel",
        "Interrumpir voz",
        'localVoice.localVoiceState === "cancelled" || localVoice.localVoiceState === "stopped"',
    ):
        assert marker in source

    for marker in (
        '"listening"',
        '"transcribing"',
        '"thinking"',
        '"speaking"',
        '"cancelled"',
        '"stopped"',
        '"error"',
    ):
        assert marker in source

    assert "No puedo hacer eso, David. Las credenciales y secretos están protegidos." in smart_bar
    assert "No puedo hacer eso, David. Las credenciales y secretos están protegidos." in utils
    assert "speechSynthesis no está disponible" in loop
    assert "SpeechRecognition/webkitSpeechRecognition no está disponible" in loop
    assert "No se fingió escucha" in loop
    assert "speechSynthesis.cancel()" in loop
    assert "raw_audio_sent_to_backend=false" in source
    assert "transcript_persistence=false" in source
    assert "wake no aprueba" in source
    assert "wake no ejecuta" in source
    assert "provider browser/manual" in source
    assert "HermesRuntimeAdapter" not in source
    assert "AIAgent" not in source
    assert not re.search(r'fetch\([^)]*["\']/execute', source)
    assert ".getUserMedia(" not in loop
    assert ".mediaDevices.getUserMedia(" not in shell


def test_no_new_voice_runtime_dependencies_or_direct_heavy_provider_imports():
    web_package = json.loads(_read(WEB / "package.json"))
    web_deps = set(web_package.get("dependencies", {})) | set(web_package.get("devDependencies", {}))
    assert web_deps.isdisjoint(
        {
            "faster-whisper",
            "whisper.cpp",
            "piper",
            "ffmpeg",
            "sounddevice",
            "torch",
            "openwakeword",
            "@mediapipe/tasks-vision",
            "@tensorflow/tfjs",
            "react-ai-voice-visualizer",
        }
    )

    pack_source = _read(VOICE_PACK)
    for forbidden in (
        "import faster_whisper",
        "from faster_whisper",
        "import torch",
        "import sounddevice",
        "import openwakeword",
        "import piper",
        "subprocess",
        "pip install",
        "npm install",
    ):
        assert forbidden not in pack_source
    assert "importlib.util.find_spec" in pack_source
    assert "shutil.which" in pack_source


def test_documentation_for_pr_163_exists_and_declares_external_repos_and_limits():
    assert DOC.exists()
    doc = _read(DOC)
    for marker in (
        "PR #163",
        "Fase 1",
        "Voice Runtime Pack",
        "No se implemento",
        "browser_speech_recognition",
        "browser_speech_synthesis",
        "piper_local_disabled_or_missing",
        "faster_whisper_disabled_or_missing",
        "whisper_cpp_disabled_or_missing",
        "raw_audio_sent_to_backend=false",
        "transcript_persistence=false",
        "wake phrase no aprueba",
        "voice approval disabled",
        "Repos externas revisadas",
        "OpenVoiceOS/ovos-core",
        "MycroftAI/mycroft-core",
        "dscripka/openWakeWord",
        "SYSTRAN/faster-whisper",
        "openai/whisper",
        "ggml-org/whisper.cpp",
        "OHF-Voice/piper1-gpl",
        "OHF-Voice/wyoming",
        "chevgan/react-ai-voice-visualizer",
        "No se copio runtime externo",
        "Siguiente PR recomendada",
    ):
        assert marker in doc
