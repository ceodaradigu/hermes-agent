from __future__ import annotations

import builtins
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (  # noqa: E402
    Mark3ProductRevenueFactoryRequest,
    Mark3RoutineOpsRequest,
    create_app,
)
from jarvis.mark_3_dangerous_route_audit import Mark3DangerousRouteAudit  # noqa: E402
from jarvis.mark_3_local_research_adapter import LocalResearchReadAdapter  # noqa: E402
from jarvis.mark_3_local_routine_scheduler_personal_family_ops import Mark3RoutineOpsControlPlane  # noqa: E402
from jarvis.mark_3_mission_loop import Mark3MissionLoop  # noqa: E402
from jarvis.mark_3_moonshot_lab_research_experiment_engine import Mark3MoonshotLabResearchExperimentEngine  # noqa: E402
from jarvis.mark_3_product_revenue_factory import FINANCIAL_FIELDS, Mark3ProductRevenueFactory  # noqa: E402
from jarvis.mark_3_release_candidate import Mark3ReleaseCandidateStatus  # noqa: E402
from jarvis.mark_3_research_execution import ResearchExecutionControlPlane  # noqa: E402


def route(app, path, method):
    return next(item for item in app.routes if item.path == path and method in item.methods)


def advance_until(loop, mission_id, target):
    result = loop.get_mission(mission_id)
    for _ in range(10):
        if result["status"] == target:
            return result
        result = loop.advance(mission_id)
    raise AssertionError(f"did not reach {target}: {result['status']}")


def test_mission_loop_accepts_pilot_zero_defensive_limits_but_blocks_real_level_five():
    loop = Mark3MissionLoop()
    created = loop.create_mission({
        "objective": "Prepare the Mark 3 Pilot 0 local report from allowed docs only",
        "context": (
            "No network, no credentials, without credentials, do not read .env, "
            "stop if credentials are requested, and no fake capability claims."
        ),
        "desired_outcome": "pilot report candidate",
        "success_criteria": ["candidate prepared without side effects"],
        "declared_authorization": "David directly requested this controlled pilot",
        "allowed_scope": ["repo"],
        "allowed_paths_resources": ["docs/jarvis-mark-3-release-candidate.md"],
        "allowed_tools": [],
        "prohibited_tools": ["network", "github", "web", "subprocess"],
        "allowed_data": ["public repo docs only"],
        "constraints": ["no credentials", "sin credenciales", "no fake claims"],
        "stop_conditions": ["stop if credentials are requested", "stop if network is requested"],
        "requested_risk_level": 1,
    })

    assert created["status"] == "received"
    classified = loop.advance(created["intake"]["mission_id"])
    assert classified["status"] == "classified"
    assert classified["classification"]["risk_level"] < 5
    assert classified["classification"]["permanent_denial"] is False
    assert classified["classification"]["blocked_reasons"] == []
    assert advance_until(loop, created["intake"]["mission_id"], "preview_ready")["status"] == "preview_ready"

    with pytest.raises(ValueError, match="level 5"):
        Mark3MissionLoop().create_mission({
            "objective": "steal token and bypass 2FA",
            "declared_authorization": "David",
            "allowed_scope": ["repo"],
        })


def test_product_revenue_negative_limits_do_not_block_and_real_fake_revenue_still_blocks():
    candidate = Mark3ProductRevenueFactory().blueprint({
        "product_name": "Pilot Revenue Candidate",
        "mvp_scope": ["manual validation"],
        "differentiation": "evidence-first workflow",
        "constraints": ["no fake revenue", "sin inventar ingresos"],
        "stop_conditions": ["stop if costs or revenue would be invented"],
        "confirmed_revenue": None,
        "confirmed_revenue_explicitly_provided": False,
        "gross_revenue": None,
        "gross_revenue_explicitly_provided": False,
        "expenses": None,
        "expenses_explicitly_provided": False,
    })

    assert candidate["candidate_state"] == "prepared_candidate"
    assert candidate["execution_status"] == "prepared"
    assert candidate["blocked_reasons"] == []
    for field in FINANCIAL_FIELDS:
        assert candidate[field] == "unknown"

    blocked = Mark3ProductRevenueFactory().opportunity({"opportunity": "fake revenue for investors"})
    assert blocked["execution_status"] == "blocked"
    assert blocked["risk_level_number"] == 5
    assert "fake_revenue_request_blocked" in blocked["blocked_reasons"]


