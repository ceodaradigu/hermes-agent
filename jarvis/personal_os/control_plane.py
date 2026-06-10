from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from jarvis.approval_audit import redact_sensitive_data


@dataclass(frozen=True)
class StopControls:
    global_pause: bool = False
    memory_activation_paused: bool = False
    scheduler_paused: bool = False
    routines_paused: bool = False
    personal_os_paused: bool = False
    external_sources_paused: bool = True
    tool_invocations_paused: bool = True
    reason: str = ""
    updated_at: str = ""
    prepare_only: bool = True
    would_execute: bool = False

    def __post_init__(self) -> None:
        safe_reason, _ = redact_sensitive_data(self.reason)
        object.__setattr__(self, "reason", _clean_text(safe_reason)[:240])
        object.__setattr__(self, "updated_at", self.updated_at or datetime.now(timezone.utc).isoformat())
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "would_execute", False)

    @property
    def memory_blocked(self) -> bool:
        return self.global_pause or self.memory_activation_paused or self.personal_os_paused

    @property
    def scheduler_blocked(self) -> bool:
        return self.global_pause or self.scheduler_paused or self.personal_os_paused

    @property
    def routines_blocked(self) -> bool:
        return self.global_pause or self.routines_paused or self.scheduler_paused or self.personal_os_paused

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data.update(
            memory_blocked=self.memory_blocked,
            scheduler_blocked=self.scheduler_blocked,
            routines_blocked=self.routines_blocked,
        )
        return data


@dataclass(frozen=True)
class PersonalOSState:
    personal_os_available: bool = True
    active_mode: str = "manual"
    focus_mode: str = "off"
    daily_priorities: List[str] = field(default_factory=list)
    weekly_priorities: List[str] = field(default_factory=list)
    routines: List[Dict[str, Any]] = field(default_factory=list)
    reminders: List[Dict[str, Any]] = field(default_factory=list)
    review_queue: List[Dict[str, Any]] = field(default_factory=list)
    stop_controls: StopControls = field(default_factory=StopControls)
    authorized_sources: List[str] = field(default_factory=list)
    blocked_sources: List[str] = field(default_factory=list)
    external_sources_enabled: bool = False
    private_sources_enabled: bool = False
    execution_enabled: bool = False
    side_effects_enabled: bool = False
    autoload_enabled: bool = False
    scheduler_enabled: bool = False
    watcher_enabled: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    prepare_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "personal_os_available", True)
        object.__setattr__(self, "active_mode", _clean_text(self.active_mode) or "manual")
        object.__setattr__(self, "focus_mode", _clean_text(self.focus_mode) or "off")
        for name in ("daily_priorities", "weekly_priorities", "authorized_sources", "blocked_sources", "blocked_reasons"):
            object.__setattr__(self, name, _safe_list(getattr(self, name)))
        for name in ("routines", "reminders", "review_queue"):
            safe, _ = redact_sensitive_data(list(getattr(self, name) or []))
            object.__setattr__(self, name, safe)
        if isinstance(self.stop_controls, dict):
            object.__setattr__(self, "stop_controls", StopControls(**self.stop_controls))
        for name in (
            "external_sources_enabled",
            "private_sources_enabled",
            "execution_enabled",
            "side_effects_enabled",
            "autoload_enabled",
            "scheduler_enabled",
            "watcher_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "prepare_only", True)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["stop_controls"] = self.stop_controls.to_dict()
        return data


class PersonalOSControlPlane:
    def status(self) -> Dict[str, Any]:
        return {
            **PersonalOSState().to_dict(),
            "personal_os_control_plane_available": True,
            "daily_review_preview_available": True,
            "weekly_review_preview_available": True,
            "stop_controls_available": True,
            "calendar_reading_enabled": False,
            "email_reading_enabled": False,
            "document_reading_enabled": False,
            "local_file_scanning_enabled": False,
            "notifications_enabled": False,
        }

    def policy(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "personal_os_control_plane_available": True,
            "no_autoload": True,
            "no_execution": True,
            "no_side_effects": True,
            "no_watchers": True,
            "no_external_sources_by_default": True,
            "no_private_sources_by_default": True,
            "source_approval_required": True,
            "strong_approval_required_for_private_sources": True,
            "memory_is_not_permission": True,
            "scheduler_due_is_not_execution": True,
        }

    def preview_state(self, **values: Any) -> PersonalOSState:
        return PersonalOSState(**values)


def _safe_list(values: List[Any]) -> List[str]:
    safe, _ = redact_sensitive_data(list(values or []))
    return [_clean_text(value) for value in safe if _clean_text(value)]


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())
