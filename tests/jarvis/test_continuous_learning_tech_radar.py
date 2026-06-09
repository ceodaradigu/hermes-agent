import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import ContinuousLearningPreviewRequest, create_app
from jarvis.continuous_learning.foundation import (
    ApprovalWorkflowPreview,
    ContinuousLearningStatus,
    LearningBacklogPreview,
    LearningProposalPreview,
    PRPlannerPreview,
    ProposalImpactAnalysis,
    ProposalRiskAnalysis,
    TechRadarDecisionPreview,
    TechRadarSafetyPolicy,
    TechnologyCandidateProfile,
)
from jarvis.operator_console import OperatorConsoleCapabilityMatrix, OperatorConsoleSnapshot


POST_ROUTES = (
    "/continuous-learning/candidate-profile",
    "/continuous-learning/relevance-filter",
    "/continuous-learning/contrarian-review",
    "/continuous-learning/proposal-preview",
    "/continuous-learning/impact-analysis",
    "/continuous-learning/risk-analysis",
    "/continuous-learning/pr-planner",
    "/continuous-learning/approval-workflow",
    "/continuous-learning/backlog-preview",
    "/continuous-learning/decision-preview",
)

DANGEROUS_ROUTES = (
    "/continuous-learning/install",
    "/continuous-learning/update",
    "/continuous-learning/deploy",
    "/continuous-learning/modify-runtime",
    "/continuous-learning/modify-prompts",
    "/continuous-learning/create-pr",
    "/continuous-learning/clone",
    "/continuous-learning/research-external",
    "/continuous-learning/run",
)

STATUS_FALSE_FIELDS = (
    "continuous_learning_available",
    "tech_radar_available",
    "external_research_enabled",
    "auto_update_enabled",
    "auto_install_enabled",
    "auto_deploy_enabled",
    "runtime_modification_enabled",
    "prompt_modification_enabled",
    "dependency_modification_enabled",
    "pr_creation_enabled",
    "external_calls_enabled",
    "secrets_access_enabled",
    "hermes_called",
    "approval_gateway_called",
    "execution_enabled",
    "persistence_enabled",
)


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Continuous Learning")


def _app():
    return create_app(adapter_factory=FailAdapter)