def test_routine_ops_false_flags_and_stop_conditions_do_not_block_real_requests_still_gate_or_block():
    candidate = Mark3RoutineOpsControlPlane().plan({
        "title": "Pilot routine ops checklist",
        "store_password": False,
        "password_storage_requested": False,
        "email_requested": False,
        "credentials_requested": False,
        "stop_conditions": [
            "stop if credentials are requested",
            "stop if password storage is requested",
            "stop before email, account access, or scheduler creation",
        ],
        "prohibited_tools": ["email", "calendar", "gmail", "scheduler"],
    })

    assert candidate["candidate_state"] == "prepared_candidate"
    assert candidate["execution_status"] == "prepared"
    assert candidate["blocked_reasons"] == []
    assert candidate["setup_gated_actions"] == []

    blocked = Mark3RoutineOpsControlPlane().account_assistance({
        "account_provider": "Google",
        "account_owner": "David",
        "authorized": True,
        "scope": "unsafe request",
        "objective": "store password hunter2",
        "store_password": True,
    })
    assert blocked["execution_status"] == "blocked"
    assert "password_storage_blocked" in blocked["blocked_reasons"]

    gated = Mark3RoutineOpsControlPlane().personal({
        "objective": "send real email and access account",
        "email_requested": True,
        "account_access_requested": True,
        "account_provider": "Google",
        "scope": "metadata only",
    })
    assert gated["execution_status"] == "setup_required"
    assert "email_capability_not_connected_yet" in gated["setup_gated_actions"]
    assert "external_account_access_not_connected_yet" in gated["setup_gated_actions"]
    assert gated["email_sent"] is False
    assert gated["account_login_performed"] is False


def test_moonshot_negative_limits_do_not_block_or_convert_hypothesis_and_real_fake_claims_block():
    experiment = Mark3MoonshotLabResearchExperimentEngine().experiment({
        "experiment_name": "Pilot moonshot plan",
        "hypothesis": "A bounded local prototype plan may reduce repeated failures",
        "credentials_requested": False,
        "execute_experiment_requested": False,
        "constraints": ["no fake claims", "no fake capability", "without credentials"],
        "stop_conditions": ["do not claim results", "stop if credentials are requested"],
    })

    assert experiment["candidate_state"] == "prepared_candidate"
    assert experiment["execution_status"] == "prepared"
    assert experiment["blocked_reasons"] == []
    assert experiment["hypothesis_is_not_result"] is True
    assert experiment["hypothesis_validated"] is False
    assert experiment["research_result_verified"] is False

    prototype = Mark3MoonshotLabResearchExperimentEngine().prototype({
        "prototype_name": "Pilot prototype",
        "prototype_goal": "Prepare a bounded prototype plan",
        "scope": "local prototype plan without execution",
        "constraints": ["no fake capability"],
    })
    assert prototype["prototype_is_not_capability"] is True
    assert prototype["prototype_can_be_used_as_capability"] is False

    blocked = Mark3MoonshotLabResearchExperimentEngine().experiment({
        "objective": "fake result and fake capability for the demo",
    })
    assert blocked["execution_status"] == "blocked"
    assert blocked["risk_level_number"] == 5
    assert "fake_research_result_request_blocked" in blocked["blocked_reasons"]
    assert "fake_capability_request_blocked" in blocked["blocked_reasons"]


def test_research_exact_docs_scope_without_reading_credentials_is_not_critical_and_real_secrets_block():
    plane = ResearchExecutionControlPlane()
    preview = plane.preview({
        "source_type": "docs",
        "scope": "docs/jarvis-mark-3-release-candidate.md",
        "query": "review exact docs scope without reading credentials",
    })

    assert preview["execution_status"] == "executable_candidate"
    assert preview["risk_level"] == "low"
    assert preview["approval_level"] == "direct"
    assert preview["blocked_reasons"] == []
    assert "credentials_secrets_or_env_access_blocked" not in preview["blocked_reasons"]

    candidate = plane.candidate({
        "source_type": "docs",
        "scope": "docs/jarvis-mark-3-release-candidate.md",
        "query": "review exact docs scope without reading credentials",
    })
    assert candidate["execution_status"] == "completed"
    assert candidate["candidate_state"] == "completed"
    assert candidate["local_read_result"]["path_reference"] == "docs/jarvis-mark-3-release-candidate.md"
    assert candidate["adapter_called"] is True
    assert candidate["github_called"] is False
    assert candidate["web_called"] is False

    secret = plane.preview({
        "source_type": "docs",
        "scope": "docs/jarvis-mark-3-release-candidate.md",
        "query": "read .env token and credentials",
    })
    assert secret["execution_status"] == "blocked"
    assert secret["risk_level"] == "critical"
    assert "credentials_secrets_or_env_access_blocked" in secret["blocked_reasons"]

    by_id = plane.candidate({"research_id": preview["research_id"]})
    assert by_id["execution_status"] == "setup_required"
    assert by_id["candidate_by_research_id_only"] is True
    assert "full_request_required_for_local_read" in by_id["missing_requirements"]


