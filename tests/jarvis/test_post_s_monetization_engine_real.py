from __future__ import annotations

import builtins
from pathlib import Path
import socket
import subprocess

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import MonetizationPreviewRequest, create_app
from jarvis.command_center import build_command_center_view_model
from jarvis.monetization_engine import MonetizationEngine, MonetizationEngineStatus, monetization_markers
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import build_operational_console_summary, build_operational_system_status
from jarvis.payment_approval_control import BudgetGuard, PaymentApprovalControl, StripeReadinessPreview
from jarvis.pricing_strategy import PricingPlan
from jarvis.revenue_modeling import RevenueProjection, UnitEconomicsProjection
from jarvis.wake_voice_runtime import WakeVoiceRuntime


DOC = Path("docs/jarvis-post-s-monetization-engine-real.md")
DANGEROUS_ROUTES = (
    "/monetization/charge",
    "/monetization/pay",
    "/monetization/spend",
    "/monetization/stripe/live/charge",
    "/monetization/stripe/create-checkout",
    "/monetization/stripe/create-product",
    "/monetization/stripe/create-price",
    "/monetization/stripe/create-customer",
    "/monetization/execute",
    "/monetization/run",
    "/monetization/auto-approve",
    "/monetization/approve-all",
)


def _route(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route
    return None


def test_status_and_policy_define_real_monetization_readiness_with_safe_defaults():
    engine = MonetizationEngine()
    status = engine.status()
    policy = engine.policy()
    assert MonetizationEngineStatus().monetization_engine_available is True
    assert status["restrictions_are_approval_gates"] is True
    assert status["real_money_movement_enabled"] is False
    assert status["external_payment_calls_disabled"] is True
    assert status["live_payments_enabled"] is False
    assert status["money_actions_executable_after_valid_approval"] is True
    assert status["revenue_estimates_are_not_confirmed"] is True
    assert policy["wake_phrase_is_not_payment_permission"] is True
    assert policy["scheduler_due_is_not_spend_permission"] is True
    assert policy["memory_active_is_not_monetization_permission"] is True


def test_pricing_preview_proposes_plan_without_live_billing_or_charge():
    plan = PricingPlan.from_request(
        {
            "plan_id": "starter",
            "name": "Starter",
            "price_amount": 20,
            "currency": "eur",
            "billing_interval": "monthly",
            "included_usage": "100 runs",
        }
    ).to_dict()
    assert plan["price_amount"] == 20
    assert plan["enabled_for_preview"] is True
    assert plan["live_billing_enabled"] is False
    assert plan["would_charge_real_money"] is False
    assert "proposed price is not a confirmed sale" in plan["risk_notes"]


def test_revenue_projection_calculates_estimates_and_never_confirms_revenue():
    projection = RevenueProjection.from_request(
        {
            "expected_customers": 10,
            "conversion_rate": 0.1,
            "churn_rate": 0.03,
            "monthly_price": 20,
            "assumptions": ["customer count is hypothetical"],
        }
    ).to_dict()
    assert projection["estimated_mrr"] == 200
    assert projection["estimated_arr"] == 2400
    assert projection["is_estimate"] is True
    assert projection["is_confirmed_revenue"] is False


def test_revenue_projection_marks_unknowns_instead_of_inventing_customers():
    projection = RevenueProjection.from_request({}).to_dict()
    assert "expected_customers" in projection["unknowns"]
    assert "conversion_rate" in projection["unknowns"]
    assert projection["estimated_mrr"] is None
    assert projection["confidence_level"] == "low"
    assert projection["blocked_reasons"]


def test_budget_guard_blocks_without_approval_and_unknown_cost():
    normal = BudgetGuard.from_request(
        {"monthly_budget_limit": 100, "per_action_spend_limit": 30, "current_spend_estimate": 10, "proposed_spend": 20}
    ).to_dict()
    unknown = BudgetGuard.from_request(
        {"monthly_budget_limit": 100, "per_action_spend_limit": 30, "valid_approval_present": True}
    ).to_dict()
    assert normal["remaining_budget"] == 70
    assert normal["spend_allowed"] is False
    assert "valid explicit approval required" in normal["blocked_reasons"]
    assert unknown["strong_approval_required"] is True
    assert unknown["double_confirmation_required"] is True
    assert "proposed spend is unknown" in unknown["blocked_reasons"]


def test_budget_guard_over_limit_requires_strong_approval_and_double_confirmation():
    guard = BudgetGuard.from_request(
        {
            "monthly_budget_limit": 100,
            "per_action_spend_limit": 30,
            "current_spend_estimate": 0,
            "proposed_spend": 40,
            "valid_approval_present": True,
        }
    ).to_dict()
    assert guard["budget_exceeded"] is True
    assert guard["strong_approval_required"] is True
    assert guard["double_confirmation_required"] is True
    assert guard["spend_allowed"] is False


def test_payment_preview_default_denies_and_test_mode_never_calls_provider():
    control = PaymentApprovalControl()
    blocked = control.preview({"action_name": "charge customer", "amount": 30, "real_money_requested": True}).to_dict()
    test_mode = control.preview(
        {
            "action_name": "prepare Stripe test",
            "provider": "stripe",
            "mode": "test",
            "valid_approval_present": True,
            "context_fingerprint_matches": True,
            "permission_gates_passed": True,
            "audit_present": True,
        }
    ).to_dict()
    assert blocked["eligible_after_approval"] is False
    assert blocked["execution_allowed"] is False
    assert test_mode["eligible_after_approval"] is True
    assert test_mode["strong_approval_required"] is False
    assert test_mode["would_call_payment_provider"] is False


def test_live_payment_requires_strong_approval_and_double_confirmation_then_only_becomes_eligible():
    control = PaymentApprovalControl()
    blocked = control.preview(
        {"action_name": "Stripe live charge", "provider": "stripe_live", "mode": "live", "valid_approval_present": True}
    ).to_dict()
    eligible = control.preview(
        {
            "action_name": "Stripe live charge",
            "provider": "stripe_live",
            "mode": "live",
            "amount": 30,
            "valid_approval_present": True,
            "strong_approval_present": True,
            "double_confirmation_present": True,
            "context_fingerprint_matches": True,
            "permission_gates_passed": True,
            "audit_present": True,
            "rollback_or_stop_plan_present": True,
        }
    ).to_dict()
    assert blocked["strong_approval_required"] is True
    assert blocked["double_confirmation_required"] is True
    assert blocked["eligible_after_approval"] is False
    assert eligible["eligible_after_approval"] is True
    assert eligible["execution_allowed"] is False
    assert eligible["would_charge_real_money"] is False
    assert eligible["would_call_payment_provider"] is False


@pytest.mark.parametrize("flag", ["illegal", "fraudulent", "unsafe", "unauthorized", "impossible", "unsupported"])
def test_payment_permanent_denial_cannot_be_overridden(flag):
    decision = PaymentApprovalControl().preview(
        {
            "action_name": "denied payment",
            "mode": "live",
            "valid_approval_present": True,
            "strong_approval_present": True,
            "double_confirmation_present": True,
            flag: True,
        }
    ).to_dict()
    assert decision["permanent_denial"] is True
    assert decision["eligible_after_approval"] is False
    assert decision["denial_reason"]


def test_stripe_readiness_never_loads_or_exposes_secrets_or_live_calls():
    preview = StripeReadinessPreview.from_request(
        {
            "secret_key_loaded": True,
            "stripe_live_mode_ready": True,
            "live_charges_enabled": True,
            "external_calls_enabled": True,
            "product_catalog_preview": [{"api_key": "sk_test_sensitive"}],
            "checkout_preview": {"client_secret": "secret-sensitive"},
        }
    ).to_dict()
    assert preview["stripe_configured"] is False
    assert preview["secret_key_loaded"] is False
    assert preview["secret_key_value_redacted"] is True
    assert preview["stripe_live_mode_ready"] is False
    assert preview["live_charges_enabled"] is False
    assert preview["external_calls_enabled"] is False
    assert "sk_test_sensitive" not in str(preview)
    assert "secret-sensitive" not in str(preview)


def test_action_previews_never_execute_charge_spend_or_call_external():
    engine = MonetizationEngine()
    preview = engine.preview_action(
        {
            "action_type": "approve_payment_candidate",
            "valid_approval_present": True,
            "strong_approval_present": True,
            "double_confirmation_present": True,
        }
    )
    assert preview["eligible_after_valid_approval"] is True
    for field in ("would_execute", "would_charge_real_money", "would_spend_real_money", "would_call_external"):
        assert preview[field] is False


def test_unit_economics_calculates_estimates_and_preserves_uncertainty():
    calculated = UnitEconomicsProjection.from_request(
        {
            "acquisition_spend": 100,
            "acquired_customers": 10,
            "monthly_revenue_per_customer": 20,
            "gross_margin_rate": 0.8,
            "monthly_churn_rate": 0.1,
            "investment": 100,
            "return_amount": 80,
            "assumptions": ["inputs are estimates"],
        }
    ).to_dict()
    unknown = UnitEconomicsProjection.from_request({}).to_dict()
    assert calculated["cac_estimate"] == 10
    assert calculated["ltv_estimate"] == 160
    assert calculated["roi_estimate"] == -20
    assert calculated["roi_assessment"] == "negative"
    assert calculated["not_financial_advice"] is True
    assert calculated["not_confirmed_results"] is True
    assert unknown["roi_assessment"] == "uncertain"
    assert unknown["confidence"] == "low"


def test_control_plane_endpoints_exist_and_do_not_use_env_network_or_subprocess(monkeypatch):
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
    gets = ("/monetization/status", "/monetization/policy")
    posts = (
        "/monetization/preview-pricing",
        "/monetization/preview-revenue",
        "/monetization/preview-budget",
        "/monetization/preview-payment-approval",
        "/monetization/preview-stripe-readiness",
        "/monetization/preview-action",
        "/monetization/preview-unit-economics",
    )
    for path in gets:
        route = _route(app, path, "GET")
        assert route is not None and route.status_code in (None, 200)
        route.endpoint()
    for path in posts:
        route = _route(app, path, "POST")
        assert route is not None and route.status_code in (None, 200)
        payload = route.endpoint(MonetizationPreviewRequest())
        assert payload.get("would_execute", False) is False
        assert payload.get("would_call_payment_provider", False) is False
        assert payload.get("external_calls_enabled", False) is False
    for path in DANGEROUS_ROUTES:
        assert _route(app, path, "GET") is None
        assert _route(app, path, "POST") is None


def test_operational_command_center_and_operator_console_expose_monetization_markers():
    status = build_operational_system_status().to_dict()
    summary = build_operational_console_summary()
    command = build_command_center_view_model(view_id="monetization", generated_at="2026-06-11T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="monetization", generated_at="2026-06-11T00:00:00+00:00")
    for marker in monetization_markers():
        assert summary["command_center"][marker] is True
        assert command.metadata[marker] is True
        assert operator.metadata[marker] is True
    assert status["monetization_engine_available"] is True
    assert status["real_money_movement_enabled"] is False
    assert status["money_actions_executable_after_valid_approval"] is True
    assert status["current_mark"] == "Mark 1"


def test_wake_phrase_scheduler_due_and_memory_policy_are_not_money_permission():
    wake = WakeVoiceRuntime().parse("Jarvis cobra 30 euros a este cliente").to_dict()
    policy = MonetizationEngine().policy()
    assert wake["wake_phrase_is_not_permission"] is True
    assert wake["execution_enabled"] is False
    assert policy["scheduler_due_is_not_spend_permission"] is True
    assert policy["memory_active_is_not_monetization_permission"] is True


def test_documentation_declares_boundaries_examples_and_next_macro():
    content = DOC.read_text(encoding="utf-8")
    for text in (
        "no es Phase T",
        "Mark 1",
        "Restrictions are approval gates, not permanent bans",
        "no mueve dinero real",
        "revenue estimado no es revenue confirmado",
        "no llama Stripe",
        "Post-S Macro 9",
        "/monetization/preview-payment-approval",
    ):
        assert text in content
