from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import math
from typing import Any, Callable, Dict, Iterable, List, Optional
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data
from jarvis.mark_3_mission_loop_models import UNKNOWN
from jarvis.mark_3_negative_intent_parser import (
    payload_has_actionable_marker,
    payload_text,
    redact_mark_3_payload,
)


FACTORY_ENDPOINTS = (
    "GET /mark-3/product-revenue/status",
    "POST /mark-3/product-revenue/opportunity",
    "POST /mark-3/product-revenue/blueprint",
    "POST /mark-3/product-revenue/experiment",
    "POST /mark-3/product-revenue/decision",
)
FINANCIAL_FIELDS = (
    "projected_revenue",
    "confirmed_revenue",
    "gross_revenue",
    "expenses",
    "net_revenue",
)
INVARIANTS = {
    "no_fake_revenue": True,
    "no_fake_costs": True,
    "candidate_is_not_publication": True,
    "candidate_is_not_payment": True,
    "candidate_is_not_deploy": True,
    "approval_is_not_execution": True,
}
SIDE_EFFECT_FLAGS = {
    "execution_performed": False,
    "external_calls_performed": False,
    "web_called": False,
    "github_called": False,
    "stripe_called": False,
    "email_sent": False,
    "deploy_performed": False,
    "domain_purchase_performed": False,
    "publication_performed": False,
    "checkout_created": False,
    "payment_processed": False,
    "money_moved": False,
    "credentials_used": False,
    "providers_called": False,
    "hermes_called": False,
    "approval_gateway_called": False,
}
LEVEL_4_ACTIONS = (
    "stripe_live",
    "real_checkout",
    "payment_processing",
    "money_movement",
    "production",
    "domain_or_dns",
    "real_publication",
    "real_email_send",
    "david_identity",
)
EXTERNAL_SETUP_GATED_ACTIONS = (
    "web_research",
    "github_research",
    "stripe_provider",
    "email_provider",
    "deploy_provider",
)


