from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.approval_execution_semantics import ARCHITECTURAL_RULE, GlobalApprovalExecutionSemantics
from jarvis.product_blueprint import (
    CapabilityBlockPlan,
    LandingPagePlan,
    RepoScaffoldPlan,
    SaaSProductBlueprint,
    TechStackRecommendation,
)
from jarvis.product_validation_engine import ProductValidationEngine
from jarvis.publishing_deploy_control import PublishingDeployControl
from jarvis.saas_execution_candidates import ProductExecutionCandidate


NEXT_RECOMMENDED_MACRO_PR = "Post-S Macro 10 — Mark 1 Hardening, E2E Real Ops & Release Candidate"
_ACTIONS = {
    "intake_idea", "validate_product", "review_differentiation", "plan_capability_blocks",
    "build_blueprint", "recommend_stack", "plan_repo_scaffold", "plan_landing",
    "plan_publishing", "plan_deploy", "prepare_execution_candidate", "review_launch_readiness",
}


@dataclass(frozen=True)
class AdaptiveSaaSBuilderStatus:
    control_plane_only: bool = True
    preview_only: bool = True
    adaptive_saas_builder_available: bool = True
    product_builder_adaptativo_available: bool = True
    product_validation_available: bool = True
    differentiation_engine_available: bool = True
    product_blueprint_available: bool = True
    capability_blocks_available: bool = True
    scaffold_planning_available: bool = True
    publishing_plan_available: bool = True
    deploy_plan_available: bool = True
    execution_candidates_available: bool = True
    launch_readiness_review_available: bool = True
    template_builder_mode: bool = False
    rigid_boilerplate_generation: bool = False
    cloned_product_generation_allowed: bool = False
    reusable_patterns_are_guardrails: bool = True
    capability_blocks_are_composable: bool = True
    real_repo_creation_enabled: bool = False
    real_filesystem_write_enabled: bool = False
    real_publish_enabled: bool = False
    real_deploy_enabled: bool = False
    external_platform_calls_enabled: bool = False
    production_operations_enabled: bool = False
    execution_requires_valid_approval: bool = True
    critical_publish_deploy_requires_double_confirmation: bool = True
    restrictions_are_approval_gates: bool = True
    current_mark: str = "Mark 1"
    next_recommended_macro_pr: str = NEXT_RECOMMENDED_MACRO_PR

    def __post_init__(self) -> None:
        for name in (
            "control_plane_only", "preview_only", "adaptive_saas_builder_available",
            "product_builder_adaptativo_available", "product_validation_available",
            "differentiation_engine_available", "product_blueprint_available",
            "capability_blocks_available", "scaffold_planning_available",
            "publishing_plan_available", "deploy_plan_available", "execution_candidates_available",
            "launch_readiness_review_available", "reusable_patterns_are_guardrails",
            "capability_blocks_are_composable", "execution_requires_valid_approval",
            "critical_publish_deploy_requires_double_confirmation", "restrictions_are_approval_gates",
        ):
            object.__setattr__(self, name, True)
        for name in (
            "template_builder_mode", "rigid_boilerplate_generation", "cloned_product_generation_allowed",
            "real_repo_creation_enabled", "real_filesystem_write_enabled", "real_publish_enabled",
            "real_deploy_enabled", "external_platform_calls_enabled", "production_operations_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "current_mark", "Mark 1")
        object.__setattr__(self, "next_recommended_macro_pr", NEXT_RECOMMENDED_MACRO_PR)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdaptiveSaaSBuilderActionPreview:
    action_type: str
    preview_only: bool = True
    would_execute: bool = False
    would_call_external: bool = False
    would_write_files: bool = False
    would_create_repo: bool = False
    would_publish: bool = False
    would_deploy: bool = False
    approval_required: bool = False
    strong_approval_required: bool = False
    double_confirmation_required: bool = False
    eligible_after_valid_approval: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    next_safe_step: str = "review preview"

    def __post_init__(self) -> None:
        object.__setattr__(self, "preview_only", True)
        for name in ("would_execute", "would_call_external", "would_write_files", "would_create_repo", "would_publish", "would_deploy"):
            object.__setattr__(self, name, False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LaunchReadinessReview:
    product_ready: bool
    differentiation_ready: bool
    pricing_ready: bool
    legal_ready: bool
    privacy_ready: bool
    security_ready: bool
    analytics_ready: bool
    support_ready: bool
    deploy_ready: bool
    rollback_ready: bool
    approval_ready: bool
    launch_score: int
    blockers: List[str]
    warnings: List[str]
    next_actions: List[str]

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "LaunchReadinessReview":
        source = dict(data or {})
        fields = {
            name: source.get(name) is True
            for name in (
                "product_ready", "differentiation_ready", "pricing_ready", "legal_ready",
                "privacy_ready", "security_ready", "analytics_ready", "support_ready",
                "deploy_ready", "rollback_ready", "approval_ready",
            )
        }
        blockers = _list(source.get("blockers"))
        for name in ("differentiation_ready", "legal_ready", "privacy_ready", "security_ready"):
            if not fields[name]:
                blockers.append(f"{name.removesuffix('_ready')} readiness is required")
        if source.get("environment") == "production" and not fields["approval_ready"]:
            blockers.append("valid production approval is required")
        if source.get("environment") == "production" and not fields["rollback_ready"]:
            blockers.append("rollback readiness is required for production")
        warnings = _list(source.get("warnings"))
        if not fields["analytics_ready"]:
            warnings.append("success metrics or analytics readiness is incomplete")
        score = round(sum(fields.values()) / len(fields) * 100)
        return cls(**fields, launch_score=score, blockers=list(dict.fromkeys(blockers)), warnings=list(dict.fromkeys(warnings)), next_actions=_list(source.get("next_actions")) or ["resolve blockers and repeat launch readiness review"])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def adaptive_saas_builder_markers() -> Dict[str, bool]:
    return {
        "post_s_adaptive_saas_builder_publishing_deploy_execution": True,
        "adaptive_saas_builder_available": True,
        "product_builder_adaptativo_available": True,
        "template_builder_mode_disabled": True,
        "rigid_boilerplate_generation_disabled": True,
        "cloned_product_generation_disallowed": True,
        "reusable_patterns_as_guardrails": True,
        "capability_blocks_composable": True,
        "product_validation_available": True,
        "differentiation_engine_available": True,
        "product_blueprint_available": True,
        "scaffold_planning_available": True,
        "publishing_plan_available": True,
        "deploy_plan_available": True,
        "product_execution_candidates_available": True,
        "launch_readiness_review_available": True,
        "real_repo_creation_disabled": True,
        "real_filesystem_write_disabled": True,
        "real_publish_disabled": True,
        "real_deploy_disabled": True,
        "external_platform_calls_disabled": True,
        "production_operations_disabled": True,
        "builder_actions_blocked_without_approval": True,
        "builder_actions_executable_after_valid_approval": True,
        "production_deploy_requires_strong_approval": True,
        "production_deploy_requires_double_confirmation": True,
        "rollback_required_for_production": True,
        "adaptive_saas_builder_mark_1": True,
    }


class AdaptiveSaaSBuilder:
    def __init__(self, semantics: Optional[GlobalApprovalExecutionSemantics] = None) -> None:
        self.semantics = semantics or GlobalApprovalExecutionSemantics()
        self.validation = ProductValidationEngine()
        self.publishing = PublishingDeployControl(self.semantics)

    def status(self) -> Dict[str, Any]:
        return AdaptiveSaaSBuilderStatus().to_dict()

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            "architectural_rule": ARCHITECTURAL_RULE,
            "default_deny_without_valid_approval": True,
            "quality_rule": "If two generated products look like twins, the Product Builder Adaptativo has failed.",
            "no_fake_market_claims": True,
            "no_confirmed_revenue_invented": True,
            "wake_phrase_is_not_builder_or_deploy_permission": True,
            "scheduler_due_is_not_builder_or_deploy_permission": True,
            "memory_active_is_not_builder_or_deploy_permission": True,
            "tool_layer_does_not_invoke_external_platforms": True,
            "controlled_runtime_bridge_provides_readiness_not_deploy_execution": True,
        }

    def preview_intake(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return self.validation.intake(data).to_dict()

    def preview_validation(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return self.validation.validate(data).to_dict()

    def preview_differentiation(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return self.validation.review_differentiation(data).to_dict()

    def preview_capability_blocks(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return CapabilityBlockPlan.from_request(data).to_dict()

    def preview_blueprint(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return SaaSProductBlueprint.from_request(data).to_dict()

    def preview_stack(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return TechStackRecommendation.from_request(data).to_dict()

    def preview_scaffold(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return RepoScaffoldPlan.from_request(data).to_dict()

    def preview_landing(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return LandingPagePlan.from_request(data).to_dict()

    def preview_publishing(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return self.publishing.publishing_plan(data).to_dict()

    def preview_deploy(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return self.publishing.deploy_plan(data).to_dict()

    def preview_execution_candidate(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return ProductExecutionCandidate.from_request(data, self.semantics).to_dict()

    def preview_launch_readiness(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return LaunchReadinessReview.from_request(data).to_dict()

    def preview_action(self, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        source = dict(data or {})
        action = _text(source.get("action_type")).lower() or "unknown"
        execution_action = action in {"plan_repo_scaffold", "plan_publishing", "plan_deploy", "prepare_execution_candidate"}
        critical = action in {"plan_publishing", "plan_deploy"} and source.get("environment") == "production"
        valid = source.get("valid_approval_present") is True
        strong = source.get("strong_approval_present") is True
        double = source.get("double_confirmation_present") is True
        supported = action in _ACTIONS
        eligible = supported and (not execution_action or valid) and (not critical or (strong and double))
        blocked = []
        if not supported:
            blocked.append("unsupported Adaptive SaaS Builder preview action")
        if execution_action and not valid:
            blocked.append("valid explicit approval required")
        if critical and not strong:
            blocked.append("valid strong approval required")
        if critical and not double:
            blocked.append("double confirmation required")
        blocked.append("builder execution is disabled in this PR")
        return AdaptiveSaaSBuilderActionPreview(
            action_type=action,
            approval_required=execution_action,
            strong_approval_required=critical,
            double_confirmation_required=critical,
            eligible_after_valid_approval=eligible,
            blocked_reasons=blocked,
            next_safe_step="review the product-specific preview and required gates",
        ).to_dict()


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:1000]


def _list(value: Any) -> List[str]:
    return [_text(item) for item in (value or []) if _text(item)]
