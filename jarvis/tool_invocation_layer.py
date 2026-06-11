from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.approval_audit import ApprovalAuditTrail, redact_sensitive_data
from jarvis.approval_hardening import ApprovalKind, ApprovalRecord, RiskLevel, StrongApprovalPolicy
from jarvis.controlled_runtime_bridge import (
    ControlledRuntimeBridge,
    ControlledRuntimeExecutionRequest,
    ControlledRuntimeGateResult,
)
from jarvis.tool_connectors import ConnectorDefinition, redact_contract_data
from jarvis.tool_registry import ToolDefinition, ToolRegistry


@dataclass(frozen=True)
class ToolInvocationPreview:
    invocation_id: str
    tool_id: str
    connector_id: str
    action_type: str
    target: str
    scope: List[str]
    payload_summary: Dict[str, Any] = field(default_factory=dict)
    requested_by: str = "jarvis"
    reason: str = ""
    dry_run_required: bool = True
    sandbox_required: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False
    controlled_runtime_request: Optional[ControlledRuntimeExecutionRequest] = None
    blocked_reasons: List[str] = field(default_factory=list)
    requested_external_call: bool = False
    requested_filesystem_write: bool = False
    requested_credentials: bool = False
    requested_production: bool = False
    requested_side_effects: bool = False
    would_call_external: bool = False
    would_write_files: bool = False
    would_use_credentials: bool = False
    would_execute: bool = False
    execution_enabled: bool = False
    prepare_only: bool = True

    def __post_init__(self) -> None:
        safe_payload, _ = redact_sensitive_data(dict(self.payload_summary or {}))
        object.__setattr__(self, "scope", _clean_list(self.scope))
        object.__setattr__(self, "payload_summary", safe_payload)
        object.__setattr__(self, "reason", _redacted_text(self.reason))
        object.__setattr__(self, "blocked_reasons", _clean_list(self.blocked_reasons))
        for name in (
            "would_call_external",
            "would_write_files",
            "would_use_credentials",
            "would_execute",
            "execution_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "dry_run_required", True)
        object.__setattr__(self, "sandbox_required", True)
        object.__setattr__(self, "prepare_only", True)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.controlled_runtime_request:
            data["controlled_runtime_request"] = self.controlled_runtime_request.to_dict()
        return redact_contract_data(data)


@dataclass(frozen=True)
class ToolPermissionCheckResult:
    allowed: bool = False
    allowed_for_future_invocation: bool = False
    safe_to_invoke: bool = False
    execution_enabled: bool = False
    connector_enabled: bool = False
    tool_registered: bool = False
    connector_registered: bool = False
    permission_gate_allowed: bool = False
    approval_status: str = "missing"
    strong_approval_status: str = "missing"
    runtime_gate_safe_to_execute: bool = False
    context_matches: bool = False
    sandbox_ready: bool = False
    dry_run_passed: bool = False
    risk_level: RiskLevel = RiskLevel.MEDIUM
    missing_permissions: List[str] = field(default_factory=list)
    blocked_reasons: List[str] = field(default_factory=list)
    audit_events: List[Dict[str, Any]] = field(default_factory=list)
    prepare_only: bool = True
    readiness_only: bool = True
    would_execute: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_level", RiskLevel(self.risk_level))
        object.__setattr__(self, "allowed", False)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "would_execute", False)
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "readiness_only", True)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        return redact_contract_data(data)


