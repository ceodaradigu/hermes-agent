from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List
from uuid import uuid4

from jarvis.mark_2_external_operations_policy import ExternalOperationsPolicyEngine, approval_blockers, safe_text, valid_approval


@dataclass(frozen=True)
class DomainPublishingCandidate:
    candidate_id: str
    provider: str
    operation: str
    domain_summary: str
    target_summary: str
    production_impact: bool
    access_material_required: bool
    network_required: bool
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    rollback_or_unpublish_plan: str
    valid_approval_present: bool
    eligible_after_valid_approval: bool
    would_publish: bool = False
    would_modify_dns: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    next_safe_step: str = "Review exact record or publish target, approval, and rollback or unpublish plan."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark2DomainPublishingAdapter:
    def __init__(self) -> None:
        self.policy = ExternalOperationsPolicyEngine()

    def preview(self, **values: Any) -> DomainPublishingCandidate:
        operation = str(values.get("operation") or "unknown").lower()
        production = bool(values.get("production_impact"))
        rollback = _text(values.get("rollback_or_unpublish_plan"))
        policy = self.policy.evaluate(**{
            **values,
            "operation_type": "domain_publish",
            "operation": operation,
            "environment": "production" if production else "staging",
            "production_impact": production,
            "rollback_or_stop_plan": rollback,
        })
        return DomainPublishingCandidate(
            candidate_id=str(uuid4()),
            provider=safe_text(values.get("provider"), "unknown"),
            operation=operation,
            domain_summary="domain identity redacted; ownership and exact target require manual review",
            target_summary=safe_text(values.get("target_summary"), "target not provided"),
            production_impact=production,
            access_material_required=True,
            network_required=True,
            approval_required=True,
            strong_approval_required=True,
            double_confirmation_required=production,
            rollback_or_unpublish_plan=safe_text(rollback, "missing"),
            valid_approval_present=valid_approval(values),
            eligible_after_valid_approval=policy.eligible_after_valid_approval,
            blocked_reasons=approval_blockers(policy, values),
        )


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())
