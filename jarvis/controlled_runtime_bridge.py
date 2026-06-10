from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.approval_audit import ApprovalAuditTrail, redact_sensitive_data
from jarvis.approval_hardening import (
    ApprovalRecord,
    RiskLevel,
    StrongApprovalPolicy,
    build_context_fingerprint,
)
from jarvis.permission_gates import PermissionGateResult, evaluate_permission_gate


@dataclass(frozen=True)
class ControlledRuntimeExecutionRequest:
    request_id: str
    action_type: str
    target: str
    scope: List[str]
    command: Optional[str] = None
    tool_name: Optional[str] = None
    payload_summary: Dict[str, Any] = field(default_factory=dict)
    environment: str = "preview"
    production: bool = False
    external_call: bool = False
    secrets: bool = False
    filesystem_write: bool = False
    network_access: bool = False
    side_effects: bool = False
    persistent_changes: bool = False
    requested_by: str = "jarvis"
    reason: str = ""
    created_at: str = ""
    context_fingerprint: str = ""
    prepare_only: bool = True
    execution_enabled: bool = False
    side_effects_enabled: bool = False

    def __post_init__(self) -> None:
        safe_payload, _ = redact_sensitive_data(dict(self.payload_summary or {}))
        object.__setattr__(self, "scope", [_clean_text(item) for item in self.scope if _clean_text(item)])
        object.__setattr__(self, "payload_summary", safe_payload)
        object.__setattr__(self, "command", _optional_text(self.command))
        object.__setattr__(self, "tool_name", _optional_text(self.tool_name))
        object.__setattr__(self, "reason", _redacted_text(self.reason))
        object.__setattr__(self, "created_at", self.created_at or _now_iso())
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "side_effects_enabled", False)
        object.__setattr__(self, "context_fingerprint", build_context_fingerprint(self.context()))

    def context(self) -> Dict[str, Any]:
        fingerprint_payload = {
            "payload_summary": self.payload_summary,
            "scope": list(self.scope),
        }
        for key, value in (
            ("filesystem_write", self.filesystem_write),
            ("network_access", self.network_access),
            ("side_effects", self.side_effects),
            ("persistent_changes", self.persistent_changes),
        ):
            if value:
                fingerprint_payload[key] = True
        context = {
            "action_type": self.action_type,
            "target": self.target,
            "environment": self.environment,
            "user_payload": fingerprint_payload,
        }
        for key, value in (
            ("command", self.command),
            ("tool_name", self.tool_name),
            ("production", self.production),
            ("external_call", self.external_call),
            ("secret_access", self.secrets),
            ("filesystem_write", self.filesystem_write),
            ("network", self.network_access),
            ("side_effects", self.side_effects),
            ("persistent_changes", self.persistent_changes),
        ):
            if value:
                context[key] = value
        return context

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["action_type"] = _redacted_text(self.action_type)
        data["target"] = _redacted_text(self.target)
        data["scope"] = [_redacted_text(item) for item in self.scope]
        data["command"] = _redacted_text(self.command) if self.command else None
        data["tool_name"] = _redacted_text(self.tool_name) if self.tool_name else None
        return data


@dataclass(frozen=True)
class DryRunResult:
    dry_run_performed: bool = False
    would_execute: bool = False
    command_preview: str = "[no command preview]"
    expected_side_effects: List[str] = field(default_factory=list)
    blocked_reasons: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    passed: bool = False
    notes: List[str] = field(default_factory=list)
    prepare_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "would_execute", False)
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "risk_level", RiskLevel(self.risk_level))
        object.__setattr__(self, "expected_side_effects", list(self.expected_side_effects))
        object.__setattr__(self, "blocked_reasons", list(self.blocked_reasons))
        object.__setattr__(self, "notes", list(self.notes))

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        return data


