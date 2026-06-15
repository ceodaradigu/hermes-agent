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
    Mark3ProductRevenueFactoryRequest,
    Mark3ResearchExecutionCandidateRequest,
    create_app,
)
from jarvis.mark_3_local_research_adapter import LocalResearchReadAdapter  # noqa: E402
from jarvis.mark_3_product_revenue_factory import (  # noqa: E402
    FINANCIAL_FIELDS,
    Mark3ProductRevenueFactory,
)
from jarvis.mark_3_research_execution import ResearchExecutionControlPlane  # noqa: E402


def route(app, path, method):
    return next(item for item in app.routes if item.path == path and method in item.methods)


def _request(**values):
    return Mark3ProductRevenueFactoryRequest(**values)


def _all_side_effects_disabled(payload):
    for key in (
        "execution_performed",
        "external_calls_performed",
        "web_called",
        "github_called",
        "stripe_called",
        "email_sent",
        "deploy_performed",
        "domain_purchase_performed",
        "publication_performed",
        "checkout_created",
        "payment_processed",
        "money_moved",
        "credentials_used",
        "providers_called",
        "hermes_called",
        "approval_gateway_called",
    ):
        assert payload[key] is False


def test_status_is_safe_prepare_only_and_lists_required_endpoints():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    status = route(app, "/mark-3/product-revenue/status", "GET").endpoint()

    assert status["available"] is True
    assert status["prepare_only"] is True
    assert status["control_plane_only"] is True
    assert status["safe_to_render"] is True
    assert status["financial_fields"] == list(FINANCIAL_FIELDS)
    for invariant in (
        "no_fake_revenue",
        "no_fake_costs",
        "candidate_is_not_publication",
        "candidate_is_not_payment",
        "candidate_is_not_deploy",
        "approval_is_not_execution",
    ):
        assert status[invariant] is True
        assert status["invariants"][invariant] is True
    _all_side_effects_disabled(status)
    assert "POST /mark-3/product-revenue/opportunity" in status["endpoints"]
    assert "POST /mark-3/product-revenue/decision" in status["endpoints"]


def test_opportunity_candidate_has_required_control_plane_fields_without_side_effects():
    candidate = Mark3ProductRevenueFactory(id_factory=lambda: "fixed-id").opportunity({
        "opportunity": "Agency reporting risk signals",
        "niche": "small agencies",
        "target_customer": "agency owners",
        "problem": "client churn risk is found too late",
        "value_proposition": "weekly risk deltas",
    })

    for key in (
        "risk_level",
        "approval_required",
        "required_approval_level",
        "scope",
        "budget_limit",
        "assumptions",
        "evidence_required",
        "stop_conditions",
        "next_safe_action",
        "audit_summary",
    ):
        assert key in candidate
    assert candidate["candidate_type"] == "opportunity"
    assert candidate["candidate_state"] == "prepared_candidate"
    assert candidate["niche_validation"]["market_demand_confirmed"] is False
    assert candidate["approval_required"] is False
    assert candidate["required_approval_level"] == "direct"
    _all_side_effects_disabled(candidate)


def test_blueprint_contains_monetization_evidence_pricing_unit_economics_and_measurement():
    candidate = Mark3ProductRevenueFactory().blueprint({
        "product_name": "Agency Signal",
        "target_customer": "small agencies",
        "problem": "weekly client reporting misses churn signals",
        "value_proposition": "show client-risk changes before the weekly report",
        "differentiation": "change-focused risk signals instead of generic dashboards",
        "mvp_scope": ["capture weekly status", "show risk deltas"],
        "pricing_hypothesis": "Starter tier may be tested at 19 EUR/month",
        "pricing_tiers": ["Starter 19 EUR/month"],
        "evidence_required": ["five agency interviews", "one willingness-to-pay signal"],
        "monthly_price": 19,
        "expected_customers": 5,
    })

    assert candidate["product_blueprint"]["quality_gate_passed"] is True
    assert candidate["product_blueprint"]["generic_template_used"] is False
    assert candidate["offer_landing_candidate"]["would_publish"] is False
    assert candidate["pricing_candidate"]["would_create_checkout"] is False
    assert candidate["pricing_candidate"]["projected_revenue"] == 95.0
    assert candidate["unit_economics"]["not_confirmed_results"] is True
    assert candidate["revenue_model"]["would_call_stripe"] is False
    assert candidate["measurement_plan"]["no_external_analytics_calls"] is True
    assert candidate["evidence_required"] == ["five agency interviews", "one willingness-to-pay signal"]


