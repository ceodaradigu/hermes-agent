from __future__ import annotations

import builtins
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import create_app
from jarvis.command_center import build_command_center_view_model
from jarvis.mission_control import MissionControl
from jarvis.operator_console import build_operational_console_summary
from jarvis.operational_consolidation import (
    CapabilityReadiness,
    CapabilitySummary,
    NEXT_MACRO_PR,
    OperationalSystemStatus,
    SafetyBoundarySummary,
    build_capability_registry,
    build_operational_system_status,
    build_readiness_matrix,
    build_safety_boundary_summary,
)
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


DOC = Path("docs/jarvis-post-s-operational-console-system-consolidation.md")
CAPABILITY_NAMES = {
    "mission_core",
    "approvals_policy",
    "hermes_bridge",
    "command_center",
    "operator_console",
    "voice",
    "mobile",
    "ambient_vision",
    "multi_device",
    "sandbox_execution",
    "tool_adoption",
    "asset_factory",
    "deploy_publishing",
    "marketing_distribution",
    "payments_revenue",
    "daily_operator",
    "continuous_learning",
    "personal_os",
    "advanced_personalization",
    "future_moonshot",
    "smoke_validation",
}
OPERATIONAL_GET_ROUTES = (
    "/operational/status",
    "/operational/capabilities",
    "/operational/readiness",
    "/operational/safety-boundaries",
    "/operational/console-summary",
)
DANGEROUS_OPERATIONAL_ROUTES = (
    "/operational/execute",
    "/operational/run",
    "/operational/approve",
    "/operational/deploy",
    "/operational/send",
    "/operational/install",
    "/operational/activate",
    "/operational/start-worker",
)


class FailHermesAdapter:
    def run(self, *args, **kwargs):
        raise AssertionError("Hermes must not be called by operational consolidation")


class FailApprovalGateway:
    def create_request(self, *args, **kwargs):
        raise AssertionError("ApprovalGateway must not be called by operational consolidation")


@pytest.fixture
def app():
    return create_app(adapter_factory=lambda: FailHermesAdapter(), approval_gateway=FailApprovalGateway())


def _route(app, path: str, method: str = "GET"):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route
    return None


def test_operational_status_is_post_s_prepare_only_and_fully_disabled():
    payload = build_operational_system_status().to_dict()

    assert payload["prepare_only"] is True
    assert payload["phase_range"] == "A-S"
    assert payload["last_master_phase"] == "Phase S"
    assert payload["no_phase_t"] is True
    assert payload["global_readiness"] == "foundation_complete_prepare_only"
    for field in (
        "runtime_execution_enabled",
        "side_effects_enabled",
        "external_calls_enabled",
        "secrets_access_enabled",
        "hermes_called",
        "approval_gateway_called",
        "persistence_enabled",
    ):
        assert payload[field] is False


def test_operational_dtos_cannot_be_manually_enabled():
    status = OperationalSystemStatus(runtime_execution_enabled=True, side_effects_enabled=True)
    capability = CapabilitySummary(
        name="unsafe",
        category="test",
        phase_or_source="test",
        prepare_only=False,
        blocked=False,
        execution_enabled=True,
        side_effects_enabled=True,
        external_calls_enabled=True,
    )
    readiness = CapabilityReadiness(
        name="unsafe",
        ready_for_preview=True,
        ready_for_dry_run=True,
        ready_for_real_execution=True,
        missing_requirements=["hardening"],
        approval_requirements=["approval"],
        risk_level="high",
        next_safe_step="remain disabled",
    )
    boundaries = SafetyBoundarySummary(no_execution=False, no_production=False)

    assert status.runtime_execution_enabled is False
    assert status.side_effects_enabled is False
    assert capability.prepare_only is True
    assert capability.blocked is True
    assert capability.execution_enabled is False
    assert capability.side_effects_enabled is False
    assert capability.external_calls_enabled is False
    assert readiness.ready_for_real_execution is False
    assert boundaries.no_execution is True
    assert boundaries.no_production is True


def test_capability_registry_covers_a_s_and_disables_all_execution_and_side_effects():
    capabilities = build_capability_registry()

    assert {item.name for item in capabilities} == CAPABILITY_NAMES
    assert all(item.prepare_only for item in capabilities)
    assert all(item.execution_enabled is False for item in capabilities)
    assert all(item.side_effects_enabled is False for item in capabilities)
    assert all(item.external_calls_enabled is False for item in capabilities)
    assert all(item.blocked for item in capabilities)


