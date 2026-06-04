from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional

from jarvis.command_center import CommandCenterViewModel
from jarvis.policy.policy_engine import PolicyEngine
from jarvis.voice.companion import (
    VoiceCompanionIntentPreview,
    VoiceCompanionPreviewPolicyDecision,
)


_MOBILE_STATUS_REASON = "Mobile Companion is prepare-only; no native app runtime is connected."
_MOBILE_POLICY_REASON = "Mobile Companion can read safe snapshots and preview intent only."
_MOBILE_PREVIEW_REASON = "Mobile Companion preview is prepare-only; no execution path is enabled."
_MOBILE_CREDENTIAL_MARKER_PATTERN = re.compile(
    r"(?<![a-z0-9])("
    r"api[\s_-]*key|"
    r"private[\s_-]*key|"
    r"access[\s_-]*key|"
    r"refresh[\s_-]*token|"
    r"client[\s_-]*secret|"
    r"bearer[\s_-]*token"
    r")(?![a-z0-9])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MobileCompanionStatus:
    """Prepare-only status for the future Mobile Companion surface."""

    prepare_only: bool = True
    mobile_available: bool = False
    native_app_connected: bool = False
    push_enabled: bool = False
    background_sync_enabled: bool = False
    location_enabled: bool = False
    contacts_enabled: bool = False
    camera_enabled: bool = False
    microphone_enabled: bool = False
    execution_enabled: bool = False
    approval_actions_enabled: bool = False
    requires_approval_for_sensitive_actions: bool = True

    @classmethod
    def placeholder(cls) -> "MobileCompanionStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "MobileCompanionStatus":
        return cls()

    def to_dict(self) -> Dict[str, bool]:
        return {
            "prepare_only": True,
            "mobile_available": False,
            "native_app_connected": False,
            "push_enabled": False,
            "background_sync_enabled": False,
            "location_enabled": False,
            "contacts_enabled": False,
            "camera_enabled": False,
            "microphone_enabled": False,
            "execution_enabled": False,
            "approval_actions_enabled": False,
            "requires_approval_for_sensitive_actions": True,
        }


@dataclass(frozen=True)
class MobileCompanionPermissionPolicy:
    """Mobile permission policy with all active capabilities disabled."""

    prepare_only: bool = True
    can_read_command_center: bool = True
    can_preview_intent: bool = True
    can_execute: bool = False
    can_approve: bool = False
    can_reject: bool = False
    can_use_location: bool = False
    can_use_contacts: bool = False
    can_use_camera: bool = False
    can_use_microphone: bool = False
    can_receive_push: bool = False
    can_run_background: bool = False

    @classmethod
    def placeholder(cls) -> "MobileCompanionPermissionPolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "MobileCompanionPermissionPolicy":
        return cls()

    def to_dict(self) -> Dict[str, bool]:
        return {
            "prepare_only": True,
            "can_read_command_center": True,
            "can_preview_intent": True,
            "can_execute": False,
            "can_approve": False,
            "can_reject": False,
            "can_use_location": False,
            "can_use_contacts": False,
            "can_use_camera": False,
            "can_use_microphone": False,
            "can_receive_push": False,
            "can_run_background": False,
        }


@dataclass(frozen=True)
class MobileCommandCenterSnapshot:
    """Small mobile-safe projection of CommandCenterViewModel.

    This model intentionally drops payloads, paths, audio fields, raw audit
    text, Hermes command inputs, and approval action bodies. It keeps only
    counts, high-level status, safe flags, and placeholder capability metadata.
    """

    prepare_only: bool = True
    snapshot_id: str = "mobile-command-center-placeholder"
    generated_at: str = ""
    status: str = "ready"
    command_center_status: str = "ready"
    mission_count: int = 0
    pending_approval_count: int = 0
    audit_event_count: int = 0
    agent_count: int = 0
    device_count: int = 0
    mobile_status: MobileCompanionStatus = field(default_factory=MobileCompanionStatus.placeholder)
    permission_policy: MobileCompanionPermissionPolicy = field(
        default_factory=MobileCompanionPermissionPolicy.placeholder
    )
    safety: Dict[str, Any] = field(default_factory=dict)
    capabilities: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "mission_count", max(0, int(self.mission_count)))
        object.__setattr__(self, "pending_approval_count", max(0, int(self.pending_approval_count)))
        object.__setattr__(self, "audit_event_count", max(0, int(self.audit_event_count)))
        object.__setattr__(self, "agent_count", max(0, int(self.agent_count)))
        object.__setattr__(self, "device_count", max(0, int(self.device_count)))
        object.__setattr__(self, "mobile_status", MobileCompanionStatus.from_dict({}))
        object.__setattr__(self, "permission_policy", MobileCompanionPermissionPolicy.from_dict({}))
        object.__setattr__(self, "safety", _safe_snapshot_safety(self.safety))
        object.__setattr__(self, "capabilities", _safe_snapshot_capabilities(self.capabilities))
        object.__setattr__(self, "metadata", _safe_snapshot_metadata(self.metadata))

    @classmethod
    def placeholder(cls) -> "MobileCommandCenterSnapshot":
        return cls(metadata={"source": "empty_placeholder_snapshot"})

    @classmethod
    def from_command_center_view(
        cls,
        view: CommandCenterViewModel,
    ) -> "MobileCommandCenterSnapshot":
        data = view.to_dict()
        return cls(
            snapshot_id=str(data.get("view_id", "mobile-command-center-placeholder")),
            generated_at=str(data.get("generated_at", "")),
            status=str(data.get("status", "ready")),
            command_center_status=str(data.get("status", "ready")),
            mission_count=len(data.get("missions", []) or []),
            pending_approval_count=len(data.get("approvals", []) or []),
            audit_event_count=len(data.get("audit_timeline", []) or []),
            agent_count=len(data.get("agents", []) or []),
            device_count=len(data.get("devices", []) or []),
            safety={
                "execution_enabled": False,
                "approval_actions_enabled": False,
                "hermes_connected": False,
                "approval_gateway_called": False,
                "requires_approval_for_sensitive_actions": True,
                "policy_engine_boundary": (data.get("safety_indicator") or {}).get("policy_engine_boundary", ""),
            },
            capabilities={
                "read_command_center": True,
                "preview_intent": True,
                "execute": False,
                "approve": False,
                "reject": False,
                "push": False,
                "background_sync": False,
                "location": False,
                "contacts": False,
                "camera": False,
                "microphone": False,
            },
            metadata={
                "phase": "F",
                "source": "command_center_mobile_projection",
                "command_center_phase": (data.get("metadata") or {}).get("phase", "unknown"),
                "native_app_connected": False,
            },
        )

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "MobileCommandCenterSnapshot":
        source = dict(data or {})
        return cls(
            snapshot_id=str(source.get("snapshot_id", "mobile-command-center-placeholder")),
            generated_at=str(source.get("generated_at", "")),
            status=str(source.get("status", "ready")),
            command_center_status=str(source.get("command_center_status", source.get("status", "ready"))),
            mission_count=int(source.get("mission_count", 0) or 0),
            pending_approval_count=int(source.get("pending_approval_count", 0) or 0),
            audit_event_count=int(source.get("audit_event_count", 0) or 0),
            agent_count=int(source.get("agent_count", 0) or 0),
            device_count=int(source.get("device_count", 0) or 0),
            safety=dict(source.get("safety") or {}),
            capabilities=dict(source.get("capabilities") or {}),
            metadata=dict(source.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "snapshot_id": self.snapshot_id,
            "generated_at": self.generated_at,
            "status": self.status,
            "command_center_status": self.command_center_status,
            "mission_count": self.mission_count,
            "pending_approval_count": self.pending_approval_count,
            "audit_event_count": self.audit_event_count,
            "agent_count": self.agent_count,
            "device_count": self.device_count,
            "mobile_status": self.mobile_status.to_dict(),
            "permission_policy": self.permission_policy.to_dict(),
            "safety": dict(self.safety),
            "capabilities": dict(self.capabilities),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class MobileIntentPreview:
    """Prepare-only text intent preview for a future mobile client.

    The textual classification is shared with Voice Companion so mobile and
    voice surfaces preview the same user intent categories. The mobile DTO
    remains separate and never enables execution, Hermes calls, or approvals.
    """

    prepare_only: bool = True
    input_text: str = ""
    intent: str = "unknown"
    policy_decision: str = "unknown"
    would_execute: bool = False
    execution_enabled: bool = False
    approval_created: bool = False
    approval_gateway_called: bool = False
    hermes_called: bool = False
    mobile_action_allowed: bool = False
    sensitive_boundary_triggered: bool = False
    warnings: List[str] = field(default_factory=list)
    reason: str = _MOBILE_PREVIEW_REASON

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        sensitive = bool(self.sensitive_boundary_triggered or _contains_sensitive_marker(self.input_text))
        object.__setattr__(self, "input_text", _sanitize_mobile_text(self.input_text, sensitive=sensitive))
        intent = _safe_label(self.intent, fallback="unknown")
        policy_decision = _safe_policy_decision(self.policy_decision)
        if sensitive and policy_decision not in {"requires_approval", "denied"}:
            policy_decision = "requires_approval"
        if sensitive and intent != "denied":
            intent = "requires_approval"
        object.__setattr__(self, "intent", intent)
        object.__setattr__(self, "policy_decision", policy_decision)
        object.__setattr__(self, "would_execute", False)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "approval_created", False)
        object.__setattr__(self, "approval_gateway_called", False)
        object.__setattr__(self, "hermes_called", False)
        object.__setattr__(self, "mobile_action_allowed", False)
        object.__setattr__(self, "sensitive_boundary_triggered", sensitive)
        object.__setattr__(self, "warnings", [_safe_warning(item) for item in self.warnings])
        object.__setattr__(self, "reason", _safe_warning(self.reason or _MOBILE_PREVIEW_REASON))

    @classmethod
    def placeholder(cls) -> "MobileIntentPreview":
        return cls()

    @classmethod
    def from_voice_preview(cls, preview: VoiceCompanionIntentPreview) -> "MobileIntentPreview":
        data = preview.to_dict()
        return cls(
            input_text=str(data.get("input_text", "")),
            intent=str(data.get("intent", "unknown")),
            policy_decision=str(data.get("policy_decision", "unknown")),
            sensitive_boundary_triggered=bool(data.get("sensitive_boundary_triggered", False)),
            warnings=[str(item) for item in data.get("warnings", []) or []],
            reason=str(data.get("reason", _MOBILE_PREVIEW_REASON)),
        )

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        policy_engine: Optional[PolicyEngine] = None,
    ) -> "MobileIntentPreview":
        voice_preview = VoiceCompanionIntentPreview.from_text(
            text,
            policy_engine=policy_engine,
        )
        return cls.from_voice_preview(voice_preview)

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "MobileIntentPreview":
        source = dict(data or {})
        return cls(
            input_text=str(source.get("input_text", "")),
            intent=str(source.get("intent", "unknown")),
            policy_decision=str(source.get("policy_decision", "unknown")),
            sensitive_boundary_triggered=bool(source.get("sensitive_boundary_triggered", False)),
            warnings=[str(item) for item in source.get("warnings", []) or []],
            reason=str(source.get("reason", _MOBILE_PREVIEW_REASON)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "input_text": self.input_text,
            "intent": self.intent,
            "policy_decision": self.policy_decision,
            "would_execute": False,
            "execution_enabled": False,
            "approval_created": False,
            "approval_gateway_called": False,
            "hermes_called": False,
            "mobile_action_allowed": False,
            "sensitive_boundary_triggered": self.sensitive_boundary_triggered,
            "warnings": list(self.warnings),
        }


def _safe_snapshot_safety(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "prepare_only": True,
        "execution_enabled": False,
        "approval_actions_enabled": False,
        "hermes_connected": False,
        "approval_gateway_called": False,
        "requires_approval_for_sensitive_actions": True,
        "policy_engine_boundary": _safe_text(data.get("policy_engine_boundary", "")),
    }


def _safe_snapshot_capabilities(data: Dict[str, Any]) -> Dict[str, bool]:
    return {
        "read_command_center": True,
        "preview_intent": True,
        "execute": False,
        "approve": False,
        "reject": False,
        "push": False,
        "background_sync": False,
        "location": False,
        "contacts": False,
        "camera": False,
        "microphone": False,
    }


def _safe_snapshot_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    source = dict(data or {})
    return {
        "phase": "F",
        "source": _safe_label(source.get("source", "mobile_companion_placeholder")),
        "prepare_only": True,
        "native_app_connected": False,
        "mobile_available": False,
        "execution_enabled": False,
        "approval_actions_enabled": False,
        "reason": _MOBILE_STATUS_REASON,
        "permission_reason": _MOBILE_POLICY_REASON,
    }


def _safe_policy_decision(value: str) -> str:
    normalized = _safe_label(value, fallback="unknown")
    allowed_values = {item.value for item in VoiceCompanionPreviewPolicyDecision}
    return normalized if normalized in allowed_values else "unknown"


def _safe_label(value: Any, *, fallback: str = "unknown") -> str:
    text = str(value or "").strip().lower()
    if not text or _contains_sensitive_marker(text):
        return fallback
    return text.replace(" ", "_")[:64]


def _safe_warning(value: Any) -> str:
    text = _safe_text(value)
    if not text:
        return _MOBILE_PREVIEW_REASON
    if _contains_sensitive_marker(text):
        return "Sensitive mobile preview details were redacted; execution remains disabled."
    return text[:180]


def _sanitize_mobile_text(text: Any, *, sensitive: bool = False) -> str:
    value = _safe_text(text)
    if not value:
        return ""
    if sensitive or _contains_sensitive_marker(value):
        return "[redacted sensitive mobile input]"
    return value[:240]


def _safe_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _contains_sensitive_marker(value: Any) -> bool:
    text = str(value or "").lower()
    if _MOBILE_CREDENTIAL_MARKER_PATTERN.search(text):
        return True
    return any(
        marker in text
        for marker in (
            ".env",
            "api key",
            "api-key",
            "api_key",
            "apikey",
            "authorization",
            "banco",
            "bearer",
            "bearer-token",
            "bearer_token",
            "clave",
            "client secret",
            "client-secret",
            "client_secret",
            "contraseña",
            "contrasena",
            "credencial",
            "credenciales",
            "credential",
            "credentials",
            "dni",
            "password",
            "private key",
            "private-key",
            "private_key",
            "access key",
            "access-key",
            "access_key",
            "refresh token",
            "refresh-token",
            "refresh_token",
            "secret",
            "secreto",
            "tarjeta",
            "token",
        )
    )