def test_pricing_and_revenue_fields_use_unknown_when_evidence_is_missing():
    candidate = Mark3ProductRevenueFactory().blueprint({
        "product_name": "Unknown Revenue Tool",
        "mvp_scope": ["manual validation"],
        "differentiation": "specific workflow evidence required",
    })

    for field in FINANCIAL_FIELDS:
        assert candidate[field] == "unknown"
    assert candidate["financial_summary"]["unknown_when_missing_evidence"] is True
    assert candidate["confirmed_revenue"] == "unknown"
    assert candidate["expenses"] == "unknown"
    assert candidate["unit_economics"]["cac"] == "unknown"
    assert candidate["unit_economics"]["ltv"] == "unknown"


def test_financial_fields_remain_separate_and_net_uses_only_explicit_values():
    candidate = Mark3ProductRevenueFactory().blueprint({
        "projected_revenue": "operator projection: 500 EUR MRR",
        "confirmed_revenue": "operator ledger: 120 EUR",
        "confirmed_revenue_explicitly_provided": True,
        "gross_revenue": 150,
        "gross_revenue_explicitly_provided": True,
        "expenses": 40,
        "expenses_explicitly_provided": True,
    })

    assert candidate["projected_revenue"] == "operator projection: 500 EUR MRR"
    assert candidate["confirmed_revenue"] == "operator ledger: 120 EUR"
    assert candidate["gross_revenue"] == 150.0
    assert candidate["expenses"] == 40.0
    assert candidate["net_revenue"] == 110.0
    assert candidate["financial_summary"]["financial_evidence"]["net_revenue"] == "calculated_from_operator_provided_gross_revenue_and_expenses"


def test_implicit_confirmed_revenue_or_expenses_are_not_counted():
    candidate = Mark3ProductRevenueFactory().blueprint({
        "confirmed_revenue": "999 EUR",
        "gross_revenue": 999,
        "expenses": 12,
    })

    assert candidate["confirmed_revenue"] == "unknown"
    assert candidate["gross_revenue"] == "unknown"
    assert candidate["expenses"] == "unknown"
    assert candidate["net_revenue"] == "unknown"
    assert candidate["no_fake_revenue"] is True
    assert candidate["no_fake_costs"] is True


def test_fake_revenue_or_fake_cost_requests_are_blocked():
    revenue = Mark3ProductRevenueFactory().opportunity({"opportunity": "invent revenue for this niche"})
    costs = Mark3ProductRevenueFactory().opportunity({"opportunity": "fabricate costs for the deck"})

    assert revenue["execution_status"] == "blocked"
    assert "fake_revenue_request_blocked" in revenue["blocked_reasons"]
    assert revenue["permanent_denial"] is True
    assert costs["execution_status"] == "blocked"
    assert "fake_cost_request_blocked" in costs["blocked_reasons"]
    assert costs["permanent_denial"] is True


def test_sensitive_credentials_are_redacted_blocked_and_not_low_risk():
    candidate = Mark3ProductRevenueFactory().opportunity({
        "opportunity": "paid workflow using api key abc123-sensitive",
        "api_key": "abc123-sensitive",
    })
    serialized = json.dumps(candidate).lower()

    assert candidate["execution_status"] == "blocked"
    assert candidate["risk_level"] == "denied"
    assert "credentials_or_sensitive_input_redacted" in candidate["blocked_reasons"]
    assert "credentials_or_env_access_blocked" in candidate["blocked_reasons"]
    assert candidate["credentials_used"] is False
    assert "abc123-sensitive" not in serialized


def test_stripe_live_payment_deploy_domain_production_and_identity_require_level_4():
    candidate = Mark3ProductRevenueFactory().experiment({
        "experiment_name": "paid launch",
        "stripe_live_requested": True,
        "checkout_requested": True,
        "payment_requested": True,
        "money_movement_requested": True,
        "production_requested": True,
        "domain_requested": True,
        "identity_requested": True,
        "publish_requested": True,
    })

    assert candidate["risk_level"] == "critical"
    assert candidate["risk_level_number"] == 4
    assert candidate["approval_required"] is True
    assert candidate["required_approval_level"] == "level_4_strong_double_or_triple"
    assert candidate["strong_approval_required"] is True
    assert candidate["double_confirmation_required"] is True
    assert candidate["triple_confirmation_required"] is True
    assert "stripe_live" in candidate["critical_requested_actions"]
    assert "domain_or_dns" in candidate["critical_requested_actions"]
    assert candidate["approval_requirements"]["approval_grants_execution"] is False
    assert candidate["rollback_or_stop_plan"]["required"] is True
    _all_side_effects_disabled(candidate)


