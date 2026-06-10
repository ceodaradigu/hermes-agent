from __future__ import annotations

import builtins
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (
    ConnectorPreviewRequest,
    ToolInvocationPreviewRequest,
    ToolRegistrationPreviewRequest,
    create_app,
)
from jarvis.approval_hardening import ApprovalHardeningService, ApprovalKind
from jarvis.command_center import build_command_center_view_model
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import NEXT_MACRO_PR, build_operational_system_status
from jarvis.tool_connectors import ConnectorDefinition, ConnectorType, default_connector_definitions
from jarvis.tool_invocation_layer import ToolInvocationLayer, ToolPermissionCheckResult
from jarvis.tool_registry import ToolDefinition, ToolRegistry


DOC = Path("docs/jarvis-post-s-real-connectors-tool-execution-layer.md")
DANGEROUS_ROUTES = (
    "/tools/execute",
    "/tools/run",
    "/tools/call",
    "/tools/deploy",
    "/tools/install",
    "/tools/send",
    "/tools/pay",
    "/tools/read-secret",
    "/tools/read-env",
    "/tools/github/create-pr",
    "/tools/github/merge",
    "/tools/github/push",
    "/tools/browser/open",
    "/tools/api/request",
    "/tools/files/write",
    "/tools/shell",
    "/tools/subprocess",
)


def _route(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route
    return None


def _enabled_layer(*, connector_type=ConnectorType.MOCK_SAFE, tool_overrides=None, connector_overrides=None):
    registry = ToolRegistry(include_defaults=False)
    connector_values = {
        "connector_id": "connector",
        "connector_type": connector_type,
        "enabled": True,
        "approval_required": True,
    }
    connector_values.update(connector_overrides or {})
    tool_values = {
        "tool_id": "tool",
        "name": "Controlled tool preview",
        "connector_type": connector_type,
        "enabled": True,
    }
    tool_values.update(tool_overrides or {})
    registry.register_connector(ConnectorDefinition(**connector_values))
    registry.register_tool(ToolDefinition(**tool_values))
    return ToolInvocationLayer(registry=registry)


def _preview(layer, **overrides):
    values = {
        "tool_id": "tool",
        "connector_id": "connector",
        "action_type": "prepare_report",
        "target": "local-preview",
        "scope": ["workspace/report"],
    }
    values.update(overrides)
    return layer.preview_invocation(**values)


def _approval(preview, *, strong=False):
    service = ApprovalHardeningService()
    record = service.request(
        action_type=preview.controlled_runtime_request.action_type,
        context=preview.controlled_runtime_request.context(),
        approval_kind=ApprovalKind.STRONG if strong else ApprovalKind.NORMAL,
    )
    service.decide(
        record.approval_id,
        "approved",
        confirmation_phrase=record.user_confirmation_phrase if strong else None,
    )
    return record


def _ready(layer, preview, *, strong=False, permissions=None, **overrides):
    values = {
        "approval": _approval(preview, strong=strong),
        "granted_permissions": permissions or [],
        "policy_allowed": True,
        "sandbox_available": True,
        "timeout_present": True,
    }
    values.update(overrides)
    return layer.preview_permission(preview, **values)


def test_status_registry_and_contract_defaults_are_prepare_only_default_deny():
    layer = ToolInvocationLayer()
    status = layer.status()
    snapshot = layer.registry.snapshot().to_dict()
    assert status["prepare_only"] is True
    assert status["tool_execution_enabled"] is False
    assert status["external_calls_enabled"] is False
    assert status["credentials_enabled"] is False
    assert status["filesystem_writes_enabled"] is False
    assert snapshot["default_deny"] is True
    assert snapshot["execution_enabled"] is False
    assert snapshot["production_enabled"] is False
    assert ToolDefinition("id", "name", ConnectorType.MOCK_SAFE).enabled is False
    assert ToolDefinition("id", "name", ConnectorType.MOCK_SAFE, execution_enabled=True).execution_enabled is False
    connector = ConnectorDefinition("id", ConnectorType.MOCK_SAFE)
    assert connector.read_only_by_default is True
    assert connector.write_disabled_by_default is True


def test_default_connector_contracts_model_required_boundaries_without_credentials():
    connectors = {item.connector_type: item for item in default_connector_definitions()}
    local = connectors[ConnectorType.LOCAL_FILESYSTEM_SCOPED]
    github = connectors[ConnectorType.GITHUB]
    browser = connectors[ConnectorType.WEB_BROWSER]
    api = connectors[ConnectorType.EXTERNAL_API]
    assert local.filesystem_scope_required is True
    assert github.requires_credentials is True
    assert github.credentials_loaded is False
    assert browser.network_required is True
    assert browser.enabled is False
    assert api.approval_required is True
    assert api.strong_approval_required is True


def test_registration_connector_and_invocation_previews_never_execute_or_enable():
    app = create_app()
    registration = _route(app, "/tools/preview-registration", "POST").endpoint(
        ToolRegistrationPreviewRequest(tool_id="new", name="new", enabled=True)
    )
    connector = _route(app, "/tools/preview-connector", "POST").endpoint(
        ConnectorPreviewRequest(connector_id="new", enabled=True)
    )
    invocation = _route(app, "/tools/preview-invocation", "POST").endpoint(
        ToolInvocationPreviewRequest(
            tool_id="github-preview",
            connector_id="github",
            action_type="create_pr",
            target="repo",
            scope=["repo"],
            external_call=True,
            filesystem_write=True,
            credentials=True,
        )
    )
    assert registration["enabled"] is False
    assert registration["execution_enabled"] is False
    assert connector["enabled"] is False
    assert connector["credentials_loaded"] is False
    for field in ("would_execute", "would_call_external", "would_write_files", "would_use_credentials"):
        assert invocation[field] is False


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"tool_id": "missing"}, "tool is not registered"),
        ({"connector_id": "missing"}, "connector is not registered"),
        ({"action_type": ""}, "action_type is empty"),
        ({"target": ""}, "target is empty"),
        ({"scope": []}, "scope is empty"),
    ],
)
def test_missing_registration_or_invocation_context_blocks(change, reason):
    layer = _enabled_layer()
    result = layer.preview_permission(_preview(layer, **change))
    assert result.safe_to_invoke is False
    assert reason in result.blocked_reasons


