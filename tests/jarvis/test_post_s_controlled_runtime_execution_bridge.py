from __future__ import annotations

import socket
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import RuntimePreviewRequest, create_app
from jarvis.approval_hardening import ApprovalHardeningService, ApprovalKind
from jarvis.command_center import build_command_center_view_model
from jarvis.controlled_runtime_bridge import (
    ControlledRuntimeBridge,
    ControlledRuntimeGateResult,
    RollbackPlan,
    SandboxRequirements,
)
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import NEXT_MACRO_PR, build_operational_system_status


DOC = Path("docs/jarvis-post-s-controlled-runtime-execution-bridge.md")
DANGEROUS_ROUTES = (
    "/runtime/execute",
    "/runtime/run",
    "/runtime/deploy",
    "/runtime/install",
    "/runtime/send",
    "/runtime/pay",
    "/runtime/read-secret",
    "/runtime/start-worker",
    "/runtime/start-camera",
    "/runtime/start-microphone",
    "/runtime/capture-screen",
    "/runtime/shell",
    "/runtime/subprocess",
)


def _request(bridge: ControlledRuntimeBridge, **overrides):
    values = {
        "action_type": "prepare_report",
        "target": "local-preview",
        "scope": ["workspace/report"],
        "tool_name": "report_preview",
    }
    values.update(overrides)
    return bridge.prepare_request(**values)


def _approved(request, *, strong=False, expires_at=None):
    service = ApprovalHardeningService()
    record = service.request(
        action_type=request.action_type,
        context=request.context(),
        approval_kind=ApprovalKind.STRONG if strong else ApprovalKind.NORMAL,
        expires_at=expires_at,
    )
    phrase = record.user_confirmation_phrase if strong else None
    service.decide(record.approval_id, "approved", confirmation_phrase=phrase)
    return service, record


def _ready_parts(bridge, request):
    return (
        bridge.preview_dry_run(request),
        bridge.preview_sandbox(request, sandbox_available=True, timeout_present=True),
        bridge.preview_rollback(request),
    )


def _route(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route
    return None


def test_runtime_status_is_prepare_only_post_s_without_phase_t():
    status = ControlledRuntimeBridge().status()
    assert status["controlled_runtime_bridge_available"] is True
    assert status["runtime_execution_enabled"] is False
    assert status["side_effects_enabled"] is False
    assert status["safe_to_execute"] is False
    assert status["allowed_for_future_execution"] is False
    assert NEXT_MACRO_PR == "Post-S Macro 4 - Real Connectors & Tool Execution Layer"


def test_defaults_cannot_enable_execution_or_side_effects():
    result = ControlledRuntimeGateResult(safe_to_execute=True, allowed_for_future_execution=True)
    assert result.execution_enabled is False
    assert result.side_effects_enabled is False
    assert result.readiness_only is True
    assert SandboxRequirements().ready is False


def test_plan_and_dry_run_are_redacted_and_never_execute():
    bridge = ControlledRuntimeBridge()
    request = _request(bridge, command="echo token=abc", payload_summary={"password": "secret-value"})
    dry_run = bridge.preview_dry_run(request)
    serialized = str({"request": request.to_dict(), "dry_run": dry_run.to_dict()}).lower()
    assert dry_run.dry_run_performed is True
    assert dry_run.would_execute is False
    assert "secret-value" not in serialized
    assert "token=abc" not in serialized


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"action_type": ""}, "action_type is empty"),
        ({"target": ""}, "target is empty"),
        ({"scope": ["*"]}, "scope is empty or open"),
        ({"scope": []}, "scope is empty or open"),
        ({"tool_name": None, "command": ""}, "command or tool_name is required"),
        ({"tool_name": None, "command": "execute"}, "command is ambiguous"),
    ],
)
def test_invalid_or_ambiguous_requests_block(overrides, reason):
    bridge = ControlledRuntimeBridge()
    assert reason in bridge.preview_dry_run(_request(bridge, **overrides)).blocked_reasons


