from __future__ import annotations

import builtins
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import Mark2ToolExecutionPreviewRequest, create_app
from jarvis.command_center import build_command_center_view_model
from jarvis.mark_2_browser_adapter import BrowserToolAdapter
from jarvis.mark_2_external_api_adapter import ExternalAPIToolAdapter
from jarvis.mark_2_filesystem_adapter import FilesystemToolAdapter
from jarvis.mark_2_github_adapter import GitHubToolAdapter
from jarvis.mark_2_tool_execution import Mark2ToolExecutionLayer
from jarvis.mark_2_tool_execution_policy import Mark2ToolExecutionPolicyEngine, Mark2ToolExecutionStatus, mark_2_tool_execution_markers
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import build_operational_system_status


DOC = Path("docs/jarvis-mark-2-real-tool-execution-browser-github-filesystem-apis.md")
SAFE_ROUTES = (
    ("GET", "/mark-2/tools/status"), ("GET", "/mark-2/tools/policy"),
    ("POST", "/mark-2/tools/preview-request"), ("POST", "/mark-2/tools/preview-candidate"),
    ("POST", "/mark-2/tools/preview-filesystem"), ("POST", "/mark-2/tools/preview-github"),
    ("POST", "/mark-2/tools/preview-browser"), ("POST", "/mark-2/tools/preview-api"),
    ("POST", "/mark-2/tools/preview-execution"), ("GET", "/mark-2/tools/audit-preview"),
)
DANGEROUS_ROUTES = (
    "/mark-2/tools/execute-free", "/mark-2/tools/execute-any", "/mark-2/tools/auto-approve",
    "/mark-2/tools/approve-all", "/mark-2/tools/read-env", "/mark-2/tools/use-token",
    "/mark-2/tools/github-live", "/mark-2/tools/browser-live", "/mark-2/tools/api-live",
    "/mark-2/tools/deploy", "/mark-2/tools/pay", "/mark-2/tools/charge",
    "/mark-2/tools/write-anywhere", "/mark-2/tools/delete-anywhere",
)


def _route(app, path, method):
    return next((route for route in app.routes if route.path == path and method in route.methods), None)


def test_status_policy_and_global_defaults_are_safe():
    status = Mark2ToolExecutionStatus().to_dict()
    policy = Mark2ToolExecutionPolicyEngine().policy()
    assert status["current_mark"] == "Mark 2" and status["mark_2_macro"] == "Mark 2 Macro 2"
    for name in ("real_tool_execution_layer_available", "filesystem_adapter_available", "github_adapter_available", "browser_adapter_available", "external_api_adapter_available", "sandbox_boundaries_available", "allowlist_policy_available", "denylist_policy_available", "audit_available", "voice_approval_supported", "restrictions_are_approval_gates"):
        assert status[name] is True
    assert status["wake_phrase_is_permission"] is False
    for name in ("real_execution_enabled", "external_network_enabled", "access_material_enabled", "production_operations_enabled", "money_movement_enabled", "filesystem_external_write_enabled", "browser_real_launch_enabled", "github_real_calls_enabled", "external_api_real_calls_enabled"):
        assert status[name] is False
    assert policy["scheduler_due_is_permission"] is False
    assert policy["memory_active_is_permission"] is False


def test_policy_classifies_gates_and_permanent_denial():
    engine = Mark2ToolExecutionPolicyEngine()
    env = engine.evaluate(action_type="read_file", target_type="filesystem", target=".env", allowlist_match=True)
    outside = engine.evaluate(action_type="write_file", target_type="filesystem", target="/tmp/x", allowlist_match=False)
    network = engine.evaluate(action_type="post", target_type="external_api", target="https://example.test")
    credentials = engine.evaluate(action_type="login", target_type="browser", target="https://example.test", requires_credentials=True)
    production = engine.evaluate(action_type="deploy", target_type="deploy", target="production", production_impact=True)
    money = engine.evaluate(action_type="charge", target_type="payment", target="customer", cost_impact=True)
    unsupported = engine.evaluate(action_type="fly", target_type="unknown", target="moon")
    assert "secret or .env access is blocked" in env.blocked_reasons
    assert "filesystem target is outside allowlist" in outside.blocked_reasons
    assert network.network_required is True and network.approval_required is True
    assert credentials.strong_approval_required is True
    assert production.strong_approval_required is True and production.double_confirmation_required is True
    assert money.double_confirmation_required is True and money.triple_confirmation_required is True
    assert unsupported.permanent_denial is True


def test_request_risk_cannot_be_downgraded_and_non_permissions_do_not_approve():
    layer = Mark2ToolExecutionLayer()
    request = layer.prepare_request(
        action_type="charge",
        target_type="payment",
        target="real purchase",
        risk_level_declared="low",
        approval_context={"valid_approval_present": True, "scheduler_due": True, "memory_active": True, "wake_phrase": True},
        rollback_or_stop_plan="cancel purchase",
    )
    candidate = layer.prepare_candidate(request)
    assert request.risk_level_classified.value == "critical" and request.risk_downgrade_attempted is True
    assert candidate.valid_approval_present is False and candidate.execution_allowed is False


