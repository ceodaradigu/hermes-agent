from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional


_DEVICE_TYPES = {"desktop", "mobile", "watch", "glasses", "tablet", "unknown"}
_SAFE_DEVICE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,79}$")
_PAIRING_REASON = "Device pairing preview is prepare-only; no device is paired or trusted."
_REVOKE_REASON = "Device revoke preview is prepare-only; no device is removed."
_APPROVAL_REASON = (
    "Device approval channel preview is prepare-only; trusted-device status never replaces "
    "strong approval and no approval action is created."
)
_SYNC_REASON = "Device sync preview is prepare-only; no state is synchronized or persisted."
_NOTIFICATION_REASON = "Notification routing preview is prepare-only; no notification or push is sent."


@dataclass(frozen=True)
class MultiDeviceRuntimeStatus:
    prepare_only: bool = True
    runtime_available: bool = False
    device_registry_enabled: bool = False
    trusted_devices_enabled: bool = False
    pairing_enabled: bool = False
    revoke_enabled: bool = False
    approval_from_device_enabled: bool = False
    sync_enabled: bool = False
    notification_routing_enabled: bool = False
    websocket_enabled: bool = False
    background_runtime_enabled: bool = False
    execution_enabled: bool = False
    hermes_connected: bool = False
    approval_gateway_called: bool = False

    @classmethod
    def placeholder(cls) -> "MultiDeviceRuntimeStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "MultiDeviceRuntimeStatus":
        return cls()

    def to_dict(self) -> Dict[str, bool]:
        return {
            "prepare_only": True,
            "runtime_available": False,
            "device_registry_enabled": False,
            "trusted_devices_enabled": False,
            "pairing_enabled": False,
            "revoke_enabled": False,
            "approval_from_device_enabled": False,
            "sync_enabled": False,
            "notification_routing_enabled": False,
            "websocket_enabled": False,
            "background_runtime_enabled": False,
            "execution_enabled": False,
            "hermes_connected": False,
            "approval_gateway_called": False,
        }


@dataclass(frozen=True)
class DeviceCapabilityProfile:
    prepare_only: bool = True
    device_id: str = "device-placeholder"
    device_type: str = "unknown"
    trusted: bool = False
    can_view_status: bool = True
    can_preview_intent: bool = True
    can_request_approval: bool = False
    can_approve: bool = False
    can_reject: bool = False
    can_execute: bool = False
    can_use_microphone: bool = False
    can_use_camera: bool = False
    can_use_location: bool = False
    can_receive_notifications: bool = False
    strong_approval_capable: bool = False
    requires_pairing: bool = True
    revocable: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "device_id", _safe_device_id(self.device_id))
        object.__setattr__(self, "device_type", _safe_device_type(self.device_type))
        object.__setattr__(self, "trusted", False)
        object.__setattr__(self, "can_view_status", bool(self.can_view_status))
        object.__setattr__(self, "can_preview_intent", bool(self.can_preview_intent))
        for name in (
            "can_request_approval",
            "can_approve",
            "can_reject",
            "can_execute",
            "can_use_microphone",
            "can_use_camera",
            "can_use_location",
            "can_receive_notifications",
            "strong_approval_capable",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "requires_pairing", True)
        object.__setattr__(self, "revocable", True)

    @classmethod
    def placeholder(cls) -> "DeviceCapabilityProfile":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "DeviceCapabilityProfile":
        source = dict(data or {})
        return cls(
            device_id=source.get("device_id", "device-placeholder"),
            device_type=source.get("device_type", "unknown"),
            can_view_status=bool(source.get("can_view_status", True)),
            can_preview_intent=bool(source.get("can_preview_intent", True)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "device_id": self.device_id,
            "device_type": self.device_type,
            "trusted": False,
            "can_view_status": self.can_view_status,
            "can_preview_intent": self.can_preview_intent,
            "can_request_approval": False,
            "can_approve": False,
            "can_reject": False,
            "can_execute": False,
            "can_use_microphone": False,
            "can_use_camera": False,
            "can_use_location": False,
            "can_receive_notifications": False,
            "strong_approval_capable": False,
            "requires_pairing": True,
            "revocable": True,
        }


@dataclass(frozen=True)
class DeviceRegistrySnapshot:
    prepare_only: bool = True
    registry_available: bool = False
    device_count: int = 0
    trusted_device_count: int = 0
    devices: List[DeviceCapabilityProfile] = field(default_factory=list)
    persistence_enabled: bool = False
    secrets_included: bool = False
    pairing_material_included: bool = False

    def __post_init__(self) -> None:
        safe_devices = [
            DeviceCapabilityProfile.from_dict(item if isinstance(item, dict) else item.to_dict())
            for item in self.devices
            if isinstance(item, (dict, DeviceCapabilityProfile))
        ]
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "registry_available", False)
        object.__setattr__(self, "devices", safe_devices)
        object.__setattr__(self, "device_count", len(safe_devices))
        object.__setattr__(self, "trusted_device_count", 0)
        object.__setattr__(self, "persistence_enabled", False)
        object.__setattr__(self, "secrets_included", False)
        object.__setattr__(self, "pairing_material_included", False)

    @classmethod
    def placeholder(cls) -> "DeviceRegistrySnapshot":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "DeviceRegistrySnapshot":
        source = dict(data or {})
        return cls(devices=list(source.get("devices") or []))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "registry_available": False,
            "device_count": self.device_count,
            "trusted_device_count": 0,
            "devices": [item.to_dict() for item in self.devices],
            "persistence_enabled": False,
            "secrets_included": False,
            "pairing_material_included": False,
        }


