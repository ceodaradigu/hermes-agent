import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi import HTTPException

from jarvis.api.app import (
    Mark3ExecutionApprovalDecisionRequest,
    Mark3ExecutionDispatchRequest,
    Mark3ExecutionPreviewRequest,
    Mark3ExecutionRequestApprovalRequest,
    Mark3ExecutionStopRequest,
    create_app,
)
from jarvis.memory_brain_v2 import MemoryBrainV2Store
from jarvis.persistent_audit import PersistentAuditLedger
from jarvis.phase_1_governed_execution import PROTECTED_CREDENTIAL_MESSAGE
from jarvis.phase_2_local_assistant_runtime import ACTION_CATALOG, ExecutionHistoryStore


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
PHASE_2_TEST = "tests/jarvis/test_pr_166_phase_2_local_assistant_runtime.py"


class FakeHermesReadAdapter:
    def __init__(self, guard, calls):
        self.guard = guard
        self.calls = calls
        self.interruptions = []

    def run(self, message, **kwargs):
        path = message.rsplit("path:", 1)[-1].strip()
        decision = self.guard("read_file", {
            "path": path,
            "cwd": str(Path(path).resolve().parent),
            "backend": "local",
        })
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
    return _route(app, "/mark-3/execution/preview", "POST").endpoint(
        Mark3ExecutionPreviewRequest(**payload)
    )


def _request_approval(app, preview_id, actor="David"):
    return _route(app, "/mark-3/execution/request-approval", "POST").endpoint(
        Mark3ExecutionRequestApprovalRequest(preview_id=preview_id, actor=actor)
    )


def _decide(app, approval_id, decision="approve", **payload):
    return _route(app, "/mark-3/execution/approval-decision", "POST").endpoint(
        Mark3ExecutionApprovalDecisionRequest(approval_id=approval_id, decision=decision, **payload)
    )


def _dispatch(app, preview_id, approval_id=None):
    return _route(app, "/mark-3/execution/dispatch", "POST").endpoint(
        Mark3ExecutionDispatchRequest(preview_id=preview_id, approval_id=approval_id, actor="David")
    )


def _stop(app, preview_id=None, session_id=None, reason="operator stop"):
    return _route(app, "/mark-3/execution/stop", "POST").endpoint(
        Mark3ExecutionStopRequest(preview_id=preview_id, session_id=session_id, reason=reason)
    )


def _event_types(ledger):
    return {entry["event_type"] for entry in ledger.list_entries(limit=200)}