@dataclass(frozen=True)
class SandboxRequirements:
    sandbox_required: bool = True
    sandbox_available: bool = False
    filesystem_scope_required: bool = False
    filesystem_scope_present: bool = False
    network_disabled_by_default: bool = True
    network_allowed: bool = False
    secrets_blocked: bool = True
    timeout_required: bool = True
    timeout_present: bool = False
    rollback_required: bool = False
    missing_requirements: List[str] = field(default_factory=list)
    prepare_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "network_disabled_by_default", True)
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "missing_requirements", list(self.missing_requirements))

    @property
    def ready(self) -> bool:
        return bool(
            not self.missing_requirements
            and (not self.sandbox_required or self.sandbox_available)
            and (not self.filesystem_scope_required or self.filesystem_scope_present)
            and (not self.timeout_required or self.timeout_present)
            and not self.secrets_blocked
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["ready"] = self.ready
        return data


@dataclass(frozen=True)
class RollbackPlan:
    rollback_required: bool = False
    rollback_available: bool = False
    rollback_steps: List[str] = field(default_factory=list)
    rollback_notes: str = ""
    blocked_if_missing: bool = True
    prepare_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rollback_steps", [_redacted_text(item) for item in self.rollback_steps if _clean_text(item)])
        object.__setattr__(self, "rollback_notes", _redacted_text(self.rollback_notes))
        object.__setattr__(self, "prepare_only", True)

    @property
    def ready(self) -> bool:
        return not self.rollback_required or (self.rollback_available and bool(self.rollback_steps))

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["ready"] = self.ready
        return data


@dataclass(frozen=True)
class ControlledRuntimeGateResult:
    allowed_for_future_execution: bool = False
    safe_to_execute: bool = False
    requires_approval: bool = True
    requires_strong_approval: bool = False
    policy_allowed: bool = False
    permission_gate_allowed: bool = False
    approval_status: str = "missing"
    context_matches: bool = False
    sandbox_ready: bool = False
    dry_run_passed: bool = False
    rollback_ready: bool = False
    risk_level: RiskLevel = RiskLevel.MEDIUM
    blocked_reasons: List[str] = field(default_factory=list)
    audit_events: List[Dict[str, Any]] = field(default_factory=list)
    execution_enabled: bool = False
    side_effects_enabled: bool = False
    prepare_only: bool = True
    readiness_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_level", RiskLevel(self.risk_level))
        object.__setattr__(self, "blocked_reasons", list(self.blocked_reasons))
        object.__setattr__(self, "audit_events", list(self.audit_events))
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "side_effects_enabled", False)
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "readiness_only", True)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        return data


