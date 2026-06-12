from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List
from uuid import uuid4

from jarvis.mark_2_external_operations_policy import ExternalOperationsPolicyEngine, safe_text


@dataclass(frozen=True)
class RoutineExecutionBridge:
    routine_id: str
    routine_type: str
    selected_adapter: str
    reason_for_adapter_choice: str
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
    would_execute: bool = False
    blocked_reasons: List[str] = field(default_factory=lambda: ["real routine execution is disabled"])
    next_safe_step: str = "Review adapter choice, scope, cost, approval, audit, and stop plan."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def preview(cls, **values: Any) -> "RoutineExecutionBridge":
        routine = str(values.get("routine_type") or "unknown").lower()
        use_case = str(values.get("use_case") or "").lower()
        if routine == "ai_coding":
            adapter, reason = "Codex CLI", "subscription CLI suits heavy supervised coding in a worktree"
        elif routine == "desktop_cowork":
            adapter, reason = "Claude Cowork/Desktop", "supervised desktop routine requested"
        elif routine in {"external_api"} or use_case in {"json_router", "classification", "worker", "automation_24_7", "fallback"}:
            adapter, reason = "ApiFallbackAdapter", "stable structured JSON, worker, 24/7, or fallback use case"
        elif routine in {"deploy", "payment", "email"}:
            adapter, reason = f"{routine.title()}OperationAdapter", "specialized external-operation candidate required"
        else:
            adapter, reason = "LocalScriptAdapter", "local-first is preferred when the mission permits it"
        operation = {"deploy": "deploy", "payment": "payment", "email": "email", "external_api": "api_fallback"}.get(routine, "ai_cli")
        policy = ExternalOperationsPolicyEngine().evaluate(**{
            **values,
            "operation_type": operation,
            "provider": adapter,
            "rollback_or_stop_plan": values.get("rollback_or_stop_plan") or "stop before execution",
        })
        return cls(
            routine_id=str(values.get("routine_id") or uuid4()),
            routine_type=routine,
            selected_adapter=adapter,
            reason_for_adapter_choice=reason,
            risk_level=policy.risk_level.value,
            policy_decision="eligible_after_valid_approval" if policy.eligible_after_valid_approval else "permanent_denial",
            approval_state="not_requested",
            worktree=safe_text(values.get("worktree"), "required for AI coding"),
            sandbox_scope=list(values.get("sandbox_scope") or []),
            command_or_action_preview=safe_text(values.get("command_or_action_preview"), "preview only; no action will run"),
            expected_outputs=list(values.get("expected_outputs") or ["summary", "audit"]),
            cost_usage_summary="estimated or unknown; no provider billing queried",
            audit_required=True,
            rollback_or_stop_plan=safe_text(values.get("rollback_or_stop_plan"), "stop before execution"),
            eligible_after_valid_approval=policy.eligible_after_valid_approval,
            blocked_reasons=list(dict.fromkeys(policy.blocked_reasons + ["real routine execution is disabled"])),
        )
