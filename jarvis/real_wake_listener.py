from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from jarvis.voice_session_control import VoiceSessionControl


@dataclass(frozen=True)
class RealWakeListenerPlan:
    real_wake_listener_available: bool = True
    wake_listener_enabled: bool = False
    microphone_opt_in_present: bool = False
    supported_wake_phrases: List[str] = field(default_factory=lambda: ["Hola Jarvis", "Jarvis"])
    wake_phrase_is_permission: bool = False
    wake_phrase_starts_session: bool = True
    wake_phrase_plus_command_supported: bool = True
    stop_phrases: List[str] = field(
        default_factory=lambda: [
            "para",
            "cancela",
            "detente",
            "silencio",
            "cancelar misión",
            "apaga escucha",
            "no escuches",
            "stop",
        ]
    )
    noise_or_unclear_input_policy: str = "Do not approve or execute; request a clear repeat."
    false_positive_policy: str = "Close or ignore the preview session without granting permission."
    visible_listening_indicator_required: bool = True
    audit_wake_events: bool = True
    audio_recording_enabled: bool = False
    audio_streaming_enabled: bool = False
    external_speech_api_enabled: bool = False
    local_provider_required: bool = True
    provider_adapter: str = "openWakeWord"
    provider_adapter_ready: bool = False
    openwakeword_dependency_installed: bool = False
    auto_start_enabled: bool = False
    activation_endpoint_enabled: bool = False
    requires_operator_start: bool = True
    implementation_status: str = "adapter_contract_only"
    raw_audio_persistence_enabled: bool = False
    raw_audio_sent_to_backend: bool = False
    transcript_before_valid_activation_enabled: bool = False
    wake_phrase_can_approve: bool = False
    wake_phrase_can_execute: bool = False
    visible_indicator_required_in_ui: bool = True
    stop_cancel_required: bool = True
    ephemeral_buffer_contract: Dict[str, Any] = field(
        default_factory=lambda: {
            "in_memory_only": True,
            "persisted": False,
            "sent_to_backend": False,
            "transcribed_before_valid_activation": False,
            "cleared_after_activation_or_timeout": True,
            "no_audio_retention": True,
        }
    )
    test_plan: List[str] = field(
        default_factory=lambda: [
            "install openwakeword in the local runtime environment",
            "start adapter only from an explicit local daemon control",
            "verify wake events contain metadata only",
            "verify no raw audio is persisted or sent to providers",
            "verify wake phrase opens command window only and never approves or executes",
        ]
    )
    no_microphone_access_in_tests: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RealWakeListener:
    def __init__(self, *, session_control: VoiceSessionControl | None = None) -> None:
        self.session_control = session_control or VoiceSessionControl()

    def status(self) -> Dict[str, Any]:
        dependency_installed = importlib.util.find_spec("openwakeword") is not None
        return RealWakeListenerPlan(
            provider_adapter_ready=dependency_installed,
            openwakeword_dependency_installed=dependency_installed,
        ).to_dict()

    def preview_transcript(self, text: str, *, confidence: float = 1.0) -> Dict[str, Any]:
        session = self.session_control.preview_session(text, confidence=confidence).to_dict()
        command = session["extracted_command"]
        return {
            **session,
            "session_started": session["opened_by_wake_phrase"] and session["state"] == "active_session",
            "command_extracted": bool(command),
            "approval_granted": False,
            "approval_flow_started": bool(command and session["approval_required"]),
            "microphone_accessed": False,
            "would_execute": False,
        }
