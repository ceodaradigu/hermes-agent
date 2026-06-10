from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_UNKNOWN = "unknown"
_REDACTED = "[redacted sensitive input]"
_CONFIDENCE = {"unknown", "low", "medium", "high"}
_PREFERENCE_TYPES = {"tone", "workflow", "format", "project", "risk", "monetization", "learning", "unknown"}
_GOAL_TYPES = {"revenue", "portfolio", "automation", "learning", "product", "job", "unknown"}
_MEMORY_CATEGORIES = {
    "preference", "workflow", "project", "business_goal", "communication_style", "safety_constraint", "unknown",
}
_SENSITIVITY_LEVELS = {"none", "low", "medium", "high", "unknown"}
_REVIEW_STATUSES = {"pending", "acceptable", "needs_edit", "reject", "unknown"}
_LIFECYCLE_ACTIONS = {"propose", "review", "approve", "activate", "deactivate", "reverse", "audit", "unknown"}
_RECOMMENDATION_TYPES = {"tone", "workflow", "focus", "monetization", "product", "learning", "unknown"}
_SENSITIVE_RISKS = {"none", "low", "medium", "high", "unknown"}
_SENSITIVE_MARKERS = (
    ".env", "api key", "api-key", "api_key", "apikey", "authorization", "bearer",
    "credential", "credentials", "password", "private key", "private_key", "secret", "token",
)


