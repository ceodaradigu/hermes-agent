from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.approval_hardening import RiskLevel


ARCHITECTURAL_RULE = "Restrictions are approval gates, not permanent bans."
CURRENT_MARK = "Mark 1"
NEXT_RECOMMENDED_MACRO_PR = "PR #123 - Monetization Engine Real"


@dataclass(frozen=True)
class ExecutionEligibilityDecision:
    action_name: str
    action_category: str
    risk_level: RiskLevel
    blocked_without_approval: bool
    valid_approval_present: bool
    approval_required: bool
    strong_approval_required: bool
    strong_approval_present: bool
    double_confirmation_required: bool
    double_confirmation_present: bool
    context_fingerprint_matches: bool
    permission_gates_passed: bool
    audit_required: bool
    audit_present: bool
    rollback_or_stop_plan_required: bool
    rollback_or_stop_plan_present: bool
    execution_capable_when_approved: bool
    execution_allowed: bool
    permanent_denial: bool
    denial_reason: Optional[str]
    blocked_reasons: List[str] = field(default_factory=list)
    warning_message: str = ""
    required_confirmation_phrase: Optional[str] = None
    preview_only: bool = True
    would_execute: bool = False
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_level", RiskLevel(self.risk_level))
        object.__setattr__(self, "blocked_reasons", list(self.blocked_reasons))
        object.__setattr__(self, "preview_only", True)
        object.__setattr__(self, "would_execute", False)
        object.__setattr__(self, "execution_enabled", False)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        return data


