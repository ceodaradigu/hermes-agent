from __future__ import annotations

import builtins
import json
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (  # noqa: E402
    Mark3ProductRevenueFactoryRequest,
    Mark3ResearchExecutionCandidateRequest,
    Mark3RoutineOpsRequest,
    create_app,
)
from jarvis.mark_3_approval_path_audit import Mark3ApprovalPathAudit  # noqa: E402
from jarvis.mark_3_dangerous_route_audit import Mark3DangerousRouteAudit  # noqa: E402
from jarvis.mark_3_e2e_readiness import Mark3E2EReadinessSmoke  # noqa: E402
from jarvis.mark_3_local_research_adapter import LocalResearchReadAdapter  # noqa: E402
from jarvis.mark_3_moonshot_lab_research_experiment_engine import Mark3MoonshotLabResearchExperimentEngine  # noqa: E402
from jarvis.mark_3_pilot_plan import Mark3ControlledPilotPlan  # noqa: E402
from jarvis.mark_3_release_candidate import (  # noqa: E402
    Mark3CapabilityMatrix,
    Mark3ReadinessMatrix,
    Mark3ReleaseCandidateStatus,
)
from jarvis.mark_3_research_execution import ResearchExecutionControlPlane  # noqa: E402


GET_ROUTES = (
    "/mark-3/release-candidate/status",
    "/mark-3/release-candidate/capabilities",
    "/mark-3/release-candidate/readiness",
    "/mark-3/release-candidate/dangerous-route-audit",
    "/mark-3/release-candidate/approval-path-audit",
    "/mark-3/release-candidate/e2e-smoke",
    "/mark-3/release-candidate/pilot-plan",
    "/mark-3/release-candidate/runbook",
    "/mark-3/release-candidate/known-limitations",
    "/mark-3/release-candidate/next-steps",
)


def route(app, path, method="GET"):
    return next((item for item in app.routes if item.path == path and method in item.methods), None)


def test_status_declares_mark_3_rc_not_free_autonomy():
    status = Mark3ReleaseCandidateStatus().to_dict()

    assert status["release_candidate_status"] == "ready_as_controlled_release_candidate"
    assert status["ready_as_controlled_release_candidate"] is True
    assert status["not_ready_for_free_autonomy"] is True
    assert status["local_first"] is True
    assert status["human_control_required"] is True
    assert status["restrictions_are_approval_gates_not_permanent_bans"] is True
    assert status["hermes_remains_execution_engine"] is True
    assert status["no_duplicate_hermes_runtime"] is True
    for key in (
        "free_autonomy_enabled",
        "real_scheduler_enabled",
        "external_network_enabled",
        "github_web_providers_connected",
        "email_send_enabled",
        "stripe_live_enabled",
        "deploy_publish_domain_enabled",
        "credentials_or_access_material_enabled",
        "background_24_7_enabled",
        "production_enabled",
        "money_movement_enabled",
        "real_pilot_executed",
    ):
        assert status[key] is False


def test_capability_matrix_covers_required_mark_3_surfaces():
    payload = Mark3CapabilityMatrix().to_dict()
    capabilities = {item["capability_id"]: item for item in payload["capabilities"]}

    for capability_id in (
        "master_planning",
        "autonomous_mission_loop",
        "governed_hermes_runtime_read_file",
        "outcome_failure_memory",
        "learning_proposals",
        "growth_radar",
        "research_execution_control_plane",
        "local_docs_repo_research_adapter",
        "product_revenue_factory",
        "local_routine_scheduler_personal_family_ops",
        "moonshot_lab_research_experiment_engine",
    ):
        assert capability_id in capabilities
    assert capabilities["governed_hermes_runtime_read_file"]["real_execution_supported_now"] is True
    assert capabilities["local_docs_repo_research_adapter"]["real_execution_supported_now"] is True
    assert capabilities["governed_hermes_runtime_read_file"]["execution_default"] == "gated_read_only_disabled_by_default"
    assert capabilities["local_docs_repo_research_adapter"]["execution_default"] == "gated_read_only_disabled_by_default"
    assert all(item["real_execution_enabled_by_default"] is False for item in capabilities.values())
    assert payload["restrictions_are_approval_gates_not_permanent_bans"] is True