@dataclass(frozen=True)
class DevicePairingPreview:
    prepare_only: bool = True
    device_id: str = "device-placeholder"
    device_type: str = "unknown"
    pairing_requested: bool = False
    would_pair_device: bool = False
    device_trusted_after_preview: bool = False
    pairing_code_created: bool = False
    strong_approval_required: bool = True
    approval_gateway_called: bool = False
    execution_enabled: bool = False
    reason: str = _PAIRING_REASON
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "device_id", _safe_device_id(self.device_id))
        object.__setattr__(self, "device_type", _safe_device_type(self.device_type))
        object.__setattr__(self, "pairing_requested", bool(self.pairing_requested))
        object.__setattr__(self, "would_pair_device", False)
        object.__setattr__(self, "device_trusted_after_preview", False)
        object.__setattr__(self, "pairing_code_created", False)
        object.__setattr__(self, "strong_approval_required", True)
        object.__setattr__(self, "approval_gateway_called", False)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "reason", _safe_text(self.reason, _PAIRING_REASON))
        object.__setattr__(self, "warnings", _safe_warnings(self.warnings))

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "DevicePairingPreview":
        source = dict(data or {})
        return cls(
            device_id=source.get("device_id", "device-placeholder"),
            device_type=source.get("device_type", "unknown"),
            pairing_requested=bool(source.get("pairing_requested", False)),
            warnings=["Pairing requires a future explicit strong-approval flow."] if source.get("pairing_requested") else [],
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "device_id": self.device_id,
            "device_type": self.device_type,
            "pairing_requested": self.pairing_requested,
            "would_pair_device": False,
            "device_trusted_after_preview": False,
            "pairing_code_created": False,
            "strong_approval_required": True,
            "approval_gateway_called": False,
            "execution_enabled": False,
            "reason": self.reason,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class DeviceRevokePreview:
    prepare_only: bool = True
    device_id: str = "device-placeholder"
    revoke_requested: bool = False
    would_revoke_device: bool = False
    device_removed: bool = False
    audit_required: bool = True
    approval_gateway_called: bool = False
    execution_enabled: bool = False
    reason: str = _REVOKE_REASON

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "device_id", _safe_device_id(self.device_id))
        object.__setattr__(self, "revoke_requested", bool(self.revoke_requested))
        object.__setattr__(self, "would_revoke_device", False)
        object.__setattr__(self, "device_removed", False)
        object.__setattr__(self, "audit_required", True)
        object.__setattr__(self, "approval_gateway_called", False)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "reason", _safe_text(self.reason, _REVOKE_REASON))

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "DeviceRevokePreview":
        source = dict(data or {})
        return cls(device_id=source.get("device_id", "device-placeholder"), revoke_requested=source.get("revoke_requested", False))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "device_id": self.device_id,
            "revoke_requested": self.revoke_requested,
            "would_revoke_device": False,
            "device_removed": False,
            "audit_required": True,
            "approval_gateway_called": False,
            "execution_enabled": False,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DeviceApprovalChannelPreview:
    prepare_only: bool = True
    device_id: str = "device-placeholder"
    approval_channel_requested: bool = False
    device_trusted: bool = False
    strong_approval_required: bool = True
    challenge_required: bool = True
    approval_created: bool = False
    approval_granted: bool = False
    approval_rejected: bool = False
    approval_gateway_called: bool = False
    execution_enabled: bool = False
    approve_all_forever_allowed: bool = False
    reason: str = _APPROVAL_REASON
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "device_id", _safe_device_id(self.device_id))
        object.__setattr__(self, "approval_channel_requested", bool(self.approval_channel_requested))
        for name in (
            "device_trusted",
            "approval_created",
            "approval_granted",
            "approval_rejected",
            "approval_gateway_called",
            "execution_enabled",
            "approve_all_forever_allowed",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "strong_approval_required", True)
        object.__setattr__(self, "challenge_required", True)
        object.__setattr__(self, "reason", _safe_text(self.reason, _APPROVAL_REASON))
        object.__setattr__(self, "warnings", _safe_warnings(self.warnings))

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "DeviceApprovalChannelPreview":
        source = dict(data or {})
        requested = bool(source.get("approval_channel_requested", False))
        warnings = ["Trusted devices never replace strong approval or permit approve-all-forever."] if requested else []
        return cls(device_id=source.get("device_id", "device-placeholder"), approval_channel_requested=requested, warnings=warnings)

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "device_id": self.device_id,
            "approval_channel_requested": self.approval_channel_requested,
            "device_trusted": False,
            "strong_approval_required": True,
            "challenge_required": True,
            "approval_created": False,
            "approval_granted": False,
            "approval_rejected": False,
            "approval_gateway_called": False,
            "execution_enabled": False,
            "approve_all_forever_allowed": False,
            "reason": self.reason,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class DeviceSyncPreview:
    prepare_only: bool = True
    device_id: str = "device-placeholder"
    sync_requested: bool = False
    would_sync: bool = False
    state_changed: bool = False
    persisted: bool = False
    background_sync_started: bool = False
    external_calls_made: bool = False
    execution_enabled: bool = False
    reason: str = _SYNC_REASON

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "device_id", _safe_device_id(self.device_id))
        object.__setattr__(self, "sync_requested", bool(self.sync_requested))
        for name in ("would_sync", "state_changed", "persisted", "background_sync_started", "external_calls_made", "execution_enabled"):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "reason", _safe_text(self.reason, _SYNC_REASON))

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "DeviceSyncPreview":
        source = dict(data or {})
        return cls(device_id=source.get("device_id", "device-placeholder"), sync_requested=source.get("sync_requested", False))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "device_id": self.device_id,
            "sync_requested": self.sync_requested,
            "would_sync": False,
            "state_changed": False,
            "persisted": False,
            "background_sync_started": False,
            "external_calls_made": False,
            "execution_enabled": False,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class NotificationRoutingPreview:
    prepare_only: bool = True
    device_id: str = "device-placeholder"
    notification_requested: bool = False
    would_route_notification: bool = False
    push_sent: bool = False
    background_routing_started: bool = False
    external_calls_made: bool = False
    secrets_included: bool = False
    execution_enabled: bool = False
    reason: str = _NOTIFICATION_REASON

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "device_id", _safe_device_id(self.device_id))
        object.__setattr__(self, "notification_requested", bool(self.notification_requested))
        for name in (
            "would_route_notification",
            "push_sent",
            "background_routing_started",
            "external_calls_made",
            "secrets_included",
            "execution_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "reason", _safe_text(self.reason, _NOTIFICATION_REASON))

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "NotificationRoutingPreview":
        source = dict(data or {})
        return cls(device_id=source.get("device_id", "device-placeholder"), notification_requested=source.get("notification_requested", False))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "device_id": self.device_id,
            "notification_requested": self.notification_requested,
            "would_route_notification": False,
            "push_sent": False,
            "background_routing_started": False,
            "external_calls_made": False,
            "secrets_included": False,
            "execution_enabled": False,
            "reason": self.reason,
        }


def _safe_device_type(value: Any) -> str:
    device_type = str(value or "unknown").strip().lower()
    return device_type if device_type in _DEVICE_TYPES else "unknown"


def _safe_device_id(value: Any) -> str:
    device_id = str(value or "").strip()
    if not _SAFE_DEVICE_ID_PATTERN.fullmatch(device_id) or _contains_sensitive_marker(device_id):
        return "device-placeholder"
    return device_id


def _safe_text(value: Any, fallback: str) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text or _contains_sensitive_marker(text):
        return fallback
    return text[:300]


def _safe_warnings(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    return [_safe_text(item, "Sensitive warning details were redacted.")[:240] for item in values[:10]]


def _contains_sensitive_marker(value: Any) -> bool:
    text = str(value or "").lower()
    return any(marker in text for marker in (".env", "api_key", "apikey", "authorization", "bearer", "password", "private_key", "secret", "token"))
