from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_UNKNOWN = "unknown"
_REDACTED = "[redacted sensitive input]"
_TARGET_TYPES = {"static_host", "server", "container", "cloud", "unknown"}
_ENVIRONMENTS = {"preview", "staging", "production", "unknown"}
_SENSITIVE_MARKERS = (
    ".env", "api key", "api-key", "api_key", "apikey", "authorization", "bearer",
    "client secret", "client_secret", "credential", "credentials", "password",
    "private key", "private_key", "secret", "token",
)
_DEFAULT_CHECKS = [
    "asset review",
    "legal review",
    "target review",
    "rollback plan",
    "strong approval",
]
_DEFAULT_MISSING = [
    "readiness has not been completed",
    "strong approval has not been granted",
]


@dataclass(frozen=True)
class DeployPublishingStatus:
    prepare_only: bool = True
    deploy_control_available: bool = False
    publishing_enabled: bool = False
    deployment_enabled: bool = False
    production_enabled: bool = False
    domain_management_enabled: bool = False
    external_account_connection_enabled: bool = False
    paid_resource_creation_enabled: bool = False
    identity_usage_enabled: bool = False
    rollback_execution_enabled: bool = False
    build_execution_enabled: bool = False
    external_calls_enabled: bool = False
    secrets_access_enabled: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        _force_safe(self)

    @classmethod
    def placeholder(cls) -> "DeployPublishingStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "DeployPublishingStatus":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class DeployPublishingPolicy:
    prepare_only: bool = True
    no_publish_by_default: bool = True
    no_deploy_by_default: bool = True
    no_production_by_default: bool = True
    no_domain_changes_by_default: bool = True
    no_external_accounts_by_default: bool = True
    no_paid_resources_by_default: bool = True
    no_identity_usage_by_default: bool = True
    no_secret_access_by_default: bool = True
    rollback_plan_required: bool = True
    readiness_check_required: bool = True
    strong_approval_required_for_publish: bool = True
    strong_approval_required_for_production: bool = True
    strong_approval_required_for_domains: bool = True
    strong_approval_required_for_paid_resources: bool = True
    strong_approval_required_for_identity: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        for name in self.__dataclass_fields__:
            if name != "prepare_only":
                object.__setattr__(self, name, True)

    @classmethod
    def placeholder(cls) -> "DeployPublishingPolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "DeployPublishingPolicy":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class DeploymentTargetPreview:
    prepare_only: bool = True
    target_name: str = _UNKNOWN
    target_type: str = _UNKNOWN
    environment: str = _UNKNOWN
    would_connect: bool = False
    would_create_resource: bool = False
    would_deploy: bool = False
    production_target: bool = False
    paid_resource_requested: bool = False
    domain_requested: bool = False
    identity_requested: bool = False
    strong_approval_required: bool = False
    external_calls_enabled: bool = False
    secrets_required: bool = False
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_name", _safe_text(self.target_name, _UNKNOWN))
        object.__setattr__(self, "target_type", _choice(self.target_type, _TARGET_TYPES))
        object.__setattr__(self, "environment", _choice(self.environment, _ENVIRONMENTS))
        production = bool(self.production_target or self.environment == "production")
        object.__setattr__(self, "production_target", production)
        for name in ("paid_resource_requested", "domain_requested", "identity_requested"):
            object.__setattr__(self, name, bool(getattr(self, name)))
        object.__setattr__(
            self,
            "strong_approval_required",
            bool(production or self.paid_resource_requested or self.domain_requested or self.identity_requested),
        )
        warnings = _safe_list(self.warnings)
        if production:
            warnings.append("Production target requested; real deployment remains disabled.")
        object.__setattr__(self, "warnings", _dedupe(warnings))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "DeploymentTargetPreview":
        source = dict(data or {})
        return cls(
            target_name=source.get("target_name", _UNKNOWN),
            target_type=source.get("target_type", _UNKNOWN),
            environment=source.get("environment", _UNKNOWN),
            production_target=source.get("production_target") is True,
            paid_resource_requested=source.get("paid_resource_requested") is True,
            domain_requested=source.get("domain_requested") is True,
            identity_requested=source.get("identity_requested") is True,
            warnings=_safe_list(source.get("warnings")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PublishingPlanPreview:
    prepare_only: bool = True
    asset_reference: str = _UNKNOWN
    publish_destination: str = _UNKNOWN
    would_publish: bool = False
    would_deploy: bool = False
    would_use_domain: bool = False
    would_use_identity: bool = False
    would_spend: bool = False
    would_call_external_service: bool = False
    approval_required: bool = True
    strong_approval_required: bool = True
    blocked: bool = True
    readiness_complete: bool = False
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "asset_reference", _safe_text(self.asset_reference, _UNKNOWN))
        object.__setattr__(self, "publish_destination", _safe_text(self.publish_destination, _UNKNOWN))
        object.__setattr__(self, "approval_required", True)
        object.__setattr__(self, "strong_approval_required", True)
        object.__setattr__(self, "blocked", True)
        object.__setattr__(self, "readiness_complete", False)
        object.__setattr__(self, "warnings", _safe_list(self.warnings))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PublishingPlanPreview":
        source = dict(data or {})
        return cls(
            asset_reference=source.get("asset_reference", _UNKNOWN),
            publish_destination=source.get("publish_destination", _UNKNOWN),
            warnings=_safe_list(source.get("warnings")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class DomainConnectionPreview:
    prepare_only: bool = True
    domain_requested: bool = False
    domain_name: str = _UNKNOWN
    would_connect_domain: bool = False
    would_change_dns: bool = False
    would_verify_domain: bool = False
    domain_ownership_unverified: bool = True
    strong_approval_required: bool = True
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "domain_requested", bool(self.domain_requested))
        object.__setattr__(self, "domain_name", _safe_text(self.domain_name, _UNKNOWN))
        object.__setattr__(self, "domain_ownership_unverified", True)
        object.__setattr__(self, "strong_approval_required", True)
        object.__setattr__(self, "warnings", _safe_list(self.warnings))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "DomainConnectionPreview":
        source = dict(data or {})
        return cls(
            domain_requested=source.get("domain_requested") is True,
            domain_name=source.get("domain_name", _UNKNOWN),
            warnings=_safe_list(source.get("warnings")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ExternalAccountConnectionPreview:
    prepare_only: bool = True
    account_type: str = _UNKNOWN
    would_connect_account: bool = False
    would_request_token: bool = False
    would_store_credentials: bool = False
    secrets_access_enabled: bool = False
    strong_approval_required: bool = True
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "account_type", _safe_text(self.account_type, _UNKNOWN))
        object.__setattr__(self, "strong_approval_required", True)
        object.__setattr__(self, "warnings", _safe_list(self.warnings))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ExternalAccountConnectionPreview":
        source = dict(data or {})
        return cls(account_type=source.get("account_type", _UNKNOWN), warnings=_safe_list(source.get("warnings")))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ProductionReleasePreview:
    prepare_only: bool = True
    production_requested: bool = False
    would_release: bool = False
    production_access_enabled: bool = False
    strong_approval_required: bool = True
    rollback_plan_required: bool = True
    readiness_check_required: bool = True
    blocked: bool = True
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "production_requested", bool(self.production_requested))
        for name in ("strong_approval_required", "rollback_plan_required", "readiness_check_required", "blocked"):
            object.__setattr__(self, name, True)
        object.__setattr__(self, "warnings", _safe_list(self.warnings))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ProductionReleasePreview":
        source = dict(data or {})
        return cls(
            production_requested=source.get("production_requested") is True,
            warnings=_safe_list(source.get("warnings")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PublishingRollbackPreview:
    prepare_only: bool = True
    rollback_required: bool = True
    would_rollback: bool = False
    rollback_execution_enabled: bool = False
    rollback_steps_preview: List[str] = field(default_factory=list)
    irreversible_risks: List[str] = field(default_factory=list)
    audit_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rollback_required", True)
        object.__setattr__(self, "audit_required", True)
        object.__setattr__(self, "rollback_steps_preview", _safe_list(self.rollback_steps_preview))
        object.__setattr__(self, "irreversible_risks", _safe_list(self.irreversible_risks))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PublishingRollbackPreview":
        source = dict(data or {})
        return cls(
            rollback_steps_preview=_safe_list(source.get("rollback_steps_preview")),
            irreversible_risks=_safe_list(source.get("irreversible_risks")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PublishingReadinessChecklist:
    prepare_only: bool = True
    ready_to_publish: bool = False
    required_checks: List[str] = field(default_factory=lambda: list(_DEFAULT_CHECKS))
    missing_items: List[str] = field(default_factory=lambda: list(_DEFAULT_MISSING))
    legal_review_required: bool = True
    identity_approval_required: bool = False
    domain_approval_required: bool = False
    paid_resource_approval_required: bool = False
    production_approval_required: bool = False
    strong_approval_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "required_checks", _safe_list(self.required_checks) or list(_DEFAULT_CHECKS))
        object.__setattr__(self, "missing_items", _safe_list(self.missing_items) or list(_DEFAULT_MISSING))
        object.__setattr__(self, "legal_review_required", True)
        for name in (
            "identity_approval_required", "domain_approval_required",
            "paid_resource_approval_required", "production_approval_required",
        ):
            object.__setattr__(self, name, bool(getattr(self, name)))
        object.__setattr__(self, "strong_approval_required", True)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PublishingReadinessChecklist":
        source = dict(data or {})
        return cls(
            required_checks=_safe_list(source.get("required_checks")) or list(_DEFAULT_CHECKS),
            missing_items=_safe_list(source.get("missing_items")) or list(_DEFAULT_MISSING),
            identity_approval_required=source.get("identity_requested") is True,
            domain_approval_required=source.get("domain_requested") is True,
            paid_resource_approval_required=source.get("paid_resource_requested") is True,
            production_approval_required=source.get("production_requested") is True,
        )

    from_dict = from_request

    @classmethod
    def placeholder(cls) -> "PublishingReadinessChecklist":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PublishingApprovalRequirements:
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
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PublishingApprovalRequirements":
        source = dict(data or {})
        strong = any(source.get(name) is True for name in (
            "publish_requested", "production_requested", "domain_requested",
            "paid_resource_requested", "identity_requested", "secrets_requested",
        ))
        return cls(strong_approval_required=strong)

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


_FORCED_FALSE = {
    "deploy_control_available", "publishing_enabled", "deployment_enabled", "production_enabled",
    "domain_management_enabled", "external_account_connection_enabled", "paid_resource_creation_enabled",
    "identity_usage_enabled", "rollback_execution_enabled", "build_execution_enabled", "external_calls_enabled",
    "secrets_access_enabled", "hermes_called", "approval_gateway_called", "execution_enabled", "would_connect",
    "would_create_resource", "would_deploy", "secrets_required", "would_publish", "would_use_domain",
    "would_use_identity", "would_spend", "would_call_external_service", "readiness_complete",
    "would_connect_domain", "would_change_dns", "would_verify_domain", "would_connect_account",
    "would_request_token", "would_store_credentials", "would_release", "production_access_enabled",
    "would_rollback", "ready_to_publish", "approval_created", "approval_granted", "approval_rejected",
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


def _dedupe(items: List[str]) -> List[str]:
    return list(dict.fromkeys(items))
