from __future__ import annotations

import builtins
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import CameraControlPreviewRequest, WakeVoicePreviewRequest, create_app
from jarvis.camera_control_runtime import CameraControlRuntime
from jarvis.command_center import build_command_center_view_model
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import NEXT_RECOMMENDED_MACRO_PR, build_operational_system_status
from jarvis.voice_session_control import VoiceSessionControl
from jarvis.wake_voice_runtime import VoiceCameraSafetyStatus, WakePhraseConfig, WakeVoiceRuntime


DOC = Path("docs/jarvis-post-s-local-wake-voice-camera-control.md")
DANGEROUS_ROUTES = (
    "/voice-runtime/start-microphone", "/voice-runtime/record", "/voice-runtime/stream",
    "/voice-runtime/send-audio", "/voice-runtime/execute", "/voice-runtime/run",
    "/voice-runtime/call-tool", "/voice-runtime/deploy", "/voice-runtime/pay",
    "/camera-control/start-camera", "/camera-control/record", "/camera-control/stream",
    "/camera-control/send-video", "/camera-control/analyze-face", "/camera-control/capture-screen",
    "/camera-control/watch", "/camera-control/execute",
)
MARKERS = (
    "post_s_local_wake_voice_camera_control", "wake_phrase_hola_jarvis", "wake_phrase_jarvis",
    "wake_phrase_command_parser", "wake_phrase_is_not_permission", "voice_session_control",
    "push_to_talk_fallback", "camera_opt_in_control", "visible_indicators_required",
    "audio_retention_disabled", "recording_disabled", "external_audio_disabled",
    "external_video_disabled", "microphone_inactive", "camera_inactive",
    "voice_execution_disabled", "camera_execution_disabled",
)


