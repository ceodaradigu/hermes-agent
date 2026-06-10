from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from jarvis.approval_audit import ApprovalAuditEventType, ApprovalAuditTrail
from jarvis.approval_hardening import (
    ApprovalKind,
    ApprovalRecord,
    ApprovalStatus,
    RiskLevel,
    StrongApprovalPolicy,
    build_context_fingerprint,
)


@dataclass(frozen=True)
class PermissionGateResult:
    allowed: bool = False
    requires_approval: bool = True
    requires_strong_approval: bool = False
    reason: str = "Permission gate denied by default."
    risk_level: RiskLevel = RiskLevel.MEDIUM
    missing_requirements: List[str] = field(default_factory=lambda: ["valid approval"])
    approval_status: str = "missing"
    context_matches: bool = False
    safe_to_execute: bool = False
    blocked_actions: List[str] = field(default_factory=lambda: ["real execution", "side effects"])
    prepare_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_level", RiskLevel(self.risk_level))
        object.__setattr__(self, "missing_requirements", list(self.missing_requirements))
        object.__setattr__(self, "blocked_actions", list(self.blocked_actions))
        object.__setattr__(self, "safe_to_execute", False)
        object.__setattr__(self, "prepare_only", True)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        return data


def evaluate_permission_gate(
    context: Dict[str, Any],
    approval: Optional[ApprovalRecord] = None,
    *,
    policy: Optional[StrongApprovalPolicy] = None,
    audit_trail: Optional[ApprovalAuditTrail] = None,
) -> PermissionGateResult:
    policy = policy or StrongApprovalPolicy()
    risk, requires_strong, _ = policy.classify(context)
    missing: List[str] = []
    expired = bool(approval) and _is_expired(approval.expires_at)
    status = ApprovalStatus.EXPIRED.value if expired else (approval.status.value if approval else "missing")
    context_matches = bool(approval) and approval.context_fingerprint == build_context_fingerprint(context)

    if approval is None:
        missing.append("approval")
    elif expired:
        missing.append("approval status is expired")
    elif approval.status != ApprovalStatus.APPROVED:
        missing.append(f"approval status is {approval.status.value}")
    if requires_strong and (approval is None or approval.approval_kind != ApprovalKind.STRONG):
        missing.append("strong approval")
    if approval is not None and not context_matches:
        missing.append("approved context fingerprint match")
        if audit_trail:
            audit_trail.append(
                ApprovalAuditEventType.APPROVAL_CONTEXT_MISMATCH,
                approval.approval_id,
                summary="Approval context fingerprint mismatch.",
            )

    allowed = not missing
    reason = (
        "Approval gate allowed for future execution only; runtime execution remains disabled."
        if allowed
        else "Approval gate denied: " + "; ".join(missing)
    )
    result = PermissionGateResult(
        allowed=allowed,
        requires_approval=True,
        requires_strong_approval=requires_strong,
        reason=reason,
        risk_level=risk,
        missing_requirements=missing,
        approval_status=status,
        context_matches=context_matches,
        safe_to_execute=False,
        blocked_actions=["real execution", "side effects", "runtime bridge"],
    )
    if audit_trail:
        audit_trail.append(
            ApprovalAuditEventType.APPROVAL_GATE_ALLOWED_FOR_FUTURE_EXECUTION
            if allowed
            else ApprovalAuditEventType.APPROVAL_GATE_DENIED,
            approval.approval_id if approval else "missing",
            summary=reason,
            metadata={"allowed": allowed, "risk_level": risk.value, "context_matches": context_matches},
        )
    return result


def _is_expired(expires_at: str) -> bool:
    parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= parsed.astimezone(timezone.utc)
