from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List
from uuid import uuid4

from jarvis.mark_2_external_operations_policy import (
    ExternalOperationsPolicyEngine,
    approval_blockers,
    valid_approval,
    valid_voice_approval,
    safe_text,
)


@dataclass(frozen=True)
class DeployOperationCandidate:
    candidate_id: str
    provider: str
    environment: str
    project_name: str
    artifact_summary: str
    build_command_preview: str
    deploy_command_preview: str
    env_vars_required_summary: str
    access_material_required: bool
    preflight_checks: List[str]
    smoke_tests: List[str]
    healthcheck_url_preview: str
    rollback_plan: str
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    triple_confirmation_required: bool
    valid_approval_present: bool
    valid_voice_approval_present: bool
    eligible_after_valid_approval: bool
    would_deploy: bool = False
    would_call_external: bool = False
    would_touch_production: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    next_safe_step: str = "Review preflight, approval, provider access, healthcheck, and rollback plan."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark2DeployAdapter:
    def __init__(self) -> None:
        self.policy = ExternalOperationsPolicyEngine()

    def preview(self, **values: Any) -> DeployOperationCandidate:
        environment = str(values.get("environment") or "preview").lower()
        rollback = _text(values.get("rollback_plan"))
        policy = self.policy.evaluate(**{
            **values,
            "operation_type": "deploy",
            "environment": environment,
            "rollback_or_stop_plan": rollback,
            "production_impact": environment == "production",
            "access_material_required": True,
            "network_required": True,
        })
        return DeployOperationCandidate(
            candidate_id=str(uuid4()),
            provider=safe_text(values.get("provider"), "unknown"),
            environment=environment,
            project_name=safe_text(values.get("project_name"), "unnamed project"),
            artifact_summary=safe_text(values.get("artifact_summary"), "operator-provided artifact summary required"),
            build_command_preview=safe_text(values.get("build_command_preview"), "provider build command preview not provided"),
            deploy_command_preview=safe_text(values.get("deploy_command_preview"), "provider deploy command preview not provided"),
            env_vars_required_summary="runtime configuration names must be provided manually; values are never read",
            access_material_required=True,
            preflight_checks=list(values.get("preflight_checks") or ["tests pass", "artifact reviewed", "provider target confirmed"]),
            smoke_tests=list(values.get("smoke_tests") or ["health endpoint responds", "critical user flow reviewed"]),
            healthcheck_url_preview=safe_text(values.get("healthcheck_url_preview"), "manual provider healthcheck required"),
            rollback_plan=safe_text(rollback, "missing"),
            approval_required=policy.approval_required,
            strong_approval_required=policy.strong_approval_required,
            double_confirmation_required=policy.double_confirmation_required,
            triple_confirmation_required=policy.triple_confirmation_required,
            valid_approval_present=valid_approval(values),
            valid_voice_approval_present=valid_voice_approval(values),
            eligible_after_valid_approval=policy.eligible_after_valid_approval,
            would_touch_production=environment == "production",
            blocked_reasons=approval_blockers(policy, values),
        )


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())
