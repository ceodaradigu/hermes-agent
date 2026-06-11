from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.approval_execution_semantics import GlobalApprovalExecutionSemantics


_ACTIONS = {
    "create_repo", "write_files", "publish_landing", "deploy_backend",
    "configure_domain", "configure_billing", "run_smoke_tests",
}


@dataclass(frozen=True)
class ProductExecutionCandidate:
    candidate_id: str
    action_type: str
    target: str
    environment: str
    risk_level: str
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    valid_approval_present: bool
    eligible_after_valid_approval: bool
    execution_allowed: bool
    would_execute: bool
    would_call_external: bool
    would_modify_filesystem: bool
    would_touch_production: bool
    audit_required: bool
    rollback_or_stop_plan_required: bool
    rollback_or_stop_plan_present: bool
    blocked_reasons: List[str] = field(default_factory=list)
    next_safe_step: str = "review candidate"

    def __post_init__(self) -> None:
        object.__setattr__(self, "execution_allowed", False)
        object.__setattr__(self, "would_execute", False)
        object.__setattr__(self, "would_call_external", False)
        object.__setattr__(self, "would_modify_filesystem", False)
        object.__setattr__(self, "would_touch_production", False)
        object.__setattr__(self, "audit_required", True)

    @classmethod
    def from_request(
        cls,
        data: Optional[Dict[str, Any]],
        semantics: Optional[GlobalApprovalExecutionSemantics] = None,
    ) -> "ProductExecutionCandidate":
        source = dict(data or {})
        action = _text(source.get("action_type")).lower() or "unknown"
        environment = _text(source.get("environment")).lower() or "preview"
        production = environment == "production"
        critical = production or action in {"configure_domain", "configure_billing"}
        sensitive = critical or action in {"create_repo", "configure_domain", "configure_billing"}
        sensitive = sensitive or source.get("sensitive_filesystem_requested") is True or source.get("credentials_required") is True
        rollback_required = critical or action in {"write_files", "publish_landing", "deploy_backend"}
        rollback_present = source.get("rollback_or_stop_plan_present") is True
        authority = semantics or GlobalApprovalExecutionSemantics()
        decision = authority.preview_decision(
            action_name=action,
            action_category="critical" if critical else ("sensitive" if sensitive else "normal"),
            risk_level="critical" if critical else ("high" if sensitive else "medium"),
            valid_approval_present=source.get("valid_approval_present") is True,
            strong_approval_present=source.get("strong_approval_present") is True,
            double_confirmation_present=source.get("double_confirmation_present") is True,
            context_fingerprint_matches=source.get("context_fingerprint_matches") is True,
            permission_gates_passed=source.get("permission_gates_passed") is True,
            audit_present=source.get("audit_present") is True,
            rollback_or_stop_plan_required=rollback_required,
            rollback_or_stop_plan_present=rollback_present,
            execution_capable_when_approved=action in _ACTIONS,
            illegal=source.get("illegal") is True,
            unsafe=source.get("unsafe") is True,
            unauthorized=source.get("unauthorized") is True,
            impossible=source.get("impossible") is True,
            unsupported=source.get("unsupported") is True or action not in _ACTIONS,
        )
        blocked = list(decision.blocked_reasons) + ["execution is disabled in this PR"]
        return cls(
            candidate_id=_text(source.get("candidate_id")) or str(uuid4()),
            action_type=action,
            target=_text(source.get("target")) or "unknown",
            environment=environment,
            risk_level=decision.risk_level.value,
            approval_required=True,
            strong_approval_required=decision.strong_approval_required,
            double_confirmation_required=decision.double_confirmation_required,
            valid_approval_present=decision.valid_approval_present,
            eligible_after_valid_approval=decision.execution_allowed,
            execution_allowed=False,
            would_execute=False,
            would_call_external=False,
            would_modify_filesystem=False,
            would_touch_production=False,
            audit_required=True,
            rollback_or_stop_plan_required=rollback_required,
            rollback_or_stop_plan_present=rollback_present,
            blocked_reasons=list(dict.fromkeys(blocked)),
            next_safe_step="review gates and retain as an execution candidate",
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:1000]
