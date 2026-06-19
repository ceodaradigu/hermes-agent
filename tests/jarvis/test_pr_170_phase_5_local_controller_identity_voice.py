from dataclasses import replace
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi import HTTPException

from jarvis.api.app import (
    Mark3ExecutionPreviewRequest,
    Mark3ExecutionRequestApprovalRequest,
    Mark3LocalControllerKillSwitchRequest,
    Mark3LocalControllerOptInRequest,
    Mark3LocalControllerRegisterRequest,
    Mark3LocalControllerStartRequest,
    Mark3LocalPairingChallengeRequest,
    Mark3LocalPairingVerifyRequest,
    Mark3RemotePairingRevokeRequest,
    Mark3TrustedApprovalChannelVerifyRequest,
    Mark3TrustedApprovalDecisionRequest,
    Mark3TrustedDeviceImportPreviewRequest,
    Mark3VoiceApprovalDecisionRequest,
    Mark3VoiceApprovalStartRequest,
    create_app,
)
from jarvis.memory_brain_v2 import MemoryBrainV2Store
from jarvis.persistent_audit import PersistentAuditLedger
from jarvis.phase_2_local_assistant_runtime import ACTION_CATALOG
from jarvis.phase_4_local_controller_remote_pairing import (
    LOCAL_CONTROLLER_VERIFICATION_PHRASE,
    TERMINAL_VERIFICATION_PHRASE,
)


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


class FakeHermesReadAdapter:
    def __init__(self, calls):
        self.calls = calls
        self.interruptions = []

    def run(self, message, **kwargs):
        self.calls.append({"message": message, "kwargs": kwargs})
        return {"success": True, "completed": True}

    def interrupt(self, reason):
        self.interruptions.append(reason)
        return True


def _make_app(tmp_path, monkeypatch):
    state_dir = tmp_path / "state"
    monkeypatch.setenv("JARVIS_LOCAL_STATE_DIR", str(state_dir))
    ledger = PersistentAuditLedger(base_dir=state_dir)
    memory = MemoryBrainV2Store(base_dir=state_dir, audit_ledger=ledger)
    calls = []

    app = create_app(
        adapter_factory=lambda: pytest.fail("legacy Hermes adapter must not be called"),
        hermes_runtime_adapter_factory=lambda _guard: FakeHermesReadAdapter(calls),
        persistent_audit_ledger=ledger,
        memory_brain_v2=memory,
    )
    return app, ledger, calls, state_dir


def _route(app, path, method="GET"):
    return next(route for route in app.routes if route.path == path and method in getattr(route, "methods", set()))


def _preview(app, **payload):
    return _route(app, "/mark-3/execution/preview", "POST").endpoint(Mark3ExecutionPreviewRequest(**payload))


def _request_approval(app, preview_id, actor="David"):
    return _route(app, "/mark-3/execution/request-approval", "POST").endpoint(
        Mark3ExecutionRequestApprovalRequest(preview_id=preview_id, actor=actor)
    )


def _pair_voice_device(app, *, public_identifier="phase5-phone-public", scope=None):
    scope = scope or ["voice_approval", "normal", "strong"]
    challenge = _route(app, "/mark-3/local-pairing/challenge", "POST").endpoint(
        Mark3LocalPairingChallengeRequest(
            display_name="David phone",
            public_identifier=public_identifier,
            channel="local_voice_device",
            scope=scope,
        )
    )
    return _route(app, "/mark-3/local-pairing/verify", "POST").endpoint(
        Mark3LocalPairingVerifyRequest(
            challenge_id=challenge["challenge_id"],
            nonce=challenge["nonce"],
            response_phrase=challenge["challenge_phrase"],
            public_identifier=public_identifier,
            display_name="David phone",
            scope=scope,
        )
    )


def _verify_terminal(app):
    return _route(app, "/mark-3/trusted-approval-channels/verify", "POST").endpoint(
        Mark3TrustedApprovalChannelVerifyRequest(
            channel_id="terminal_local",
            challenge_response=TERMINAL_VERIFICATION_PHRASE,
        )
    )


