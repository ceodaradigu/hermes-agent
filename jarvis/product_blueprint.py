from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.pricing_strategy import PricingPlan


@dataclass(frozen=True)
class CapabilityBlockPlan:
    selected_blocks: List[str]
    omitted_blocks: List[str]
    why_each_block_is_needed: Dict[str, str]
    why_each_block_is_not_needed: Dict[str, str]
    auth_block_needed: bool
    api_block_needed: bool
    frontend_block_needed: bool
    database_block_needed: bool
    payments_block_needed: bool
    admin_panel_needed: bool
    analytics_block_needed: bool
    notification_block_needed: bool
    tests_block_needed: bool
    security_block_needed: bool
    documentation_block_needed: bool
    customization_required: List[str]
    reusable_patterns_used_as_guardrails: bool = True
    rigid_template_used: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "reusable_patterns_used_as_guardrails", True)
        object.__setattr__(self, "rigid_template_used", False)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "CapabilityBlockPlan":
        source = dict(data or {})
        optional = {
            "auth": source.get("auth_block_needed") is True,
            "api": source.get("api_block_needed") is True,
            "frontend": source.get("frontend_block_needed") is True,
            "database": source.get("database_block_needed") is True,
            "payments": source.get("payments_block_needed") is True,
            "admin_panel": source.get("admin_panel_needed") is True,
            "analytics": source.get("analytics_block_needed") is True,
            "notifications": source.get("notification_block_needed") is True,
            "tests": source.get("tests_block_needed", True) is True,
            "security": source.get("security_block_needed", True) is True,
            "documentation": source.get("documentation_block_needed", True) is True,
        }
        selected = [name for name, needed in optional.items() if needed]
        omitted = [name for name, needed in optional.items() if not needed]
        needed_reasons = _dict(source.get("why_each_block_is_needed"))
        omitted_reasons = _dict(source.get("why_each_block_is_not_needed"))
        for name in selected:
            needed_reasons.setdefault(name, f"{name} supports an explicit product requirement")
        for name in omitted:
            omitted_reasons.setdefault(name, f"{name} is not justified by the current MVP scope")
        return cls(
            selected_blocks=selected,
            omitted_blocks=omitted,
            why_each_block_is_needed=needed_reasons,
            why_each_block_is_not_needed=omitted_reasons,
            customization_required=_list(source.get("customization_required")),
            auth_block_needed=optional["auth"],
            api_block_needed=optional["api"],
            frontend_block_needed=optional["frontend"],
            database_block_needed=optional["database"],
            payments_block_needed=optional["payments"],
            admin_panel_needed=optional["admin_panel"],
            analytics_block_needed=optional["analytics"],
            notification_block_needed=optional["notifications"],
            tests_block_needed=optional["tests"],
            security_block_needed=optional["security"],
            documentation_block_needed=optional["documentation"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SaaSProductBlueprint:
    product_name: str
    one_liner: str
    target_customer: str
    core_problem: str
    value_proposition: str
    differentiation: str
    reason_to_exist: str
    feature_set: List[str]
    mvp_scope: List[str]
    out_of_scope: List[str]
    user_roles: List[str]
    data_model_preview: List[str]
    api_surface_preview: List[str]
    frontend_pages: List[str]
    backend_services: List[str]
    auth_required: bool
    billing_required: bool
    analytics_required: bool
    privacy_notes: List[str]
    security_notes: List[str]
    success_metrics: List[str]
    primary_success_metric: str
    launch_checklist: List[str]
    risks: List[str]
    assumptions: List[str]
    unknowns: List[str]
    pricing_preview: Dict[str, Any]
    quality_gate_passed: bool

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "SaaSProductBlueprint":
        source = dict(data or {})
        differentiation = _text(source.get("differentiation"))
        reason = _text(source.get("reason_to_exist"))
        mvp = _list(source.get("mvp_scope"))[:10]
        unknowns = _list(source.get("unknowns"))
        if not mvp:
            unknowns.append("concrete MVP scope")
        passed = bool(differentiation and reason and mvp) and source.get("differentiation_quality_gate_passed", True) is True
        pricing_data = source.get("pricing") if isinstance(source.get("pricing"), dict) else source
        return cls(
            product_name=_text(source.get("product_name")) or "Unnamed product",
            one_liner=_text(source.get("one_liner")) or "Product proposition requires clarification",
            target_customer=_text(source.get("target_customer")) or "unknown",
            core_problem=_text(source.get("core_problem")) or "unknown",
            value_proposition=_text(source.get("value_proposition")) or "unknown",
            differentiation=differentiation or "unknown",
            reason_to_exist=reason or "unknown",
            feature_set=_list(source.get("feature_set"))[:15],
            mvp_scope=mvp,
            out_of_scope=_list(source.get("out_of_scope")),
            user_roles=_list(source.get("user_roles")),
            data_model_preview=_list(source.get("data_model_preview")),
            api_surface_preview=_list(source.get("api_surface_preview")),
            frontend_pages=_list(source.get("frontend_pages")),
            backend_services=_list(source.get("backend_services")),
            auth_required=source.get("auth_required") is True,
            billing_required=source.get("billing_required") is True,
            analytics_required=source.get("analytics_required") is True,
            privacy_notes=_list(source.get("privacy_notes")),
            security_notes=_list(source.get("security_notes")),
            success_metrics=_list(source.get("success_metrics")),
            primary_success_metric=_text(source.get("primary_success_metric")) or "unknown",
            launch_checklist=_list(source.get("launch_checklist")),
            risks=_list(source.get("risks")),
            assumptions=_list(source.get("assumptions")),
            unknowns=list(dict.fromkeys(unknowns)),
            pricing_preview=PricingPlan.from_request(pricing_data).to_dict(),
            quality_gate_passed=passed,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TechStackRecommendation:
    frontend_stack: str
    backend_stack: str
    database: str
    auth: str
    payments: str
    hosting: str
    analytics: str
    email: str
    monitoring: str
    estimated_monthly_cost: Optional[float]
    free_tier_possible: bool
    paid_services_needed: List[str]
    approval_required_for_paid_services: bool
    why_this_stack: List[str]
    rejected_alternatives: List[str]
    risk_notes: List[str]
    alternatives: List[str]

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "TechStackRecommendation":
        source = dict(data or {})
        paid = _list(source.get("paid_services_needed"))
        cost = _number(source.get("estimated_monthly_cost"))
        return cls(
            frontend_stack=_text(source.get("frontend_stack")) or "static HTML/CSS or lightweight React only if interactivity requires it",
            backend_stack=_text(source.get("backend_stack")) or "Python FastAPI only if server behavior is required",
            database=_text(source.get("database")) or "none until persistent product data is required",
            auth=_text(source.get("auth")) or "none until user accounts are required",
            payments=_text(source.get("payments")) or "none until billing is validated",
            hosting=_text(source.get("hosting")) or "low-cost preview hosting candidate",
            analytics=_text(source.get("analytics")) or "privacy-conscious basic events",
            email=_text(source.get("email")) or "none until notification use cases are validated",
            monitoring=_text(source.get("monitoring")) or "basic health and error logs",
            estimated_monthly_cost=cost,
            free_tier_possible=source.get("free_tier_possible", True) is True,
            paid_services_needed=paid,
            approval_required_for_paid_services=bool(paid or (cost is not None and cost > 0)),
            why_this_stack=_list(source.get("why_this_stack")) or ["minimizes cost and complexity for the stated MVP"],
            rejected_alternatives=_list(source.get("rejected_alternatives")),
            risk_notes=_list(source.get("risk_notes")) + ["credentials are not assumed or loaded"],
            alternatives=_list(source.get("alternatives")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RepoScaffoldPlan:
    repo_name: str
    repo_visibility: str
    folders_to_create: List[str]
    files_to_create: List[str]
    package_manager: str
    commands_preview: List[str]
    env_vars_required: List[str]
    secrets_required: List[str]
    tests_to_add: List[str]
    ci_preview: List[str]
    docker_needed: bool
    local_run_command: str
    product_specific_files: List[str]
    product_specific_tests: List[str]
    would_write_files: bool
    would_create_repo: bool
    approval_required: bool
    strong_approval_required: bool
    eligible_after_valid_approval: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "would_write_files", False)
        object.__setattr__(self, "would_create_repo", False)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "RepoScaffoldPlan":
        source = dict(data or {})
        external = source.get("external_repo_requested") is True
        sensitive = source.get("sensitive_filesystem_requested") is True
        valid = source.get("valid_approval_present") is True
        strong = source.get("strong_approval_present") is True
        return cls(
            repo_name=_text(source.get("repo_name")) or "product-repo-preview",
            repo_visibility=_choice(source.get("repo_visibility"), {"private", "public", "unknown"}, "private"),
            folders_to_create=_list(source.get("folders_to_create")),
            files_to_create=_list(source.get("files_to_create")),
            package_manager=_text(source.get("package_manager")) or "product-dependent",
            commands_preview=_list(source.get("commands_preview")),
            env_vars_required=_list(source.get("env_vars_required")),
            secrets_required=_list(source.get("secrets_required")),
            tests_to_add=_list(source.get("tests_to_add")),
            ci_preview=_list(source.get("ci_preview")),
            docker_needed=source.get("docker_needed") is True,
            local_run_command=_text(source.get("local_run_command")) or "define after stack selection",
            product_specific_files=_list(source.get("product_specific_files")),
            product_specific_tests=_list(source.get("product_specific_tests")),
            would_write_files=False,
            would_create_repo=False,
            approval_required=True,
            strong_approval_required=external or sensitive,
            eligible_after_valid_approval=valid and (not (external or sensitive) or strong),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LandingPagePlan:
    headline: str
    subheadline: str
    target_customer: str
    pain_points: List[str]
    benefits: List[str]
    feature_blocks: List[str]
    differentiation_section: str
    pricing_section: str
    faq: List[str]
    call_to_action: str
    trust_notes: List[str]
    privacy_notes: List[str]
    analytics_needed: bool
    publish_ready: bool
    assumptions: List[str]
    unknowns: List[str]

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "LandingPagePlan":
        source = dict(data or {})
        differentiation = _text(source.get("differentiation_section"))
        target = _text(source.get("target_customer"))
        headline = _text(source.get("headline"))
        return cls(
            headline=headline or "Clarify the product promise",
            subheadline=_text(source.get("subheadline")) or "Explain the specific outcome without unsupported claims",
            target_customer=target or "unknown",
            pain_points=_list(source.get("pain_points")),
            benefits=_list(source.get("benefits")),
            feature_blocks=_list(source.get("feature_blocks")),
            differentiation_section=differentiation or "Differentiation requires refinement",
            pricing_section=_text(source.get("pricing_section")) or "Pricing hypothesis requires validation",
            faq=_list(source.get("faq")),
            call_to_action=_text(source.get("call_to_action")) or "Join the validation waitlist",
            trust_notes=_list(source.get("trust_notes")) + ["do not use false guarantees or fabricated social proof"],
            privacy_notes=_list(source.get("privacy_notes")),
            analytics_needed=source.get("analytics_needed") is True,
            publish_ready=bool(headline and target and differentiation) and source.get("claims_verified", False) is True,
            assumptions=_list(source.get("assumptions")),
            unknowns=_list(source.get("unknowns")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:1000]


def _list(value: Any) -> List[str]:
    return [_text(item) for item in (value or []) if _text(item)]


def _dict(value: Any) -> Dict[str, str]:
    return {str(key): _text(item) for key, item in (value or {}).items()} if isinstance(value, dict) else {}


def _number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 2) if number >= 0 else None


def _choice(value: Any, choices: set[str], default: str) -> str:
    normalized = _text(value).lower()
    return normalized if normalized in choices else default