def test_no_web_github_stripe_email_or_deploy_real_side_effects(monkeypatch):
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
    candidate = route(app, "/mark-3/product-revenue/experiment", "POST").endpoint(
        _request(
            experiment_name="external setup candidate",
            product_name="Stripe provider setup for external review",
            web_requested=True,
            github_requested=True,
            provider_requested=True,
            external_email_requested=True,
            external_deploy_requested=True,
        )
    )
    module_source = inspect.getsource(__import__("jarvis.mark_3_product_revenue_factory", fromlist=["x"]))

    assert candidate["execution_status"] == "setup_required_for_external_capability"
    assert {"web_research", "github_research", "stripe_provider", "email_provider", "deploy_provider"} <= set(candidate["setup_gated_actions"])
    _all_side_effects_disabled(candidate)
    assert "import requests" not in module_source
    assert "subprocess" not in module_source
    assert "socket" not in module_source


def test_product_revenue_api_has_no_dangerous_execute_pay_deploy_send_publish_endpoints():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    routes = {item.path for item in app.routes if item.path.startswith("/mark-3/product-revenue")}

    assert routes == {
        "/mark-3/product-revenue/status",
        "/mark-3/product-revenue/opportunity",
        "/mark-3/product-revenue/blueprint",
        "/mark-3/product-revenue/experiment",
        "/mark-3/product-revenue/decision",
    }
    for path in routes:
        for forbidden in ("/execute", "/pay", "/deploy", "/send", "/publish", "/checkout"):
            assert forbidden not in path


def test_decision_recommendation_uses_evidence_and_does_not_claim_revenue():
    hold = Mark3ProductRevenueFactory().decision({
        "product_name": "Agency Signal",
        "success_metrics": ["three qualified interviews"],
    })
    continue_candidate = Mark3ProductRevenueFactory().decision({
        "product_name": "Agency Signal",
        "success_metrics": ["three qualified interviews"],
        "evidence": ["three qualified interviews completed"],
        "evidence_explicitly_provided": True,
        "evidence_state": "verified",
        "success_metrics_met": True,
    })
    killed = Mark3ProductRevenueFactory().decision({
        "product_name": "Agency Signal",
        "stop_conditions_met": True,
    })

    assert hold["kill_continue_recommendation"]["recommendation"] == "hold_for_evidence"
    assert continue_candidate["kill_continue_recommendation"]["recommendation"] == "continue"
    assert killed["kill_continue_recommendation"]["recommendation"] == "kill"
    assert hold["kill_continue_recommendation"]["no_revenue_claim_made"] is True


def test_docs_and_handoff_are_updated_for_pr_138_product_revenue_factory():
    product_doc = Path("docs/jarvis-mark-3-product-revenue-factory.md").read_text(encoding="utf-8")
    master = Path("docs/JARVIS_MASTER_BUILD_MAP.md").read_text(encoding="utf-8")
    roadmap = Path("docs/jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md").read_text(encoding="utf-8")
    handoff = Path("docs/jarvis-handoff-context.md").read_text(encoding="utf-8")
    serialized = "\n".join([product_doc, master, roadmap, handoff]).lower()

    assert "pr #138" in serialized
    assert "product/revenue factory" in serialized
    assert "projected_revenue" in serialized
    assert "confirmed_revenue" in serialized
    assert "gross_revenue" in serialized
    assert "expenses" in serialized
    assert "net_revenue" in serialized
    assert "no_fake_revenue" in serialized
    assert "no_fake_costs" in serialized
    assert "local docs/repo research adapter" in serialized


def test_pr_137_local_docs_repo_research_adapter_still_reads_exact_allowed_file(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("PR 137 local adapter evidence\n", encoding="utf-8")
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
    assert "PR 137 local adapter evidence" in result["local_read_result"]["content"]
    assert result["github_called"] is False
    assert result["web_called"] is False