def _frontend_source():
    paths = [
        WEB / "src/lib/api.ts",
        WEB / "src/pages/JarvisCommandCenterPage.tsx",
    ]
    paths.extend(sorted((WEB / "src/components/jarvis").glob("*.ts")))
    paths.extend(sorted((WEB / "src/components/jarvis").glob("*.tsx")))
    paths.extend(sorted((WEB / "src/hooks/jarvis").glob("*.ts")))
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_phase_2_routes_status_catalog_browser_and_runtime_readiness(tmp_path, monkeypatch):
    app, _ledger, _memory, calls, state_dir = _make_app(tmp_path, monkeypatch)
    route_paths = {route.path for route in app.routes}

    assert "/execute" not in route_paths
    assert "/jarvis/execute" not in route_paths
    for path in (
        "/mark-3/phase-2/status",
        "/mark-3/execution/action-catalog",
        "/mark-3/execution/history",
        "/mark-3/execution/history/{execution_id}",
        "/mark-3/execution/status",
        "/mark-3/approval/status",
        "/mark-3/local-runtime/status",
        "/mark-3/browser-verification/status",
        "/mark-3/execution/preview",
        "/mark-3/execution/request-approval",
        "/mark-3/execution/approval-decision",
        "/mark-3/execution/dispatch",
        "/mark-3/execution/cancel",
        "/mark-3/execution/stop",
    ):
        assert path in route_paths

    phase = _route(app, "/mark-3/phase-2/status").endpoint()
    assert phase["status"] == "implemented_as_local_governed_runtime_macro_phase"
    assert phase["route_readiness"]["generic_execute_absent"] is True
    assert phase["blocked_or_unsupported"]["freeform_shell"] == "denied"
    assert phase["blocked_or_unsupported"]["critical_double_triple"] == "blocked_requires_stronger_approval_not_configured"

    catalog = _route(app, "/mark-3/execution/action-catalog").endpoint()
    action_keys = {action["action_key"] for action in catalog["actions"]}
    assert action_keys == set(ACTION_CATALOG)
    assert "repo.tests.run_allowlisted" in action_keys
    assert "repo.file.read_safe" in action_keys
    assert catalog["allowlist_only"] is True
    assert catalog["freeform_shell_allowed"] is False
    assert catalog["arbitrary_command_allowed"] is False
    for action in catalog["actions"]:
        for required in (
            "action_key",
            "description",
            "allowed_inputs_schema",
            "risk_level",
            "approval_required",
            "timeout_seconds",
            "stop_supported",
            "rollback_supported",
            "audit_event_types",
            "output_redaction",
            "filesystem_scope",
            "network_allowed",
            "external_side_effects",
            "secrets_policy",
            "contract",
        ):
            assert required in action
        assert action["network_allowed"] is False
        assert action["external_side_effects"] is False
    for denied in ("shell_freeform", "arbitrary_command", ".env_read", "secret_read", "deploy", "stripe", "email"):
        assert denied in catalog["denied_actions"]

    status = _route(app, "/mark-3/execution/status").endpoint()
    assert {"none", "soft", "normal", "strong", "double", "triple", "blocked", "unsupported"} <= set(status["approval_levels"])
    assert status["safety"]["strong_approval_v2"] is True
    assert status["safety"]["approvals_single_use"] is True
    assert status["safety"]["voice_can_submit_intent_but_not_approve"] is True
    assert status["execution_history"]["metadata_only"] is True
    assert str(state_dir) in status["local_runtime"]["state_dir_contract"]["execution_history_path"]

    runtime = _route(app, "/mark-3/local-runtime/status").endpoint()
    assert runtime["daemon_status"] in {"readiness_contract_only", "running_embedded_local_api_process"}
    assert runtime["tray_status"] in {"readiness_contract_only", "not_installed"}
    assert runtime["local_runtime_ready"] is True
    assert runtime["startup_mode"] == "manual"
    assert runtime["background_listening_enabled"] is False
    assert runtime["auto_start_enabled"] is False
    assert runtime["user_opt_in_required"] is True
    assert runtime["privacy_contract"]["no_auto_mic"] is True
    assert runtime["privacy_contract"]["no_auto_camera"] is True

    browser = _route(app, "/mark-3/browser-verification/status").endpoint()
    checks = {check["name"]: check for check in browser["checks"]}
    assert checks["api_reachability"]["passed"] is True
    assert checks["voice_capability_check"]["passed"] is True
    assert checks["approval_panel_render_check"]["passed"] is True
    assert checks["event_stream_check"]["passed"] is True
    assert checks["audit_status_check"]["passed"] is True
    assert checks["memory_status_check"]["passed"] is True
    assert checks["execution_history_check"]["passed"] is True
    assert checks["no_auto_get_user_media"]["passed"] is True
    assert checks["no_execute_route"]["passed"] is True
    assert checks["no_frontend_direct_hermes"]["passed"] is True
    assert calls == []


