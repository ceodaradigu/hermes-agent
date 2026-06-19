from __future__ import annotations

import importlib.util
import shutil
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

from jarvis.phase_6_voice_wake_sensor_runtime import VoiceProviderRegistry


VOICE_RUNTIME_PACK_SCHEMA_VERSION = "jarvis.voice_runtime_pack.v1"
VOICE_RUNTIME_PACK_ID = "jarvis-local-manual-voice-runtime-pack"

VOICE_RUNTIME_STATES: Tuple[str, ...] = (
    "idle",
    "listening",
    "transcribing",
    "thinking",
    "speaking",
    "awaiting_approval",
    "awaiting_spoken_challenge",
    "cancelled",
    "stopped",
    "error",
    "approval_required",
    "wake_listening_available",
    "wake_listening_disabled",
)


@dataclass(frozen=True)
class STTProviderContract:
    provider_name: str
    mode: str
    installed: bool | str
    detected: bool | str
    enabled: bool = False
    requires_model: bool = False
    model_path: Optional[str] = None
    model_available: bool = False
    local_only: bool = True
    network_required: bool = False
    external_provider: bool = False
    raw_audio_persistence: bool = False
    status: str = "disabled"
    unavailable_reason: str = ""
    browser_client_side: bool = False
    detection_location: str = "backend_metadata_only"

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", False)
        object.__setattr__(self, "network_required", False)
        object.__setattr__(self, "external_provider", False)
        object.__setattr__(self, "raw_audio_persistence", False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TTSProviderContract:
    provider_name: str
    mode: str
    installed: bool | str
    detected: bool | str
    enabled: bool = False
    local_only: bool = True
    network_required: bool = False
    external_provider: bool = False
    voice_name: Optional[str] = None
    voice_quality: str = "unknown"
    status: str = "disabled"
    unavailable_reason: str = ""
    browser_client_side: bool = False
    detection_location: str = "backend_metadata_only"

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", False)
        object.__setattr__(self, "network_required", False)
        object.__setattr__(self, "external_provider", False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VoiceRuntimePackStatus:
    schema_version: str = VOICE_RUNTIME_PACK_SCHEMA_VERSION
    runtime_id: str = VOICE_RUNTIME_PACK_ID
    mode: str = "local_manual_browser_voice_control_plane"
    enabled: bool = True
    manual_push_to_talk_enabled: bool = True
    browser_stt_available: str = "client_side_unknown"
    browser_tts_available: str = "client_side_unknown"
    local_stt_provider_status: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    local_tts_provider_status: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    local_vad_provider_status: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    wake_provider_status: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    provider_availability_diagnostics: Dict[str, Any] = field(default_factory=dict)
    wake_runtime_status: Dict[str, Any] = field(default_factory=dict)
    active_session: Dict[str, Any] = field(default_factory=dict)
    last_transcript_summary: Dict[str, Any] = field(default_factory=dict)
    last_response_summary: Dict[str, Any] = field(default_factory=dict)
    current_state: str = "idle"
    supported_states: List[str] = field(default_factory=lambda: list(VOICE_RUNTIME_STATES))
    can_interrupt: bool = True
    can_cancel: bool = True
    raw_audio_sent_to_backend: bool = False
    transcript_persistence: bool = False
    voice_approval_enabled: bool = False
    wake_phrase_can_approve: bool = False
    wake_phrase_can_execute: bool = False
    hermes_dispatch_allowed: bool = False
    provider_architecture: Dict[str, Any] = field(default_factory=dict)
    transcript_lifecycle: Dict[str, Any] = field(default_factory=dict)
    tts_lifecycle: Dict[str, Any] = field(default_factory=dict)
    visual_state_mapping: Dict[str, str] = field(default_factory=dict)
    safety: Dict[str, bool] = field(default_factory=dict)
    source_endpoint: str = "/mark-3/voice-runtime/status"
    source_endpoints: List[str] = field(default_factory=lambda: ["/mark-3/voice-runtime/status", "/voice-runtime/session-status", "/mark-2/wake-listener/status"])
    preview_only: bool = False
    read_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "supported_states", list(self.supported_states))
        object.__setattr__(self, "enabled", True)
        object.__setattr__(self, "manual_push_to_talk_enabled", True)
        for name in (
            "raw_audio_sent_to_backend",
            "transcript_persistence",
            "voice_approval_enabled",
            "wake_phrase_can_approve",
            "wake_phrase_can_execute",
            "hermes_dispatch_allowed",
            "preview_only",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "read_only", True)

    def validate(self) -> None:
        missing = [state for state in VOICE_RUNTIME_STATES if state not in self.supported_states]
        if missing:
            raise ValueError(f"voice runtime pack missing states: {missing}")
        if self.current_state not in self.supported_states:
            raise ValueError(f"unsupported voice runtime state: {self.current_state}")
        if self.raw_audio_sent_to_backend is not False:
            raise ValueError("raw audio must not be sent to backend")
        if self.transcript_persistence is not False:
            raise ValueError("transcript persistence must default false")
        if self.voice_approval_enabled is not False:
            raise ValueError("voice approval must remain disabled")
        if self.wake_phrase_can_approve is not False or self.wake_phrase_can_execute is not False:
            raise ValueError("wake phrase must not approve or execute")
        if self.hermes_dispatch_allowed is not False:
            raise ValueError("Hermes dispatch must remain disabled")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)


