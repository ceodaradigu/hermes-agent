import json
import os
from pathlib import Path
import socket
import subprocess

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import InMemoryTaskStore, MarketingDistributionPreviewRequest, create_app
from jarvis.marketing_distribution.foundation import (
    AudienceSegmentPreview,
    BudgetSpendGuardPreview,
    CampaignPlanPreview,
    ChannelStrategyPreview,
    ContentDistributionPackPreview,
    DistributionApprovalRequirements,
    LaunchChecklistPreview,
    MarketingDistributionPolicy,
    MarketingDistributionStatus,
    MeasurementPlanPreview,
)
from jarvis.mission_control import MissionControl
from jarvis.operator_console import OperatorConsoleSnapshot
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


POST_ROUTES = {
    "/marketing-distribution/audience-preview": AudienceSegmentPreview,
    "/marketing-distribution/channel-strategy": ChannelStrategyPreview,
    "/marketing-distribution/campaign-plan": CampaignPlanPreview,
    "/marketing-distribution/content-pack": ContentDistributionPackPreview,
    "/marketing-distribution/measurement-plan": MeasurementPlanPreview,
    "/marketing-distribution/budget-guard": BudgetSpendGuardPreview,
    "/marketing-distribution/launch-checklist": LaunchChecklistPreview,
    "/marketing-distribution/approval-requirements": DistributionApprovalRequirements,
}

DANGEROUS_ROUTES = (
    "/marketing-distribution/publish",
    "/marketing-distribution/send-email",
    "/marketing-distribution/send-dm",
    "/marketing-distribution/post-social",
    "/marketing-distribution/create-ad",
    "/marketing-distribution/spend",
    "/marketing-distribution/connect-account",
    "/marketing-distribution/scrape",
    "/marketing-distribution/run",
)


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Marketing / Distribution Engine")


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
    return _endpoint(app, path, "POST")(MarketingDistributionPreviewRequest(**data))


def test_status_endpoint_is_http_200_prepare_only_and_fully_disabled():
    app = _app()
    route = next(route for route in app.routes if route.path == "/marketing-distribution/status")
    payload = route.endpoint()

    assert "GET" in route.methods
    assert route.status_code in (None, 200)
    assert payload["prepare_only"] is True
    for key in (
        "marketing_engine_available",
        "campaign_execution_enabled",
        "publishing_enabled",
        "external_account_connection_enabled",
        "paid_ads_enabled",
        "email_sending_enabled",
        "dm_sending_enabled",
        "social_posting_enabled",
        "scraping_enabled",
        "identity_usage_enabled",
        "budget_spend_enabled",
        "external_calls_enabled",
        "secrets_access_enabled",
        "hermes_called",
        "approval_gateway_called",
        "execution_enabled",
    ):
        assert payload[key] is False


def test_policy_endpoint_is_default_deny_and_requires_strong_approval():
    payload = _get(_app(), "/marketing-distribution/policy")

    assert payload["prepare_only"] is True
    for key in (
        "no_publish_by_default",
        "no_send_by_default",
        "no_paid_ads_by_default",
        "no_scraping_by_default",
        "no_spam_by_default",
        "no_external_accounts_by_default",
        "no_identity_usage_by_default",
        "no_budget_spend_by_default",
        "no_fake_claims_by_default",
        "no_fake_social_proof_by_default",
        "review_required_before_distribution",
        "strong_approval_required_for_publish",
        "strong_approval_required_for_sending",
        "strong_approval_required_for_paid_ads",
        "strong_approval_required_for_identity",
        "strong_approval_required_for_external_accounts",
        "strong_approval_required_for_budget_spend",
    ):
        assert payload[key] is True


def test_audience_preview_uses_only_user_input_and_no_personal_data():
    payload = _post(
        _app(),
        "/marketing-distribution/audience-preview",
        {
            "audience_name": "Independent teams",
            "problem": "Distribution planning",
            "channels": ["community", "SEO"],
            "data_source": "user_provided",
            "confidence": "medium",
        },
    )

    assert payload["audience_name"] == "Independent teams"
    assert payload["data_source"] == "user_provided"
    assert payload["no_external_research_performed"] is True
    assert payload["no_personal_data_required"] is True


def test_channel_strategy_is_organic_prepare_only():
    payload = _post(
        _app(),
        "/marketing-distribution/channel-strategy",
        {"channels": ["SEO", "community"], "expected_cost": "low"},
    )

    assert payload["organic_first"] is True
    assert payload["paid_distribution_allowed"] is False
    assert payload["external_account_required"] is False
    assert payload["approval_required"] is True


