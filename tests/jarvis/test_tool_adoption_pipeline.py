import os
import subprocess

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
from jarvis.api.app import (
    InMemoryTaskStore,
    ToolAdoptionDecisionPreviewRequest,
    ToolCandidateProfileRequest,
    ToolDependencyRiskReviewRequest,
    ToolLicenseReviewRequest,
    ToolRepoHealthReviewRequest,
    ToolSandboxInstallProposalRequest,
    ToolSpikePlanRequest,
    ToolValueMeasurementPreviewRequest,
    create_app,
)
from jarvis.mission_control import MissionControl
from jarvis.operator_console import OperatorConsoleSnapshot
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter
from jarvis.tool_adoption.pipeline import (
    ToolAdoptionDecisionPreview,
    ToolAdoptionStatus,
    ToolCandidateProfile,
    ToolDependencyRiskReview,
    ToolLicenseReview,
    ToolRepoHealthReview,
    ToolSandboxInstallProposal,
    ToolSpikePlan,
    ToolValueMeasurementPreview,
)


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Tool Adoption Pipeline")


REQUEST_TYPES = {
    "/tools/candidate/profile": ToolCandidateProfileRequest,
    "/tools/license/review": ToolLicenseReviewRequest,
    "/tools/repo-health/review": ToolRepoHealthReviewRequest,
    "/tools/dependency-risk/review": ToolDependencyRiskReviewRequest,
    "/tools/sandbox-install/proposal": ToolSandboxInstallProposalRequest,
    "/tools/spike/plan": ToolSpikePlanRequest,
    "/tools/value/preview": ToolValueMeasurementPreviewRequest,
    "/tools/adoption/decision-preview": ToolAdoptionDecisionPreviewRequest,
}


def _app():
    return create_app(adapter_factory=FailAdapter)