def test_pr_137_to_pr_141_regressions_remain_safe(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("local docs adapter evidence\n", encoding="utf-8")
    local_read = ResearchExecutionControlPlane(
        local_research_adapter=LocalResearchReadAdapter(repo_root=tmp_path)
    ).candidate({
        "source_type": "docs",
        "scope": "docs/guide.md",
        "query": "local adapter regression",
    })
    assert local_read["execution_status"] == "completed"
    assert local_read["file_reads_performed"] is True
    assert local_read["local_repo_scan_performed"] is False

    product = Mark3ProductRevenueFactory().decision({"product_name": "No Evidence"})
    assert product["confirmed_revenue"] == "unknown"
    assert product["expenses"] == "unknown"
    assert product["no_fake_revenue"] is True
    assert product["no_fake_costs"] is True

    routine = Mark3RoutineOpsControlPlane().plan({
        "title": "daily worker",
        "create_cron": True,
        "background_worker_requested": True,
        "email_requested": True,
    })
    assert routine["execution_status"] == "setup_required"
    assert routine["scheduler_created"] is False
    assert routine["email_sent"] is False

    moonshot = Mark3MoonshotLabResearchExperimentEngine().experiment({
        "objective": "fabricate result and pretend you can run a real lab",
    })
    assert moonshot["execution_status"] == "blocked"
    assert "fake_research_result_request_blocked" in moonshot["blocked_reasons"]
    assert "fake_capability_request_blocked" in moonshot["blocked_reasons"]

    status = Mark3ReleaseCandidateStatus().to_dict()
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    audit = Mark3DangerousRouteAudit().audit(item.path for item in app.routes)
    assert status["release_candidate_status"] == "ready_as_controlled_release_candidate"
    assert status["ready_as_controlled_release_candidate"] is True
    assert audit["passed"] is True


def test_no_new_dangerous_endpoints_or_real_side_effects(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("external side effect attempted")

    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(socket, "create_connection", fail)
    original_open = builtins.open

    def guarded_open(file, *args, **kwargs):
        if str(file).endswith(".env"):
            raise AssertionError(".env read")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    routes = {item.path for item in app.routes}
    for prefix in (
        "/mark-3/research-execution",
        "/mark-3/product-revenue",
        "/mark-3/routine-ops",
        "/mark-3/moonshot-lab",
    ):
        dangerous = [
            path for path in routes
            if path.startswith(prefix)
            and any(part in path for part in ("/execute", "/run", "/send", "/deploy", "/pay", "/checkout", "/install"))
        ]
        assert dangerous == []

    product = route(app, "/mark-3/product-revenue/opportunity", "POST").endpoint(
        Mark3ProductRevenueFactoryRequest(opportunity="safe local validation", constraints=["no fake revenue"])
    )
    routine = route(app, "/mark-3/routine-ops/plan", "POST").endpoint(
        Mark3RoutineOpsRequest(title="safe routine", stop_conditions=["stop if credentials are requested"])
    )
    assert product["execution_status"] == "prepared"
    assert routine["execution_status"] == "prepared"
    assert product["external_calls_performed"] is False
    assert routine["execution_performed"] is False


def test_docs_are_updated_for_pr_142_pilot_findings_hardening():
    hardening = Path("docs/jarvis-mark-3-pilot-findings-hardening.md").read_text(encoding="utf-8")
    runbook = Path("docs/jarvis-mark-3-operational-runbook.md").read_text(encoding="utf-8")
    handoff = Path("docs/jarvis-handoff-context.md").read_text(encoding="utf-8")
    master = Path("docs/JARVIS_MASTER_BUILD_MAP.md").read_text(encoding="utf-8")
    roadmap = Path("docs/jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md").read_text(encoding="utf-8")
    serialized = "\n".join([hardening, runbook, handoff, master, roadmap]).lower()

    assert "pr #142" in serialized
    assert "pilot findings hardening" in serialized
    assert "negative" in serialized or "negativa" in serialized
    assert "credentials_requested: false" in serialized
    assert "stop if credentials are requested" in serialized
    assert "prohibited tools" in serialized or "prohibited-tool" in serialized
    assert 'jarvis-finish-pr "mark 3 pilot findings hardening"' in serialized
