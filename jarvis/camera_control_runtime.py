from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CameraControlState:
    camera_available: bool = True
    camera_session_active: bool = False
    camera_opt_in_required: bool = True
    visible_indicator_required: bool = True
    recording_enabled: bool = False
    external_video_processing_enabled: bool = False
    face_person_analysis_enabled: bool = False
    screen_capture_enabled: bool = False
    stop_phrase: str = "no mires"
    last_session_summary: Optional[str] = None
    blocked_reasons: List[str] = field(default_factory=list)
    execution_enabled: bool = False
    side_effects_enabled: bool = False
    prepare_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "camera_available", True)
        object.__setattr__(self, "camera_session_active", False)
        object.__setattr__(self, "camera_opt_in_required", True)
        object.__setattr__(self, "visible_indicator_required", True)
        for name in (
            "recording_enabled",
            "external_video_processing_enabled",
            "face_person_analysis_enabled",
            "screen_capture_enabled",
            "execution_enabled",
            "side_effects_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "stop_phrase", "no mires")
        object.__setattr__(self, "blocked_reasons", list(self.blocked_reasons))
        object.__setattr__(self, "prepare_only", True)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CameraPreviewDecision:
    would_start_camera: bool = False
    would_record: bool = False
    would_analyze_people: bool = False
    would_capture_screen: bool = False
    opt_in_present: bool = False
    approval_required: bool = True
    strong_approval_required: bool = False
    visible_indicator_ready: bool = False
    local_only: bool = True
    blocked_reasons: List[str] = field(default_factory=list)
    execution_enabled: bool = False
    side_effects_enabled: bool = False
    prepare_only: bool = True

    def __post_init__(self) -> None:
        for name in (
            "would_start_camera",
            "would_record",
            "would_analyze_people",
            "would_capture_screen",
            "execution_enabled",
            "side_effects_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "local_only", True)
        object.__setattr__(self, "blocked_reasons", list(self.blocked_reasons))
        object.__setattr__(self, "prepare_only", True)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CameraControlRuntime:
    """Opt-in camera control-plane. It has no sensor or capture dependency."""

    def status(self) -> Dict[str, Any]:
        return CameraControlState().to_dict()

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            "local_only": True,
            "no_recording_by_default": True,
            "no_person_or_face_analysis": True,
            "no_screen_capture": True,
            "no_external_video": True,
            "opt_in_does_not_start_camera": True,
            "strong_approval_for_sensitive_capture": True,
        }

    def preview_session(
        self,
        *,
        opt_in_present: bool = False,
        visible_indicator_ready: bool = False,
        recording_requested: bool = False,
        analyze_people_requested: bool = False,
        screen_capture_requested: bool = False,
        external_video_requested: bool = False,
    ) -> CameraPreviewDecision:
        sensitive = any(
            (recording_requested, analyze_people_requested, screen_capture_requested, external_video_requested)
        )
        blocked = ["camera preview never activates a real camera"]
        if not opt_in_present:
            blocked.append("explicit camera opt-in is required")
        if not visible_indicator_ready:
            blocked.append("visible camera indicator is required")
        if sensitive:
            blocked.append("sensitive camera capability is disabled and requires strong approval")
        return CameraPreviewDecision(
            opt_in_present=opt_in_present,
            approval_required=True,
            strong_approval_required=sensitive,
            visible_indicator_ready=visible_indicator_ready,
            blocked_reasons=blocked,
        )

    def preview_stop(self, phrase: str) -> CameraControlState:
        matched = str(phrase or "").strip().casefold() == "no mires"
        return CameraControlState(
            last_session_summary="camera stop preview accepted" if matched else "camera stop phrase not recognized",
            blocked_reasons=[] if matched else ["stop phrase was not recognized"],
        )
