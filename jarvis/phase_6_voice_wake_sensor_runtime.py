from __future__ import annotations

import hashlib
import importlib.util
import math
import os
import re
import shutil
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
from uuid import uuid4

from jarvis.sensor_ledger import SensorLedger
from jarvis.wake_voice_runtime import WakeVoiceRuntime, normalize_confidence


PHASE_6_SCHEMA_VERSION = "jarvis.phase_6_voice_wake_memory_sensor_runtime.v1"
VOICE_PROVIDER_REGISTRY_SCHEMA_VERSION = "jarvis.voice_provider_registry.v1"
VOICE_SESSION_MANAGER_V2_SCHEMA_VERSION = "jarvis.voice_session_manager.v2"
WAKE_RUNTIME_OPT_IN_SCHEMA_VERSION = "jarvis.wake_runtime_opt_in.v1"
SENSOR_RUNTIME_OPT_IN_SCHEMA_VERSION = "jarvis.sensor_runtime_opt_in.v1"

VOICE_SESSION_V2_STATES: Tuple[str, ...] = (
    "idle",
    "listening",
    "transcribing",
    "thinking",
    "speaking",
    "awaiting_approval",
    "awaiting_spoken_challenge",
    "cancelled",
    "error",
)

SENSOR_RUNTIME_TYPES: Tuple[str, ...] = (
    "microphone",
    "camera",
    "screen_context",
    "audio_recording",
    "video_recording",
    "wake",
)

SECRET_TRANSCRIPT_MARKERS = (
    ".env",
    "api key",
    "api_key",
    "authorization:",
    "bearer ",
    "cookie",
    "credential",
    "password",
    "private key",
    "secret",
    "sk-",
    "token",
)


@dataclass(frozen=True)
class VoiceProviderConfig:
    """Explicit manual pilot config. Defaults never enable local providers."""

    allow_local_stt: bool = False
    allow_local_tts: bool = False
    allow_local_vad: bool = False
    allow_wake_provider: bool = False
    allow_wyoming: bool = False
    faster_whisper_model_path: Optional[str] = None
    whisper_cpp_binary: Optional[str] = None
    whisper_cpp_model_path: Optional[str] = None
    piper_binary: Optional[str] = None
    piper_voice_path: Optional[str] = None
    wyoming_url: str = "tcp://127.0.0.1:10300"

    @classmethod
    def from_environment(cls) -> "VoiceProviderConfig":
        """Read non-secret local pilot toggles without installing or probing devices."""

        return cls(
            allow_local_stt=_env_bool("JARVIS_ALLOW_LOCAL_STT"),
            allow_local_tts=_env_bool("JARVIS_ALLOW_LOCAL_TTS"),
            allow_local_vad=_env_bool("JARVIS_ALLOW_LOCAL_VAD"),
            allow_wake_provider=_env_bool("JARVIS_ALLOW_WAKE_PROVIDER"),
            allow_wyoming=_env_bool("JARVIS_ALLOW_WYOMING"),
            faster_whisper_model_path=os.environ.get("JARVIS_FASTER_WHISPER_MODEL_PATH") or None,
            whisper_cpp_binary=os.environ.get("JARVIS_WHISPER_CPP_BINARY") or None,
            whisper_cpp_model_path=os.environ.get("JARVIS_WHISPER_CPP_MODEL_PATH") or None,
            piper_binary=os.environ.get("JARVIS_PIPER_BINARY") or None,
            piper_voice_path=os.environ.get("JARVIS_PIPER_VOICE_PATH") or None,
            wyoming_url=os.environ.get("JARVIS_WYOMING_URL") or "tcp://127.0.0.1:10300",
        )


