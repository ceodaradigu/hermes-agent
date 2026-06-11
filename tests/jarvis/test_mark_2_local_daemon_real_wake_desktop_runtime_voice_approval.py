from __future__ import annotations

import builtins
import socket
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import Mark2VoiceApprovalRequest, WakeVoicePreviewRequest, create_app
from jarvis.command_center import build_command_center_view_model
from jarvis.desktop_runtime import DesktopRuntime, DesktopRuntimeState
from jarvis.local_daemon import LocalDaemonControl, LocalDaemonStatus
from jarvis.local_runtime_safety import LocalRuntimeSafetyPolicy
from jarvis.mark_1_release_candidate import Mark1ReleaseCandidateStatus
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import build_operational_console_summary, build_operational_system_status
from jarvis.real_wake_listener import RealWakeListener, RealWakeListenerPlan
from jarvis.voice_approval_channel import EXACT_CRITICAL_PHRASE, VoiceApprovalChannel, mark_2_macro_1_markers


DOC = Path("docs/jarvis-mark-2-local-daemon-real-wake-desktop-runtime-voice-approval.md")
SAFE_ROUTES = (
    ("GET", "/mark-2/local-daemon/status"), ("GET", "/mark-2/desktop-runtime/status"),
    ("GET", "/mark-2/local-runtime/safety-policy"), ("GET", "/mark-2/wake-listener/status"),
    ("POST", "/mark-2/wake-listener/preview-transcript"), ("GET", "/mark-2/voice-approval/status"),
    ("POST", "/mark-2/voice-approval/preview-start"), ("POST", "/mark-2/voice-approval/preview-confirm"),
    ("POST", "/mark-2/voice-approval/preview-flow"), ("GET", "/mark-2/local-daemon/command-preview"),
    ("GET", "/mark-2/local-audit/preview"),
)
DANGEROUS_ROUTES = (
    "/mark-2/local-daemon/start-real", "/mark-2/local-daemon/install-service",
    "/mark-2/wake-listener/start-microphone", "/mark-2/wake-listener/record", "/mark-2/wake-listener/stream",
    "/mark-2/voice-approval/approve-all", "/mark-2/voice-approval/auto-approve", "/mark-2/execute",
    "/mark-2/deploy", "/mark-2/pay", "/mark-2/charge", "/mark-2/publish", "/mark-2/create-repo", "/mark-2/write-files",
)


def _route(app, path, method):
    return next((route for route in app.routes if route.path == path and method in route.methods), None)


def test_local_daemon_desktop_and_safety_defaults_are_safe():
    daemon = LocalDaemonStatus().to_dict()
    desktop = DesktopRuntime().status().to_dict()
    policy = LocalRuntimeSafetyPolicy().to_dict()
    assert daemon["current_mark"] == "Mark 2" and daemon["mark_2_macro"] == "Mark 2 Macro 1"
    assert daemon["local_daemon_available"] is True
    for name in ("local_daemon_enabled", "local_daemon_running", "auto_start_enabled", "install_as_service_enabled", "external_network_enabled", "secrets_access_enabled", "filesystem_external_write_enabled"):
        assert daemon[name] is False
    assert daemon["daemon_pid"] is None and daemon["daemon_lock_present"] is False
    assert daemon["kill_switch_available"] is True and daemon["stop_phrase_available"] is True
    assert daemon["voice_can_approve"] is True and daemon["wake_phrase_is_permission"] is False
    assert desktop["desktop_runtime_available"] is True and desktop["runtime_mode"] == "disabled"
    assert desktop["visible_status_required"] is True and desktop["microphone_state"] == "opt_in_required"
    assert desktop["no_background_execution_without_state"] is True
    assert policy["default_disabled"] is True and policy["microphone_requires_opt_in"] is True
    assert policy["voice_approval_requires_readback"] is True
    assert policy["wake_phrase_never_grants_permission"] is True
    assert policy["critical_actions_require_double_confirmation"] is True


