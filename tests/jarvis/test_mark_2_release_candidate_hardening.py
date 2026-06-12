from __future__ import annotations

import builtins
import json
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import create_app
from jarvis.command_center import build_command_center_view_model
from jarvis.mark_2_approval_path_audit import Mark2ApprovalPathAudit
from jarvis.mark_2_dangerous_route_audit import DANGEROUS_ROUTE_PATTERNS, Mark2DangerousRouteAudit
from jarvis.mark_2_e2e_readiness import Mark2E2EReadinessSmoke
from jarvis.mark_2_operational_runbook import Mark2OperationalRunbook
from jarvis.mark_2_release_candidate import (
    Mark2CapabilityMatrix,
    Mark2ReadinessMatrix,
    Mark2ReleaseCandidateStatus,
    mark_2_release_candidate_markers,
)
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import build_operational_system_status


GET_ROUTES = (
    "/mark-2/release-candidate/status",
    "/mark-2/release-candidate/capabilities",
    "/mark-2/release-candidate/readiness",
    "/mark-2/release-candidate/dangerous-route-audit",
    "/mark-2/release-candidate/approval-path-audit",
    "/mark-2/release-candidate/e2e-smoke",
    "/mark-2/release-candidate/runbook",
    "/mark-2/release-candidate/known-limitations",
    "/mark-2/release-candidate/next-steps",
)
FORBIDDEN_ROUTES = (
    "/mark-2/release-candidate/execute",
    "/mark-2/release-candidate/approve-all",
    "/mark-2/release-candidate/auto-approve",
    "/mark-2/release-candidate/deploy",
    "/mark-2/release-candidate/pay",
    "/mark-2/release-candidate/send-email",
    "/mark-2/release-candidate/run-codex",
    "/mark-2/release-candidate/run-claude",
    "/mark-2/release-candidate/use-cookies",
    "/mark-2/release-candidate/use-session-token",
    "/mark-2/release-candidate/read-env",
)
FORBIDDEN_COMMAND_CENTER = (
    ".env", "api_key", "apikey", "secret", "token", "password", "credential",
    "authorization", "audio_path", "audio_bytes", "ref_audio", "base_url", "prompt_text",
)


def _route(app, path, method="GET"):
    return next((route for route in app.routes if route.path == path and method in route.methods), None)


def test_status_closes_mark_2_as_controlled_release_candidate():
    status = Mark2ReleaseCandidateStatus().to_dict()
    assert status["release_candidate"] and status["mark_2_complete_as_release_candidate"]
    assert len(status["completed_macro_prs"]) == 4
    assert status["mark_2_not_full_autonomy"] and not status["mark_2_real_execution_default_enabled"]
    assert status["restrictions_are_approval_gates"] and status["voice_can_approve"]
    assert not status["wake_phrase_is_permission"]
    assert status["production_requires_strong_double_and_rollback"]
    assert status["money_requires_strong_double_or_triple"]
    assert status["no_fake_costs"]
    for name in (
        "real_deploy_enabled", "stripe_live_enabled", "email_send_enabled", "domain_publish_enabled",
        "codex_cli_real_invocation_enabled", "claude_code_real_invocation_enabled",
        "claude_cowork_real_invocation_enabled", "api_fallback_real_invocation_enabled",
        "external_network_enabled", "access_material_enabled",
    ):
        assert status[name] is False


def test_capability_and_readiness_matrices_cover_all_macros_without_side_effects():
    capabilities = {item["capability_id"]: item for item in Mark2CapabilityMatrix().to_dict()["capabilities"]}
    for name in (
        "local_daemon", "voice_approval_channel", "filesystem_candidate_execution",
        "github_candidate_execution", "browser_candidate_execution", "external_api_candidate_execution",
        "visual_command_center", "human_approval_console", "agent_operations_dashboard", "cost_usage_dashboard",
        "deploy_candidate_operations", "stripe_candidate_operations", "email_candidate_operations",
        "domain_candidate_operations", "codex_cli_adapter_preview", "claude_code_adapter_preview",
        "claude_cowork_adapter_preview", "api_fallback_adapter_preview", "routine_execution_bridge",
    ):
        assert name in capabilities
    assert all(item["real_side_effects_enabled_now"] is False for item in capabilities.values())
    readiness = Mark2ReadinessMatrix().to_dict()
    assert readiness["release_candidate_readiness"] == "ready_as_controlled_release_candidate"
    assert readiness["full_autonomy_readiness"] == "blocked"
    assert readiness["production_readiness"] == "pilot_ready_after_manual_setup_and_valid_approvals"