def test_valid_voice_approval_can_satisfy_approval_but_not_disabled_runtime_gates():
    layer = Mark2ToolExecutionLayer()
    valid = layer.prepare_request(
        action_type="create_pr",
        target_type="github",
        target="ceodaradigu/hermes-agent",
        requires_external_write=True,
        rollback_or_stop_plan="close PR",
        voice_approval_context={"valid_voice_approval_present": True, "readback_completed": True, "strong_approval_satisfied": True},
    )
    expired = layer.prepare_request(
        action_type="create_pr",
        target_type="github",
        target="ceodaradigu/hermes-agent",
        voice_approval_context={"valid_voice_approval_present": True, "expired": True},
    )
    candidate = layer.prepare_candidate(valid)
    assert candidate.valid_voice_approval_present is True
    assert candidate.execution_allowed is False and "external network gate disabled" in candidate.blocked_reasons
    assert layer.prepare_candidate(expired).valid_voice_approval_present is False
    no_readback = layer.prepare_request(
        action_type="write_file",
        target_type="filesystem",
        target="jarvis/x.py",
        voice_approval_context={"valid_voice_approval_present": True},
    )
    assert layer.prepare_candidate(no_readback).valid_voice_approval_present is False


def test_candidate_blocks_missing_approval_rollback_denylist_kill_switch_and_stop_phrase():
    layer = Mark2ToolExecutionLayer()
    request = layer.prepare_request(action_type="write_file", target_type="filesystem", target=".env", requires_filesystem_write=True)
    preview = layer.filesystem.preview_write_file(".env", "secret")
    candidate = layer.prepare_candidate(request, adapter_preview=preview, kill_switch_active=True, stop_phrase_detected=True)
    for reason in ("valid explicit approval required", "required rollback or stop plan is missing", "kill switch active", "candidate cancelled by stop phrase"):
        assert reason in candidate.blocked_reasons
    assert candidate.denylist_match is True and candidate.would_execute is False


def test_delete_preview_forwards_rollback_plan_and_keeps_strong_approval_requirement():
    layer = Mark2ToolExecutionLayer()
    without_rollback = layer.prepare_request(
        action_type="delete_file",
        target_type="filesystem",
        target="jarvis/x.py",
        requires_filesystem_write=True,
    )
    with_rollback = layer.prepare_request(
        action_type="delete_file",
        target_type="filesystem",
        target="jarvis/x.py",
        requires_filesystem_write=True,
        rollback_or_stop_plan="restore jarvis/x.py",
    )
    blocked = layer.prepare_candidate(without_rollback)
    planned = layer.prepare_candidate(with_rollback)
    assert "delete requires rollback plan" in blocked.blocked_reasons
    assert "delete requires rollback plan" not in planned.blocked_reasons
    assert planned.rollback_or_stop_plan_required is True
    assert planned.strong_approval_required is True


def test_candidate_never_lowers_adapter_declared_safety_requirements():
    layer = Mark2ToolExecutionLayer()
    merge_request = layer.prepare_request(
        action_type="merge_pr",
        target_type="github",
        target="owner/repo",
        rollback_or_stop_plan="revert merge",
    )
    merge_preview = layer.preview_adapter(merge_request, branch="main", protected_branch=True)
    merge = layer.prepare_candidate(merge_request, adapter_preview=merge_preview)
    payment_request = layer.prepare_request(
        action_type="submit_form",
        target_type="browser",
        target="https://example.test/payment",
        rollback_or_stop_plan="close browser",
    )
    payment = layer.prepare_candidate(payment_request)
    api_request = layer.prepare_request(
        action_type="post",
        target_type="external_api",
        target="https://example.test/data",
        rollback_or_stop_plan="cancel request",
    )
    api_preview = layer.preview_adapter(
        api_request,
        method="POST",
        credentials_required=True,
        payload={"token": "redact-me"},
    )
    api = layer.prepare_candidate(api_request, adapter_preview=api_preview)
    assert merge.approval_required is True
    assert merge.strong_approval_required is True
    assert merge.double_confirmation_required is True
    assert merge.credentials_required is True
    assert merge.network_required is True
    assert merge.would_modify_remote is True
    assert payment.strong_approval_required is True
    assert payment.double_confirmation_required is True
    assert payment.triple_confirmation_required is True
    assert payment.cost_impact is True
    assert api.credentials_required is True
    assert api.network_required is True
    assert api.rollback_or_stop_plan_required is True
    assert api.sensitive_payload_detected is True


