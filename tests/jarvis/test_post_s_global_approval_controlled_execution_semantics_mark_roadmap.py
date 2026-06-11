from __future__ import annotations

import builtins
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (
    ApprovalExecutionDecisionPreviewRequest,
    CriticalActionWarningPreviewRequest,
    create_app,
)
from jarvis.approval_execution_semantics import (
    ARCHITECTURAL_RULE,
    GlobalApprovalExecutionSemantics,
    MarkRoadmap,
    global_execution_markers,
)
from jarvis.command_center import build_command_center_view_model
from jarvis.controlled_runtime_bridge import ControlledRuntimeBridge
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import (
    NEXT_RECOMMENDED_MACRO_PR,
    build_command_center_system_map,
    build_operational_console_summary,
    build_operational_system_status,
)
from jarvis.tool_invocation_layer import ToolInvocationLayer


DOC = Path("docs/jarvis-post-s-global-approval-controlled-execution-semantics-mark-roadmap.md")
MARKER_NAMES = tuple(global_execution_markers())


def _route(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route
    return None


def _ready_decision(semantics, **overrides):
    values = {
        "action_name": "prepare local report",
        "action_category": "normal",
        "risk_level": "medium",
        "valid_approval_present": True,
        "strong_approval_present": False,
        "double_confirmation_present": False,
        "context_fingerprint_matches": True,
        "permission_gates_passed": True,
        "audit_present": True,
        "rollback_or_stop_plan_required": False,
        "rollback_or_stop_plan_present": False,
        "execution_capable_when_approved": True,
    }
    values.update(overrides)
    return semantics.preview_decision(**values)


def test_global_status_and_policy_define_approval_gated_not_permanent_prepare_only():
    semantics = GlobalApprovalExecutionSemantics()
    status = semantics.status()
    policy = semantics.policy()
    assert status["architectural_rule"] == ARCHITECTURAL_RULE
    assert status["restrictions_are_approval_gates"] is True
    assert status["default_denied_without_approval"] is True
    assert status["executable_after_valid_approval"] is True
    assert status["jarvis_is_not_prepare_only_forever"] is True
    assert status["real_execution_enabled"] is False
    assert policy["approval_cannot_override_legality_safety_authorization_or_capability"] is True
    assert policy["approval_hardening_is_authority_for_valid_approval_strong_approval_expiration_revocation_context_and_audit"] is True
    assert policy["preview_inputs_are_assertions_not_authoritative_approval_records"] is True
    assert policy["audit_required"] is True
    assert policy["permission_gates_required"] is True


def test_without_valid_approval_execution_is_denied():
    decision = GlobalApprovalExecutionSemantics().preview_decision(action_name="normal action")
    assert decision.blocked_without_approval is True
    assert decision.execution_allowed is False
    assert "valid explicit approval required" in decision.blocked_reasons


def test_preview_gate_assertions_are_conservative_by_default():
    decision = GlobalApprovalExecutionSemantics().preview_decision(
        action_name="normal action",
        valid_approval_present=True,
    )
    assert decision.execution_allowed is False
    assert "context fingerprint mismatch" in decision.blocked_reasons
    assert "permission gates failed" in decision.blocked_reasons
    assert "execution audit is missing" in decision.blocked_reasons
    assert "real execution capability is unavailable" in decision.blocked_reasons


def test_normal_action_can_become_eligible_after_valid_approval_and_all_gates():
    decision = _ready_decision(GlobalApprovalExecutionSemantics())
    assert decision.execution_allowed is True
    assert decision.permanent_denial is False
    assert decision.preview_only is True
    assert decision.would_execute is False
    assert decision.execution_enabled is False


def test_sensitive_action_requires_strong_approval():
    semantics = GlobalApprovalExecutionSemantics()
    blocked = _ready_decision(semantics, action_category="sensitive", risk_level="high")
    allowed = _ready_decision(
        semantics,
        action_category="sensitive",
        risk_level="high",
        strong_approval_present=True,
    )
    assert blocked.strong_approval_required is True
    assert blocked.execution_allowed is False
    assert "valid strong approval required" in blocked.blocked_reasons
    assert allowed.execution_allowed is True


def test_critical_action_requires_strong_approval_and_double_confirmation():
    semantics = GlobalApprovalExecutionSemantics()
    blocked = _ready_decision(
        semantics,
        action_name="deploy production",
        action_category="critical",
        risk_level="critical",
        strong_approval_present=True,
        rollback_or_stop_plan_required=True,
        rollback_or_stop_plan_present=True,
    )
    allowed = _ready_decision(
        semantics,
        action_name="deploy production",
        action_category="critical",
        risk_level="critical",
        strong_approval_present=True,
        double_confirmation_present=True,
        rollback_or_stop_plan_required=True,
        rollback_or_stop_plan_present=True,
    )
    assert blocked.double_confirmation_required is True
    assert blocked.execution_allowed is False
    assert blocked.required_confirmation_phrase
    assert allowed.execution_allowed is True


@pytest.mark.parametrize("flag", ["illegal", "unsafe", "unauthorized", "impossible", "unsupported"])
def test_permanent_denial_cannot_be_overridden_by_approval(flag):
    decision = _ready_decision(
        GlobalApprovalExecutionSemantics(),
        action_category="critical",
        risk_level="critical",
        strong_approval_present=True,
        double_confirmation_present=True,
        **{flag: True},
    )
    assert decision.permanent_denial is True
    assert decision.denial_reason
    assert decision.execution_allowed is False


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"context_fingerprint_matches": False}, "context fingerprint mismatch"),
        ({"permission_gates_passed": False}, "permission gates failed"),
        ({"audit_present": False}, "execution audit is missing"),
        (
            {"rollback_or_stop_plan_required": True, "rollback_or_stop_plan_present": False},
            "required rollback or stop plan is missing",
        ),
        ({"execution_capable_when_approved": False}, "real execution capability is unavailable"),
    ],
)
def test_required_execution_gates_block_when_missing(overrides, reason):
    decision = _ready_decision(GlobalApprovalExecutionSemantics(), **overrides)
    assert decision.execution_allowed is False
    assert reason in decision.blocked_reasons