def test_readiness_matrix_marks_rc_ready_and_free_autonomy_not_ready():
    readiness = Mark3ReadinessMatrix().to_dict()

    assert readiness["release_candidate_status"] == "ready_as_controlled_release_candidate"
    assert readiness["ready_as_controlled_release_candidate"] is True
    assert readiness["not_ready_for_free_autonomy"] is True
    assert readiness["readiness"]["free_autonomy"] == "not_ready"
    assert readiness["readiness"]["real_scheduler"] == "not_ready"
    assert readiness["readiness"]["product_revenue_factory"] == "ready_prepare_only"
    assert readiness["readiness"]["moonshot_lab"] == "ready_prepare_only"
    assert readiness["pilot_readiness"] == "ready_to_prepare_local_controlled_pilot"
    assert readiness["pilot_executed"] is False


def test_dangerous_route_audit_confirms_no_new_free_dangerous_routes():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    audit = Mark3DangerousRouteAudit().audit(item.path for item in app.routes)

    assert audit["passed"] is True
    assert audit["blocked_or_absent"] is True
    assert audit["audited_route_prefixes"] == ["/mark-3/"]
    assert audit["dangerous_routes_registered"] == []
    for key in (
        "no_research_execute_route",
        "no_experiment_execute_route",
        "no_real_scheduler_cron_or_worker_route",
        "no_send_email_route",
        "no_gmail_calendar_contacts_real_route",
        "no_login_or_account_access_route",
        "no_password_storage_route",
        "no_token_cookie_session_use_route",
        "no_stripe_live_payment_checkout_route",
        "no_deploy_publish_domain_route",
        "no_install_subprocess_thread_network_route",
        "no_fake_revenue_cost_benchmark_result_capability_route",
    ):
        assert audit[key] is True
    assert "/mark-3/hermes-runtime/execute-read" in audit["allowed_gated_routes"]
    assert audit["execute_read_requires_valid_mission_candidate_approval_scope_and_operator_authorization"] is True


def test_approval_path_audit_covers_levels_zero_through_five():
    audit = Mark3ApprovalPathAudit().audit()
    paths = {item["level"]: item for item in audit["approval_paths"]}

    assert set(paths) == set(range(6))
    assert audit["coverage"]["level_0_1_low_risk"] is True
    assert audit["coverage"]["level_2_scoped_local_read_repo_docs"] is True
    assert audit["coverage"]["level_3_external_research_private_metrics_ai_cli_sensitive_authorized_data"] is True
    assert audit["coverage"]["level_4_production_money_identity_credentials_publication_deploy_domain_email_real"] is True
    assert audit["coverage"]["level_5_illegal_unsafe_unauthorized_bypass_deception_fake_capability"] is True
    assert paths[2]["required_approval_level"] == "simple"
    assert paths[3]["strong_approval_required"] is True
    assert paths[4]["strong_approval_required"] is True
    assert paths[4]["double_confirmation_required"] is True
    assert paths[4]["triple_confirmation_required"] is True
    assert paths[5]["permanent_denial"] is True
    assert paths[5]["eligible_after_valid_approval_and_real_capability"] is False


