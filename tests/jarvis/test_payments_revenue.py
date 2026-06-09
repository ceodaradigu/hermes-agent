import json
import os
from pathlib import Path
import socket
import subprocess

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import InMemoryTaskStore, PaymentsRevenuePreviewRequest, create_app
from jarvis.mission_control import MissionControl
from jarvis.operator_console import OperatorConsoleSnapshot
from jarvis.payments_revenue.foundation import (
    CheckoutPlanPreview,
    FinancialRiskGuardPreview,
    InvoicePaymentLinkPreview,
    PaymentApprovalRequirements,
    PaymentProviderPreview,
    PaymentsRevenuePolicy,
    PaymentsRevenueStatus,
    PricingModelPreview,
    RefundChargebackPolicyPreview,
    RevenueExperimentPreview,
    RevenueMetricsPreview,
    SubscriptionPlanPreview,
)
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


POST_ROUTES = {
    "/payments-revenue/pricing-preview": PricingModelPreview,
    "/payments-revenue/checkout-plan": CheckoutPlanPreview,
    "/payments-revenue/provider-preview": PaymentProviderPreview,
    "/payments-revenue/metrics-preview": RevenueMetricsPreview,
    "/payments-revenue/subscription-preview": SubscriptionPlanPreview,
    "/payments-revenue/invoice-payment-link-preview": InvoicePaymentLinkPreview,
    "/payments-revenue/refund-chargeback-policy": RefundChargebackPolicyPreview,
    "/payments-revenue/financial-risk-guard": FinancialRiskGuardPreview,
    "/payments-revenue/revenue-experiment": RevenueExperimentPreview,
    "/payments-revenue/approval-requirements": PaymentApprovalRequirements,
}

DANGEROUS_ROUTES = (
    "/payments-revenue/create-checkout",
    "/payments-revenue/process-payment",
    "/payments-revenue/connect-provider",
    "/payments-revenue/connect-bank",
    "/payments-revenue/create-subscription",
    "/payments-revenue/create-invoice",
    "/payments-revenue/create-payment-link",
    "/payments-revenue/refund",
    "/payments-revenue/payout",
    "/payments-revenue/webhook",
    "/payments-revenue/run",
)

FORBIDDEN_FALSE_FIELDS = (
    "payments_available",
    "revenue_tracking_available",
    "checkout_creation_enabled",
    "payment_provider_connection_enabled",
    "payment_processing_enabled",
    "subscription_creation_enabled",
    "invoice_creation_enabled",
    "refund_execution_enabled",
    "chargeback_handling_enabled",
    "payout_enabled",
    "bank_connection_enabled",
    "card_data_handling_enabled",
    "paid_resource_creation_enabled",
    "external_calls_enabled",
    "secrets_access_enabled",
    "identity_usage_enabled",
    "hermes_called",
    "approval_gateway_called",
    "execution_enabled",
)


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Payments & Revenue")


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
    return _endpoint(app, path, "POST")(PaymentsRevenuePreviewRequest(**data))


def test_status_endpoint_is_http_200_prepare_only_and_fully_disabled():
    app = _app()
    route = next(route for route in app.routes if route.path == "/payments-revenue/status")
    payload = route.endpoint()

    assert "GET" in route.methods
    assert route.status_code in (None, 200)
    assert payload["prepare_only"] is True
    for key in FORBIDDEN_FALSE_FIELDS:
        assert payload[key] is False


def test_policy_endpoint_is_default_deny_and_requires_strong_approval():
    payload = _get(_app(), "/payments-revenue/policy")

    assert payload["prepare_only"] is True
    for key, value in payload.items():
        assert key == "prepare_only" or value is True
    for key in (
        "strong_approval_required_for_checkout",
        "strong_approval_required_for_payment_provider",
        "strong_approval_required_for_money_movement",
        "strong_approval_required_for_bank_connection",
        "strong_approval_required_for_identity",
        "strong_approval_required_for_refunds",
    ):
        assert payload[key] is True


def test_pricing_preview_is_hypothetical_and_does_not_invent_confirmed_revenue():
    payload = _post(
        _app(),
        "/payments-revenue/pricing-preview",
        {
            "product_name": "Reviewable product",
            "pricing_hypothesis": "10 EUR may be testable",
            "pricing_tiers": ["Starter: 10 EUR"],
        },
    )

    assert payload["pricing_hypothesis"] == "10 EUR may be testable"
    assert payload["validation_needed"] is True
    assert payload["no_confirmed_revenue"] is True
    assert payload["no_income_guarantees"] is True
    assert payload["would_charge"] is False
    assert payload["would_create_checkout"] is False


