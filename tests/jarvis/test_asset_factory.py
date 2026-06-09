import json
import os
import subprocess

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import AssetFactoryPreviewRequest, InMemoryTaskStore, create_app
from jarvis.asset_factory.foundation import (
    AssetFactoryStatus,
    AssetGenerationPolicy,
    BuildPackagePreview,
    CopyContentPackPreview,
    LandingPagePlan,
    MonetizationOfferPreview,
    PublishingReadinessPreview,
    StaticAssetManifestPreview,
    WebProjectBrief,
    WebsiteStructurePlan,
)
from jarvis.mission_control import MissionControl
from jarvis.operator_console import OperatorConsoleSnapshot
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


POST_ROUTES = {
    "/asset-factory/web-brief": WebProjectBrief,
    "/asset-factory/landing-plan": LandingPagePlan,
    "/asset-factory/website-structure": WebsiteStructurePlan,
    "/asset-factory/copy-pack": CopyContentPackPreview,
    "/asset-factory/static-asset-manifest": StaticAssetManifestPreview,
    "/asset-factory/build-package-preview": BuildPackagePreview,
    "/asset-factory/publishing-readiness": PublishingReadinessPreview,
    "/asset-factory/monetization-offer-preview": MonetizationOfferPreview,
}


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Asset Factory")


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
    return _endpoint(app, path, "POST")(AssetFactoryPreviewRequest(**data))


class DirectResponse:
    def __init__(self, payload):
        self.status_code = 200
        self._payload = payload

    def json(self):
        return self._payload


def test_asset_factory_status_endpoint_is_http_200_and_fully_disabled():
    response = DirectResponse(_get(_app(), "/asset-factory/status"))
    payload = response.json()

    assert response.status_code == 200
    assert payload["prepare_only"] is True
    for key in (
        "asset_factory_available",
        "web_builder_available",
        "publishing_enabled",
        "deployment_enabled",
        "domain_connection_enabled",
        "external_account_connection_enabled",
        "paid_resource_creation_enabled",
        "identity_usage_enabled",
        "build_execution_enabled",
        "external_calls_enabled",
        "secrets_access_enabled",
        "hermes_called",
        "approval_gateway_called",
        "execution_enabled",
    ):
        assert payload[key] is False


def test_asset_generation_policy_requires_review_and_strong_approval():
    response = DirectResponse(_get(_app(), "/asset-factory/policy"))
    payload = response.json()

    assert response.status_code == 200
    assert payload["prepare_only"] is True
    assert payload["review_required_before_publication"] is True
    for key in (
        "no_publishing_by_default",
        "no_deployment_by_default",
        "no_domain_changes_by_default",
        "no_external_accounts_by_default",
        "no_paid_resources_by_default",
        "no_identity_usage_by_default",
        "no_income_claims_by_default",
        "strong_approval_required_for_publish",
        "strong_approval_required_for_domains",
        "strong_approval_required_for_paid_resources",
        "strong_approval_required_for_identity",
    ):
        assert payload[key] is True


def test_web_brief_preserves_unknown_roi_and_never_takes_action():
    payload = _post(
        _app(),
        "/asset-factory/web-brief",
        {
            "project_name": "Reviewable demo",
            "audience": "Small teams",
            "monetization_hypothesis": "Subscription may be tested later",
            "confirmed_roi": "900 percent",
        },
    )

    assert payload["prepare_only"] is True
    assert payload["confirmed_roi"] == "unknown"
    assert payload["unknown_remains_unknown"] is True
    assert payload["would_publish"] is False
    assert payload["would_deploy"] is False
    assert payload["would_spend"] is False
    assert payload["would_use_identity"] is False


def test_landing_plan_is_prepare_only_and_forbids_fake_claims():
    payload = _post(
        _app(),
        "/asset-factory/landing-plan",
        {"hero": "A reviewable draft", "sections": ["Problem", "Offer"], "cta": "Review the proposal"},
    )

    assert payload["prepare_only"] is True
    assert payload["hero"] == "A reviewable draft"
    assert payload["sections"] == ["Problem", "Offer"]
    assert payload["no_income_guarantees"] is True
    assert payload["no_fake_testimonials"] is True
    assert payload["no_fake_metrics"] is True
    assert payload["no_fake_legal_claims"] is True
    assert payload["would_publish"] is False
    assert payload["would_deploy"] is False


