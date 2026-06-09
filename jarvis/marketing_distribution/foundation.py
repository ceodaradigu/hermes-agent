from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_UNKNOWN = "unknown"
_REDACTED = "[redacted sensitive input]"
_CONFIDENCE = {"unknown", "low", "medium", "high"}
_COST = {"unknown", "zero", "low", "medium", "high"}
_SENSITIVE_MARKERS = (
    ".env", "api key", "api-key", "api_key", "apikey", "authorization", "bearer",
    "client secret", "client_secret", "credential", "credentials", "email address",
    "password", "phone number", "private key", "private_key", "secret", "token",
)
_DEFAULT_LAUNCH_ASSETS = [
    "reviewed campaign plan",
    "reviewed content distribution pack",
    "measurement plan",
    "legal review",
    "strong approval",
]
_DEFAULT_MISSING = [
    "real distribution remains disabled",
    "strong approval has not been granted",
]


@dataclass(frozen=True)
class MarketingDistributionStatus:
    prepare_only: bool = True
    marketing_engine_available: bool = False
    campaign_execution_enabled: bool = False
    publishing_enabled: bool = False
    external_account_connection_enabled: bool = False
    paid_ads_enabled: bool = False
    email_sending_enabled: bool = False
    dm_sending_enabled: bool = False
    social_posting_enabled: bool = False
    scraping_enabled: bool = False
    identity_usage_enabled: bool = False
    budget_spend_enabled: bool = False
    external_calls_enabled: bool = False
    secrets_access_enabled: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        _force_safe(self)

    @classmethod
    def placeholder(cls) -> "MarketingDistributionStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "MarketingDistributionStatus":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MarketingDistributionPolicy:
    prepare_only: bool = True
    no_publish_by_default: bool = True
    no_send_by_default: bool = True
    no_paid_ads_by_default: bool = True
    no_scraping_by_default: bool = True
    no_spam_by_default: bool = True
    no_external_accounts_by_default: bool = True
    no_identity_usage_by_default: bool = True
    no_budget_spend_by_default: bool = True
    no_fake_claims_by_default: bool = True
    no_fake_social_proof_by_default: bool = True
    review_required_before_distribution: bool = True
    strong_approval_required_for_publish: bool = True
    strong_approval_required_for_sending: bool = True
    strong_approval_required_for_paid_ads: bool = True
    strong_approval_required_for_identity: bool = True
    strong_approval_required_for_external_accounts: bool = True
    strong_approval_required_for_budget_spend: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        for name in self.__dataclass_fields__:
            if name != "prepare_only":
                object.__setattr__(self, name, True)

    @classmethod
    def placeholder(cls) -> "MarketingDistributionPolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "MarketingDistributionPolicy":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class AudienceSegmentPreview:
    prepare_only: bool = True
    audience_name: str = _UNKNOWN
    problem: str = _UNKNOWN
    pains: List[str] = field(default_factory=list)
    desired_outcomes: List[str] = field(default_factory=list)
    objections: List[str] = field(default_factory=list)
    channels: List[str] = field(default_factory=list)
    data_source: str = _UNKNOWN
    no_external_research_performed: bool = True
    confidence: str = _UNKNOWN
    no_personal_data_required: bool = True
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "audience_name", _safe_text(self.audience_name, _UNKNOWN))
        object.__setattr__(self, "problem", _safe_text(self.problem, _UNKNOWN))
        for name in ("pains", "desired_outcomes", "objections", "channels", "warnings"):
            object.__setattr__(self, name, _safe_list(getattr(self, name)))
        object.__setattr__(self, "data_source", "user_provided" if self.data_source == "user_provided" else _UNKNOWN)
        object.__setattr__(self, "confidence", _choice(self.confidence, _CONFIDENCE))
        object.__setattr__(self, "no_external_research_performed", True)
        object.__setattr__(self, "no_personal_data_required", True)
        object.__setattr__(self, "prepare_only", True)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "AudienceSegmentPreview":
        source = dict(data or {})
        return cls(
            audience_name=source.get("audience_name", _UNKNOWN),
            problem=source.get("problem", _UNKNOWN),
            pains=_safe_list(source.get("pains")),
            desired_outcomes=_safe_list(source.get("desired_outcomes")),
            objections=_safe_list(source.get("objections")),
            channels=_safe_list(source.get("channels")),
            data_source="user_provided" if source.get("data_source") == "user_provided" else _UNKNOWN,
            confidence=source.get("confidence", _UNKNOWN),
            warnings=_safe_list(source.get("warnings")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ChannelStrategyPreview:
    prepare_only: bool = True
    channels: List[str] = field(default_factory=list)
    rationale: List[str] = field(default_factory=list)
    content_types: List[str] = field(default_factory=list)
    expected_effort: str = _UNKNOWN
    expected_cost: str = _UNKNOWN
    organic_first: bool = True
    paid_distribution_allowed: bool = False
    external_account_required: bool = False
    approval_required: bool = True

    def __post_init__(self) -> None:
        for name in ("channels", "rationale", "content_types"):
            object.__setattr__(self, name, _safe_list(getattr(self, name)))
        object.__setattr__(self, "expected_effort", _safe_text(self.expected_effort, _UNKNOWN))
        object.__setattr__(self, "expected_cost", _choice(self.expected_cost, _COST))
        object.__setattr__(self, "organic_first", True)
        object.__setattr__(self, "approval_required", True)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ChannelStrategyPreview":
        source = dict(data or {})
        return cls(
            channels=_safe_list(source.get("channels")),
            rationale=_safe_list(source.get("rationale")),
            content_types=_safe_list(source.get("content_types")),
            expected_effort=source.get("expected_effort", _UNKNOWN),
            expected_cost=source.get("expected_cost", _UNKNOWN),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class CampaignPlanPreview:
    prepare_only: bool = True
    campaign_name: str = _UNKNOWN
    objective: str = _UNKNOWN
    audience: str = _UNKNOWN
    channels: List[str] = field(default_factory=list)
    offer: str = _UNKNOWN
    assets_needed: List[str] = field(default_factory=list)
    schedule_preview: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    would_publish: bool = False
    would_send: bool = False
    would_spend: bool = False
    would_call_external_service: bool = False
    approval_required: bool = True
    strong_approval_required: bool = False

    def __post_init__(self) -> None:
        for name in ("campaign_name", "objective", "audience", "offer"):
            object.__setattr__(self, name, _safe_text(getattr(self, name), _UNKNOWN))
        for name in ("channels", "assets_needed", "schedule_preview", "success_metrics"):
            object.__setattr__(self, name, _safe_list(getattr(self, name)))
        object.__setattr__(self, "approval_required", True)
        object.__setattr__(self, "strong_approval_required", bool(self.strong_approval_required))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "CampaignPlanPreview":
        source = dict(data or {})
        return cls(
            campaign_name=source.get("campaign_name", _UNKNOWN),
            objective=source.get("objective", _UNKNOWN),
            audience=source.get("audience", _UNKNOWN),
            channels=_safe_list(source.get("channels")),
            offer=source.get("offer", _UNKNOWN),
            assets_needed=_safe_list(source.get("assets_needed")),
            schedule_preview=_safe_list(source.get("schedule_preview")),
            success_metrics=_safe_list(source.get("success_metrics")),
            strong_approval_required=_risky_distribution_requested(source),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ContentDistributionPackPreview:
    prepare_only: bool = True
    posts: List[str] = field(default_factory=list)
    email_drafts: List[str] = field(default_factory=list)
    community_posts: List[str] = field(default_factory=list)
    outreach_messages: List[str] = field(default_factory=list)
    seo_snippets: List[str] = field(default_factory=list)
    cta_variants: List[str] = field(default_factory=list)
    would_publish: bool = False
    would_send: bool = False
    no_fake_claims: bool = True
    no_fake_social_proof: bool = True
    no_income_guarantees: bool = True
    no_fabricated_metrics: bool = True
    sensitive_input_redacted: bool = False

    def __post_init__(self) -> None:
        values: List[str] = []
        for name in ("posts", "email_drafts", "community_posts", "outreach_messages", "seo_snippets", "cta_variants"):
            safe = _safe_list(getattr(self, name))
            object.__setattr__(self, name, safe)
            values.extend(safe)
        object.__setattr__(self, "sensitive_input_redacted", bool(self.sensitive_input_redacted or _was_redacted(values)))
        for name in ("no_fake_claims", "no_fake_social_proof", "no_income_guarantees", "no_fabricated_metrics"):
            object.__setattr__(self, name, True)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ContentDistributionPackPreview":
        source = dict(data or {})
        names = ("posts", "email_drafts", "community_posts", "outreach_messages", "seo_snippets", "cta_variants")
        values = {name: _safe_list(source.get(name)) for name in names}
        return cls(**values, sensitive_input_redacted=_was_redacted(item for items in values.values() for item in items))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MeasurementPlanPreview:
    prepare_only: bool = True
    utm_plan: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    attribution_assumptions: List[str] = field(default_factory=list)
    dashboard_fields_preview: List[str] = field(default_factory=list)
    no_tracking_installed: bool = True
    no_external_analytics_calls: bool = True
    no_personal_data_collection: bool = True

    def __post_init__(self) -> None:
        for name in ("utm_plan", "metrics", "attribution_assumptions", "dashboard_fields_preview"):
            object.__setattr__(self, name, _safe_list(getattr(self, name)))
        for name in ("no_tracking_installed", "no_external_analytics_calls", "no_personal_data_collection"):
            object.__setattr__(self, name, True)
        object.__setattr__(self, "prepare_only", True)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "MeasurementPlanPreview":
        source = dict(data or {})
        return cls(
            utm_plan=_safe_list(source.get("utm_plan")),
            metrics=_safe_list(source.get("metrics")),
            attribution_assumptions=_safe_list(source.get("attribution_assumptions")),
            dashboard_fields_preview=_safe_list(source.get("dashboard_fields_preview")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class BudgetSpendGuardPreview:
    prepare_only: bool = True
    budget_requested: str = _UNKNOWN
    would_spend: bool = False
    paid_ads_enabled: bool = False
    payment_setup_enabled: bool = False
    spend_limit_required: bool = True
    strong_approval_required: bool = True
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "budget_requested", _safe_text(self.budget_requested, _UNKNOWN))
        object.__setattr__(self, "warnings", _safe_list(self.warnings))
        object.__setattr__(self, "spend_limit_required", True)
        object.__setattr__(self, "strong_approval_required", True)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "BudgetSpendGuardPreview":
        source = dict(data or {})
        return cls(budget_requested=source.get("budget_requested", _UNKNOWN), warnings=_safe_list(source.get("warnings")))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class LaunchChecklistPreview:
    prepare_only: bool = True
    ready_to_launch: bool = False
    required_assets: List[str] = field(default_factory=lambda: list(_DEFAULT_LAUNCH_ASSETS))
    missing_items: List[str] = field(default_factory=lambda: list(_DEFAULT_MISSING))
    legal_review_required: bool = True
    identity_approval_required: bool = False
    external_account_approval_required: bool = False
    paid_budget_approval_required: bool = False
    publish_approval_required: bool = True
    strong_approval_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "required_assets", _safe_list(self.required_assets) or list(_DEFAULT_LAUNCH_ASSETS))
        object.__setattr__(self, "missing_items", _safe_list(self.missing_items) or list(_DEFAULT_MISSING))
        for name in (
            "legal_review_required", "publish_approval_required", "strong_approval_required",
        ):
            object.__setattr__(self, name, True)
        for name in ("identity_approval_required", "external_account_approval_required", "paid_budget_approval_required"):
            object.__setattr__(self, name, bool(getattr(self, name)))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "LaunchChecklistPreview":
        source = dict(data or {})
        return cls(
            required_assets=_safe_list(source.get("required_assets")) or list(_DEFAULT_LAUNCH_ASSETS),
            missing_items=_safe_list(source.get("missing_items")) or list(_DEFAULT_MISSING),
            identity_approval_required=source.get("identity_requested") is True,
            external_account_approval_required=source.get("external_account_requested") is True,
            paid_budget_approval_required=source.get("paid_requested") is True or source.get("budget_requested") not in (None, ""),
        )

    from_dict = from_request

    @classmethod
    def placeholder(cls) -> "LaunchChecklistPreview":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class DistributionApprovalRequirements:
    prepare_only: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False
    approval_gateway_called: bool = False
    approval_created: bool = False
    approval_granted: bool = False
    approval_rejected: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "approval_required", True)
        object.__setattr__(self, "strong_approval_required", bool(self.strong_approval_required))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "DistributionApprovalRequirements":
        return cls(strong_approval_required=_risky_distribution_requested(dict(data or {})))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


_FORCED_FALSE = {
    "marketing_engine_available", "campaign_execution_enabled", "publishing_enabled",
    "external_account_connection_enabled", "paid_ads_enabled", "email_sending_enabled",
    "dm_sending_enabled", "social_posting_enabled", "scraping_enabled", "identity_usage_enabled",
    "budget_spend_enabled", "external_calls_enabled", "secrets_access_enabled", "hermes_called",
    "approval_gateway_called", "execution_enabled", "paid_distribution_allowed",
    "external_account_required", "would_publish", "would_send", "would_spend",
    "would_call_external_service", "payment_setup_enabled", "ready_to_launch",
    "approval_created", "approval_granted", "approval_rejected",
}


def _force_safe(value: Any) -> None:
    object.__setattr__(value, "prepare_only", True)
    for name in _FORCED_FALSE:
        if name in value.__dataclass_fields__:
            object.__setattr__(value, name, False)


def _serialize(value: Any) -> Dict[str, Any]:
    result = {}
    for name in value.__dataclass_fields__:
        item = getattr(value, name)
        result[name] = list(item) if isinstance(item, list) else item
    result["prepare_only"] = True
    for name in _FORCED_FALSE:
        if name in result:
            result[name] = False
    return result


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


def _was_redacted(values: Any) -> bool:
    return any(value == _REDACTED for value in values)


def _risky_distribution_requested(source: Dict[str, Any]) -> bool:
    explicit_risk = any(source.get(name) is True for name in (
        "publish_requested", "send_requested", "paid_requested", "external_account_requested",
        "identity_requested", "secrets_requested", "budget_spend_requested",
    ))
    return explicit_risk or source.get("budget_requested") not in (None, "")
