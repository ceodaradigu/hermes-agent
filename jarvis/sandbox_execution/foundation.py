from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional


_BLOCKED_PATH_MARKERS = (".env", "id_rsa", "private_key", "credentials", "secrets")
_BLOCKED_COMMAND_MARKERS = ("sudo", "rm -rf", "curl | sh", "wget | sh", "chmod 777")
_SECRET_MARKERS = (
    ".env",
    "api key",
    "api-key",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "credentials",
    "id_rsa",
    "password",
    "private key",
    "private-key",
    "private_key",
    "secret",
    "secrets",
    "token",
)
_INSTALL_PATTERN = re.compile(r"(^|[;&|]\s*|\s)(apt(-get)?|brew|dnf|npm|pip|pip3|pnpm|yarn)\s+(install|add)\b", re.I)
_PRODUCTION_PATTERN = re.compile(r"\b(deploy|production|prod|release)\b", re.I)
_NETWORK_PATTERN = re.compile(r"\b(curl|wget|ssh|scp|rsync|nc|netcat|ftp|http://|https://)\b", re.I)
_REDACTED_COMMAND = "[redacted sensitive sandbox command]"
_REDACTED_PATH = "[redacted sensitive working directory]"
_PREPARE_ONLY_REASON = "Sandbox execution is prepare-only; no command, shell, tool, or rollback is executed."


@dataclass(frozen=True)
class SandboxExecutionStatus:
    prepare_only: bool = True
    sandbox_available: bool = False
    executor_connected: bool = False
    execution_enabled: bool = False
    dry_run_required: bool = True
    filesystem_scope_enforced: bool = True
    secret_scan_enabled: bool = True
    network_access_enabled: bool = False
    production_access_enabled: bool = False
    install_commands_enabled: bool = False
    rollback_required: bool = True
    audit_required: bool = True
    hermes_connected: bool = False
    approval_gateway_called: bool = False

    @classmethod
    def placeholder(cls) -> "SandboxExecutionStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "SandboxExecutionStatus":
        return cls()

    def to_dict(self) -> Dict[str, bool]:
        return {
            "prepare_only": True,
            "sandbox_available": False,
            "executor_connected": False,
            "execution_enabled": False,
            "dry_run_required": True,
            "filesystem_scope_enforced": True,
            "secret_scan_enabled": True,
            "network_access_enabled": False,
            "production_access_enabled": False,
            "install_commands_enabled": False,
            "rollback_required": True,
            "audit_required": True,
            "hermes_connected": False,
            "approval_gateway_called": False,
        }


@dataclass(frozen=True)
class SandboxExecutionPolicy:
    prepare_only: bool = True
    allowed_working_roots: List[str] = field(default_factory=list)
    blocked_path_markers: List[str] = field(default_factory=lambda: list(_BLOCKED_PATH_MARKERS))
    blocked_command_markers: List[str] = field(default_factory=lambda: list(_BLOCKED_COMMAND_MARKERS))
    network_default: str = "blocked"
    production_default: str = "blocked"
    install_default: str = "blocked"
    dry_run_required: bool = True
    rollback_required: bool = True
    strong_approval_required_for_production: bool = True
    strong_approval_required_for_secrets: bool = True
    strong_approval_required_for_installs: bool = True

    @classmethod
    def placeholder(cls) -> "SandboxExecutionPolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "SandboxExecutionPolicy":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "allowed_working_roots": [],
            "blocked_path_markers": list(_BLOCKED_PATH_MARKERS),
            "blocked_command_markers": list(_BLOCKED_COMMAND_MARKERS),
            "network_default": "blocked",
            "production_default": "blocked",
            "install_default": "blocked",
            "dry_run_required": True,
            "rollback_required": True,
            "strong_approval_required_for_production": True,
            "strong_approval_required_for_secrets": True,
            "strong_approval_required_for_installs": True,
        }


