from __future__ import annotations

import builtins
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import create_app
from jarvis.command_center import build_command_center_view_model
from jarvis.mark_1_e2e_readiness import Mark1E2ERealOpsSmoke
from jarvis.mark_1_operational_runbook import Mark1KnownLimitations, Mark1OperationalRunbook, Mark2NextPlan
from jarvis.mark_1_release_candidate import (
    FORBIDDEN_MARK_1_ROUTES,
    Mark1ApprovalPathAudit,
    Mark1CapabilityMatrix,
    Mark1DangerousRouteAudit,
    Mark1DocumentationStatus,
    Mark1ReleaseCandidateStatus,
    mark_1_release_candidate_markers,
)
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import build_operational_console_summary, build_operational_system_status


MARK_1_GET_ROUTES = (
    "/mark-1/status",
    "/mark-1/capabilities",
    "/mark-1/e2e-smoke",
    "/mark-1/dangerous-route-audit",
    "/mark-1/approval-path-audit",
    "/mark-1/docs-status",
    "/mark-1/runbook",
    "/mark-1/known-limitations",
    "/mark-1/next-plan",
)
RELEASE_DOC = Path("docs/jarvis-mark-1-release-candidate.md")
RUNBOOK_DOC = Path("docs/jarvis-mark-1-operational-runbook.md")


def _route(app, path: str, method: str = "GET"):
    return next((route for route in app.routes if route.path == path and method in route.methods), None)


def test_mark_1_release_candidate_status_has_required_safe_defaults():
    status = Mark1ReleaseCandidateStatus().to_dict()
    assert status["current_mark"] == "Mark 1"
    assert status["mark_1_release_candidate"] is True
    assert status["mark_1_ready"] is True
    assert status["phase_s_is_last_master_phase"] is True
    assert status["phase_t_exists"] is False
    assert status["post_s_macro_prs_complete"] is True
    assert status["restrictions_are_approval_gates"] is True
    assert status["prepare_only_forever"] is False
    assert status["execution_requires_valid_approval"] is True
    assert status["critical_actions_require_double_confirmation"] is True
    for name in (
        "real_external_execution_enabled",
        "real_money_movement_enabled",
        "real_deploy_enabled",
        "real_publish_enabled",
        "real_sensor_activation_enabled",
    ):
        assert status[name] is False
    assert status["mark_2_planned"] is True
    assert status["mark_3_planned"] is True
    assert status["next_recommended_mark"] == "Mark 2"


def test_capability_matrix_covers_mark_1_cross_cutting_capabilities():
    payload = Mark1CapabilityMatrix().to_dict()
    capabilities = {item["capability_name"]: item for item in payload["capabilities"]}
    for name in (
        "approval_controlled_execution",
        "audit",
        "permission_gates",
        "controlled_runtime",
        "tool_registry_and_invocation",
        "memory",
        "personal_os",
        "scheduler",
        "wake_voice",
        "camera_control",
        "monetization",
        "adaptive_saas_builder",
        "publishing_deploy_candidates",
        "operational_console",
        "command_center",
        "operator_console",
        "documentation",
        "tests",
    ):
        assert capabilities[name]["available"] is True
        assert capabilities[name]["control_plane_ready"] is True
        assert capabilities[name]["real_execution_enabled_by_default"] is False
        assert capabilities[name]["mark_1_status"] == "ready"


def test_e2e_real_ops_smoke_composes_full_flow_without_execution():
    payload = Mark1E2ERealOpsSmoke().run(simulated_valid_approval=True)
    stages = [item["stage"] for item in payload["stages"]]
    assert stages == [
        "idea_intake",
        "validation_contrarian",
        "differentiation_review",
        "blueprint",
        "pricing_preview",
        "revenue_projection",
        "budget_guard",
        "publishing_plan",
        "deploy_plan",
        "execution_candidate",
        "approval_decision",
        "critical_warning",
        "launch_readiness_review",
    ]
    assert payload["passed"] is True
    assert payload["eligible_after_valid_approval"] is True
    for name in (
        "would_execute",
        "would_create_repo",
        "would_write_external_filesystem",
        "would_call_external",
        "would_use_credentials",
        "would_move_money",
        "would_deploy",
        "would_publish",
    ):
        assert payload[name] is False
    candidate = next(item["result"] for item in payload["stages"] if item["stage"] == "execution_candidate")
    assert candidate["eligible_after_valid_approval"] is True
    assert candidate["would_execute"] is False


def test_e2e_without_simulated_approval_remains_blocked():
    payload = Mark1E2ERealOpsSmoke().run(simulated_valid_approval=False)
    candidate = next(item["result"] for item in payload["stages"] if item["stage"] == "execution_candidate")
    assert candidate["eligible_after_valid_approval"] is False
    assert "valid explicit approval required" in candidate["blocked_reasons"]
    assert payload["would_execute"] is False