def test_campaign_plan_never_publishes_sends_spends_or_calls_external_service():
    payload = _post(
        _app(),
        "/marketing-distribution/campaign-plan",
        {
            "campaign_name": "Reviewable launch",
            "publish_requested": True,
            "send_requested": True,
            "paid_requested": True,
        },
    )

    assert payload["would_publish"] is False
    assert payload["would_send"] is False
    assert payload["would_spend"] is False
    assert payload["would_call_external_service"] is False
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True


def test_content_pack_redacts_sensitive_input_and_forbids_fabrication():
    payload = _post(
        _app(),
        "/marketing-distribution/content-pack",
        {
            "posts": ["Review this draft"],
            "email_drafts": ["Authorization: Bearer abc"],
            "seo_snippets": ["Useful planning guide"],
        },
    )
    serialized = json.dumps(payload).lower()

    assert payload["email_drafts"] == ["[redacted sensitive input]"]
    assert payload["sensitive_input_redacted"] is True
    assert payload["would_publish"] is False
    assert payload["would_send"] is False
    assert payload["no_fake_claims"] is True
    assert payload["no_fake_social_proof"] is True
    assert payload["no_income_guarantees"] is True
    assert payload["no_fabricated_metrics"] is True
    assert "abc" not in serialized


def test_measurement_plan_does_not_install_tracking_or_call_analytics():
    payload = _post(
        _app(),
        "/marketing-distribution/measurement-plan",
        {"utm_plan": ["utm_source=review"], "metrics": ["reviewed click count"]},
    )

    assert payload["no_tracking_installed"] is True
    assert payload["no_external_analytics_calls"] is True
    assert payload["no_personal_data_collection"] is True


def test_budget_guard_never_spends_and_requires_strong_approval():
    payload = _post(_app(), "/marketing-distribution/budget-guard", {"budget_requested": "100 EUR maximum"})

    assert payload["budget_requested"] == "100 EUR maximum"
    assert payload["would_spend"] is False
    assert payload["paid_ads_enabled"] is False
    assert payload["payment_setup_enabled"] is False
    assert payload["spend_limit_required"] is True
    assert payload["strong_approval_required"] is True


def test_budget_amount_makes_campaign_and_approval_requirements_strong():
    app = _app()

    campaign = _post(app, "/marketing-distribution/campaign-plan", {"budget_requested": "50 EUR"})
    approval = _post(app, "/marketing-distribution/approval-requirements", {"budget_requested": "50 EUR"})

    assert campaign["strong_approval_required"] is True
    assert approval["strong_approval_required"] is True


def test_launch_checklist_is_not_ready_and_marks_risky_approvals():
    payload = _post(
        _app(),
        "/marketing-distribution/launch-checklist",
        {
            "required_assets": ["Reviewed content"],
            "missing_items": [],
            "identity_requested": True,
            "external_account_requested": True,
            "budget_requested": "50 EUR",
        },
    )

    assert payload["ready_to_launch"] is False
    assert payload["missing_items"]
    assert payload["legal_review_required"] is True
    assert payload["identity_approval_required"] is True
    assert payload["external_account_approval_required"] is True
    assert payload["paid_budget_approval_required"] is True
    assert payload["publish_approval_required"] is True
    assert payload["strong_approval_required"] is True


