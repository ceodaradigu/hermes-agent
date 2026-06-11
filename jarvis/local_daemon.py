from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class LocalDaemonStatus:
    current_mark: str = "Mark 2"
    mark_2_macro: str = "Mark 2 Macro 1"
    local_daemon_available: bool = True
    local_daemon_enabled: bool = False
    local_daemon_running: bool = False
    auto_start_enabled: bool = False
    install_as_service_enabled: bool = False
    system_service_installation_supported: bool = False
    daemon_pid: Optional[int] = None
    daemon_lock_present: bool = False
    healthcheck_available: bool = True
    safe_shutdown_available: bool = True
    kill_switch_available: bool = True
    stop_phrase_available: bool = True
    local_only: bool = True
    external_network_enabled: bool = False
    secrets_access_enabled: bool = False
    filesystem_external_write_enabled: bool = False
    approval_required_for_sensitive_actions: bool = True
    restrictions_are_approval_gates: bool = True
    wake_phrase_is_permission: bool = False
    voice_can_approve: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LocalDaemonCommandPreview:
    command: str
    preview_only: bool = True
    would_start_process: bool = False
    would_access_microphone: bool = False
    would_modify_system_service: bool = False
    would_write_outside_repo: bool = False
    approval_required: bool = False
    strong_approval_required: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    next_safe_step: str = "Review the preview and keep the local runtime disabled."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LocalDaemonControl:
    COMMANDS = {
        "daemon_status",
        "daemon_start_preview",
        "daemon_stop_preview",
        "daemon_kill_switch_preview",
        "wake_listener_enable_preview",
        "wake_listener_disable_preview",
        "voice_approval_enable_preview",
        "voice_approval_disable_preview",
        "runtime_healthcheck",
        "runtime_state_transition_preview",
    }

    def status(self) -> Dict[str, Any]:
        return LocalDaemonStatus().to_dict()

    def preview_command(self, command: str = "daemon_status") -> LocalDaemonCommandPreview:
        normalized = str(command or "daemon_status").strip().lower()
        if normalized not in self.COMMANDS:
            return LocalDaemonCommandPreview(
                command=normalized,
                blocked_reasons=["unsupported local daemon preview command"],
                next_safe_step="Choose a supported preview command.",
            )
        sensitive = normalized in {"daemon_start_preview", "wake_listener_enable_preview", "voice_approval_enable_preview"}
        return LocalDaemonCommandPreview(
            command=normalized,
            approval_required=sensitive,
            strong_approval_required=normalized == "wake_listener_enable_preview",
            blocked_reasons=["preview does not start processes, sensors, services, or execution"] if sensitive else [],
            next_safe_step="Obtain explicit local approval and implement a future reviewed runtime path." if sensitive else "Inspect status only.",
        )

