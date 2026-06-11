from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.approval_execution_semantics import GlobalApprovalExecutionSemantics


@dataclass(frozen=True)
class PublishingPlan:
    target_platform: str
    domain_plan: str
    environment: str
    build_command: str
    output_directory: str
    required_env_vars: List[str]
    required_secrets: List[str]
    preflight_checks: List[str]
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    would_publish: bool
    would_call_external: bool
    eligible_after_valid_approval: bool
    blocked_reasons: List[str]
    rollback_or_unpublish_plan: List[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "would_publish", False)
        object.__setattr__(self, "would_call_external", False)

    @classmethod
    def from_request(
        cls,
        data: Optional[Dict[str, Any]],
        semantics: Optional[GlobalApprovalExecutionSemantics] = None,
    ) -> "PublishingPlan":
        source = dict(data or {})
        environment = _choice(source.get("environment"), {"preview", "staging", "production"}, "preview")
        production = environment == "production"
        rollback = _list(source.get("rollback_or_unpublish_plan"))
        authority = semantics or GlobalApprovalExecutionSemantics()
        decision = authority.preview_decision(
            action_name=f"publish {environment}",
            action_category="critical" if production else "normal",
            risk_level="critical" if production else "medium",
            valid_approval_present=source.get("valid_approval_present") is True,
            strong_approval_present=source.get("strong_approval_present") is True,
            double_confirmation_present=source.get("double_confirmation_present") is True,
            context_fingerprint_matches=source.get("context_fingerprint_matches") is True,
            permission_gates_passed=source.get("permission_gates_passed") is True,
            audit_present=source.get("audit_present") is True,
            rollback_or_stop_plan_required=production,
            rollback_or_stop_plan_present=bool(rollback),
            execution_capable_when_approved=True,
            illegal=source.get("illegal") is True,
            unsafe=source.get("unsafe") is True,
            unauthorized=source.get("unauthorized") is True,
            impossible=source.get("impossible") is True,
            unsupported=source.get("unsupported") is True,
        )
        blocked = list(decision.blocked_reasons)
        blocked.append("publishing execution is disabled in this PR")
        return cls(
            target_platform=_choice(source.get("target_platform"), {"vercel", "render", "github_pages", "cloudflare", "manual", "unknown"}, "unknown"),
            domain_plan=_text(source.get("domain_plan")) or "unknown",
            environment=environment,
            build_command=_text(source.get("build_command")) or "unknown",
            output_directory=_text(source.get("output_directory")) or "unknown",
            required_env_vars=_list(source.get("required_env_vars")),
            required_secrets=_list(source.get("required_secrets")),
            preflight_checks=_list(source.get("preflight_checks")),
            approval_required=True,
            strong_approval_required=decision.strong_approval_required,
            double_confirmation_required=decision.double_confirmation_required,
            would_publish=False,
            would_call_external=False,
            eligible_after_valid_approval=decision.execution_allowed,
            blocked_reasons=list(dict.fromkeys(blocked)),
            rollback_or_unpublish_plan=rollback,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DeployExecutionPlan:
    deploy_target: str
    environment: str
    artifact: str
    preflight_checks: List[str]
    migration_required: bool
    secrets_required: List[str]
    healthcheck_url_preview: str
    smoke_tests: List[str]
    rollback_plan: List[str]
    owner_approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    execution_candidate: bool
    execution_allowed: bool
    eligible_after_valid_approval: bool
    would_deploy: bool
    would_call_external: bool
    would_touch_production: bool
    blocked_reasons: List[str]
    warning_message: str
    confirmation_phrase: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "execution_allowed", False)
        object.__setattr__(self, "would_deploy", False)
        object.__setattr__(self, "would_call_external", False)
        object.__setattr__(self, "would_touch_production", False)

    @classmethod
    def from_request(
        cls,
        data: Optional[Dict[str, Any]],
        semantics: Optional[GlobalApprovalExecutionSemantics] = None,
    ) -> "DeployExecutionPlan":
        source = dict(data or {})
        environment = _choice(source.get("environment"), {"preview", "staging", "production"}, "preview")
        production = environment == "production"
        rollback = _list(source.get("rollback_plan"))
        secrets = _list(source.get("secrets_required"))
        required_secrets_available = source.get("required_secrets_available") is True or not secrets
        authority = semantics or GlobalApprovalExecutionSemantics()
        decision = authority.preview_decision(
            action_name=f"deploy {environment}",
            action_category="critical" if production else "normal",
            risk_level="critical" if production else "medium",
            valid_approval_present=source.get("valid_approval_present") is True,
            strong_approval_present=source.get("strong_approval_present") is True,
            double_confirmation_present=source.get("double_confirmation_present") is True,
            context_fingerprint_matches=source.get("context_fingerprint_matches") is True,
            permission_gates_passed=source.get("permission_gates_passed") is True,
            audit_present=source.get("audit_present") is True,
            rollback_or_stop_plan_required=production,
            rollback_or_stop_plan_present=bool(rollback),
            execution_capable_when_approved=True,
            illegal=source.get("illegal") is True,
            unsafe=source.get("unsafe") is True,
            unauthorized=source.get("unauthorized") is True,
            impossible=source.get("impossible") is True,
            unsupported=source.get("unsupported") is True,
        )
        blocked = list(decision.blocked_reasons)
        if not required_secrets_available:
            blocked.append("required secrets are unavailable")
        blocked.append("deploy execution is disabled in this PR")
        eligible = decision.execution_allowed and required_secrets_available
        return cls(
            deploy_target=_text(source.get("deploy_target")) or "unknown",
            environment=environment,
            artifact=_text(source.get("artifact")) or "unknown",
            preflight_checks=_list(source.get("preflight_checks")),
            migration_required=source.get("migration_required") is True,
            secrets_required=secrets,
            healthcheck_url_preview=_text(source.get("healthcheck_url_preview")) or "unknown",
            smoke_tests=_list(source.get("smoke_tests")),
            rollback_plan=rollback,
            owner_approval_required=True,
            strong_approval_required=decision.strong_approval_required,
            double_confirmation_required=decision.double_confirmation_required,
            execution_candidate=eligible,
            execution_allowed=False,
            eligible_after_valid_approval=eligible,
            would_deploy=False,
            would_call_external=False,
            would_touch_production=False,
            blocked_reasons=list(dict.fromkeys(blocked)),
            warning_message=decision.warning_message,
            confirmation_phrase=decision.required_confirmation_phrase,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PublishingDeployControl:
    def __init__(self, semantics: Optional[GlobalApprovalExecutionSemantics] = None) -> None:
        self.semantics = semantics or GlobalApprovalExecutionSemantics()

    def publishing_plan(self, data: Optional[Dict[str, Any]]) -> PublishingPlan:
        return PublishingPlan.from_request(data, self.semantics)

    def deploy_plan(self, data: Optional[Dict[str, Any]]) -> DeployExecutionPlan:
        return DeployExecutionPlan.from_request(data, self.semantics)


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:1000]


def _list(value: Any) -> List[str]:
    return [_text(item) for item in (value or []) if _text(item)]


def _choice(value: Any, choices: set[str], default: str) -> str:
    normalized = _text(value).lower()
    return normalized if normalized in choices else default
