from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.approval_execution_semantics import ARCHITECTURAL_RULE, GlobalApprovalExecutionSemantics
from jarvis.payment_approval_control import BudgetGuard, PaymentApprovalControl, StripeReadinessPreview
from jarvis.pricing_strategy import PricingPlan
from jarvis.revenue_modeling import RevenueProjection, UnitEconomicsProjection


NEXT_RECOMMENDED_MACRO_PR = "Post-S Macro 9 — SaaS/Product Builder + Publishing/Deploy Execution"
_ACTIONS = {
    "create_pricing",
    "estimate_revenue",
    "evaluate_budget",
    "prepare_stripe_test_catalog",
    "prepare_checkout_preview",
    "prepare_subscription_plan",
    "prepare_usage_limits",
    "prepare_marketing_offer",
    "request_payment_approval",
    "approve_payment_candidate",
    "reject_payment_candidate",
}


@dataclass(frozen=True)
class MonetizationEngineStatus:
    monetization_engine_available: bool = True
    pricing_strategy_available: bool = True
    revenue_modeling_available: bool = True
    budget_guard_available: bool = True
    payment_approval_control_available: bool = True
    stripe_readiness_available: bool = True
    live_payments_enabled: bool = False
    real_charges_enabled: bool = False
    real_spend_enabled: bool = False
    external_payment_provider_calls_enabled: bool = False
    execution_requires_valid_approval: bool = True
    critical_money_actions_require_double_confirmation: bool = True
    restrictions_are_approval_gates: bool = True
    permanent_denial_for_illegal_unsafe_unauthorized_impossible_unsupported: bool = True
    current_mark: str = "Mark 1"
    next_recommended_macro_pr: str = NEXT_RECOMMENDED_MACRO_PR

    def __post_init__(self) -> None:
        for name in (
            "monetization_engine_available", "pricing_strategy_available", "revenue_modeling_available",
            "budget_guard_available", "payment_approval_control_available", "stripe_readiness_available",
            "execution_requires_valid_approval", "critical_money_actions_require_double_confirmation",
            "restrictions_are_approval_gates",
            "permanent_denial_for_illegal_unsafe_unauthorized_impossible_unsupported",
        ):
            object.__setattr__(self, name, True)
        for name in ("live_payments_enabled", "real_charges_enabled", "real_spend_enabled", "external_payment_provider_calls_enabled"):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "current_mark", "Mark 1")
        object.__setattr__(self, "next_recommended_macro_pr", NEXT_RECOMMENDED_MACRO_PR)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MonetizationActionPreview:
    action_type: str
    preview_only: bool = True
    would_execute: bool = False
    would_call_external: bool = False
    would_charge_real_money: bool = False
    would_spend_real_money: bool = False
    approval_required: bool = False
    strong_approval_required: bool = False
    double_confirmation_required: bool = False
    eligible_after_valid_approval: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    next_safe_step: str = "review preview"

    def __post_init__(self) -> None:
        object.__setattr__(self, "preview_only", True)
        for name in ("would_execute", "would_call_external", "would_charge_real_money", "would_spend_real_money"):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "blocked_reasons", list(self.blocked_reasons))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def monetization_markers() -> Dict[str, bool]:
    return {
        "post_s_monetization_engine_real": True,
        "pricing_strategy_available": True,
        "revenue_modeling_available": True,
        "budget_guard_available": True,
        "payment_approval_control_available": True,
        "stripe_readiness_available": True,
        "real_money_movement_disabled": True,
        "external_payment_calls_disabled": True,
        "live_payments_disabled_by_default": True,
        "money_actions_blocked_without_approval": True,
        "money_actions_executable_after_valid_approval": True,
        "live_money_actions_require_strong_approval": True,
        "critical_money_actions_require_double_confirmation": True,
        "revenue_estimates_not_confirmed": True,
        "no_real_money_moved": True,
        "monetization_mark_1": True,
    }


class MonetizationEngine:
    def __init__(self, semantics: Optional[GlobalApprovalExecutionSemantics] = None) -> None:
        self.semantics = semantics or GlobalApprovalExecutionSemantics()
        self.payment_control = PaymentApprovalControl(self.semantics)

    def status(self) -> Dict[str, Any]:
        return {
            **MonetizationEngineStatus().to_dict(),
            "real_money_movement_enabled": False,
            "money_actions_blocked_without_approval": True,
            "money_actions_executable_after_valid_approval": True,
            "live_payments_require_strong_approval": True,
            "live_payments_require_double_confirmation": True,
            "real_spend_requires_budget_gate": True,
            "revenue_estimates_are_not_confirmed": True,
            "stripe_live_disabled_by_default": True,
            "external_payment_calls_disabled": True,
            "no_real_money_moved": True,
        }

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            "architectural_rule": ARCHITECTURAL_RULE,
            "default_deny_without_valid_approval": True,
            "approval_hardening_is_authority": True,
            "controlled_runtime_bridge_is_readiness_only_for_payments": True,
            "tool_layer_does_not_invoke_payment_providers": True,
            "wake_phrase_is_not_payment_permission": True,
            "scheduler_due_is_not_spend_permission": True,
            "memory_active_is_not_monetization_permission": True,
            "estimates_must_not_be_presented_as_confirmed_revenue": True,
            "no_income_guarantees": True,
        }

    def preview_pricing(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return PricingPlan.from_request(data).to_dict()

    def preview_revenue(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return RevenueProjection.from_request(data).to_dict()

    def preview_budget(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return BudgetGuard.from_request(data).to_dict()

    def preview_payment_approval(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return self.payment_control.preview(data).to_dict()

    def preview_stripe_readiness(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return StripeReadinessPreview.from_request(data).to_dict()

    def preview_unit_economics(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return UnitEconomicsProjection.from_request(data).to_dict()

    def preview_action(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        source = dict(data or {})
        action = str(source.get("action_type") or "unknown").strip().lower()
        supported = action in _ACTIONS
        money_action = action in {"request_payment_approval", "approve_payment_candidate", "reject_payment_candidate"}
        critical = action == "approve_payment_candidate"
        valid = source.get("valid_approval_present") is True
        strong = source.get("strong_approval_present") is True
        double = source.get("double_confirmation_present") is True
        eligible = supported and (not money_action or (valid and (not critical or (strong and double))))
        blocked = []
        if not supported:
            blocked.append("unsupported monetization preview action")
        if money_action and not valid:
            blocked.append("valid explicit approval required")
        if critical and not strong:
            blocked.append("valid strong approval required")
        if critical and not double:
            blocked.append("double confirmation required")
        blocked.append("monetization execution is disabled in this PR")
        return MonetizationActionPreview(
            action_type=action,
            approval_required=money_action,
            strong_approval_required=critical,
            double_confirmation_required=critical,
            eligible_after_valid_approval=eligible,
            blocked_reasons=blocked,
            next_safe_step="review the preview and obtain required approval gates" if supported else "choose a supported preview action",
        ).to_dict()