def test_critical_warning_includes_consequences_and_confirmation_phrase():
    warning = GlobalApprovalExecutionSemantics().preview_critical_warning(
        action_name="deploy production",
        affected_system="production",
        estimated_cost="unknown",
        rollback_available=True,
    )
    assert warning.possible_consequences
    assert warning.confirmation_phrase.startswith("CONFIRM CRITICAL ACTION:")
    assert warning.required_double_confirmation is True
    assert warning.preview_only is True
    assert warning.would_execute is False


def test_wake_scheduler_memory_runtime_and_tool_readiness_are_not_permission_or_execution():
    policy = GlobalApprovalExecutionSemantics().policy()
    runtime = ControlledRuntimeBridge().status()
    tools = ToolInvocationLayer().status()
    operational = build_operational_system_status().to_dict()
    assert policy["wake_phrase_is_not_permission"] is True
    assert policy["scheduler_due_is_not_permission"] is True
    assert policy["memory_active_is_not_permission"] is True
    assert operational["wake_phrase_is_not_permission"] is True
    assert operational["scheduler_due_is_not_permission"] is True
    assert operational["memory_active_is_not_permission"] is True
    assert runtime["safe_to_execute_potentially_true_after_valid_approval_and_gates"] is True
    assert runtime["runtime_execution_enabled"] is False
    assert tools["safe_to_invoke_potentially_true_after_valid_approval_and_gates"] is True
    assert tools["tool_execution_enabled"] is False


def test_control_plane_endpoints_exist_and_never_execute_or_call_external(monkeypatch):
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
    status_route = _route(app, "/approval-execution/status", "GET")
    policy_route = _route(app, "/approval-execution/policy", "GET")
    decision_route = _route(app, "/approval-execution/preview-decision", "POST")
    warning_route = _route(app, "/approval-execution/preview-critical-warning", "POST")
    roadmap_route = _route(app, "/roadmap/marks", "GET")
    for route in (status_route, policy_route, decision_route, warning_route, roadmap_route):
        assert route is not None
        assert route.status_code in (None, 200)
    assert status_route.endpoint()["real_execution_enabled"] is False
    assert policy_route.endpoint()["restrictions_are_approval_gates"] is True
    decision = decision_route.endpoint(
        ApprovalExecutionDecisionPreviewRequest(
            action_name="deploy production",
            action_category="critical",
            risk_level="critical",
            valid_approval_present=True,
            strong_approval_present=True,
            double_confirmation_present=True,
        )
    )
    warning = warning_route.endpoint(
        CriticalActionWarningPreviewRequest(action_name="Stripe live", affected_system="billing")
    )
    roadmap = roadmap_route.endpoint()
    assert decision["execution_enabled"] is False and decision["would_execute"] is False
    assert warning["would_execute"] is False
    assert roadmap["current_mark"] == "Mark 1"


def test_mark_roadmap_uses_marks_and_large_macro_prs():
    roadmap = MarkRoadmap().to_dict()
    serialized = str(roadmap)
    assert roadmap["current_mark"] == "Mark 1"
    assert all(name in serialized for name in ("Mark 1", "Mark 2", "Mark 3"))
    assert all(name not in serialized for name in ("V1", "V2", "V3"))
    assert all(f"PR #{number}" in serialized for number in range(122, 126))
    assert len(roadmap["mark_2_macro_prs"]) == 5
    assert len(roadmap["mark_3_macro_prs"]) == 5
    assert roadmap["no_micro_pr_policy"] is True
    assert NEXT_RECOMMENDED_MACRO_PR == "PR #123 - Monetization Engine Real"


def test_operational_command_center_and_operator_console_expose_global_markers():
    operational = build_operational_system_status().to_dict()
    summary = build_operational_console_summary()
    system_map = build_command_center_system_map()
    command = build_command_center_view_model(view_id="macro-7", generated_at="2026-06-11T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="macro-7", generated_at="2026-06-11T00:00:00+00:00")
    for marker in MARKER_NAMES:
        assert system_map[marker] is True
        assert command.metadata[marker] is True
        assert operator.metadata[marker] is True
    assert operational["restrictions_are_approval_gates"] is True
    assert summary["next_recommended_macro_pr"] == "PR #123 - Monetization Engine Real"


def test_docs_define_new_semantics_marks_and_do_not_create_phase_t():
    content = DOC.read_text(encoding="utf-8")
    assert ARCHITECTURAL_RULE in content
    assert "JARVIS no es prepare-only para siempre" in content
    assert "permanent_denial=true" in content
    assert "doble confirmación" in content
    assert all(name in content for name in ("Mark 1", "Mark 2", "Mark 3"))
    assert "120 PRs" in content
    assert "### Phase T" not in content
