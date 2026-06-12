from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from jarvis.approval_hardening import RiskLevel
from jarvis.approval_audit import redact_sensitive_data


NEXT_RECOMMENDED_MACRO_PR = "Mark 2 Release Candidate Hardening"


@dataclass(frozen=True)
class Mark2ExternalOperationsStatus:
    current_mark: str = "Mark 2"
    mark_2_macro: str = "Mark 2 Macro 4"
    real_deploy_operations_available: bool = True
    stripe_operations_available: bool = True
    email_operations_available: bool = True
    domain_publishing_operations_available: bool = True
    codex_cli_adapter_available: bool = True
    claude_code_adapter_available: bool = True
    claude_cowork_adapter_available: bool = True
    api_fallback_adapter_available: bool = True
    routine_execution_bridge_available: bool = True
    ai_cli_session_audit_available: bool = True
    external_operations_policy_available: bool = True
    real_external_invocation_enabled: bool = False
    real_deploy_enabled: bool = False
    stripe_live_enabled: bool = False
    email_send_enabled: bool = False
    domain_publish_enabled: bool = False
    codex_cli_real_invocation_enabled: bool = False
    claude_code_real_invocation_enabled: bool = False
    claude_cowork_real_invocation_enabled: bool = False
    api_fallback_real_invocation_enabled: bool = False
    access_material_enabled: bool = False
    external_network_enabled: bool = False
    production_operations_enabled: bool = False
    money_movement_enabled: bool = False
    audit_required: bool = True
    rollback_required_for_production: bool = True
    strong_approval_required_for_sensitive: bool = True
    double_confirmation_required_for_critical: bool = True
    triple_confirmation_supported_for_very_high_risk: bool = True
    voice_approval_supported: bool = True
    wake_phrase_is_permission: bool = False
    restrictions_are_approval_gates: bool = True
    next_recommended_macro_pr: str = NEXT_RECOMMENDED_MACRO_PR

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalOperationsPolicy:
    operation_type: str
    provider: str
    environment: str
    risk_level: RiskLevel
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    triple_confirmation_required: bool
    voice_approval_allowed: bool
    readback_required: bool
    access_material_required: bool
    network_required: bool
    cost_impact: bool
    production_impact: bool
    user_data_impact: bool
    rollback_or_stop_plan_required: bool
    audit_required: bool
    manual_handoff_required: bool
    blocked_reasons: List[str] = field(default_factory=list)
    eligible_after_valid_approval: bool = True
    permanent_denial: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        return data


class ExternalOperationsPolicyEngine:
    SUPPORTED_OPERATIONS = {"deploy", "payment", "email", "domain_publish", "ai_cli", "api_fallback"}

    def status(self) -> Dict[str, Any]:
        return Mark2ExternalOperationsStatus().to_dict()

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            "default_decision": "blocked_or_preview",
            "preview_never_executes": True,
            "candidate_is_not_execution": True,
            "gated_execution_real_invocation_enabled": False,
            "manual_handoff_for_provider_login_or_access_material": True,
            "permanent_denial_only_for_illegal_unsafe_unauthorized_impossible_or_unsupported": True,
            "costs_are_estimated_or_unknown": True,
            "no_fake_costs": True,
        }

    def evaluate(self, **values: Any) -> ExternalOperationsPolicy:
        operation = _clean(values.get("operation_type")).lower() or "unknown"
        provider = _clean(values.get("provider")).lower() or "unknown"
        environment = _clean(values.get("environment")).lower() or "unknown"
        text = " ".join(_clean(values.get(name)).lower() for name in ("operation", "action", "task_summary"))
        production = bool(values.get("production_impact") or environment == "production")
        money = bool(values.get("money_movement") or operation == "payment")
        sensitive = bool(values.get("contains_sensitive_data") or values.get("bulk_or_marketing"))
        mutation = operation in {"deploy", "payment", "email", "domain_publish", "ai_cli", "api_fallback"} and (
            operation != "email" or "draft" not in text
        )
        access = bool(values.get("access_material_required", operation in {"deploy", "payment", "email", "domain_publish", "api_fallback"}))
        network = bool(values.get("network_required", operation != "ai_cli" or provider != "local"))
        domain_sensitive = operation == "domain_publish"
        ai_write = operation == "ai_cli" and any(marker in text for marker in ("write", "modify", "push", "merge", "deploy"))
        critical = production or money
        strong = critical or sensitive or domain_sensitive or ai_write
        triple = bool(money and values.get("require_triple_confirmation", True))
        rollback = bool(production or money or operation in {"deploy", "domain_publish"} or ai_write)
        unsupported = bool(values.get("unsupported") or operation not in self.SUPPORTED_OPERATIONS)
        permanent = any(bool(values.get(name)) for name in ("illegal", "unsafe", "unauthorized", "impossible")) or unsupported
        blocked = [
            label
            for name, label in (
                ("illegal", "operation is illegal"),
                ("unsafe", "operation is unsafe"),
                ("unauthorized", "operation is unauthorized"),
                ("impossible", "operation is impossible"),
            )
            if values.get(name)
        ]
        if unsupported:
            blocked.append("operation is unsupported")
        manual = access and not values.get("access_material_available", False)
        if manual:
            blocked.append("provider access material unavailable; manual handoff required")
        if network and not values.get("external_network_enabled", False):
            blocked.append("external network gate disabled")
        if production and not values.get("production_operations_enabled", False):
            blocked.append("production operations gate disabled")
        if money and not values.get("money_movement_enabled", False):
            blocked.append("money movement gate disabled")
        if rollback and not _clean(values.get("rollback_or_stop_plan")):
            blocked.append("required rollback or stop plan is missing")
        if values.get("kill_switch_active"):
            blocked.append("kill switch active")
        if values.get("stop_phrase_detected"):
            blocked.append("candidate cancelled by stop phrase")
        risk = RiskLevel.CRITICAL if critical else RiskLevel.HIGH if strong or (network and mutation) else RiskLevel.MEDIUM
        return ExternalOperationsPolicy(
            operation_type=operation,
            provider=provider,
            environment=environment,
            risk_level=risk,
            approval_required=mutation,
            strong_approval_required=strong,
            double_confirmation_required=critical or (domain_sensitive and production),
            triple_confirmation_required=triple,
            voice_approval_allowed=True,
            readback_required=mutation,
            access_material_required=access,
            network_required=network,
            cost_impact=bool(money or values.get("cost_impact")),
            production_impact=production,
            user_data_impact=bool(sensitive or values.get("user_data_impact")),
            rollback_or_stop_plan_required=rollback,
            audit_required=True,
            manual_handoff_required=manual,
            blocked_reasons=list(dict.fromkeys(blocked)),
            eligible_after_valid_approval=not permanent,
            permanent_denial=permanent,
        )


