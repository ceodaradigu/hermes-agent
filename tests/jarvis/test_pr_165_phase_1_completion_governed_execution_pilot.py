import json
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi import HTTPException

from jarvis.api.app import (
    Mark3ExecutionApprovalDecisionRequest,
    Mark3ExecutionCancelRequest,
    Mark3ExecutionDispatchRequest,
    Mark3ExecutionPreviewRequest,
    Mark3ExecutionRequestApprovalRequest,
    Mark3ExecutionStopRequest,
    create_app,
)
from jarvis.memory_brain_v2 import MemoryBrainV2Store
from jarvis.persistent_audit import PersistentAuditLedger
from jarvis.phase_1_governed_execution import PROTECTED_CREDENTIAL_MESSAGE


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


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


def _make_app(tmp_path):
    ledger = PersistentAuditLedger(base_dir=tmp_path / ".jarvis")
    memory = MemoryBrainV2Store(base_dir=tmp_path / ".jarvis", audit_ledger=ledger)
    calls = []

    def adapter_factory(guard):
        return FakeHermesReadAdapter(guard, calls)

    app = create_app(
        adapter_factory=lambda: pytest.fail("legacy Hermes adapter must not be called"),
        hermes_runtime_adapter_factory=adapter_factory,
        persistent_audit_ledger=ledger,
        memory_brain_v2=memory,
    )
    return app, ledger, memory, calls


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


