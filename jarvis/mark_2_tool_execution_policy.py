from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from jarvis.approval_hardening import RiskLevel


RISK_ORDER = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


@dataclass(frozen=True)
class Mark2ToolExecutionStatus:
    current_mark: str = "Mark 2"
    mark_2_macro: str = "Mark 2 Macro 2"
    real_tool_execution_layer_available: bool = True
    tool_execution_readiness_available: bool = True
    filesystem_adapter_available: bool = True
    github_adapter_available: bool = True
    browser_adapter_available: bool = True
    external_api_adapter_available: bool = True
    sandbox_boundaries_available: bool = True
    allowlist_policy_available: bool = True
    denylist_policy_available: bool = True
    audit_available: bool = True
    rollback_plan_required: bool = True
    voice_approval_supported: bool = True
    wake_phrase_is_permission: bool = False
    restrictions_are_approval_gates: bool = True
    real_execution_enabled: bool = False
    external_network_enabled: bool = False
    access_material_enabled: bool = False
    production_operations_enabled: bool = False
    money_movement_enabled: bool = False
    filesystem_external_write_enabled: bool = False
    browser_real_launch_enabled: bool = False
    github_real_calls_enabled: bool = False
    external_api_real_calls_enabled: bool = False
    next_recommended_macro_pr: str = "Mark 2 Macro 3 — Visual Command Center UI & Human Approval Console"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolExecutionPolicy:
    default_decision: str
    action_type: str
    target_type: str
    risk_level: RiskLevel
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    triple_confirmation_required: bool
    voice_approval_allowed: bool = True
    voice_approval_requirements: List[str] = field(default_factory=list)
    audit_required: bool = True
    sandbox_required: bool = True
    allowlist_required: bool = True
    rollback_or_stop_plan_required: bool = False
    credentials_required: bool = False
    network_required: bool = False
    production_impact: bool = False
    cost_impact: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    eligible_after_valid_approval: bool = True
    permanent_denial: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        return data


class Mark2ToolExecutionPolicyEngine:
    """Default-deny policy classifier for Mark 2 tool execution candidates."""

    def status(self) -> Dict[str, Any]:
        return Mark2ToolExecutionStatus().to_dict()

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            "default_decision": "blocked",
            "preview_is_always_non_executing": True,
            "candidate_is_not_execution": True,
            "tool_execution_requires_approval": True,
            "sensitive_tool_execution_requires_strong_approval": True,
            "critical_tool_execution_requires_double_confirmation": True,
            "money_movement_can_require_triple_confirmation": True,
            "scheduler_due_is_permission": False,
            "memory_active_is_permission": False,
            "wake_phrase_is_permission": False,
            "permanent_denial_only_for_illegal_unsafe_unauthorized_impossible_or_unsupported": True,
        }

    def evaluate(self, **values: Any) -> ToolExecutionPolicy:
        action = _clean(values.get("action_type")) or "unknown"
        target_type = _clean(values.get("target_type")).lower() or "unknown"
        target = _clean(values.get("target"))
        environment = _clean(values.get("environment")).lower() or "unknown"
        text = f"{action} {target_type} {target} {environment}".lower()
        credentials = bool(values.get("requires_credentials") or _has(text, "credential", "token", "login", "secret"))
        network = bool(values.get("requires_network") or target_type in {"github", "browser", "external_api"})
        production = bool(values.get("production_impact") or environment == "production" or "production" in text)
        money = bool(values.get("cost_impact") or _has(text, "payment", "pay", "purchase", "charge", "stripe", "money"))
        mutation = bool(values.get("mutation") or _has(action.lower(), "write", "patch", "delete", "create", "merge", "submit", "post", "put"))
        illegal = bool(values.get("illegal"))
        unsafe = bool(values.get("unsafe"))
        unauthorized = bool(values.get("unauthorized"))
        impossible = bool(values.get("impossible"))
        unsupported = bool(values.get("unsupported") or target_type not in {
            "filesystem", "github", "browser", "external_api", "deploy", "payment", "email"
        })
        permanent = illegal or unsafe or unauthorized or impossible or unsupported
        blocked = []
        for enabled, reason in (
            (illegal, "action is illegal"),
            (unsafe, "action is unsafe"),
            (unauthorized, "action is unauthorized"),
            (impossible, "action is impossible"),
            (unsupported, "action or target is unsupported"),
        ):
            if enabled:
                blocked.append(reason)
        if ".env" in text or _has(text, "private_key", "read secret", "read token"):
            blocked.append("secret or .env access is blocked")
        if target_type == "filesystem" and not values.get("allowlist_match", False):
            blocked.append("filesystem target is outside allowlist")
        if values.get("denylist_match"):
            blocked.append("target matches denylist")
        if network and not values.get("network_enabled", False):
            blocked.append("external network gate disabled")
        if credentials and not values.get("access_material_enabled", False):
            blocked.append("credentials access gate disabled")
        if production and not values.get("production_operations_enabled", False):
            blocked.append("production operations gate disabled")
        if money and not values.get("money_movement_enabled", False):
            blocked.append("money movement gate disabled")
        risk = RiskLevel(values.get("risk_level") or RiskLevel.MEDIUM)
        classified = RiskLevel.CRITICAL if production or money else (
            RiskLevel.HIGH if credentials or (network and mutation) or action.lower().startswith("delete") else RiskLevel.MEDIUM
        )
        risk = max((risk, classified), key=RISK_ORDER.get)
        strong = risk in {RiskLevel.HIGH, RiskLevel.CRITICAL} or credentials
        double = risk == RiskLevel.CRITICAL
        triple = bool(money and values.get("require_triple_confirmation", True))
        rollback = bool(mutation or production or money)
        decision = "blocked" if blocked or permanent else "executable_after_approval"
        return ToolExecutionPolicy(
            default_decision=decision,
            action_type=action,
            target_type=target_type,
            risk_level=risk,
            approval_required=True,
            strong_approval_required=strong,
            double_confirmation_required=double,
            triple_confirmation_required=triple,
            voice_approval_requirements=[
                "explicit valid Voice Approval Channel state",
                "readback completed",
                "wake phrase is not permission",
                "unexpired approval bound to the exact action",
            ],
            rollback_or_stop_plan_required=rollback,
            credentials_required=credentials,
            network_required=network,
            production_impact=production,
            cost_impact=money,
            blocked_reasons=list(dict.fromkeys(blocked)),
            eligible_after_valid_approval=not permanent,
            permanent_denial=permanent,
        )


