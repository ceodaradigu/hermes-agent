from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class ApprovalPath:
    action_type: str
    risk_level: str
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    triple_confirmation_required: bool
    voice_approval_allowed: bool = True
    wake_phrase_allowed: bool = False
    rollback_or_stop_plan_required: bool = True
    audit_required: bool = True
    access_material_required: bool = False
    eligible_after_valid_approval: bool = True
    permanently_denied: bool = False
    denial_reason: str = ""
    passed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark2ApprovalPathAudit:
    _SPECS = (
        ("production deploy", "critical", True, True, True, False, True, True),
        ("staging deploy", "high", True, True, False, False, True, True),
        ("Stripe test operation", "high", True, True, False, False, True, True),
        ("Stripe live/payment", "critical", True, True, True, True, True, True),
        ("email draft", "low", False, False, False, False, False, False),
        ("email send", "high", True, False, False, False, True, True),
        ("bulk/sensitive email", "high", True, True, False, False, True, True),
        ("domain/DNS publish", "critical", True, True, True, False, True, True),
        ("filesystem write/delete", "high", True, True, False, False, True, False),
        ("GitHub branch/PR candidate", "high", True, True, False, False, True, True),
        ("browser form assist", "high", True, True, False, False, True, True),
        ("external API call", "high", True, True, False, False, True, True),
        ("Codex CLI invocation", "high", True, True, False, False, True, False),
        ("Claude Code invocation", "high", True, True, False, False, True, False),
        ("Claude Cowork routine", "high", True, True, False, False, True, False),
        ("API fallback", "high", True, True, False, False, True, True),
        ("scheduler recurring routine", "high", True, True, False, False, True, False),
        ("memory write/activation", "high", True, True, False, False, True, False),
        ("access material setup", "high", True, True, False, False, True, True),
    )

    def audit(self) -> Dict[str, Any]:
        paths: List[ApprovalPath] = [
            ApprovalPath(
                action_type=action,
                risk_level=risk,
                approval_required=approval,
                strong_approval_required=strong,
                double_confirmation_required=double,
                triple_confirmation_required=triple,
                rollback_or_stop_plan_required=rollback,
                access_material_required=access,
            )
            for action, risk, approval, strong, double, triple, rollback, access in self._SPECS
        ]
        return {
            "passed": all(path.passed for path in paths),
            "restrictions_are_approval_gates": True,
            "wake_phrase_is_permission": False,
            "voice_can_approve": True,
            "approval_paths": [path.to_dict() for path in paths],
        }
