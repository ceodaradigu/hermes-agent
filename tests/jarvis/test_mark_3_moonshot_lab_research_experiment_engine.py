from __future__ import annotations

import builtins
import inspect
import json
from pathlib import Path
import socket
import subprocess

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (  # noqa: E402
    Mark3MoonshotLabRequest,
    Mark3ProductRevenueFactoryRequest,
    Mark3ResearchExecutionCandidateRequest,
    Mark3RoutineOpsRequest,
    create_app,
)
from jarvis.mark_3_local_research_adapter import LocalResearchReadAdapter  # noqa: E402
from jarvis.mark_3_moonshot_lab_research_experiment_engine import (  # noqa: E402
    INVARIANTS,
    MOONSHOT_LAB_ENDPOINTS,
    REQUIRED_CANDIDATE_FIELDS,
    Mark3MoonshotLabResearchExperimentEngine,
)
from jarvis.mark_3_research_execution import ResearchExecutionControlPlane  # noqa: E402


def route(app, path, method):
    return next(item for item in app.routes if item.path == path and method in item.methods)


def _request(**values):
    return Mark3MoonshotLabRequest(**values)


def _all_side_effects_disabled(payload):
    for key in (
        "would_execute",
        "would_call_network",
        "would_install_dependencies",
        "would_use_provider",
        "would_publish",
        "would_deploy",
        "would_move_money",
        "execution_performed",
        "experiment_executed",
        "prototype_built",
        "network_called",
        "web_called",
        "github_called",
        "provider_called",
        "dependencies_installed",
        "external_process_started",
        "background_worker_started",
        "publication_performed",
        "deploy_performed",
        "payment_processed",
        "money_moved",
        "credentials_used",
        "benchmark_claimed",
        "research_result_claimed",
        "breakthrough_claimed",
        "hermes_called",
        "approval_gateway_called",
    ):
        assert payload[key] is False


def _required_fields_present(candidate):
    for key in REQUIRED_CANDIDATE_FIELDS:
        assert key in candidate


def test_status_is_safe_prepare_only_and_lists_required_endpoints():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    status = route(app, "/mark-3/moonshot-lab/status", "GET").endpoint()

    assert status["available"] is True
    assert status["prepare_only"] is True
    assert status["control_plane_only"] is True
    assert status["safe_to_render"] is True
    assert status["endpoints"] == list(MOONSHOT_LAB_ENDPOINTS)
    assert status["required_candidate_fields"] == list(REQUIRED_CANDIDATE_FIELDS)
    assert status["real_experiment_execution_connected"] is False
    assert status["external_research_connected"] is False
    assert status["github_connected"] is False
    assert status["web_connected"] is False
    assert status["provider_connected"] is False
    assert status["dependency_install_connected"] is False
    assert status["publication_connected"] is False
    assert status["deploy_connected"] is False
    assert status["money_movement_connected"] is False
    for invariant in INVARIANTS:
        assert status[invariant] is True
        assert status["invariants"][invariant] is True
    _all_side_effects_disabled(status)


def test_moonshot_intake_candidate_has_required_contract_without_side_effects():
    candidate = Mark3MoonshotLabResearchExperimentEngine(id_factory=lambda: "moonshot-fixed").intake({
        "moonshot_type": "deep simulation",
        "objective": "Explore whether local simulations can reduce failed product experiments",
        "hypothesis": "A bounded simulator may improve experiment selection before build work",
        "scope": "conceptual intake only",
    })

    _required_fields_present(candidate)
    assert candidate["candidate_id"] == "moonshot-fixed"
    assert candidate["candidate_type"] == "moonshot_intake"
    assert candidate["candidate_state"] == "prepared_candidate"
    assert candidate["risk_level_number"] == 1
    assert candidate["approval_required"] is False
    assert candidate["required_approval_level"] == "direct"
    assert candidate["evidence_score"] == 0
    assert candidate["uncertainty_level"] == "extreme"
    assert candidate["stage_gate"]["gate"] == "gate_0_intake_review"
    assert candidate["moonshot_intake"]["would_start_research"] is False
    _all_side_effects_disabled(candidate)