@dataclass(frozen=True)
class AdvancedPersonalizationStatus:
    prepare_only: bool = True
    advanced_personalization_available: bool = False
    user_model_available: bool = False
    opaque_learning_enabled: bool = False
    automatic_memory_enabled: bool = False
    memory_write_enabled: bool = False
    memory_activation_enabled: bool = False
    memory_deactivation_enabled: bool = False
    sensitive_inference_enabled: bool = False
    manipulation_enabled: bool = False
    action_authorization_from_memory_enabled: bool = False
    private_certainty_enabled: bool = False
    external_calls_enabled: bool = False
    secrets_access_enabled: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    execution_enabled: bool = False
    persistence_enabled: bool = False

    def __post_init__(self) -> None:
        _force_safe(self)

    @classmethod
    def placeholder(cls) -> "AdvancedPersonalizationStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AdvancedPersonalizationStatus":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class UserModelSafetyPolicy:
    prepare_only: bool = True
    no_opaque_learning_by_default: bool = True
    no_auto_memory_by_default: bool = True
    no_sensitive_inference_by_default: bool = True
    no_manipulation_by_default: bool = True
    no_memory_as_permission: bool = True
    no_private_certainty_claims: bool = True
    explicit_memory_proposals_required: bool = True
    review_required_before_memory_activation: bool = True
    reversible_memory_required: bool = True
    audit_required: bool = True
    uncertainty_required: bool = True
    approval_required_for_memory_changes: bool = True
    strong_approval_required_for_sensitive_memory: bool = True
    strong_approval_required_for_actions_based_on_personalization: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        for name in self.__dataclass_fields__:
            if name != "prepare_only":
                object.__setattr__(self, name, True)

    @classmethod
    def placeholder(cls) -> "UserModelSafetyPolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "UserModelSafetyPolicy":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class UserPreferenceProfilePreview:
    prepare_only: bool = True
    preference_name: str = _UNKNOWN
    preference_type: str = _UNKNOWN
    evidence_preview: List[str] = field(default_factory=list)
    confidence: str = _UNKNOWN
    uncertainty_notes: List[str] = field(default_factory=list)
    would_store_memory: bool = False
    would_activate_memory: bool = False
    approval_required: bool = True
    sensitive_inference_made: bool = False
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _safe_common(self, choices={"preference_type": _PREFERENCE_TYPES, "confidence": _CONFIDENCE})
        _force_true(self, "approval_required")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(dict(data or {}), cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class SpeechStylePatternPreview:
    prepare_only: bool = True
    pattern_name: str = _UNKNOWN
    observed_style_preview: str = _UNKNOWN
    preferred_response_style: str = _UNKNOWN
    examples_preview: List[str] = field(default_factory=list)
    uncertainty_notes: List[str] = field(default_factory=list)
    no_identity_claim: bool = True
    would_store_memory: bool = False
    would_adapt_response_only: bool = False
    approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "no_identity_claim", "approval_required")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(dict(data or {}), cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class DecisionModelPreview:
    prepare_only: bool = True
    decision_axis: str = _UNKNOWN
    observed_preference: str = _UNKNOWN
    tradeoffs: List[str] = field(default_factory=list)
    risk_tolerance: str = _UNKNOWN
    monetization_bias: str = _UNKNOWN
    contrarian_needed: bool = False
    uncertainty_notes: List[str] = field(default_factory=list)
    no_manipulation: bool = True
    would_store_memory: bool = False
    would_authorize_action: bool = False
    approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "no_manipulation", "approval_required")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(dict(data or {}), cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class BusinessGoalModelPreview:
    prepare_only: bool = True
    goal_name: str = _UNKNOWN
    goal_type: str = _UNKNOWN
    expected_value: str = _UNKNOWN
    constraints: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    priority_reason: str = _UNKNOWN
    no_fake_roi: bool = True
    no_confirmed_revenue_without_evidence: bool = True
    would_store_memory: bool = False
    approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self, choices={"goal_type": _GOAL_TYPES})
        _force_true(self, "no_fake_roi", "no_confirmed_revenue_without_evidence", "approval_required")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(dict(data or {}), cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ContrarianModeProfilePreview:
    prepare_only: bool = True
    contrarian_mode_requested: bool = False
    critique_style: str = _UNKNOWN
    challenge_threshold: str = _UNKNOWN
    allowed_pushback: List[str] = field(default_factory=list)
    blocked_pushback: List[str] = field(default_factory=list)
    no_humiliation: bool = True
    no_manipulation: bool = True
    would_store_memory: bool = False
    approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "no_humiliation", "no_manipulation", "approval_required")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(dict(data or {}), cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MemoryProposalPreview:
    prepare_only: bool = True
    proposal_id_preview: str = _UNKNOWN
    proposed_memory: str = _UNKNOWN
    memory_category: str = _UNKNOWN
    evidence: List[str] = field(default_factory=list)
    usefulness: str = _UNKNOWN
    risks: List[str] = field(default_factory=list)
    sensitivity_level: str = _UNKNOWN
    reversible: bool = True
    activation_required: bool = False
    would_store: bool = False
    would_activate: bool = False
    approval_required: bool = True
    strong_approval_required: bool = False

    def __post_init__(self) -> None:
        _safe_common(self, choices={"memory_category": _MEMORY_CATEGORIES, "sensitivity_level": _SENSITIVITY_LEVELS})
        _force_true(self, "reversible", "approval_required")
        object.__setattr__(self, "strong_approval_required", self.sensitivity_level in {"medium", "high"} or self.strong_approval_required)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "MemoryProposalPreview":
        source = dict(data or {})
        return cls(
            **_select(source, cls, exclude={"strong_approval_required"}),
            strong_approval_required=_strong_approval_requested(source),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MemoryReviewPreview:
    prepare_only: bool = True
    proposal_id_preview: str = _UNKNOWN
    review_status: str = _UNKNOWN
    acceptance_reasons: List[str] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    sensitivity_warnings: List[str] = field(default_factory=list)
    uncertainty_notes: List[str] = field(default_factory=list)
    suggested_revision: str = _UNKNOWN
    would_approve: bool = False
    would_reject: bool = False
    would_activate: bool = False

    def __post_init__(self) -> None:
        _safe_common(self, choices={"review_status": _REVIEW_STATUSES})
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(dict(data or {}), cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MemoryLifecyclePreview:
    prepare_only: bool = True
    proposal_id_preview: str = _UNKNOWN
    requested_action: str = _UNKNOWN
    approval_required: bool = True
    strong_approval_required: bool = False
    would_create_memory: bool = False
    would_update_memory: bool = False
    would_activate_memory: bool = False
    would_deactivate_memory: bool = False
    would_delete_memory: bool = False
    would_persist: bool = False
    audit_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self, choices={"requested_action": _LIFECYCLE_ACTIONS})
        _force_true(self, "approval_required", "audit_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "MemoryLifecyclePreview":
        source = dict(data or {})
        return cls(
            **_select(source, cls, exclude={"strong_approval_required"}),
            strong_approval_required=_strong_approval_requested(source),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MemoryAuditReversalPreview:
    prepare_only: bool = True
    memory_id_preview: str = _UNKNOWN
    audit_reason: str = _UNKNOWN
    current_state_preview: str = _UNKNOWN
    reversal_available: bool = True
    deactivation_available: bool = True
    deletion_available: bool = False
    would_reverse: bool = False
    would_deactivate: bool = False
    would_delete: bool = False
    would_persist: bool = False

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "reversal_available", "deactivation_available")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(dict(data or {}), cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class UncertaintyHandlingPreview:
    prepare_only: bool = True
    claim_or_preference: str = _UNKNOWN
    confidence: str = _UNKNOWN
    unknowns: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    evidence_needed: List[str] = field(default_factory=list)
    must_ask_user_before_using_as_fact: bool = True
    no_private_certainty_claim: bool = True
    would_store_memory: bool = False

    def __post_init__(self) -> None:
        _safe_common(self, choices={"confidence": _CONFIDENCE})
        _force_true(self, "no_private_certainty_claim")
        object.__setattr__(self, "must_ask_user_before_using_as_fact", self.confidence in {"unknown", "low"})
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(dict(data or {}), cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PersonalizationRecommendationPreview:
    prepare_only: bool = True
    recommendation_name: str = _UNKNOWN
    basis: List[str] = field(default_factory=list)
    expected_benefit: str = _UNKNOWN
    risks: List[str] = field(default_factory=list)
    uncertainty_notes: List[str] = field(default_factory=list)
    recommendation_type: str = _UNKNOWN
    no_manipulation: bool = True
    no_action_authorization: bool = True
    would_execute: bool = False
    would_store_memory: bool = False

    def __post_init__(self) -> None:
        _safe_common(self, choices={"recommendation_type": _RECOMMENDATION_TYPES})
        _force_true(self, "no_manipulation", "no_action_authorization")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(dict(data or {}), cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class SensitiveInferenceGuardPreview:
    prepare_only: bool = True
    input_category: str = _UNKNOWN
    sensitive_attribute_risk: str = _UNKNOWN
    blocked_inferences: List[str] = field(default_factory=list)
    allowed_non_sensitive_summary: str = _UNKNOWN
    requires_explicit_user_request: bool = True
    would_infer_sensitive_attribute: bool = False
    would_store_sensitive_memory: bool = False
    strong_approval_required: bool = False

    def __post_init__(self) -> None:
        _safe_common(self, choices={"sensitive_attribute_risk": _SENSITIVE_RISKS})
        _force_true(self, "requires_explicit_user_request")
        object.__setattr__(
            self,
            "strong_approval_required",
            self.sensitive_attribute_risk in {"medium", "high"} or self.strong_approval_required,
        )
        if self.sensitive_attribute_risk in {"medium", "high", "unknown"} and not self.blocked_inferences:
            object.__setattr__(self, "blocked_inferences", ["Sensitive attribute inference is blocked."])
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "SensitiveInferenceGuardPreview":
        source = dict(data or {})
        return cls(
            **_select(source, cls, exclude={"strong_approval_required"}),
            strong_approval_required=_strong_approval_requested(source),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PersonalizationApprovalRequirements:
    prepare_only: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False
    approval_gateway_called: bool = False
    approval_created: bool = False
    approval_granted: bool = False
    approval_rejected: bool = False
    memory_change_authorized: bool = False
    action_authorized: bool = False

    def __post_init__(self) -> None:
        _force_true(self, "approval_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PersonalizationApprovalRequirements":
        return cls(strong_approval_required=_strong_approval_requested(dict(data or {})))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


_FORCED_FALSE = {
    "advanced_personalization_available", "user_model_available", "opaque_learning_enabled",
    "automatic_memory_enabled", "memory_write_enabled", "memory_activation_enabled",
    "memory_deactivation_enabled", "sensitive_inference_enabled", "manipulation_enabled",
    "action_authorization_from_memory_enabled", "private_certainty_enabled", "external_calls_enabled",
    "secrets_access_enabled", "hermes_called", "approval_gateway_called", "execution_enabled",
    "persistence_enabled", "would_store_memory", "would_activate_memory", "sensitive_inference_made",
    "would_adapt_response_only", "would_authorize_action", "activation_required", "would_store",
    "would_activate", "would_approve", "would_reject", "would_create_memory", "would_update_memory",
    "would_deactivate_memory", "would_delete_memory", "would_persist", "deletion_available",
    "would_reverse", "would_deactivate", "would_delete", "would_execute", "would_infer_sensitive_attribute",
    "would_store_sensitive_memory", "approval_created", "approval_granted", "approval_rejected",
    "memory_change_authorized", "action_authorized",
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
        result[name] = list(item) if isinstance(item, list) else item
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
            object.__setattr__(value, name, _choice(item, choices[name]) if name in choices else _safe_text(item, _UNKNOWN))


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
    return text if text in choices else _UNKNOWN


def _select(source: Dict[str, Any], cls: Any, *, exclude: Optional[set[str]] = None) -> Dict[str, Any]:
    blocked = _FORCED_FALSE | {"prepare_only", "approval_required"} | set(exclude or set())
    return {
        name: source[name]
        for name in cls.__dataclass_fields__
        if name not in blocked and name in source and source[name] is not None
    }


def _strong_approval_requested(source: Dict[str, Any]) -> bool:
    sensitivity = _choice(source.get("sensitivity_level") or source.get("sensitive_attribute_risk"), _SENSITIVITY_LEVELS)
    names = (
        "sensitive_memory", "sensitive_source", "private_source", "cross_context",
        "action_based_on_personalization", "private_data", "sensitive_attribute",
    )
    return sensitivity in {"medium", "high"} or any(
        bool(source.get(name) or source.get(f"{name}_requested")) for name in names
    )
