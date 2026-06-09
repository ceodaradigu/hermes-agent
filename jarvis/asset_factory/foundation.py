from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_UNKNOWN = "unknown"
_REDACTED = "[redacted sensitive input]"
_SENSITIVE_MARKERS = (
    ".env",
    "api key",
    "api-key",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client secret",
    "client_secret",
    "credential",
    "credentials",
    "password",
    "private key",
    "private_key",
    "secret",
    "token",
)


@dataclass(frozen=True)
class AssetFactoryStatus:
    prepare_only: bool = True
    asset_factory_available: bool = False
    web_builder_available: bool = False
    publishing_enabled: bool = False
    deployment_enabled: bool = False
    domain_connection_enabled: bool = False
    external_account_connection_enabled: bool = False
    paid_resource_creation_enabled: bool = False
    identity_usage_enabled: bool = False
    build_execution_enabled: bool = False
    external_calls_enabled: bool = False
    secrets_access_enabled: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        _force_false(self)

    @classmethod
    def placeholder(cls) -> "AssetFactoryStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AssetFactoryStatus":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class AssetGenerationPolicy:
    prepare_only: bool = True
    no_publishing_by_default: bool = True
    no_deployment_by_default: bool = True
    no_domain_changes_by_default: bool = True
    no_external_accounts_by_default: bool = True
    no_paid_resources_by_default: bool = True
    no_identity_usage_by_default: bool = True
    no_income_claims_by_default: bool = True
    strong_approval_required_for_publish: bool = True
    strong_approval_required_for_domains: bool = True
    strong_approval_required_for_paid_resources: bool = True
    strong_approval_required_for_identity: bool = True
    review_required_before_publication: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        for name in self.__dataclass_fields__:
            if name != "prepare_only":
                object.__setattr__(self, name, True)

    @classmethod
    def placeholder(cls) -> "AssetGenerationPolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AssetGenerationPolicy":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class WebProjectBrief:
    prepare_only: bool = True
    project_name: str = _UNKNOWN
    audience: str = _UNKNOWN
    problem: str = _UNKNOWN
    promise_or_value_proposition: str = _UNKNOWN
    offer_type: str = _UNKNOWN
    monetization_hypothesis: str = _UNKNOWN
    tone: str = _UNKNOWN
    constraints: List[str] = field(default_factory=list)
    source_inputs_redacted: bool = False
    confirmed_roi: str = _UNKNOWN
    unknown_remains_unknown: bool = True
    would_publish: bool = False
    would_deploy: bool = False
    would_spend: bool = False
    would_use_identity: bool = False

    def __post_init__(self) -> None:
        for name in (
            "project_name", "audience", "problem", "promise_or_value_proposition",
            "offer_type", "monetization_hypothesis", "tone", "confirmed_roi",
        ):
            object.__setattr__(self, name, _safe_text(getattr(self, name), _UNKNOWN))
        object.__setattr__(self, "constraints", _safe_list(self.constraints))
        object.__setattr__(
            self,
            "source_inputs_redacted",
            bool(self.source_inputs_redacted or _was_redacted([self.project_name, self.audience, self.problem, *self.constraints])),
        )
        object.__setattr__(self, "unknown_remains_unknown", True)
        _force_false(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "WebProjectBrief":
        source = dict(data or {})
        values = {name: _safe_text(source.get(name), _UNKNOWN) for name in (
            "project_name", "audience", "problem", "promise_or_value_proposition",
            "offer_type", "monetization_hypothesis", "tone",
        )}
        constraints = _safe_list(source.get("constraints"))
        return cls(
            **values,
            constraints=constraints,
            source_inputs_redacted=_was_redacted([*values.values(), *constraints]),
            confirmed_roi=_safe_text(source.get("confirmed_roi"), _UNKNOWN)
            if source.get("confirmed_roi_explicitly_provided") is True else _UNKNOWN,
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class LandingPagePlan:
    prepare_only: bool = True
    hero: str = _UNKNOWN
    sections: List[str] = field(default_factory=list)
    cta: str = _UNKNOWN
    trust_elements: List[str] = field(default_factory=list)
    faq: List[str] = field(default_factory=list)
    risk_disclaimers: List[str] = field(default_factory=list)
    conversion_goal: str = _UNKNOWN
    no_income_guarantees: bool = True
    no_fake_testimonials: bool = True
    no_fake_metrics: bool = True
    no_fake_legal_claims: bool = True
    would_publish: bool = False
    would_deploy: bool = False

    def __post_init__(self) -> None:
        for name in ("hero", "cta", "conversion_goal"):
            object.__setattr__(self, name, _safe_text(getattr(self, name), _UNKNOWN))
        for name in ("sections", "trust_elements", "faq", "risk_disclaimers"):
            object.__setattr__(self, name, _safe_list(getattr(self, name)))
        for name in ("no_income_guarantees", "no_fake_testimonials", "no_fake_metrics", "no_fake_legal_claims"):
            object.__setattr__(self, name, True)
        _force_false(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "LandingPagePlan":
        source = dict(data or {})
        return cls(
            hero=_safe_text(source.get("hero"), _UNKNOWN),
            sections=_safe_list(source.get("sections")),
            cta=_safe_text(source.get("cta"), _UNKNOWN),
            trust_elements=_safe_list(source.get("trust_elements")),
            faq=_safe_list(source.get("faq")),
            risk_disclaimers=_safe_list(source.get("risk_disclaimers")),
            conversion_goal=_safe_text(source.get("conversion_goal"), _UNKNOWN),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class WebsiteStructurePlan:
    prepare_only: bool = True
    pages: List[str] = field(default_factory=list)
    navigation: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    data_requirements: List[str] = field(default_factory=list)
    static_dynamic_classification: str = _UNKNOWN
    build_required: bool = False
    deployment_required: bool = False
    external_services_required: bool = False

    def __post_init__(self) -> None:
        for name in ("pages", "navigation", "components", "data_requirements"):
            object.__setattr__(self, name, _safe_list(getattr(self, name)))
        object.__setattr__(
            self,
            "static_dynamic_classification",
            _safe_text(self.static_dynamic_classification, _UNKNOWN),
        )
        _force_false(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "WebsiteStructurePlan":
        source = dict(data or {})
        return cls(
            pages=_safe_list(source.get("pages")),
            navigation=_safe_list(source.get("navigation")),
            components=_safe_list(source.get("components")),
            data_requirements=_safe_list(source.get("data_requirements")),
            static_dynamic_classification=_safe_text(source.get("static_dynamic_classification"), _UNKNOWN),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class CopyContentPackPreview:
    prepare_only: bool = True
    headlines: List[str] = field(default_factory=list)
    subheadlines: List[str] = field(default_factory=list)
    cta_copy: List[str] = field(default_factory=list)
    offer_copy: List[str] = field(default_factory=list)
    faq_copy: List[str] = field(default_factory=list)
    disclaimer_copy: List[str] = field(default_factory=list)
    no_fake_claims: bool = True
    no_fake_testimonials: bool = True
    no_fabricated_numbers: bool = True
    no_income_guarantees: bool = True
    sensitive_input_redacted: bool = False

    def __post_init__(self) -> None:
        values = []
        for name in ("headlines", "subheadlines", "cta_copy", "offer_copy", "faq_copy", "disclaimer_copy"):
            safe = _safe_list(getattr(self, name))
            object.__setattr__(self, name, safe)
            values.extend(safe)
        object.__setattr__(self, "sensitive_input_redacted", bool(self.sensitive_input_redacted or _was_redacted(values)))
        for name in ("no_fake_claims", "no_fake_testimonials", "no_fabricated_numbers", "no_income_guarantees"):
            object.__setattr__(self, name, True)
        object.__setattr__(self, "prepare_only", True)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "CopyContentPackPreview":
        source = dict(data or {})
        values = {name: _safe_list(source.get(name)) for name in (
            "headlines", "subheadlines", "cta_copy", "offer_copy", "faq_copy", "disclaimer_copy",
        )}
        return cls(**values, sensitive_input_redacted=_was_redacted(item for items in values.values() for item in items))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class StaticAssetManifestPreview:
    prepare_only: bool = True
    files_to_create: List[str] = field(default_factory=list)
    directories: List[str] = field(default_factory=list)
    would_write_files: bool = False
    would_overwrite_files: bool = False
    filesystem_scope_required: bool = True
    sandbox_execution_required: bool = True
    approval_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "files_to_create", _safe_paths(self.files_to_create))
        object.__setattr__(self, "directories", _safe_paths(self.directories))
        for name in ("filesystem_scope_required", "sandbox_execution_required", "approval_required"):
            object.__setattr__(self, name, True)
        _force_false(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "StaticAssetManifestPreview":
        source = dict(data or {})
        return cls(
            files_to_create=_safe_paths(source.get("files_to_create")),
            directories=_safe_paths(source.get("directories")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class BuildPackagePreview:
    prepare_only: bool = True
    framework: str = _UNKNOWN
    package_type: str = _UNKNOWN
    dependencies_preview: List[str] = field(default_factory=list)
    build_steps_preview: List[str] = field(default_factory=list)
    would_install: bool = False
    would_build: bool = False
    would_run: bool = False
    would_modify_package_files: bool = False
    sandbox_required: bool = True
    tool_adoption_review_required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "framework", _safe_text(self.framework, _UNKNOWN))
        object.__setattr__(self, "package_type", _safe_text(self.package_type, _UNKNOWN))
        object.__setattr__(self, "dependencies_preview", _safe_list(self.dependencies_preview))
        object.__setattr__(self, "build_steps_preview", _safe_list(self.build_steps_preview))
        object.__setattr__(self, "sandbox_required", True)
        object.__setattr__(
            self,
            "tool_adoption_review_required",
            bool(self.tool_adoption_review_required or self.dependencies_preview),
        )
        _force_false(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "BuildPackagePreview":
        source = dict(data or {})
        dependencies = _safe_list(source.get("dependencies_preview"))
        return cls(
            framework=_safe_text(source.get("framework"), _UNKNOWN),
            package_type=_safe_text(source.get("package_type"), _UNKNOWN),
            dependencies_preview=dependencies,
            build_steps_preview=_safe_list(source.get("build_steps_preview")),
            tool_adoption_review_required=bool(dependencies),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PublishingReadinessPreview:
    prepare_only: bool = True
    ready_to_publish: bool = False
    required_checks: List[str] = field(default_factory=list)
    missing_items: List[str] = field(default_factory=list)
    legal_review_required: bool = True
    identity_approval_required: bool = True
    domain_approval_required: bool = True
    paid_resource_approval_required: bool = True
    strong_approval_required: bool = True
    publish_allowed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "required_checks", _safe_list(self.required_checks))
        object.__setattr__(self, "missing_items", _safe_list(self.missing_items))
        for name in (
            "legal_review_required", "identity_approval_required", "domain_approval_required",
            "paid_resource_approval_required", "strong_approval_required",
        ):
            object.__setattr__(self, name, True)
        _force_false(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PublishingReadinessPreview":
        source = dict(data or {})
        return cls(
            required_checks=_safe_list(source.get("required_checks")),
            missing_items=_safe_list(source.get("missing_items")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MonetizationOfferPreview:
    prepare_only: bool = True
    offer_name: str = _UNKNOWN
    audience: str = _UNKNOWN
    pricing_hypothesis: str = _UNKNOWN
    revenue_hypothesis: str = _UNKNOWN
    validation_needed: bool = True
    no_confirmed_revenue: bool = True
    no_income_guarantees: bool = True
    payment_setup_enabled: bool = False
    stripe_or_payment_calls_enabled: bool = False
    approval_required: bool = True

    def __post_init__(self) -> None:
        for name in ("offer_name", "audience", "pricing_hypothesis", "revenue_hypothesis"):
            object.__setattr__(self, name, _safe_text(getattr(self, name), _UNKNOWN))
        object.__setattr__(self, "validation_needed", True)
        object.__setattr__(self, "no_income_guarantees", True)
        object.__setattr__(self, "approval_required", True)
        _force_false(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "MonetizationOfferPreview":
        source = dict(data or {})
        explicitly_confirmed = source.get("confirmed_revenue_explicitly_provided") is True
        return cls(
            offer_name=_safe_text(source.get("offer_name"), _UNKNOWN),
            audience=_safe_text(source.get("audience"), _UNKNOWN),
            pricing_hypothesis=_safe_text(source.get("pricing_hypothesis"), _UNKNOWN),
            revenue_hypothesis=_safe_text(source.get("revenue_hypothesis"), _UNKNOWN),
            no_confirmed_revenue=not explicitly_confirmed,
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


def _serialize(value: Any) -> Dict[str, Any]:
    result = {}
    for name in value.__dataclass_fields__:
        item = getattr(value, name)
        result[name] = list(item) if isinstance(item, list) else item
    result["prepare_only"] = True
    for name in (
        "asset_factory_available", "web_builder_available", "publishing_enabled", "deployment_enabled",
        "domain_connection_enabled", "external_account_connection_enabled", "paid_resource_creation_enabled",
        "identity_usage_enabled", "build_execution_enabled", "external_calls_enabled", "secrets_access_enabled",
        "hermes_called", "approval_gateway_called", "execution_enabled", "would_publish", "would_deploy",
        "would_spend", "would_use_identity", "would_write_files", "would_overwrite_files", "would_install",
        "would_build", "would_run", "would_modify_package_files", "build_required", "deployment_required",
        "external_services_required", "ready_to_publish", "publish_allowed", "payment_setup_enabled",
        "stripe_or_payment_calls_enabled",
    ):
        if name in result:
            result[name] = False
    return result


def _force_false(value: Any) -> None:
    object.__setattr__(value, "prepare_only", True)
    for name in (
        "asset_factory_available", "web_builder_available", "publishing_enabled", "deployment_enabled",
        "domain_connection_enabled", "external_account_connection_enabled", "paid_resource_creation_enabled",
        "identity_usage_enabled", "build_execution_enabled", "external_calls_enabled", "secrets_access_enabled",
        "hermes_called", "approval_gateway_called", "execution_enabled", "would_publish", "would_deploy",
        "would_spend", "would_use_identity", "would_write_files", "would_overwrite_files", "would_install",
        "would_build", "would_run", "would_modify_package_files", "build_required", "deployment_required",
        "external_services_required", "ready_to_publish", "publish_allowed", "payment_setup_enabled",
        "stripe_or_payment_calls_enabled",
    ):
        if name in value.__dataclass_fields__:
            object.__setattr__(value, name, False)


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


def _safe_paths(value: Any) -> List[str]:
    paths = []
    for item in _safe_list(value):
        lowered = item.lower()
        if item == _REDACTED or item.startswith(("/", "~")) or ".." in item or any(marker in lowered for marker in _SENSITIVE_MARKERS):
            paths.append(_REDACTED)
        else:
            paths.append(item[:240])
    return paths


def _was_redacted(values: Any) -> bool:
    return any(item == _REDACTED for item in values)