def test_sandbox_network_filesystem_and_secrets_are_default_deny():
    bridge = ControlledRuntimeBridge()
    request = _request(bridge, filesystem_write=True, network_access=True, external_call=True, secrets=True)
    sandbox = bridge.preview_sandbox(request)
    assert sandbox.sandbox_required is True
    assert sandbox.ready is False
    assert "sandbox unavailable" in sandbox.missing_requirements
    assert "filesystem scope missing" in sandbox.missing_requirements
    assert "network permission missing" in sandbox.missing_requirements
    assert "secrets are blocked" in sandbox.missing_requirements


def test_external_call_requires_explicit_network_permission():
    bridge = ControlledRuntimeBridge()
    request = _request(bridge, external_call=True)
    assert "network permission missing" in bridge.preview_sandbox(request).missing_requirements


def test_side_effects_require_rollback_and_present_plan_only_advances_readiness():
    bridge = ControlledRuntimeBridge()
    request = _request(bridge, side_effects=True)
    missing = bridge.preview_rollback(request)
    present = bridge.preview_rollback(request, rollback_available=True, rollback_steps=["restore prior state"])
    assert missing.rollback_required is True
    assert missing.ready is False
    assert present.ready is True
    assert present.prepare_only is True


@pytest.mark.parametrize("status", ["pending", "rejected", "revoked", "expired"])
def test_non_valid_approval_states_block(status):
    bridge = ControlledRuntimeBridge()
    request = _request(bridge)
    service = ApprovalHardeningService()
    expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat() if status == "expired" else None
    record = service.request(action_type=request.action_type, context=request.context(), expires_at=expires_at)
    if status == "rejected":
        service.decide(record.approval_id, "rejected")
    elif status == "revoked":
        service.decide(record.approval_id, "approved")
        service.revoke(record.approval_id)
    elif status == "expired":
        service.refresh_expiration(record)
    dry, sandbox, rollback = _ready_parts(bridge, request)
    gate = bridge.preview_gate(
        request, dry_run=dry, sandbox=sandbox, rollback=rollback, approval=record, policy_allowed=True
    )
    assert gate.safe_to_execute is False
    assert gate.approval_status == status


def test_production_requires_strong_approval_and_matching_context():
    bridge = ControlledRuntimeBridge()
    request = _request(bridge, production=True, side_effects=True)
    rollback = bridge.preview_rollback(request, rollback_available=True, rollback_steps=["restore release"])
    dry = bridge.preview_dry_run(request)
    sandbox = bridge.preview_sandbox(request, sandbox_available=True, timeout_present=True)
    _, normal = _approved(request)
    normal_gate = bridge.preview_gate(
        request, dry_run=dry, sandbox=sandbox, rollback=rollback, approval=normal, policy_allowed=True
    )
    _, strong = _approved(request, strong=True)
    mismatch = _request(bridge, production=True, side_effects=True, target="changed")
    mismatch_gate = bridge.preview_gate(
        mismatch,
        dry_run=bridge.preview_dry_run(mismatch),
        sandbox=bridge.preview_sandbox(mismatch, sandbox_available=True, timeout_present=True),
        rollback=bridge.preview_rollback(mismatch, rollback_available=True, rollback_steps=["restore release"]),
        approval=strong,
        policy_allowed=True,
    )
    assert normal_gate.requires_strong_approval is True
    assert normal_gate.safe_to_execute is False
    assert mismatch_gate.context_matches is False
    assert mismatch_gate.safe_to_execute is False


def test_scope_change_changes_fingerprint_and_blocks_existing_approval():
    bridge = ControlledRuntimeBridge()
    request = _request(bridge)
    _, approval = _approved(request)
    changed = _request(bridge, scope=["workspace/other"])
    dry, sandbox, rollback = _ready_parts(bridge, changed)
    gate = bridge.preview_gate(
        changed, dry_run=dry, sandbox=sandbox, rollback=rollback, approval=approval, policy_allowed=True
    )
    assert changed.context_fingerprint != request.context_fingerprint
    assert gate.context_matches is False
    assert gate.safe_to_execute is False


