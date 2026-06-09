from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_PREVIEW_REASON = (
    "Ambient Vision session preview is prepare-only; no camera, recording, streaming, "
    "storage, external vision, approval, Hermes, mission, task, or execution path is enabled."
)
_SENSITIVE_WARNING = (
    "Sensitive visual capability requested; future activation would require strong approval "
    "and remains disabled."
)


@dataclass(frozen=True)
class AmbientVisionStatus:
    prepare_only: bool = True
    vision_available: bool = False
    camera_connected: bool = False
    camera_active: bool = False
    recording_enabled: bool = False
    streaming_enabled: bool = False
    continuous_watch_enabled: bool = False
    face_analysis_enabled: bool = False
    person_analysis_enabled: bool = False
    external_vision_calls_enabled: bool = False
    image_storage_enabled: bool = False
    execution_enabled: bool = False
    hard_stop_available: bool = True
    privacy_redaction_enabled: bool = True
    requires_approval_for_sensitive_capture: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        for name in (
            "vision_available",
            "camera_connected",
            "camera_active",
            "recording_enabled",
            "streaming_enabled",
            "continuous_watch_enabled",
            "face_analysis_enabled",
            "person_analysis_enabled",
            "external_vision_calls_enabled",
            "image_storage_enabled",
            "execution_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "hard_stop_available", True)
        object.__setattr__(self, "privacy_redaction_enabled", True)
        object.__setattr__(self, "requires_approval_for_sensitive_capture", True)

    @classmethod
    def placeholder(cls) -> "AmbientVisionStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AmbientVisionStatus":
        return cls()

    def to_dict(self) -> Dict[str, bool]:
        return {
            "prepare_only": True,
            "vision_available": False,
            "camera_connected": False,
            "camera_active": False,
            "recording_enabled": False,
            "streaming_enabled": False,
            "continuous_watch_enabled": False,
            "face_analysis_enabled": False,
            "person_analysis_enabled": False,
            "external_vision_calls_enabled": False,
            "image_storage_enabled": False,
            "execution_enabled": False,
            "hard_stop_available": True,
            "privacy_redaction_enabled": True,
            "requires_approval_for_sensitive_capture": True,
        }


@dataclass(frozen=True)
class AmbientVisionPrivacyPolicy:
    prepare_only: bool = True
    camera_requires_explicit_start: bool = True
    visible_indicator_required: bool = True
    no_recording_by_default: bool = True
    no_streaming_by_default: bool = True
    no_face_analysis_by_default: bool = True
    no_person_analysis_by_default: bool = True
    no_retention_by_default: bool = True
    no_external_uploads: bool = True
    hard_stop_phrase: str = "no mires"
    sensitive_capture_requires_strong_approval: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        for name in (
            "camera_requires_explicit_start",
            "visible_indicator_required",
            "no_recording_by_default",
            "no_streaming_by_default",
            "no_face_analysis_by_default",
            "no_person_analysis_by_default",
            "no_retention_by_default",
            "no_external_uploads",
            "sensitive_capture_requires_strong_approval",
        ):
            object.__setattr__(self, name, True)
        object.__setattr__(self, "hard_stop_phrase", "no mires")

    @classmethod
    def placeholder(cls) -> "AmbientVisionPrivacyPolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AmbientVisionPrivacyPolicy":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "camera_requires_explicit_start": True,
            "visible_indicator_required": True,
            "no_recording_by_default": True,
            "no_streaming_by_default": True,
            "no_face_analysis_by_default": True,
            "no_person_analysis_by_default": True,
            "no_retention_by_default": True,
            "no_external_uploads": True,
            "hard_stop_phrase": "no mires",
            "sensitive_capture_requires_strong_approval": True,
        }


