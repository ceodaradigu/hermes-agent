import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi import HTTPException

from jarvis.api.app import (
    Mark3ExecutionPreviewRequest,
    Mark3ExecutionRequestApprovalRequest,
    Mark3LocalControllerHeartbeatRequest,
    Mark3LocalControllerRegisterRequest,
    Mark3LocalControllerRequest,
    Mark3LocalControllerStopRequest,
    Mark3RemotePairingCancelRequest,
    Mark3RemotePairingPrepareRequest,
    Mark3RemotePairingRevokeRequest,
    Mark3TrustedApprovalChannelVerifyRequest,
    Mark3TrustedApprovalDecisionRequest,
    create_app,
)
from jarvis.memory_brain_v2 import MemoryBrainV2Store
from jarvis.persistent_audit import PersistentAuditLedger
from jarvis.phase_1_governed_execution import PROTECTED_CREDENTIAL_MESSAGE
from jarvis.phase_2_local_assistant_runtime import ACTION_CATALOG
from jarvis.phase_4_local_controller_remote_pairing import (
    LOCAL_CONTROLLER_VERIFICATION_PHRASE,
    TERMINAL_VERIFICATION_PHRASE,
)


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


class FakeHermesReadAdapter:
    def __init__(self, guard, calls):
        self.guard = guard
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

    def adapter_factory(guard):
        return FakeHermesReadAdapter(guard, calls)

    app = create_app(
        adapter_factory=lambda: pytest.fail("legacy Hermes adapter must not be called"),
        hermes_runtime_adapter_factory=adapter_factory,
        persistent_audit_ledger=ledger,
        memory_brain_v2=memory,
    )
    return app, ledger, calls


def _route(app, path, method="GET"):
    return next(route for route in app.routes if route.path == path and method in getattr(route, "methods", set()))


def _preview(app, **payload):
    return _route(app, "/mark-3/execution/preview", "POST").endpoint(Mark3ExecutionPreviewRequest(**payload))


def _request_approval(app, preview_id, actor="David"):
    return _route(app, "/mark-3/execution/request-approval", "POST").endpoint(
        Mark3ExecutionRequestApprovalRequest(preview_id=preview_id, actor=actor)
    )


def _triple_decide(app, **payload):
    return _route(app, "/mark-3/approval/triple-decision", "POST").endpoint(
        Mark3TrustedApprovalDecisionRequest(**payload)
    )


def _verify_terminal(app):
    return _route(app, "/mark-3/trusted-approval-channels/verify", "POST").endpoint(
        Mark3TrustedApprovalChannelVerifyRequest(
            channel_id="terminal_local",
            challenge_response=TERMINAL_VERIFICATION_PHRASE,
        )
    )


def _register_controller(app, controller_id="ctrl-test"):
    return _route(app, "/mark-3/local-controller/register", "POST").endpoint(
        Mark3LocalControllerRegisterRequest(
            controller_id=controller_id,
            display_name="Test Local Controller",
            verification_phrase=LOCAL_CONTROLLER_VERIFICATION_PHRASE,
        )
    )


def _event_types(ledger):
    return {entry["event_type"] for entry in ledger.list_entries(limit=300)}