def test_strong_approval_v2_levels_high_critical_expiry_reuse_and_voice_wake_denials(tmp_path, monkeypatch):
    app, ledger, _memory, calls, _state_dir = _make_app(tmp_path, monkeypatch)

    high_contract = replace(ACTION_CATALOG["jarvis.phase.status"], risk_level="high", approval_required="strong")
    monkeypatch.setitem(ACTION_CATALOG, "jarvis.phase.status", high_contract)
    high = _preview(app, intent="Lee estado de fase con confirmación fuerte", action_key="jarvis.phase.status")
    assert high["risk_level"] == "high"
    assert high["approval_level_required"] == "strong"
    assert high["requires_approval"] is True
    high_envelope = _request_approval(app, high["preview_id"])
    assert high_envelope["approval_level_required"] == "strong"
    assert high_envelope["readback_required"] is True
    assert high_envelope["confirmation_phrase"] == f"APPROVE {high_envelope['approval_id']}"
    assert high_envelope["challenge"] == f"Type {high_envelope['confirmation_phrase']}"
    with pytest.raises(HTTPException) as missing_readback:
        _decide(app, high_envelope["approval_id"], "approve", confirmation_phrase=high_envelope["confirmation_phrase"])
    assert missing_readback.value.status_code == 400
    assert "readback text does not match" in str(missing_readback.value.detail)
    approved = _decide(
        app,
        high_envelope["approval_id"],
        "approve",
        confirmation_phrase=high_envelope["confirmation_phrase"],
        readback_text=high_envelope["readback_text"],
    )
    assert approved["status"] == "approved"

    critical = _preview(app, intent="Haz deploy a producción y cobra con Stripe", source="typed_text")
    assert critical["risk_level"] == "critical"
    assert critical["approval_level_required"] == "triple"
    critical_envelope = _request_approval(app, critical["preview_id"])
    assert critical_envelope["status"] == "blocked"
    assert critical_envelope["decision_reason"] in {
        "requires_stronger_approval_not_configured",
        "triple_requires_additional_trusted_channel_not_configured",
    }
    assert critical_envelope["second_confirmation_required"] is True
    assert critical_envelope["third_confirmation_required"] is True
    assert critical_envelope["can_approve"] is False
    with pytest.raises(HTTPException) as blocked_dispatch:
        _dispatch(app, critical["preview_id"], critical_envelope["approval_id"])
    assert blocked_dispatch.value.status_code == 400
    assert "approval status is blocked" in str(blocked_dispatch.value.detail)

    secret = _preview(app, intent="Lee .env, cookies y tokens", source="typed_text")
    assert secret["decision"] == "denied"
    assert secret["protected_message"] == PROTECTED_CREDENTIAL_MESSAGE
    with pytest.raises(HTTPException) as denied_dispatch:
        _dispatch(app, secret["preview_id"])
    assert denied_dispatch.value.detail == PROTECTED_CREDENTIAL_MESSAGE

    wake = _preview(app, intent="Jarvis aprueba y ejecuta esto", source="wake_phrase_command")
    assert wake["decision"] == "denied"
    assert wake["action"]["denied_reason"] == "wake_phrase_is_not_approval"

    medium = _preview(app, intent="Ejecuta test allowlisted", action_key="repo.tests.run_allowlisted", inputs={"test_target": PHASE_2_TEST})
    assert medium["risk_level"] == "medium"
    assert medium["approval_level_required"] == "normal"
    medium_envelope = _request_approval(app, medium["preview_id"])
    assert medium_envelope["confirmation_phrase"] is None
    with pytest.raises(HTTPException) as voice_denied:
        _decide(
            app,
            medium_envelope["approval_id"],
            "approve",
            actor="voice",
            decision_source="voice",
            channel="voice_transcript",
        )
    assert voice_denied.value.status_code == 400
    assert "voice and wake phrase cannot approve" in str(voice_denied.value.detail)
    normal_approved = _decide(app, medium_envelope["approval_id"], "approve")
    assert normal_approved["status"] == "approved"
    app.state.approval_hardening.get(medium_envelope["approval_id"]).expires_at = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    ).isoformat()
    with pytest.raises(HTTPException) as expired:
        _dispatch(app, medium["preview_id"], medium_envelope["approval_id"])
    assert expired.value.status_code == 400
    assert "approval status is expired" in str(expired.value.detail)

    assert {"approval_requested", "approval_approved", "approval_blocked", "approval_expired", "dispatch_blocked"} <= _event_types(ledger)
    assert calls == []


