from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List

from jarvis.approval_audit import redact_sensitive_data


class ConnectorType(str, Enum):
    LOCAL_FILESYSTEM_SCOPED = "local_filesystem_scoped"
    GITHUB = "github"
    WEB_BROWSER = "web_browser"
    EXTERNAL_API = "external_api"
    MOCK_SAFE = "mock_safe"


@dataclass(frozen=True)
class ConnectorDefinition:
    connector_id: str
    connector_type: ConnectorType
    allowed_scopes: List[str] = field(default_factory=list)
    denied_scopes: List[str] = field(default_factory=list)
    requires_credentials: bool = False
    credentials_loaded: bool = False
    network_required: bool = False
    external_call_required: bool = False
    filesystem_scope_required: bool = False
    approval_required: bool = True
    strong_approval_required: bool = False
    read_only_by_default: bool = True
    write_disabled_by_default: bool = True
    enabled: bool = False
    status: str = "registered_disabled"
    blocked_reasons: List[str] = field(default_factory=list)
    prepare_only: bool = True
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "connector_type", ConnectorType(self.connector_type))
        object.__setattr__(self, "allowed_scopes", _clean_list(self.allowed_scopes))
        object.__setattr__(self, "denied_scopes", _clean_list(self.denied_scopes))
        object.__setattr__(self, "blocked_reasons", _clean_list(self.blocked_reasons))
        object.__setattr__(self, "credentials_loaded", False)
        object.__setattr__(self, "read_only_by_default", True)
        object.__setattr__(self, "write_disabled_by_default", True)
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "execution_enabled", False)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["connector_type"] = self.connector_type.value
        return redact_contract_data(data)


def default_connector_definitions() -> List[ConnectorDefinition]:
    return [
        ConnectorDefinition(
            connector_id="local-filesystem-scoped",
            connector_type=ConnectorType.LOCAL_FILESYSTEM_SCOPED,
            filesystem_scope_required=True,
            blocked_reasons=["explicit filesystem scope required", "filesystem writes disabled"],
        ),
        ConnectorDefinition(
            connector_id="github",
            connector_type=ConnectorType.GITHUB,
            requires_credentials=True,
            network_required=True,
            external_call_required=True,
            strong_approval_required=True,
            blocked_reasons=["credentials unavailable", "network disabled", "GitHub actions disabled"],
        ),
        ConnectorDefinition(
            connector_id="web-browser",
            connector_type=ConnectorType.WEB_BROWSER,
            network_required=True,
            external_call_required=True,
            strong_approval_required=True,
            blocked_reasons=["network disabled", "browser actions disabled"],
        ),
        ConnectorDefinition(
            connector_id="external-api",
            connector_type=ConnectorType.EXTERNAL_API,
            requires_credentials=True,
            network_required=True,
            external_call_required=True,
            strong_approval_required=True,
            blocked_reasons=["credentials unavailable", "network disabled", "API calls disabled"],
        ),
        ConnectorDefinition(
            connector_id="mock-safe",
            connector_type=ConnectorType.MOCK_SAFE,
            approval_required=False,
            blocked_reasons=["connector disabled until explicitly enabled for a controlled preview"],
        ),
    ]


def preview_connector(values: Dict[str, Any]) -> ConnectorDefinition:
    source = dict(values or {})
    source["connector_id"] = _clean_text(source.get("connector_id")) or "connector-preview"
    source["connector_type"] = source.get("connector_type") or ConnectorType.MOCK_SAFE
    source["allowed_scopes"] = source.get("allowed_scopes") or []
    source["denied_scopes"] = source.get("denied_scopes") or []
    source["blocked_reasons"] = source.get("blocked_reasons") or ["preview only; connector not registered"]
    source["enabled"] = False
    return ConnectorDefinition(**source)


def redact_contract_data(value: Any) -> Any:
    """Redact free-text values while preserving explicit safety flag names."""
    if isinstance(value, dict):
        return {str(key): redact_contract_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_contract_data(item) for item in value]
    if isinstance(value, tuple):
        return [redact_contract_data(item) for item in value]
    if isinstance(value, str):
        safe, _ = redact_sensitive_data(value)
        return safe
    return value


def _clean_list(values: List[str]) -> List[str]:
    return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())
