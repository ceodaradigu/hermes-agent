from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from jarvis.mark_2_external_operations_policy import ExternalOperationsPolicyEngine, safe_text


_IMPROVEMENT_PLAN_STEPS = [
    "Inspect repo status manually or via an approved read-only endpoint.",
    "Review Mark 2 RC readiness and dashboard state.",
    "Identify candidate improvements from docs/tests after explicit approval.",
    "Open a worktree before any file edits.",
    "Run tests before PR close.",
]


@dataclass(frozen=True)
class RoutineExecutionBridge:
    routine_id: str
    routine_type: str
    preferred_mode: str
    selected_adapter: str
    selected_adapter_mode: str
    reason_for_adapter_choice: str
    adapter_selection_respected_user_flags: bool
    risk_level: str
    policy_decision: str
    approval_state: str
    worktree: str
    sandbox_scope: List[str]
    command_or_action_preview: str
    expected_outputs: List[str]
    cost_usage_summary: str
    audit_required: bool
    rollback_or_stop_plan: str
    eligible_after_valid_approval: bool
    real_invocation_allowed: bool = False
    file_write_allowed: bool = False
    network_allowed: bool = False
    codex_real_allowed: bool = False
    claude_real_allowed: bool = False
    deploy_allowed: bool = False
    money_allowed: bool = False
    improvement_plan_preview: Dict[str, Any] = field(default_factory=dict)
    risk_review: Dict[str, Any] = field(default_factory=dict)
    audit_summary: Dict[str, Any] = field(default_factory=dict)
    user_flags_summary: Dict[str, bool] = field(default_factory=dict)
    unmet_requirements: List[str] = field(default_factory=list)
    would_execute: bool = False
    blocked_reasons: List[str] = field(default_factory=lambda: ["real routine execution is disabled"])
    next_safe_step: str = "Review adapter choice, scope, cost, approval, audit, and stop plan."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def preview(cls, **values: Any) -> "RoutineExecutionBridge":
        routine = str(values.get("routine_type") or "unknown").strip().lower()
        preferred_mode = str(values.get("preferred_mode") or "conservative_default").strip().lower()
        expected_outputs = list(values.get("expected_outputs") or ["summary", "audit"])
        flags = _user_flags(values)
        adapter, adapter_mode, reason, unmet = _select_adapter(
            routine=routine,
            use_case=str(values.get("use_case") or "").strip().lower(),
            preferred_mode=preferred_mode,
            flags=flags,
        )
        operation = {
            "deploy": "deploy",
            "payment": "payment",
            "email": "email",
            "external_api": "api_fallback",
        }.get(routine, "ai_cli")
        policy = ExternalOperationsPolicyEngine().evaluate(**{
            **values,
            "operation_type": operation,
            "provider": adapter,
            "network_required": adapter == "ApiFallbackAdapter",
            "access_material_required": adapter not in {"LocalScriptAdapter", "NoSuitableAdapter"},
            "external_network_enabled": flags["allow_network"],
            "production_operations_enabled": flags["allow_deploy"],
            "money_movement_enabled": flags["allow_money"],
            "rollback_or_stop_plan": values.get("rollback_or_stop_plan") or "stop before execution",
        })
        selection_eligible = policy.eligible_after_valid_approval and adapter_mode not in {
            "blocked",
            "no_suitable_adapter",
        }
        policy_decision = (
            adapter_mode
            if adapter_mode in {"blocked", "no_suitable_adapter"}
            else "eligible_after_valid_approval" if selection_eligible else "permanent_denial"
        )
        blocked = list(policy.blocked_reasons)
        blocked.extend(unmet)
        blocked.append("real routine execution is disabled")
        if not flags["allow_real_execution"]:
            blocked.append("allow_real_execution is false")
        if not flags["allow_file_write"]:
            blocked.append("file writes are disabled by user flag")
        return cls(
            routine_id=str(values.get("routine_id") or uuid4()),
            routine_type=routine,
            preferred_mode=preferred_mode,
            selected_adapter=adapter,
            selected_adapter_mode=adapter_mode,
            reason_for_adapter_choice=reason,
            adapter_selection_respected_user_flags=True,
            risk_level=policy.risk_level.value,
            policy_decision=policy_decision,
            approval_state="not_requested",
            worktree=safe_text(values.get("worktree"), "required for AI coding"),
            sandbox_scope=list(values.get("sandbox_scope") or []),
            command_or_action_preview=safe_text(values.get("command_or_action_preview"), "preview only; no action will run"),
            expected_outputs=expected_outputs,
            cost_usage_summary="estimated or unknown; no provider billing queried",
            audit_required=True,
            rollback_or_stop_plan=safe_text(values.get("rollback_or_stop_plan"), "stop before execution"),
            eligible_after_valid_approval=selection_eligible,
            file_write_allowed=flags["allow_file_write"],
            network_allowed=flags["allow_network"],
            codex_real_allowed=flags["allow_codex_real"],
            claude_real_allowed=flags["allow_claude_real"],
            deploy_allowed=flags["allow_deploy"],
            money_allowed=flags["allow_money"],
            improvement_plan_preview=_improvement_plan_preview(expected_outputs),
            risk_review=_risk_review(flags),
            audit_summary=_audit_summary(),
            user_flags_summary=flags,
            unmet_requirements=list(dict.fromkeys(unmet)),
            blocked_reasons=list(dict.fromkeys(blocked)),
            next_safe_step=_next_safe_step(adapter, adapter_mode),
        )