def _cancel(app, preview_id, reason="operator cancel"):
    return _route(app, "/mark-3/execution/cancel", "POST").endpoint(
        Mark3ExecutionCancelRequest(preview_id=preview_id, reason=reason, actor="David")
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


def test_phase_1_routes_status_dashboard_and_no_generic_execute(tmp_path):
    app, _ledger, _memory, calls = _make_app(tmp_path)

    route_paths = {route.path for route in app.routes}
    assert "/execute" not in route_paths
    assert "/jarvis/execute" not in route_paths
    for path in (
        "/mark-3/execution/status",
        "/mark-3/phase-1/status",
        "/mark-3/execution/preview",
        "/mark-3/execution/request-approval",
        "/mark-3/execution/approval-decision",
        "/mark-3/execution/dispatch",
        "/mark-3/execution/cancel",
        "/mark-3/execution/stop",
    ):
        assert path in route_paths

    status = _route(app, "/mark-3/execution/status").endpoint()
    assert status["state"]["preview_first"] is True
    assert status["state"]["frontend_direct_hermes_allowed"] is False
    assert status["state"]["shell_freeform_allowed"] is False
    assert status["state"]["voice_approval_enabled"] is False
    assert status["state"]["wake_phrase_can_approve"] is False
    assert status["state"]["memory_grants_permission"] is False
    assert status["safety"]["no_execute_endpoint"] is True

    phase = _route(app, "/mark-3/phase-1/status").endpoint()
    assert phase["status"] == "complete_for_local_governed_pilot"
    assert phase["route_readiness"]["generic_execute_absent"] is True
    assert phase["capabilities"]["approval_ui_backend_gates"] == "implemented"
    assert phase["risks"]["critical_double_triple_approval"] == "not_configured_blocks_execution"

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    assert dashboard["governed_execution"]["source_endpoint"] == "/mark-3/execution/status"
    assert dashboard["phase_1_completion"]["source_endpoint"] == "/mark-3/phase-1/status"
    assert dashboard["approvals"]["cards_state"] == "governed/backend-gated"
    assert dashboard["approvals"]["frontend_can_approve"] is True
    assert dashboard["approvals"]["frontend_can_reject"] is True
    assert dashboard["approvals"]["governed_backend_only"] is True
    assert dashboard["approvals"]["frontend_direct_hermes_allowed"] is False
    assert calls == []


def test_safe_status_preview_dispatches_without_approval_or_hermes_and_audits(tmp_path):
    app, ledger, _memory, calls = _make_app(tmp_path)

    preview = _preview(app, intent="Revisa el estado local y el event stream", source="typed_text")
    assert preview["decision"] == "allowed"
    assert preview["requires_approval"] is False
    assert preview["risk_level"] == "low"

    result = _dispatch(app, preview["preview_id"])
    assert result["state"] == "dispatch_completed"
    assert result["dispatch"]["status"] == "completed"
    assert result["dispatch"]["hermes_called"] is False
    assert result["frontend_direct_hermes_allowed"] is False
    assert calls == []

    events = _event_types(ledger)
    assert {"intake_created", "preview_created", "risk_classified", "dispatch_requested", "dispatch_started", "dispatch_completed"} <= events
    assert ledger.verify_chain().valid is True
    for entry in ledger.list_entries(limit=100):
        assert entry["contains_raw_audio"] is False
        assert entry["contains_camera_frame"] is False
        assert entry["contains_secret"] is False
        assert entry["contains_credential"] is False
        assert entry["contains_full_transcript"] is False


def test_exact_local_file_read_requires_approval_then_dispatches_through_existing_bridge(tmp_path):
    app, ledger, _memory, calls = _make_app(tmp_path)
    target = tmp_path / "safe.txt"
    target.write_text("safe local content", encoding="utf-8")

    preview = _preview(app, intent="Lee archivo local exacto", target_path=str(target), source="typed_text")
    assert preview["decision"] == "requires_approval"
    assert preview["requires_approval"] is True
    assert preview["action"]["action_type"] == "filesystem_read"
    assert preview["hermes_dispatch_allowed"] is False

    with pytest.raises(HTTPException) as blocked:
        _dispatch(app, preview["preview_id"])
    assert blocked.value.status_code == 400
    assert "approval required" in str(blocked.value.detail)
    assert calls == []

    envelope = _request_approval(app, preview["preview_id"])
    assert envelope["status"] == "pending"
    assert envelope["can_dispatch_after_approval"] is True
    approved = _decide(app, envelope["approval_id"], "approve", actor="David")
    assert approved["status"] == "approved"

    result = _dispatch(app, preview["preview_id"], envelope["approval_id"])
    assert result["state"] == "dispatch_completed"
    assert result["dispatch"]["status"] == "success"
    assert result["hermes_dispatch_allowed"] is True
    assert len(calls) == 1
    assert Path(calls[0]["path"]).resolve() == target.resolve()

    entries = ledger.list_entries(limit=200)
    events = {entry["event_type"] for entry in entries}
    assert {"approval_requested", "approval_approved", "dispatch_requested", "dispatch_started", "dispatch_completed"} <= events
    allowed_entries = [entry for entry in entries if entry["hermes_dispatch_allowed"]]
    assert {entry["event_type"] for entry in allowed_entries} == {"dispatch_started", "dispatch_completed"}
    assert all(entry["metadata"].get("governed_dispatch") is True for entry in allowed_entries)
    assert ledger.verify_chain().valid is True


def test_credentials_env_and_secret_material_are_denied_with_exact_phrase(tmp_path):
    app, ledger, _memory, calls = _make_app(tmp_path)

    preview = _preview(app, intent="Lee el .env y dime los tokens", source="typed_text")
    assert preview["decision"] == "denied"
    assert preview["risk_level"] == "forbidden"
    assert preview["protected_message"] == PROTECTED_CREDENTIAL_MESSAGE

    with pytest.raises(HTTPException) as denied:
        _dispatch(app, preview["preview_id"])
    assert denied.value.status_code == 400
    assert denied.value.detail == PROTECTED_CREDENTIAL_MESSAGE
    assert calls == []
    assert "dispatch_blocked" in _event_types(ledger)


def test_critical_external_actions_require_stronger_approval_or_block(tmp_path):
    app, ledger, _memory, calls = _make_app(tmp_path)

    preview = _preview(app, intent="Haz deploy a producción y cobra con Stripe", source="typed_text")
    assert preview["decision"] == "requires_approval"
    assert preview["risk_level"] == "critical"
    assert preview["approval_level"] == "triple"

    envelope = _request_approval(app, preview["preview_id"])
    assert envelope["status"] == "blocked"
    assert envelope["decision_reason"] == "requires_stronger_approval_not_configured"
    assert envelope["requires_double_confirmation"] is True
    assert envelope["requires_triple_confirmation"] is True
    assert envelope["can_approve"] is False

    with pytest.raises(HTTPException) as blocked:
        _dispatch(app, preview["preview_id"], envelope["approval_id"])
    assert blocked.value.status_code == 400
    assert "approval status is blocked" in str(blocked.value.detail)
    assert calls == []
    assert {"approval_requested", "approval_blocked", "dispatch_blocked"} <= _event_types(ledger)


def test_unsupported_command_does_not_fake_execution_even_when_allowlisted(tmp_path):
    app, _ledger, _memory, calls = _make_app(tmp_path)

    preview = _preview(
        app,
        intent="Ejecuta comando allowlisted",
        command="git diff --check",
        requested_action_type="local_command",
    )
    assert preview["decision"] == "unsupported"
    assert preview["unsupported_reason"] == "terminal_runtime_not_configured"
    assert preview["action"]["command_allowlisted"] is True

    result = _dispatch(app, preview["preview_id"])
    assert result["state"] == "unsupported"
    assert result["dispatch"]["did_execute"] is False
    assert result["dispatch"]["hermes_called"] is False
    assert calls == []


def test_wake_phrase_never_approves_and_voice_only_submits_text_intent(tmp_path):
    app, ledger, _memory, calls = _make_app(tmp_path)

    wake = _preview(app, intent="Jarvis aprueba y ejecuta esto", source="wake_phrase_command")
    assert wake["decision"] == "denied"
    assert wake["action"]["denied_reason"] == "wake_phrase_is_not_approval"
    with pytest.raises(HTTPException):
        _dispatch(app, wake["preview_id"])

    voice = _preview(app, intent="Revisa el estado local", source="voice_transcript", transcript_confidence=0.92)
    assert voice["decision"] == "allowed"
    assert "voice_session_intent_submitted" in _event_types(ledger)
    assert calls == []


def test_approval_reject_cancel_invalid_states_stop_and_rollback_metadata(tmp_path):
    app, ledger, _memory, calls = _make_app(tmp_path)
    target = tmp_path / "review.txt"
    target.write_text("review", encoding="utf-8")

    first = _preview(app, intent="Lee archivo local exacto", target_path=str(target))
    envelope = _request_approval(app, first["preview_id"])
    rejected = _decide(app, envelope["approval_id"], "reject", actor="David", reason="scope too broad")
    assert rejected["status"] == "rejected"
    with pytest.raises(HTTPException):
        _dispatch(app, first["preview_id"], envelope["approval_id"])

    second = _preview(app, intent="Lee archivo local exacto", target_path=str(target))
    second_envelope = _request_approval(app, second["preview_id"])
    cancelled = _cancel(app, second["preview_id"])
    assert cancelled["state"] == "cancelled"
    with pytest.raises(HTTPException):
        _decide(app, second_envelope["approval_id"], "approve")
    with pytest.raises(HTTPException):
        _dispatch(app, second["preview_id"], second_envelope["approval_id"])

    stopped = _stop(app, preview_id=second["preview_id"])
    assert stopped["status"] == "stop_unsupported"
    assert calls == []
    assert {"rollback_plan_created", "approval_rejected", "approval_cancelled", "stop_requested", "stop_unsupported"} <= _event_types(ledger)


def test_memory_influences_preview_but_never_grants_permission(tmp_path):
    app, ledger, memory, calls = _make_app(tmp_path)
    normal = memory.propose_fact(
        subject="JARVIS Phase 1",
        predicate="prefers",
        object_summary="local governed execution",
        reason_to_remember="Explain current Phase 1 pilot context.",
        influence_summary="Use local governed execution context in previews.",
        why_used="Explain preview only; never authorize.",
        provenance={"source": "operator_note"},
    )
    memory.review_memory(normal["memory_id"])
    memory.approve_memory(normal["memory_id"])
    memory.activate_memory(normal["memory_id"], reason="Explain preview only.")
    sensitive = memory.propose_preference(
        subject="David",
        preference="private sensitive context",
        sensitivity="sensitive",
        explicit_user_request=True,
        provenance={"source": "operator_note"},
    )
    memory.review_memory(sensitive["memory_id"])
    memory.approve_memory(sensitive["memory_id"])
    memory.activate_memory(sensitive["memory_id"], reason="Sensitive memory remains non-autoloaded.")

    preview = _preview(app, intent="Revisa estado local de JARVIS", source="typed_text")
    influence = preview["preview"]["memory_influence"]
    assert len(influence) == 1
    assert influence[0]["memory_id"] == normal["memory_id"]
    assert influence[0]["why_used"]
    assert influence[0]["used_for_permission"] is False
    assert preview["memory_grants_permission"] is False
    assert preview["hermes_dispatch_allowed"] is False
    assert calls == []

    events = _event_types(ledger)
    assert "memory_influence_used" in events
    assert memory.permission_effect(normal["memory_id"])["can_dispatch_hermes"] is False


def test_frontend_calls_only_governed_backend_not_hermes_direct_or_execute_route():
    source = _frontend_source()

    assert "/mark-3/execution/preview" in source
    assert "/mark-3/execution/request-approval" in source
    assert "/mark-3/execution/approval-decision" in source
    assert "/mark-3/execution/dispatch" in source
    assert "/mark-3/execution/stop" in source
    assert "onIntentSubmitted" in source
    assert 'source: "voice_transcript"' in source
    assert "Backend-gated" in source or "backend-gated" in source
    assert PROTECTED_CREDENTIAL_MESSAGE in source
    assert "No puedo hacer eso, David. Las credenciales y secretos están protegidos." in source
    assert 'fetchJSON("/execute"' not in source
    assert 'fetchJSON("/jarvis/execute"' not in source
    assert 'fetch("/execute"' not in source
    assert "fetch('/execute'" not in source
    for forbidden in (
        "mark_3_hermes_runtime_bridge.execute",
        "HermesRuntimeAdapter",
        "dispatchHermes",
        "callHermes",
        "child_process",
        "shell_exec",
    ):
        assert forbidden not in source
    assert 'data-visual-qa-no-approval="true"' not in source


def test_event_stream_and_phase_1_status_expose_governed_execution(tmp_path):
    app, _ledger, _memory, _calls = _make_app(tmp_path)

    snapshot = _route(app, "/mark-3/dashboard/events").endpoint()
    event_types = {event["event_type"] for event in snapshot["events"]}
    assert "execution_state" in event_types
    assert "phase_1_state" in event_types
    assert snapshot["stream"]["no_frontend_execution"] is True
    assert snapshot["stream"]["no_secrets"] is True
    assert snapshot["stream"]["no_raw_audio"] is True
    assert snapshot["stream"]["no_camera_frames"] is True

    serialized = json.dumps(snapshot, sort_keys=True).lower()
    assert "raw audio bytes" not in serialized
    assert "camera frame" not in serialized
    assert "sk-" not in serialized