def test_dangerous_route_audit_passes_and_detects_injected_forbidden_route():
    clean = Mark1DangerousRouteAudit().audit(MARK_1_GET_ROUTES)
    unsafe = Mark1DangerousRouteAudit().audit([*MARK_1_GET_ROUTES, "/mark-1/deploy-production"])
    assert clean["dangerous_routes_absent"] is True
    assert clean["findings"] == []
    assert unsafe["dangerous_routes_absent"] is False
    assert unsafe["findings"] == ["/mark-1/deploy-production"]


def test_approval_path_audit_requires_all_critical_gates():
    payload = Mark1ApprovalPathAudit().audit()
    examples = {item["action_name"]: item for item in payload["examples"]}
    for name in ("deploy production", "Stripe live charge", "external publish", "microphone/camera real activation"):
        assert examples[name]["approval_required"] is True
        assert examples[name]["strong_approval_required"] is True
        assert examples[name]["double_confirmation_required"] is True
        assert examples[name]["audit_required"] is True
        assert examples[name]["permission_gates_required"] is True
        assert examples[name]["context_fingerprint_required"] is True
        assert examples[name]["rollback_or_stop_plan_required"] is True
        assert examples[name]["would_execute"] is False
    assert examples["GitHub repo creation"]["strong_approval_required"] is True
    assert examples["filesystem write"]["strong_approval_required"] is True


def test_mark_1_get_endpoints_exist_return_200_contracts_and_never_call_side_effects(monkeypatch):
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
    for path in MARK_1_GET_ROUTES:
        route = _route(app, path)
        assert route is not None
        assert route.status_code in (None, 200)
        payload = route.endpoint()
        assert isinstance(payload, dict)
    for path in FORBIDDEN_MARK_1_ROUTES:
        assert _route(app, path, "GET") is None
        assert _route(app, path, "POST") is None


def test_operational_command_center_and_operator_console_expose_mark_1_markers():
    markers = mark_1_release_candidate_markers()
    operational = build_operational_system_status().to_dict()
    summary = build_operational_console_summary()
    command = build_command_center_view_model(view_id="mark-1", generated_at="2026-06-11T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="mark-1", generated_at="2026-06-11T00:00:00+00:00")
    for marker, expected in markers.items():
        assert summary["command_center"][marker] == expected
        assert command.metadata[marker] == expected
        assert operator.metadata[marker] == expected
    assert operational["mark_1_release_candidate"] is True
    assert operational["mark_1_runtime_ready"] is True
    assert operational["mark_1_tools_ready"] is True
    assert operational["mark_1_memory_ready"] is True
    assert operational["mark_1_voice_camera_ready"] is True
    assert operational["real_external_execution_enabled"] is False


def test_docs_status_runbook_limitations_and_next_plan_are_explicit():
    docs = Mark1DocumentationStatus().to_dict()
    runbook = Mark1OperationalRunbook().to_dict()
    limitations = Mark1KnownLimitations().to_dict()
    plan = Mark2NextPlan().to_dict()
    serialized_runbook = str(runbook)
    serialized_limits = str(limitations)
    serialized_plan = str(plan)
    assert docs["docs_ready"] is True
    assert docs["phase_t_exists"] is False
    assert docs["mark_1_release_candidate_doc_present"] is True
    assert docs["mark_1_runbook_present"] is True
    for text in ("worktree", "Codex", "jarvis-finish-pr", "401", "/mark-1/status"):
        assert text in serialized_runbook
    for text in ("daemon", "microphone wake listener", "advanced visual UI", "deep real tool execution", "Stripe live", "24/7"):
        assert text in serialized_limits
    assert "Mark 2" in serialized_plan and "Mark 3" in serialized_plan
    assert plan["no_micro_pr_policy"] is True
    assert plan["phase_t_exists"] is False


def test_release_docs_exist_use_marks_and_do_not_claim_finished_forever():
    release = RELEASE_DOC.read_text(encoding="utf-8")
    runbook = RUNBOOK_DOC.read_text(encoding="utf-8")
    normalized_release = " ".join(release.split())
    assert "Mark 1 Release Candidate" in release
    assert "No existe Phase T" in release
    assert "Restrictions are approval gates, not permanent bans" in release
    assert "Mark 2" in release and "Mark 3" in release
    assert "terminado para siempre" in normalized_release
    assert "no incluye daemon local real" in release
    assert "jarvis-finish-pr" in runbook
    assert "401" in runbook
    assert "120 micro-PRs" in runbook


def test_no_document_approves_phase_t():
    for path in (
        Path("docs/JARVIS_MASTER_BUILD_MAP.md"),
        Path("docs/jarvis-handoff-context.md"),
        RELEASE_DOC,
        RUNBOOK_DOC,
    ):
        content = path.read_text(encoding="utf-8").lower()
        assert "phase t | aprobada" not in content
        assert "phase t: approved" not in content
        assert "phase t is approved" not in content