def test_website_structure_never_requires_build_deployment_or_external_services():
    payload = _post(
        _app(),
        "/asset-factory/website-structure",
        {"pages": ["Home", "FAQ"], "external_services_required": True, "deployment_required": True},
    )

    assert payload["pages"] == ["Home", "FAQ"]
    assert payload["build_required"] is False
    assert payload["deployment_required"] is False
    assert payload["external_services_required"] is False


def test_copy_pack_redacts_sensitive_input_and_forbids_fabrication():
    payload = _post(
        _app(),
        "/asset-factory/copy-pack",
        {"headlines": ["Simple offer"], "offer_copy": ["Use API_KEY=abc"], "cta_copy": ["Review"]},
    )
    serialized = json.dumps(payload).lower()

    assert payload["headlines"] == ["Simple offer"]
    assert payload["offer_copy"] == ["[redacted sensitive input]"]
    assert payload["sensitive_input_redacted"] is True
    assert payload["no_fake_claims"] is True
    assert payload["no_fake_testimonials"] is True
    assert payload["no_fabricated_numbers"] is True
    assert payload["no_income_guarantees"] is True
    assert "abc" not in serialized


def test_static_asset_manifest_is_preview_only_and_redacts_unsafe_paths():
    payload = _post(
        _app(),
        "/asset-factory/static-asset-manifest",
        {"files_to_create": ["index.html", "../../.env"], "directories": ["assets", "/etc"]},
    )

    assert payload["files_to_create"] == ["index.html", "[redacted sensitive input]"]
    assert payload["directories"] == ["assets", "[redacted sensitive input]"]
    assert payload["would_write_files"] is False
    assert payload["would_overwrite_files"] is False
    assert payload["filesystem_scope_required"] is True
    assert payload["sandbox_execution_required"] is True
    assert payload["approval_required"] is True


def test_build_package_preview_never_installs_builds_runs_or_modifies_packages():
    payload = _post(
        _app(),
        "/asset-factory/build-package-preview",
        {
            "framework": "static html",
            "package_type": "reviewable preview",
            "dependencies_preview": ["new-package"],
            "build_steps_preview": ["Future approved build step"],
        },
    )

    assert payload["would_install"] is False
    assert payload["would_build"] is False
    assert payload["would_run"] is False
    assert payload["would_modify_package_files"] is False
    assert payload["sandbox_required"] is True
    assert payload["tool_adoption_review_required"] is True


def test_publishing_readiness_never_allows_publish_and_requires_strong_approval():
    payload = _post(
        _app(),
        "/asset-factory/publishing-readiness",
        {"required_checks": ["Legal review"], "missing_items": []},
    )

    assert payload["ready_to_publish"] is False
    assert payload["publish_allowed"] is False
    assert payload["legal_review_required"] is True
    assert payload["identity_approval_required"] is True
    assert payload["domain_approval_required"] is True
    assert payload["paid_resource_approval_required"] is True
    assert payload["strong_approval_required"] is True


def test_monetization_preview_never_sets_up_payments_or_confirms_revenue():
    payload = _post(
        _app(),
        "/asset-factory/monetization-offer-preview",
        {"offer_name": "Draft offer", "pricing_hypothesis": "Test 10 EUR later"},
    )

    assert payload["prepare_only"] is True
    assert payload["validation_needed"] is True
    assert payload["no_confirmed_revenue"] is True
    assert payload["no_income_guarantees"] is True
    assert payload["payment_setup_enabled"] is False
    assert payload["stripe_or_payment_calls_enabled"] is False
    assert payload["approval_required"] is True


