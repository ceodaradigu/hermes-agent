from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (
    ApprovalDecisionPreviewRequest,
    ApprovalGatePreviewRequest,
    ApprovalPreviewRequest,
    create_app,
)
from jarvis.approval_audit import ApprovalAuditEventType, ApprovalAuditTrail
from jarvis.approval_hardening import (
    ApprovalHardeningService,
    ApprovalKind,
    ApprovalStatus,
    StrongApprovalPolicy,
    build_context_fingerprint,
)
from jarvis.command_center import build_command_center_view_model
from jarvis.operational_consolidation import NEXT_MACRO_PR, build_operational_system_status
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.permission_gates import PermissionGateResult, evaluate_permission_gate


DOC = Path("docs/jarvis-post-s-real-approval-audit-permission-hardening.md")
DANGEROUS_ROUTES = (
    "/approvals/execute",
    "/approvals/run",
    "/approvals/deploy",
    "/approvals/send",
    "/approvals/install",
    "/approvals/pay",
    "/approvals/read-secret",
    "/approvals/start-camera",
    "/approvals/start-microphone",
    "/approvals/capture-screen",
)


def _context(**overrides):
    context = {"action_type": "prepare_report", "target": "local-preview", "environment": "preview"}
    context.update(overrides)
    return context


def _approved(service: ApprovalHardeningService, context=None, *, kind=ApprovalKind.NORMAL):
    context = context or _context()
    record = service.request(action_type=context["action_type"], context=context, approval_kind=kind)
    phrase = record.user_confirmation_phrase if kind == ApprovalKind.STRONG else None
    return service.decide(record.approval_id, "approved", confirmation_phrase=phrase)


