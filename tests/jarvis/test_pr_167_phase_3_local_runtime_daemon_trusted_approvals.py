import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi import HTTPException

from jarvis.api.app import (
    Mark3ExecutionDispatchRequest,
    Mark3ExecutionPreviewRequest,
    Mark3ExecutionRequestApprovalRequest,
    Mark3ExecutionStopRequest,
    Mark3LocalDaemonControlRequest,
    Mark3LocalDaemonHeartbeatRequest,
    Mark3TrustedApprovalChannelVerifyRequest,
    Mark3TrustedApprovalDecisionRequest,
    create_app,
)
from jarvis.memory_brain_v2 import MemoryBrainV2Store
from jarvis.persistent_audit import PersistentAuditLedger
from jarvis.phase_1_governed_execution import PROTECTED_CREDENTIAL_MESSAGE
from jarvis.phase_2_local_assistant_runtime import ACTION_CATALOG, ExecutionHistoryStore


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


class FakeHermesReadAdapter:
    def __init__(self, guard, calls):
        self.guard = guard
        self.calls = calls
        self.interruptions = []

    def run(self, message, **kwargs):
        path = message.rsplit("path:", 1)[-1].strip()
        decision = self.guard("read_file", {"path": path, "cwd": str(Path(path).resolve().parent), "backend": "local"})
        self.calls.append({"path": path, "decision": decision, "kwargs": kwargs})
        if decision is not True:
            return {"success": False, "completed": False, "error": decision}
        return {"success": True}

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
    return app, ledger, memory, calls, state_dir


def _route(app, path, method="GET"):
    return next(route for route in app.routes if route.path == path and method in getattr(route, "methods", set()))


def _preview(app, **payload):
    return _route(app, "/mark-3/execution/preview", "POST").endpoint(Mark3ExecutionPreviewRequest(**payload))


def _request_approval(app, preview_id, actor="David"):
    return _route(app, "/mark-3/execution/request-approval", "POST").endpoint(
        Mark3ExecutionRequestApprovalRequest(preview_id=preview_id, actor=actor)
    )


def _dispatch(app, preview_id, approval_id=None):
    return _route(app, "/mark-3/execution/dispatch", "POST").endpoint(
        Mark3ExecutionDispatchRequest(preview_id=preview_id, approval_id=approval_id, actor="David")
    )


def _verify_channel(app, channel_id, local_presence=True):
    return _route(app, "/mark-3/trusted-approval-channels/verify", "POST").endpoint(
        Mark3TrustedApprovalChannelVerifyRequest(channel_id=channel_id, local_presence=local_presence)
    )


def _double_decide(app, **payload):
    return _route(app, "/mark-3/approval/double-decision", "POST").endpoint(
        Mark3TrustedApprovalDecisionRequest(**payload)
    )


def _strong_decide(app, **payload):
    return _route(app, "/mark-3/approval/strong-decision", "POST").endpoint(
        Mark3TrustedApprovalDecisionRequest(**payload)
    )


def _event_types(ledger):
    return {entry["event_type"] for entry in ledger.list_entries(limit=300)}