@dataclass(frozen=True)
class VoiceProviderStatus:
    provider_id: str
    capability: str
    display_name: str
    mode: str
    status: str
    installed: bool | str = False
    detected: bool | str = False
    enabled: bool = False
    ready: bool = False
    local_only: bool = True
    browser_client_side: bool = False
    requires_model: bool = False
    model_path_configured: bool = False
    model_available: bool = False
    binary_path: Optional[str] = None
    network_required: bool = False
    external_provider: bool = False
    raw_audio_persistence: bool = False
    hidden_sensor_activation: bool = False
    continuous_transcription: bool = False
    model_download_performed: bool = False
    provider_install_performed: bool = False
    unavailable_reason: str = ""
    license: str = "not_bundled"
    adopted: str = "status_contract_only"

    def __post_init__(self) -> None:
        computed_ready = bool(
            self.enabled
            and self.detected is True
            and (not self.requires_model or self.model_available)
            and not self.network_required
            and not self.external_provider
        )
        object.__setattr__(self, "ready", computed_ready)
        object.__setattr__(self, "network_required", False)
        object.__setattr__(self, "external_provider", False)
        object.__setattr__(self, "raw_audio_persistence", False)
        object.__setattr__(self, "hidden_sensor_activation", False)
        object.__setattr__(self, "continuous_transcription", False)
        object.__setattr__(self, "model_download_performed", False)
        object.__setattr__(self, "provider_install_performed", False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VoiceProviderRegistry:
    """Honest local provider diagnostics. It never opens audio devices."""

    def __init__(self, config: Optional[VoiceProviderConfig] = None) -> None:
        self.config = config or VoiceProviderConfig.from_environment()

    def status(self) -> Dict[str, Any]:
        providers = self._providers()
        by_capability: Dict[str, List[Dict[str, Any]]] = {}
        for provider in providers:
            by_capability.setdefault(provider.capability, []).append(provider.to_dict())
        ready = [provider.provider_id for provider in providers if provider.ready]
        missing_or_disabled = [
            provider.provider_id
            for provider in providers
            if provider.status in {"missing", "disabled_by_default", "client_side_unknown", "configured_model_missing"}
        ]
        return {
            "schema_version": VOICE_PROVIDER_REGISTRY_SCHEMA_VERSION,
            "state": {
                "mode": "honest_local_provider_diagnostics",
                "local_only_default": True,
                "backend_opens_microphone": False,
                "backend_speaks_audio": False,
                "model_download_performed": False,
                "provider_install_performed": False,
                "external_api_calls_enabled": False,
                "hidden_microphone": False,
            },
            "providers": {provider.provider_id: provider.to_dict() for provider in providers},
            "providers_by_capability": by_capability,
            "diagnostics": {
                "ready_provider_ids": ready,
                "ready_provider_count": len(ready),
                "missing_or_disabled_provider_ids": missing_or_disabled,
                "browser_fallback_status": "client_side_unknown_until_browser_checks",
                "no_fake_provider_success": True,
                "manual_pilot_hooks_available": True,
                "manual_pilot_hooks_enabled": any(
                    (
                        self.config.allow_local_stt,
                        self.config.allow_local_tts,
                        self.config.allow_local_vad,
                        self.config.allow_wake_provider,
                        self.config.allow_wyoming,
                    )
                ),
            },
            "safety": {
                "no_hidden_microphone": True,
                "no_hidden_speaker": True,
                "no_continuous_transcription": True,
                "no_raw_audio_storage": True,
                "no_model_download": True,
                "no_dependency_install": True,
                "no_external_api_default": True,
                "wake_phrase_can_approve": False,
            },
            "source_endpoint": "/mark-3/voice-providers/status",
            "metadata_only": True,
            "read_only": True,
        }

    def _providers(self) -> List[VoiceProviderStatus]:
        faster_whisper_installed = _module_available("faster_whisper")
        faster_model_available = _path_exists(self.config.faster_whisper_model_path)
        whisper_binary = self.config.whisper_cpp_binary or _which(("whisper-cli", "whisper-cpp", "whisper.cpp"))
        whisper_detected = bool(whisper_binary)
        whisper_model_available = _path_exists(self.config.whisper_cpp_model_path)
        piper_binary = self.config.piper_binary or _which(("piper",))
        piper_detected = bool(piper_binary) or _module_available("piper") or _module_available("piper_tts")
        piper_voice_available = _path_exists(self.config.piper_voice_path)
        silero_detected = _module_available("silero_vad") or _module_available("torch")
        openwakeword_detected = _module_available("openwakeword")
        wyoming_detected = _module_available("wyoming")

        return [
            VoiceProviderStatus(
                provider_id="browser_speech_recognition",
                capability="stt",
                display_name="Browser Web Speech STT",
                mode="browser_manual_push_to_talk",
                status="client_side_unknown",
                installed="client_side_unknown",
                detected="client_side_unknown",
                enabled=False,
                ready=False,
                local_only=False,
                browser_client_side=True,
                unavailable_reason="Backend cannot detect window.SpeechRecognition; browser checks it after a user gesture.",
                license="browser_api",
                adopted="browser_fallback_contract",
            ),
            VoiceProviderStatus(
                provider_id="browser_speech_synthesis",
                capability="tts",
                display_name="Browser SpeechSynthesis TTS",
                mode="browser_manual_tts",
                status="client_side_unknown",
                installed="client_side_unknown",
                detected="client_side_unknown",
                enabled=False,
                ready=False,
                local_only=False,
                browser_client_side=True,
                unavailable_reason="Backend cannot detect speechSynthesis voices; browser checks it without server audio.",
                license="browser_api",
                adopted="browser_fallback_contract",
            ),
            self._local_provider(
                provider_id="faster_whisper",
                capability="stt",
                display_name="faster-whisper",
                mode="local_stt_manual_file_or_buffer_future",
                detected=faster_whisper_installed,
                enabled=self.config.allow_local_stt,
                requires_model=True,
                model_available=faster_model_available,
                model_path_configured=bool(self.config.faster_whisper_model_path),
                unavailable_missing="faster-whisper is not installed; no install or model download performed.",
                unavailable_disabled="faster-whisper detected but disabled by default.",
                unavailable_model="faster-whisper enabled but model path is missing or unavailable.",
                license="MIT",
                adopted="manual_pilot_hook_only",
            ),
            self._local_provider(
                provider_id="whisper_cpp",
                capability="stt",
                display_name="whisper.cpp",
                mode="local_stt_binary_manual_file_future",
                detected=whisper_detected,
                enabled=self.config.allow_local_stt,
                requires_model=True,
                model_available=whisper_model_available,
                model_path_configured=bool(self.config.whisper_cpp_model_path),
                binary_path=whisper_binary,
                unavailable_missing="whisper.cpp binary not detected; no build, install, or model download performed.",
                unavailable_disabled="whisper.cpp binary detected but disabled by default.",
                unavailable_model="whisper.cpp enabled but model path is missing or unavailable.",
                license="MIT",
                adopted="manual_pilot_hook_only",
            ),
            self._local_provider(
                provider_id="silero_vad",
                capability="vad",
                display_name="Silero VAD",
                mode="local_vad_future_short_window",
                detected=silero_detected,
                enabled=self.config.allow_local_vad,
                requires_model=False,
                model_available=True,
                unavailable_missing="Silero VAD/torch not detected; no install performed.",
                unavailable_disabled="Silero VAD dependency detected but disabled by default.",
                unavailable_model="",
                license="MIT",
                adopted="manual_pilot_hook_only",
            ),
            self._local_provider(
                provider_id="openwakeword",
                capability="wake",
                display_name="openWakeWord",
                mode="local_wake_future_small_buffer",
                detected=openwakeword_detected,
                enabled=self.config.allow_wake_provider,
                requires_model=False,
                model_available=True,
                unavailable_missing="openWakeWord not detected; manual text fixture wake runtime remains available.",
                unavailable_disabled="openWakeWord detected but wake provider is disabled by default.",
                unavailable_model="",
                license="Apache-2.0",
                adopted="manual_pilot_hook_only",
            ),
            self._local_provider(
                provider_id="piper",
                capability="tts",
                display_name="Piper",
                mode="local_tts_binary_manual_future",
                detected=piper_detected,
                enabled=self.config.allow_local_tts,
                requires_model=True,
                model_available=piper_voice_available,
                model_path_configured=bool(self.config.piper_voice_path),
                binary_path=piper_binary,
                unavailable_missing="Piper not detected; no install or voice/model download performed.",
                unavailable_disabled="Piper detected but disabled by default.",
                unavailable_model="Piper enabled but voice/model path is missing or unavailable.",
                license="license_review_required_gpl3_surface_inspected",
                adopted="manual_pilot_hook_only",
            ),
            self._local_provider(
                provider_id="wyoming",
                capability="protocol",
                display_name="Wyoming protocol",
                mode="local_loopback_protocol_future",
                detected=wyoming_detected,
                enabled=self.config.allow_wyoming,
                requires_model=False,
                model_available=True,
                unavailable_missing="Wyoming Python package not detected; no service connection attempted.",
                unavailable_disabled="Wyoming detected but protocol adapter disabled by default.",
                unavailable_model="",
                license="MIT",
                adopted="manual_pilot_hook_only",
            ),
        ]

    def _local_provider(
        self,
        *,
        provider_id: str,
        capability: str,
        display_name: str,
        mode: str,
        detected: bool,
        enabled: bool,
        requires_model: bool,
        model_available: bool,
        unavailable_missing: str,
        unavailable_disabled: str,
        unavailable_model: str,
        model_path_configured: bool = False,
        binary_path: Optional[str] = None,
        license: str,
        adopted: str,
    ) -> VoiceProviderStatus:
        if not detected:
            status = "missing"
            reason = unavailable_missing
        elif not enabled:
            status = "disabled_by_default"
            reason = unavailable_disabled
        elif requires_model and not model_available:
            status = "configured_model_missing"
            reason = unavailable_model
        else:
            status = "ready_manual_pilot"
            reason = "Provider is locally detected and explicitly enabled; caller must still provide explicit sensor/audio input."
        return VoiceProviderStatus(
            provider_id=provider_id,
            capability=capability,
            display_name=display_name,
            mode=mode,
            status=status,
            installed=detected,
            detected=detected,
            enabled=bool(enabled),
            requires_model=requires_model,
            model_path_configured=model_path_configured,
            model_available=bool(model_available),
            binary_path=binary_path,
            unavailable_reason=reason,
            license=license,
            adopted=adopted,
        )


@dataclass(frozen=True)
class VoiceSessionV2:
    session_id: str
    state: str
    activation: str
    source: str
    created_at: str
    last_activity_at: str
    expires_at: str
    device_id: str = ""
    opened_by_wake_phrase: bool = False
    wake_phrase: Optional[str] = None
    approval_id: Optional[str] = None
    challenge_id: Optional[str] = None
    transcript_summary: Dict[str, Any] = field(default_factory=dict)
    voice_event_metadata: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    timed_out: bool = False
    cancel_reason: str = ""
    raw_audio_stored: bool = False
    transcript_stored: bool = False
    raw_audio_sent_to_backend: bool = False
    wake_phrase_can_approve: bool = False
    hermes_dispatch_allowed: bool = False

    def __post_init__(self) -> None:
        if self.state not in VOICE_SESSION_V2_STATES:
            raise ValueError(f"unsupported voice session state: {self.state}")
        for name in (
            "raw_audio_stored",
            "transcript_stored",
            "raw_audio_sent_to_backend",
            "wake_phrase_can_approve",
            "hermes_dispatch_allowed",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "transcript_summary", dict(self.transcript_summary))
        object.__setattr__(self, "voice_event_metadata", _safe_metadata(self.voice_event_metadata))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VoiceSessionManagerV2:
    """In-memory lifecycle manager for manual/local voice sessions."""

    def __init__(self, *, clock: Any = None, default_timeout_seconds: int = 90) -> None:
        self.clock = clock or _now_iso
        self.default_timeout_seconds = max(5, min(int(default_timeout_seconds), 600))
        self._lock = RLock()
        self._sessions: Dict[str, VoiceSessionV2] = {}
        self._events: List[Dict[str, Any]] = []

    def status(self) -> Dict[str, Any]:
        with self._lock:
            self._expire_overdue_locked()
            active = [session.to_dict() for session in self._sessions.values() if session.active]
            latest = next(reversed(self._sessions.values()), None) if self._sessions else None
            return {
                "schema_version": VOICE_SESSION_MANAGER_V2_SCHEMA_VERSION,
                "state": {
                    "current_state": latest.state if latest else "idle",
                    "active": bool(active),
                    "active_session_count": len(active),
                    "manual_push_to_talk_supported": True,
                    "wake_can_start_session": True,
                    "awaiting_approval_supported": True,
                    "awaiting_spoken_challenge_supported": True,
                    "timeout_seconds": self.default_timeout_seconds,
                },
                "supported_states": list(VOICE_SESSION_V2_STATES),
                "active_sessions": active,
                "latest_session": latest.to_dict() if latest else None,
                "recent_events": list(self._events[-25:]),
                "privacy": {
                    "raw_audio_stored": False,
                    "transcript_stored": False,
                    "raw_audio_sent_to_backend": False,
                    "full_transcript_in_events": False,
                    "metadata_only_events": True,
                    "no_raw_audio_by_default": True,
                },
                "controls": {
                    "can_interrupt": True,
                    "can_cancel": True,
                    "stop_global_supported": True,
                    "session_timeout_supported": True,
                },
                "approval": {
                    "active_voice_session_required": True,
                    "wake_phrase_alone_never_approves": True,
                    "voice_cannot_downgrade_risk": True,
                },
                "source_endpoint": "/mark-3/voice-session-v2/status",
                "metadata_only": True,
                "read_only": True,
            }

    def start_manual(
        self,
        *,
        device_id: str = "",
        source: str = "manual_push_to_talk",
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        return self._start(
            activation="manual_push_to_talk",
            source=source,
            device_id=device_id,
            opened_by_wake_phrase=False,
            wake_phrase=None,
            timeout_seconds=timeout_seconds,
        )

    def start_from_wake(
        self,
        *,
        transcript: str,
        matched_phrase: str,
        confidence: float,
        source: str = "wake_runtime_fixture",
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        session = self._start(
            activation="wake_phrase",
            source=source,
            opened_by_wake_phrase=True,
            wake_phrase=matched_phrase,
            timeout_seconds=timeout_seconds,
            extra_metadata={"wake_confidence": normalize_confidence(confidence)},
        )
        self.transition(session["session"]["session_id"], "listening", transcript=transcript, reason="wake phrase opened session")
        return session

    def transition(
        self,
        session_id: str,
        state: str,
        *,
        transcript: str = "",
        approval_id: Optional[str] = None,
        challenge_id: Optional[str] = None,
        reason: str = "state transition",
    ) -> Dict[str, Any]:
        if state not in VOICE_SESSION_V2_STATES:
            raise ValueError(f"unsupported voice session state: {state}")
        with self._lock:
            session = self._require_session(session_id)
            active = state not in {"cancelled", "error"}
            updated = replace(
                session,
                state=state,
                last_activity_at=self.clock(),
                active=active,
                approval_id=approval_id if approval_id is not None else session.approval_id,
                challenge_id=challenge_id if challenge_id is not None else session.challenge_id,
                transcript_summary=_transcript_summary(transcript) if transcript else session.transcript_summary,
            )
            self._sessions[session_id] = updated
            event = self._event_locked(
                "voice_session_transitioned",
                session_id=session_id,
                state=state,
                metadata={"reason": reason, "approval_id": approval_id or "", "challenge_id": challenge_id or ""},
            )
            return {"session": updated.to_dict(), "event": event, "metadata_only": True}

    def await_approval(
        self,
        session_id: str,
        *,
        approval_id: str,
        challenge_id: str = "",
        strong_challenge_required: bool = False,
    ) -> Dict[str, Any]:
        state = "awaiting_spoken_challenge" if strong_challenge_required else "awaiting_approval"
        return self.transition(
            session_id,
            state,
            approval_id=approval_id,
            challenge_id=challenge_id,
            reason="approval handoff",
        )

    def cancel(self, session_id: str, *, reason: str = "operator cancel") -> Dict[str, Any]:
        with self._lock:
            session = self._require_session(session_id)
            updated = replace(session, state="cancelled", active=False, cancel_reason=_safe_text(reason), last_activity_at=self.clock())
            self._sessions[session_id] = updated
            event = self._event_locked("voice_session_cancelled", session_id=session_id, state="cancelled", metadata={"reason": reason})
            return {"session": updated.to_dict(), "event": event, "metadata_only": True}

    def stop_global(self, *, reason: str = "operator stop global") -> Dict[str, Any]:
        stopped: List[str] = []
        with self._lock:
            for session_id, session in list(self._sessions.items()):
                if session.active:
                    self._sessions[session_id] = replace(
                        session,
                        state="cancelled",
                        active=False,
                        cancel_reason=_safe_text(reason),
                        last_activity_at=self.clock(),
                    )
                    stopped.append(session_id)
            event = self._event_locked("voice_session_stop_global", state="cancelled", metadata={"reason": reason, "stopped_count": len(stopped)})
            return {"stopped_session_ids": stopped, "event": event, "metadata_only": True}

    def is_active(self, session_id: str) -> bool:
        with self._lock:
            self._expire_overdue_locked()
            session = self._sessions.get(session_id)
            return bool(session and session.active and session.state not in {"cancelled", "error"})

    def _start(
        self,
        *,
        activation: str,
        source: str,
        device_id: str = "",
        opened_by_wake_phrase: bool,
        wake_phrase: Optional[str],
        timeout_seconds: Optional[int],
        extra_metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = self.clock()
        duration = max(5, min(int(timeout_seconds or self.default_timeout_seconds), 600))
        session = VoiceSessionV2(
            session_id=f"voice-session-{uuid4()}",
            state="listening",
            activation=activation,
            source=_safe_text(source),
            device_id=_safe_text(device_id),
            opened_by_wake_phrase=opened_by_wake_phrase,
            wake_phrase=wake_phrase,
            created_at=now,
            last_activity_at=now,
            expires_at=_after_seconds(duration, now=now),
            voice_event_metadata={
                "operator_gesture_required": activation == "manual_push_to_talk",
                "wake_phrase_starts_session_only": opened_by_wake_phrase,
                "no_raw_audio_storage": True,
                **dict(extra_metadata or {}),
            },
        )
        with self._lock:
            self._sessions[session.session_id] = session
            event = self._event_locked(
                "voice_session_started",
                session_id=session.session_id,
                state=session.state,
                metadata={"activation": activation, "source": source, "opened_by_wake_phrase": opened_by_wake_phrase},
            )
            return {"session": session.to_dict(), "event": event, "metadata_only": True}

    def _require_session(self, session_id: str) -> VoiceSessionV2:
        session = self._sessions.get(session_id)
        if not session:
            raise KeyError(session_id)
        return session

    def _expire_overdue_locked(self) -> None:
        now = _parse_time(self.clock())
        for session_id, session in list(self._sessions.items()):
            if session.active and now >= _parse_time(session.expires_at):
                self._sessions[session_id] = replace(
                    session,
                    state="cancelled",
                    active=False,
                    timed_out=True,
                    cancel_reason="session_timeout",
                    last_activity_at=self.clock(),
                )
                self._event_locked("voice_session_timed_out", session_id=session_id, state="cancelled", metadata={"reason": "session_timeout"})

    def _event_locked(
        self,
        event_type: str,
        *,
        session_id: str = "",
        state: str = "idle",
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        event = {
            "schema_version": VOICE_SESSION_MANAGER_V2_SCHEMA_VERSION,
            "event_id": f"voice-session-event-{uuid4()}",
            "event_type": event_type,
            "session_id": _safe_text(session_id),
            "state": state,
            "created_at": self.clock(),
            "metadata": _safe_metadata(metadata or {}),
            "raw_audio_included": False,
            "raw_transcript_included": False,
            "metadata_only": True,
        }
        self._events.append(event)
        if len(self._events) > 100:
            self._events = self._events[-100:]
        return dict(event)


class WakeRuntimeOptIn:
    """Manual/test wake runtime pilot. No real microphone is opened."""

    def __init__(
        self,
        *,
        session_manager: VoiceSessionManagerV2,
        provider_registry: Optional[VoiceProviderRegistry] = None,
        wake_runtime: Optional[WakeVoiceRuntime] = None,
        clock: Any = None,
    ) -> None:
        self.session_manager = session_manager
        self.provider_registry = provider_registry or VoiceProviderRegistry()
        self.wake_runtime = wake_runtime or WakeVoiceRuntime()
        self.clock = clock or _now_iso
        self._lock = RLock()
        self._enabled = False
        self._phrase = "hola jarvis"
        self._visible_indicator = False
        self._last_event: Optional[Dict[str, Any]] = None

    def status(self) -> Dict[str, Any]:
        provider = self.provider_registry.status()["providers"].get("openwakeword", {})
        return {
            "schema_version": WAKE_RUNTIME_OPT_IN_SCHEMA_VERSION,
            "state": {
                "mode": "manual_fixture_wake_runtime_opt_in",
                "enabled": self._enabled,
                "configured_phrase": self._phrase,
                "default_phrase": "hola jarvis",
                "visible_indicator": self._visible_indicator,
                "local_only": True,
                "continuous_transcription": False,
                "small_in_memory_buffer_only": True,
                "raw_audio_storage": False,
                "auto_start": False,
            },
            "provider": provider,
            "last_event": self._last_event,
            "rules": {
                "wake_starts_session": True,
                "wake_phrase_can_approve": False,
                "wake_phrase_can_execute": False,
                "no_continuous_transcription_by_default": True,
                "stop_cancel_supported": True,
            },
            "source_endpoint": "/mark-3/wake-runtime/status",
            "metadata_only": True,
            "read_only": True,
        }

    def configure(self, *, enabled: bool, phrase: str = "", actor: str = "David", reason: str = "operator opt-in") -> Dict[str, Any]:
        with self._lock:
            self._enabled = bool(enabled)
            clean_phrase = _normalize_phrase(phrase or self._phrase or "hola jarvis")
            self._phrase = clean_phrase if clean_phrase else "hola jarvis"
            self._visible_indicator = bool(enabled)
            self._last_event = {
                "event_id": f"wake-event-{uuid4()}",
                "event_type": "wake_runtime_opt_in_changed",
                "created_at": self.clock(),
                "enabled": self._enabled,
                "actor": _safe_text(actor),
                "reason": _safe_text(reason),
                "metadata_only": True,
            }
            return {"status": self.status(), "event": dict(self._last_event)}

    def handle_fixture_transcript(self, *, transcript: str, confidence: float = 1.0) -> Dict[str, Any]:
        confidence = normalize_confidence(confidence)
        if not self._enabled:
            return {
                "schema_version": WAKE_RUNTIME_OPT_IN_SCHEMA_VERSION,
                "wake_detected": False,
                "session_started": False,
                "reason": "wake_runtime_not_opted_in",
                "approval_granted": False,
                "would_execute": False,
                "metadata_only": True,
            }
        parsed = self.wake_runtime.parse(transcript, confidence=confidence)
        manual_phrase_matched = False
        manual_command = ""
        normalized_transcript = _normalize_phrase(transcript)
        if not parsed.wake_phrase_detected and normalized_transcript.startswith(self._phrase):
            manual_phrase_matched = True
            manual_command = normalized_transcript[len(self._phrase) :].strip(" ,;:.!?")
        if not parsed.wake_phrase_detected:
            if manual_phrase_matched and confidence >= self.wake_runtime.config.confidence_threshold:
                session = self.session_manager.start_from_wake(
                    transcript=transcript,
                    matched_phrase=self._phrase,
                    confidence=confidence,
                )
                self._last_event = {
                    "event_id": f"wake-event-{uuid4()}",
                    "event_type": "wake_phrase_detected_session_started",
                    "created_at": self.clock(),
                    "session_id": session["session"]["session_id"],
                    "matched_phrase": self._phrase,
                    "confidence": confidence,
                    "approval_granted": False,
                    "metadata_only": True,
                }
                return {
                    "wake_phrase_detected": True,
                    "matched_phrase": self._phrase,
                    "extracted_command": manual_command,
                    "confidence": confidence,
                    "should_open_session": True,
                    "should_answer": True,
                    "low_confidence": False,
                    "blocked_reasons": [],
                    "prepare_only": True,
                    "wake_phrase_is_not_permission": True,
                    "execution_enabled": False,
                    "side_effects_enabled": False,
                    "session_started": True,
                    "session": session["session"],
                    "approval_granted": False,
                    "would_execute": False,
                    "wake_phrase_can_approve": False,
                    "metadata_only": True,
                }
            return {
                **parsed.to_dict(),
                "session_started": False,
                "approval_granted": False,
                "would_execute": False,
                "metadata_only": True,
            }
        if parsed.low_confidence:
            return {
                **parsed.to_dict(),
                "session_started": False,
                "approval_granted": False,
                "would_execute": False,
                "metadata_only": True,
            }
        session = self.session_manager.start_from_wake(
            transcript=transcript,
            matched_phrase=parsed.matched_phrase or self._phrase,
            confidence=confidence,
        )
        self._last_event = {
            "event_id": f"wake-event-{uuid4()}",
            "event_type": "wake_phrase_detected_session_started",
            "created_at": self.clock(),
            "session_id": session["session"]["session_id"],
            "matched_phrase": parsed.matched_phrase,
            "confidence": confidence,
            "approval_granted": False,
            "metadata_only": True,
        }
        return {
            **parsed.to_dict(),
            "session_started": True,
            "session": session["session"],
            "approval_granted": False,
            "would_execute": False,
            "wake_phrase_can_approve": False,
            "metadata_only": True,
        }

    def stop(self, *, reason: str = "operator stop") -> Dict[str, Any]:
        with self._lock:
            self._enabled = False
            self._visible_indicator = False
            self._last_event = {
                "event_id": f"wake-event-{uuid4()}",
                "event_type": "wake_runtime_stopped",
                "created_at": self.clock(),
                "reason": _safe_text(reason),
                "metadata_only": True,
            }
            return {"status": self.status(), "event": dict(self._last_event)}


class SensorRuntimeOptIn:
    """Metadata-only sensor opt-in control plane."""

    def __init__(self, *, ledger: Optional[SensorLedger] = None, clock: Any = None) -> None:
        self.ledger = ledger or SensorLedger()
        self.clock = clock or _now_iso
        self._lock = RLock()
        self._states: Dict[str, Dict[str, Any]] = {
            sensor_type: {
                "sensor_type": sensor_type,
                "opted_in": False,
                "active": False,
                "recording_active": False,
                "visible_indicator": False,
                "local_retention": "none",
                "last_event_at": None,
            }
            for sensor_type in SENSOR_RUNTIME_TYPES
        }

    def status(self) -> Dict[str, Any]:
        with self._lock:
            active = [item for item in self._states.values() if item["active"]]
            return {
                "schema_version": SENSOR_RUNTIME_OPT_IN_SCHEMA_VERSION,
                "state": {
                    "mode": "metadata_only_sensor_runtime_opt_in",
                    "active_sensor_count": len(active),
                    "recording_active": any(item["recording_active"] for item in self._states.values()),
                    "defaults_off": True,
                    "local_only": True,
                    "visible_indicator_required": True,
                    "stop_cancel_supported": True,
                    "delete_clear_supported": True,
                },
                "sensors": {key: dict(value) for key, value in self._states.items()},
                "retention": {
                    "raw_audio_storage_default": False,
                    "raw_video_storage_default": False,
                    "screen_context_storage_default": False,
                    "local_retention_only": True,
                    "cloud_upload": False,
                },
                "safety": {
                    "no_hidden_microphone": True,
                    "no_hidden_camera": True,
                    "no_biometric_identification": True,
                    "no_recording_by_default": True,
                    "no_cloud_upload": True,
                    "metadata_only_audit_default": True,
                },
                "recent_events": self.ledger.events(limit=25),
                "source_endpoint": "/mark-3/sensor-runtime/status",
                "metadata_only": True,
                "read_only": True,
            }

    def set_opt_in(self, *, sensor_type: str, enabled: bool, actor: str = "David", reason: str = "operator opt-in") -> Dict[str, Any]:
        sensor_type = _sensor_choice(sensor_type)
        with self._lock:
            state = dict(self._states[sensor_type])
            state.update({
                "opted_in": bool(enabled),
                "visible_indicator": bool(enabled and state.get("active")),
                "last_event_at": self.clock(),
            })
            if not enabled:
                state.update({"active": False, "recording_active": False, "visible_indicator": False})
            self._states[sensor_type] = state
            event = self.ledger.record(
                sensor_type=_ledger_sensor_type(sensor_type),
                event_type="requested" if enabled else "cancelled",
                source="/mark-3/sensor-runtime/opt-in",
                metadata={"sensor_type": sensor_type, "enabled": enabled, "actor": actor, "reason": reason},
                created_at=self.clock(),
            )
            return {"sensor": dict(state), "event": event, "metadata_only": True}

    def start(self, *, sensor_type: str, recording: bool = False, actor: str = "David", reason: str = "operator start") -> Dict[str, Any]:
        sensor_type = _sensor_choice(sensor_type)
        with self._lock:
            state = dict(self._states[sensor_type])
            if not state["opted_in"]:
                raise ValueError("sensor opt-in required before start")
            if recording and sensor_type not in {"audio_recording", "video_recording"}:
                raise ValueError("recording can only be active on recording sensor types")
            state.update({
                "active": True,
                "recording_active": bool(recording),
                "visible_indicator": True,
                "local_retention": "browser_or_local_memory_until_delete" if recording else "none",
                "last_event_at": self.clock(),
            })
            self._states[sensor_type] = state
            event = self.ledger.record(
                sensor_type=_ledger_sensor_type(sensor_type),
                event_type="started",
                source="/mark-3/sensor-runtime/start",
                metadata={"sensor_type": sensor_type, "recording": recording, "actor": actor, "reason": reason},
                created_at=self.clock(),
            )
            return {"sensor": dict(state), "event": event, "metadata_only": True}

    def stop(self, *, sensor_type: str = "all", reason: str = "operator stop") -> Dict[str, Any]:
        stopped: List[str] = []
        with self._lock:
            targets = list(self._states) if sensor_type == "all" else [_sensor_choice(sensor_type)]
            for target in targets:
                state = dict(self._states[target])
                if state["active"] or state["recording_active"]:
                    state.update({"active": False, "recording_active": False, "visible_indicator": False, "last_event_at": self.clock()})
                    self._states[target] = state
                    stopped.append(target)
                    self.ledger.record(
                        sensor_type=_ledger_sensor_type(target),
                        event_type="stopped",
                        source="/mark-3/sensor-runtime/stop",
                        metadata={"sensor_type": target, "reason": reason},
                        created_at=self.clock(),
                    )
            return {"stopped_sensor_types": stopped, "metadata_only": True, "status": self.status()}

    def delete_local_retention(self, *, sensor_type: str, actor: str = "David", reason: str = "operator delete") -> Dict[str, Any]:
        sensor_type = _sensor_choice(sensor_type)
        with self._lock:
            state = dict(self._states[sensor_type])
            state.update({"local_retention": "none", "recording_active": False, "last_event_at": self.clock()})
            self._states[sensor_type] = state
            event = self.ledger.record(
                sensor_type=_ledger_sensor_type(sensor_type),
                event_type="deleted",
                source="/mark-3/sensor-runtime/delete",
                metadata={"sensor_type": sensor_type, "actor": actor, "reason": reason},
                created_at=self.clock(),
            )
            return {"sensor": dict(state), "event": event, "metadata_only": True}


class Phase6VoiceWakeMemorySensorRuntime:
    """Aggregate Phase 6 pilot contracts without duplicating Hermes execution."""

    def __init__(
        self,
        *,
        provider_registry: Optional[VoiceProviderRegistry] = None,
        voice_session_manager: Optional[VoiceSessionManagerV2] = None,
        wake_runtime: Optional[WakeRuntimeOptIn] = None,
        sensor_runtime: Optional[SensorRuntimeOptIn] = None,
        memory_brain_v3: Any = None,
    ) -> None:
        self.provider_registry = provider_registry or VoiceProviderRegistry()
        self.voice_session_manager = voice_session_manager or VoiceSessionManagerV2()
        self.wake_runtime = wake_runtime or WakeRuntimeOptIn(
            session_manager=self.voice_session_manager,
            provider_registry=self.provider_registry,
        )
        self.sensor_runtime = sensor_runtime or SensorRuntimeOptIn()
        self.memory_brain_v3 = memory_brain_v3

    def status(self) -> Dict[str, Any]:
        provider_status = self.provider_registry.status()
        session_status = self.voice_session_manager.status()
        wake_status = self.wake_runtime.status()
        sensor_status = self.sensor_runtime.status()
        memory_status = self.memory_brain_v3.status() if self.memory_brain_v3 is not None else {}
        return {
            "schema_version": PHASE_6_SCHEMA_VERSION,
            "phase": "Phase 6",
            "title": "PR #171 -- Phase 6 Real Voice, Wake, Memory & Sensor Runtime",
            "status": "implemented_as_local_runtime_pilot_contracts",
            "implemented_blocks": {
                "voice_provider_registry_v1": True,
                "voice_session_manager_v2": True,
                "spoken_approval_v2_contract": True,
                "wake_runtime_opt_in_v1": True,
                "local_stt_tts_vad_readiness": True,
                "memory_brain_v3_contract": bool(memory_status),
                "sensor_runtime_opt_in_v1": True,
                "dashboard_event_stream_phase_6": True,
                "local_controller_stop_global_integration": True,
            },
            "real_vs_readiness": {
                "browser_stt_tts": "real browser APIs when manually activated by the user; backend reports client_side_unknown",
                "local_stt_tts_vad_wake": "honest readiness diagnostics and manual pilot hooks only; no models downloaded",
                "wake_runtime": "manual transcript fixture and opt-in state are real; openWakeWord engine not started by default",
                "voice_session_manager": "real in-memory lifecycle and timeout/cancel/stop metadata; no raw audio capture",
                "spoken_approval": "real governed text-transcript approval fixture over Phase 5 trusted identity; no raw audio stored",
                "memory_brain_v3": "safe runtime wrapper over Memory Brain v2 store; no autonomous permission effect",
                "sensor_runtime": "real opt-in/control metadata and ledger; browser/device capture remains manual UI/local only",
            },
            "voice_providers": provider_status,
            "voice_session_v2": session_status,
            "wake_runtime": wake_status,
            "sensor_runtime": sensor_status,
            "memory_brain_v3": memory_status,
            "local_controller_integration": {
                "stop_global_cancels_voice_wake_sensor": True,
                "local_controller_autostart": False,
                "trusted_device_required_for_spoken_approval": True,
            },
            "safety": {
                "jarvis_governs": True,
                "hermes_executes": True,
                "no_duplicate_hermes_runtime": True,
                "frontend_direct_hermes": False,
                "no_execute_endpoint": True,
                "no_hidden_microphone": True,
                "no_hidden_camera": True,
                "no_continuous_transcription_default": True,
                "no_raw_audio_video_storage_default": True,
                "no_cloud_upload": True,
                "wake_phrase_can_approve": False,
                "memory_grants_permission": False,
            },
            "source_endpoint": "/mark-3/phase-6/status",
            "metadata_only": True,
            "read_only": True,
        }

    def stop_global(self, *, reason: str = "operator stop global") -> Dict[str, Any]:
        voice = self.voice_session_manager.stop_global(reason=reason)
        wake = self.wake_runtime.stop(reason=reason)
        sensors = self.sensor_runtime.stop(sensor_type="all", reason=reason)
        return {
            "schema_version": PHASE_6_SCHEMA_VERSION,
            "status": "stopped",
            "voice": voice,
            "wake": wake,
            "sensors": sensors,
            "reason": _safe_text(reason),
            "metadata_only": True,
            "raw_audio_stored": False,
            "frames_stored": False,
        }


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _which(names: Iterable[str]) -> Optional[str]:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def _path_exists(value: Optional[str]) -> bool:
    if not value:
        return False
    try:
        path = Path(value).expanduser()
        return path.exists() and path.is_file()
    except (OSError, RuntimeError):
        return False


def _env_bool(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}


def _transcript_summary(text: str) -> Dict[str, Any]:
    normalized = " ".join(str(text or "").split())
    lowered = normalized.lower()
    return {
        "raw_text_included": False,
        "character_count": len(normalized),
        "word_count": len(normalized.split()) if normalized else 0,
        "text_hash": hashlib.sha256(normalized.casefold().encode("utf-8")).hexdigest()[:16] if normalized else "",
        "contains_sensitive_marker": any(marker in lowered for marker in SECRET_TRANSCRIPT_MARKERS),
        "redaction": "raw transcript omitted; metadata only",
    }


def _safe_metadata(values: Mapping[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in dict(values or {}).items():
        key_text = _safe_text(key, limit=80)
        lowered = key_text.lower()
        if any(marker in lowered for marker in ("audio", "raw", "transcript", "frame", "image", "video", "secret", "token", "password", "credential", "cookie")):
            safe[key_text] = "[redacted]"
        elif isinstance(value, Mapping):
            safe[key_text] = _safe_metadata(value)
        elif isinstance(value, (list, tuple)):
            safe[key_text] = [_safe_scalar(item) for item in value[:20]]
        else:
            safe[key_text] = _safe_scalar(value)
    return safe


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return 0.0
        return value
    return _safe_text(value, limit=300)


def _safe_text(value: Any, default: str = "", *, limit: int = 240) -> str:
    text = " ".join(str(value if value is not None else default).strip().split())
    return (text or default)[:limit]


def _sensor_choice(sensor_type: str) -> str:
    normalized = _safe_text(sensor_type, "unknown").lower()
    if normalized not in SENSOR_RUNTIME_TYPES:
        raise ValueError(f"unsupported sensor type: {sensor_type}")
    return normalized


def _ledger_sensor_type(sensor_type: str) -> str:
    return {
        "microphone": "voice_session",
        "camera": "camera",
        "screen_context": "camera",
        "audio_recording": "recording",
        "video_recording": "recording",
        "wake": "wake",
    }[sensor_type]


def _normalize_phrase(value: str) -> str:
    text = str(value or "").strip().casefold()
    text = re.sub(r"\s+", " ", text)
    return text or "hola jarvis"


def _after_seconds(seconds: int, *, now: Optional[str] = None) -> str:
    current = _parse_time(now) if now else datetime.now(timezone.utc)
    return (current + timedelta(seconds=seconds)).isoformat()


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