def _frontend_source():
    paths = [
        WEB / "src/lib/api.ts",
        WEB / "src/components/jarvis/JarvisDebugDrawer.tsx",
        WEB / "src/components/jarvis/JarvisPresenceShell.tsx",
        WEB / "src/components/jarvis/JarvisOrb3D.tsx",
        WEB / "src/components/jarvis/contracts.ts",
        WEB / "src/components/jarvis/utils.ts",
        WEB / "src/hooks/jarvis/useJarvisOrbState.ts",
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_phase_4_routes_and_local_controller_defaults_register_heartbeat_stop(tmp_path, monkeypatch):
    app, ledger, calls = _make_app(tmp_path, monkeypatch)
    route_paths = {route.path for route in app.routes}

    assert "/execute" not in route_paths
    assert "/jarvis/execute" not in route_paths
    for path in (
        "/mark-3/phase-4/status",
        "/mark-3/local-controller/status",
        "/mark-3/local-controller/register",
        "/mark-3/local-controller/heartbeat",
        "/mark-3/local-controller/open-jarvis-request",
        "/mark-3/local-controller/stop-request",
        "/mark-3/trusted-devices/status",
        "/mark-3/remote-pairing/status",
        "/mark-3/telegram-bridge/status",
        "/mark-3/stop-rollback/status",
    ):
        assert path in route_paths

    phase4 = _route(app, "/mark-3/phase-4/status").endpoint()
    assert phase4["status"] == "implemented_as_local_controller_remote_pairing_readiness_macro_phase"
    assert phase4["security_gates"]["jarvis_governs"] is True
    assert phase4["security_gates"]["remote_pairing_enabled"] is False
    assert phase4["security_gates"]["remote_approval_allowed"] is False
    assert phase4["security_gates"]["remote_execution_allowed"] is False
    assert phase4["security_gates"]["telegram_api_called"] is False
    assert phase4["security_gates"]["env_read_for_tokens"] is False

    controller = _route(app, "/mark-3/local-controller/status").endpoint()
    assert controller["local_only"] is True
    assert controller["bind_host"] == "127.0.0.1"
    assert controller["auto_start_enabled"] is False
    assert controller["installed_as_system_service"] is False
    assert controller["startup_integration_enabled"] is False
    assert controller["user_opt_in_required"] is True
    assert controller["no_background_capture"] is True
    assert controller["can_open_jarvis"] is True
    assert controller["can_show_status"] is True
    assert controller["can_show_approvals"] is True
    assert controller["can_request_stop"] is True

    with pytest.raises(HTTPException) as external_bind:
        _route(app, "/mark-3/local-controller/register", "POST").endpoint(
            Mark3LocalControllerRegisterRequest(bind_host="0.0.0.0")
        )
    assert external_bind.value.status_code == 400

    registered = _register_controller(app)
    assert registered["verified"] is True
    assert registered["trusted_device"]["can_grant_triple"] is True

    heartbeat = _route(app, "/mark-3/local-controller/heartbeat", "POST").endpoint(
        Mark3LocalControllerHeartbeatRequest(controller_id=registered["controller_id"])
    )
    assert heartbeat["controller_status"] == "heartbeat_verified"
    assert heartbeat["metadata_only"] is True

    opened = _route(app, "/mark-3/local-controller/open-jarvis-request", "POST").endpoint(
        Mark3LocalControllerRequest(controller_id=registered["controller_id"])
    )
    assert opened["request_status"] == "recorded_not_executed"
    assert opened["did_open_browser"] is False

    stopped = _route(app, "/mark-3/local-controller/stop-request", "POST").endpoint(
        Mark3LocalControllerStopRequest(
            controller_id=registered["controller_id"],
            reason="pilot stop",
            scope=["local_controller", "approval_panel"],
        )
    )
    assert stopped["stop_actor"] == "David"
    assert stopped["stop_channel"] == "local_controller"
    assert stopped["cooperative_stop_signal"] is True
    assert stopped["result_observed"] is False
    assert stopped["final_state"] == "unsupported_embedded_backend_not_stopped"

    status = _route(app, "/mark-3/stop-rollback/status").endpoint()
    assert status["rollback_dry_run_mode"] is True
    assert status["destructive_rollback_executed"] is False
    assert {"local_controller_registered", "local_controller_heartbeat", "local_controller_open_requested", "local_controller_stop_requested"} <= _event_types(ledger)
    assert calls == []


def test_trusted_devices_default_remote_zero_terminal_controller_and_revoke(tmp_path, monkeypatch):
    app, ledger, calls = _make_app(tmp_path, monkeypatch)

    devices = _route(app, "/mark-3/trusted-devices/status").endpoint()
    assert devices["default_remote_devices_zero_untrusted"] is True
    assert devices["remote_devices_count"] == 0
    assert devices["remote_trusted_devices_count"] == 0
    by_id = {item["device_id"]: item for item in devices["devices"]}
    assert by_id["device-ui_local_browser"]["trusted"] is True
    assert by_id["device-ui_local_browser"]["can_grant_strong"] is True
    assert by_id["device-terminal_local"]["trusted"] is False
    assert by_id["device-local_controller"]["trusted"] is False
    assert by_id["device-voice_readback_only"]["can_grant_strong"] is False
    assert by_id["device-wake_phrase_disabled"]["can_grant_strong"] is False

    rejected = _route(app, "/mark-3/trusted-approval-channels/verify", "POST").endpoint(
        Mark3TrustedApprovalChannelVerifyRequest(channel_id="terminal_local", challenge_response="WRONG")
    )
    assert rejected["verified"] is False
    assert rejected["reason"] == "terminal_challenge_invalid"

    terminal = _verify_terminal(app)
    assert terminal["verified"] is True
    registered = _register_controller(app, controller_id="ctrl-revoke")
    assert registered["verified"] is True

    ready = _route(app, "/mark-3/trusted-devices/status").endpoint()
    assert ready["can_grant_double"] is True
    assert ready["can_grant_triple"] is True

    revoked = _route(app, "/mark-3/remote-pairing/revoke", "POST").endpoint(
        Mark3RemotePairingRevokeRequest(device_id=registered["trusted_device"]["device_id"])
    )
    assert revoked["remote_execution_allowed"] is False
    after_revoke = _route(app, "/mark-3/trusted-devices/status").endpoint()
    controller = next(item for item in after_revoke["devices"] if item["channel_type"] == "local_controller")
    assert controller["revoked"] is True
    assert controller["can_grant_triple"] is False
    assert after_revoke["can_grant_triple"] is False
    assert {"trusted_channel_rejected", "trusted_channel_verified", "remote_pairing_revoked"} <= _event_types(ledger)
    assert calls == []


def test_triple_approval_requires_three_separate_verified_channels_and_policy_recalc(tmp_path, monkeypatch):
    app, ledger, calls = _make_app(tmp_path, monkeypatch)
    triple_contract = replace(ACTION_CATALOG["jarvis.phase.status"], risk_level="critical", approval_required="triple")
    monkeypatch.setitem(ACTION_CATALOG, "jarvis.phase.status", triple_contract)

    blocked_preview = _preview(app, intent="Critical blocked", action_key="jarvis.phase.status")
    blocked = _request_approval(app, blocked_preview["preview_id"])
    assert blocked["approval_level_required"] == "triple"
    assert blocked["status"] == "blocked"
    assert blocked["step_count_required"] == 3
    assert len(blocked["approval_steps"]) == 3
    blocked_decision = _triple_decide(app, approval_id=blocked["approval_id"], channel_id="ui_local_browser")
    assert blocked_decision["status"] == "blocked"
    assert blocked_decision["can_dispatch_after_approval"] is False

    _verify_terminal(app)
    _register_controller(app)
    preview = _preview(app, intent="Critical ready", action_key="jarvis.phase.status")
    envelope = _request_approval(app, preview["preview_id"])
    assert envelope["status"] == "pending"
    assert envelope["step_count_required"] == 3
    assert envelope["channel_separation_required"] is True
    assert envelope["policy_recalculation_before_final_decision"] is True

    with pytest.raises(HTTPException) as voice_rejected:
        _triple_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-1",
            channel_id="voice_readback_only",
            confirmation_phrase=envelope["approval_steps"][0]["confirmation_phrase"],
            readback_text=envelope["readback_text"],
        )
    assert voice_rejected.value.status_code == 400
    assert "voice" in str(voice_rejected.value.detail) or "channel cannot grant triple" in str(voice_rejected.value.detail)

    with pytest.raises(HTTPException) as wrong_phrase:
        _triple_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-1",
            channel_id="ui_local_browser",
            confirmation_phrase="WRONG",
            readback_text=envelope["readback_text"],
        )
    assert wrong_phrase.value.status_code == 400
    assert "confirmation phrase" in str(wrong_phrase.value.detail)

    step1 = _triple_decide(
        app,
        approval_id=envelope["approval_id"],
        step_id="step-1",
        channel_id="ui_local_browser",
        confirmation_phrase=envelope["approval_steps"][0]["confirmation_phrase"],
        readback_text=envelope["readback_text"],
    )
    assert step1["status"] == "pending"
    assert step1["step_count_approved"] == 1

    with pytest.raises(HTTPException) as reused_step:
        _triple_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-1",
            channel_id="terminal_local",
            confirmation_phrase=envelope["approval_steps"][0]["confirmation_phrase"],
            readback_text=envelope["readback_text"],
        )
    assert reused_step.value.status_code == 400
    assert "already approved" in str(reused_step.value.detail)

    with pytest.raises(HTTPException) as same_channel:
        _triple_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-2",
            channel_id="ui_local_browser",
            confirmation_phrase=envelope["approval_steps"][1]["confirmation_phrase"],
            readback_text=envelope["readback_text"],
        )
    assert same_channel.value.status_code == 400
    assert "three separate trusted channels" in str(same_channel.value.detail)

    step2 = _triple_decide(
        app,
        approval_id=envelope["approval_id"],
        step_id="step-2",
        channel_id="terminal_local",
        confirmation_phrase=envelope["approval_steps"][1]["confirmation_phrase"],
        readback_text=envelope["readback_text"],
    )
    assert step2["status"] == "pending"
    assert step2["step_count_approved"] == 2

    changed_contract = replace(ACTION_CATALOG["jarvis.phase.status"], risk_level="low", approval_required="none")
    monkeypatch.setitem(ACTION_CATALOG, "jarvis.phase.status", changed_contract)
    with pytest.raises(HTTPException) as policy_changed:
        _triple_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-3",
            channel_id="local_controller",
            confirmation_phrase=envelope["approval_steps"][2]["confirmation_phrase"],
            readback_text=envelope["readback_text"],
        )
    assert policy_changed.value.status_code == 400
    assert "policy changed" in str(policy_changed.value.detail)

    expired_contract = replace(ACTION_CATALOG["jarvis.phase.status"], risk_level="critical", approval_required="triple")
    monkeypatch.setitem(ACTION_CATALOG, "jarvis.phase.status", expired_contract)
    expired_preview = _preview(app, intent="Critical expired", action_key="jarvis.phase.status")
    expired = _request_approval(app, expired_preview["preview_id"])
    app.state.phase_4_local_controller._approval_envelopes[expired["approval_id"]]["approval_steps"][0]["expires_at"] = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()
    with pytest.raises(HTTPException) as expired_step:
        _triple_decide(
            app,
            approval_id=expired["approval_id"],
            step_id="step-1",
            channel_id="ui_local_browser",
            confirmation_phrase=expired["approval_steps"][0]["confirmation_phrase"],
            readback_text=expired["readback_text"],
        )
    assert expired_step.value.status_code == 400
    assert "expired" in str(expired_step.value.detail)

    assert {"approval_step_requested", "approval_step_approved", "approval_step_expired", "approval_blocked"} <= _event_types(ledger)
    assert calls == []