def _frontend_source():
    paths = [
        WEB / "src/lib/api.ts",
        WEB / "src/components/jarvis/JarvisDebugDrawer.tsx",
        WEB / "src/components/jarvis/JarvisSmartBar.tsx",
        WEB / "src/components/jarvis/utils.ts",
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_phase_3_routes_daemon_tray_doctor_and_bridge_readiness(tmp_path, monkeypatch):
    app, ledger, _memory, calls, state_dir = _make_app(tmp_path, monkeypatch)
    route_paths = {route.path for route in app.routes}

    assert "/execute" not in route_paths
    assert "/jarvis/execute" not in route_paths
    for path in (
        "/mark-3/phase-3/status",
        "/mark-3/local-daemon/status",
        "/mark-3/local-daemon/health",
        "/mark-3/local-daemon/heartbeat",
        "/mark-3/local-daemon/stop-request",
        "/mark-3/local-daemon/restart-request",
        "/mark-3/local-doctor/status",
        "/mark-3/trusted-approval-channels/status",
        "/mark-3/trusted-approval-channels/verify",
        "/mark-3/approval/strong-decision",
        "/mark-3/approval/double-decision",
        "/mark-3/approval/triple-decision",
        "/mark-3/execution/history/export-preview",
    ):
        assert path in route_paths

    phase3 = _route(app, "/mark-3/phase-3/status").endpoint()
    assert phase3["status"] == "implemented_as_local_governed_runtime_macro_phase"
    assert phase3["security_gates"]["jarvis_governs"] is True
    assert phase3["security_gates"]["remote_approval_allowed"] is False
    assert phase3["security_gates"]["remote_execution_allowed"] is False
    assert phase3["blocked_or_unsupported"]["triple"] == "triple_requires_additional_trusted_channel_not_configured"

    daemon = _route(app, "/mark-3/local-daemon/status").endpoint()
    assert daemon["local_only"] is True
    assert daemon["bind_host"] == "127.0.0.1"
    assert daemon["auto_start_enabled"] is False
    assert daemon["background_listening_enabled"] is False
    assert daemon["mic_auto_start"] is False
    assert daemon["camera_auto_start"] is False
    assert daemon["wake_auto_start"] is False
    assert daemon["user_opt_in_required"] is True
    assert str(state_dir) in daemon["state_dir"]

    health = _route(app, "/mark-3/local-daemon/health").endpoint()
    assert health["health_status"] == "healthy"
    assert {check["name"] for check in health["checks"]} >= {"safe_bind_host", "auto_start_disabled"}

    heartbeat = _route(app, "/mark-3/local-daemon/heartbeat", "POST").endpoint(
        Mark3LocalDaemonHeartbeatRequest(daemon_id=daemon["daemon_id"])
    )
    assert heartbeat["daemon_status"] == "heartbeat_recorded"
    assert _route(app, "/mark-3/local-daemon/status").endpoint()["last_heartbeat_at"] == heartbeat["last_heartbeat_at"]

    stop = _route(app, "/mark-3/local-daemon/stop-request", "POST").endpoint(Mark3LocalDaemonControlRequest())
    assert stop["stop_request_id"].startswith("stop-")
    assert stop["bridge_stop_supported"] is False
    assert stop["process_stop_supported"] is False
    assert stop["confirmed_stopped"] is False
    assert stop["final_status"] == "unsupported_embedded_api_process_cannot_self_terminate"

    restart = _route(app, "/mark-3/local-daemon/restart-request", "POST").endpoint(Mark3LocalDaemonControlRequest())
    assert restart["restart_supported"] is False
    assert restart["final_status"] == "unsupported_honest"

    tray = phase3["tray"]
    assert tray["tray_available"] is True
    assert tray["tray_installed"] is False
    assert tray["tray_running"] is False
    assert tray["no_background_capture"] is True

    doctor = _route(app, "/mark-3/local-doctor/status").endpoint()
    assert doctor["state"]["local_bind_host_safe"] is True
    assert doctor["state"]["external_bind_enabled"] is False
    assert doctor["state"]["env_file_read"] is False
    assert doctor["state"]["secrets_exposed"] is False
    assert doctor["safety"]["no_env_read"] is True
    assert "python_env" in {check["name"] for check in doctor["checks"]}

    assert {"daemon_heartbeat", "daemon_stop_requested", "daemon_restart_requested"} <= _event_types(ledger)
    assert calls == []


def test_trusted_channels_voice_wake_remote_disabled_and_terminal_verify(tmp_path, monkeypatch):
    app, ledger, _memory, calls, _state_dir = _make_app(tmp_path, monkeypatch)

    status = _route(app, "/mark-3/trusted-approval-channels/status").endpoint()
    channels = {item["channel_id"]: item for item in status["channels"]}
    assert channels["ui_local_browser"]["can_grant_strong"] is True
    assert channels["terminal_local"]["can_grant_double"] is True
    assert channels["voice_readback_only"]["can_grant_approval"] is False
    assert channels["wake_phrase_disabled"]["can_grant_approval"] is False
    assert channels["telegram_future_disabled"]["enabled"] is False
    assert channels["mobile_future_disabled"]["enabled"] is False
    assert status["can_grant_triple"] is False
    assert status["remote_approval_allowed"] is False

    rejected = _verify_channel(app, "telegram_future_disabled")
    assert rejected["verified"] is False

    terminal = _verify_channel(app, "terminal_local")
    assert terminal["verified"] is True
    assert terminal["channel"]["authenticated"] is True
    assert {"trusted_channel_rejected", "trusted_channel_verified"} <= _event_types(ledger)
    assert calls == []


def test_strong_approval_endpoint_rejects_voice_channel_without_triple_fallback(tmp_path, monkeypatch):
    app, _ledger, _memory, calls, _state_dir = _make_app(tmp_path, monkeypatch)
    strong_contract = replace(ACTION_CATALOG["jarvis.phase.status"], risk_level="high", approval_required="strong")
    monkeypatch.setitem(ACTION_CATALOG, "jarvis.phase.status", strong_contract)

    preview = _preview(app, intent="Lee estado con confirmación fuerte", action_key="jarvis.phase.status")
    envelope = _request_approval(app, preview["preview_id"])
    assert envelope["approval_level_required"] == "strong"

    with pytest.raises(HTTPException) as voice_rejected:
        _strong_decide(
            app,
            approval_id=envelope["approval_id"],
            channel_id="voice_readback_only",
            confirmation_phrase=envelope["confirmation_phrase"],
            readback_text=envelope["readback_text"],
        )
    assert voice_rejected.value.status_code == 400
    assert "channel cannot grant strong approval" in str(voice_rejected.value.detail)
    assert app.state.phase_3_local_runtime._approval_envelopes[envelope["approval_id"]]["status"] == "pending"

    approved = _strong_decide(
        app,
        approval_id=envelope["approval_id"],
        channel_id="ui_local_browser",
        confirmation_phrase=envelope["confirmation_phrase"],
        readback_text=envelope["readback_text"],
    )
    assert approved["status"] == "approved"
    assert calls == []


def test_double_approval_requires_two_steps_expiry_phrase_readback_and_anti_reuse(tmp_path, monkeypatch):
    app, ledger, _memory, calls, _state_dir = _make_app(tmp_path, monkeypatch)
    double_contract = replace(ACTION_CATALOG["jarvis.phase.status"], risk_level="high", approval_required="double")
    monkeypatch.setitem(ACTION_CATALOG, "jarvis.phase.status", double_contract)

    preview = _preview(app, intent="Lee estado con doble aprobación", action_key="jarvis.phase.status")
    assert preview["approval_level_required"] == "double"
    envelope = _request_approval(app, preview["preview_id"])
    assert envelope["approval_level_required"] == "double"
    assert envelope["step_count_required"] == 2
    assert envelope["readback_required"] is True
    assert envelope["approval_steps"][0]["step_id"] == "step-1"
    assert envelope["approval_steps"][1]["step_id"] == "step-2"

    with pytest.raises(HTTPException) as terminal_not_verified:
        _double_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-2",
            channel_id="terminal_local",
            confirmation_phrase=envelope["approval_steps"][1]["confirmation_phrase"],
            readback_text=envelope["readback_text"],
        )
    assert terminal_not_verified.value.status_code == 400
    assert "channel must be verified" in str(terminal_not_verified.value.detail)

    with pytest.raises(HTTPException) as wrong_phrase:
        _double_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-1",
            channel_id="ui_local_browser",
            confirmation_phrase="WRONG",
            readback_text=envelope["readback_text"],
        )
    assert wrong_phrase.value.status_code == 400
    assert "confirmation phrase" in str(wrong_phrase.value.detail)

    step1 = _double_decide(
        app,
        approval_id=envelope["approval_id"],
        step_id="step-1",
        channel_id="ui_local_browser",
        confirmation_phrase=envelope["approval_steps"][0]["confirmation_phrase"],
        readback_text=envelope["readback_text"],
    )
    assert step1["status"] == "pending"
    assert step1["step_count_approved"] == 1
    assert step1["approval_steps"][0]["status"] == "approved"

    _verify_channel(app, "terminal_local")
    with pytest.raises(HTTPException) as same_channel:
        _double_decide(
            app,
            approval_id=envelope["approval_id"],
            step_id="step-2",
            channel_id="ui_local_browser",
            confirmation_phrase=envelope["approval_steps"][1]["confirmation_phrase"],
            readback_text=envelope["readback_text"],
        )
    assert same_channel.value.status_code == 400
    assert "separate trusted channels" in str(same_channel.value.detail)

    approved = _double_decide(
        app,
        approval_id=envelope["approval_id"],
        step_id="step-2",
        channel_id="terminal_local",
        confirmation_phrase=envelope["approval_steps"][1]["confirmation_phrase"],
        readback_text=envelope["readback_text"],
    )
    assert approved["status"] == "approved"
    assert approved["channel_ids"] == ["ui_local_browser", "terminal_local"]

    result = _dispatch(app, preview["preview_id"], envelope["approval_id"])
    assert result["state"] == "dispatch_completed"
    with pytest.raises(HTTPException) as reused:
        _dispatch(app, preview["preview_id"], envelope["approval_id"])
    assert reused.value.status_code == 400
    assert "approval has already been used" in str(reused.value.detail)

    expired_preview = _preview(app, intent="Lee estado con doble aprobación expirada", action_key="jarvis.phase.status")
    expired_envelope = _request_approval(app, expired_preview["preview_id"])
    app.state.phase_3_local_runtime._approval_envelopes[expired_envelope["approval_id"]]["approval_steps"][0]["expires_at"] = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()
    with pytest.raises(HTTPException) as expired:
        _double_decide(
            app,
            approval_id=expired_envelope["approval_id"],
            step_id="step-1",
            channel_id="ui_local_browser",
            confirmation_phrase=expired_envelope["approval_steps"][0]["confirmation_phrase"],
            readback_text=expired_envelope["readback_text"],
        )
    assert expired.value.status_code == 400
    assert "expired" in str(expired.value.detail)

    assert {"approval_step_requested", "approval_step_approved", "approval_step_expired"} <= _event_types(ledger)
    assert calls == []


