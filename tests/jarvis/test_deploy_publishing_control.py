import os
from pathlib import Path
import socket
import subprocess

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import DeployPublishingPreviewRequest, InMemoryTaskStore, create_app
from jarvis.deploy_publishing.foundation import (
    DeployPublishingPolicy,
    DeployPublishingStatus,
    DeploymentTargetPreview,
    DomainConnectionPreview,
    ExternalAccountConnectionPreview,
    ProductionReleasePreview,
    PublishingApprovalRequirements,
    PublishingPlanPreview,
    PublishingReadinessChecklist,
    PublishingRollbackPreview,
)
from jarvis.mission_control import MissionControl
from jarvis.operator_console import OperatorConsoleSnapshot
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


POST_ROUTES = {
    "/deploy-publishing/target-preview": DeploymentTargetPreview,
    "/deploy-publishing/publish-plan": PublishingPlanPreview,
    "/deploy-publishing/domain-preview": DomainConnectionPreview,
    "/deploy-publishing/account-preview": ExternalAccountConnectionPreview,
    "/deploy-publishing/production-preview": ProductionReleasePreview,
    "/deploy-publishing/rollback-preview": PublishingRollbackPreview,
    "/deploy-publishing/readiness-checklist": PublishingReadinessChecklist,
    "/deploy-publishing/approval-requirements": PublishingApprovalRequirements,
}

DANGEROUS_ROUTES = (
    "/deploy-publishing/publish",
    "/deploy-publishing/deploy",
    "/deploy-publishing/production-release",
    "/deploy-publishing/connect-domain",
    "/deploy-publishing/change-dns",
    "/deploy-publishing/connect-account",
    "/deploy-publishing/create-resource",
    "/deploy-publishing/pay",
    "/deploy-publishing/rollback",
)


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Deploy & Publishing Control")


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
    return _endpoint(app, path, "POST")(DeployPublishingPreviewRequest(**data))


def test_status_endpoint_is_http_200_and_every_execution_capability_is_disabled():
    app = _app()
    route = next(route for route in app.routes if route.path == "/deploy-publishing/status")
    payload = route.endpoint()

    assert "GET" in route.methods
    assert route.status_code in (None, 200)
    assert payload["prepare_only"] is True
    for key in (
        "deploy_control_available",
        "publishing_enabled",
        "deployment_enabled",
        "production_enabled",
        "domain_management_enabled",
        "external_account_connection_enabled",
        "paid_resource_creation_enabled",
        "identity_usage_enabled",
        "rollback_execution_enabled",
        "build_execution_enabled",
        "external_calls_enabled",
        "secrets_access_enabled",
        "hermes_called",
        "approval_gateway_called",
        "execution_enabled",
    ):
        assert payload[key] is False


def test_policy_endpoint_is_default_deny_and_requires_strong_approval():
    payload = _get(_app(), "/deploy-publishing/policy")

    assert payload["prepare_only"] is True
    for key in (
        "no_publish_by_default",
        "no_deploy_by_default",
        "no_production_by_default",
        "no_domain_changes_by_default",
        "no_external_accounts_by_default",
        "no_paid_resources_by_default",
        "no_identity_usage_by_default",
        "no_secret_access_by_default",
        "rollback_plan_required",
        "readiness_check_required",
        "strong_approval_required_for_publish",
        "strong_approval_required_for_production",
        "strong_approval_required_for_domains",
        "strong_approval_required_for_paid_resources",
        "strong_approval_required_for_identity",
    ):
        assert payload[key] is True


def test_target_preview_never_connects_creates_resources_or_deploys():
    payload = _post(
        _app(),
        "/deploy-publishing/target-preview",
        {"target_name": "review-host", "target_type": "cloud", "environment": "staging"},
    )

    assert payload["target_name"] == "review-host"
    assert payload["target_type"] == "cloud"
    assert payload["environment"] == "staging"
    assert payload["would_connect"] is False
    assert payload["would_create_resource"] is False
    assert payload["would_deploy"] is False
    assert payload["external_calls_enabled"] is False
    assert payload["secrets_required"] is False


def test_production_target_requires_strong_approval_without_enabling_production():
    payload = _post(
        _app(),
        "/deploy-publishing/target-preview",
        {"target_name": "prod", "target_type": "server", "environment": "production"},
    )

    assert payload["production_target"] is True
    assert payload["strong_approval_required"] is True
    assert payload["would_connect"] is False
    assert payload["would_deploy"] is False