def valid_approval(values: Dict[str, Any]) -> bool:
    return bool(values.get("valid_approval_present")) and not any(
        values.get(name) for name in ("expired", "revoked", "wake_phrase", "scheduler_due", "memory_active")
    )


def valid_voice_approval(values: Dict[str, Any]) -> bool:
    return bool(values.get("valid_voice_approval_present") and values.get("readback_completed")) and not any(
        values.get(name) for name in ("expired", "cancelled", "wake_phrase")
    )


def approval_blockers(policy: ExternalOperationsPolicy, values: Dict[str, Any]) -> List[str]:
    approval = valid_approval(values)
    voice = valid_voice_approval(values)
    blocked = list(policy.blocked_reasons)
    if policy.approval_required and not (approval or voice):
        blocked.append("valid explicit approval required")
    if policy.strong_approval_required and not (
        values.get("strong_approval_present") or values.get("strong_approval_satisfied")
    ):
        blocked.append("valid strong approval required")
    if policy.double_confirmation_required and not (
        values.get("double_confirmation_present") or values.get("double_confirmation_satisfied")
    ):
        blocked.append("double confirmation required")
    if policy.triple_confirmation_required and not (
        values.get("triple_confirmation_present") or values.get("triple_confirmation_satisfied")
    ):
        blocked.append("triple confirmation required")
    return list(dict.fromkeys(blocked))


def mark_2_external_operations_markers() -> Dict[str, Any]:
    status = Mark2ExternalOperationsStatus().to_dict()
    for collision in ("current_mark", "mark_2_macro", "next_recommended_macro_pr"):
        status.pop(collision)
    return {
        "mark_2_macro_4_external_ops_ai_cli": True,
        "mark_2_macro_4_external_ops_ai_cli_available": True,
        **status,
        "real_external_invocation_disabled_by_default": True,
        "real_deploy_disabled_by_default": True,
        "stripe_live_disabled_by_default": True,
        "email_send_disabled_by_default": True,
        "domain_publish_disabled_by_default": True,
        "codex_cli_real_invocation_disabled_by_default": True,
        "claude_code_real_invocation_disabled_by_default": True,
        "claude_cowork_real_invocation_disabled_by_default": True,
        "api_fallback_real_invocation_disabled_by_default": True,
        "access_material_disabled_by_default": True,
        "external_network_disabled_by_default": True,
        "production_operations_disabled_by_default": True,
        "money_movement_disabled_by_default": True,
        "human_approval_required_for_sensitive_actions": True,
        "voice_approval_supported_for_external_ops": True,
        "costs_are_estimated_or_unknown": True,
        "no_fake_costs": True,
        "mark_2_release_candidate_planned": True,
        "mark_2_macro_4_next_recommended_macro_pr": NEXT_RECOMMENDED_MACRO_PR,
    }


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def safe_text(value: Any, fallback: str = "") -> str:
    safe, _ = redact_sensitive_data(str(value or ""))
    return _clean(safe) or fallback