class ControlledRuntimeBridge:
    """Pure control-plane previews for a future runtime execution layer."""

    def __init__(
        self,
        *,
        strong_policy: Optional[StrongApprovalPolicy] = None,
        audit_trail: Optional[ApprovalAuditTrail] = None,
    ) -> None:
        self.strong_policy = strong_policy or StrongApprovalPolicy()
        self.audit_trail = audit_trail or ApprovalAuditTrail()

    def status(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "controlled_runtime_bridge_available": True,
            "runtime_execution_enabled": False,
            "side_effects_enabled": False,
            "dry_run_required": True,
            "sandbox_required": True,
            "rollback_required_for_side_effects": True,
            "permission_gates_enforced": True,
            "approval_gates_enforced": True,
            "strong_approval_enforced": True,
            "safe_to_execute_is_readiness_only": True,
            "safe_to_execute": False,
            "allowed_for_future_execution": False,
            "next_recommended_macro_pr": "Post-S Macro 4 - Real Connectors & Tool Execution Layer",
        }

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            "network_disabled_by_default": True,
            "secrets_blocked_by_default": True,
            "open_scope_blocked": True,
            "ambiguous_command_blocked": True,
            "production_requires_strong_approval": True,
            "approval_does_not_execute": True,
            "permission_gate_does_not_execute": True,
            "strong_approval_policy": self.strong_policy.to_dict(),
        }

    def prepare_request(self, **values: Any) -> ControlledRuntimeExecutionRequest:
        values = dict(values)
        values["request_id"] = values.get("request_id") or str(uuid4())
        values["scope"] = values.get("scope") or []
        values["payload_summary"] = values.get("payload_summary") or {}
        return ControlledRuntimeExecutionRequest(**values)

    def preview_dry_run(self, request: ControlledRuntimeExecutionRequest) -> DryRunResult:
        risk, _, _ = self.strong_policy.classify(request.context())
        blocked = _request_blocked_reasons(request)
        expected = _expected_side_effects(request)
        return DryRunResult(
            dry_run_performed=True,
            command_preview=_command_preview(request),
            expected_side_effects=expected,
            blocked_reasons=blocked,
            risk_level=risk,
            passed=not blocked,
            notes=["Simulation only; no command, tool, network, filesystem, mission, or task action was performed."],
        )

    def preview_sandbox(
        self,
        request: ControlledRuntimeExecutionRequest,
        *,
        sandbox_available: bool = False,
        filesystem_scope_present: bool = False,
        network_allowed: bool = False,
        secrets_authorized: bool = False,
        timeout_present: bool = False,
    ) -> SandboxRequirements:
        sandbox_required = _risky(request)
        filesystem_required = request.filesystem_write
        rollback_required = _rollback_required(request)
        missing = []
        if sandbox_required and not sandbox_available:
            missing.append("sandbox unavailable")
        if filesystem_required and not filesystem_scope_present:
            missing.append("filesystem scope missing")
        if (request.network_access or request.external_call) and not network_allowed:
            missing.append("network permission missing")
        if request.secrets and not secrets_authorized:
            missing.append("secrets are blocked")
        if sandbox_required and not timeout_present:
            missing.append("timeout missing")
        return SandboxRequirements(
            sandbox_required=sandbox_required,
            sandbox_available=sandbox_available,
            filesystem_scope_required=filesystem_required,
            filesystem_scope_present=filesystem_scope_present,
            network_allowed=network_allowed,
            secrets_blocked=request.secrets and not secrets_authorized,
            timeout_required=sandbox_required,
            timeout_present=timeout_present,
            rollback_required=rollback_required,
            missing_requirements=missing,
        )

    def preview_rollback(
        self,
        request: ControlledRuntimeExecutionRequest,
        *,
        rollback_available: bool = False,
        rollback_steps: Optional[List[str]] = None,
        rollback_notes: str = "",
    ) -> RollbackPlan:
        return RollbackPlan(
            rollback_required=_rollback_required(request),
            rollback_available=rollback_available,
            rollback_steps=rollback_steps or [],
            rollback_notes=rollback_notes,
        )

    def preview_gate(
        self,
        request: ControlledRuntimeExecutionRequest,
        *,
        dry_run: Optional[DryRunResult] = None,
        sandbox: Optional[SandboxRequirements] = None,
        rollback: Optional[RollbackPlan] = None,
        approval: Optional[ApprovalRecord] = None,
        policy_allowed: bool = False,
    ) -> ControlledRuntimeGateResult:
        dry_run = dry_run or DryRunResult()
        sandbox = sandbox or SandboxRequirements()
        rollback = rollback or RollbackPlan(rollback_required=_rollback_required(request))
        permission = evaluate_permission_gate(
            request.context(),
            approval,
            policy=self.strong_policy,
            audit_trail=self.audit_trail,
        )
        blocked = _request_blocked_reasons(request)
        if not policy_allowed:
            blocked.append("policy denied or not explicitly allowed")
        blocked.extend(_permission_blocked_reasons(permission))
        if not dry_run.dry_run_performed or not dry_run.passed:
            blocked.append("dry-run missing or failed")
        sandbox_blocked = _sandbox_blocked_reasons(request, sandbox)
        rollback_ready = not _rollback_required(request) or bool(rollback.rollback_available and rollback.rollback_steps)
        blocked.extend(sandbox_blocked)
        if not rollback_ready:
            blocked.append("required rollback plan missing")
        blocked = _deduplicate(blocked)
        ready = not blocked
        events = [event.to_dict() for event in self.audit_trail.list_events(approval.approval_id if approval else "missing")]
        return ControlledRuntimeGateResult(
            allowed_for_future_execution=ready,
            safe_to_execute=ready,
            requires_approval=permission.requires_approval,
            requires_strong_approval=permission.requires_strong_approval,
            policy_allowed=policy_allowed,
            permission_gate_allowed=permission.allowed,
            approval_status=permission.approval_status,
            context_matches=permission.context_matches,
            sandbox_ready=not sandbox_blocked,
            dry_run_passed=dry_run.dry_run_performed and dry_run.passed,
            rollback_ready=rollback_ready,
            risk_level=permission.risk_level,
            blocked_reasons=blocked,
            audit_events=events,
        )