class ToolInvocationLayer:
    """Prepare-only connector/tool control plane with no execution callback."""

    def __init__(
        self,
        *,
        registry: Optional[ToolRegistry] = None,
        runtime_bridge: Optional[ControlledRuntimeBridge] = None,
        audit_trail: Optional[ApprovalAuditTrail] = None,
    ) -> None:
        self.registry = registry or ToolRegistry()
        self.audit_trail = audit_trail or ApprovalAuditTrail()
        self.runtime_bridge = runtime_bridge or ControlledRuntimeBridge(audit_trail=self.audit_trail)
        self.strong_policy = StrongApprovalPolicy()

    def status(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "current_implementation_remains_control_plane_only": True,
            "restrictions_are_approval_gates": True,
            "default_denied_without_approval": True,
            "safe_to_invoke_potentially_true_after_valid_approval_and_gates": True,
            "permanent_denial_never_safe_to_invoke": True,
            "tool_registry_available": True,
            "connector_contracts_available": True,
            "tool_invocation_preview_available": True,
            "real_connectors_control_plane_available": True,
            "tool_execution_enabled": False,
            "external_calls_enabled": False,
            "credentials_enabled": False,
            "filesystem_writes_enabled": False,
            "github_actions_enabled": False,
            "browser_actions_enabled": False,
            "api_calls_enabled": False,
            "production_enabled": False,
            "controlled_runtime_bridge_required": True,
            "permission_gates_enforced": True,
            "approval_gates_enforced": True,
            "strong_approval_enforced": True,
            "safe_to_invoke_is_readiness_only": True,
            "safe_to_invoke": False,
            "next_recommended_macro_pr": "Post-S Macro 5 - Memory, Personal OS & Scheduler Real",
        }

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            "default_deny": True,
            "read_only_by_default": True,
            "write_disabled_by_default": True,
            "registration_does_not_grant_permission": True,
            "critical_invocation_requires_double_confirmation": True,
            "approval_cannot_override_permanent_denial": True,
            "approval_does_not_invoke": True,
            "runtime_safe_to_execute_does_not_invoke": True,
            "permission_gate_allowed_does_not_invoke": True,
            "preview_does_not_invoke": True,
        }

    def preview_invocation(self, **values: Any) -> ToolInvocationPreview:
        tool = self.registry.get_tool(str(values.get("tool_id") or ""))
        connector = self.registry.get_connector(str(values.get("connector_id") or ""))
        external = bool(values.get("external_call") or (tool and tool.external_call_required))
        network_access = bool(
            values.get("network_access")
            or external
            or (tool and tool.network_access_required)
            or (connector and connector.network_required)
        )
        filesystem_write = bool(values.get("filesystem_write"))
        credentials = bool(values.get("credentials") or (tool and tool.secrets_required) or (connector and connector.requires_credentials))
        production = bool(values.get("production"))
        side_effects = bool(values.get("side_effects") or filesystem_write)
        action_type = _clean_text(values.get("action_type"))
        target = _clean_text(values.get("target"))
        scope = _clean_list(values.get("scope") or [])
        blocked = []
        if not action_type:
            blocked.append("action_type is empty")
        if not target:
            blocked.append("target is empty")
        if not scope:
            blocked.append("scope is empty")
        runtime_request = self.runtime_bridge.prepare_request(
            action_type=action_type,
            target=target,
            scope=scope,
            tool_name=str(values.get("tool_id") or "") or None,
            payload_summary=values.get("payload_summary") or {},
            environment=values.get("environment") or "preview",
            production=production,
            external_call=external,
            secrets=credentials,
            filesystem_write=filesystem_write,
            network_access=network_access,
            side_effects=side_effects,
            persistent_changes=bool(values.get("persistent_changes") or filesystem_write),
            requested_by=values.get("requested_by") or "jarvis",
            reason=values.get("reason") or "",
        )
        return ToolInvocationPreview(
            invocation_id=str(values.get("invocation_id") or uuid4()),
            tool_id=str(values.get("tool_id") or ""),
            connector_id=str(values.get("connector_id") or ""),
            action_type=action_type,
            target=target,
            scope=scope,
            payload_summary=values.get("payload_summary") or {},
            requested_by=values.get("requested_by") or "jarvis",
            reason=values.get("reason") or "",
            approval_required=bool(tool.requires_approval if tool else True),
            strong_approval_required=bool(
                (tool and tool.requires_strong_approval)
                or (connector and connector.strong_approval_required)
                or credentials
                or external
                or production
            ),
            controlled_runtime_request=runtime_request,
            blocked_reasons=blocked,
            requested_external_call=external,
            requested_filesystem_write=filesystem_write,
            requested_credentials=credentials,
            requested_production=production,
            requested_side_effects=side_effects,
        )

    def preview_permission(
        self,
        preview: ToolInvocationPreview,
        *,
        approval: Optional[ApprovalRecord] = None,
        granted_permissions: Optional[List[str]] = None,
        policy_allowed: bool = False,
        sandbox_available: bool = False,
        filesystem_scope_present: bool = False,
        network_allowed: bool = False,
        secrets_authorized: bool = False,
        timeout_present: bool = False,
        rollback_available: bool = False,
        rollback_steps: Optional[List[str]] = None,
    ) -> ToolPermissionCheckResult:
        tool = self.registry.get_tool(preview.tool_id)
        connector = self.registry.get_connector(preview.connector_id)
        granted = set(_clean_list(granted_permissions or []))
        missing_permissions = [item for item in (tool.required_permissions if tool else []) if item not in granted]
        blocked = list(preview.blocked_reasons)
        if not tool:
            blocked.append("tool is not registered")
        elif not tool.enabled:
            blocked.append("tool is disabled")
        if not connector:
            blocked.append("connector is not registered")
        elif not connector.enabled:
            blocked.append("connector is disabled")
        if connector:
            blocked.extend(connector.blocked_reasons)
        if tool and connector and tool.connector_type != connector.connector_type:
            blocked.append("tool and connector types do not match")
        blocked.extend(f"missing permission: {item}" for item in missing_permissions)
        blocked.extend(_connector_scope_reasons(connector, preview.scope))

        runtime_gate = self._runtime_gate(
            preview,
            approval=approval,
            policy_allowed=policy_allowed,
            sandbox_available=sandbox_available,
            filesystem_scope_present=filesystem_scope_present,
            network_allowed=network_allowed,
            secrets_authorized=secrets_authorized,
            timeout_present=timeout_present,
            rollback_available=rollback_available,
            rollback_steps=rollback_steps,
        )
        blocked.extend(runtime_gate.blocked_reasons)
        if preview.strong_approval_required and (
            not approval or approval.approval_kind != ApprovalKind.STRONG or runtime_gate.approval_status != "approved"
        ):
            blocked.append("valid strong approval required")
        if preview.requested_credentials and (
            not approval or approval.approval_kind != ApprovalKind.STRONG or runtime_gate.approval_status != "approved"
        ):
            blocked.append("credentials require valid strong approval")
        if preview.requested_external_call and not network_allowed:
            blocked.append("external call requires explicit network permission")
        if preview.requested_filesystem_write and (not preview.scope or not filesystem_scope_present):
            blocked.append("filesystem write requires explicit scope")
        if preview.requested_production and not runtime_gate.requires_strong_approval:
            blocked.append("production requires strong approval")
        blocked = _deduplicate(blocked)
        ready = bool(tool and connector and tool.enabled and connector.enabled and runtime_gate.safe_to_execute and not blocked)
        return ToolPermissionCheckResult(
            allowed=False,
            allowed_for_future_invocation=ready,
            safe_to_invoke=ready,
            connector_enabled=bool(connector and connector.enabled),
            tool_registered=tool is not None,
            connector_registered=connector is not None,
            permission_gate_allowed=runtime_gate.permission_gate_allowed,
            approval_status=runtime_gate.approval_status,
            strong_approval_status=_strong_approval_status(approval),
            runtime_gate_safe_to_execute=runtime_gate.safe_to_execute,
            context_matches=runtime_gate.context_matches,
            sandbox_ready=runtime_gate.sandbox_ready,
            dry_run_passed=runtime_gate.dry_run_passed,
            risk_level=_max_risk(tool.risk_level if tool else RiskLevel.MEDIUM, runtime_gate.risk_level),
            missing_permissions=missing_permissions,
            blocked_reasons=blocked,
            audit_events=runtime_gate.audit_events,
        )

    def _runtime_gate(self, preview: ToolInvocationPreview, **values: Any) -> ControlledRuntimeGateResult:
        request = preview.controlled_runtime_request
        if request is None:
            return ControlledRuntimeGateResult(blocked_reasons=["controlled runtime request missing"])
        dry_run = self.runtime_bridge.preview_dry_run(request)
        sandbox = self.runtime_bridge.preview_sandbox(
            request,
            sandbox_available=values["sandbox_available"],
            filesystem_scope_present=values["filesystem_scope_present"],
            network_allowed=values["network_allowed"],
            secrets_authorized=values["secrets_authorized"],
            timeout_present=values["timeout_present"],
        )
        rollback = self.runtime_bridge.preview_rollback(
            request,
            rollback_available=values["rollback_available"],
            rollback_steps=values["rollback_steps"] or [],
        )
        return self.runtime_bridge.preview_gate(
            request,
            dry_run=dry_run,
            sandbox=sandbox,
            rollback=rollback,
            approval=values["approval"],
            policy_allowed=values["policy_allowed"],
        )


