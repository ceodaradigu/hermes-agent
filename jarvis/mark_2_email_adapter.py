from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data
from jarvis.mark_2_external_operations_policy import ExternalOperationsPolicyEngine, approval_blockers, safe_text, valid_approval


@dataclass(frozen=True)
class EmailOperationCandidate:
    candidate_id: str
    provider: str
    operation: str
    recipients_summary: str
    subject_summary: str
    body_summary_redacted: str
    contains_sensitive_data: bool
    bulk_or_marketing: bool
    access_material_required: bool
    network_required: bool
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    valid_approval_present: bool
    eligible_after_valid_approval: bool
    would_send_email: bool = False
    would_call_external: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    next_safe_step: str = "Review recipients, redacted content summary, consent, and approval gates."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark2EmailAdapter:
    def __init__(self) -> None:
        self.policy = ExternalOperationsPolicyEngine()

    def preview(self, **values: Any) -> EmailOperationCandidate:
        operation = str(values.get("operation") or "draft").lower()
        sensitive = bool(values.get("contains_sensitive_data"))
        bulk = bool(values.get("bulk_or_marketing") or operation == "bulk_send")
        policy = self.policy.evaluate(**{
            **values,
            "operation_type": "email",
            "operation": operation,
            "contains_sensitive_data": sensitive,
            "bulk_or_marketing": bulk,
            "access_material_required": operation != "draft",
            "network_required": operation != "draft",
            "rollback_or_stop_plan": "stop before send",
        })
        blocked = approval_blockers(policy, values) if operation != "draft" else []
        safe_body = redact_sensitive_data({"body": values.get("body_summary", "content summary not provided")})[0]["body"]
        return EmailOperationCandidate(
            candidate_id=str(uuid4()),
            provider=safe_text(values.get("provider"), "unknown"),
            operation=operation,
            recipients_summary="recipient identities redacted; count and audience must be reviewed",
            subject_summary=safe_text(values.get("subject_summary"), "subject not provided"),
            body_summary_redacted=str(safe_body),
            contains_sensitive_data=sensitive,
            bulk_or_marketing=bulk,
            access_material_required=operation != "draft",
            network_required=operation != "draft",
            approval_required=operation != "draft",
            strong_approval_required=sensitive or bulk,
            double_confirmation_required=False,
            valid_approval_present=valid_approval(values),
            eligible_after_valid_approval=policy.eligible_after_valid_approval,
            blocked_reasons=blocked,
        )