def _route(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route
    return None


def test_status_is_post_s_prepare_only_without_phase_t_or_runtime():
    status = build_operational_system_status().to_dict()
    assert status["approval_hardening_available"] is True
    assert status["approval_audit_available"] is True
    assert status["strong_approval_policy_available"] is True
    assert status["permission_gates_available"] is True
    assert status["no_phase_t"] is True
    assert status["runtime_execution_enabled"] is False
    assert status["side_effects_enabled"] is False
    assert NEXT_MACRO_PR == "Post-S Macro 5 - Memory, Personal OS & Scheduler Real"


def test_approval_request_starts_pending_and_approved_record_executes_nothing():
    service = ApprovalHardeningService()
    record = service.request(action_type="prepare_report", context=_context())
    assert record.status == ApprovalStatus.PENDING
    approved = service.decide(record.approval_id, "approved")
    assert approved.status == ApprovalStatus.APPROVED
    assert approved.safe_to_execute is False
    assert approved.prepare_only is True


@pytest.mark.parametrize("terminal_status", ["pending", "rejected", "revoked", "expired"])
def test_non_valid_approval_states_block_gate(terminal_status):
    service = ApprovalHardeningService()
    context = _context()
    if terminal_status == "expired":
        record = service.request(
            action_type=context["action_type"],
            context=context,
            expires_at=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
        )
        service.refresh_expiration(record)
    else:
        record = service.request(action_type=context["action_type"], context=context)
        if terminal_status == "rejected":
            service.decide(record.approval_id, "rejected")
        elif terminal_status == "revoked":
            service.decide(record.approval_id, "approved")
            service.revoke(record.approval_id)
    result = evaluate_permission_gate(context, record)
    assert result.allowed is False
    assert result.safe_to_execute is False
    assert result.approval_status == terminal_status


def test_normal_approval_never_satisfies_strong_required_gate():
    service = ApprovalHardeningService()
    context = _context(production=True)
    record = _approved(service, context)
    result = evaluate_permission_gate(context, record)
    assert record.status == ApprovalStatus.APPROVED
    assert result.allowed is False
    assert result.requires_strong_approval is True
    assert "strong approval" in result.missing_requirements


def test_strong_approval_requires_exact_confirmation_and_then_only_allows_future_execution():
    service = ApprovalHardeningService()
    context = _context(production=True)
    record = service.request(action_type=context["action_type"], context=context, approval_kind=ApprovalKind.STRONG)
    with pytest.raises(ValueError, match="confirmation phrase"):
        service.decide(record.approval_id, "approved", confirmation_phrase="wrong")
    approved = service.decide(record.approval_id, "approved", confirmation_phrase=record.user_confirmation_phrase)
    result = evaluate_permission_gate(context, approved)
    assert result.allowed is True
    assert result.safe_to_execute is False
    assert "future execution only" in result.reason


@pytest.mark.parametrize(
    "context",
    [
        _context(production=True),
        _context(action_type="deploy"),
        _context(action_type="payment"),
        _context(secret_access=True),
        _context(private_data=True),
        _context(identity=True),
        _context(memory_activation=True),
        _context(action_type="install dependencies"),
        _context(command="pytest"),
        _context(external_call=True),
        _context(action_type="send email"),
        _context(camera=True),
        _context(microphone=True),
        _context(screen=True),
        _context(robot=True),
        _context(drone=True),
        _context(device_control=True),
        _context(runtime_change=True),
        _context(policy_change=True),
        _context(security_change=True),
    ],
)
def test_sensitive_categories_require_strong_approval(context):
    risk, requires_strong, categories = StrongApprovalPolicy().classify(context)
    gate = evaluate_permission_gate(context)
    assert requires_strong is True
    assert categories
    assert risk.value in {"high", "critical"}
    assert gate.allowed is False
    assert gate.requires_strong_approval is True
    assert "strong approval" in gate.missing_requirements


@pytest.mark.parametrize("field", ["command", "target", "amount", "environment", "tool_name"])
def test_context_fingerprint_changes_for_relevant_fields(field):
    first = _context(**{field: "one"})
    second = _context(**{field: "two"})
    assert build_context_fingerprint(first) != build_context_fingerprint(second)


def test_context_mismatch_blocks_and_is_audited():
    service = ApprovalHardeningService()
    record = _approved(service)
    result = evaluate_permission_gate(_context(target="changed"), record, audit_trail=service.audit_trail)
    assert result.allowed is False
    assert result.context_matches is False
    assert ApprovalAuditEventType.APPROVAL_CONTEXT_MISMATCH in {
        event.event_type for event in service.audit_trail.list_events(record.approval_id)
    }


def test_audit_records_lifecycle_and_redacts_sensitive_values():
    audit = ApprovalAuditTrail()
    service = ApprovalHardeningService(audit_trail=audit)
    approved = _approved(service)
    service.revoke(approved.approval_id)
    rejected = service.request(action_type="prepare_other", context={"action_type": "prepare_other"})
    service.decide(rejected.approval_id, "rejected")
    expired = service.request(
        action_type="prepare_expired",
        context={"action_type": "prepare_expired"},
        expires_at=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
    )
    service.refresh_expiration(expired)
    audit.append(
        ApprovalAuditEventType.APPROVAL_GATE_DENIED,
        "sensitive",
        metadata={"token": "abc", "nested": {"password": "xyz"}, "safe": "read .env secret"},
    )
    serialized = str(audit.preview()).lower()
    event_types = {event.event_type for event in audit.list_events()}
    for expected in (
        ApprovalAuditEventType.APPROVAL_REQUESTED,
        ApprovalAuditEventType.APPROVAL_APPROVED,
        ApprovalAuditEventType.APPROVAL_REJECTED,
        ApprovalAuditEventType.APPROVAL_REVOKED,
        ApprovalAuditEventType.APPROVAL_EXPIRED,
    ):
        assert expected in event_types
    assert "'token': 'abc'" not in serialized
    assert "'password': 'xyz'" not in serialized
    assert ".env" not in serialized


def test_permission_gate_defaults_are_denied_and_never_safe_to_execute():
    result = PermissionGateResult()
    assert result.allowed is False
    assert result.safe_to_execute is False
    assert PermissionGateResult(allowed=True, safe_to_execute=True).safe_to_execute is False


def test_api_preview_routes_are_control_plane_only_and_dangerous_routes_absent():
    app = create_app()
    status = _route(app, "/approvals/status", "GET").endpoint()
    policy = _route(app, "/approvals/policy", "GET").endpoint()
    request_route = _route(app, "/approvals/preview-request", "POST")
    decision_route = _route(app, "/approvals/preview-decision", "POST")
    gate_route = _route(app, "/approvals/preview-gate", "POST")
    record = request_route.endpoint(ApprovalPreviewRequest(action_type="prepare_report", context=_context()))
    decided = decision_route.endpoint(
        ApprovalDecisionPreviewRequest(approval_id=record["approval_id"], decision="approved")
    )
    gate = gate_route.endpoint(ApprovalGatePreviewRequest(approval_id=record["approval_id"], context=_context()))
    audit = _route(app, "/approvals/audit-preview", "GET").endpoint()

    assert status["prepare_only"] is True
    assert policy["prepare_only"] is True
    assert record["status"] == "pending"
    assert decided["status"] == "approved"
    assert decided["safe_to_execute"] is False
    assert gate["safe_to_execute"] is False
    assert audit["append_only"] is True
    for path in DANGEROUS_ROUTES:
        assert _route(app, path, "GET") is None
        assert _route(app, path, "POST") is None


def test_command_center_and_operator_console_expose_prepare_only_markers():
    command = build_command_center_view_model(view_id="post-s-2", generated_at="2026-06-10T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="post-s-2", generated_at="2026-06-10T00:00:00+00:00")
    for marker in (
        "post_s_approval_hardening",
        "strong_approval_policy",
        "approval_audit",
        "permission_gates",
        "context_fingerprint",
        "side_effect_gate_readiness",
    ):
        assert command.metadata[marker] == "prepare_only"
        assert operator.metadata[marker] == "prepare_only"


def test_docs_define_post_s_macro_without_phase_t_and_without_execution():
    content = DOC.read_text(encoding="utf-8")
    assert "no es Phase T" in content
    assert "Post-S Macro 3" in content
    assert "safe_to_execute=false" in content