def test_dangerous_route_and_approval_path_audits_pass():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    audit = Mark2DangerousRouteAudit().audit(route.path for route in app.routes)
    assert audit["passed"] and audit["blocked_or_absent"] and audit["dangerous_routes_registered"] == []
    assert set(DANGEROUS_ROUTE_PATTERNS) <= set(audit["dangerous_routes_checked"])
    paths = {item["action_type"]: item for item in Mark2ApprovalPathAudit().audit()["approval_paths"]}
    for name in ("production deploy", "Stripe live/payment", "email send", "domain/DNS publish", "Codex CLI invocation", "Claude Code invocation", "Claude Cowork routine", "API fallback"):
        assert name in paths
        assert paths[name]["audit_required"] and paths[name]["wake_phrase_allowed"] is False
    for item in paths.values():
        if item["risk_level"] == "critical":
            assert item["approval_required"] and item["strong_approval_required"] and item["double_confirmation_required"]


def test_e2e_smoke_is_prepare_only_and_runbook_covers_operations():
    smoke = Mark2E2EReadinessSmoke().run()
    assert smoke["passed"] and smoke["prepare_only"] and smoke["audit_safe"] and smoke["no_fake_costs"]
    for name in ("would_execute", "would_deploy", "would_move_money", "would_send_email", "would_modify_dns", "would_call_external", "access_material_enabled", "external_network_enabled", "wake_phrase_is_permission"):
        assert smoke[name] is False
    assert smoke["voice_can_approve"] and smoke["kill_switch_stop_control_ready"]
    runbook = json.dumps(Mark2OperationalRunbook().to_dict())
    for text in ("jarvis-finish-pr", "TestClient", "main' is already used by worktree", "kill switch", "Codex CLI login", "Claude Code login"):
        assert text in runbook


def test_rc_endpoints_are_read_only_safe_and_dangerous_routes_absent(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("network called"))
    monkeypatch.setattr(Path, "write_text", lambda *a, **k: pytest.fail("filesystem write"))
    original_open = builtins.open

    def guarded_open(file, *args, **kwargs):
        if str(file).endswith(".env"):
            pytest.fail(".env read")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    for path in GET_ROUTES:
        route = _route(app, path)
        assert route is not None and isinstance(route.endpoint(), dict)
    for path in FORBIDDEN_ROUTES:
        assert _route(app, path, "GET") is None and _route(app, path, "POST") is None


def test_operational_command_center_and_operator_console_have_safe_rc_markers():
    markers = mark_2_release_candidate_markers()
    operational = build_operational_system_status().to_dict()
    command = build_command_center_view_model(view_id="mark-2-rc", generated_at="2026-06-12T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="mark-2-rc", generated_at="2026-06-12T00:00:00+00:00")
    for marker, expected in markers.items():
        assert operational[marker] == expected
        assert command.metadata[marker] == expected
        assert operator.metadata[marker] == expected
    serialized = json.dumps(command.to_dict()).lower()
    for forbidden in FORBIDDEN_COMMAND_CENTER:
        assert forbidden not in serialized


def test_release_candidate_docs_cover_required_boundaries():
    release = Path("docs/jarvis-mark-2-release-candidate.md").read_text(encoding="utf-8")
    runbook = Path("docs/jarvis-mark-2-operational-runbook.md").read_text(encoding="utf-8")
    combined = f"{release}\n{runbook}"
    for text in (
        "Mark 2 Release Candidate", "no es autonomía libre", "manual setup", "cookies",
        "session tokens", "access material", "Voice Approval Channel", "wake phrase",
        "Mark 3", "jarvis-finish-pr", "TestClient",
    ):
        assert text in combined