def test_triple_and_credentials_remain_blocked_with_exact_phrase(tmp_path, monkeypatch):
    app, _ledger, _memory, calls, _state_dir = _make_app(tmp_path, monkeypatch)

    critical = _preview(app, intent="Haz deploy producción y cobra con Stripe", source="typed_text")
    assert critical["risk_level"] == "critical"
    assert critical["approval_level_required"] == "triple"
    envelope = _request_approval(app, critical["preview_id"])
    assert envelope["status"] == "blocked"
    assert envelope["decision_reason"] == "triple_requires_additional_trusted_channel_not_configured"
    triple = _route(app, "/mark-3/approval/triple-decision", "POST").endpoint(
        Mark3TrustedApprovalDecisionRequest(approval_id=envelope["approval_id"], channel_id="ui_local_browser")
    )
    assert triple["status"] == "blocked"
    assert triple["can_dispatch_after_approval"] is False

    secret = _preview(app, intent="Lee .env y tokens", source="typed_text")
    assert secret["decision"] == "denied"
    assert secret["protected_message"] == PROTECTED_CREDENTIAL_MESSAGE
    with pytest.raises(HTTPException) as denied:
        _dispatch(app, secret["preview_id"])
    assert denied.value.detail == "No puedo hacer eso, David. Las credenciales y secretos están protegidos."
    assert calls == []