def test_registered_but_disabled_tool_and_connector_block():
    registry = ToolRegistry(include_defaults=False)
    registry.register_tool(ToolDefinition("tool", "tool", ConnectorType.MOCK_SAFE))
    registry.register_connector(ConnectorDefinition("connector", ConnectorType.MOCK_SAFE))
    result = ToolInvocationLayer(registry=registry).preview_permission(
        ToolInvocationLayer(registry=registry).preview_invocation(
            tool_id="tool",
            connector_id="connector",
            action_type="preview",
            target="target",
            scope=["scope"],
        )
    )
    assert "tool is disabled" in result.blocked_reasons
    assert "connector is disabled" in result.blocked_reasons


def test_external_credentials_filesystem_production_and_side_effect_rules_block_without_gates():
    layer = _enabled_layer(
        connector_type=ConnectorType.EXTERNAL_API,
        tool_overrides={
            "required_permissions": ["network", "api_scope"],
            "external_call_required": True,
            "secrets_required": True,
            "production_capable": True,
            "write_capable": True,
            "side_effect_capable": True,
            "requires_strong_approval": True,
        },
        connector_overrides={
            "requires_credentials": True,
            "network_required": True,
            "external_call_required": True,
            "strong_approval_required": True,
        },
    )
    preview = _preview(layer, filesystem_write=True, production=True, side_effects=True)
    result = layer.preview_permission(preview, granted_permissions=["network", "api_scope"], policy_allowed=True)
    assert result.safe_to_invoke is False
    assert "external call requires explicit network permission" in result.blocked_reasons
    assert "credentials require valid strong approval" in result.blocked_reasons
    assert "filesystem write requires explicit scope" in result.blocked_reasons
    assert "required rollback plan missing" in result.blocked_reasons


def test_declared_strong_approval_and_connector_blocked_reasons_are_enforced():
    strong_layer = _enabled_layer(tool_overrides={"requires_strong_approval": True})
    strong_preview = _preview(strong_layer)
    normal_result = _ready(strong_layer, strong_preview)
    assert "valid strong approval required" in normal_result.blocked_reasons
    assert normal_result.safe_to_invoke is False

    blocked_layer = _enabled_layer(connector_overrides={"blocked_reasons": ["connector policy block"]})
    blocked_result = _ready(blocked_layer, _preview(blocked_layer))
    assert "connector policy block" in blocked_result.blocked_reasons
    assert blocked_result.safe_to_invoke is False