def test_hypothesis_is_not_treated_as_result():
    candidate = Mark3MoonshotLabResearchExperimentEngine().hypothesis({
        "moonshot_type": "research",
        "hypothesis": "If retrieval uses failure memory, repeated diagnostic loops should drop",
        "null_hypothesis": "Failure memory does not reduce repeated diagnostics",
    })

    _required_fields_present(candidate)
    assert candidate["hypothesis"] == "If retrieval uses failure memory, repeated diagnostic loops should drop"
    assert candidate["hypothesis_is_not_result"] is True
    assert candidate["hypothesis_validated"] is False
    assert candidate["research_result_verified"] is False
    assert candidate["hypothesis_frame"]["hypothesis_is_result"] is False
    assert candidate["hypothesis_frame"]["result_claim_made"] is False
    assert candidate["no_fake_research_result"] is True


def test_prototype_candidate_is_not_real_capability():
    candidate = Mark3MoonshotLabResearchExperimentEngine().prototype({
        "prototype_name": "Local simulator preview",
        "prototype_goal": "Prepare a bounded prototype plan",
        "scope": "local scoped prototype plan without execution",
    })

    _required_fields_present(candidate)
    assert candidate["candidate_type"] == "prototype_candidate"
    assert candidate["risk_level_number"] == 2
    assert candidate["required_approval_level"] == "simple"
    assert candidate["prototype_is_not_capability"] is True
    assert candidate["prototype_can_be_used_as_capability"] is False
    assert candidate["prototype_candidate"]["prototype_is_capability"] is False
    assert candidate["prototype_candidate"]["operational_capability_available"] is False
    assert candidate["prototype_built"] is False
    _all_side_effects_disabled(candidate)


def test_local_repo_or_docs_research_without_exact_scope_returns_setup_required():
    candidate = Mark3MoonshotLabResearchExperimentEngine().experiment({
        "source_type": "local_repo",
        "hypothesis": "Local repo evidence may clarify feasibility",
    })

    assert candidate["risk_level_number"] == 2
    assert candidate["required_approval_level"] == "simple"
    assert candidate["candidate_state"] == "setup_required"
    assert candidate["execution_status"] == "setup_required"
    assert candidate["capability_status"] == "setup_required"
    assert "local_research_exact_scope_required" in candidate["setup_gated_actions"]
    assert candidate["stage_gate"]["status"] == "setup_required"
    _all_side_effects_disabled(candidate)


def test_evidence_score_uncertainty_labels_and_no_result_claim():
    candidate = Mark3MoonshotLabResearchExperimentEngine().experiment({
        "experiment_name": "Failure-memory simulation plan",
        "hypothesis": "Failure memory may reduce repeated diagnostics",
        "evidence": ["two prior repeated failures", "one verified local fixture"],
        "evidence_state": "verified",
        "observed_metrics": {"repeat_count": 2},
        "observed_metrics_explicitly_provided": True,
    })

    assert candidate["evidence_score"] == 75
    assert candidate["evidence_score_label"] == "strong_candidate_evidence"
    assert candidate["uncertainty_level"] == "medium"
    assert "hypothesis_not_result" in candidate["uncertainty_labels"]
    assert "prototype_not_capability" in candidate["uncertainty_labels"]
    assert candidate["evidence_score_is_result"] is False
    assert candidate["research_result_claimed"] is False
    assert candidate["benchmark_claimed"] is False


def test_reproducibility_checklist_stage_gate_and_stop_conditions_are_present():
    candidate = Mark3MoonshotLabResearchExperimentEngine().experiment({
        "experiment_name": "Reproducibility candidate",
        "hypothesis": "A bounded protocol may be reproducible",
        "scope": "plan only",
        "budget_limit": "0 EUR",
    })

    assert candidate["reproducibility_checklist"]
    assert "hypothesis is written separately from results" in candidate["reproducibility_checklist"]
    assert candidate["stage_gate"]["gate"] == "gate_2_experiment_plan_review"
    assert candidate["stage_gate"]["passes_to_execution"] is False
    assert any("stop before any real execution" in item for item in candidate["stop_conditions"])
    assert candidate["experiment_budget_preview"]["would_spend_money"] is False


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ({"objective": "fake breakthrough for this deck"}, "fake_breakthrough_request_blocked"),
        ({"objective": "invent benchmark numbers"}, "fake_benchmark_request_blocked"),
        ({"objective": "fabricate result for the paper"}, "fake_research_result_request_blocked"),
        ({"objective": "invent cost evidence"}, "fake_cost_request_blocked"),
        ({"objective": "fake revenue for investors"}, "fake_revenue_request_blocked"),
        ({"objective": "pretend you can run a real robotics lab"}, "fake_capability_request_blocked"),
    ],
)
def test_no_fake_breakthrough_benchmark_result_cost_revenue_or_capability(payload, reason):
    candidate = Mark3MoonshotLabResearchExperimentEngine().experiment(payload)

    assert candidate["execution_status"] == "blocked"
    assert candidate["risk_level_number"] == 5
    assert candidate["required_approval_level"] == "level_5_denied"
    assert candidate["permanent_denial"] is True
    assert reason in candidate["blocked_reasons"]
    assert candidate["stage_gate"]["gate"] == "gate_5_permanent_denial"
    _all_side_effects_disabled(candidate)


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ({"objective": "illegal experiment plan"}, "illegal_request_blocked"),
        ({"objective": "harm a service with unsafe malware"}, "unsafe_or_harmful_request_blocked"),
        ({"objective": "unauthorized access to a third-party account"}, "unauthorized_request_blocked"),
        ({"objective": "bypass provider controls"}, "bypass_or_evasion_request_blocked"),
        ({"objective": "deceive reviewers with phishing"}, "deception_request_blocked"),
    ],
)
def test_blocks_illegal_unsafe_unauthorized_bypass_harm_or_deception(payload, reason):
    candidate = Mark3MoonshotLabResearchExperimentEngine().intake(payload)

    assert candidate["execution_status"] == "blocked"
    assert candidate["risk_level"] == "denied"
    assert candidate["risk_level_number"] == 5
    assert reason in candidate["blocked_reasons"]
    assert candidate["permanent_denial"] is True
    assert candidate["legal_safety_review"]["permanent_denial"] is True