def test_readiness_matrix_preserves_requirements_and_never_enables_real_execution():
    matrix = build_readiness_matrix()

    assert {item.name for item in matrix} == CAPABILITY_NAMES
    assert all(item.ready_for_preview for item in matrix)
    assert all(item.ready_for_real_execution is False for item in matrix)
    assert all(item.missing_requirements for item in matrix)
    assert all(item.approval_requirements for item in matrix)
    assert all(item.next_safe_step for item in matrix)


def test_safety_boundaries_block_sensitive_and_physical_operations():
    payload = build_safety_boundary_summary().to_dict()

    for field in (
        "no_execution",
        "no_production",
        "no_payments_movement",
        "no_credential_access",
        "no_external_calls_by_default",
        "no_camera_by_default",
        "no_microphone_by_default",
        "no_screen_capture_by_default",
        "no_camera_microphone_screen_by_default",
        "no_physical_world_automation",
        "no_memory_activation_unless_explicitly_approved",
        "no_scheduler_execution_unless_approved",
        "no_deployment_unless_strong_approval",
    ):
        assert payload[field] is True


def test_operator_console_summary_and_command_center_marker_are_consolidated_prepare_only():
    summary = build_operational_console_summary()
    command_center = build_command_center_view_model(view_id="post-s", generated_at="2026-06-10T00:00:00+00:00")

    assert summary["prepare_only"] is True
    assert summary["operational_status"]["prepare_only"] is True
    assert summary["next_recommended_macro_pr"] == NEXT_MACRO_PR
    assert summary["blocked_actions"]
    assert summary["visible_reasons"]
    assert command_center.metadata["post_s_operational_consolidation"] is True
    assert command_center.metadata["global_readiness"] == "foundation_complete_prepare_only"
    assert command_center.metadata["system_map"]["no_phase_t"] is True
    assert command_center.metadata["safe_next_steps"]


def test_operational_api_get_routes_are_http_200_read_only_and_dangerous_routes_are_absent(app):
    for path in OPERATIONAL_GET_ROUTES:
        route = _route(app, path)
        assert route is not None, path
        assert route.status_code in (None, 200)
        payload = route.endpoint()
        assert payload["prepare_only"] is True

    for path in DANGEROUS_OPERATIONAL_ROUTES:
        assert _route(app, path, "POST") is None
        assert _route(app, path, "GET") is None


def test_operational_views_do_not_call_hermes_approval_gateway_or_create_missions(monkeypatch, app):
    monkeypatch.setattr(HermesRuntimeAdapter, "run", lambda *args, **kwargs: pytest.fail("Hermes called"), raising=False)
    monkeypatch.setattr(ApprovalGateway, "create_request", lambda *args, **kwargs: pytest.fail("ApprovalGateway called"))
    monkeypatch.setattr(MissionControl, "create_mission", lambda *args, **kwargs: pytest.fail("mission created"))

    missions_before = app.state.mission_control.list_missions()
    for path in OPERATIONAL_GET_ROUTES:
        _route(app, path).endpoint()
    assert app.state.mission_control.list_missions() == missions_before == []


def test_operational_views_do_not_read_env_files_use_shell_or_network(monkeypatch, app):
    original_open = builtins.open

    def guarded_open(file, *args, **kwargs):
        if str(file).endswith(".env"):
            raise AssertionError(".env must not be read")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: pytest.fail("subprocess.run called"))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: pytest.fail("subprocess.Popen called"))
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: pytest.fail("network called"))

    for path in OPERATIONAL_GET_ROUTES:
        assert _route(app, path).endpoint()["prepare_only"] is True


def test_post_s_operational_consolidation_docs_keep_no_phase_t_and_next_macro_pr():
    content = DOC.read_text(encoding="utf-8")

    assert "no es Phase T" in content
    assert "No existe Phase T" in content
    assert "foundation_complete_prepare_only" in content
    assert "Post-S Macro 2" in content
    assert "Real Approval, Audit & Permission Hardening" in content
    assert "test_e2e_prepare_only_smoke_after_phase_s.py" in content