def _request_blocked_reasons(request: ControlledRuntimeExecutionRequest) -> List[str]:
    blocked = []
    if not _clean_text(request.action_type):
        blocked.append("action_type is empty")
    if not _clean_text(request.target):
        blocked.append("target is empty")
    if not request.scope or any(_is_open_scope(item) for item in request.scope):
        blocked.append("scope is empty or open")
    if not request.command and not request.tool_name:
        blocked.append("command or tool_name is required")
    if request.command and _is_ambiguous_command(request.command):
        blocked.append("command is ambiguous")
    return blocked


def _permission_blocked_reasons(permission: PermissionGateResult) -> List[str]:
    return [] if permission.allowed else [f"permission gate: {item}" for item in permission.missing_requirements]


def _sandbox_blocked_reasons(
    request: ControlledRuntimeExecutionRequest,
    sandbox: SandboxRequirements,
) -> List[str]:
    blocked = list(sandbox.missing_requirements)
    if _risky(request) and not sandbox.sandbox_available:
        blocked.append("sandbox unavailable")
    if request.filesystem_write and not sandbox.filesystem_scope_present:
        blocked.append("filesystem scope missing")
    if (request.network_access or request.external_call) and not sandbox.network_allowed:
        blocked.append("network permission missing")
    if request.secrets and sandbox.secrets_blocked:
        blocked.append("secrets are blocked")
    if _risky(request) and not sandbox.timeout_present:
        blocked.append("timeout missing")
    return _deduplicate(blocked)


def _command_preview(request: ControlledRuntimeExecutionRequest) -> str:
    if request.command:
        return _redacted_text(request.command)
    if request.tool_name:
        return f"tool:{_redacted_text(request.tool_name)}"
    return "[no command preview]"


def _expected_side_effects(request: ControlledRuntimeExecutionRequest) -> List[str]:
    effects = []
    for enabled, label in (
        (request.filesystem_write, "filesystem write"),
        (request.network_access, "network access"),
        (request.external_call, "external call"),
        (request.production, "production change"),
        (request.persistent_changes, "persistent change"),
        (request.side_effects, "declared side effects"),
    ):
        if enabled:
            effects.append(label)
    return effects


def _risky(request: ControlledRuntimeExecutionRequest) -> bool:
    return bool(request.command or request.tool_name or _expected_side_effects(request) or request.secrets)


def _rollback_required(request: ControlledRuntimeExecutionRequest) -> bool:
    action = _clean_text(request.action_type).lower()
    return bool(
        request.side_effects
        or request.filesystem_write
        or request.production
        or request.external_call
        or request.persistent_changes
        or "deploy" in action
    )


def _is_open_scope(value: str) -> bool:
    return _clean_text(value).lower() in {"*", "all", "any", "global", "open", "unrestricted", "/"}


def _is_ambiguous_command(value: str) -> bool:
    text = _clean_text(value).lower()
    return text in {"*", "...", "unknown", "any", "all", "run", "execute"} or text.endswith(" *")


def _redacted_text(value: Any) -> str:
    safe, _ = redact_sensitive_data(str(value or ""))
    return _clean_text(safe)


def _optional_text(value: Any) -> Optional[str]:
    text = _clean_text(value)
    return text or None


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _deduplicate(values: List[str]) -> List[str]:
    return list(dict.fromkeys(value for value in values if value))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