def _endpoint(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def _get(app, path):
    return _endpoint(app, path, "GET")()


class DirectResponse:
    def __init__(self, payload):
        self.status_code = 200
        self._payload = payload

    def json(self):
        return self._payload


def _post(app, path, data):
    return _endpoint(app, path, "POST")(REQUEST_TYPES[path](**data))


def test_tool_adoption_status_endpoint_is_http_200_and_fully_disabled():
    response = DirectResponse(_get(_app(), "/tools/adoption/status"))
    payload = response.json()

    assert response.status_code == 200
    assert payload["prepare_only"] is True
    for key in (
        "tool_adoption_available",
        "external_discovery_enabled",
        "repo_clone_enabled",
        "install_enabled",
        "sandbox_install_enabled",
        "external_execution_enabled",
        "core_dependency_adoption_enabled",
        "network_access_enabled",
        "secrets_access_enabled",
        "approval_gateway_called",
        "hermes_called",
        "execution_enabled",
    ):
        assert payload[key] is False


def test_candidate_profile_never_clones_installs_executes_or_adopts_core():
    payload = _post(
        _app(),
        "/tools/candidate/profile",
        {
            "tool_name": "Graphify",
            "source_url": "https://user:password@example.invalid/repo?token=abc#private",
            "declared_use_case": "Evaluate code graph value",
        },
    )

    assert payload["prepare_only"] is True
    assert payload["source_url"] == ""
    assert payload["license"] == "unknown"
    assert payload["adoption_blocked"] is True
    assert payload["requires_approval"] is True
    assert payload["would_clone"] is False
    assert payload["would_install"] is False
    assert payload["would_execute"] is False
    assert payload["would_become_core_dependency"] is False


@pytest.mark.parametrize(
    "license_value,blocked,strong",
    [
        ("unknown", True, False),
        ("", True, False),
        ("unclear custom", True, False),
        ("commercial proprietary", False, True),
    ],
)
def test_license_review_is_prepare_only_and_conservative(license_value, blocked, strong):
    payload = _post(_app(), "/tools/license/review", {"license": license_value})

    assert payload["prepare_only"] is True
    assert payload["external_lookup_performed"] is False
    assert payload["legal_conclusion"] == "not_provided"
    assert payload["adoption_blocked"] is blocked
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is strong
    assert payload["core_adoption_requires_strong_approval"] is True


def test_repo_health_review_uses_only_optional_caller_metadata_and_preserves_unknown():
    unknown = _post(_app(), "/tools/repo-health/review", {})
    provided = _post(
        _app(),
        "/tools/repo-health/review",
        {"metadata": {"stars": 12, "forks": 3, "open_issues": 4, "last_activity": "caller-provided"}},
    )

    assert unknown["repo_health"] == "unknown"
    assert unknown["stars"] is None
    assert unknown["external_lookup_performed"] is False
    assert unknown["network_called"] is False
    assert provided["metadata_provided"] is True
    assert provided["stars"] == 12
    assert provided["repo_health"] == "unknown"


def test_dependency_risk_flags_native_binary_postinstall_and_network_characteristics():
    payload = _post(
        _app(),
        "/tools/dependency-risk/review",
        {"dependencies": ["node-gyp native", "prebuilt binary", "postinstall script", "network download"]},
    )

    assert payload["dependency_risk"] == "high"
    assert payload["native_dependency_detected"] is True
    assert payload["binary_dependency_detected"] is True
    assert payload["postinstall_dependency_detected"] is True
    assert payload["network_dependency_detected"] is True
    assert payload["risky_dependencies"]
    assert payload["install_performed"] is False
    assert payload["package_manager_called"] is False
    assert payload["install_proposal_blocked"] is True
    assert payload["strong_approval_required"] is True


def test_sandbox_install_proposal_never_installs_and_requires_all_guards():
    payload = _post(_app(), "/tools/sandbox-install/proposal", {"tool_name": "CodeGraph"})

    assert payload["prepare_only"] is True
    assert payload["would_install"] is False
    assert payload["install_enabled"] is False
    assert payload["sandbox_required"] is True
    assert payload["filesystem_scope_required"] is True
    assert payload["network_blocked_by_default"] is True
    assert payload["secrets_blocked"] is True
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["rollback_required"] is True
    assert payload["blocked"] is True


def test_spike_plan_contains_required_plan_fields_and_never_executes():
    payload = _post(
        _app(),
        "/tools/spike/plan",
        {
            "hypothesis": "CodeGraph reduces review time",
            "scope": "one synthetic fixture",
            "success_metric": "20 percent less review time",
            "max_time": "2 hours",
            "max_cost": "0",
            "rollback": "discard isolated artifacts",
        },
    )

    assert payload["hypothesis"] == "CodeGraph reduces review time"
    assert payload["scope"] == "one synthetic fixture"
    assert payload["success_metric"] == "20 percent less review time"
    assert payload["rollback"] == "discard isolated artifacts"
    assert payload["would_execute"] is False
    assert payload["execution_enabled"] is False
    assert payload["approval_required_before_install_or_run"] is True


def test_value_preview_preserves_unknowns_and_does_not_invent_roi_or_revenue():
    unknown = _post(_app(), "/tools/value/preview", {})
    provided = _post(_app(), "/tools/value/preview", {"time_saved": "caller measured 10 minutes"})

    assert unknown["time_saved"] == "unknown"
    assert unknown["token_saved"] == "unknown"
    assert unknown["revenue_enablement"] == "unknown"
    assert unknown["roi"] == "unknown"
    assert unknown["confirmed_revenue"] is False
    assert provided["time_saved"] == "caller measured 10 minutes"
    assert provided["roi"] == "unknown"
    assert provided["confirmed_revenue"] is False


def test_adoption_decision_blocks_core_adoption_and_requires_strong_approval_for_risk():
    payload = _post(
        _app(),
        "/tools/adoption/decision-preview",
        {
            "license": "mit",
            "repo_health": "healthy",
            "dependency_risk": "low",
            "expected_value": "measured",
            "core_dependency_requested": True,
        },
    )

    assert payload["decision"] == "adoption_blocked"
    assert payload["keep_decision"] is False
    assert payload["rollback_plan_required"] is True
    assert payload["core_dependency_allowed"] is False
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["would_become_core_dependency"] is False


def test_tool_adoption_endpoints_have_no_forbidden_side_effects(monkeypatch):
    app = _app()

    def fail(*args, **kwargs):
        raise AssertionError("Tool adoption preview attempted a forbidden side effect")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail, raising=False)
    monkeypatch.setattr(MissionControl, "create_mission", fail)
    monkeypatch.setattr(InMemoryTaskStore, "create", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(os, "system", fail)
    monkeypatch.setattr("builtins.open", fail)

    assert _get(app, "/tools/adoption/status")["execution_enabled"] is False
    assert _post(app, "/tools/candidate/profile", {})["would_clone"] is False
    assert _post(app, "/tools/license/review", {})["external_lookup_performed"] is False
    assert _post(app, "/tools/repo-health/review", {})["network_called"] is False
    assert _post(app, "/tools/dependency-risk/review", {})["package_manager_called"] is False
    assert _post(app, "/tools/sandbox-install/proposal", {})["would_install"] is False
    assert _post(app, "/tools/spike/plan", {})["would_execute"] is False
    assert _post(app, "/tools/value/preview", {})["roi"] == "unknown"
    assert _post(app, "/tools/adoption/decision-preview", {})["core_dependency_allowed"] is False


@pytest.mark.parametrize(
    "path",
    ["/tools/install", "/tools/run", "/tools/clone", "/tools/adopt-core", "/tools/execute", "/tools/network"],
)
def test_dangerous_tool_adoption_routes_do_not_exist(path):
    assert path not in [route.path for route in _app().routes]


def test_command_center_and_operator_console_expose_prepare_only_tool_adoption_capability():
    app = _app()
    command_center = _get(app, "/command-center")
    operator = _get(app, "/operator/console/snapshot")

    assert command_center["metadata"]["tool_adoption_pipeline"] == "prepare_only"
    assert operator["metadata"]["tool_adoption_pipeline"] == "prepare_only"
    assert operator["tool_adoption_status"] == ToolAdoptionStatus.placeholder().to_dict()
    assert operator["capability_matrix"]["read_tool_adoption_status"] is True
    assert operator["capability_matrix"]["preview_tool_adoption"] is True
    assert operator["capability_matrix"]["execute_mission"] is False


@pytest.mark.parametrize(
    "model",
    [
        ToolAdoptionStatus,
        ToolCandidateProfile,
        ToolLicenseReview,
        ToolRepoHealthReview,
        ToolDependencyRiskReview,
        ToolSandboxInstallProposal,
        ToolSpikePlan,
        ToolValueMeasurementPreview,
        ToolAdoptionDecisionPreview,
    ],
)
def test_from_dict_cannot_enable_forbidden_tool_adoption_capabilities(model):
    payload = model.from_dict(
        {
            "tool_name": "candidate",
            "prepare_only": False,
            "tool_adoption_available": True,
            "external_discovery_enabled": True,
            "repo_clone_enabled": True,
            "install_enabled": True,
            "sandbox_install_enabled": True,
            "external_execution_enabled": True,
            "core_dependency_adoption_enabled": True,
            "network_access_enabled": True,
            "secrets_access_enabled": True,
            "approval_gateway_called": True,
            "hermes_called": True,
            "execution_enabled": True,
            "would_clone": True,
            "would_install": True,
            "would_execute": True,
            "would_access_network": True,
            "would_access_secrets": True,
            "would_become_core_dependency": True,
            "core_dependency_allowed": True,
        }
    ).to_dict()

    assert payload["prepare_only"] is True
    for key in (
        "tool_adoption_available",
        "external_discovery_enabled",
        "repo_clone_enabled",
        "install_enabled",
        "sandbox_install_enabled",
        "external_execution_enabled",
        "core_dependency_adoption_enabled",
        "network_access_enabled",
        "secrets_access_enabled",
        "approval_gateway_called",
        "hermes_called",
        "execution_enabled",
        "would_clone",
        "would_install",
        "would_execute",
        "would_access_network",
        "would_access_secrets",
        "would_become_core_dependency",
        "core_dependency_allowed",
    ):
        if key in payload:
            assert payload[key] is False


def test_operator_snapshot_from_dict_cannot_enable_tool_adoption():
    payload = OperatorConsoleSnapshot.from_dict(
        {"tool_adoption_status": {key: True for key in ToolAdoptionStatus.placeholder().to_dict()}}
    ).to_dict()

    assert payload["tool_adoption_status"] == ToolAdoptionStatus.placeholder().to_dict()