def test_permission_allowed_and_safe_to_execute_true_remain_readiness_only():
    bridge = ControlledRuntimeBridge()
    request = _request(bridge)
    _, approval = _approved(request)
    dry, sandbox, rollback = _ready_parts(bridge, request)
    gate = bridge.preview_gate(
        request, dry_run=dry, sandbox=sandbox, rollback=rollback, approval=approval, policy_allowed=True
    )
    assert gate.permission_gate_allowed is True
    assert gate.safe_to_execute is True
    assert gate.allowed_for_future_execution is True
    assert gate.execution_enabled is False
    assert gate.side_effects_enabled is False


def test_policy_denied_and_missing_sandbox_block_even_with_approval():
    bridge = ControlledRuntimeBridge()
    request = _request(bridge)
    _, approval = _approved(request)
    gate = bridge.preview_gate(request, approval=approval)
    assert gate.safe_to_execute is False
    assert gate.blocked_reasons


def test_gate_recomputes_sandbox_and_rollback_requirements_from_request():
    bridge = ControlledRuntimeBridge()
    request = _request(bridge, external_call=True, side_effects=True)
    _, approval = _approved(request, strong=True)
    gate = bridge.preview_gate(
        request,
        dry_run=bridge.preview_dry_run(request),
        sandbox=SandboxRequirements(sandbox_available=True, timeout_present=True, missing_requirements=[]),
        rollback=RollbackPlan(rollback_required=False),
        approval=approval,
        policy_allowed=True,
    )
    assert "network permission missing" in gate.blocked_reasons
    assert "required rollback plan missing" in gate.blocked_reasons
    assert gate.safe_to_execute is False


def test_runtime_api_routes_are_preview_only_and_do_not_mutate(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("network called"))
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes factory called"))
    payload = RuntimePreviewRequest(
        action_type="prepare_report",
        target="local-preview",
        scope=["workspace/report"],
        tool_name="report_preview",
    )
    missions_before = app.state.mission_control.list_missions()
    tasks_before = app.state.task_store.list()
    assert _route(app, "/runtime/status", "GET").endpoint()["prepare_only"] is True
    assert _route(app, "/runtime/policy", "GET").endpoint()["prepare_only"] is True
    for path in ("/runtime/preview-plan", "/runtime/preview-dry-run", "/runtime/preview-gate", "/runtime/preview-rollback"):
        result = _route(app, path, "POST").endpoint(payload)
        assert result["prepare_only"] is True
    assert app.state.mission_control.list_missions() == missions_before == []
    assert app.state.task_store.list() == tasks_before == []
    for path in DANGEROUS_ROUTES:
        assert _route(app, path, "GET") is None
        assert _route(app, path, "POST") is None


def test_operational_command_center_and_operator_console_markers_exist():
    status = build_operational_system_status().to_dict()
    command = build_command_center_view_model(view_id="post-s-3", generated_at="2026-06-10T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="post-s-3", generated_at="2026-06-10T00:00:00+00:00")
    assert status["controlled_runtime_bridge_available"] is True
    assert status["runtime_execution_enabled"] is False
    for marker in (
        "post_s_controlled_runtime_bridge",
        "dry_run_bridge",
        "sandbox_requirements",
        "rollback_plan",
        "runtime_permission_gate",
        "runtime_approval_gate",
        "safe_to_execute_readiness_only",
        "runtime_execution_disabled",
    ):
        assert command.metadata[marker] == "prepare_only"
        assert operator.metadata[marker] == "prepare_only"


def test_docs_define_macro_3_without_phase_t_or_execution():
    content = DOC.read_text(encoding="utf-8")
    assert "no es Phase T" in content
    assert "safe_to_execute" in content
    assert "no ejecuta" in content.lower()
    assert "Post-S Macro 4" in content