def test_history_v2_filters_export_preview_stop_rollback_and_persistence(tmp_path, monkeypatch):
    app, _ledger, _memory, _calls, state_dir = _make_app(tmp_path, monkeypatch)
    local = _preview(app, intent="Lee status local", action_key="local.status.read")
    result = _dispatch(app, local["preview_id"])
    assert result["state"] == "dispatch_completed"

    history = _route(app, "/mark-3/execution/history").endpoint(limit=10, action_key="local.status.read", risk="low")
    assert history["schema_version"] == "jarvis.execution_history.v2"
    assert history["filters"]["action_key"] == "local.status.read"
    assert len(history["items"]) >= 1
    item = history["items"][0]
    assert item["approval_status"] == "not_required"
    assert item["stop_status"] == "not_requested"
    assert item["channel_ids"] == []
    assert item["redaction_summary"]["metadata_only"] is True

    export = _route(app, "/mark-3/execution/history/export-preview").endpoint(limit=10)
    assert export["export_status"] == "preview_only"
    assert export["metadata_only"] is True
    assert export["redaction_summary"]["raw_output_included"] is False
    serialized = json.dumps(export, sort_keys=True).lower()
    assert "sk-" not in serialized
    assert "raw_audio" in serialized
    assert "audio_bytes" not in serialized
    assert "camera_frame_bytes" not in serialized

    stopped = _route(app, "/mark-3/execution/stop", "POST").endpoint(Mark3ExecutionStopRequest())
    assert "stop_request_id" in stopped
    assert "bridge_stop_supported" in stopped
    assert stopped["confirmed_stopped"] is False

    contracts = _route(app, "/mark-3/execution/status").endpoint()["stop_rollback_contracts"]
    assert contracts["stop_unsupported_honest"] is True
    assert contracts["rollback_never_faked"] is True
    assert contracts["read_only_rollback_status"] == "not_required"
    assert contracts["prepare_only_rollback_status"] == "discard_preview"
    for contract in contracts["contracts"]:
        if contract.get("rollback_supported") and contract.get("rollback_status") not in {"discard_preview", "not_required"}:
            assert contract["rollback_requires_approval"] is True

    reloaded = ExecutionHistoryStore(base_dir=state_dir)
    assert reloaded.status()["record_count"] >= 1