def test_confirmed_revenue_flag_changes_only_when_value_is_explicitly_provided():
    implicit = _post(_app(), "/payments-revenue/pricing-preview", {"confirmed_revenue": "100 EUR"})
    explicit = _post(
        _app(),
        "/payments-revenue/pricing-preview",
        {"confirmed_revenue": "100 EUR", "confirmed_revenue_explicitly_provided": True},
    )

    assert implicit["no_confirmed_revenue"] is True
    assert explicit["no_confirmed_revenue"] is False


def test_checkout_plan_is_blocked_and_never_creates_or_processes():
    payload = _post(
        _app(),
        "/payments-revenue/checkout-plan",
        {
            "checkout_requested": True,
            "provider": "stripe",
            "product_reference": "product-preview",
            "price_reference": "price-preview",
        },
    )

    assert payload["checkout_requested"] is True
    assert payload["provider"] == "stripe"
    assert payload["would_create_checkout"] is False
    assert payload["would_connect_provider"] is False
    assert payload["would_process_payment"] is False
    assert payload["would_collect_card_data"] is False
    assert payload["would_store_customer_data"] is False
    assert payload["secrets_required"] is False
    assert payload["strong_approval_required"] is True
    assert payload["blocked"] is True


def test_provider_preview_never_requests_key_stores_credentials_or_calls_external_service():
    payload = _post(_app(), "/payments-revenue/provider-preview", {"provider_name": "Stripe"})

    assert payload["provider_name"] == "Stripe"
    assert payload["would_connect_provider"] is False
    assert payload["would_request_api_key"] is False
    assert payload["would_store_credentials"] is False
    assert payload["would_create_webhook"] is False
    assert payload["would_create_product"] is False
    assert payload["would_create_price"] is False
    assert payload["would_make_external_call"] is False
    assert payload["secrets_access_enabled"] is False


def test_metrics_preview_keeps_unknowns_without_explicit_values_and_never_invents_metrics():
    payload = _post(_app(), "/payments-revenue/metrics-preview", {})

    assert set(payload["metrics"]) == {"MRR", "ARR", "ARPU", "conversion_rate", "churn", "LTV", "CAC", "gross_margin"}
    assert set(payload["metrics"].values()) == {"unknown"}
    assert payload["no_fake_metrics"] is True
    assert payload["no_confirmed_revenue"] is True
    assert payload["no_external_analytics_calls"] is True
    assert payload["no_personal_data_collection"] is True


def test_metrics_preview_accepts_only_explicit_user_provided_values():
    implicit = _post(_app(), "/payments-revenue/metrics-preview", {"metrics": {"MRR": "100"}})
    explicit = _post(
        _app(),
        "/payments-revenue/metrics-preview",
        {"metrics": {"MRR": "user-provided 100"}, "metrics_explicitly_provided": True},
    )

    assert implicit["metrics"]["MRR"] == "unknown"
    assert explicit["metrics"]["MRR"] == "user-provided 100"
    assert explicit["metrics"]["ARR"] == "unknown"


def test_subscription_preview_never_creates_subscription_trial_charge_or_payment_method():
    payload = _post(
        _app(),
        "/payments-revenue/subscription-preview",
        {"plan_name": "Preview", "billing_interval": "monthly", "trial_policy": "14 days"},
    )

    assert payload["would_create_subscription"] is False
    assert payload["would_create_trial"] is False
    assert payload["would_charge"] is False
    assert payload["would_store_payment_method"] is False
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True


def test_invoice_payment_link_preview_never_creates_sends_or_charges():
    payload = _post(
        _app(),
        "/payments-revenue/invoice-payment-link-preview",
        {"invoice_requested": True, "payment_link_requested": True},
    )

    assert payload["invoice_requested"] is True
    assert payload["payment_link_requested"] is True
    assert payload["would_create_invoice"] is False
    assert payload["would_create_payment_link"] is False
    assert payload["would_send_invoice"] is False
    assert payload["would_charge"] is False
    assert payload["tax_review_required"] is True
    assert payload["legal_review_required"] is True