def _user_flags(values: Dict[str, Any]) -> Dict[str, bool]:
    return {
        name: values.get(name) is True
        for name in (
            "allow_real_execution",
            "allow_file_write",
            "allow_network",
            "allow_codex_real",
            "allow_claude_real",
            "allow_deploy",
            "allow_money",
        )
    }


def _select_adapter(
    *, routine: str, use_case: str, preferred_mode: str, flags: Dict[str, bool]
) -> Tuple[str, str, str, List[str]]:
    if preferred_mode == "local_first_preview":
        cli_status = (
            "AI CLI real invocation disabled by flags"
            if not flags["allow_codex_real"] and not flags["allow_claude_real"]
            else "local preview requested ahead of any allowed AI CLI candidate"
        )
        return (
            "LocalScriptAdapter",
            "preview_only",
            f"local_first_preview requested; {cli_status}; using local preview candidate.",
            [],
        )
    if preferred_mode == "subscription_cli":
        if routine != "ai_coding":
            return (
                "NoSuitableAdapter",
                "no_suitable_adapter",
                "subscription_cli requested, but the routine is not an AI coding mission.",
                ["subscription CLI requires routine_type=ai_coding"],
            )
        if flags["allow_codex_real"]:
            return (
                "Codex CLI",
                "preview_only",
                "subscription_cli requested and Codex is allowed as a preview candidate; real invocation remains disabled.",
                [],
            )
        if flags["allow_claude_real"]:
            return (
                "Claude Code",
                "preview_only",
                "subscription_cli requested and Claude is allowed as a preview candidate; real invocation remains disabled.",
                [],
            )
        return (
            "LocalScriptAdapter",
            "preview_only",
            "subscription_cli requested; Codex and Claude real invocation disabled by flags; using local preview candidate.",
            ["allow_codex_real or allow_claude_real required for a subscription CLI candidate"],
        )
    if preferred_mode == "api_fallback":
        if flags["allow_network"]:
            return (
                "ApiFallbackAdapter",
                "preview_only",
                "api_fallback requested and network allowed; API adapter remains preview-only.",
                [],
            )
        return (
            "ApiFallbackAdapter",
            "blocked",
            "api_fallback requested, but network is disabled; API adapter is blocked and preview-only.",
            ["allow_network is required for API fallback execution"],
        )
    if routine == "ai_coding":
        return (
            "LocalScriptAdapter",
            "preview_only",
            "No recognized preferred_mode was provided; using a conservative local preview candidate.",
            [] if preferred_mode == "conservative_default" else [f"unknown preferred_mode: {preferred_mode}"],
        )
    if routine == "desktop_cowork" and flags["allow_claude_real"]:
        return (
            "Claude Cowork/Desktop",
            "preview_only",
            "Claude Cowork is allowed as a preview candidate; real invocation remains disabled.",
            [],
        )
    if routine == "external_api" or use_case in {"json_router", "classification", "worker", "automation_24_7", "fallback"}:
        mode = "preview_only" if flags["allow_network"] else "blocked"
        return (
            "ApiFallbackAdapter",
            mode,
            "API fallback candidate selected conservatively; network and real invocation gates remain enforced.",
            [] if flags["allow_network"] else ["allow_network is required for API fallback execution"],
        )
    if routine in {"deploy", "payment", "email"}:
        operation_flag = flags["allow_deploy"] if routine == "deploy" else flags["allow_money"] if routine == "payment" else True
        allowed = flags["allow_network"] and operation_flag
        unmet = []
        if not flags["allow_network"]:
            unmet.append("allow_network is required for external operation execution")
        if not operation_flag:
            unmet.append(f"{routine} operation is disabled by user flags")
        return (
            f"{routine.title()}OperationAdapter",
            "candidate" if allowed else "blocked",
            "Specialized external-operation candidate selected; user flags and preview-only boundary remain enforced.",
            unmet,
        )
    return (
        "LocalScriptAdapter",
        "preview_only",
        "No recognized preferred_mode was provided; using a conservative local preview candidate.",
        [] if preferred_mode == "conservative_default" else [f"unknown preferred_mode: {preferred_mode}"],
    )


def _improvement_plan_preview(expected_outputs: List[str]) -> Dict[str, Any]:
    if "improvement_plan" not in expected_outputs:
        return {}
    return {
        "mode": "preview_only",
        "based_on": "operator-provided payload only; repository not inspected",
        "will_edit_files": False,
        "will_invoke_ai_cli": False,
        "steps": list(_IMPROVEMENT_PLAN_STEPS),
        "requires_real_execution_for_deeper_analysis": True,
    }


def _risk_review(flags: Dict[str, bool]) -> Dict[str, bool]:
    return {
        "no_production": True,
        "no_money": True,
        "no_deploy": True,
        "no_email": True,
        "no_dns": True,
        "no_codex_or_claude_real": True,
        "no_file_write": True,
        "no_network": True,
        "would_execute": False,
    }


def _audit_summary() -> Dict[str, bool]:
    return {
        "audit_required": True,
        "external_call_made": False,
        "real_tool_invoked": False,
        "file_write_made": False,
        "access_material_read": False,
        "safe_to_render": True,
    }


def _next_safe_step(adapter: str, adapter_mode: str) -> str:
    if adapter_mode in {"blocked", "no_suitable_adapter"}:
        return "Review unmet requirements and explicitly approve only the minimum required flags."
    if adapter == "LocalScriptAdapter":
        return "Review the payload-only local preview before approving any read-only repo inspection."
    return "Review the preview candidate, user flags, and unmet requirements; do not invoke the real adapter."