@pytest.mark.parametrize(
    "risk",
    [
        "publish_requested",
        "send_requested",
        "paid_requested",
        "external_account_requested",
        "identity_requested",
        "secrets_requested",
        "budget_spend_requested",
    ],
)
def test_approval_requirements_require_strong_approval_for_risky_distribution(risk):
    payload = _post(_app(), "/marketing-distribution/approval-requirements", {risk: True})

    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["approval_gateway_called"] is False
    assert payload["approval_created"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_rejected"] is False


def test_all_endpoints_have_no_forbidden_side_effects(monkeypatch):
    app = _app()

    def fail(*args, **kwargs):
        raise AssertionError("Marketing / Distribution preview attempted a forbidden side effect")

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

    assert _get(app, "/marketing-distribution/status")["execution_enabled"] is False
    assert _get(app, "/marketing-distribution/policy")["no_spam_by_default"] is True
    for path in POST_ROUTES:
        assert _post(app, path, {})["prepare_only"] is True


def test_api_schema_does_not_request_external_account_or_token_values():
    fields = set(MarketingDistributionPreviewRequest.model_fields)

    assert "account" not in fields
    assert "account_id" not in fields
    assert "token" not in fields
    assert "api_key" not in fields
    assert "credentials" not in fields
    assert "external_account_requested" in fields


@pytest.mark.parametrize("path", DANGEROUS_ROUTES)
def test_dangerous_routes_do_not_exist(path):
    assert path not in [route.path for route in _app().routes]


def test_no_marketing_distribution_websocket_exists():
    assert not any(
        route.path.startswith("/marketing-distribution") and route.__class__.__name__ == "APIWebSocketRoute"
        for route in _app().routes
    )


def test_command_center_and_operator_console_remain_prepare_only():
    app = _app()
    command_center = _get(app, "/command-center")
    operator = _get(app, "/operator/console/snapshot")

    assert command_center["prepare_only"] is True
    assert command_center["execution_enabled"] is False
    assert command_center["metadata"]["marketing_distribution_engine"] == "prepare_only"
    assert operator["prepare_only"] is True
    assert operator["metadata"]["marketing_distribution_engine"] == "prepare_only"
    assert operator["marketing_distribution_status"] == MarketingDistributionStatus.placeholder().to_dict()
    assert operator["marketing_distribution_policy"] == MarketingDistributionPolicy.placeholder().to_dict()
    assert operator["marketing_launch_readiness"] == LaunchChecklistPreview.placeholder().to_dict()
    assert operator["capability_matrix"]["read_marketing_distribution_status"] is True
    assert operator["capability_matrix"]["read_marketing_distribution_policy"] is True
    assert operator["capability_matrix"]["preview_marketing_distribution"] is True
    assert operator["capability_matrix"]["deploy"] is False
    assert operator["capability_matrix"]["spend_money"] is False


@pytest.mark.parametrize(
    "model",
    [
        MarketingDistributionStatus,
        MarketingDistributionPolicy,
        AudienceSegmentPreview,
        ChannelStrategyPreview,
        CampaignPlanPreview,
        ContentDistributionPackPreview,
        MeasurementPlanPreview,
        BudgetSpendGuardPreview,
        LaunchChecklistPreview,
        DistributionApprovalRequirements,
    ],
)
def test_from_dict_cannot_enable_forbidden_capabilities(model):
    hostile = {
        "prepare_only": False,
        "marketing_engine_available": True,
        "campaign_execution_enabled": True,
        "publishing_enabled": True,
        "external_account_connection_enabled": True,
        "paid_ads_enabled": True,
        "email_sending_enabled": True,
        "dm_sending_enabled": True,
        "social_posting_enabled": True,
        "scraping_enabled": True,
        "identity_usage_enabled": True,
        "budget_spend_enabled": True,
        "external_calls_enabled": True,
        "secrets_access_enabled": True,
        "hermes_called": True,
        "approval_gateway_called": True,
        "execution_enabled": True,
        "paid_distribution_allowed": True,
        "external_account_required": True,
        "would_publish": True,
        "would_send": True,
        "would_spend": True,
        "would_call_external_service": True,
        "payment_setup_enabled": True,
        "ready_to_launch": True,
        "approval_created": True,
        "approval_granted": True,
        "approval_rejected": True,
    }
    payload = model.from_dict(hostile).to_dict()

    assert payload["prepare_only"] is True
    for key, value in payload.items():
        if key in hostile and key != "prepare_only":
            assert value is False


def test_operator_console_from_dict_cannot_enable_marketing_distribution():
    payload = OperatorConsoleSnapshot.from_dict(
        {
            "marketing_distribution_status": {"publishing_enabled": True, "execution_enabled": True},
            "marketing_distribution_policy": {"no_spam_by_default": False},
            "marketing_launch_readiness": {"ready_to_launch": True},
            "capability_matrix": {"spend_money": True, "deploy": True},
        }
    ).to_dict()

    assert payload["marketing_distribution_status"]["publishing_enabled"] is False
    assert payload["marketing_distribution_status"]["execution_enabled"] is False
    assert payload["marketing_distribution_policy"]["no_spam_by_default"] is True
    assert payload["marketing_launch_readiness"]["ready_to_launch"] is False
    assert payload["capability_matrix"]["spend_money"] is False
    assert payload["capability_matrix"]["deploy"] is False