def test_refund_chargeback_policy_never_contacts_provider_refunds_or_moves_money():
    payload = _post(
        _app(),
        "/payments-revenue/refund-chargeback-policy",
        {"refund_policy": "Review within 14 days", "chargeback_risk": "unknown"},
    )

    assert payload["would_issue_refund"] is False
    assert payload["would_contact_provider"] is False
    assert payload["would_move_money"] is False
    assert payload["financial_review_required"] is True
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True


@pytest.mark.parametrize(
    "risk",
    [
        "money_movement_requested",
        "bank_requested",
        "card_requested",
        "provider_requested",
        "provider_connection_requested",
        "secrets_requested",
    ],
)
def test_financial_risk_guard_blocks_money_bank_card_provider_and_secret_risk(risk):
    payload = _post(_app(), "/payments-revenue/financial-risk-guard", {risk: True})

    assert payload["risk_level"] == "blocked"
    assert payload["blocked"] is True
    assert payload["strong_approval_required"] is True


def test_financial_risk_guard_marks_tax_legal_and_income_claim_risk_without_conclusion():
    payload = _post(
        _app(),
        "/payments-revenue/financial-risk-guard",
        {"tax_requested": True, "legal_requested": True, "income_claim_requested": True},
    )

    assert payload["tax_or_legal_risk_detected"] is True
    assert payload["income_claim_risk_detected"] is True
    assert payload["risk_level"] == "high"
    assert payload["strong_approval_required"] is True


def test_financial_risk_guard_never_accepts_unverified_low_risk_and_round_trips_risk_signals():
    unverified = _post(_app(), "/payments-revenue/financial-risk-guard", {"risk_level": "low"})
    original = FinancialRiskGuardPreview.from_request({"bank_requested": True, "tax_requested": True})
    restored = FinancialRiskGuardPreview.from_dict(original.to_dict()).to_dict()

    assert unverified["risk_level"] == "unknown"
    assert restored["bank_or_card_data_detected"] is True
    assert restored["tax_or_legal_risk_detected"] is True
    assert restored["risk_level"] == "blocked"
    assert restored["blocked"] is True


def test_revenue_experiment_never_launches_spends_creates_checkout_or_processes_payment():
    payload = _post(
        _app(),
        "/payments-revenue/revenue-experiment",
        {"experiment_name": "Pricing test", "max_budget": "50 EUR"},
    )

    assert payload["would_launch"] is False
    assert payload["would_spend"] is False
    assert payload["would_create_checkout"] is False
    assert payload["would_process_payment"] is False
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True


