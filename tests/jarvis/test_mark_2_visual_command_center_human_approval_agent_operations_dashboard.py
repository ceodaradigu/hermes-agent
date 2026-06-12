from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import create_app
from jarvis.command_center import build_command_center_view_model
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import build_operational_system_status
from jarvis.visual_command_center import (
    VisualCommandCenter,
    VisualCommandCenterStatus,
    mark_2_visual_dashboard_markers,
)


DOC = Path("docs/jarvis-mark-2-visual-command-center-human-approval-agent-operations-dashboard.md")
SAFE_ROUTES = (
    "/mark-2/dashboard/status",
    "/mark-2/dashboard/overview",
    "/mark-2/dashboard/panels",
    "/mark-2/dashboard/agents",
    "/mark-2/dashboard/sessions",
    "/mark-2/dashboard/costs",
    "/mark-2/dashboard/approvals",
    "/mark-2/dashboard/risks",
    "/mark-2/dashboard/worktree-guard",
    "/mark-2/dashboard/diffs-tests-reviews",
    "/mark-2/dashboard/audit",
    "/mark-2/dashboard/next-actions",
)
DANGEROUS_ROUTES = (
    "/mark-2/dashboard/execute",
    "/mark-2/dashboard/run-agent",
    "/mark-2/dashboard/start-codex-real",
    "/mark-2/dashboard/start-claude-real",
    "/mark-2/dashboard/use-session-token",
    "/mark-2/dashboard/read-env",
    "/mark-2/dashboard/approve-all",
    "/mark-2/dashboard/auto-approve",
    "/mark-2/dashboard/deploy",
    "/mark-2/dashboard/pay",
    "/mark-2/dashboard/charge",
    "/mark-2/dashboard/push",
    "/mark-2/dashboard/merge",
)
FORBIDDEN_COMMAND_CENTER = (
    ".env", "api_key", "apikey", "secret", "token", "password", "credential",
    "authorization", "audio_path", "audio_bytes", "ref_audio", "base_url", "prompt_text",
)


def test_all_dashboard_get_endpoints_are_registered_read_only_and_dangerous_routes_are_absent():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    for path in SAFE_ROUTES:
        route = next(route for route in app.routes if route.path == path and "GET" in route.methods)
        assert isinstance(route.endpoint(), dict)
    registered = {(method, route.path) for route in app.routes for method in route.methods}
    for path in DANGEROUS_ROUTES:
        assert ("GET", path) not in registered
        assert ("POST", path) not in registered


def test_status_and_overview_are_control_plane_only_and_safe():
    status = VisualCommandCenterStatus().to_dict()
    overview = VisualCommandCenter().overview()
    for key in (
        "visual_command_center_available", "human_approval_console_available",
        "agent_operations_dashboard_available", "ai_coding_session_control_available",
        "cost_usage_dashboard_available", "risk_panel_available", "audit_timeline_available",
        "worktree_guard_panel_available", "diff_test_review_panel_available",
        "kill_switch_visible", "stop_control_visible", "voice_approval_visible",
        "dashboard_data_endpoints_available", "control_plane_only", "no_fake_costs",
    ):
        assert status[key] is True
    for key in (
        "real_frontend_enabled", "real_agent_execution_enabled", "real_ai_cli_invocation_enabled",
        "codex_cli_real_invocation_enabled", "claude_code_real_invocation_enabled",
        "claude_cowork_real_invocation_enabled", "api_fallback_real_invocation_enabled",
        "external_network_enabled", "access_material_enabled", "wake_phrase_is_permission",
    ):
        assert status[key] is False
    assert status["voice_can_approve"] is True
    assert overview["safe_to_render"] is True
    assert overview["dashboard_health"] == "ready_control_plane_only"