def test_allowlisted_dispatch_hermes_bridge_history_persistence_and_no_secrets(tmp_path, monkeypatch):
    app, ledger, _memory, calls, state_dir = _make_app(tmp_path, monkeypatch)

    local = _preview(app, intent="Lee status local", action_key="local.status.read")
    assert local["decision"] == "allowed"
    local_result = _dispatch(app, local["preview_id"])
    assert local_result["state"] == "dispatch_completed"
    assert local_result["dispatch"]["hermes_called"] is False
    assert local_result["dispatch"]["status"] == "completed"

    target = tmp_path / "safe.txt"
    target.write_text("safe local content", encoding="utf-8")
    read = _preview(app, intent="Lee archivo local exacto", action_key="repo.file.read_safe", inputs={"path": str(target)})
    assert read["decision"] == "requires_approval"
    assert read["approval_level_required"] == "normal"
    with pytest.raises(HTTPException) as no_approval:
        _dispatch(app, read["preview_id"])
    assert no_approval.value.status_code == 400
    assert "approval required" in str(no_approval.value.detail)

    envelope = _request_approval(app, read["preview_id"])
    assert envelope["action_key"] == "repo.file.read_safe"
    assert envelope["approval_level_required"] == "normal"
    assert envelope["readback_required"] is False
    assert envelope["confirmation_phrase"] is None
    approved = _decide(app, envelope["approval_id"], "approve")
    assert approved["status"] == "approved"
    read_result = _dispatch(app, read["preview_id"], envelope["approval_id"])
    assert read_result["state"] == "dispatch_completed"
    assert read_result["hermes_dispatch_allowed"] is True
    assert len(calls) == 1
    assert Path(calls[0]["path"]).resolve() == target.resolve()

    with pytest.raises(HTTPException) as reused:
        _dispatch(app, read["preview_id"], envelope["approval_id"])
    assert reused.value.status_code == 400
    assert "approval has already been used" in str(reused.value.detail)

    history = _route(app, "/mark-3/execution/history").endpoint(limit=10)
    assert history["read_only"] is True
    assert history["status"]["metadata_only"] is True
    assert history["status"]["persistent"] is True
    assert history["status"]["contains_secret"] is False
    assert history["status"]["contains_credential"] is False
    assert history["status"]["contains_raw_audio"] is False
    assert history["status"]["contains_camera_frame"] is False
    assert len(history["items"]) >= 2
    keys = {item["action_key"] for item in history["items"]}
    assert {"local.status.read", "repo.file.read_safe"} <= keys
    for item in history["items"]:
        assert item["contains_secret"] is False
        assert item["contains_credential"] is False
        assert item["contains_raw_audio"] is False
        assert item["contains_camera_frame"] is False
        assert item["redaction_summary"]["metadata_only"] is True
        assert item["redaction_summary"]["raw_output_stored"] is False
    detail = _route(app, "/mark-3/execution/history/{execution_id}").endpoint(history["items"][0]["execution_id"])
    assert detail["execution_id"] == history["items"][0]["execution_id"]

    reloaded = ExecutionHistoryStore(base_dir=state_dir)
    assert reloaded.status()["record_count"] >= 2
    assert {item["action_key"] for item in reloaded.list(limit=10)} >= {"local.status.read", "repo.file.read_safe"}
    serialized = json.dumps(history, sort_keys=True).lower()
    assert "safe local content" not in serialized
    assert "sk-" not in serialized
    assert ledger.verify_chain().valid is True