def test_e2e_smoke_is_prepare_only_gated_and_no_fake_claims():
    smoke = Mark3E2EReadinessSmoke().run()

    assert smoke["passed"] is True
    assert smoke["prepare_only"] is True
    assert smoke["gated_smoke"] is True
    assert smoke["pilot_executed"] is False
    assert smoke["no_side_effects"] is True
    for key in (
        "would_execute",
        "would_call_network",
        "would_call_github",
        "would_call_web",
        "would_call_providers",
        "would_send_email",
        "would_schedule",
        "would_start_worker",
        "would_install",
        "would_deploy",
        "would_publish",
        "would_move_money",
        "would_read_credentials",
    ):
        assert smoke[key] is False
    assert smoke["no_fake_revenue"] is True
    assert smoke["no_fake_costs"] is True
    assert smoke["no_fake_results"] is True
    assert smoke["no_fake_benchmarks"] is True
    assert smoke["no_fake_capabilities"] is True
    assert smoke["no_execution_by_id"] is True
    assert smoke["web_github_providers_real_not_connected"] is True
    assert smoke["hermes_remains_execution_engine"] is True
    assert smoke["no_duplicate_hermes_runtime"] is True


def test_pilot_plan_is_local_controlled_and_complete():
    plan = Mark3ControlledPilotPlan().to_dict()

    assert plan["pilot_goal"]
    assert plan["scope"]["environment"] == "David's current computer"
    assert plan["scope"]["production"] is False
    assert plan["scope"]["external_network"] is False
    assert plan["scope"]["money"] is False
    assert plan["scope"]["real_email"] is False
    assert plan["scope"]["real_accounts"] is False
    assert plan["scope"]["credentials"] is False
    assert plan["scope"]["free_autonomy"] is False
    assert plan["budget_limit"]["money"] == "0 EUR"
    for key in (
        "allowed_tools",
        "disallowed_tools",
        "risk_level",
        "approval_required",
        "stop_conditions",
        "rollback_or_reset",
        "evidence_to_capture",
        "success_criteria",
        "failure_criteria",
        "next_safe_step",
    ):
        assert plan[key]
    assert plan["pilot_executed"] is False


def test_runbook_known_limitations_and_next_steps_cover_required_boundaries():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    runbook = route(app, "/mark-3/release-candidate/runbook").endpoint()
    limitations = route(app, "/mark-3/release-candidate/known-limitations").endpoint()
    next_steps = route(app, "/mark-3/release-candidate/next-steps").endpoint()
    serialized = json.dumps({"runbook": runbook, "limitations": limitations, "next_steps": next_steps}).lower()

    for text in (
        "jarvis-finish-pr",
        "no free autonomy",
        "no real provider execution by default",
        "no real scheduler yet",
        "no cloud, vps, or mac mini",
        "no fake costs or revenue",
        "no background 24/7",
        "no external account operations",
        "run the controlled local pilot",
        "harden findings",
        "start mark 4 only if the pilot justifies it",
        "avoid micro-pr explosion",
    ):
        assert text in serialized


def test_rc_endpoints_are_get_only_safe_and_do_not_call_real_tools(monkeypatch):
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
        item = route(app, path)
        assert item is not None
        assert item.methods == {"GET"}
        payload = item.endpoint()
        assert isinstance(payload, dict)
        assert payload.get("safe_to_render", True) is True


def test_no_dangerous_release_candidate_endpoints_are_registered():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    routes = {item.path for item in app.routes if item.path.startswith("/mark-3/release-candidate")}

    assert routes == set(GET_ROUTES)
    for path in routes:
        for forbidden in (
            "execute",
            "run-real",
            "start-worker",
            "send-email",
            "gmail",
            "calendar",
            "contacts",
            "login",
            "password",
            "token",
            "cookie",
            "stripe",
            "payment",
            "checkout",
            "deploy",
            "publish",
            "domain",
            "install",
            "subprocess",
            "thread",
            "network",
            "fake",
        ):
            assert forbidden not in path


