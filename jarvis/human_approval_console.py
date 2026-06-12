from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class HumanApprovalItem:
    approval_id: str
    action_summary: str
    action_type: str
    requested_by: str
    channel: str
    risk_level: str
    approval_required: bool = True
    strong_approval_required: bool = False
    double_confirmation_required: bool = False
    triple_confirmation_required: bool = False
    voice_approval_allowed: bool = True
    text_approval_allowed: bool = True
    readback_required: bool = True
    readback_text: str = "Read back the exact action, risk, cost, impact, and stop plan."
    required_confirmation_phrase: Optional[str] = None
    confirmations_completed: int = 0
    expires_at: Optional[str] = None
    expired: bool = False
    audit_required: bool = True
    rollback_or_stop_plan_present: bool = True
    current_state: str = "pending"
    approve_action_available: bool = False
    reject_action_available: bool = False
    would_execute_after_approval: bool = False
    next_safe_step: str = "Review the request in preview mode; no dashboard approval action is enabled."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_human_approval_console() -> List[HumanApprovalItem]:
    return [
        HumanApprovalItem(
            approval_id="preview-production-change",
            action_summary="Preview approval requirements for a future production change.",
            action_type="production",
            requested_by="OperatorAgent",
            channel="text",
            risk_level="critical",
            strong_approval_required=True,
            double_confirmation_required=True,
            required_confirmation_phrase="Exact strong confirmation required in a future reviewed approval flow.",
        ),
        HumanApprovalItem(
            approval_id="preview-money-action",
            action_summary="Preview approval requirements for a future money action.",
            action_type="money",
            requested_by="OperatorAgent",
            channel="voice",
            risk_level="critical",
            strong_approval_required=True,
            double_confirmation_required=True,
            triple_confirmation_required=True,
        ),
    ]

