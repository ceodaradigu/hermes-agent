from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


RUNTIME_MODES = {"disabled", "standby", "listening", "processing", "awaiting_approval", "executing", "stopped"}


@dataclass(frozen=True)
class DesktopRuntimeState:
    desktop_runtime_available: bool = True
    runtime_mode: str = "disabled"
    visible_status_required: bool = True
    current_visible_status: str = "JARVIS local runtime disabled"
    last_transition: Optional[str] = None
    active_session_id: Optional[str] = None
    local_user: str = "David"
    microphone_state: str = "opt_in_required"
    speaker_state: str = "available"
    kill_switch_state: str = "available"
    stop_phrase_state: str = "available"
    approval_channel_state: str = "disabled"
    safety_lock_state: str = "locked"
    pending_action_summary: Optional[str] = None
    pending_risk_summary: Optional[str] = None
    no_background_execution_without_state: bool = True
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.runtime_mode not in RUNTIME_MODES:
            raise ValueError("unsupported desktop runtime mode")
        if self.runtime_mode == "listening" and (not self.visible_status_required or not self.current_visible_status.strip()):
            raise ValueError("listening requires a visible status")
        object.__setattr__(self, "execution_enabled", False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DesktopRuntime:
    def __init__(self, *, owner_name: str = "David") -> None:
        self.owner_name = str(owner_name or "David").strip() or "David"

    def status(self) -> DesktopRuntimeState:
        return DesktopRuntimeState(local_user=self.owner_name)

    def preview_transition(
        self,
        mode: str,
        *,
        visible_status: Optional[str] = None,
        valid_voice_approval_present: bool = False,
        critical_action: bool = False,
        current_mode: str = "disabled",
    ) -> DesktopRuntimeState:
        mode = str(mode or "").strip().lower()
        current_mode = str(current_mode or "").strip().lower()
        if critical_action and mode == "executing" and (
            current_mode != "awaiting_approval" or not valid_voice_approval_present
        ):
            raise ValueError("critical execution preview requires awaiting_approval state and a valid approval")
        return DesktopRuntimeState(
            runtime_mode=mode,
            current_visible_status=visible_status or f"JARVIS runtime preview: {mode}",
            last_transition=datetime.now(timezone.utc).isoformat(),
            local_user=self.owner_name,
            approval_channel_state="valid_preview" if valid_voice_approval_present else "disabled",
            safety_lock_state="locked",
        )