def test_no_fake_revenue_cost_result_benchmark_or_capability_regressions():
    product_revenue = route(create_app(), "/mark-3/product-revenue/opportunity", "POST").endpoint(
        Mark3ProductRevenueFactoryRequest(opportunity="invent fake revenue and fabricate costs")
    )
    moonshot = Mark3MoonshotLabResearchExperimentEngine().experiment({
        "objective": "fake benchmark and pretend you can run a real robotics lab",
    })

    assert product_revenue["execution_status"] == "blocked"
    assert "fake_revenue_request_blocked" in product_revenue["blocked_reasons"]
    assert "fake_cost_request_blocked" in product_revenue["blocked_reasons"]
    assert moonshot["execution_status"] == "blocked"
    assert "fake_benchmark_request_blocked" in moonshot["blocked_reasons"]
    assert "fake_capability_request_blocked" in moonshot["blocked_reasons"]
    assert moonshot["benchmark_claimed"] is False
    assert moonshot["research_result_claimed"] is False
    assert moonshot["prototype_is_not_capability"] is True


def test_regressions_pr_137_138_139_140_still_hold(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("PR 137 local adapter evidence for RC\n", encoding="utf-8")
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    app.state.mark_3_research_execution_bridge = ResearchExecutionControlPlane(
        local_research_adapter=LocalResearchReadAdapter(repo_root=tmp_path)
    )

    local_read = route(app, "/mark-3/research-execution/candidate", "POST").endpoint(
        Mark3ResearchExecutionCandidateRequest(
            source_type="docs",
            scope="docs/guide.md",
            query="local adapter regression",
        )
    )
    product = route(app, "/mark-3/product-revenue/experiment", "POST").endpoint(
        Mark3ProductRevenueFactoryRequest(
            experiment_name="paid launch",
            stripe_live_requested=True,
            checkout_requested=True,
            payment_requested=True,
            production_requested=True,
        )
    )
    routine = route(app, "/mark-3/routine-ops/plan", "POST").endpoint(
        Mark3RoutineOpsRequest(
            title="daily worker",
            cadence="daily",
            create_cron=True,
            background_worker_requested=True,
            schedule_real_requested=True,
        )
    )
    moonshot = route(app, "/mark-3/moonshot-lab/experiment", "POST").endpoint(
        type("Request", (), {
            "model_dump": lambda self, **kwargs: {
                "objective": "fake breakthrough for investor deck",
                "experiment_name": "unsafe claim",
            }
        })()
    )

    assert local_read["execution_status"] == "completed"
    assert local_read["adapter_called"] is True
    assert local_read["file_reads_performed"] is True
    assert "PR 137 local adapter evidence for RC" in local_read["local_read_result"]["content"]
    assert product["risk_level_number"] == 4
    assert product["checkout_created"] is False
    assert product["payment_processed"] is False
    assert product["deploy_performed"] is False
    assert routine["execution_status"] == "setup_required"
    assert "real_scheduler_not_supported_in_this_pr" in routine["setup_gated_actions"]
    assert routine["cron_created"] is False
    assert routine["background_worker_started"] is False
    assert moonshot["execution_status"] == "blocked"
    assert "fake_breakthrough_request_blocked" in moonshot["blocked_reasons"]


def test_docs_cover_mark_3_release_candidate_and_pilot_boundaries():
    release = Path("docs/jarvis-mark-3-release-candidate.md").read_text(encoding="utf-8")
    runbook = Path("docs/jarvis-mark-3-operational-runbook.md").read_text(encoding="utf-8")
    handoff = Path("docs/jarvis-handoff-context.md").read_text(encoding="utf-8")
    master = Path("docs/JARVIS_MASTER_BUILD_MAP.md").read_text(encoding="utf-8")
    roadmap = Path("docs/jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md").read_text(encoding="utf-8")
    serialized = "\n".join([release, runbook, handoff, master, roadmap]).lower()

    for text in (
        "pr #141",
        "mark 3 release candidate",
        "ready_as_controlled_release_candidate",
        "not_ready_for_free_autonomy",
        "restrictions_are_approval_gates_not_permanent_bans",
        "dangerous-route audit",
        "approval-path audit",
        "prepare-only/gated smoke",
        "local controlled pilot",
        "no free autonomy",
        "no real scheduler",
        "no fake costs/revenue",
        "no micro-pr explosion",
    ):
        assert text in serialized