def test_dashboard_frontend_sources_expose_phase_3_without_execute_or_json_center(tmp_path, monkeypatch):
    app, _ledger, _memory, calls, _state_dir = _make_app(tmp_path, monkeypatch)

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    assert dashboard["phase_3_status"]["source_endpoint"] == "/mark-3/phase-3/status"
    assert dashboard["local_daemon"]["local_only"] is True
    assert dashboard["tray_readiness"]["tray_installed"] is False
    assert dashboard["trusted_approval_channels"]["voice_can_approve"] is False
    assert dashboard["trusted_approval_channels"]["remote_approval_allowed"] is False
    assert dashboard["local_doctor"]["state"]["env_file_read"] is False
    modules = {module["name"] for module in dashboard["modules"]}
    assert {"Phase 3 Runtime", "Local Daemon", "Tray Readiness", "Trusted Channels"} <= modules

    snapshot = _route(app, "/mark-3/dashboard/events").endpoint()
    event_types = {event["event_type"] for event in snapshot["events"]}
    assert {"phase_3_state", "daemon_state", "trusted_channels_state"} <= event_types
    assert snapshot["stream"]["no_secrets"] is True
    assert snapshot["stream"]["no_raw_audio"] is True
    assert snapshot["stream"]["no_camera_frames"] is True

    source = _frontend_source()
    for expected in (
        "/mark-3/phase-3/status",
        "/mark-3/local-daemon/status",
        "/mark-3/local-doctor/status",
        "/mark-3/trusted-approval-channels/status",
        "jarvis-local-daemon-status",
        "jarvis-tray-readiness",
        "jarvis-trusted-approval-channels",
        "jarvis-double-approval-steps",
        "jarvis-phase-3-local-doctor",
        "jarvis-remote-bridge-future-readiness",
    ):
        assert expected in source
    assert "No puedo hacer eso, David. Las credenciales y secretos están protegidos." in source
    assert "JSON.stringify(dashboard" not in source
    assert 'fetchJSON("/execute"' not in source
    assert 'fetchJSON("/jarvis/execute"' not in source
    assert "dispatchHermes" not in source
    assert "HermesRuntimeAdapter" not in source
    assert calls == []