@dataclass(frozen=True)
class ProductRevenueAuditEvent:
    event_id: str
    event_type: str
    created_at: str
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    redacted_fields: List[str] = field(default_factory=list)
    safe_to_execute: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark3ProductRevenueFactory:
    """Prepare-only Product/Revenue Factory for Mark 3.

    This control-plane builds reviewable candidates. It does not publish, deploy,
    create checkouts, call providers, move money, send email, use credentials, or
    invoke Hermes.
    """

    def __init__(
        self,
        *,
        clock: Optional[Callable[[], str]] = None,
        id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        self.clock = clock or now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self._candidates: Dict[str, Dict[str, Any]] = {}
        self._audit: List[ProductRevenueAuditEvent] = []

    def status(self) -> Dict[str, Any]:
        return {
            "available": True,
            "mark": "Mark 3",
            "factory": "product_revenue_factory",
            "prepare_only": True,
            "control_plane_only": True,
            "in_memory_only": True,
            "candidate_count": len(self._candidates),
            "audit_event_count": len(self._audit),
            "endpoints": list(FACTORY_ENDPOINTS),
            "financial_fields": list(FINANCIAL_FIELDS),
            "invariants": dict(INVARIANTS),
            **INVARIANTS,
            **SIDE_EFFECT_FLAGS,
            "safe_to_render": True,
            "can_prepare_opportunity_candidates": True,
            "can_prepare_blueprint_candidates": True,
            "can_prepare_experiment_candidates": True,
            "can_prepare_kill_continue_decisions": True,
            "no_real_web_github_stripe_email_deploy": True,
            "no_checkout_or_payment_creation": True,
            "no_publication_or_domain_purchase": True,
            "no_credentials_or_env_access": True,
            "hermes_remains_execution_engine": True,
            "jarvis_governs_risk_approval_audit": True,
            "approval_requirements_by_risk": approval_requirements_by_risk(),
            "level_4_critical_actions": list(LEVEL_4_ACTIONS),
        }

    def opportunity(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate("opportunity", values)
        candidate.update({
            "opportunity_candidate": {
                "opportunity": _text(_first_present(candidate["input"], "opportunity", "idea", "product_idea")) or UNKNOWN,
                "niche": _text(_first_present(candidate["input"], "niche", "market", "audience")) or UNKNOWN,
                "target_customer": _text(candidate["input"].get("target_customer")) or UNKNOWN,
                "problem": _text(candidate["input"].get("problem")) or UNKNOWN,
                "value_proposition": _text(candidate["input"].get("value_proposition")) or UNKNOWN,
                "expected_value": _text(candidate["input"].get("expected_value")) or UNKNOWN,
                "confidence": _choice(candidate["input"].get("confidence"), {"low", "medium", "high"}, UNKNOWN),
                "opportunity_score": _explicit_or_unknown(candidate["input"], "opportunity_score", "opportunity_score_explicitly_provided"),
                "source_evidence_state": _evidence_state(candidate["input"]),
            },
            "niche_validation": _niche_validation(candidate["input"], candidate["evidence_required"]),
        })
        return self._store(candidate)

    def blueprint(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate("blueprint", values)
        candidate.update({
            "product_blueprint": _product_blueprint(candidate["input"]),
            "offer_landing_candidate": _offer_landing_candidate(candidate["input"]),
            "pricing_candidate": _pricing_candidate(candidate["input"], candidate["financial_summary"]),
            "unit_economics": _unit_economics(candidate["input"]),
            "revenue_model": _revenue_model(candidate["input"], candidate["financial_summary"]),
            "measurement_plan": _measurement_plan(candidate["input"]),
        })
        return self._store(candidate)

    def experiment(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate("experiment", values)
        candidate.update({
            "experiment_plan": _experiment_plan(candidate["input"], candidate),
            "measurement_plan": _measurement_plan(candidate["input"]),
            "rollback_or_stop_plan": _rollback_or_stop_plan(candidate["input"], candidate["critical_requested_actions"]),
        })
        return self._store(candidate)

    def decision(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate("decision", values)
        recommendation = _kill_continue_recommendation(candidate["input"], candidate)
        candidate.update({
            "kill_continue_recommendation": recommendation,
            "decision_evidence": {
                "evidence_state": _evidence_state(candidate["input"]),
                "observed_metrics": _observed_metrics(candidate["input"]),
                "missing_evidence": _missing_evidence(candidate["input"], candidate["evidence_required"]),
                "financial_summary": candidate["financial_summary"],
            },
            "measurement_plan": _measurement_plan(candidate["input"]),
        })
        return self._store(candidate)

    def list_candidates(self) -> List[Dict[str, Any]]:
        return list(self._candidates.values())

    def audit(self) -> Dict[str, Any]:
        return {
            "append_only": True,
            "in_memory_only": True,
            "safe_to_execute": False,
            "events": [item.to_dict() for item in self._audit],
        }

    def _base_candidate(self, candidate_type: str, values: Dict[str, Any]) -> Dict[str, Any]:
        raw_input = dict(values or {})
        safe_input, redacted_fields = redact_mark_3_payload(raw_input)
        blocked_reasons = _blocked_reasons(raw_input, redacted_fields)
        risk = classify_product_revenue_risk(raw_input)
        if _permanent_denial(blocked_reasons):
            risk = {"risk_level": "denied", "risk_level_number": 5}
        elif blocked_reasons and risk["risk_level_number"] < 3:
            risk = {"risk_level": "high", "risk_level_number": 3}
        approval = approval_requirements_for(raw_input, risk)
        financials = _financial_summary(safe_input)
        evidence_required = _evidence_required(candidate_type, safe_input)
        critical_actions = _critical_requested_actions(raw_input)
        setup_gated_actions = _setup_gated_actions(raw_input)
        candidate_id = _text(safe_input.get("candidate_id")) or self.id_factory()
        created_at = self.clock()
        candidate_state = "blocked" if blocked_reasons else "prepared_candidate"
        execution_status = "blocked" if blocked_reasons else "prepared"
        if not blocked_reasons and critical_actions:
            execution_status = "awaiting_level_4_approval_for_any_real_side_effect"
        elif not blocked_reasons and setup_gated_actions:
            execution_status = "setup_required_for_external_capability"

        candidate = {
            "candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "created_at": created_at,
            "input": safe_input,
            "redacted_fields": redacted_fields,
            "candidate_state": candidate_state,
            "execution_status": execution_status,
            "control_plane_only": True,
            "prepare_only": True,
            "safe_to_execute": False,
            "risk_level": risk["risk_level"],
            "risk_level_number": risk["risk_level_number"],
            "approval_required": approval["approval_required"],
            "required_approval_level": approval["required_approval_level"],
            "approval_requirements": approval,
            "approval_requirements_by_risk": approval_requirements_by_risk(),
            "strong_approval_required": approval["strong_approval_required"],
            "double_confirmation_required": approval["double_confirmation_required"],
            "triple_confirmation_required": approval["triple_confirmation_required"],
            "scope": _scope(safe_input),
            "budget_limit": _budget_limit(safe_input),
            "assumptions": _assumptions(candidate_type, safe_input),
            "evidence_required": evidence_required,
            "expected_evidence": evidence_required,
            "stop_conditions": _stop_conditions(candidate_type, safe_input, critical_actions),
            "next_safe_action": _next_safe_action(candidate_type, approval, critical_actions, setup_gated_actions, blocked_reasons),
            "audit_summary": _audit_summary(candidate_type, critical_actions, setup_gated_actions, blocked_reasons),
            "critical_requested_actions": critical_actions,
            "setup_gated_actions": setup_gated_actions,
            "blocked_reasons": blocked_reasons,
            "permanent_denial": _permanent_denial(blocked_reasons),
            "financial_summary": financials,
            **financials,
            "invariants": dict(INVARIANTS),
            **INVARIANTS,
            **SIDE_EFFECT_FLAGS,
            "candidate_can_execute": False,
            "candidate_can_publish": False,
            "candidate_can_deploy": False,
            "candidate_can_create_checkout": False,
            "candidate_can_process_payment": False,
            "candidate_can_send_email": False,
            "candidate_can_buy_domain": False,
            "candidate_can_use_david_identity": False,
            "external_provider_capabilities_connected": False,
            "web_github_stripe_email_deploy_connected": False,
            "hermes_is_execution_engine": True,
            "jarvis_governs_decides_approves_audits": True,
            "no_duplicate_hermes_runtime": True,
            "no_income_guarantees": True,
            "no_fake_metrics": True,
            "approval_is_gate_not_permanent_ban": True,
        }
        return candidate

    def _store(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        self._candidates[candidate["candidate_id"]] = candidate
        self._append_audit(
            "product_revenue_candidate_prepared",
            candidate["audit_summary"],
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_type": candidate["candidate_type"],
                "risk_level": candidate["risk_level"],
                "required_approval_level": candidate["required_approval_level"],
                "execution_status": candidate["execution_status"],
            },
        )
        return candidate

    def _append_audit(self, event_type: str, summary: str, metadata: Dict[str, Any]) -> None:
        safe, redacted = redact_sensitive_data(metadata)
        self._audit.append(ProductRevenueAuditEvent(
            event_id=self.id_factory(),
            event_type=event_type,
            created_at=self.clock(),
            summary=summary,
            metadata=safe,
            redacted_fields=redacted,
        ))


def classify_product_revenue_risk(values: Dict[str, Any]) -> Dict[str, Any]:
    blocked = _blocked_reasons(values, [])
    critical_actions = _critical_requested_actions(values)
    setup_gated = _setup_gated_actions(values)
    budget = _number(_first_present(values, "budget_limit", "max_budget", "experiment_budget"))
    if _permanent_denial(blocked):
        return {"risk_level": "denied", "risk_level_number": 5}
    if critical_actions:
        return {"risk_level": "critical", "risk_level_number": 4}
    if setup_gated:
        return {"risk_level": "high", "risk_level_number": 3}
    if budget not in (None, 0):
        return {"risk_level": "medium", "risk_level_number": 2}
    return {"risk_level": "low", "risk_level_number": 1}


def approval_requirements_for(values: Dict[str, Any], risk: Dict[str, Any]) -> Dict[str, Any]:
    critical_actions = _critical_requested_actions(values)
    setup_gated = _setup_gated_actions(values)
    risk_number = int(risk["risk_level_number"])
    if risk_number == 5:
        required_level = "level_5_denied"
    elif critical_actions:
        required_level = "level_4_strong_double_or_triple"
    elif risk_number >= 3 or setup_gated:
        required_level = "strong"
    elif risk_number == 2:
        required_level = "simple"
    else:
        required_level = "direct"

    triple = any(action in critical_actions for action in {
        "stripe_live",
        "real_checkout",
        "payment_processing",
        "money_movement",
        "production",
        "domain_or_dns",
        "david_identity",
    })
    double = bool(critical_actions)
    return {
        "approval_required": required_level not in {"direct", "level_5_denied"},
        "required_approval_level": required_level,
        "prepare_candidate_approval_level": "direct",
        "strong_approval_required": required_level in {"strong", "level_4_strong_double_or_triple"},
        "double_confirmation_required": double,
        "triple_confirmation_required": triple,
        "readback_required": bool(critical_actions),
        "rollback_or_stop_plan_required": bool(critical_actions),
        "candidate_preparation_executes": False,
        "approval_grants_execution": False,
        "critical_actions_requiring_level_4": critical_actions,
        "setup_gated_actions": setup_gated,
        "level_4_requires": [
            "exact action readback",
            "strong approval",
            "double confirmation",
            "triple confirmation for very high risk money, production, domain, or identity actions",
            "budget limit",
            "rollback or stop plan",
            "audit",
            "visible human stop control",
        ] if critical_actions else [],
    }


def approval_requirements_by_risk() -> Dict[str, Dict[str, Any]]:
    return {
        "low": {
            "level": 0,
            "required_approval_level": "direct",
            "examples": ["prepare opportunity candidate", "draft assumptions", "summarize provided evidence"],
        },
        "medium": {
            "level": 2,
            "required_approval_level": "simple",
            "examples": ["bounded local file work in a future PR", "reviewable experiment budget proposal"],
        },
        "high": {
            "level": 3,
            "required_approval_level": "strong",
            "examples": ["external research capability", "private metrics review", "provider setup candidate"],
        },
        "critical": {
            "level": 4,
            "required_approval_level": "level_4_strong_double_or_triple",
            "examples": [
                "Stripe live",
                "real checkout",
                "production deploy",
                "domain or DNS",
                "real publication",
                "money movement",
                "bulk email",
                "David identity usage",
            ],
        },
        "denied": {
            "level": 5,
            "required_approval_level": "level_5_denied",
            "examples": ["fake revenue", "fake costs", "illegal or unauthorized action", "credential theft"],
        },
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _financial_summary(values: Dict[str, Any]) -> Dict[str, Any]:
    projected = _projected_revenue(values)
    confirmed = _explicit_or_unknown(values, "confirmed_revenue", "confirmed_revenue_explicitly_provided")
    gross = _explicit_or_unknown(values, "gross_revenue", "gross_revenue_explicitly_provided")
    expenses = _explicit_or_unknown(values, "expenses", "expenses_explicitly_provided")
    explicit_net = _explicit_or_unknown(values, "net_revenue", "net_revenue_explicitly_provided")
    if explicit_net != UNKNOWN:
        net = explicit_net
        net_basis = "operator_explicitly_provided"
    else:
        gross_number = _number(gross)
        expenses_number = _number(expenses)
        if gross_number is not None and expenses_number is not None:
            net = round(gross_number - expenses_number, 2)
            net_basis = "calculated_from_operator_provided_gross_revenue_and_expenses"
        else:
            net = UNKNOWN
            net_basis = UNKNOWN

    evidence = {
        "projected_revenue": _value_source(projected),
        "confirmed_revenue": _explicit_source(values, "confirmed_revenue", "confirmed_revenue_explicitly_provided"),
        "gross_revenue": _explicit_source(values, "gross_revenue", "gross_revenue_explicitly_provided"),
        "expenses": _explicit_source(values, "expenses", "expenses_explicitly_provided"),
        "net_revenue": net_basis,
    }
    return {
        "projected_revenue": projected,
        "confirmed_revenue": confirmed,
        "gross_revenue": gross,
        "expenses": expenses,
        "net_revenue": net,
        "financial_evidence": evidence,
        "unknown_when_missing_evidence": True,
        "no_fake_revenue": True,
        "no_fake_costs": True,
        "revenue_is_not_guaranteed": True,
    }


def _projected_revenue(values: Dict[str, Any]) -> Any:
    explicit = _first_present(values, "projected_revenue", "revenue_projection")
    if _has_value(explicit):
        return _safe_scalar(explicit)
    expected_customers = _number(_first_present(values, "expected_customers", "projected_customers"))
    monthly_price = _number(_first_present(values, "monthly_price", "price_amount"))
    if expected_customers is not None and monthly_price is not None:
        return round(expected_customers * monthly_price, 2)
    return UNKNOWN


def _value_source(value: Any) -> str:
    return UNKNOWN if value == UNKNOWN else "operator_supplied_or_calculated_from_operator_inputs"


def _explicit_source(values: Dict[str, Any], key: str, flag: str) -> str:
    return "operator_explicitly_provided" if values.get(flag) is True and _has_value(values.get(key)) else UNKNOWN


def _explicit_or_unknown(values: Dict[str, Any], key: str, flag: str) -> Any:
    if values.get(flag) is True and _has_value(values.get(key)):
        return _safe_scalar(values.get(key))
    return UNKNOWN


def _product_blueprint(values: Dict[str, Any]) -> Dict[str, Any]:
    mvp_scope = _items(values.get("mvp_scope"))[:10]
    unknowns = _items(values.get("unknowns"))
    if not mvp_scope:
        unknowns.append("concrete MVP scope")
    if not _text(values.get("differentiation")):
        unknowns.append("differentiation")
    return {
        "product_name": _text(values.get("product_name")) or UNKNOWN,
        "target_customer": _text(values.get("target_customer")) or UNKNOWN,
        "core_problem": _text(values.get("problem")) or UNKNOWN,
        "value_proposition": _text(values.get("value_proposition")) or UNKNOWN,
        "differentiation": _text(values.get("differentiation")) or UNKNOWN,
        "mvp_scope": mvp_scope,
        "out_of_scope": _items(values.get("out_of_scope")) or [
            "real checkout creation",
            "production deploy",
            "domain purchase",
            "publication as David",
        ],
        "risks": _items(values.get("risks")),
        "unknowns": _unique(unknowns),
        "quality_gate_passed": bool(mvp_scope and _text(values.get("differentiation"))),
        "generic_template_used": False,
        "product_specificity_required": True,
    }


def _offer_landing_candidate(values: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "offer_name": _text(_first_present(values, "offer_name", "product_name")) or UNKNOWN,
        "headline": _text(values.get("headline")) or UNKNOWN,
        "target_customer": _text(values.get("target_customer")) or UNKNOWN,
        "promise_or_value_proposition": _text(_first_present(values, "promise", "value_proposition")) or UNKNOWN,
        "call_to_action": _text(values.get("call_to_action")) or "join validation list",
        "trust_requirements": _items(values.get("trust_requirements")) or [
            "no fabricated social proof",
            "no income guarantees",
            "claims must be supported by evidence before publication",
        ],
        "publish_ready": False,
        "would_publish": False,
        "would_use_david_identity": False,
    }


def _pricing_candidate(values: Dict[str, Any], financials: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "pricing_hypothesis": _text(values.get("pricing_hypothesis")) or UNKNOWN,
        "pricing_tiers": _items(values.get("pricing_tiers")),
        "price_amount": _number(_first_present(values, "price_amount", "monthly_price")) if _has_value(_first_present(values, "price_amount", "monthly_price")) else UNKNOWN,
        "currency": (_text(values.get("currency")) or UNKNOWN).upper() if _text(values.get("currency")) else UNKNOWN,
        "billing_interval": _choice(values.get("billing_interval"), {"monthly", "yearly", "one_time", "usage_based"}, UNKNOWN),
        "projected_revenue": financials["projected_revenue"],
        "confirmed_revenue": financials["confirmed_revenue"],
        "validation_needed": True,
        "would_charge_real_money": False,
        "would_create_checkout": False,
        "live_billing_enabled": False,
    }


def _unit_economics(values: Dict[str, Any]) -> Dict[str, Any]:
    acquisition_spend = _number(values.get("acquisition_spend"))
    acquired_customers = _number(values.get("acquired_customers"))
    monthly_revenue_per_customer = _number(_first_present(values, "monthly_revenue_per_customer", "monthly_price"))
    gross_margin_rate = _rate(values.get("gross_margin_rate"))
    monthly_churn_rate = _rate(values.get("monthly_churn_rate"))
    cac = round(acquisition_spend / acquired_customers, 2) if acquisition_spend is not None and acquired_customers not in (None, 0) else UNKNOWN
    gross_margin = (
        round(monthly_revenue_per_customer * gross_margin_rate, 2)
        if monthly_revenue_per_customer is not None and gross_margin_rate is not None
        else UNKNOWN
    )
    ltv = round(gross_margin / monthly_churn_rate, 2) if isinstance(gross_margin, (int, float)) and monthly_churn_rate not in (None, 0) else UNKNOWN
    payback = round(cac / gross_margin, 2) if isinstance(cac, (int, float)) and isinstance(gross_margin, (int, float)) and gross_margin != 0 else UNKNOWN
    unknowns = []
    for value, label in (
        (acquisition_spend, "acquisition_spend"),
        (acquired_customers, "acquired_customers"),
        (monthly_revenue_per_customer, "monthly_revenue_per_customer"),
        (gross_margin_rate, "gross_margin_rate"),
        (monthly_churn_rate, "monthly_churn_rate"),
    ):
        if value is None:
            unknowns.append(label)
    return {
        "cac": cac,
        "gross_margin": gross_margin,
        "ltv": ltv,
        "payback_period_months": payback,
        "unknowns": unknowns,
        "not_confirmed_results": True,
    }


def _revenue_model(values: Dict[str, Any], financials: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "model_type": _text(_first_present(values, "revenue_model", "business_model")) or UNKNOWN,
        "monetization_path": _text(values.get("monetization_path")) or UNKNOWN,
        "pricing_basis": _text(values.get("pricing_basis")) or UNKNOWN,
        "financial_summary": financials,
        "required_evidence_before_counting_revenue": [
            "confirmed payment/provider export or ledger entry",
            "operator-provided source for gross revenue",
            "operator-provided source for expenses",
            "calculation showing net revenue from gross revenue minus expenses",
        ],
        "would_create_checkout": False,
        "would_call_stripe": False,
        "would_move_money": False,
    }


def _niche_validation(values: Dict[str, Any], evidence_required: List[str]) -> Dict[str, Any]:
    return {
        "niche": _text(_first_present(values, "niche", "market", "audience")) or UNKNOWN,
        "validation_questions": _items(values.get("validation_questions")) or [
            "Who has the painful problem now?",
            "What manual workaround proves urgency?",
            "What evidence shows willingness to pay?",
            "What existing alternatives would this replace?",
        ],
        "evidence_required": evidence_required,
        "market_demand_confirmed": False,
        "willingness_to_pay": _explicit_or_unknown(values, "willingness_to_pay", "willingness_to_pay_explicitly_provided"),
        "recommendation": "validate_before_building",
    }


def _experiment_plan(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "experiment_name": _text(values.get("experiment_name")) or _text(values.get("product_name")) or UNKNOWN,
        "hypothesis": _text(values.get("hypothesis")) or UNKNOWN,
        "scope": candidate["scope"],
        "budget_limit": candidate["budget_limit"],
        "success_metrics": _items(values.get("success_metrics")) or ["unknown"],
        "pricing_variants": _items(values.get("pricing_variants")),
        "measurement_plan": _measurement_plan(values),
        "would_launch": False,
        "would_spend": False,
        "would_publish": False,
        "would_send_email": False,
        "would_create_checkout": False,
        "candidate_only": True,
    }


def _measurement_plan(values: Dict[str, Any]) -> Dict[str, Any]:
    metrics = _items(values.get("metrics")) or _items(values.get("success_metrics")) or [
        "qualified interest",
        "validated pain signal",
        "pricing objection",
        "conversion intent",
    ]
    return {
        "metrics": metrics,
        "baseline": _explicit_or_unknown(values, "baseline", "baseline_explicitly_provided"),
        "instrumentation": _items(values.get("instrumentation")) or ["manual tracking or approved analytics plan only"],
        "attribution_assumptions": _items(values.get("attribution_assumptions")),
        "confirmed_metrics": _observed_metrics(values),
        "no_external_analytics_calls": True,
        "no_personal_data_collection": True,
        "no_fake_metrics": True,
    }


def _rollback_or_stop_plan(values: Dict[str, Any], critical_actions: List[str]) -> Dict[str, Any]:
    steps = _items(_first_present(values, "rollback_or_stop_plan", "rollback_plan", "stop_plan"))
    if not steps:
        steps = [
            "stop before any real publication, payment, deploy, email, domain, or identity action",
            "discard the candidate or revise assumptions",
            "record outcome and evidence gaps for the next review",
        ]
    return {
        "required": bool(critical_actions),
        "steps": steps,
        "kill_switch_required_for_real_execution": bool(critical_actions),
        "candidate_has_no_runtime_to_stop": True,
    }


def _kill_continue_recommendation(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    evidence_state = _evidence_state(values)
    stop_met = values.get("stop_conditions_met") is True
    success_met = values.get("success_metrics_met") is True
    missing_evidence = _missing_evidence(values, candidate["evidence_required"])
    if candidate["blocked_reasons"]:
        recommendation = "kill_or_rewrite_request"
        reason = "request is blocked by policy or unsafe input"
    elif stop_met:
        recommendation = "kill"
        reason = "operator-provided stop conditions are met"
    elif evidence_state == "verified" and success_met and not missing_evidence:
        recommendation = "continue"
        reason = "operator-provided verified evidence satisfies the declared success metrics"
    else:
        recommendation = "hold_for_evidence"
        reason = "required evidence is missing or not verified"
    return {
        "recommendation": recommendation,
        "reason": reason,
        "evidence_state": evidence_state,
        "stop_conditions_met": stop_met,
        "success_metrics_met": success_met,
        "missing_evidence": missing_evidence,
        "next_safe_action": candidate["next_safe_action"],
        "no_revenue_claim_made": True,
    }


def _scope(values: Dict[str, Any]) -> str:
    explicit = _text(values.get("scope"))
    if explicit:
        return explicit
    product = _text(_first_present(values, "product_name", "opportunity", "idea"))
    return product or "product/revenue candidate preparation only"


def _budget_limit(values: Dict[str, Any]) -> Any:
    value = _first_present(values, "budget_limit", "max_budget", "experiment_budget")
    if not _has_value(value):
        return UNKNOWN
    number = _number(value)
    return number if number is not None else _safe_scalar(value)


def _assumptions(candidate_type: str, values: Dict[str, Any]) -> List[str]:
    assumptions = _items(values.get("assumptions"))
    if assumptions:
        return assumptions
    defaults = {
        "opportunity": ["opportunity is unvalidated until evidence is provided"],
        "blueprint": ["MVP scope and pricing remain hypotheses until validated"],
        "experiment": ["experiment will not launch from this candidate"],
        "decision": ["decision uses only operator-provided evidence"],
    }
    return defaults.get(candidate_type, ["candidate requires review"])


def _evidence_required(candidate_type: str, values: Dict[str, Any]) -> List[str]:
    explicit = _items(values.get("evidence_required"))
    if explicit:
        return explicit
    common = [
        "source of the problem signal",
        "target customer evidence",
        "willingness-to-pay evidence",
        "cost source if costs are claimed",
        "confirmed revenue source if confirmed revenue is claimed",
    ]
    by_type = {
        "opportunity": ["niche signal", "existing alternatives", "manual workaround evidence"],
        "blueprint": ["MVP acceptance criteria", "differentiation evidence", "pricing validation plan"],
        "experiment": ["hypothesis", "success metric definition", "measurement method", "stop threshold"],
        "decision": ["observed metrics", "evidence state", "stop/continue threshold"],
    }
    return _unique((by_type.get(candidate_type) or []) + common)


def _stop_conditions(candidate_type: str, values: Dict[str, Any], critical_actions: List[str]) -> List[str]:
    explicit = _items(values.get("stop_conditions"))
    if explicit:
        return explicit
    conditions = [
        "evidence remains unknown after the planned validation step",
        "costs or revenue cannot be sourced without guessing",
        "operator asks to stop",
    ]
    if critical_actions:
        conditions.append("any request attempts real payment, publication, deploy, domain, email, identity, or money movement without Level 4 approval")
    if candidate_type == "experiment":
        conditions.append("success metrics cannot be measured safely")
    return conditions


def _next_safe_action(
    candidate_type: str,
    approval: Dict[str, Any],
    critical_actions: List[str],
    setup_gated_actions: List[str],
    blocked_reasons: List[str],
) -> str:
    if blocked_reasons:
        return "rewrite the request to remove unsafe, unauthorized, secret, or fake-financial content"
    if critical_actions:
        return "review this candidate only; create a separate Level 4 strong approval flow before any real side effect"
    if setup_gated_actions:
        return "review the candidate and connect an approved governed capability in a future PR before any external call"
    if candidate_type == "decision":
        return "review the kill/continue recommendation against supplied evidence"
    return "review candidate assumptions and collect the required evidence"


def _audit_summary(candidate_type: str, critical_actions: List[str], setup_gated_actions: List[str], blocked_reasons: List[str]) -> str:
    if blocked_reasons:
        return f"Product/revenue {candidate_type} request blocked before any side effect."
    if critical_actions:
        return f"Product/revenue {candidate_type} candidate prepared; Level 4 actions were identified but not executed."
    if setup_gated_actions:
        return f"Product/revenue {candidate_type} candidate prepared; external setup-gated actions were not called."
    return f"Product/revenue {candidate_type} candidate prepared with no external execution."


def _critical_requested_actions(values: Dict[str, Any]) -> List[str]:
    checks = {
        "stripe_live": _truthy(values, "stripe_live_requested") or _action_requested(values, ("stripe live", "live stripe")),
        "real_checkout": _truthy(values, "checkout_requested") or _action_requested(values, ("create checkout", "real checkout")),
        "payment_processing": _truthy(values, "payment_requested") or _action_requested(values, ("process payment", "charge card")),
        "money_movement": _truthy(values, "money_movement_requested") or _truthy(values, "spend_requested") or _truthy(values, "budget_spend_requested") or _action_requested(values, ("move money", "spend money")),
        "production": _truthy(values, "production_requested") or _action_requested(values, ("production",)),
        "domain_or_dns": _truthy(values, "domain_requested") or _action_requested(values, ("buy domain", "dns")),
        "real_publication": _truthy(values, "publish_requested") or _action_requested(values, ("publish real", "real publication")),
        "real_email_send": _truthy(values, "email_requested") or _truthy(values, "send_requested") or _action_requested(values, ("send email", "bulk email")),
        "david_identity": _truthy(values, "identity_requested") or _action_requested(values, ("david identity", "as david", "como david")),
    }
    if _truthy(values, "deploy_requested") or _action_requested(values, ("deploy",)):
        checks["production"] = True
    return [name for name, active in checks.items() if active]


def _setup_gated_actions(values: Dict[str, Any]) -> List[str]:
    checks = {
        "web_research": _truthy(values, "web_requested") or _action_requested(values, ("web search", "call web")),
        "github_research": _truthy(values, "github_requested") or _action_requested(values, ("github",)),
        "stripe_provider": _truthy(values, "provider_requested") and _action_requested(values, ("stripe",)),
        "email_provider": _truthy(values, "external_email_requested"),
        "deploy_provider": _truthy(values, "external_deploy_requested"),
    }
    return [name for name, active in checks.items() if active]


def _blocked_reasons(values: Dict[str, Any], redacted_fields: Iterable[str]) -> List[str]:
    reasons: List[str] = []
    if redacted_fields:
        reasons.append("credentials_or_sensitive_input_redacted")
    if _action_requested(values, ("fake revenue", "invent revenue", "fabricate revenue", "inventar ingresos", "ingresos falsos")):
        reasons.append("fake_revenue_request_blocked")
    if _action_requested(values, ("fake costs", "invent costs", "fabricate costs", "inventar costes", "inventar costos", "costes falsos", "costos falsos")):
        reasons.append("fake_cost_request_blocked")
    if _action_requested(values, ("steal", "bypass 2fa", "unauthorized access", "hack account")):
        reasons.append("illegal_or_unauthorized_request_blocked")
    if _truthy(values, "secrets_requested") or _action_requested(
        values,
        (".env", "api key", "api-key", "api_key", "token", "credential", "credentials", "password", "private key", "secret"),
    ):
        reasons.append("credentials_or_env_access_blocked")
    return _unique(reasons)


def _permanent_denial(reasons: Iterable[str]) -> bool:
    permanent = {
        "fake_revenue_request_blocked",
        "fake_cost_request_blocked",
        "illegal_or_unauthorized_request_blocked",
        "credentials_or_env_access_blocked",
    }
    return any(reason in permanent for reason in reasons)


def _observed_metrics(values: Dict[str, Any]) -> Dict[str, Any]:
    metrics = values.get("observed_metrics")
    if isinstance(metrics, dict) and values.get("observed_metrics_explicitly_provided") is True:
        safe, _ = redact_sensitive_data(metrics)
        return dict(safe)
    return {}


def _missing_evidence(values: Dict[str, Any], evidence_required: List[str]) -> List[str]:
    provided = _items(values.get("evidence")) if values.get("evidence_explicitly_provided") is True else []
    if _evidence_state(values) in {"verified", "observed"} and provided:
        return []
    return list(evidence_required)


def _evidence_state(values: Dict[str, Any]) -> str:
    return _choice(values.get("evidence_state"), {"unknown", "planned", "reported", "observed", "verified"}, UNKNOWN)


def _items(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [_text(f"{key}: {item}") for key, item in value.items() if _text(f"{key}: {item}")]
    items = value if isinstance(value, list) else [value]
    return [_text(item) for item in items if _text(item)]


def _first_present(values: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = values.get(key)
        if _has_value(value):
            return value
    return None


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return round(float(value), 2) if math.isfinite(float(value)) else UNKNOWN
    return _text(value) or UNKNOWN


def _number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 4) if math.isfinite(number) and number >= 0 else None


def _rate(value: Any) -> Optional[float]:
    number = _number(value)
    return number if number is not None and number <= 1 else None


def _choice(value: Any, allowed: set[str], fallback: str) -> str:
    text = _text(value).lower()
    return text if text in allowed else fallback


def _truthy(values: Dict[str, Any], key: str) -> bool:
    value = values.get(key)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return value is True


def _combined(values: Dict[str, Any]) -> str:
    return payload_text(values)


def _flatten_text(value: Any) -> List[str]:
    if isinstance(value, dict):
        result: List[str] = []
        for item in value.values():
            result.extend(_flatten_text(item))
        return result
    if isinstance(value, (list, tuple, set)):
        result = []
        for item in value:
            result.extend(_flatten_text(item))
        return result
    return [_text(value)]


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:1000]


def _unique(items: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(item for item in items if item))


def _action_requested(values: Dict[str, Any], markers: Iterable[str]) -> bool:
    return payload_has_actionable_marker(values, markers)
