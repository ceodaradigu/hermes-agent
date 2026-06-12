from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.mark_2_external_operations_policy import ExternalOperationsPolicyEngine, approval_blockers, safe_text, valid_approval, valid_voice_approval


@dataclass(frozen=True)
class StripeOperationCandidate:
    candidate_id: str
    stripe_mode: str
    operation: str
    amount: Optional[float]
    currency: str
    customer_data_summary: str
    money_movement: bool
    live_mode: bool
    access_material_required: bool
    network_required: bool
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    triple_confirmation_required: bool
    valid_approval_present: bool
    valid_voice_approval_present: bool
    eligible_after_valid_approval: bool
    would_call_stripe: bool = False
    would_move_money: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    rollback_or_stop_plan: str = "stop before provider call; provider-specific reversal must be reviewed"
    next_safe_step: str = "Review mode, amount, customer-data redaction, approvals, and provider reversal plan."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark2StripeAdapter:
    MONEY_OPERATIONS = {"refund", "charge"}

    def __init__(self) -> None:
        self.policy = ExternalOperationsPolicyEngine()

    def preview(self, **values: Any) -> StripeOperationCandidate:
        mode = str(values.get("stripe_mode") or "unknown").lower()
        operation = str(values.get("operation") or "unknown").lower()
        money = bool(values.get("money_movement") or operation in self.MONEY_OPERATIONS)
        rollback = _text(values.get("rollback_or_stop_plan")) or "stop before provider call; provider-specific reversal must be reviewed"
        policy = self.policy.evaluate(**{
            **values,
            "operation_type": "payment",
            "provider": "stripe",
            "environment": "production" if mode == "live" else "staging",
            "production_impact": mode == "live",
            "money_movement": money,
            "rollback_or_stop_plan": rollback,
            "require_triple_confirmation": money,
        })
        return StripeOperationCandidate(
            candidate_id=str(uuid4()),
            stripe_mode=mode,
            operation=operation,
            amount=values.get("amount"),
            currency=safe_text(values.get("currency"), "unknown"),
            customer_data_summary="customer data redacted; provide only the minimum required summary",
            money_movement=money,
            live_mode=mode == "live",
            access_material_required=True,
            network_required=True,
            approval_required=True,
            strong_approval_required=policy.strong_approval_required,
            double_confirmation_required=policy.double_confirmation_required,
            triple_confirmation_required=policy.triple_confirmation_required,
            valid_approval_present=valid_approval(values),
            valid_voice_approval_present=valid_voice_approval(values),
            eligible_after_valid_approval=policy.eligible_after_valid_approval,
            blocked_reasons=approval_blockers(policy, values),
            rollback_or_stop_plan=safe_text(rollback, "stop before provider call"),
        )


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())