def _endpoint(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def _get(app, path):
    return _endpoint(app, path, "GET")()


def _post(app, path, data):
    return _endpoint(app, path, "POST")(ContinuousLearningPreviewRequest(**data))


def test_status_endpoint_is_http_200_prepare_only_and_fully_disabled():
    app = _app()
    route = next(route for route in app.routes if route.path == "/continuous-learning/status")
    payload = route.endpoint()

    assert route.status_code in (None, 200)
    assert payload["prepare_only"] is True
    for field in STATUS_FALSE_FIELDS:
        assert payload[field] is False


def test_policy_endpoint_is_default_deny_and_requires_strong_approval():
    payload = _get(_app(), "/continuous-learning/policy")

    assert payload["prepare_only"] is True
    assert all(payload.values())
    for field in (
        "strong_approval_required_for_install",
        "strong_approval_required_for_runtime_changes",
        "strong_approval_required_for_prompt_changes",
        "strong_approval_required_for_production",
        "strong_approval_required_for_credentials",
    ):
        assert payload[field] is True


def test_candidate_profile_uses_only_provided_data_and_never_looks_up_or_installs():
    payload = _post(
        _app(),
        "/continuous-learning/candidate-profile",
        {"candidate_name": "Example", "source_reference": "provided note", "maturity": "experimental"},
    )

    assert payload["candidate_name"] == "Example"
    assert payload["maturity"] == "experimental"
    assert payload["no_external_lookup"] is True
    assert payload["would_install"] is False
    assert payload["would_modify_runtime"] is False
    assert payload["would_create_pr"] is False


def test_relevance_filter_preserves_unknowns_without_inventing_metrics():
    payload = _post(
        _app(),
        "/continuous-learning/relevance-filter",
        {"candidate_name": "Example", "unknowns": ["Measured time saving"], "time_saving_relevance": "unknown"},
    )

    assert payload["relevance_score"] == "unknown"
    assert payload["time_saving_relevance"] == "unknown"
    assert payload["unknowns"] == ["Measured time saving"]
    assert payload["no_decision_final"] is True


def test_contrarian_review_is_skeptical_and_no_hype():
    payload = _post(_app(), "/continuous-learning/contrarian-review", {"candidate_name": "Example"})

    assert payload["no_hype_mode"] is True
    assert payload["skeptical_questions"]
    assert "disprove" in payload["skeptical_questions"][0].lower()


def test_proposal_preview_contains_complete_review_contract_and_has_no_side_effects():
    payload = _post(
        _app(),
        "/continuous-learning/proposal-preview",
        {
            "candidate_name": "Example",
            "expected_impact": ["Reduce manual review time"],
            "risks": ["Dependency risk unknown"],
            "dependencies": ["example-package"],
            "tests_required": ["Unit tests"],
            "rollback_plan": ["Revert reviewed change"],
            "decision_recommendation": "investigate",
        },
    )

    for field in ("expected_impact", "risks", "dependencies", "tests_required", "rollback_plan"):
        assert payload[field]
    assert payload["decision_recommendation"] == "investigate"
    assert payload["would_create_pr"] is False
    assert payload["would_modify_code"] is False
    assert payload["approval_required"] is True


def test_proposal_and_approval_workflow_require_strong_approval_for_sensitive_change_classes():
    for risk in (
        "install_requested",
        "runtime_requested",
        "prompt_requested",
        "production_requested",
        "credentials_requested",
        "deploy_requested",
    ):
        proposal = _post(_app(), "/continuous-learning/proposal-preview", {risk: True})
        workflow = _post(_app(), "/continuous-learning/approval-workflow", {risk: True})
        assert proposal["strong_approval_required"] is True
        assert workflow["strong_approval_required"] is True
        assert workflow["approval_gateway_called"] is False
        assert workflow["approval_created"] is False


def test_impact_analysis_never_invents_confirmed_roi():
    payload = _post(
        _app(),
        "/continuous-learning/impact-analysis",
        {"impact_categories": {"time_saved": "unknown", "revenue_enablement": "hypothesis only"}},
    )

    assert payload["no_fake_metrics"] is True
    assert payload["unknowns_preserved"] is True
    assert payload["no_confirmed_roi"] is True
    assert payload["confirmed_roi"] == "unknown"


def test_impact_analysis_accepts_confirmed_roi_only_when_explicitly_provided():
    payload = _post(
        _app(),
        "/continuous-learning/impact-analysis",
        {"confirmed_roi": "Measured in reviewed source", "confirmed_roi_explicitly_provided": True},
    )

    assert payload["no_confirmed_roi"] is False
    assert payload["confirmed_roi"] == "Measured in reviewed source"


@pytest.mark.parametrize("risk_field", ["secret_risk", "production_risk", "runtime_risk", "dependency_risk"])
def test_risk_analysis_blocks_unresolved_sensitive_or_change_risk(risk_field):
    payload = _post(_app(), "/continuous-learning/risk-analysis", {risk_field: "unknown"})
    assert payload["blocked"] is True


def test_risk_analysis_requires_strong_approval_for_high_risk():
    payload = _post(_app(), "/continuous-learning/risk-analysis", {"security_risk": "high"})
    assert payload["strong_approval_required"] is True


def test_pr_planner_never_creates_branch_commit_push_or_pr():
    payload = _post(
        _app(),
        "/continuous-learning/pr-planner",
        {"branch_name_preview": "phase-p-preview", "files_likely_to_change": ["jarvis/example.py"]},
    )

    assert payload["branch_name_preview"] == "phase-p-preview"
    assert payload["would_create_branch"] is False
    assert payload["would_commit"] is False
    assert payload["would_push"] is False
    assert payload["would_create_pr"] is False
    assert payload["approval_required"] is True


def test_backlog_preview_never_persists_schedules_or_executes():
    payload = _post(
        _app(),
        "/continuous-learning/backlog-preview",
        {"backlog_items": ["Review Example"], "review_cadence": "weekly"},
    )

    assert payload["backlog_items"] == ["Review Example"]
    assert payload["would_persist"] is False
    assert payload["would_schedule"] is False
    assert payload["would_execute"] is False


def test_decision_preview_never_auto_adopts_installs_updates_deploys_or_modifies_runtime():
    payload = _post(_app(), "/continuous-learning/decision-preview", {"decision": "investigate"})

    assert payload["decision"] == "investigate"
    assert payload["no_auto_adoption"] is True
    assert payload["would_install"] is False
    assert payload["would_update"] is False
    assert payload["would_deploy"] is False
    assert payload["would_modify_runtime"] is False


def test_all_preview_routes_are_local_pure_and_do_not_call_bridges_or_create_work(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("Forbidden side effect was called")

    monkeypatch.setattr("jarvis.policy.approval_gateway.ApprovalGateway.create_request", fail)
    monkeypatch.setattr("jarvis.runtime.hermes_adapter.HermesRuntimeAdapter.run", fail, raising=False)
    monkeypatch.setattr("jarvis.mission_control.MissionControl.create_mission", fail)
    monkeypatch.setattr("jarvis.api.app.InMemoryTaskStore.create", fail)
    monkeypatch.setattr("subprocess.run", fail)
    monkeypatch.setattr("subprocess.Popen", fail)
    monkeypatch.setattr("socket.create_connection", fail)

    app = _app()
    for path in POST_ROUTES:
        payload = _post(app, path, {})
        assert payload["prepare_only"] is True


def test_dangerous_routes_and_websocket_do_not_exist():
    app = _app()
    route_pairs = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}

    for path in DANGEROUS_ROUTES:
        assert (path, "POST") not in route_pairs
    assert not any(route.__class__.__name__ == "APIWebSocketRoute" for route in app.routes)


def test_foundation_source_has_no_network_shell_git_package_manager_or_env_access():
    source = Path("jarvis/continuous_learning/foundation.py").read_text().lower()
    for forbidden in (
        "subprocess", "socket", "requests", "httpx", "urllib.request", "os.getenv", "os.environ",
        "dotenv", "pip install", "npm install", "git branch", "git commit", "git push", "gh pr",
    ):
        assert forbidden not in source


def test_command_center_and_operator_console_expose_prepare_only_markers():
    app = _app()
    command_center = _get(app, "/command-center")
    snapshot = OperatorConsoleSnapshot.from_dict({}).to_dict()
    capabilities = OperatorConsoleCapabilityMatrix.from_dict({}).to_dict()

    assert command_center["metadata"]["continuous_learning_tech_radar"] == "prepare_only"
    assert snapshot["metadata"]["continuous_learning_tech_radar"] == "prepare_only"
    assert snapshot["continuous_learning_status"]["prepare_only"] is True
    assert snapshot["tech_radar_safety_policy"]["prepare_only"] is True
    assert snapshot["learning_backlog_readiness"]["would_execute"] is False
    assert capabilities["read_continuous_learning_status"] is True
    assert capabilities["read_tech_radar_policy"] is True
    assert capabilities["preview_learning_backlog"] is True
    assert capabilities["execute_mission"] is False


def test_from_dict_and_serialization_cannot_enable_forbidden_capabilities():
    malicious = {field: True for field in STATUS_FALSE_FIELDS}
    malicious.update({
        "prepare_only": False,
        "would_install": True,
        "would_update": True,
        "would_deploy": True,
        "would_modify_runtime": True,
        "would_create_pr": True,
        "would_modify_code": True,
        "would_create_branch": True,
        "would_commit": True,
        "would_push": True,
        "approval_gateway_called": True,
        "approval_created": True,
        "would_persist": True,
        "would_schedule": True,
        "would_execute": True,
    })
    values = (
        ContinuousLearningStatus.from_dict(malicious),
        TechnologyCandidateProfile.from_dict(malicious),
        LearningProposalPreview.from_dict(malicious),
        ProposalImpactAnalysis.from_dict(malicious),
        ProposalRiskAnalysis.from_dict(malicious),
        PRPlannerPreview.from_dict(malicious),
        ApprovalWorkflowPreview.from_dict(malicious),
        LearningBacklogPreview.from_dict(malicious),
        TechRadarDecisionPreview.from_dict(malicious),
    )

    serialized = json.dumps([value.to_dict() for value in values])
    assert '"prepare_only": true' in serialized
    for field in (
        *STATUS_FALSE_FIELDS,
        "would_install", "would_update", "would_deploy", "would_modify_runtime", "would_create_pr",
        "would_modify_code", "would_create_branch", "would_commit", "would_push", "approval_gateway_called",
        "approval_created", "would_persist", "would_schedule", "would_execute",
    ):
        for value in values:
            if field in value.to_dict():
                assert value.to_dict()[field] is False


def test_policy_from_dict_cannot_disable_safety_requirements():
    payload = TechRadarSafetyPolicy.from_dict({
        name: False for name in TechRadarSafetyPolicy.__dataclass_fields__
    }).to_dict()
    assert all(payload.values())