def test_triple_approval_can_complete_after_three_verified_channels(tmp_path, monkeypatch):
    app, _ledger, calls = _make_app(tmp_path, monkeypatch)
    triple_contract = replace(ACTION_CATALOG["jarvis.phase.status"], risk_level="critical", approval_required="triple")
    monkeypatch.setitem(ACTION_CATALOG, "jarvis.phase.status", triple_contract)
    _verify_terminal(app)
    _register_controller(app)

    preview = _preview(app, intent="Critical complete", action_key="jarvis.phase.status")
    envelope = _request_approval(app, preview["preview_id"])
    for step_id, channel_id in (("step-1", "ui_local_browser"), ("step-2", "terminal_local"), ("step-3", "local_controller")):
        step = next(item for item in envelope["approval_steps"] if item["step_id"] == step_id)
        envelope = _triple_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id=step_id,
            channel_id=channel_id,
            confirmation_phrase=step["confirmation_phrase"],
            readback_text=envelope["readback_text"],
        )

    assert envelope["status"] == "approved"
    assert envelope["channel_ids"] == ["ui_local_browser", "terminal_local", "local_controller"]
    assert envelope["decision_reason"] == "triple_approval_completed_policy_recalculated"
    assert calls == []


def test_remote_pairing_and_telegram_readiness_disabled_no_tokens_or_external_calls(tmp_path, monkeypatch):
    app, ledger, calls = _make_app(tmp_path, monkeypatch)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "SHOULD_NOT_BE_READ")

    status = _route(app, "/mark-3/remote-pairing/status").endpoint()
    assert status["remote_pairing_enabled"] is False
    assert status["remote_approval_allowed"] is False
    assert status["remote_execution_allowed"] is False
    assert status["trusted_pairing_required"] is True
    assert status["pairing_code_created"] is False

    prepared = _route(app, "/mark-3/remote-pairing/prepare", "POST").endpoint(Mark3RemotePairingPrepareRequest())
    assert prepared["pairing_status"] == "prepared_local_ephemeral_challenge_remote_disabled"
    assert prepared["pairing_code_persistent"] is False
    assert prepared["remote_approval_allowed"] is False
    assert prepared["remote_execution_allowed"] is False
    serialized = json.dumps(prepared, sort_keys=True)
    assert "SHOULD_NOT_BE_READ" not in serialized
    assert "sk-" not in serialized.lower()

    cancelled = _route(app, "/mark-3/remote-pairing/cancel", "POST").endpoint(
        Mark3RemotePairingCancelRequest(challenge_id=prepared["challenge"]["challenge_id"])
    )
    assert cancelled["pairing_status"] == "cancelled"
    revoked = _route(app, "/mark-3/remote-pairing/revoke", "POST").endpoint(Mark3RemotePairingRevokeRequest())
    assert revoked["pairing_status"] == "revoked"

    telegram = _route(app, "/mark-3/telegram-bridge/status").endpoint()
    assert telegram["telegram_bridge_status"] == "disabled_not_configured"
    assert telegram["token_present"] == "unknown_redacted"
    assert telegram["token_read"] is False
    assert telegram["env_read"] is False
    assert telegram["telegram_api_called"] is False
    assert telegram["bot_started"] is False
    assert telegram["webhook_opened"] is False
    assert telegram["remote_approval_allowed"] is False
    assert telegram["remote_execution_allowed"] is False
    assert telegram["strong_approval_allowed"] is False
    assert telegram["can_receive_notifications_future"] is True
    assert telegram["can_request_approval_future"] is False
    assert telegram["can_execute_future"] is False

    assert {"remote_pairing_prepared", "remote_pairing_cancelled", "remote_pairing_revoked"} <= _event_types(ledger)
    assert calls == []