@dataclass(frozen=True)
class SandboxCommandPlan:
    prepare_only: bool = True
    command: str = ""
    working_directory: str = ""
    requested_network: bool = False
    requested_install: bool = False
    requested_production: bool = False
    requested_secret_access: bool = False
    would_execute: bool = False
    execution_enabled: bool = False
    requires_approval: bool = False
    requires_strong_approval: bool = False
    blocked: bool = False
    reason: str = _PREPARE_ONLY_REASON
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        analysis = _analyze(self.command, self.working_directory)
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "command", analysis["command"])
        object.__setattr__(self, "working_directory", analysis["working_directory"])
        for name in ("requested_network", "requested_install", "requested_production", "requested_secret_access"):
            object.__setattr__(self, name, analysis[name])
        object.__setattr__(self, "would_execute", False)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "requires_approval", analysis["requires_approval"])
        object.__setattr__(self, "requires_strong_approval", analysis["requires_strong_approval"])
        object.__setattr__(self, "blocked", analysis["blocked"])
        object.__setattr__(self, "reason", analysis["reason"])
        object.__setattr__(self, "warnings", analysis["warnings"])

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "SandboxCommandPlan":
        source = dict(data or {})
        return cls(command=str(source.get("command", "")), working_directory=str(source.get("working_directory", "")))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "command": self.command,
            "working_directory": self.working_directory,
            "requested_network": self.requested_network,
            "requested_install": self.requested_install,
            "requested_production": self.requested_production,
            "requested_secret_access": self.requested_secret_access,
            "would_execute": False,
            "execution_enabled": False,
            "requires_approval": self.requires_approval,
            "requires_strong_approval": self.requires_strong_approval,
            "blocked": self.blocked,
            "reason": self.reason,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class SandboxDryRunResult:
    prepare_only: bool = True
    dry_run_completed: bool = True
    would_execute: bool = False
    execution_enabled: bool = False
    blocked: bool = False
    risk_level: str = "low"
    filesystem_scope_ok: bool = True
    secret_scan_passed: bool = True
    network_blocked: bool = False
    production_blocked: bool = False
    install_blocked: bool = False
    approval_required: bool = False
    strong_approval_required: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    audit_preview_created: bool = True
    rollback_preview_created: bool = True
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "SandboxDryRunResult":
        plan = SandboxCommandPlan.from_request(data)
        directory_requested = bool(str((data or {}).get("working_directory", "")).strip())
        filesystem_scope_ok = not directory_requested and not plan.requested_secret_access
        network_blocked = plan.requested_network
        production_blocked = plan.requested_production
        install_blocked = plan.requested_install
        blocked = bool(plan.blocked or not filesystem_scope_ok)
        if blocked:
            risk = "blocked"
        elif plan.requires_strong_approval:
            risk = "high"
        elif plan.requires_approval:
            risk = "medium"
        else:
            risk = "low"
        warnings = list(plan.warnings)
        if not filesystem_scope_ok and "Requested working directory is outside the empty sandbox allowlist." not in warnings:
            warnings.append("Requested working directory is outside the empty sandbox allowlist.")
        return cls(
            blocked=blocked,
            risk_level=risk,
            filesystem_scope_ok=filesystem_scope_ok,
            secret_scan_passed=not plan.requested_secret_access,
            network_blocked=network_blocked,
            production_blocked=production_blocked,
            install_blocked=install_blocked,
            approval_required=plan.requires_approval,
            strong_approval_required=plan.requires_strong_approval,
            warnings=warnings,
        )

    from_dict = from_request

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "dry_run_completed", True)
        object.__setattr__(self, "would_execute", False)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "hermes_called", False)
        object.__setattr__(self, "approval_gateway_called", False)
        object.__setattr__(self, "audit_preview_created", True)
        object.__setattr__(self, "rollback_preview_created", True)
        object.__setattr__(self, "warnings", _safe_warnings(self.warnings))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "dry_run_completed": True,
            "would_execute": False,
            "execution_enabled": False,
            "blocked": self.blocked,
            "risk_level": self.risk_level,
            "filesystem_scope_ok": self.filesystem_scope_ok,
            "secret_scan_passed": self.secret_scan_passed,
            "network_blocked": self.network_blocked,
            "production_blocked": self.production_blocked,
            "install_blocked": self.install_blocked,
            "approval_required": self.approval_required,
            "strong_approval_required": self.strong_approval_required,
            "hermes_called": False,
            "approval_gateway_called": False,
            "audit_preview_created": True,
            "rollback_preview_created": True,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class SandboxRollbackPreview:
    prepare_only: bool = True
    rollback_required: bool = False
    reversible: bool = True
    irreversible: bool = False
    would_rollback: bool = False
    execution_enabled: bool = False
    plan: str = "No rollback action is needed for a read-only preview."
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "SandboxRollbackPreview":
        plan = SandboxCommandPlan.from_request(data)
        risky = bool(plan.blocked or plan.requires_approval or plan.requires_strong_approval)
        irreversible = bool(plan.requested_production or _contains_any(str((data or {}).get("command", "")), ("rm -rf",)))
        return cls(
            rollback_required=risky,
            reversible=not irreversible,
            irreversible=irreversible,
            plan=(
                "No real rollback is available for an irreversible or production-like command; execution remains blocked."
                if irreversible
                else "A future executor must snapshot affected files and document restoration before execution."
                if risky
                else "No rollback action is needed for a read-only preview."
            ),
            warnings=list(plan.warnings),
        )

    from_dict = from_request

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "would_rollback", False)
        object.__setattr__(self, "execution_enabled", False)
        if _contains_any(self.plan, _SECRET_MARKERS):
            object.__setattr__(self, "plan", "Sensitive rollback details were redacted; no rollback is executed.")
        object.__setattr__(self, "warnings", _safe_warnings(self.warnings))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "rollback_required": self.rollback_required,
            "reversible": self.reversible,
            "irreversible": self.irreversible,
            "would_rollback": False,
            "execution_enabled": False,
            "plan": self.plan,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class SandboxAuditPreview:
    prepare_only: bool = True
    audit_required: bool = True
    persisted: bool = False
    command: str = ""
    working_directory: str = ""
    decision: str = "previewed"
    secrets_redacted: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "SandboxAuditPreview":
        plan = SandboxCommandPlan.from_request(data)
        return cls(
            command=plan.command,
            working_directory=plan.working_directory,
            decision="blocked" if plan.blocked else "previewed",
            secrets_redacted=plan.requested_secret_access,
            warnings=list(plan.warnings),
        )

    from_dict = from_request

    def __post_init__(self) -> None:
        analysis = _analyze(self.command, self.working_directory)
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "audit_required", True)
        object.__setattr__(self, "persisted", False)
        object.__setattr__(self, "command", analysis["command"])
        object.__setattr__(self, "working_directory", analysis["working_directory"])
        object.__setattr__(self, "decision", "blocked" if analysis["blocked"] else "previewed")
        object.__setattr__(self, "secrets_redacted", bool(self.secrets_redacted or analysis["requested_secret_access"]))
        object.__setattr__(self, "hermes_called", False)
        object.__setattr__(self, "approval_gateway_called", False)
        object.__setattr__(self, "warnings", _safe_warnings([*self.warnings, *analysis["warnings"]]))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "audit_required": True,
            "persisted": False,
            "command": self.command,
            "working_directory": self.working_directory,
            "decision": self.decision,
            "secrets_redacted": self.secrets_redacted,
            "hermes_called": False,
            "approval_gateway_called": False,
            "warnings": list(self.warnings),
        }