def _route(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route
    return None


def test_wake_config_status_and_no_phase_t_are_safe_by_default():
    config = WakePhraseConfig()
    status = WakeVoiceRuntime(config).status()
    operational = build_operational_system_status().to_dict()
    assert config.enabled is False and config.local_only is True
    assert config.wake_phrases == ["hola jarvis", "jarvis"]
    assert config.background_listening_allowed is False
    assert config.push_to_talk_fallback is True
    assert status["wake_phrases"] == ["Hola Jarvis", "Jarvis"]
    assert status["wake_phrase_is_not_permission"] is True
    assert VoiceCameraSafetyStatus().camera_control_available is True
    assert status["microphone_active"] is False
    assert operational["no_phase_t"] is True
    assert NEXT_RECOMMENDED_MACRO_PR == "Post-S Macro 7 - Monetization Engine Real"
    assert "Phase T" in DOC.read_text(encoding="utf-8")


@pytest.mark.parametrize("text,command", [
    ("Hola Jarvis", ""),
    ("Jarvis", ""),
    ("Hola Jarvis, resume el estado", "resume el estado"),
    ("Jarvis prepara la siguiente PR", "prepara la siguiente PR"),
])
def test_wake_phrase_detects_opens_and_extracts_immediate_command(text, command):
    result = WakeVoiceRuntime().parse(text)
    assert result.wake_phrase_detected is True
    assert result.extracted_command == command
    assert result.should_open_session is True
    assert result.should_answer is True


def test_normal_jarvis_word_and_low_confidence_do_not_process():
    runtime = WakeVoiceRuntime()
    normal = runtime.parse("El proyecto Jarvis está listo")
    low = runtime.parse("Jarvis despliega producción", confidence=0.2)
    assert normal.wake_phrase_detected is False
    assert low.wake_phrase_detected is True
    assert low.low_confidence is True
    assert low.should_open_session is False and low.should_answer is False
    assert low.blocked_reasons
    assert runtime.parse("Jarvis despliega producción", confidence=float("nan")).low_confidence is True


def test_voice_session_and_sensitive_command_never_execute_or_call_anything():
    control = VoiceSessionControl()
    session = control.preview_session("Jarvis despliega producción")
    decision = control.preview_command("despliega producción")
    safe = control.preview_command("resume el estado del proyecto")
    assert session.state == "active_session"
    assert session.action_allowed is False
    assert decision.action_allowed is False
    assert decision.approval_required is True
    assert decision.strong_approval_required is True
    assert decision.controlled_runtime_required is True
    assert decision.tool_gate_required is True
    for field in ("would_execute", "would_call_tools", "would_call_external", "would_record_audio"):
        assert getattr(decision, field) is False
    assert safe.strong_approval_required is False
    assert control.preview_session("Hola Jarvis").response_preview == "Estoy escuchando."


@pytest.mark.parametrize("phrase", ["no escuches", "para", "cállate"])
def test_voice_stop_phrases_stop_session(phrase):
    stopped = VoiceSessionControl().preview_stop(phrase)
    assert stopped.state == "stopped"
    assert stopped.stopped_by_phrase == phrase


def test_camera_requires_opt_in_and_never_records_analyzes_or_captures():
    runtime = CameraControlRuntime()
    status = runtime.status()
    blocked = runtime.preview_session()
    opted_in = runtime.preview_session(
        opt_in_present=True,
        visible_indicator_ready=True,
        recording_requested=True,
        analyze_people_requested=True,
        screen_capture_requested=True,
        external_video_requested=True,
    )
    assert status["camera_session_active"] is False
    assert status["camera_opt_in_required"] is True
    assert status["visible_indicator_required"] is True
    assert status["recording_enabled"] is False
    assert status["external_video_processing_enabled"] is False
    assert status["face_person_analysis_enabled"] is False
    assert status["screen_capture_enabled"] is False
    assert "explicit camera opt-in is required" in blocked.blocked_reasons
    assert opted_in.strong_approval_required is True
    for field in ("would_start_camera", "would_record", "would_analyze_people", "would_capture_screen"):
        assert getattr(opted_in, field) is False
    assert runtime.preview_stop("no mires").last_session_summary == "camera stop preview accepted"


def test_api_routes_are_preview_only_absent_dangerous_and_do_not_mutate_or_call_external(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("network called"))
    original_open = builtins.open

    def guarded_open(file, *args, **kwargs):
        if str(file).endswith(".env"):
            pytest.fail(".env read")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    missions_before = app.state.mission_control.list_missions()
    tasks_before = app.state.task_store.list()

    assert _route(app, "/voice-runtime/status", "GET").endpoint()["microphone_active"] is False
    assert _route(app, "/voice-runtime/policy", "GET").endpoint()["no_recording"] is True
    wake = WakeVoicePreviewRequest(text="Hola Jarvis, resume el estado")
    assert _route(app, "/voice-runtime/preview-wake-parse", "POST").endpoint(wake)["extracted_command"] == "resume el estado"
    assert _route(app, "/voice-runtime/preview-session", "POST").endpoint(wake)["execution_enabled"] is False
    assert _route(app, "/voice-runtime/preview-command", "POST").endpoint(wake)["would_execute"] is False
    assert _route(app, "/voice-runtime/preview-stop", "POST").endpoint(WakeVoicePreviewRequest(text="para"))["state"] == "stopped"
    assert _route(app, "/camera-control/status", "GET").endpoint()["camera_session_active"] is False
    assert _route(app, "/camera-control/policy", "GET").endpoint()["no_external_video"] is True
    camera = CameraControlPreviewRequest(opt_in_present=True, visible_indicator_ready=True)
    assert _route(app, "/camera-control/preview-session", "POST").endpoint(camera)["would_start_camera"] is False
    stop = CameraControlPreviewRequest(phrase="no mires")
    assert _route(app, "/camera-control/preview-stop", "POST").endpoint(stop)["camera_session_active"] is False
    assert app.state.mission_control.list_missions() == missions_before == []
    assert app.state.task_store.list() == tasks_before == []
    for path in DANGEROUS_ROUTES:
        assert _route(app, path, "GET") is None
        assert _route(app, path, "POST") is None


def test_operational_command_center_and_operator_console_expose_macro_6_markers():
    operational = build_operational_system_status().to_dict()
    command = build_command_center_view_model(view_id="macro-6", generated_at="2026-06-11T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="macro-6", generated_at="2026-06-11T00:00:00+00:00")
    assert operational["wake_voice_runtime_available"] is True
    assert operational["wake_phrases_supported"] == ["Hola Jarvis", "Jarvis"]
    assert operational["camera_active"] is False
    assert operational["voice_execution_enabled"] is False
    for marker in MARKERS:
        assert command.metadata[marker] == "prepare_only"
        assert operator.metadata[marker] == "prepare_only"