def test_publish_plan_never_publishes_or_deploys_and_stays_blocked():
    payload = _post(
        _app(),
        "/deploy-publishing/publish-plan",
        {"asset_reference": "asset-preview-1", "publish_destination": "review-host"},
    )

    assert payload["would_publish"] is False
    assert payload["would_deploy"] is False
    assert payload["would_use_domain"] is False
    assert payload["would_use_identity"] is False
    assert payload["would_spend"] is False
    assert payload["would_call_external_service"] is False
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["readiness_complete"] is False
    assert payload["blocked"] is True


def test_domain_preview_never_connects_changes_dns_or_verifies():
    payload = _post(
        _app(),
        "/deploy-publishing/domain-preview",
        {"domain_requested": True, "domain_name": "example.invalid"},
    )

    assert payload["domain_requested"] is True
    assert payload["would_connect_domain"] is False
    assert payload["would_change_dns"] is False
    assert payload["would_verify_domain"] is False
    assert payload["domain_ownership_unverified"] is True
    assert payload["strong_approval_required"] is True


def test_account_preview_never_requests_tokens_or_stores_credentials():
    payload = _post(_app(), "/deploy-publishing/account-preview", {"account_type": "hosting"})

    assert payload["would_connect_account"] is False
    assert payload["would_request_token"] is False
    assert payload["would_store_credentials"] is False
    assert payload["secrets_access_enabled"] is False
    assert payload["strong_approval_required"] is True


def test_production_preview_never_releases_and_stays_blocked():
    payload = _post(_app(), "/deploy-publishing/production-preview", {"production_requested": True})

    assert payload["production_requested"] is True
    assert payload["would_release"] is False
    assert payload["production_access_enabled"] is False
    assert payload["strong_approval_required"] is True
    assert payload["rollback_plan_required"] is True
    assert payload["readiness_check_required"] is True
    assert payload["blocked"] is True


def test_rollback_preview_never_executes_rollback():
    payload = _post(
        _app(),
        "/deploy-publishing/rollback-preview",
        {"rollback_steps_preview": ["Restore previous reviewed artifact"], "irreversible_risks": ["DNS propagation"]},
    )

    assert payload["rollback_required"] is True
    assert payload["would_rollback"] is False
    assert payload["rollback_execution_enabled"] is False
    assert payload["rollback_steps_preview"] == ["Restore previous reviewed artifact"]
    assert payload["audit_required"] is True


def test_readiness_checklist_is_never_ready_and_marks_requested_approvals():
    payload = _post(
        _app(),
        "/deploy-publishing/readiness-checklist",
        {
            "required_checks": ["Legal review"],
            "missing_items": [],
            "identity_requested": True,
            "domain_requested": True,
            "paid_resource_requested": True,
            "production_requested": True,
        },
    )

    assert payload["ready_to_publish"] is False
    assert payload["missing_items"]
    assert payload["legal_review_required"] is True
    assert payload["identity_approval_required"] is True
    assert payload["domain_approval_required"] is True
    assert payload["paid_resource_approval_required"] is True
    assert payload["production_approval_required"] is True
    assert payload["strong_approval_required"] is True