@pytest.mark.parametrize(
    "risk",
    [
        "checkout_requested",
        "provider_requested",
        "bank_requested",
        "card_requested",
        "money_movement_requested",
        "refund_requested",
        "subscription_requested",
        "invoice_requested",
        "identity_requested",
        "secrets_requested",
    ],
)
def test_approval_requirements_require_strong_approval_for_financial_risk(risk):
    payload = _post(_app(), "/payments-revenue/approval-requirements", {risk: True})

    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["approval_gateway_called"] is False
    assert payload["approval_created"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_rejected"] is False


def test_all_endpoints_have_no_forbidden_side_effects(monkeypatch):
    app = _app()

    def fail(*args, **kwargs):
        raise AssertionError("Payments & Revenue preview attempted a forbidden side effect")

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

    assert _get(app, "/payments-revenue/status")["execution_enabled"] is False
    assert _get(app, "/payments-revenue/policy")["no_payment_processing_by_default"] is True
    for path in POST_ROUTES:
        assert _post(app, path, {})["prepare_only"] is True


def test_api_schema_does_not_request_external_accounts_tokens_or_financial_data():
    fields = set(PaymentsRevenuePreviewRequest.model_fields)

    for forbidden in (
        "account", "account_id", "bank_account", "card", "card_number", "cvv", "token", "api_key",
        "credentials", "customer_identity", "webhook_url",
    ):
        assert forbidden not in fields


@pytest.mark.parametrize("path", DANGEROUS_ROUTES)
def test_dangerous_routes_do_not_exist(path):
    assert path not in [route.path for route in _app().routes]


def test_no_payments_revenue_websocket_exists():
    assert not any(
        route.path.startswith("/payments-revenue") and route.__class__.__name__ == "APIWebSocketRoute"
        for route in _app().routes
    )


def test_sensitive_values_are_redacted_from_previews():
    payload = _post(
        _app(),
        "/payments-revenue/provider-preview",
        {"provider_name": "API key secret-value", "warnings": ["card number 4111111111111111"]},
    )
    serialized = json.dumps(payload).lower()

    assert payload["provider_name"] == "[redacted sensitive input]"
    assert payload["warnings"] == ["[redacted sensitive input]"]
    assert "secret-value" not in serialized
    assert "4111111111111111" not in serialized


def test_command_center_and_operator_console_remain_prepare_only():
    app = _app()
    command_center = _get(app, "/command-center")
    operator = _get(app, "/operator/console/snapshot")

    assert command_center["prepare_only"] is True
    assert command_center["execution_enabled"] is False
    assert command_center["metadata"]["payments_revenue"] == "prepare_only"
    assert operator["prepare_only"] is True
    assert operator["metadata"]["payments_revenue"] == "prepare_only"
    assert operator["payments_revenue_status"] == PaymentsRevenueStatus.placeholder().to_dict()
    assert operator["payments_revenue_policy"] == PaymentsRevenuePolicy.placeholder().to_dict()
    assert operator["financial_readiness"] == FinancialRiskGuardPreview().to_dict()
    assert operator["capability_matrix"]["read_payments_revenue_status"] is True
    assert operator["capability_matrix"]["read_payments_revenue_policy"] is True
    assert operator["capability_matrix"]["preview_payments_revenue"] is True
    assert operator["capability_matrix"]["spend_money"] is False
    for key in FORBIDDEN_FALSE_FIELDS:
        assert operator["payments_revenue_status"][key] is False


@pytest.mark.parametrize(
    "model",
    [
        PaymentsRevenueStatus,
        PricingModelPreview,
        CheckoutPlanPreview,
        PaymentProviderPreview,
        SubscriptionPlanPreview,
        InvoicePaymentLinkPreview,
        RefundChargebackPolicyPreview,
        RevenueExperimentPreview,
        PaymentApprovalRequirements,
    ],
)
def test_from_dict_cannot_enable_forbidden_financial_capabilities(model):
    hostile = {
        "prepare_only": False,
        **{key: True for key in FORBIDDEN_FALSE_FIELDS},
        "would_charge": True,
        "would_create_checkout": True,
        "would_connect_provider": True,
        "would_process_payment": True,
        "would_collect_card_data": True,
        "would_store_customer_data": True,
        "secrets_required": True,
        "would_request_api_key": True,
        "would_store_credentials": True,
        "would_create_webhook": True,
        "would_create_product": True,
        "would_create_price": True,
        "would_make_external_call": True,
        "would_create_subscription": True,
        "would_create_trial": True,
        "would_store_payment_method": True,
        "would_create_invoice": True,
        "would_create_payment_link": True,
        "would_send_invoice": True,
        "would_issue_refund": True,
        "would_contact_provider": True,
        "would_move_money": True,
        "would_launch": True,
        "would_spend": True,
        "approval_created": True,
        "approval_granted": True,
        "approval_rejected": True,
    }
    payload = model.from_dict(hostile).to_dict()

    assert payload["prepare_only"] is True
    for key, value in payload.items():
        if key in hostile and key != "prepare_only":
            assert value is False


def test_policy_from_dict_cannot_disable_safety_requirements():
    payload = PaymentsRevenuePolicy.from_dict(
        {name: False for name in PaymentsRevenuePolicy.__dataclass_fields__}
    ).to_dict()

    assert all(payload.values())


def test_operator_console_from_dict_cannot_enable_payments_revenue():
    payload = OperatorConsoleSnapshot.from_dict(
        {
            "payments_revenue_status": {
                "payment_processing_enabled": True,
                "checkout_creation_enabled": True,
                "external_calls_enabled": True,
            },
            "payments_revenue_policy": {"no_payment_processing_by_default": False},
            "financial_readiness": {"blocked": False, "strong_approval_required": False},
            "capability_matrix": {"spend_money": True},
        }
    ).to_dict()

    assert payload["payments_revenue_status"]["payment_processing_enabled"] is False
    assert payload["payments_revenue_status"]["checkout_creation_enabled"] is False
    assert payload["payments_revenue_status"]["external_calls_enabled"] is False
    assert payload["payments_revenue_policy"]["no_payment_processing_by_default"] is True
    assert payload["capability_matrix"]["spend_money"] is False