def mark_2_tool_execution_markers() -> Dict[str, Any]:
    return {
        "mark_2_macro_2_real_tool_execution": True,
        "mark_2_macro_2_real_tool_execution_available": True,
        "real_tool_execution_layer_available": True,
        "tool_execution_readiness_available": True,
        "filesystem_adapter_available": True,
        "github_adapter_available": True,
        "browser_adapter_available": True,
        "external_api_adapter_available": True,
        "real_execution_enabled": False,
        "real_execution_disabled_by_default": True,
        "external_network_enabled": False,
        "external_network_disabled_by_default": True,
        "access_material_enabled": False,
        "access_material_disabled_by_default": True,
        "production_operations_enabled": False,
        "production_operations_disabled_by_default": True,
        "money_movement_enabled": False,
        "money_movement_disabled_by_default": True,
        "filesystem_external_write_enabled": False,
        "filesystem_external_write_disabled_by_default": True,
        "browser_real_launch_enabled": False,
        "browser_real_launch_disabled_by_default": True,
        "github_real_calls_enabled": False,
        "github_real_calls_disabled_by_default": True,
        "external_api_real_calls_enabled": False,
        "external_api_real_calls_disabled_by_default": True,
        "tool_execution_requires_approval": True,
        "sensitive_tool_execution_requires_strong_approval": True,
        "critical_tool_execution_requires_double_confirmation": True,
        "voice_approval_supported": True,
        "voice_approval_supported_for_tool_execution": True,
        "wake_phrase_is_permission": False,
        "wake_phrase_is_not_permission_for_tool_execution": True,
        "sandbox_boundaries_available": True,
        "allowlist_policy_available": True,
        "denylist_policy_available": True,
        "tool_execution_audit_available": True,
        "rollback_plan_required": True,
        "rollback_plan_required_for_tool_execution": True,
        "mark_2_macro_3_planned": True,
        "next_recommended_macro_pr": "Mark 2 Macro 3 — Visual Command Center UI & Human Approval Console",
    }


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _has(text: str, *markers: str) -> bool:
    return any(marker in text for marker in markers)