@dataclass(frozen=True)
class CriticalActionWarning:
    action_name: str
    risk_summary: str
    affected_system: str
    possible_consequences: List[str]
    estimated_cost: Optional[str]
    irreversible_or_hard_to_reverse: bool
    rollback_available: bool
    required_double_confirmation: bool
    confirmation_phrase: str
    preview_only: bool = True
    would_execute: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "possible_consequences", list(self.possible_consequences))
        object.__setattr__(self, "preview_only", True)
        object.__setattr__(self, "would_execute", False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarkRoadmap:
    current_mark: str = CURRENT_MARK
    mark_1_remaining_macro_prs: List[str] = field(
        default_factory=lambda: [
            "PR #122 - Global Approval-Controlled Execution Semantics & Mark Roadmap",
            "PR #123 - Monetization Engine Real",
            "PR #124 - SaaS/Product Builder + Publishing/Deploy Execution",
            "PR #125 - Mark 1 Hardening, E2E Real Ops & Release Candidate",
        ]
    )
    mark_2_macro_prs: List[str] = field(
        default_factory=lambda: [
            "Mark 2 Macro 1 - Local Daemon, Real Wake Listener & Desktop Runtime",
            "Mark 2 Macro 2 - Real Tool Execution: Browser, GitHub, Filesystem & APIs",
            "Mark 2 Macro 3 - Visual Command Center UI & Human Approval Console",
            "Mark 2 Macro 4 - Real Deploy, Stripe, Email & External Operations",
            "Mark 2 Release Candidate Hardening",
        ]
    )
    mark_3_macro_prs: List[str] = field(
        default_factory=lambda: [
            "Mark 3 Macro 1 - Multi-Agent Operating System",
            "Mark 3 Macro 2 - Continuous Learning & Self-Improvement Loop",
            "Mark 3 Macro 3 - Autonomous Opportunity, Product & Growth Engine",
            "Mark 3 Macro 4 - 24/7 Infrastructure, Monitoring, Recovery & Cost Control",
            "Mark 3 Release Candidate Hardening",
        ]
    )
    no_micro_pr_policy: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GlobalApprovalExecutionSemantics:
    """Control-plane authority for approval-gated execution eligibility."""

    def status(self) -> Dict[str, Any]:
        return {
            "control_plane_only": True,
            "preview_only": True,
            "real_execution_enabled": False,
            "current_implementation_remains_safe_control_plane": True,
            "jarvis_is_not_prepare_only_forever": True,
            "architectural_rule": ARCHITECTURAL_RULE,
            "restrictions_are_approval_gates": True,
            "default_denied_without_approval": True,
            "executable_after_valid_approval": True,
            "strong_approval_required_for_sensitive": True,
            "double_confirmation_required_for_critical": True,
            "permanent_denial_only_for_illegal_unsafe_unauthorized_impossible_or_unsupported": True,
            "next_recommended_macro_pr": NEXT_RECOMMENDED_MACRO_PR,
        }

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            "audit_required": True,
            "context_fingerprint_required_when_applicable": True,
            "permission_gates_required": True,
            "rollback_or_stop_plan_required_when_possible": True,
            "approval_cannot_override_legality_safety_authorization_or_capability": True,
            "approval_hardening_is_authority_for_valid_approval_strong_approval_expiration_revocation_context_and_audit": True,
            "preview_inputs_are_assertions_not_authoritative_approval_records": True,
            "wake_phrase_is_not_permission": True,
            "scheduler_due_is_not_permission": True,
            "memory_active_is_not_permission": True,
            "runtime_safe_to_execute_is_eligibility_not_execution": True,
            "tool_safe_to_invoke_is_eligibility_not_execution": True,
        }

    def preview_decision(
        self,
        *,
        action_name: str,
        action_category: str = "normal",
        risk_level: RiskLevel | str = RiskLevel.MEDIUM,
        valid_approval_present: bool = False,
        strong_approval_present: bool = False,
        double_confirmation_present: bool = False,
        context_fingerprint_matches: bool = False,
        permission_gates_passed: bool = False,
        audit_present: bool = False,
        rollback_or_stop_plan_required: bool = False,
        rollback_or_stop_plan_present: bool = False,
        execution_capable_when_approved: bool = False,
        illegal: bool = False,
        unsafe: bool = False,
        unauthorized: bool = False,
        impossible: bool = False,
        unsupported: bool = False,
    ) -> ExecutionEligibilityDecision:
        name = _clean_text(action_name) or "unnamed action"
        category = _normalized_category(action_category)
        risk = RiskLevel(risk_level)
        critical = category == "critical" or risk == RiskLevel.CRITICAL
        sensitive = critical or category == "sensitive" or risk == RiskLevel.HIGH
        permanent_reasons = [
            label
            for denied, label in (
                (illegal, "action is illegal"),
                (unsafe, "action is unsafe"),
                (unauthorized, "action is unauthorized"),
                (impossible, "action is technically impossible"),
                (unsupported, "action or capability is unsupported"),
            )
            if denied
        ]
        blocked: List[str] = list(permanent_reasons)
        if not valid_approval_present:
            blocked.append("valid explicit approval required")
        if sensitive and not strong_approval_present:
            blocked.append("valid strong approval required")
        if critical and not double_confirmation_present:
            blocked.append("double confirmation required")
        if not context_fingerprint_matches:
            blocked.append("context fingerprint mismatch")
        if not permission_gates_passed:
            blocked.append("permission gates failed")
        if not audit_present:
            blocked.append("execution audit is missing")
        if rollback_or_stop_plan_required and not rollback_or_stop_plan_present:
            blocked.append("required rollback or stop plan is missing")
        if not execution_capable_when_approved:
            blocked.append("real execution capability is unavailable")
        blocked = list(dict.fromkeys(blocked))
        permanent_denial = bool(permanent_reasons)
        phrase = _confirmation_phrase(name) if critical else None
        return ExecutionEligibilityDecision(
            action_name=name,
            action_category=category,
            risk_level=risk,
            blocked_without_approval=True,
            valid_approval_present=valid_approval_present,
            approval_required=True,
            strong_approval_required=sensitive,
            strong_approval_present=strong_approval_present,
            double_confirmation_required=critical,
            double_confirmation_present=double_confirmation_present,
            context_fingerprint_matches=context_fingerprint_matches,
            permission_gates_passed=permission_gates_passed,
            audit_required=True,
            audit_present=audit_present,
            rollback_or_stop_plan_required=rollback_or_stop_plan_required,
            rollback_or_stop_plan_present=rollback_or_stop_plan_present,
            execution_capable_when_approved=execution_capable_when_approved,
            execution_allowed=not blocked,
            permanent_denial=permanent_denial,
            denial_reason="; ".join(permanent_reasons) if permanent_denial else None,
            blocked_reasons=blocked,
            warning_message=_warning_message(name, sensitive=sensitive, critical=critical, permanent=permanent_denial),
            required_confirmation_phrase=phrase,
        )

    def preview_critical_warning(
        self,
        *,
        action_name: str,
        affected_system: str = "unspecified system",
        possible_consequences: Optional[List[str]] = None,
        estimated_cost: Optional[str] = None,
        irreversible_or_hard_to_reverse: bool = True,
        rollback_available: bool = False,
    ) -> CriticalActionWarning:
        name = _clean_text(action_name) or "unnamed critical action"
        consequences = [_clean_text(item) for item in (possible_consequences or []) if _clean_text(item)]
        if not consequences:
            consequences = _default_consequences(name)
        return CriticalActionWarning(
            action_name=name,
            risk_summary=f"Critical action affecting {_clean_text(affected_system) or 'unspecified system'}.",
            affected_system=_clean_text(affected_system) or "unspecified system",
            possible_consequences=consequences,
            estimated_cost=_clean_text(estimated_cost) if estimated_cost else None,
            irreversible_or_hard_to_reverse=irreversible_or_hard_to_reverse,
            rollback_available=rollback_available,
            required_double_confirmation=True,
            confirmation_phrase=_confirmation_phrase(name),
        )

    def roadmap(self) -> MarkRoadmap:
        return MarkRoadmap()