def test_filesystem_adapter_normalizes_and_never_mutates(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    adapter = FilesystemToolAdapter(repo, allowed_paths=(".",))
    inside = adapter.preview_write_file("src/app.py", "print('x')")
    traversal = adapter.preview_write_file("../outside.txt", "x")
    env = adapter.preview_read_file(".env")
    delete = adapter.candidate_delete_file("src/app.py")
    assert inside["path_normalized"] == str((repo / "src/app.py").resolve())
    assert inside["within_repo"] is True and inside["within_allowlist"] is True
    assert inside["approval_required"] is True and inside["would_write"] is False
    assert traversal["within_repo"] is False and traversal["blocked_reasons"]
    assert env["denylist_match"] is True and env["would_read"] is False
    assert delete["strong_approval_required"] is True and "delete requires rollback plan" in delete["blocked_reasons"]
    assert not (repo / "src/app.py").exists()


def test_github_browser_and_api_adapters_never_call_external_services():
    github = GitHubToolAdapter().preview_create_pr(repo="owner/repo", branch="feature")
    merge = GitHubToolAdapter().preview_merge_pr(repo="owner/repo", branch="main", protected_branch=True)
    browser = BrowserToolAdapter().preview_open_url("https://example.test")
    pii = BrowserToolAdapter().preview_submit_form("https://example.test/login", credentials_required=True, user_data_risk=True)
    payment = BrowserToolAdapter().preview_submit_form("https://example.test/payment")
    get = ExternalAPIToolAdapter().preview_get_request("https://example.test/data")
    post = ExternalAPIToolAdapter().preview_post_request("https://example.test/webhook", payload={"token": "abc"})
    assert github["would_call_github"] is False and github["credentials_required"] is True and github["network_required"] is True
    assert merge["strong_approval_required"] is True and merge["double_confirmation_required"] is True
    assert browser["would_launch_browser"] is False and browser["would_submit_data"] is False
    assert pii["strong_approval_required"] is True
    assert payment["double_confirmation_required"] is True and payment["triple_confirmation_required"] is True
    assert get["would_call_external_api"] is False
    assert post["approval_required"] is True and post["sensitive_payload_detected"] is True
    assert post["payload_summary"]["token"] == "[redacted]"


def test_results_and_audit_never_claim_external_success_and_redact():
    layer = Mark2ToolExecutionLayer()
    request = layer.prepare_request(action_type="post", target_type="external_api", target="https://example.test/token", requires_external_write=True)
    candidate = layer.prepare_candidate(request)
    result = layer.preview_result(request, candidate).to_dict()
    readiness = layer.preview_readiness(candidate).to_dict()
    audit = layer.audit_preview(result["audit_event_id"])["events"][0]
    assert result["executed"] is False and result["success"] is False and result["mode"] != "executed"
    assert result["external_call_made"] is False and result["remote_changed"] is False
    assert readiness["real_execution_enabled"] is False and readiness["execution_ready"] is False
    assert readiness["ready_after_all_gates"] is False
    assert audit["event_id"] == result["audit_event_id"]
    assert audit["secrets_redacted"] is True and audit["audit_safe"] is True
    assert "token" not in audit["target_redacted"]
    for name in ("approval_summary", "voice_approval_summary", "sandbox_scope", "allowlist_result", "denylist_result"):
        assert name in audit


def test_readiness_separates_policy_ready_candidate_from_disabled_real_execution():
    layer = Mark2ToolExecutionLayer()
    request = layer.prepare_request(
        action_type="read_file",
        target_type="filesystem",
        target="jarvis/command_center.py",
        approval_context={"valid_approval_present": True},
    )
    candidate = layer.prepare_candidate(request)
    readiness = layer.preview_readiness(candidate).to_dict()
    assert candidate.execution_allowed is True
    assert readiness["candidate_ready_after_policy_gates"] is True
    assert readiness["real_execution_enabled"] is False
    assert readiness["execution_ready"] is False
    assert readiness["ready_after_all_gates"] is False


def test_control_plane_endpoints_are_present_safe_and_dangerous_routes_absent(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("network called"))
    monkeypatch.setattr(Path, "write_text", lambda *a, **k: pytest.fail("filesystem write"))
    original_open = builtins.open
    monkeypatch.setattr(builtins, "open", lambda file, *a, **k: pytest.fail(".env read") if str(file).endswith(".env") else original_open(file, *a, **k))
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    payload = Mark2ToolExecutionPreviewRequest(action_type="write_file", target="jarvis/x.py", requires_filesystem_write=True)
    for method, path in SAFE_ROUTES:
        route = _route(app, path, method)
        assert route is not None
        output = route.endpoint() if method == "GET" else route.endpoint(payload)
        assert isinstance(output, dict)
        assert output.get("executed", False) is False
    for path in DANGEROUS_ROUTES:
        assert _route(app, path, "GET") is None and _route(app, path, "POST") is None


def test_operational_command_center_and_operator_console_expose_macro_2_markers():
    markers = mark_2_tool_execution_markers()
    operational = build_operational_system_status().to_dict()
    command = build_command_center_view_model(view_id="mark-2-macro-2", generated_at="2026-06-11T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="mark-2-macro-2", generated_at="2026-06-11T00:00:00+00:00")
    for marker, expected in markers.items():
        assert operational[marker] == expected
        assert command.metadata[marker] == expected
        assert operator.metadata[marker] == expected


def test_documentation_exists_and_explains_boundaries():
    content = DOC.read_text(encoding="utf-8")
    for text in ("Mark 2 Macro 2", "preview", "candidate", "gated execution", "wake phrase", "Voice Approval Channel", "Mark 2 Macro 3"):
        assert text in content