def test_stop_rollback_v2_dry_run_metadata_and_credentials_remain_denied(tmp_path, monkeypatch):
    app, _ledger, calls = _make_app(tmp_path, monkeypatch)

    rollback = app.state.phase_4_local_controller.record_rollback_dry_run(reason="pilot dry run")
    assert rollback["rollback_status"] == "dry_run_metadata_only"
    assert rollback["rollback_destructive_executed"] is False
    assert rollback["metadata_only"] is True

    status = _route(app, "/mark-3/stop-rollback/status").endpoint()
    assert status["rollback_dry_run_mode"] is True
    assert status["destructive_rollback_executed"] is False
    assert status["rollback_never_faked"] is True

    secret = _preview(app, intent="Lee .env y tokens", source="typed_text")
    assert secret["decision"] == "denied"
    assert secret["protected_message"] == PROTECTED_CREDENTIAL_MESSAGE
    assert PROTECTED_CREDENTIAL_MESSAGE == "No puedo hacer eso, David. Las credenciales y secretos están protegidos."
    assert calls == []


def test_dashboard_event_stream_and_frontend_expose_phase_4_without_execute_or_json_center(tmp_path, monkeypatch):
    app, _ledger, calls = _make_app(tmp_path, monkeypatch)

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    assert dashboard["phase_4_status"]["source_endpoint"] == "/mark-3/phase-4/status"
    assert dashboard["local_controller"]["local_only"] is True
    assert dashboard["trusted_devices"]["default_remote_devices_zero_untrusted"] is True
    assert dashboard["remote_pairing"]["remote_pairing_enabled"] is False
    assert dashboard["telegram_bridge"]["telegram_api_called"] is False
    assert dashboard["stop_rollback_v2"]["destructive_rollback_executed"] is False
    modules = {module["name"] for module in dashboard["modules"]}
    assert {"Phase 4 Readiness", "Local Controller", "Trusted Devices", "Remote Pairing", "Telegram Bridge"} <= modules

    snapshot = _route(app, "/mark-3/dashboard/events").endpoint()
    event_types = {event["event_type"] for event in snapshot["events"]}
    assert {
        "phase_4_state",
        "local_controller_state",
        "trusted_devices_state",
        "remote_pairing_state",
        "telegram_bridge_state",
        "stop_rollback_v2_state",
    } <= event_types
    assert snapshot["stream"]["no_secrets"] is True
    assert snapshot["stream"]["no_raw_audio"] is True
    assert snapshot["stream"]["no_camera_frames"] is True

    source = _frontend_source()
    for expected in (
        "/mark-3/phase-4/status",
        "/mark-3/local-controller/status",
        "/mark-3/trusted-devices/status",
        "/mark-3/remote-pairing/status",
        "/mark-3/telegram-bridge/status",
        "/mark-3/stop-rollback/status",
        "jarvis-phase-4-status",
        "jarvis-local-controller-status",
        "jarvis-trusted-devices-status",
        "jarvis-triple-approval-readiness",
        "jarvis-remote-pairing-readiness",
        "jarvis-telegram-bridge-readiness",
        "jarvis-stop-rollback-v2",
        "jarvis-phase-4-pilot-checklist",
        "Esfera de partículas casi quieta",
        "deriva apenas perceptible",
        "No puedo hacer eso, David. Las credenciales y secretos están protegidos.",
    ):
        assert expected in source
    assert "JSON.stringify(dashboard" not in source
    assert 'fetchJSON("/execute"' not in source
    assert 'fetchJSON("/jarvis/execute"' not in source
    assert "dispatchHermes" not in source
    assert "HermesRuntimeAdapter" not in source
    assert "telegramApi.send" not in source
    assert calls == []