def _connector_scope_reasons(connector: Optional[ConnectorDefinition], scope: List[str]) -> List[str]:
    if not connector:
        return []
    reasons = []
    if connector.filesystem_scope_required and not scope:
        reasons.append("connector requires filesystem scope")
    if connector.allowed_scopes and not all(
        any(item == allowed or item.startswith(f"{allowed}/") for allowed in connector.allowed_scopes)
        for item in scope
    ):
        reasons.append("scope is outside connector allowed scopes")
    if any(item == denied or item.startswith(f"{denied}/") for item in scope for denied in connector.denied_scopes):
        reasons.append("scope intersects connector denied scopes")
    return reasons


def _strong_approval_status(approval: Optional[ApprovalRecord]) -> str:
    if approval is None:
        return "missing"
    if approval.approval_kind != ApprovalKind.STRONG:
        return "not_strong"
    return approval.status.value


def _max_risk(first: RiskLevel, second: RiskLevel) -> RiskLevel:
    order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    return max((RiskLevel(first), RiskLevel(second)), key=order.index)


def _redacted_text(value: Any) -> str:
    safe, _ = redact_sensitive_data(str(value or ""))
    return _clean_text(safe)


def _clean_list(values: List[str]) -> List[str]:
    return [_clean_text(value) for value in values if _clean_text(value)]


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _deduplicate(values: List[str]) -> List[str]:
    return list(dict.fromkeys(value for value in values if value))
