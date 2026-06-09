from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit, urlunsplit


_UNKNOWN = "unknown"
_SENSITIVE_MARKERS = (".env", "api_key", "apikey", "authorization", "credential", "password", "secret", "token")
_NATIVE_MARKERS = ("native", "node-gyp", "rust", "cargo", "cffi")
_BINARY_MARKERS = ("binary", "prebuilt", "wheel", ".exe", ".dll", ".so")
_POSTINSTALL_MARKERS = ("postinstall", "preinstall", "install-script", "setup.py")
_NETWORK_MARKERS = ("network", "download", "fetch", "curl", "wget", "http://", "https://")
_COMMERCIAL_LICENSE_MARKERS = ("commercial", "proprietary", "paid", "enterprise")
_UNCLEAR_LICENSE_MARKERS = ("unclear", "custom", "unknown", "missing", "unlicensed")


class ToolAdoptionDecision(str, Enum):
    REJECT = "reject"
    NEEDS_MORE_INFO = "needs_more_info"
    SANDBOX_SPIKE_PROPOSED = "sandbox_spike_proposed"
    ADOPTION_BLOCKED = "adoption_blocked"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ToolAdoptionStatus:
    prepare_only: bool = True
    tool_adoption_available: bool = False
    external_discovery_enabled: bool = False
    repo_clone_enabled: bool = False
    install_enabled: bool = False
    sandbox_install_enabled: bool = False
    external_execution_enabled: bool = False
    core_dependency_adoption_enabled: bool = False
    network_access_enabled: bool = False
    secrets_access_enabled: bool = False
    approval_gateway_called: bool = False
    hermes_called: bool = False
    execution_enabled: bool = False

    @classmethod
    def placeholder(cls) -> "ToolAdoptionStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ToolAdoptionStatus":
        return cls()

    def to_dict(self) -> Dict[str, bool]:
        return {
            "prepare_only": True,
            "tool_adoption_available": False,
            "external_discovery_enabled": False,
            "repo_clone_enabled": False,
            "install_enabled": False,
            "sandbox_install_enabled": False,
            "external_execution_enabled": False,
            "core_dependency_adoption_enabled": False,
            "network_access_enabled": False,
            "secrets_access_enabled": False,
            "approval_gateway_called": False,
            "hermes_called": False,
            "execution_enabled": False,
        }