def test_approval_requirements_never_create_or_decide_approval():
    payload = _post(
        _app(),
        "/deploy-publishing/approval-requirements",
        {"publish_requested": True, "secrets_requested": True},
    )

    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["approval_gateway_called"] is False
    assert payload["approval_created"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_rejected"] is False


def test_all_endpoints_have_no_forbidden_side_effects(monkeypatch):
    app = _app()

    def fail(*args, **kwargs):
        raise AssertionError("Deploy & Publishing preview attempted a forbidden side effect")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail, raising=False)
    monkeypatch.setattr(MissionControl, "create_mission", fail)
    monkeypatch.setattr(InMemoryTaskStore, "create", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(os, "system", fail)
    monkeypatch.setattr(socket, "socket", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    monkeypatch.setattr(Path, "write_bytes", fail)
    monkeypatch.setattr("builtins.open", fail)

    assert _get(app, "/deploy-publishing/status")["execution_enabled"] is False
    assert _get(app, "/deploy-publishing/policy")["no_publish_by_default"] is True
    for path in POST_ROUTES:
        assert _post(app, path, {})["prepare_only"] is True


@pytest.mark.parametrize("path", DANGEROUS_ROUTES)
def test_dangerous_routes_do_not_exist(path):
    assert path not in [route.path for route in _app().routes]


def test_command_center_and_operator_console_remain_prepare_only():
    app = _app()
    command_center = _get(app, "/command-center")
    operator = _get(app, "/operator/console/snapshot")

    assert command_center["prepare_only"] is True
    assert command_center["execution_enabled"] is False
    assert command_center["metadata"]["deploy_publishing_control"] == "prepare_only"
    assert operator["prepare_only"] is True
    assert operator["metadata"]["deploy_publishing_control"] == "prepare_only"
    assert operator["deploy_publishing_status"] == DeployPublishingStatus.placeholder().to_dict()
    assert operator["deploy_publishing_policy"] == DeployPublishingPolicy.placeholder().to_dict()
    assert operator["publishing_readiness"] == PublishingReadinessChecklist.placeholder().to_dict()
    assert operator["capability_matrix"]["read_deploy_publishing_status"] is True
    assert operator["capability_matrix"]["read_deploy_publishing_policy"] is True
    assert operator["capability_matrix"]["preview_deploy_publishing"] is True
    assert operator["capability_matrix"]["deploy"] is False
    assert operator["capability_matrix"]["spend_money"] is False


@pytest.mark.parametrize(
    "model",
    [
        DeployPublishingStatus,
        DeployPublishingPolicy,
        DeploymentTargetPreview,
        PublishingPlanPreview,
        DomainConnectionPreview,
        ExternalAccountConnectionPreview,
        ProductionReleasePreview,
        PublishingRollbackPreview,
        PublishingReadinessChecklist,
        PublishingApprovalRequirements,
    ],
)
def test_from_dict_cannot_enable_forbidden_capabilities(model):
    hostile = {
        "prepare_only": False,
        "deploy_control_available": True,
        "publishing_enabled": True,
        "deployment_enabled": True,
        "production_enabled": True,
        "domain_management_enabled": True,
        "external_account_connection_enabled": True,
        "paid_resource_creation_enabled": True,
        "identity_usage_enabled": True,
        "rollback_execution_enabled": True,
        "build_execution_enabled": True,
        "external_calls_enabled": True,
        "secrets_access_enabled": True,
        "hermes_called": True,
        "approval_gateway_called": True,
        "execution_enabled": True,
        "would_connect": True,
        "would_create_resource": True,
        "would_deploy": True,
        "secrets_required": True,
        "would_publish": True,
        "would_use_domain": True,
        "would_use_identity": True,
        "would_spend": True,
        "would_call_external_service": True,
        "would_connect_domain": True,
        "would_change_dns": True,
        "would_verify_domain": True,
        "would_connect_account": True,
        "would_request_token": True,
        "would_store_credentials": True,
        "would_release": True,
        "production_access_enabled": True,
        "would_rollback": True,
        "ready_to_publish": True,
        "approval_created": True,
        "approval_granted": True,
        "approval_rejected": True,
    }
    payload = model.from_dict(hostile).to_dict()

    assert payload["prepare_only"] is True
    for key in hostile:
        if key in payload and key not in {"prepare_only"}:
            if key in {
                "deploy_control_available", "publishing_enabled", "deployment_enabled", "production_enabled",
                "domain_management_enabled", "external_account_connection_enabled", "paid_resource_creation_enabled",
                "identity_usage_enabled", "rollback_execution_enabled", "build_execution_enabled",
                "external_calls_enabled", "secrets_access_enabled", "hermes_called", "approval_gateway_called",
                "execution_enabled", "would_connect", "would_create_resource", "would_deploy", "secrets_required",
                "would_publish", "would_use_domain", "would_use_identity", "would_spend",
                "would_call_external_service", "would_connect_domain", "would_change_dns", "would_verify_domain",
                "would_connect_account", "would_request_token", "would_store_credentials", "would_release",
                "production_access_enabled", "would_rollback", "ready_to_publish", "approval_created",
                "approval_granted", "approval_rejected",
            }:
                assert payload[key] is False


def test_operator_snapshot_deserialization_cannot_enable_deploy_publishing():
    hostile = {key: True for key in DeployPublishingStatus.placeholder().to_dict()}
    payload = OperatorConsoleSnapshot.from_dict(
        {
            "deploy_publishing_status": hostile,
            "deploy_publishing_policy": {"prepare_only": False},
            "publishing_readiness": {"ready_to_publish": True},
        }
    ).to_dict()

    assert payload["deploy_publishing_status"] == DeployPublishingStatus.placeholder().to_dict()
    assert payload["deploy_publishing_policy"] == DeployPublishingPolicy.placeholder().to_dict()
    assert payload["publishing_readiness"]["ready_to_publish"] is False
