from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.approval_hardening import RiskLevel
from jarvis.tool_connectors import (
    ConnectorDefinition,
    ConnectorType,
    default_connector_definitions,
    redact_contract_data,
)


@dataclass(frozen=True)
class ToolDefinition:
    tool_id: str
    name: str
    connector_type: ConnectorType
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    requires_approval: bool = True
    requires_strong_approval: bool = False
    external_call_required: bool = False
    filesystem_access_required: bool = False
    network_access_required: bool = False
    secrets_required: bool = False
    production_capable: bool = False
    write_capable: bool = False
    side_effect_capable: bool = False
    enabled: bool = False
    execution_enabled: bool = False
    prepare_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "connector_type", ConnectorType(self.connector_type))
        object.__setattr__(self, "risk_level", RiskLevel(self.risk_level))
        object.__setattr__(self, "capabilities", _clean_list(self.capabilities))
        object.__setattr__(self, "required_permissions", _clean_list(self.required_permissions))
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "prepare_only", True)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["connector_type"] = self.connector_type.value
        data["risk_level"] = self.risk_level.value
        return redact_contract_data(data)


@dataclass(frozen=True)
class ToolRegistrySnapshot:
    registered_tools: List[Dict[str, Any]] = field(default_factory=list)
    registered_connectors: List[Dict[str, Any]] = field(default_factory=list)
    registry_available: bool = True
    default_deny: bool = True
    execution_enabled: bool = False
    external_calls_enabled: bool = False
    credentials_enabled: bool = False
    filesystem_writes_enabled: bool = False
    production_enabled: bool = False
    prepare_only: bool = True

    def __post_init__(self) -> None:
        for name in (
            "execution_enabled",
            "external_calls_enabled",
            "credentials_enabled",
            "filesystem_writes_enabled",
            "production_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "registry_available", True)
        object.__setattr__(self, "default_deny", True)
        object.__setattr__(self, "prepare_only", True)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ToolRegistry:
    """In-memory contract registry. Registration never grants permission or execution."""

    def __init__(self, *, include_defaults: bool = True) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._connectors: Dict[str, ConnectorDefinition] = {}
        if include_defaults:
            for connector in default_connector_definitions():
                self.register_connector(connector)
            for tool in default_tool_definitions():
                self.register_tool(tool)

    def register_tool(self, tool: ToolDefinition) -> ToolDefinition:
        self._tools[tool.tool_id] = tool
        return tool

    def register_connector(self, connector: ConnectorDefinition) -> ConnectorDefinition:
        self._connectors[connector.connector_id] = connector
        return connector

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return self._tools.get(str(tool_id))

    def get_connector(self, connector_id: str) -> Optional[ConnectorDefinition]:
        return self._connectors.get(str(connector_id))

    def snapshot(self) -> ToolRegistrySnapshot:
        return ToolRegistrySnapshot(
            registered_tools=[item.to_dict() for item in self._tools.values()],
            registered_connectors=[item.to_dict() for item in self._connectors.values()],
        )


def default_tool_definitions() -> List[ToolDefinition]:
    return [
        ToolDefinition(
            tool_id="local-filesystem-preview",
            name="Local scoped filesystem preview",
            connector_type=ConnectorType.LOCAL_FILESYSTEM_SCOPED,
            description="Represents scoped local filesystem intent without reading or writing files.",
            capabilities=["preview_read", "preview_write"],
            required_permissions=["filesystem_scope"],
            filesystem_access_required=True,
            write_capable=True,
            side_effect_capable=True,
        ),
        ToolDefinition(
            tool_id="github-preview",
            name="GitHub connector preview",
            connector_type=ConnectorType.GITHUB,
            required_permissions=["github_scope", "network"],
            risk_level=RiskLevel.HIGH,
            requires_strong_approval=True,
            external_call_required=True,
            network_access_required=True,
            secrets_required=True,
            write_capable=True,
            side_effect_capable=True,
        ),
        ToolDefinition(
            tool_id="web-browser-preview",
            name="Web browser connector preview",
            connector_type=ConnectorType.WEB_BROWSER,
            required_permissions=["network"],
            risk_level=RiskLevel.HIGH,
            requires_strong_approval=True,
            external_call_required=True,
            network_access_required=True,
            side_effect_capable=True,
        ),
        ToolDefinition(
            tool_id="external-api-preview",
            name="External API connector preview",
            connector_type=ConnectorType.EXTERNAL_API,
            required_permissions=["network", "api_scope"],
            risk_level=RiskLevel.HIGH,
            requires_strong_approval=True,
            external_call_required=True,
            network_access_required=True,
            secrets_required=True,
            side_effect_capable=True,
        ),
        ToolDefinition(
            tool_id="mock-safe-preview",
            name="Mock safe preview",
            connector_type=ConnectorType.MOCK_SAFE,
            risk_level=RiskLevel.LOW,
            requires_approval=False,
        ),
    ]


def preview_tool_registration(values: Dict[str, Any]) -> ToolDefinition:
    source = dict(values or {})
    source["tool_id"] = _clean_text(source.get("tool_id")) or "tool-preview"
    source["name"] = _clean_text(source.get("name")) or "Tool registration preview"
    source["connector_type"] = source.get("connector_type") or ConnectorType.MOCK_SAFE
    source["capabilities"] = source.get("capabilities") or []
    source["required_permissions"] = source.get("required_permissions") or []
    source["enabled"] = False
    return ToolDefinition(**source)


def _clean_list(values: List[str]) -> List[str]:
    return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())