def global_execution_markers() -> Dict[str, bool]:
    return {
        "global_approval_controlled_execution_semantics": True,
        "restrictions_are_approval_gates": True,
        "default_denied_without_approval": True,
        "executable_after_valid_approval": True,
        "strong_approval_for_sensitive_actions": True,
        "double_confirmation_for_critical_actions": True,
        "permanent_denial_for_illegal_unsafe_unauthorized_impossible_unsupported": True,
        "audit_required_for_execution": True,
        "context_fingerprint_required_for_sensitive_execution": True,
        "permission_gates_required_for_execution": True,
        "rollback_or_stop_plan_required_when_possible": True,
        "mark_1_current": True,
        "mark_2_planned": True,
        "mark_3_planned": True,
        "no_micro_pr_policy": True,
    }


def _normalized_category(value: str) -> str:
    category = _clean_text(value).lower()
    return category if category in {"normal", "sensitive", "critical"} else "normal"


def _confirmation_phrase(action_name: str) -> str:
    return f"CONFIRM CRITICAL ACTION: {action_name.upper()}"


def _warning_message(action_name: str, *, sensitive: bool, critical: bool, permanent: bool) -> str:
    if permanent:
        return f"{action_name} is permanently denied; approval cannot override the denial."
    if critical:
        return f"{action_name} is critical and requires valid strong approval plus double confirmation."
    if sensitive:
        return f"{action_name} is sensitive and requires valid strong approval."
    return f"{action_name} requires valid explicit approval before execution eligibility."


def _default_consequences(action_name: str) -> List[str]:
    text = action_name.lower()
    consequences = ["external or persistent side effects", "audit and recovery obligations"]
    if any(marker in text for marker in ("deploy", "production", "publish")):
        consequences.append("service disruption or unintended public changes")
    if any(marker in text for marker in ("stripe", "pay", "spend", "expense", "purchase")):
        consequences.append("real financial movement or cost")
    if any(marker in text for marker in ("email", "message", "github", "browser")):
        consequences.append("external communication or account changes")
    if any(marker in text for marker in ("camera", "microphone", "filesystem", "credential")):
        consequences.append("privacy, sensitive data, or access-control impact")
    return list(dict.fromkeys(consequences))


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())