def test_level_4_for_publication_production_money_identity_and_credentials():
    candidate = Mark3MoonshotLabResearchExperimentEngine().experiment({
        "experiment_name": "critical future action",
        "hypothesis": "A launch may validate demand",
        "publish_requested": True,
        "production_requested": True,
        "deploy_requested": True,
        "money_movement_requested": True,
        "identity_requested": True,
        "credentials_requested": True,
        "api_key": "abc123-sensitive",
    })
    serialized = json.dumps(candidate).lower()

    assert candidate["candidate_state"] == "setup_required"
    assert candidate["execution_status"] == "setup_required_for_level_4_capability"
    assert candidate["capability_status"] == "capability_not_connected_yet"
    assert candidate["risk_level_number"] == 4
    assert candidate["required_approval_level"] == "level_4_strong_double_or_triple"
    assert candidate["approval_required"] is True
    assert candidate["approval_requirements"]["approval_grants_execution"] is False
    assert {"publication", "production", "live_deploy", "money_movement", "identity", "credentials"} <= set(candidate["critical_requested_actions"])
    assert "abc123-sensitive" not in serialized
    _all_side_effects_disabled(candidate)


def test_external_network_github_provider_install_and_process_requests_do_not_execute(monkeypatch):
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
    candidate = route(app, "/mark-3/moonshot-lab/experiment", "POST").endpoint(
        _request(
            experiment_name="external setup candidate",
            hypothesis="External evidence may help",
            network_requested=True,
            web_requested=True,
            github_requested=True,
            provider_requested=True,
            ai_cli_requested=True,
            install_requested=True,
            execute_experiment_requested=True,
            subprocess_requested=True,
            thread_requested=True,
        )
    )
    module_source = inspect.getsource(__import__("jarvis.mark_3_moonshot_lab_research_experiment_engine", fromlist=["x"])).lower()

    assert candidate["execution_status"] == "setup_required"
    assert candidate["capability_status"] == "capability_not_connected_yet"
    assert {
        "network_capability_not_connected_yet",
        "web_capability_not_connected_yet",
        "github_capability_not_connected_yet",
        "provider_capability_not_connected_yet",
        "ai_cli_capability_not_connected_yet",
        "dependency_install_not_connected_yet",
        "real_experiment_execution_not_connected_yet",
        "parallel_worker_not_connected_yet",
        "local_process_not_connected_yet",
    } <= set(candidate["setup_gated_actions"])
    _all_side_effects_disabled(candidate)
    assert "import requests" not in module_source
    assert "subprocess" not in module_source
    assert "threading" not in module_source
    assert "socket" not in module_source


def test_moonshot_lab_api_has_no_dangerous_action_endpoints():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    routes = {item.path for item in app.routes if item.path.startswith("/mark-3/moonshot-lab")}

    assert routes == {
        "/mark-3/moonshot-lab/status",
        "/mark-3/moonshot-lab/intake",
        "/mark-3/moonshot-lab/hypothesis",
        "/mark-3/moonshot-lab/experiment",
        "/mark-3/moonshot-lab/prototype",
        "/mark-3/moonshot-lab/decision",
    }
    for path in routes:
        for forbidden in ("execute", "run", "install", "publish", "deploy", "pay", "send"):
            assert forbidden not in path