def test_desktop_runtime_rejects_invisible_listening_and_critical_execution():
    with pytest.raises(ValueError, match="visible"):
        DesktopRuntimeState(runtime_mode="listening", visible_status_required=False, current_visible_status="")
    with pytest.raises(ValueError, match="critical execution"):
        DesktopRuntime().preview_transition("executing", critical_action=True, valid_voice_approval_present=True)
    eligible_preview = DesktopRuntime().preview_transition(
        "executing",
        critical_action=True,
        current_mode="awaiting_approval",
        valid_voice_approval_present=True,
    )
    assert eligible_preview.runtime_mode == "executing"
    assert eligible_preview.execution_enabled is False


def test_real_wake_listener_plan_and_transcripts_never_grant_permission():
    plan = RealWakeListenerPlan().to_dict()
    wake_only = RealWakeListener().preview_transcript("Hola Jarvis")
    command = RealWakeListener().preview_transcript("Jarvis, despliega producción")
    assert plan["real_wake_listener_available"] is True and plan["wake_listener_enabled"] is False
    assert plan["microphone_opt_in_present"] is False
    assert plan["supported_wake_phrases"] == ["Hola Jarvis", "Jarvis"]
    assert plan["wake_phrase_is_permission"] is False and plan["wake_phrase_starts_session"] is True
    for name in ("audio_recording_enabled", "audio_streaming_enabled", "external_speech_api_enabled"):
        assert plan[name] is False
    assert plan["no_microphone_access_in_tests"] is True
    assert wake_only["session_started"] is True and wake_only["approval_granted"] is False
    assert command["command_extracted"] is True and command["approval_required"] is True
    assert command["approval_flow_started"] is True and command["would_execute"] is False


def test_voice_approval_critical_flow_requires_readback_exact_phrase_and_double_confirmation():
    channel = VoiceApprovalChannel()
    state = channel.start(action="deploy production", cost_summary="review required", production_impact_summary="production changes", rollback_or_stop_plan_summary="restore prior release")
    assert channel.status()["voice_approval_enabled"] is False
    assert state.action_risk_level == "critical" and state.readback_text
    assert state.confirmation_steps_required == 2
    assert channel.confirm(state.approval_id, "sí").valid_voice_approval_present is False
    assert channel.confirm(state.approval_id, "JARVIS hazlo").valid_voice_approval_present is False
    assert channel.confirm(state.approval_id, "sí, continúa").confirmation_steps_completed == 1
    final = channel.confirm(state.approval_id, EXACT_CRITICAL_PHRASE)
    assert final.strong_approval_satisfied is True and final.double_confirmation_satisfied is True
    assert final.valid_voice_approval_present is True and final.eligible_after_valid_voice_approval is True
    assert final.would_execute is False
    cannot_downgrade = channel.start(action="deploy production", risk_level="low")
    assert cannot_downgrade.action_risk_level == "critical"
    redacted = channel.start(action="deploy production with secret token")
    assert "secret" not in redacted.pending_action
    assert "token" not in redacted.readback_text
    assert channel.confirm(final.approval_id, EXACT_CRITICAL_PHRASE).valid_voice_approval_present is True


def test_voice_approval_stripe_triple_unclear_wrong_and_expired_flows():
    channel = VoiceApprovalChannel()
    triple = channel.start(action="Stripe live payment", require_triple_confirmation=True)
    assert triple.action_risk_level == "critical" and triple.confirmation_steps_required == 3
    for phrase in ("sí, continúa", EXACT_CRITICAL_PHRASE, "JARVIS, confirmación final."):
        triple = channel.confirm(triple.approval_id, phrase)
    assert triple.triple_confirmation_satisfied is True and triple.valid_voice_approval_present is True
    unclear = channel.start(action="deploy production")
    for _ in range(3):
        channel.confirm(unclear.approval_id, "ruido")
    assert unclear.cancelled is True
    assert channel.confirm(unclear.approval_id, "sí, continúa").valid_voice_approval_present is False
    wrong = channel.start(action="deploy production")
    assert channel.confirm(wrong.approval_id, "frase incorrecta").valid_voice_approval_present is False
    expired = channel.start(action="deploy production")
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    assert channel.confirm(expired.approval_id, "sí, continúa", now=future).valid_voice_approval_present is False
    assert expired.expired is True

    high = channel.start(action="review local change", risk_level="high")
    assert high.action_risk_level == "high"
    channel.confirm(high.approval_id, "sí, continúa")
    assert channel.confirm(high.approval_id, "JARVIS hazlo").valid_voice_approval_present is True