def test_asset_factory_endpoints_have_no_forbidden_side_effects(monkeypatch):
    app = _app()

    def fail(*args, **kwargs):
        raise AssertionError("Asset Factory preview attempted a forbidden side effect")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail, raising=False)
    monkeypatch.setattr(MissionControl, "create_mission", fail)
    monkeypatch.setattr(InMemoryTaskStore, "create", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(os, "system", fail)
    monkeypatch.setattr("builtins.open", fail)

    assert _get(app, "/asset-factory/status")["execution_enabled"] is False
    assert _get(app, "/asset-factory/policy")["no_publishing_by_default"] is True
    for path in POST_ROUTES:
        assert _post(app, path, {})["prepare_only"] is True


@pytest.mark.parametrize(
    "path",
    [
        "/asset-factory/publish",
        "/asset-factory/deploy",
        "/asset-factory/domain",
        "/asset-factory/connect-account",
        "/asset-factory/pay",
        "/asset-factory/build",
        "/asset-factory/write-files",
        "/asset-factory/run",
    ],
)
def test_dangerous_asset_factory_routes_do_not_exist(path):
    assert path not in [route.path for route in _app().routes]


def test_command_center_and_operator_console_expose_prepare_only_asset_factory():
    app = _app()
    command_center = _get(app, "/command-center")
    operator = _get(app, "/operator/console/snapshot")

    assert command_center["prepare_only"] is True
    assert command_center["metadata"]["asset_factory_web_builder"] == "prepare_only"
    assert operator["prepare_only"] is True
    assert operator["metadata"]["asset_factory_web_builder"] == "prepare_only"
    assert operator["asset_factory_status"] == AssetFactoryStatus.placeholder().to_dict()
    assert operator["asset_generation_policy"] == AssetGenerationPolicy.placeholder().to_dict()
    assert operator["capability_matrix"]["read_asset_factory_status"] is True
    assert operator["capability_matrix"]["read_asset_generation_policy"] is True
    assert operator["capability_matrix"]["preview_asset_factory"] is True
    assert operator["capability_matrix"]["deploy"] is False
    assert operator["capability_matrix"]["spend_money"] is False


@pytest.mark.parametrize(
    "model",
    [
        AssetFactoryStatus,
        AssetGenerationPolicy,
        WebProjectBrief,
        LandingPagePlan,
        WebsiteStructurePlan,
        CopyContentPackPreview,
        StaticAssetManifestPreview,
        BuildPackagePreview,
        PublishingReadinessPreview,
        MonetizationOfferPreview,
    ],
)
def test_from_dict_cannot_enable_forbidden_asset_factory_capabilities(model):
    payload = model.from_dict(
        {
            "prepare_only": False,
            "asset_factory_available": True,
            "web_builder_available": True,
            "publishing_enabled": True,
            "deployment_enabled": True,
            "domain_connection_enabled": True,
            "external_account_connection_enabled": True,
            "paid_resource_creation_enabled": True,
            "identity_usage_enabled": True,
            "build_execution_enabled": True,
            "external_calls_enabled": True,
            "secrets_access_enabled": True,
            "hermes_called": True,
            "approval_gateway_called": True,
            "execution_enabled": True,
            "would_publish": True,
            "would_deploy": True,
            "would_spend": True,
            "would_use_identity": True,
            "would_write_files": True,
            "would_overwrite_files": True,
            "would_install": True,
            "would_build": True,
            "would_run": True,
            "would_modify_package_files": True,
            "build_required": True,
            "deployment_required": True,
            "external_services_required": True,
            "ready_to_publish": True,
            "publish_allowed": True,
            "payment_setup_enabled": True,
            "stripe_or_payment_calls_enabled": True,
        }
    ).to_dict()

    assert payload["prepare_only"] is True
    for key, value in payload.items():
        if key in {
            "asset_factory_available", "web_builder_available", "publishing_enabled", "deployment_enabled",
            "domain_connection_enabled", "external_account_connection_enabled", "paid_resource_creation_enabled",
            "identity_usage_enabled", "build_execution_enabled", "external_calls_enabled", "secrets_access_enabled",
            "hermes_called", "approval_gateway_called", "execution_enabled", "would_publish", "would_deploy",
            "would_spend", "would_use_identity", "would_write_files", "would_overwrite_files", "would_install",
            "would_build", "would_run", "would_modify_package_files", "build_required", "deployment_required",
            "external_services_required", "ready_to_publish", "publish_allowed", "payment_setup_enabled",
            "stripe_or_payment_calls_enabled",
        }:
            assert value is False


def test_operator_snapshot_from_dict_cannot_enable_asset_factory():
    hostile = {key: True for key in AssetFactoryStatus.placeholder().to_dict()}
    payload = OperatorConsoleSnapshot.from_dict({"asset_factory_status": hostile}).to_dict()

    assert payload["asset_factory_status"] == AssetFactoryStatus.placeholder().to_dict()


def test_direct_construction_is_safe_in_memory_and_redacts_sensitive_content():
    status = AssetFactoryStatus(publishing_enabled=True, deployment_enabled=True, external_calls_enabled=True)
    copy = CopyContentPackPreview(offer_copy=["Bearer abc"], no_fake_claims=False)
    build = BuildPackagePreview(dependencies_preview=["candidate"], would_install=True, would_build=True)

    assert status.prepare_only is True
    assert status.publishing_enabled is False
    assert status.deployment_enabled is False
    assert status.external_calls_enabled is False
    assert copy.offer_copy == ["[redacted sensitive input]"]
    assert copy.sensitive_input_redacted is True
    assert copy.no_fake_claims is True
    assert build.would_install is False
    assert build.would_build is False
    assert build.tool_adoption_review_required is True