@dataclass(frozen=True)
class AmbientVisionSessionPreview:
    prepare_only: bool = True
    session_requested: bool = False
    would_start_camera: bool = False
    would_record: bool = False
    would_stream: bool = False
    would_store_images: bool = False
    would_call_external_vision: bool = False
    would_analyze_people: bool = False
    would_execute: bool = False
    approval_required: bool = False
    strong_approval_required: bool = False
    privacy_boundary_triggered: bool = False
    reason: str = _PREVIEW_REASON
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "session_requested", bool(self.session_requested))
        for name in (
            "would_start_camera",
            "would_record",
            "would_stream",
            "would_store_images",
            "would_call_external_vision",
            "would_analyze_people",
            "would_execute",
        ):
            object.__setattr__(self, name, False)
        boundary = bool(self.privacy_boundary_triggered or self.strong_approval_required)
        object.__setattr__(self, "privacy_boundary_triggered", boundary)
        object.__setattr__(self, "strong_approval_required", boundary)
        object.__setattr__(self, "approval_required", bool(self.approval_required or boundary))
        object.__setattr__(self, "reason", _safe_reason(self.reason))
        object.__setattr__(self, "warnings", [_safe_warning(item) for item in self.warnings if _safe_warning(item)])

    @classmethod
    def placeholder(cls) -> "AmbientVisionSessionPreview":
        return cls()

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "AmbientVisionSessionPreview":
        source = dict(data or {})
        ordinary_capture = any(
            bool(source.get(key, False))
            for key in (
                "camera_requested",
                "session_requested",
            )
        )
        sensitive = any(
            bool(source.get(key, False))
            for key in (
                "continuous_watch_requested",
                "external_vision_requested",
                "face_analysis_requested",
                "image_storage_requested",
                "person_analysis_requested",
                "recording_requested",
                "sensitive_capture_requested",
                "streaming_requested",
            )
        )
        session_requested = bool(ordinary_capture or sensitive)
        warnings = [_SENSITIVE_WARNING] if sensitive else []
        return cls(
            session_requested=session_requested,
            approval_required=session_requested,
            strong_approval_required=sensitive,
            privacy_boundary_triggered=sensitive,
            warnings=warnings,
        )

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AmbientVisionSessionPreview":
        source = dict(data or {})
        return cls(
            session_requested=bool(source.get("session_requested", False)),
            approval_required=bool(source.get("approval_required", False)),
            strong_approval_required=bool(source.get("strong_approval_required", False)),
            privacy_boundary_triggered=bool(source.get("privacy_boundary_triggered", False)),
            reason=str(source.get("reason", _PREVIEW_REASON)),
            warnings=[str(item) for item in source.get("warnings", []) or []],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "session_requested": self.session_requested,
            "would_start_camera": False,
            "would_record": False,
            "would_stream": False,
            "would_store_images": False,
            "would_call_external_vision": False,
            "would_analyze_people": False,
            "would_execute": False,
            "approval_required": self.approval_required,
            "strong_approval_required": self.strong_approval_required,
            "privacy_boundary_triggered": self.privacy_boundary_triggered,
            "reason": self.reason,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class AmbientVisionStopControl:
    prepare_only: bool = True
    hard_stop_available: bool = True
    hard_stop_phrase: str = "no mires"
    camera_stop_would_execute: bool = False
    active_session_required: bool = False
    execution_enabled: bool = False
    audit_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "hard_stop_available", True)
        object.__setattr__(self, "hard_stop_phrase", "no mires")
        object.__setattr__(self, "camera_stop_would_execute", False)
        object.__setattr__(self, "active_session_required", False)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "audit_required", True)

    @classmethod
    def placeholder(cls) -> "AmbientVisionStopControl":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "AmbientVisionStopControl":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "hard_stop_available": True,
            "hard_stop_phrase": "no mires",
            "camera_stop_would_execute": False,
            "active_session_required": False,
            "execution_enabled": False,
            "audit_required": True,
        }


def _safe_reason(value: Any) -> str:
    text = " ".join(str(value or "").strip().split())
    return text[:300] if text else _PREVIEW_REASON


def _safe_warning(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:240]
