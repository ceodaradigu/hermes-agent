from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_UNKNOWN = "unknown"
_REDACTED = "[redacted sensitive input]"
_MATURITY = {"unknown", "experimental", "stable", "deprecated"}
_SCORES = {"unknown", "low", "medium", "high"}
_DECISIONS = {"reject", "keep_watching", "investigate", "sandbox_spike", "propose_pr", "blocked", "unknown"}
_PROPOSAL_DECISIONS = {"reject", "investigate", "sandbox_spike", "propose_pr", "blocked", "unknown"}
_HIGH_RISK = {"high", "critical", "blocked"}
_UNRESOLVED_RISK = {"unknown", "high", "critical", "blocked"}
_SENSITIVE_MARKERS = (
    ".env", "api key", "api-key", "api_key", "apikey", "authorization", "bearer",
    "credential", "credentials", "password", "private key", "private_key", "secret", "token",
)


@dataclass(frozen=True)
class ContinuousLearningStatus:
    prepare_only: bool = True
    continuous_learning_available: bool = False
    tech_radar_available: bool = False
    external_research_enabled: bool = False
    auto_update_enabled: bool = False
    auto_install_enabled: bool = False
    auto_deploy_enabled: bool = False
    runtime_modification_enabled: bool = False
    prompt_modification_enabled: bool = False
    dependency_modification_enabled: bool = False
    pr_creation_enabled: bool = False
    external_calls_enabled: bool = False
    secrets_access_enabled: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    execution_enabled: bool = False
    persistence_enabled: bool = False

    def __post_init__(self) -> None:
        _force_safe(self)

    @classmethod
    def placeholder(cls) -> "ContinuousLearningStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ContinuousLearningStatus":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class TechRadarSafetyPolicy:
    prepare_only: bool = True
    no_auto_update_by_default: bool = True
    no_auto_install_by_default: bool = True
    no_auto_deploy_by_default: bool = True
    no_runtime_modification_by_default: bool = True
    no_prompt_modification_by_default: bool = True
    no_dependency_modification_by_default: bool = True
    no_external_research_by_default: bool = True
    no_secret_access_by_default: bool = True
    no_pr_creation_by_default: bool = True
    approval_required_for_proposals: bool = True
    strong_approval_required_for_install: bool = True
    strong_approval_required_for_runtime_changes: bool = True
    strong_approval_required_for_prompt_changes: bool = True
    strong_approval_required_for_production: bool = True
    strong_approval_required_for_credentials: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        for name in self.__dataclass_fields__:
            if name != "prepare_only":
                object.__setattr__(self, name, True)

    @classmethod
    def placeholder(cls) -> "TechRadarSafetyPolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "TechRadarSafetyPolicy":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class TechnologyCandidateProfile:
    prepare_only: bool = True
    candidate_name: str = _UNKNOWN
    category: str = _UNKNOWN
    source_reference: str = _UNKNOWN
    claimed_benefit: str = _UNKNOWN
    use_case: str = _UNKNOWN
    maturity: str = _UNKNOWN
    license: str = _UNKNOWN
    dependency_risk: str = _UNKNOWN
    security_risk: str = _UNKNOWN
    maintenance_signal: str = _UNKNOWN
    revenue_or_efficiency_hypothesis: str = _UNKNOWN
    no_external_lookup: bool = True
    would_install: bool = False
    would_modify_runtime: bool = False
    would_create_pr: bool = False
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _safe_common(self, choices={"maturity": _MATURITY})
        _force_true(self, "no_external_lookup")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "TechnologyCandidateProfile":
        source = dict(data or {})
        warnings = _safe_list(source.get("warnings"))
        if _choice(source.get("license"), set()) == _UNKNOWN:
            warnings.append("License is unknown; adoption cannot be recommended.")
        return cls(
            candidate_name=source.get("candidate_name", _UNKNOWN),
            category=source.get("category", _UNKNOWN),
            source_reference=source.get("source_reference", _UNKNOWN),
            claimed_benefit=source.get("claimed_benefit", _UNKNOWN),
            use_case=source.get("use_case", _UNKNOWN),
            maturity=source.get("maturity", _UNKNOWN),
            license=source.get("license", _UNKNOWN),
            dependency_risk=source.get("dependency_risk", _UNKNOWN),
            security_risk=source.get("security_risk", _UNKNOWN),
            maintenance_signal=source.get("maintenance_signal", _UNKNOWN),
            revenue_or_efficiency_hypothesis=source.get("revenue_or_efficiency_hypothesis", _UNKNOWN),
            warnings=warnings,
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class RelevanceFilterPreview:
    prepare_only: bool = True
    candidate_name: str = _UNKNOWN
    relevance_score: str = _UNKNOWN
    fit_reasons: List[str] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    monetization_relevance: str = _UNKNOWN
    time_saving_relevance: str = _UNKNOWN
    error_reduction_relevance: str = _UNKNOWN
    revenue_enablement_relevance: str = _UNKNOWN
    unknowns: List[str] = field(default_factory=list)
    no_decision_final: bool = True

    def __post_init__(self) -> None:
        _safe_common(self, choices={
            "relevance_score": _SCORES, "monetization_relevance": _SCORES,
            "time_saving_relevance": _SCORES, "error_reduction_relevance": _SCORES,
            "revenue_enablement_relevance": _SCORES,
        })
        _force_true(self, "no_decision_final")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "RelevanceFilterPreview":
        source = dict(data or {})
        return cls(**_select(source, cls, exclude={"prepare_only", "no_decision_final"}))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ContrarianReviewPreview:
    prepare_only: bool = True
    candidate_name: str = _UNKNOWN
    skeptical_questions: List[str] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    hidden_costs: List[str] = field(default_factory=list)
    security_concerns: List[str] = field(default_factory=list)
    maintenance_concerns: List[str] = field(default_factory=list)
    vendor_lock_in_risk: str = _UNKNOWN
    overengineering_risk: str = _UNKNOWN
    recommendation_pressure_check: str = _UNKNOWN
    no_hype_mode: bool = True

    def __post_init__(self) -> None:
        _safe_common(self)
        questions = list(self.skeptical_questions)
        if not questions:
            questions = [
                "What evidence would disprove the claimed benefit?",
                "Can the same outcome be achieved more simply?",
            ]
        object.__setattr__(self, "skeptical_questions", questions)
        _force_true(self, "no_hype_mode")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ContrarianReviewPreview":
        return cls(**_select(dict(data or {}), cls, exclude={"prepare_only", "no_hype_mode"}))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class LearningProposalPreview:
    prepare_only: bool = True
    proposal_title: str = _UNKNOWN
    candidate_name: str = _UNKNOWN
    summary: str = _UNKNOWN
    expected_impact: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tests_required: List[str] = field(default_factory=list)
    rollback_plan: List[str] = field(default_factory=list)
    decision_recommendation: str = _UNKNOWN
    confidence: str = _UNKNOWN
    would_create_pr: bool = False
    would_modify_code: bool = False
    approval_required: bool = True
    strong_approval_required: bool = False

    def __post_init__(self) -> None:
        _safe_common(self, choices={"decision_recommendation": _PROPOSAL_DECISIONS, "confidence": _SCORES})
        _force_true(self, "approval_required")
        object.__setattr__(self, "strong_approval_required", bool(self.strong_approval_required))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "LearningProposalPreview":
        source = dict(data or {})
        return cls(
            **_select(
                source,
                cls,
                exclude={
                    "prepare_only", "would_create_pr", "would_modify_code",
                    "approval_required", "strong_approval_required",
                },
            ),
            strong_approval_required=_strong_risk_requested(source),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ProposalImpactAnalysis:
    prepare_only: bool = True
    impact_categories: Dict[str, str] = field(default_factory=dict)
    no_fake_metrics: bool = True
    unknowns_preserved: bool = True
    no_confirmed_roi: bool = True
    confirmed_roi: str = _UNKNOWN

    def __post_init__(self) -> None:
        categories = dict(self.impact_categories or {})
        allowed = ("time_saved", "error_reduction", "quality_improvement", "revenue_enablement", "cost_reduction")
        object.__setattr__(
            self,
            "impact_categories",
            {name: _safe_text(categories.get(name), _UNKNOWN) for name in allowed},
        )
        object.__setattr__(self, "confirmed_roi", _safe_text(self.confirmed_roi, _UNKNOWN))
        _force_true(self, "no_fake_metrics", "unknowns_preserved")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ProposalImpactAnalysis":
        source = dict(data or {})
        explicit = (
            source.get("confirmed_roi_explicitly_provided") is True
            and bool(_safe_text(source.get("confirmed_roi")))
        )
        return cls(
            impact_categories=dict(source.get("impact_categories") or {}),
            no_confirmed_roi=not explicit,
            confirmed_roi=source.get("confirmed_roi", _UNKNOWN) if explicit else _UNKNOWN,
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ProposalRiskAnalysis:
    prepare_only: bool = True
    security_risk: str = _UNKNOWN
    dependency_risk: str = _UNKNOWN
    maintenance_risk: str = _UNKNOWN
    product_risk: str = _UNKNOWN
    cost_risk: str = _UNKNOWN
    privacy_risk: str = _UNKNOWN
    production_risk: str = _UNKNOWN
    secret_risk: str = _UNKNOWN
    runtime_risk: str = _UNKNOWN
    blocked: bool = True
    strong_approval_required: bool = False

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ProposalRiskAnalysis":
        source = dict(data or {})
        unresolved = any(_risk(source.get(name)) in _UNRESOLVED_RISK for name in (
            "secret_risk", "production_risk", "runtime_risk", "dependency_risk",
        ))
        high = any(_risk(source.get(name)) in _HIGH_RISK for name in (
            "security_risk", "dependency_risk", "maintenance_risk", "product_risk", "cost_risk",
            "privacy_risk", "production_risk", "secret_risk", "runtime_risk",
        )) or _strong_risk_requested(source)
        return cls(
            **_select(source, cls, exclude={"prepare_only", "blocked", "strong_approval_required"}),
            blocked=unresolved,
            strong_approval_required=high,
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PRPlannerPreview:
    prepare_only: bool = True
    branch_name_preview: str = _UNKNOWN
    files_likely_to_change: List[str] = field(default_factory=list)
    test_plan: List[str] = field(default_factory=list)
    review_plan: List[str] = field(default_factory=list)
    rollback_plan: List[str] = field(default_factory=list)
    migration_notes: List[str] = field(default_factory=list)
    would_create_branch: bool = False
    would_commit: bool = False
    would_push: bool = False
    would_create_pr: bool = False
    approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "approval_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PRPlannerPreview":
        return cls(**_select(dict(data or {}), cls, exclude=_FORCED_FALSE | {"prepare_only", "approval_required"}))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ApprovalWorkflowPreview:
    prepare_only: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False
    approval_gateway_called: bool = False
    approval_created: bool = False
    approval_granted: bool = False
    approval_rejected: bool = False
    next_manual_review_steps: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "approval_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ApprovalWorkflowPreview":
        source = dict(data or {})
        return cls(
            strong_approval_required=_strong_risk_requested(source),
            next_manual_review_steps=_safe_list(source.get("next_manual_review_steps")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class LearningBacklogPreview:
    prepare_only: bool = True
    backlog_items: List[str] = field(default_factory=list)
    priority_order: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    blocked_items: List[str] = field(default_factory=list)
    review_cadence: str = _UNKNOWN
    would_persist: bool = False
    would_schedule: bool = False
    would_execute: bool = False

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "LearningBacklogPreview":
        return cls(**_select(dict(data or {}), cls, exclude=_FORCED_FALSE | {"prepare_only"}))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class TechRadarDecisionPreview:
    prepare_only: bool = True
    decision: str = _UNKNOWN
    rationale: List[str] = field(default_factory=list)
    required_evidence: List[str] = field(default_factory=list)
    required_approvals: List[str] = field(default_factory=list)
    no_auto_adoption: bool = True
    would_install: bool = False
    would_update: bool = False
    would_deploy: bool = False
    would_modify_runtime: bool = False

    def __post_init__(self) -> None:
        _safe_common(self, choices={"decision": _DECISIONS})
        _force_true(self, "no_auto_adoption")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "TechRadarDecisionPreview":
        source = dict(data or {})
        decision = "blocked" if _strong_risk_requested(source) else source.get("decision", _UNKNOWN)
        return cls(
            decision=decision,
            rationale=_safe_list(source.get("rationale")),
            required_evidence=_safe_list(source.get("required_evidence")),
            required_approvals=_safe_list(source.get("required_approvals")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


_FORCED_FALSE = {
    "continuous_learning_available", "tech_radar_available", "external_research_enabled",
    "auto_update_enabled", "auto_install_enabled", "auto_deploy_enabled", "runtime_modification_enabled",
    "prompt_modification_enabled", "dependency_modification_enabled", "pr_creation_enabled",
    "external_calls_enabled", "secrets_access_enabled", "hermes_called", "approval_gateway_called",
    "execution_enabled", "persistence_enabled", "would_install", "would_modify_runtime", "would_create_pr",
    "would_modify_code", "would_create_branch", "would_commit", "would_push", "approval_created",
    "approval_granted", "approval_rejected", "would_persist", "would_schedule", "would_execute",
    "would_update", "would_deploy",
}


def _force_safe(value: Any) -> None:
    object.__setattr__(value, "prepare_only", True)
    for name in _FORCED_FALSE:
        if name in value.__dataclass_fields__:
            object.__setattr__(value, name, False)


def _force_true(value: Any, *names: str) -> None:
    for name in names:
        object.__setattr__(value, name, True)


def _serialize(value: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for name in value.__dataclass_fields__:
        item = getattr(value, name)
        result[name] = list(item) if isinstance(item, list) else dict(item) if isinstance(item, dict) else item
    result["prepare_only"] = True
    for name in _FORCED_FALSE:
        if name in result:
            result[name] = False
    return result


def _safe_common(value: Any, *, choices: Optional[Dict[str, set[str]]] = None) -> None:
    choices = choices or {}
    for name in value.__dataclass_fields__:
        item = getattr(value, name)
        if isinstance(item, list):
            object.__setattr__(value, name, _safe_list(item))
        elif isinstance(item, str):
            safe_item = _choice(item, choices[name]) if name in choices else _safe_text(item, _UNKNOWN)
            object.__setattr__(value, name, safe_item)


def _safe_text(value: Any, default: str = "") -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return default
    if any(marker in text.lower() for marker in _SENSITIVE_MARKERS):
        return _REDACTED
    return text[:500]


def _safe_list(value: Any) -> List[str]:
    items = value if isinstance(value, list) else []
    return [_safe_text(item) for item in items[:100] if _safe_text(item)]


def _choice(value: Any, choices: set[str]) -> str:
    text = str(value or "").strip().lower()
    if not choices:
        return _safe_text(text, _UNKNOWN)
    return text if text in choices else _UNKNOWN


def _risk(value: Any) -> str:
    return _choice(value, {"unknown", "low", "medium", "high", "critical", "blocked", "resolved", "none"})


def _strong_risk_requested(source: Dict[str, Any]) -> bool:
    risk_names = (
        "install", "runtime", "prompt", "production", "prod", "credential", "credentials",
        "secret", "secrets", "deploy", "dependency_modification",
    )
    return (
        any(source.get(name) is True or source.get(f"{name}_requested") is True for name in risk_names)
        or any(_risk(source.get(f"{name}_risk")) in _HIGH_RISK for name in risk_names)
    )


def _select(source: Dict[str, Any], cls: Any, *, exclude: set[str]) -> Dict[str, Any]:
    return {
        name: source[name]
        for name in cls.__dataclass_fields__
        if name not in exclude and name in source and source[name] is not None
    }