class VoiceRuntimePack:
    """Read-only voice runtime pack for local/manual browser voice.

    This class reports contracts and optional dependency status only. It never
    imports heavy provider modules, opens microphones, stores raw audio, or
    dispatches Hermes.
    """

    def status(
        self,
        *,
        wake_listener_status: Optional[Mapping[str, Any]] = None,
        voice_session_status: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        wake = dict(wake_listener_status or {})
        session = dict(voice_session_status or {})
        dependency_installed = bool(wake.get("openwakeword_dependency_installed", False))
        wake_state = "wake_listening_available" if dependency_installed else "wake_listening_disabled"
        local_stt = _local_stt_provider_contracts()
        local_tts = _local_tts_provider_contracts()
        provider_registry = VoiceProviderRegistry().status()
        registry_providers = provider_registry.get("providers", {})
        local_vad = {
            key: value
            for key, value in registry_providers.items()
            if isinstance(value, Mapping) and value.get("capability") == "vad"
        }
        wake_providers = {
            key: value
            for key, value in registry_providers.items()
            if isinstance(value, Mapping) and value.get("capability") == "wake"
        }
        browser_stt = _browser_stt_contract()
        browser_tts = _browser_tts_contract()

        model = VoiceRuntimePackStatus(
            browser_stt_available="client_side_unknown",
            browser_tts_available="client_side_unknown",
            local_stt_provider_status=local_stt,
            local_tts_provider_status=local_tts,
            local_vad_provider_status=local_vad,
            wake_provider_status=wake_providers,
            provider_availability_diagnostics=provider_registry.get("diagnostics", {}),
            wake_runtime_status={
                "status": wake_state,
                "enabled": False,
                "available": dependency_installed,
                "provider_adapter": str(wake.get("provider_adapter") or "openWakeWord"),
                "provider_adapter_ready": bool(wake.get("provider_adapter_ready", False)),
                "openwakeword_dependency_installed": dependency_installed,
                "auto_start_enabled": False,
                "always_on_enabled": False,
                "wake_phrase_can_approve": False,
                "wake_phrase_can_execute": False,
                "raw_audio_persistence": False,
                "raw_audio_sent_to_backend": False,
                "transcribes_environment": False,
            },
            active_session={
                "active": False,
                "session_id": None,
                "state": session.get("state", {}).get("current_state", "idle") if isinstance(session.get("state"), Mapping) else "idle",
                "activation": "manual_push_to_talk_browser_only",
                "operator_gesture_required": True,
                "microphone_auto_start": False,
                "raw_audio_sent_to_backend": False,
                "transcript_persistence": False,
                "hermes_dispatch_allowed": False,
            },
            last_transcript_summary={
                "available": False,
                "raw_text_included": False,
                "persistence": False,
                "storage": "browser_state_only_until_cleared",
                "retention": "ephemeral",
            },
            last_response_summary={
                "available": False,
                "raw_text_included": False,
                "tts_queued": False,
                "browser_tts_only": True,
                "local_tts_provider_enabled": False,
            },
            current_state="idle",
            can_interrupt=True,
            can_cancel=True,
            provider_architecture={
                "stt_providers": {
                    "browser_speech_recognition": browser_stt,
                    **local_stt,
                },
                "tts_providers": {
                    "browser_speech_synthesis": browser_tts,
                    **local_tts,
                },
                "vad_providers": local_vad,
                "wake_providers": wake_providers,
                "provider_registry_schema": provider_registry.get("schema_version"),
                "no_provider_install_performed": True,
                "no_model_download_performed": True,
                "browser_detection_location": "client",
                "backend_detection_location": "safe_importlib_or_binary_metadata_only",
            },
            transcript_lifecycle={
                "interim_transcript": "browser_memory_only",
                "final_transcript": "browser_state_until_next_turn_or_cancel",
                "last_transcript_summary_only": True,
                "raw_audio_sent_to_backend": False,
                "transcript_persistence": False,
                "memory_autosave": False,
            },
            tts_lifecycle={
                "queue_supported_in_browser_loop": True,
                "cancel_supported": True,
                "interrupt_supported": True,
                "provider": "browser_speech_synthesis_if_available",
                "fallback": "visible_text_response",
                "local_tts_provider_enabled": False,
                "external_tts_provider_called": False,
            },
            visual_state_mapping={
                "idle": "calm_particle_sphere",
                "listening": "attentive_concentrated_particle_sphere",
                "transcribing": "ordered_reflow_particle_sphere",
                "thinking": "internal_turbulence_particle_sphere",
                "speaking": "radial_waves_and_spikes_particle_sphere",
                "cancelled": "calm_particle_sphere",
                "stopped": "calm_particle_sphere",
                "error": "error_particle_pattern",
                "approval_required": "warm_approval_channel",
                "wake_listening_available": "gated_wake_available_indicator",
                "wake_listening_disabled": "calm_particle_sphere",
            },
            safety={
                "read_only": True,
                "get_only_endpoint": True,
                "no_execute_route": True,
                "no_hermes_dispatch": True,
                "no_frontend_direct_hermes": True,
                "no_auto_microphone": True,
                "no_always_on_wake": True,
                "no_background_transcription": True,
                "no_raw_audio_backend": True,
                "no_raw_audio_persistence": True,
                "no_transcript_persistence": True,
                "no_voice_approval": True,
                "wake_phrase_never_approves": True,
                "wake_phrase_never_executes": True,
                "no_external_stt_provider": True,
                "no_external_tts_provider": True,
                "no_model_download": True,
                "no_dependency_install": True,
                "no_money": True,
                "no_deploy": True,
                "no_email": True,
                "no_credentials": True,
            },
        )
        return model.to_dict()


def _browser_stt_contract() -> Dict[str, Any]:
    return STTProviderContract(
        provider_name="browser_speech_recognition",
        mode="browser_client_side_manual_push_to_talk",
        installed="client_side_unknown",
        detected="client_side_unknown",
        requires_model=False,
        model_path=None,
        model_available=False,
        local_only=False,
        status="client_side_unknown",
        unavailable_reason="Backend cannot honestly detect Web Speech API support; /jarvis checks window.SpeechRecognition or window.webkitSpeechRecognition.",
        browser_client_side=True,
        detection_location="browser",
    ).to_dict()


def _browser_tts_contract() -> Dict[str, Any]:
    return TTSProviderContract(
        provider_name="browser_speech_synthesis",
        mode="browser_client_side_manual_tts",
        installed="client_side_unknown",
        detected="client_side_unknown",
        local_only=False,
        voice_name=None,
        voice_quality="browser_catalog_unknown_until_loaded",
        status="client_side_unknown",
        unavailable_reason="Backend cannot honestly detect browser speechSynthesis voices; /jarvis checks speechSynthesis and SpeechSynthesisUtterance.",
        browser_client_side=True,
        detection_location="browser",
    ).to_dict()


def _local_stt_provider_contracts() -> Dict[str, Dict[str, Any]]:
    faster_whisper_installed = _python_module_available("faster_whisper")
    whisper_cpp_detected = _any_binary_available(("whisper-cpp", "whisper-cli", "whisper.cpp"))
    return {
        "faster_whisper_disabled_or_missing": STTProviderContract(
            provider_name="faster_whisper_disabled_or_missing",
            mode="local_stt_future_provider_disabled",
            installed=faster_whisper_installed,
            detected=faster_whisper_installed,
            requires_model=True,
            model_path=None,
            model_available=False,
            status="disabled_by_default" if faster_whisper_installed else "missing",
            unavailable_reason=(
                "faster_whisper module detected but disabled in Phase 1; no model path configured."
                if faster_whisper_installed
                else "faster_whisper is not installed; no install or model download performed."
            ),
        ).to_dict(),
        "whisper_cpp_disabled_or_missing": STTProviderContract(
            provider_name="whisper_cpp_disabled_or_missing",
            mode="local_stt_future_binary_provider_disabled",
            installed=whisper_cpp_detected,
            detected=whisper_cpp_detected,
            requires_model=True,
            model_path=None,
            model_available=False,
            status="disabled_by_default" if whisper_cpp_detected else "missing",
            unavailable_reason=(
                "whisper.cpp binary detected but disabled in Phase 1; no model path configured."
                if whisper_cpp_detected
                else "whisper.cpp binary not detected; no build, install, or model download performed."
            ),
        ).to_dict(),
    }


def _local_tts_provider_contracts() -> Dict[str, Dict[str, Any]]:
    piper_detected = _python_module_available("piper") or _python_module_available("piper_tts") or _any_binary_available(("piper",))
    return {
        "piper_local_disabled_or_missing": TTSProviderContract(
            provider_name="piper_local_disabled_or_missing",
            mode="local_tts_future_provider_disabled",
            installed=piper_detected,
            detected=piper_detected,
            voice_name=None,
            voice_quality="model_or_voice_missing",
            status="disabled_by_default" if piper_detected else "missing",
            unavailable_reason=(
                "Piper detected but disabled in Phase 1; no voice/model path configured."
                if piper_detected
                else "Piper is not installed; no install or voice/model download performed."
            ),
        ).to_dict(),
    }


def _python_module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _any_binary_available(names: Tuple[str, ...]) -> bool:
    return any(shutil.which(name) is not None for name in names)