def _analyze(command: str, working_directory: str) -> Dict[str, Any]:
    raw_command = " ".join(str(command or "").strip().split())[:1000]
    raw_directory = " ".join(str(working_directory or "").strip().split())[:500]
    secret = _contains_any(f"{raw_command} {raw_directory}", _SECRET_MARKERS)
    dangerous = _contains_any(raw_command, _BLOCKED_COMMAND_MARKERS)
    requested_install = bool(_INSTALL_PATTERN.search(raw_command))
    requested_production = bool(_PRODUCTION_PATTERN.search(raw_command))
    requested_network = bool(_NETWORK_PATTERN.search(raw_command))
    path_blocked = _contains_any(raw_directory, _BLOCKED_PATH_MARKERS)
    directory_outside_scope = bool(raw_directory)
    blocked = bool(secret or dangerous or requested_install or requested_production or requested_network or path_blocked or directory_outside_scope)
    strong = bool(secret or requested_install or requested_production)
    approval = bool(blocked or strong)
    warnings = []
    if secret:
        warnings.append("Secret-like input was detected and redacted; access remains blocked.")
    if dangerous:
        warnings.append("A dangerous command marker was detected; execution remains blocked.")
    if requested_network:
        warnings.append("Network access is blocked by default.")
    if requested_install:
        warnings.append("Install commands are blocked and require future strong approval.")
    if requested_production:
        warnings.append("Production-like actions are blocked and require future strong approval.")
    if directory_outside_scope:
        warnings.append("Requested working directory is outside the empty sandbox allowlist.")
    return {
        "command": _REDACTED_COMMAND if secret else raw_command,
        "working_directory": _REDACTED_PATH if secret or path_blocked else raw_directory,
        "requested_network": requested_network,
        "requested_install": requested_install,
        "requested_production": requested_production,
        "requested_secret_access": secret,
        "requires_approval": approval,
        "requires_strong_approval": strong,
        "blocked": blocked,
        "reason": _PREPARE_ONLY_REASON if not blocked else "Sandbox policy blocked the request; no execution path is enabled.",
        "warnings": _safe_warnings(warnings),
    }


def _safe_warnings(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    result = []
    for item in values[:10]:
        text = " ".join(str(item or "").strip().split())[:240]
        result.append("Sensitive warning details were redacted." if _contains_any(text, _SECRET_MARKERS) else text)
    return [item for item in result if item]


def _contains_any(value: Any, markers: Any) -> bool:
    text = str(value or "").lower()
    return any(str(marker).lower() in text for marker in markers)