def test_local_audit_and_command_previews_are_safe():
    channel = VoiceApprovalChannel()
    state = channel.start(action="deploy production", cost_summary="cost summary", production_impact_summary="impact summary", rollback_or_stop_plan_summary="rollback summary")
    channel.confirm(state.approval_id, "sí, continúa")
    event = state.audit_event_preview[-1]
    assert event["raw_audio_stored"] is False and event["secrets_redacted"] is True
    assert event["confirmation_phrase_hash_or_redacted"].startswith("sha256:")
    assert event["cost_summary"] == "cost summary" and event["rollback_or_stop_plan_summary"] == "rollback summary"
    for command in LocalDaemonControl.COMMANDS:
        preview = LocalDaemonControl().preview_command(command).to_dict()
        for name in ("would_start_process", "would_access_microphone", "would_modify_system_service", "would_write_outside_repo"):
            assert preview[name] is False


def test_mark_2_endpoints_are_safe_and_dangerous_routes_absent(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("network called"))
    monkeypatch.setattr(Path, "write_text", lambda *a, **k: pytest.fail("filesystem write"))
    original_open = builtins.open
    monkeypatch.setattr(builtins, "open", lambda file, *a, **k: pytest.fail(".env read") if str(file).endswith(".env") else original_open(file, *a, **k))
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    for method, path in SAFE_ROUTES:
        route = _route(app, path, method)
        assert route is not None
        if path == "/mark-2/wake-listener/preview-transcript":
            payload = route.endpoint(WakeVoicePreviewRequest(text="Hola Jarvis"))
        elif path == "/mark-2/voice-approval/preview-start":
            payload = route.endpoint(Mark2VoiceApprovalRequest(action="deploy production"))
        elif path == "/mark-2/voice-approval/preview-confirm":
            state = app.state.voice_approval_channel.start(action="deploy production")
            payload = route.endpoint(Mark2VoiceApprovalRequest(approval_id=state.approval_id, phrase="sí, continúa"))
        elif path == "/mark-2/voice-approval/preview-flow":
            payload = route.endpoint(Mark2VoiceApprovalRequest(action="deploy production", phrases=["sí, continúa", EXACT_CRITICAL_PHRASE]))
        else:
            payload = route.endpoint()
        assert isinstance(payload, dict)
    for path in DANGEROUS_ROUTES:
        assert _route(app, path, "GET") is None and _route(app, path, "POST") is None


def test_operational_command_center_operator_console_and_mark_1_reflect_macro():
    markers = mark_2_macro_1_markers()
    operational = build_operational_system_status().to_dict()
    summary = build_operational_console_summary()
    command = build_command_center_view_model(view_id="mark-2", generated_at="2026-06-11T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="mark-2", generated_at="2026-06-11T00:00:00+00:00")
    assert Mark1ReleaseCandidateStatus().mark_1_ready is True
    assert summary["mark_2_next_recommended_macro_pr"].startswith("Mark 2 Macro 2")
    for marker, expected in markers.items():
        assert operational[marker] == expected
        assert marker in summary["command_center"]
        assert marker in command.metadata
        assert marker in operator.metadata


def test_mark_2_documentation_exists_and_states_safety_boundary():
    content = DOC.read_text(encoding="utf-8")
    for text in ("Mark 2 Macro 1", "La voz puede aprobar", "wake phrase no puede aprobar", "Hola Jarvis", "JARVIS, entiendo los riesgos, hazlo", "audio bruto", "Mark 2 Macro 2"):
        assert text in content