def test_panels_agents_and_sessions_model_required_operational_views():
    dashboard = VisualCommandCenter()
    panel_ids = {item["panel_id"] for item in dashboard.panels()}
    assert set(VisualCommandCenter.PANEL_IDS) <= panel_ids
    assert all(item["visible_to_human"] and item["safe_to_render"] and item["redaction_applied"] for item in dashboard.panels())

    agents = dashboard.agents()
    names = {item["display_name"] for item in agents}
    assert {"PlannerAgent", "BuilderAgent", "ReviewerAgent", "TesterAgent", "OperatorAgent"} <= names
    assert {"CodexCliAgent", "ClaudeCodeAgent", "ClaudeCoworkAgent", "ApiFallbackAgent"} <= names
    assert all(item["can_execute_now"] is False for item in agents)
    assert all("paid_by" in item and "cost_mode" in item for item in agents)

    sessions = dashboard.sessions()
    assert {item["session_type"] for item in sessions} == {
        "codex_cli", "claude_code", "claude_cowork", "api_fallback", "local_script",
    }
    assert all(item["would_invoke_real_tool"] is False for item in sessions)
    assert all(not item["merge_allowed"] and not item["deploy_allowed"] and not item["push_allowed"] for item in sessions)


def test_cost_dashboard_never_invents_costs_or_limits():
    costs = VisualCommandCenter().costs()
    assert all(item["no_fake_costs"] is True for item in costs)
    assert all(item["actual_cost"] is None and item["cost_known"] is False for item in costs)
    assert all(item["usage_limit_status"] in {"unknown", "manual_input_required"} for item in costs)
    assert any(item["billing_mode"] == "subscription" for item in costs)
    assert any(item["billing_mode"] == "api_usage" for item in costs)
    assert any(item["billing_mode"] == "local_compute" and item["estimated_cost"] == 0.0 for item in costs)


def test_approval_risk_worktree_diff_and_audit_defaults_are_conservative():
    dashboard = VisualCommandCenter()
    approvals = dashboard.approvals()
    assert all({"strong_approval_required", "double_confirmation_required", "triple_confirmation_required"} <= item.keys() for item in approvals)
    assert all(item["approve_action_available"] is False and item["would_execute_after_approval"] is False for item in approvals)
    assert any(item["channel"] == "voice" and item["voice_approval_allowed"] is True for item in approvals)

    risks = dashboard.risks()
    assert {"production", "money", "access_material", "filesystem", "github", "browser", "external_api", "privacy", "legal"} <= {item["risk_type"] for item in risks}
    assert dashboard.worktree_guard()["safe_to_finish_pr"] is False
    diff = dashboard.diff_test_review()
    assert diff["diff_available"] is False and diff["review_result"] == "unknown"
    assert diff["tests_run"] is None and diff["ready_for_finish_pr"] is False
    assert all(item["redaction_applied"] and item["safe_to_render"] for item in dashboard.audit())


def test_operational_command_center_and_operator_console_reflect_macro_3_without_forbidden_output():
    markers = mark_2_visual_dashboard_markers()
    operational = build_operational_system_status().to_dict()
    command = build_command_center_view_model(view_id="macro-3", generated_at="2026-06-12T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="macro-3", generated_at="2026-06-12T00:00:00+00:00")
    for marker, expected in markers.items():
        assert operational[marker] == expected
        assert command.metadata[marker] == expected
        assert operator.metadata[marker] == expected
    serialized = json.dumps(command.to_dict()).lower()
    for forbidden in FORBIDDEN_COMMAND_CENTER:
        assert forbidden not in serialized


def test_documentation_explains_macro_3_boundaries_and_next_macro():
    content = DOC.read_text(encoding="utf-8")
    for text in (
        "Mark 2 Macro 3", "dashboard operativo", "Codex", "Claude", "Cowork",
        "subscription", "unknown", "Voice Approval Channel", "wake phrase",
        "Mark 2 Macro 4", "Restrictions are approval gates, not permanent bans",
    ):
        assert text in content