def test_stop_rollback_voice_wake_and_side_effect_contracts_are_honest(tmp_path, monkeypatch):
    app, ledger, _memory, calls, _state_dir = _make_app(tmp_path, monkeypatch)

    catalog = _route(app, "/mark-3/execution/action-catalog").endpoint()
    contracts = {action["action_key"]: action["contract"] for action in catalog["actions"]}
    assert contracts["local.status.read"]["rollback_status"] == "not_required"
    assert contracts["repo.file.read_safe"]["stop_supported"] is True
    assert contracts["jarvis.execution.preview"]["rollback_status"] == "discard_preview"
    for action in catalog["actions"]:
        if action["external_side_effects"]:
            assert action["contract"]["rollback_plan"] not in {"", "not_required"}
            assert action["contract"]["rollback_requires_approval"] is True

    local = _preview(app, intent="Lee status local", action_key="local.status.read")
    stopped = _stop(app, preview_id=local["preview_id"])
    assert stopped["status"] == "stop_requested_pending_or_unsupported"
    assert "unsupported" in stopped["reason"]
    assert {"stop_requested", "stop_unsupported"} <= _event_types(ledger)

    low_confidence = _preview(
        app,
        intent="revisa estado local",
        source="voice_transcript",
        transcript_confidence=0.31,
    )
    assert low_confidence["decision"] == "requires_clarification"
    assert low_confidence["unsupported_reason"] == "low_confidence_voice_requires_clarification"
    assert low_confidence["hermes_dispatch_allowed"] is False

    voice = _route(app, "/mark-3/voice-runtime/status").endpoint()
    phase2_voice = voice["phase_2_runtime"]
    assert phase2_voice["voice_runtime_diagnostics"]["voice_intent_submitted_to_preview"] is True
    assert phase2_voice["voice_runtime_diagnostics"]["voice_can_approve"] is False
    assert phase2_voice["voice_runtime_diagnostics"]["raw_audio_sent_to_backend"] is False
    assert phase2_voice["wake_runtime_readiness"]["provider_status"] in {"disabled", "not_configured"}
    assert phase2_voice["wake_runtime_readiness"]["wake_always_on_real"] is False
    assert phase2_voice["wake_runtime_readiness"]["wake_phrase_can_approve"] is False
    assert phase2_voice["privacy_status"]["no_auto_mic"] is True
    assert phase2_voice["privacy_status"]["no_backend_raw_audio"] is True
    assert calls == []


def test_dashboard_and_event_stream_expose_phase_2_without_json_center_or_direct_hermes(tmp_path, monkeypatch):
    app, _ledger, _memory, _calls, _state_dir = _make_app(tmp_path, monkeypatch)

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    assert dashboard["phase_2_status"]["source_endpoint"] == "/mark-3/phase-2/status"
    assert dashboard["action_catalog"]["allowlist_only"] is True
    assert dashboard["execution_history"]["read_only"] is True
    assert dashboard["local_runtime"]["background_listening_enabled"] is False
    assert dashboard["local_runtime"]["auto_start_enabled"] is False
    assert dashboard["local_runtime"]["user_opt_in_required"] is True
    assert dashboard["browser_verification"]["all_static_checks_passed"] is True
    assert dashboard["safety"]["phase_2_allowlisted_actions_only"] is True
    assert dashboard["safety"]["execution_history_metadata_only"] is True
    modules = {module["name"] for module in dashboard["modules"]}
    assert {"Phase 2 Runtime", "Action Catalog", "Execution History"} <= modules

    snapshot = _route(app, "/mark-3/dashboard/events").endpoint()
    event_types = {event["event_type"] for event in snapshot["events"]}
    assert {"phase_2_state", "action_catalog_state", "execution_history_state"} <= event_types
    assert snapshot["stream"]["no_frontend_execution"] is True
    assert snapshot["stream"]["no_secrets"] is True
    assert snapshot["stream"]["no_raw_audio"] is True
    assert snapshot["stream"]["no_camera_frames"] is True

    source = _frontend_source()
    assert "/mark-3/phase-2/status" in source
    assert "/mark-3/execution/action-catalog" in source
    assert "/mark-3/execution/history" in source
    assert "Action Catalog Allowlist" in source
    assert "Execution History" in source
    assert "Browser Verification" in source
    assert "jarvis-action-catalog-drawer" in source
    assert "jarvis-execution-history-drawer" in source
    assert "jarvis-browser-verification-checklist" in source
    assert "jarvis-approval-summary" in source
    assert "No auto getUserMedia on load" in source
    assert "Particle" in source or "particles" in source
    assert "smart bar" in source.casefold() or "Smart Bar" in source
    assert "JSON.stringify(dashboard" not in source
    assert 'fetchJSON("/execute"' not in source
    assert 'fetchJSON("/jarvis/execute"' not in source
    assert 'fetch("/execute"' not in source
    for forbidden in (
        "mark_3_hermes_runtime_bridge.execute",
        "HermesRuntimeAdapter",
        "dispatchHermes",
        "callHermes",
        "child_process",
        "shell_exec",
    ):
        assert forbidden not in source