def test_decision_returns_kill_continue_iterate_without_claiming_results():
    plane = Mark3MoonshotLabResearchExperimentEngine()
    hold = plane.decision({"hypothesis": "unknown"})
    iterate = plane.decision({
        "hypothesis": "some evidence",
        "evidence": ["reported signal", "second reported signal"],
        "evidence_state": "reported",
    })
    continue_candidate = plane.decision({
        "hypothesis": "verified evidence",
        "evidence": ["one", "two", "three"],
        "evidence_state": "verified",
        "observed_metrics": {"delta": "positive"},
        "observed_metrics_explicitly_provided": True,
    })
    killed = plane.decision({"hypothesis": "stop", "stop_conditions_met": True})

    assert hold["decision"]["recommendation"] == "hold_for_evidence"
    assert iterate["decision"]["recommendation"] == "iterate"
    assert continue_candidate["decision"]["recommendation"] == "continue_with_review"
    assert killed["decision"]["recommendation"] == "kill"
    assert continue_candidate["decision"]["approval_grants_execution"] is False
    assert continue_candidate["research_result_claimed"] is False


def test_docs_and_handoff_are_updated_for_pr_140_moonshot_lab():
    moonshot_doc = Path("docs/jarvis-mark-3-moonshot-lab-research-experiment-engine.md").read_text(encoding="utf-8")
    master = Path("docs/JARVIS_MASTER_BUILD_MAP.md").read_text(encoding="utf-8")
    roadmap = Path("docs/jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md").read_text(encoding="utf-8")
    handoff = Path("docs/jarvis-handoff-context.md").read_text(encoding="utf-8")
    serialized = "\n".join([moonshot_doc, master, roadmap, handoff]).lower()

    assert "pr #140" in serialized
    assert "moonshot lab" in serialized
    assert "research/experiment engine" in serialized
    assert "candidate_is_not_execution" in serialized
    assert "hypothesis_is_not_result" in serialized
    assert "prototype_is_not_capability" in serialized
    assert "no fake breakthrough" in serialized
    assert "no fake benchmark" in serialized
    assert "no network" in serialized
    assert "no external provider" in serialized


def test_pr_137_local_research_adapter_regression_still_reads_exact_allowed_file(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("PR 137 exact local evidence for PR 140\n", encoding="utf-8")
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    app.state.mark_3_research_execution_bridge = ResearchExecutionControlPlane(
        local_research_adapter=LocalResearchReadAdapter(repo_root=tmp_path)
    )

    result = route(app, "/mark-3/research-execution/candidate", "POST").endpoint(
        Mark3ResearchExecutionCandidateRequest(
            source_type="docs",
            scope="docs/guide.md",
            query="local adapter regression",
        )
    )

    assert result["execution_status"] == "completed"
    assert result["adapter_called"] is True
    assert result["file_reads_performed"] is True
    assert result["local_repo_scan_performed"] is False
    assert "PR 137 exact local evidence for PR 140" in result["local_read_result"]["content"]


def test_pr_138_product_revenue_factory_regression_still_prepare_only():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    candidate = route(app, "/mark-3/product-revenue/experiment", "POST").endpoint(
        Mark3ProductRevenueFactoryRequest(
            experiment_name="paid launch",
            stripe_live_requested=True,
            checkout_requested=True,
            payment_requested=True,
            production_requested=True,
        )
    )

    assert candidate["risk_level_number"] == 4
    assert candidate["required_approval_level"] == "level_4_strong_double_or_triple"
    assert candidate["checkout_created"] is False
    assert candidate["payment_processed"] is False
    assert candidate["deploy_performed"] is False
    assert candidate["candidate_is_not_payment"] is True


def test_pr_139_routine_ops_regression_still_prepare_only():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    candidate = route(app, "/mark-3/routine-ops/plan", "POST").endpoint(
        Mark3RoutineOpsRequest(
            title="daily worker",
            cadence="daily",
            create_cron=True,
            background_worker_requested=True,
            schedule_real_requested=True,
        )
    )

    assert candidate["execution_status"] == "setup_required"
    assert "real_scheduler_not_supported_in_this_pr" in candidate["setup_gated_actions"]
    assert candidate["schedule_preview"]["would_create_cron"] is False
    assert candidate["cron_created"] is False
    assert candidate["background_worker_started"] is False