@dataclass(frozen=True)
class ToolCandidateProfile:
    prepare_only: bool = True
    tool_name: str = "unknown"
    source_url: str = ""
    declared_use_case: str = "unknown"
    license: str = _UNKNOWN
    repo_health: str = _UNKNOWN
    dependency_risk: str = _UNKNOWN
    security_risk: str = _UNKNOWN
    expected_value: str = _UNKNOWN
    adoption_blocked: bool = True
    would_clone: bool = False
    would_install: bool = False
    would_execute: bool = False
    would_become_core_dependency: bool = False
    requires_approval: bool = True
    requires_strong_approval: bool = False
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ToolCandidateProfile":
        source = dict(data or {})
        license_value = _safe_label(source.get("license"))
        risks = [_safe_label(source.get(key)) for key in ("dependency_risk", "security_risk")]
        strong = any(value in {"high", "critical", "blocked"} for value in risks)
        warnings = []
        if license_value == _UNKNOWN:
            warnings.append("License is unknown; adoption remains blocked pending review.")
        if strong:
            warnings.append("High or blocked risk requires strong approval before any future action.")
        return cls(
            tool_name=_safe_text(source.get("tool_name"), "unknown"),
            source_url=_safe_url(source.get("source_url")),
            declared_use_case=_safe_text(source.get("declared_use_case"), "unknown"),
            license=license_value,
            repo_health=_safe_label(source.get("repo_health")),
            dependency_risk=_safe_label(source.get("dependency_risk")),
            security_risk=_safe_label(source.get("security_risk")),
            expected_value=_safe_label(source.get("expected_value")),
            requires_strong_approval=strong,
            warnings=warnings,
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ToolLicenseReview:
    prepare_only: bool = True
    declared_license: str = _UNKNOWN
    review_status: str = "needs_more_info"
    external_lookup_performed: bool = False
    legal_conclusion: str = "not_provided"
    adoption_blocked: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False
    core_adoption_requires_strong_approval: bool = True
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ToolLicenseReview":
        license_value = _safe_label((data or {}).get("license"))
        unclear = license_value == _UNKNOWN or _contains_any(license_value, _UNCLEAR_LICENSE_MARKERS)
        commercial = _contains_any(license_value, _COMMERCIAL_LICENSE_MARKERS)
        status = "needs_more_info" if unclear else "approval_required" if commercial else "review_required"
        warnings = ["No external lookup or legal conclusion was performed."]
        if unclear:
            warnings.append("Missing or unclear license blocks adoption.")
        if commercial:
            warnings.append("Commercial or proprietary license requires approval.")
        return cls(
            declared_license=license_value,
            review_status=status,
            adoption_blocked=unclear,
            strong_approval_required=commercial,
            warnings=warnings,
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ToolRepoHealthReview:
    prepare_only: bool = True
    repo_health: str = _UNKNOWN
    metadata_provided: bool = False
    stars: Optional[int] = None
    forks: Optional[int] = None
    open_issues: Optional[int] = None
    last_activity: Optional[str] = None
    external_lookup_performed: bool = False
    network_called: bool = False
    approval_required: bool = True
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ToolRepoHealthReview":
        metadata = dict((data or {}).get("metadata") or {})
        provided = bool(metadata)
        health = _safe_label(metadata.get("repo_health")) if provided else _UNKNOWN
        return cls(
            repo_health=health,
            metadata_provided=provided,
            stars=_safe_non_negative_int(metadata.get("stars")),
            forks=_safe_non_negative_int(metadata.get("forks")),
            open_issues=_safe_non_negative_int(metadata.get("open_issues")),
            last_activity=_safe_optional_text(metadata.get("last_activity")),
            warnings=[] if provided else ["Repository metadata was not provided; health remains unknown."],
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ToolDependencyRiskReview:
    prepare_only: bool = True
    dependencies: List[str] = field(default_factory=list)
    dependency_risk: str = _UNKNOWN
    native_dependency_detected: bool = False
    binary_dependency_detected: bool = False
    postinstall_dependency_detected: bool = False
    network_dependency_detected: bool = False
    unknown_dependency_detected: bool = True
    risky_dependencies: List[str] = field(default_factory=list)
    unknown_dependencies: List[str] = field(default_factory=list)
    install_performed: bool = False
    package_manager_called: bool = False
    install_proposal_blocked: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ToolDependencyRiskReview":
        dependencies = [_safe_text(item) for item in ((data or {}).get("dependencies") or []) if _safe_text(item)]
        native = _items_with_markers(dependencies, _NATIVE_MARKERS)
        binary = _items_with_markers(dependencies, _BINARY_MARKERS)
        postinstall = _items_with_markers(dependencies, _POSTINSTALL_MARKERS)
        network = _items_with_markers(dependencies, _NETWORK_MARKERS)
        risky = _unique(native + binary + postinstall + network)
        unknown_dependencies = [item for item in dependencies if item not in risky]
        high = bool(risky)
        unknown = not dependencies or bool(unknown_dependencies)
        risk = "high" if high else "unknown"
        return cls(
            dependencies=dependencies,
            dependency_risk=risk,
            native_dependency_detected=bool(native),
            binary_dependency_detected=bool(binary),
            postinstall_dependency_detected=bool(postinstall),
            network_dependency_detected=bool(network),
            unknown_dependency_detected=unknown,
            risky_dependencies=risky,
            unknown_dependencies=unknown_dependencies,
            install_proposal_blocked=True,
            strong_approval_required=high,
            warnings=(
                ["Risky dependency characteristics block install proposal and require strong approval."]
                if high
                else ["Dependencies were not provided; risk remains unknown."]
                if unknown
                else []
            ),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ToolSandboxInstallProposal:
    prepare_only: bool = True
    tool_name: str = "unknown"
    would_install: bool = False
    install_enabled: bool = False
    sandbox_required: bool = True
    filesystem_scope_required: bool = True
    network_blocked_by_default: bool = True
    secrets_blocked: bool = True
    approval_required: bool = True
    strong_approval_required: bool = True
    rollback_required: bool = True
    blocked: bool = True
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ToolSandboxInstallProposal":
        return cls(
            tool_name=_safe_text((data or {}).get("tool_name"), "unknown"),
            warnings=["Proposal only: no package, tool, or dependency was installed."],
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ToolSpikePlan:
    prepare_only: bool = True
    hypothesis: str = "unknown"
    scope: str = "unknown"
    success_metric: str = "unknown"
    max_time: str = "unknown"
    max_cost: str = "unknown"
    rollback: str = "required before any real spike"
    would_execute: bool = False
    execution_enabled: bool = False
    approval_required_before_install_or_run: bool = True
    strong_approval_required: bool = True
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ToolSpikePlan":
        source = dict(data or {})
        return cls(
            hypothesis=_safe_text(source.get("hypothesis"), "unknown"),
            scope=_safe_text(source.get("scope"), "unknown"),
            success_metric=_safe_text(source.get("success_metric"), "unknown"),
            max_time=_safe_text(source.get("max_time"), "unknown"),
            max_cost=_safe_text(source.get("max_cost"), "unknown"),
            rollback=_safe_text(source.get("rollback"), "required before any real spike"),
            warnings=["Plan only: no spike, install, or external code execution occurred."],
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ToolValueMeasurementPreview:
    prepare_only: bool = True
    time_saved: str = _UNKNOWN
    token_saved: str = _UNKNOWN
    error_reduction: str = _UNKNOWN
    asset_quality_improvement: str = _UNKNOWN
    revenue_enablement: str = _UNKNOWN
    roi: str = _UNKNOWN
    confirmed_revenue: bool = False
    approval_required: bool = True
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ToolValueMeasurementPreview":
        source = dict(data or {})
        return cls(
            time_saved=_safe_metric(source.get("time_saved")),
            token_saved=_safe_metric(source.get("token_saved")),
            error_reduction=_safe_metric(source.get("error_reduction")),
            asset_quality_improvement=_safe_metric(source.get("asset_quality_improvement")),
            revenue_enablement=_safe_metric(source.get("revenue_enablement")),
            confirmed_revenue=bool(source.get("confirmed_revenue") is True),
            warnings=["ROI remains unknown; this preview does not infer financial return."],
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ToolAdoptionDecisionPreview:
    prepare_only: bool = True
    decision: ToolAdoptionDecision = ToolAdoptionDecision.UNKNOWN
    keep_decision: bool = False
    rollback_decision: str = "required"
    rollback_plan_required: bool = True
    core_dependency_allowed: bool = False
    approval_required: bool = True
    strong_approval_required: bool = False
    would_install: bool = False
    would_execute: bool = False
    would_access_network: bool = False
    would_access_secrets: bool = False
    would_become_core_dependency: bool = False
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ToolAdoptionDecisionPreview":
        source = dict(data or {})
        requested_risk = any(
            bool(source.get(key))
            for key in ("install_requested", "execution_requested", "network_requested", "secrets_requested", "core_dependency_requested")
        )
        blocked = bool(source.get("blocked")) or _safe_label(source.get("license")) == _UNKNOWN
        needs_info = any(
            _safe_label(source.get(key)) == _UNKNOWN
            for key in ("license", "repo_health", "dependency_risk", "expected_value")
        )
        decision = (
            ToolAdoptionDecision.ADOPTION_BLOCKED
            if requested_risk or blocked
            else ToolAdoptionDecision.NEEDS_MORE_INFO
            if needs_info
            else ToolAdoptionDecision.SANDBOX_SPIKE_PROPOSED
        )
        return cls(
            decision=decision,
            strong_approval_required=requested_risk,
            warnings=["Preview only: keep is false and core dependency adoption remains blocked."],
        )

    from_dict = from_request

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision", ToolAdoptionDecision(self.decision))

    def to_dict(self) -> Dict[str, Any]:
        data = _serialize(self)
        data["decision"] = self.decision.value
        return data


def _serialize(value: Any) -> Dict[str, Any]:
    result = {}
    for name in value.__dataclass_fields__:
        item = getattr(value, name)
        if isinstance(item, Enum):
            item = item.value
        elif isinstance(item, list):
            item = list(item)
        result[name] = item
    result["prepare_only"] = True
    for name in (
        "tool_adoption_available",
        "external_discovery_enabled",
        "repo_clone_enabled",
        "install_enabled",
        "sandbox_install_enabled",
        "external_execution_enabled",
        "core_dependency_adoption_enabled",
        "network_access_enabled",
        "secrets_access_enabled",
        "approval_gateway_called",
        "hermes_called",
        "execution_enabled",
        "external_lookup_performed",
        "network_called",
        "install_performed",
        "package_manager_called",
        "would_clone",
        "would_install",
        "would_execute",
        "would_access_network",
        "would_access_secrets",
        "would_become_core_dependency",
        "core_dependency_allowed",
        "keep_decision",
    ):
        if name in result:
            result[name] = False
    for name in (
        "requires_approval",
        "approval_required",
        "rollback_plan_required",
        "core_adoption_requires_strong_approval",
        "sandbox_required",
        "filesystem_scope_required",
        "network_blocked_by_default",
        "secrets_blocked",
        "rollback_required",
        "approval_required_before_install_or_run",
    ):
        if name in result:
            result[name] = True
    return result


def _safe_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    if not text:
        return default
    if _contains_any(text.lower(), _SENSITIVE_MARKERS):
        return "[redacted sensitive input]"
    return text[:300]


def _safe_optional_text(value: Any) -> Optional[str]:
    text = _safe_text(value)
    return text or None


def _safe_label(value: Any) -> str:
    text = _safe_text(value, _UNKNOWN).lower()
    return re.sub(r"[^a-z0-9_.+-]+", "_", text)[:80] or _UNKNOWN


def _safe_metric(value: Any) -> str:
    return _safe_text(value, _UNKNOWN)


def _safe_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text or _contains_any(text.lower(), _SENSITIVE_MARKERS):
        return ""
    try:
        parts = urlsplit(text)
        port = f":{parts.port}" if parts.port else ""
    except ValueError:
        return ""
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return ""
    host = parts.hostname
    path = parts.path[:200]
    return urlunsplit((parts.scheme, f"{host}{port}", path, "", ""))


def _safe_non_negative_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in markers)


def _items_with_markers(items: List[str], markers: tuple[str, ...]) -> List[str]:
    return [item for item in items if _contains_any(item, markers)]


def _unique(items: List[str]) -> List[str]:
    return list(dict.fromkeys(items))