def _register_controller(app, controller_id="ctrl-phase5"):
    return _route(app, "/mark-3/local-controller/register", "POST").endpoint(
        Mark3LocalControllerRegisterRequest(
            controller_id=controller_id,
            display_name="Phase 5 Local Controller",
            verification_phrase=LOCAL_CONTROLLER_VERIFICATION_PHRASE,
        )
    )


def _triple_decide(app, **payload):
    return _route(app, "/mark-3/approval/triple-decision", "POST").endpoint(
        Mark3TrustedApprovalDecisionRequest(**payload)
    )


def _event_types(ledger):
    return {entry["event_type"] for entry in ledger.list_entries(limit=400)}


def _frontend_source():
    paths = [
        WEB / "src/lib/api.ts",
        WEB / "src/components/jarvis/JarvisDebugDrawer.tsx",
        WEB / "src/components/jarvis/contracts.ts",
        WEB / "src/components/jarvis/types.ts",
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_phase_5_routes_local_controller_and_dashboard_readiness(tmp_path, monkeypatch):
    app, ledger, calls, _state_dir = _make_app(tmp_path, monkeypatch)
    route_paths = {route.path for route in app.routes}

    assert "/execute" not in route_paths
    assert "/jarvis/execute" not in route_paths
    for path in (
        "/mark-3/phase-5/status",
        "/mark-3/local-controller/opt-in",
        "/mark-3/local-controller/start-request",
        "/mark-3/local-controller/kill-switch",
        "/mark-3/trusted-devices/import-preview",
        "/mark-3/local-pairing/status",
        "/mark-3/local-pairing/challenge",
        "/mark-3/local-pairing/verify",
        "/mark-3/voice-approval/status",
        "/mark-3/voice-approval/start",
        "/mark-3/voice-approval/decision",
        "/mark-3/notifications/status",
    ):
        assert path in route_paths

    phase5 = _route(app, "/mark-3/phase-5/status").endpoint()
    assert phase5["security_gates"]["jarvis_governs"] is True
    assert phase5["security_gates"]["frontend_can_execute_hermes_directly"] is False
    assert phase5["security_gates"]["wake_phrase_can_approve"] is False
    assert phase5["security_gates"]["raw_audio_stored_by_default"] is False
    assert phase5["local_controller"]["local_only"] is True
    assert phase5["local_controller"]["auto_start_enabled"] is False
    assert phase5["local_controller"]["external_exposure"] is False
    assert phase5["local_controller"]["hidden_background_behavior"] is False
    assert phase5["local_controller"]["native_tray_status"] == "readiness_only_not_installed"

    opted = _route(app, "/mark-3/local-controller/opt-in", "POST").endpoint(
        Mark3LocalControllerOptInRequest(enabled=True, reason="manual test")
    )
    assert opted["status"] == "opted_in"
    started = _route(app, "/mark-3/local-controller/start-request", "POST").endpoint(
        Mark3LocalControllerStartRequest(reason="manual test")
    )
    assert started["request_status"] == "recorded_not_started"
    assert started["started_process"] is False
    killed = _route(app, "/mark-3/local-controller/kill-switch", "POST").endpoint(
        Mark3LocalControllerKillSwitchRequest(enabled=True, reason="manual test")
    )
    assert killed["kill_switch"] == "enabled"

    preview = _route(app, "/mark-3/trusted-devices/import-preview", "POST").endpoint(
        Mark3TrustedDeviceImportPreviewRequest(device_id="claimed-phone", trusted=True, verified=True, paired=True)
    )
    assert preview["import_status"] == "rejected_preview_only"
    assert preview["trusted"] is False
    assert preview["hermes_dispatch_allowed"] is False

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    assert dashboard["phase_5_status"]["source_endpoint"] == "/mark-3/phase-5/status"
    modules = {module["name"] for module in dashboard["modules"]}
    assert {"Phase 5 Trust", "Local Pairing", "Voice Approval", "Notifications"} <= modules

    snapshot = _route(app, "/mark-3/dashboard/events").endpoint()
    event_types = {event["event_type"] for event in snapshot["events"]}
    assert {"phase_5_state", "local_pairing_state", "voice_approval_state", "notification_state"} <= event_types
    assert snapshot["stream"]["no_raw_audio"] is True

    source = _frontend_source()
    for expected in (
        "/mark-3/phase-5/status",
        "/mark-3/local-pairing/status",
        "/mark-3/voice-approval/status",
        "/mark-3/notifications/status",
        "jarvis-phase-5-status",
        "jarvis-phase-5-trusted-devices",
        "jarvis-local-pairing-status",
        "jarvis-voice-approval-contract",
        "jarvis-notification-readiness",
        "JARVIS, autorizo",
    ):
        assert expected in source
    assert 'fetchJSON("/execute"' not in source
    assert 'fetchJSON("/jarvis/execute"' not in source
    assert "dispatchHermes" not in source
    assert calls == []
    assert {"local_controller_opt_in_changed", "local_controller_start_requested", "local_controller_kill_switch_changed", "trusted_device_import_rejected"} <= _event_types(ledger)


def test_local_pairing_one_time_rate_limit_persistence_and_revoke(tmp_path, monkeypatch):
    app, ledger, calls, state_dir = _make_app(tmp_path, monkeypatch)
    paired = _pair_voice_device(app, public_identifier="phone-one")
    assert paired["pairing_status"] == "trusted_device_bound"
    assert paired["one_time_use_consumed"] is True
    assert paired["remote_execution_allowed"] is False
    assert paired["device"]["trusted"] is True
    device_id = paired["device"]["device_id"]

    replay = _route(app, "/mark-3/local-pairing/verify", "POST").endpoint(
        Mark3LocalPairingVerifyRequest(
            challenge_id=paired["challenge_id"],
            nonce="wrong",
            response_phrase="wrong",
            public_identifier="phone-one",
            display_name="David phone",
            scope=["voice_approval", "normal", "strong"],
        )
    )
    assert replay["reason"] == "pairing_challenge_already_used"

    limited = _route(app, "/mark-3/local-pairing/challenge", "POST").endpoint(
        Mark3LocalPairingChallengeRequest(
            display_name="Tablet",
            public_identifier="tablet-one",
            channel="local_voice_device",
            scope=["voice_approval"],
        )
    )
    for _ in range(3):
        rate_limited = _route(app, "/mark-3/local-pairing/verify", "POST").endpoint(
            Mark3LocalPairingVerifyRequest(
                challenge_id=limited["challenge_id"],
                nonce=limited["nonce"],
                response_phrase="WRONG",
                public_identifier="tablet-one",
                display_name="Tablet",
                scope=["voice_approval"],
            )
        )
    assert rate_limited["rate_limited"] is True

    _route(app, "/mark-3/remote-pairing/revoke", "POST").endpoint(
        Mark3RemotePairingRevokeRequest(device_id=device_id, reason="lost device")
    )
    restarted_app, _restarted_ledger, restarted_calls, _ = _make_app(tmp_path, monkeypatch)
    restarted_devices = _route(restarted_app, "/mark-3/trusted-devices/status").endpoint()
    restarted_device = next(item for item in restarted_devices["devices"] if item["device_id"] == device_id)
    assert restarted_device["revoked"] is True
    assert restarted_device["trusted"] is False
    assert state_dir.exists()
    assert calls == []
    assert restarted_calls == []
    assert {"local_pairing_challenge_consumed", "local_pairing_challenge_rate_limited", "remote_pairing_revoked"} <= _event_types(ledger)


def test_voice_approval_requires_trusted_device_readback_phrase_and_rejects_replay(tmp_path, monkeypatch):
    app, ledger, calls, _state_dir = _make_app(tmp_path, monkeypatch)
    paired = _pair_voice_device(app, public_identifier="voice-phone")
    device_id = paired["device"]["device_id"]

    preview = _preview(
        app,
        intent="Read a safe file",
        action_key="repo.file.read_safe",
        inputs={"path": "README.md"},
    )
    envelope = _request_approval(app, preview["preview_id"])
    assert envelope["approval_level_required"] == "normal"

    with pytest.raises(HTTPException) as untrusted:
        _route(app, "/mark-3/voice-approval/start", "POST").endpoint(
            Mark3VoiceApprovalStartRequest(
                approval_id=envelope["approval_id"],
                device_id="device-not-trusted",
                readback_text=envelope["readback_text"],
            )
        )
    assert untrusted.value.status_code == 400

    session = _route(app, "/mark-3/voice-approval/start", "POST").endpoint(
        Mark3VoiceApprovalStartRequest(
            approval_id=envelope["approval_id"],
            device_id=device_id,
            readback_text=envelope["readback_text"],
            cost_summary="unknown; operator review required",
        )
    )
    assert session["readback_presented"] is True
    assert session["expected_challenge"] == ""
    assert session["raw_audio_stored"] is False

    wake_only = _route(app, "/mark-3/voice-approval/decision", "POST").endpoint(
        Mark3VoiceApprovalDecisionRequest(
            session_id=session["session_id"],
            device_id=device_id,
            transcript="JARVIS",
            readback_text=envelope["readback_text"],
            cost_summary="unknown; operator review required",
        )
    )
    assert wake_only["decision"] == "wake_phrase_rejected"
    assert wake_only["status"] == "rejected"

    accepted = _route(app, "/mark-3/voice-approval/decision", "POST").endpoint(
        Mark3VoiceApprovalDecisionRequest(
            session_id=session["session_id"],
            device_id=device_id,
            transcript="JARVIS, autorizo",
            readback_text=envelope["readback_text"],
            action_id=envelope["action_id"],
            cost_summary="unknown; operator review required",
        )
    )
    assert accepted["decision"] == "accepted"
    assert accepted["approval"]["status"] == "approved"
    assert accepted["transcript_stored"] is False

    replay = _route(app, "/mark-3/voice-approval/decision", "POST").endpoint(
        Mark3VoiceApprovalDecisionRequest(
            session_id=session["session_id"],
            device_id=device_id,
            transcript="JARVIS, autorizo",
            readback_text=envelope["readback_text"],
            cost_summary="unknown; operator review required",
        )
    )
    assert replay["decision"] == "replay_rejected"
    assert calls == []
    assert {"voice_approval_session_started", "voice_approval_wake_phrase_rejected", "voice_approval_accepted"} <= _event_types(ledger)


def test_voice_approval_strong_requires_exact_challenge_and_revoked_device_blocks(tmp_path, monkeypatch):
    app, ledger, calls, _state_dir = _make_app(tmp_path, monkeypatch)
    high_contract = replace(ACTION_CATALOG["jarvis.phase.status"], risk_level="high", approval_required="strong")
    monkeypatch.setitem(ACTION_CATALOG, "jarvis.phase.status", high_contract)
    paired = _pair_voice_device(app, public_identifier="strong-phone")
    device_id = paired["device"]["device_id"]

    preview = _preview(app, intent="Strong phase status", action_key="jarvis.phase.status")
    envelope = _request_approval(app, preview["preview_id"])
    session = _route(app, "/mark-3/voice-approval/start", "POST").endpoint(
        Mark3VoiceApprovalStartRequest(
            approval_id=envelope["approval_id"],
            device_id=device_id,
            readback_text=envelope["readback_text"],
            cost_summary="unknown; operator review required",
        )
    )
    assert session["expected_challenge"].startswith("JARVIS, confirmo ")

    denied = _route(app, "/mark-3/voice-approval/decision", "POST").endpoint(
        Mark3VoiceApprovalDecisionRequest(
            session_id=session["session_id"],
            device_id=device_id,
            transcript="JARVIS, autorizo",
            readback_text=envelope["readback_text"],
            cost_summary="unknown; operator review required",
        )
    )
    assert denied["decision"] == "denied"
    assert denied["reason"] == "spoken_confirmation_phrase_mismatch"

    accepted = _route(app, "/mark-3/voice-approval/decision", "POST").endpoint(
        Mark3VoiceApprovalDecisionRequest(
            session_id=session["session_id"],
            device_id=device_id,
            transcript=session["expected_challenge"],
            readback_text=envelope["readback_text"],
            cost_summary="unknown; operator review required",
        )
    )
    assert accepted["decision"] == "accepted"

    second_pair = _pair_voice_device(app, public_identifier="revoked-phone")
    revoked_device_id = second_pair["device"]["device_id"]
    _route(app, "/mark-3/remote-pairing/revoke", "POST").endpoint(
        Mark3RemotePairingRevokeRequest(device_id=revoked_device_id, reason="operator revoke")
    )
    second_preview = _preview(app, intent="Strong phase status 2", action_key="jarvis.phase.status")
    second_envelope = _request_approval(app, second_preview["preview_id"])
    with pytest.raises(HTTPException) as revoked:
        _route(app, "/mark-3/voice-approval/start", "POST").endpoint(
            Mark3VoiceApprovalStartRequest(
                approval_id=second_envelope["approval_id"],
                device_id=revoked_device_id,
                readback_text=second_envelope["readback_text"],
            )
        )
    assert revoked.value.status_code == 400
    assert calls == []
    assert {"voice_approval_denied", "voice_approval_accepted", "remote_pairing_revoked"} <= _event_types(ledger)


def test_triple_approval_requires_persistent_identity_action_scope_and_no_replay(tmp_path, monkeypatch):
    app, ledger, calls, _state_dir = _make_app(tmp_path, monkeypatch)
    triple_contract = replace(ACTION_CATALOG["jarvis.phase.status"], risk_level="critical", approval_required="triple")
    monkeypatch.setitem(ACTION_CATALOG, "jarvis.phase.status", triple_contract)
    terminal = _verify_terminal(app)
    assert terminal["verified"] is True
    assert terminal["trusted_device"]["trusted"] is True
    _register_controller(app)

    readiness = _route(app, "/mark-3/phase-5/status").endpoint()["triple_approval_readiness"]
    assert readiness["persistent_identity_ready"] is True
    assert readiness["can_grant_triple"] is True

    preview = _preview(app, intent="Critical persistent identity check", action_key="jarvis.phase.status")
    envelope = _request_approval(app, preview["preview_id"])
    assert envelope["status"] == "pending"

    with pytest.raises(HTTPException) as wrong_action:
        _triple_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-1",
            channel_id="ui_local_browser",
            confirmation_phrase=envelope["approval_steps"][0]["confirmation_phrase"],
            readback_text=envelope["readback_text"],
            action_id="wrong-action",
        )
    assert wrong_action.value.status_code == 400
    assert "action_id" in str(wrong_action.value.detail)

    with pytest.raises(HTTPException) as wrong_scope:
        _triple_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-1",
            channel_id="ui_local_browser",
            confirmation_phrase=envelope["approval_steps"][0]["confirmation_phrase"],
            readback_text=envelope["readback_text"],
            scope_fingerprint="wrong-scope",
        )
    assert wrong_scope.value.status_code == 400
    assert "scope fingerprint" in str(wrong_scope.value.detail)

    step1 = _triple_decide(
        app,
        approval_id=envelope["approval_id"],
        step_id="step-1",
        channel_id="ui_local_browser",
        confirmation_phrase=envelope["approval_steps"][0]["confirmation_phrase"],
        readback_text=envelope["readback_text"],
        action_id=envelope["action_id"],
    )
    assert step1["status"] == "pending"

    with pytest.raises(HTTPException) as replay:
        _triple_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-1",
            channel_id="terminal_local",
            confirmation_phrase=envelope["approval_steps"][0]["confirmation_phrase"],
            readback_text=envelope["readback_text"],
        )
    assert replay.value.status_code == 400

    _route(app, "/mark-3/remote-pairing/revoke", "POST").endpoint(
        Mark3RemotePairingRevokeRequest(device_id="device-terminal_local", reason="operator revoke")
    )
    blocked_readiness = _route(app, "/mark-3/phase-5/status").endpoint()["triple_approval_readiness"]
    assert blocked_readiness["persistent_identity_ready"] is False
    assert blocked_readiness["can_grant_triple"] is False
    with pytest.raises(HTTPException) as revoked_terminal:
        _triple_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-2",
            channel_id="terminal_local",
            confirmation_phrase=envelope["approval_steps"][1]["confirmation_phrase"],
            readback_text=envelope["readback_text"],
        )
    assert revoked_terminal.value.status_code == 400
    assert "persistent trusted device" in str(revoked_terminal.value.detail)
    assert calls == []
    assert {"approval_step_approved", "remote_pairing_revoked"} <= _event_types(ledger)
