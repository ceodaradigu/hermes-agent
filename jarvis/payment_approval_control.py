from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Dict, List, Optional

from jarvis.approval_audit import redact_sensitive_data
from jarvis.approval_execution_semantics import GlobalApprovalExecutionSemantics


@dataclass(frozen=True)
class BudgetGuard:
    monthly_budget_limit: Optional[float]
    per_action_spend_limit: Optional[float]
    currency: str
    current_spend_estimate: Optional[float]
    proposed_spend: Optional[float]
    remaining_budget: Optional[float]
    budget_exceeded: bool
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    spend_allowed: bool
    blocked_reasons: List[str] = field(default_factory=list)
    warning_message: str = ""
    would_spend_real_money: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "blocked_reasons", _list(self.blocked_reasons))
        object.__setattr__(self, "spend_allowed", False)
        object.__setattr__(self, "would_spend_real_money", False)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "BudgetGuard":
        source = dict(data or {})
        monthly = _amount(source.get("monthly_budget_limit"))
        per_action = _amount(source.get("per_action_spend_limit"))
        current = _amount(source.get("current_spend_estimate"))
        proposed = _amount(source.get("proposed_spend"))
        valid_approval = source.get("valid_approval_present") is True
        blocked: List[str] = []
        if proposed is None:
            blocked.append("proposed spend is unknown")
        if not valid_approval:
            blocked.append("valid explicit approval required")
        remaining = round(monthly - (current or 0) - proposed, 2) if monthly is not None and proposed is not None else None
        exceeded = bool(
            proposed is not None
            and ((per_action is not None and proposed > per_action) or (remaining is not None and remaining < 0))
        )
        if monthly is None:
            blocked.append("monthly budget limit is unknown")
        if per_action is None:
            blocked.append("per-action spend limit is unknown")
        if exceeded:
            blocked.append("proposed spend exceeds a configured budget limit")
        critical = exceeded or proposed is None
        return cls(
            monthly_budget_limit=monthly,
            per_action_spend_limit=per_action,
            currency=_currency(source.get("currency")),
            current_spend_estimate=current,
            proposed_spend=proposed,
            remaining_budget=remaining,
            budget_exceeded=exceeded,
            approval_required=True,
            strong_approval_required=critical,
            double_confirmation_required=critical,
            spend_allowed=False,
            blocked_reasons=list(dict.fromkeys(blocked)),
            warning_message=(
                "Spend is blocked; strong approval and double confirmation are required."
                if critical
                else "Spend is blocked until valid approval and execution gates are available."
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PaymentApprovalDecision:
    action_name: str
    amount: Optional[float]
    currency: str
    provider: str
    mode: str
    valid_approval_present: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    double_confirmation_present: bool
    execution_allowed: bool
    eligible_after_approval: bool
    permanent_denial: bool
    denial_reason: Optional[str]
    warning_message: str
    confirmation_phrase: Optional[str]
    would_charge_real_money: bool = False
    would_spend_real_money: bool = False
    would_call_payment_provider: bool = False
    blocked_reasons: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "execution_allowed", False)
        object.__setattr__(self, "would_charge_real_money", False)
        object.__setattr__(self, "would_spend_real_money", False)
        object.__setattr__(self, "would_call_payment_provider", False)
        object.__setattr__(self, "blocked_reasons", _list(self.blocked_reasons))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StripeReadinessPreview:
    stripe_configured: bool = False
    stripe_test_mode_ready: bool = True
    stripe_live_mode_ready: bool = False
    requires_secret_key: bool = True
    secret_key_loaded: bool = False
    secret_key_value_redacted: bool = True
    webhook_required: bool = True
    product_catalog_preview: List[Dict[str, Any]] = field(default_factory=list)
    checkout_preview: Dict[str, Any] = field(default_factory=dict)
    live_charges_enabled: bool = False
    external_calls_enabled: bool = False
    blocked_reasons: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for name in ("stripe_configured", "stripe_live_mode_ready", "secret_key_loaded", "live_charges_enabled", "external_calls_enabled"):
            object.__setattr__(self, name, False)
        for name in ("stripe_test_mode_ready", "requires_secret_key", "secret_key_value_redacted", "webhook_required"):
            object.__setattr__(self, name, True)
        safe_catalog, _ = redact_sensitive_data(list(self.product_catalog_preview))
        safe_checkout, _ = redact_sensitive_data(dict(self.checkout_preview))
        object.__setattr__(self, "product_catalog_preview", safe_catalog)
        object.__setattr__(self, "checkout_preview", safe_checkout)
        blocked = _list(self.blocked_reasons) + [
            "secret key is not loaded or read by this preview",
            "Stripe live mode is disabled",
            "external payment provider calls are disabled",
        ]
        object.__setattr__(self, "blocked_reasons", list(dict.fromkeys(blocked)))

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "StripeReadinessPreview":
        source = dict(data or {})
        catalog = source.get("product_catalog_preview")
        checkout = source.get("checkout_preview")
        return cls(
            product_catalog_preview=list(catalog) if isinstance(catalog, list) else [],
            checkout_preview=dict(checkout) if isinstance(checkout, dict) else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PaymentApprovalControl:
    def __init__(self, semantics: Optional[GlobalApprovalExecutionSemantics] = None) -> None:
        self.semantics = semantics or GlobalApprovalExecutionSemantics()

    def preview(self, data: Optional[Dict[str, Any]]) -> PaymentApprovalDecision:
        source = dict(data or {})
        action = _text(source.get("action_name")) or "payment candidate"
        provider = _choice(source.get("provider"), {"stripe", "test", "stripe_live", "manual", "unknown"}, "unknown")
        mode = _choice(source.get("mode"), {"test", "live", "preview"}, "preview")
        critical = mode == "live" or provider == "stripe_live" or source.get("real_money_requested") is True
        amount = _amount(source.get("amount"))
        decision = self.semantics.preview_decision(
            action_name=action,
            action_category="critical" if critical else "normal",
            risk_level="critical" if critical else "medium",
            valid_approval_present=source.get("valid_approval_present") is True,
            strong_approval_present=source.get("strong_approval_present") is True,
            double_confirmation_present=source.get("double_confirmation_present") is True,
            context_fingerprint_matches=source.get("context_fingerprint_matches") is True,
            permission_gates_passed=source.get("permission_gates_passed") is True,
            audit_present=source.get("audit_present") is True,
            rollback_or_stop_plan_required=critical,
            rollback_or_stop_plan_present=source.get("rollback_or_stop_plan_present") is True,
            execution_capable_when_approved=True,
            illegal=source.get("illegal") is True or source.get("fraudulent") is True,
            unsafe=source.get("unsafe") is True,
            unauthorized=source.get("unauthorized") is True,
            impossible=source.get("impossible") is True,
            unsupported=source.get("unsupported") is True,
        )
        blocked = list(decision.blocked_reasons)
        if critical and amount is None:
            blocked.append("amount is unknown for a critical money action")
        blocked.append("payment provider execution is disabled in this PR")
        return PaymentApprovalDecision(
            action_name=action,
            amount=amount,
            currency=_currency(source.get("currency")),
            provider=provider,
            mode=mode,
            valid_approval_present=decision.valid_approval_present,
            strong_approval_required=decision.strong_approval_required,
            double_confirmation_required=decision.double_confirmation_required,
            double_confirmation_present=decision.double_confirmation_present,
            execution_allowed=False,
            eligible_after_approval=decision.execution_allowed and not (critical and amount is None),
            permanent_denial=decision.permanent_denial,
            denial_reason=decision.denial_reason,
            warning_message=decision.warning_message,
            confirmation_phrase=decision.required_confirmation_phrase,
            blocked_reasons=list(dict.fromkeys(blocked)),
        )


def _amount(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 2) if math.isfinite(number) and number >= 0 else None


def _currency(value: Any) -> str:
    return (_text(value) or "EUR").upper()


def _choice(value: Any, choices: set[str], default: str) -> str:
    normalized = _text(value).lower()
    return normalized if normalized in choices else default


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:500]


def _list(value: Any) -> List[str]:
    return [_text(item) for item in (value or []) if _text(item)]