def test_permission_gate_allowed_runtime_safe_and_safe_to_invoke_never_execute():
    layer = _enabled_layer()
    preview = _preview(layer)
    result = _ready(layer, preview)
    assert result.permission_gate_allowed is True
    assert result.runtime_gate_safe_to_execute is True
    assert result.safe_to_invoke is True
    assert result.allowed_for_future_invocation is True
    assert result.allowed is False
    assert result.execution_enabled is False
    assert result.would_execute is False
    assert preview.would_execute is False


def test_permission_denied_blocks_and_result_defaults_cannot_enable_execution():
    layer = _enabled_layer()
    denied = layer.preview_permission(_preview(layer), policy_allowed=True, sandbox_available=True, timeout_present=True)
    forced = ToolPermissionCheckResult(allowed=True, safe_to_invoke=True, execution_enabled=True, would_execute=True)
    assert denied.permission_gate_allowed is False
    assert denied.safe_to_invoke is False
    assert forced.allowed is False
    assert forced.execution_enabled is False
    assert forced.would_execute is False


def test_audit_and_payload_redact_secrets_tokens_and_env():
    layer = _enabled_layer()
    preview = _preview(layer, payload_summary={"token": "abc", "nested": {"password": "xyz"}, "text": "read .env"})
    result = layer.preview_permission(preview)
    serialized = str({"preview": preview.to_dict(), "result": result.to_dict()}).lower()
    assert "'token': 'abc'" not in serialized
    assert "'password': 'xyz'" not in serialized
    assert ".env" not in serialized


def test_tools_api_routes_are_control_plane_only_do_not_mutate_or_call_external(monkeypatch):
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
    missions_before = app.state.mission_control.list_missions()
    tasks_before = app.state.task_store.list()
    assert _route(app, "/tools/status", "GET").endpoint()["prepare_only"] is True
    assert _route(app, "/tools/registry", "GET").endpoint()["default_deny"] is True
    assert _route(app, "/tools/policy", "GET").endpoint()["default_deny"] is True
    payload = ToolInvocationPreviewRequest(
        tool_id="mock-safe-preview",
        connector_id="mock-safe",
        action_type="preview",
        target="target",
        scope=["scope"],
    )
    assert _route(app, "/tools/preview-invocation", "POST").endpoint(payload)["would_execute"] is False
    assert _route(app, "/tools/preview-permission", "POST").endpoint(payload)["execution_enabled"] is False
    assert app.state.mission_control.list_missions() == missions_before == []
    assert app.state.task_store.list() == tasks_before == []
    for path in DANGEROUS_ROUTES:
        assert _route(app, path, "GET") is None
        assert _route(app, path, "POST") is None


def test_operational_command_center_operator_console_and_docs_reflect_macro_4():
    status = build_operational_system_status().to_dict()
    command = build_command_center_view_model(view_id="post-s-4", generated_at="2026-06-10T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="post-s-4", generated_at="2026-06-10T00:00:00+00:00")
    for field in (
        "tool_registry_available",
        "connector_contracts_available",
        "tool_invocation_preview_available",
        "real_connectors_control_plane_available",
        "controlled_runtime_bridge_required",
        "safe_to_invoke_is_readiness_only",
    ):
        assert status[field] is True
    for field in (
        "tool_execution_enabled",
        "external_calls_enabled",
        "credentials_enabled",
        "filesystem_writes_enabled",
        "github_actions_enabled",
        "browser_actions_enabled",
        "api_calls_enabled",
    ):
        assert status[field] is False
    for marker in (
        "post_s_real_connectors_tool_layer",
        "tool_registry",
        "connector_contracts",
        "tool_invocation_preview",
        "connector_permission_gate",
        "controlled_runtime_required",
        "safe_to_invoke_readiness_only",
        "tool_execution_disabled",
        "external_calls_disabled",
        "access_material_disabled",
    ):
        assert command.metadata[marker] == "prepare_only"
        assert operator.metadata[marker] == "prepare_only"
    content = DOC.read_text(encoding="utf-8")
    assert "no es Phase T" in content
    assert "safe_to_invoke=true" in content
    assert "no ejecuta" in content.lower()
    assert "Post-S Macro 5" in content
    assert NEXT_MACRO_PR == "Post-S Macro 5 - Memory, Personal OS & Scheduler Real"
