from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from jarvis.approval_hardening import RiskLevel, StrongApprovalPolicy
from jarvis.policy.policy_engine import PolicyDecision, PolicyEngine
from jarvis.wake_voice_runtime import WakeVoiceRuntime, normalize_confidence


VOICE_SESSION_STATES: Tuple[str, ...] = (
    "idle",
    "wake_listening_available",
    "wake_listening_disabled",
    "conversation_active",
    "listening",
    "transcribing",
    "thinking",
    "speaking",
    "approval_required",
    "awaiting_approval",
    "awaiting_spoken_challenge",
    "cancelled",
    "stopped",
    "error",
)

VOICE_SESSION_SCHEMA_VERSION = "jarvis.voice_session_manager.v1"
DEFAULT_SUPPORTED_WAKE_PHRASES = ["Hola Jarvis", "Jarvis"]
DEFAULT_STOP_PHRASES = ["para", "cancela", "detente", "silencio", "cancelar misión", "apaga escucha"]


@dataclass(frozen=True)
class VoiceSessionReadModel:
    schema_version: str = VOICE_SESSION_SCHEMA_VERSION
    current_state: str = "idle"
    wake_listening_state: str = "wake_listening_disabled"
    supported_states: List[str] = field(default_factory=lambda: list(VOICE_SESSION_STATES))
    state: Dict[str, Any] = field(default_factory=dict)
    separation: Dict[str, Any] = field(default_factory=dict)
    privacy: Dict[str, Any] = field(default_factory=dict)
    approval_policy: Dict[str, Any] = field(default_factory=dict)
    safety: Dict[str, Any] = field(default_factory=dict)
    wake_architecture: Dict[str, Any] = field(default_factory=dict)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    source_endpoint: str = "/voice-runtime/session-status"
    source_endpoints: List[str] = field(default_factory=lambda: ["/voice-runtime/session-status", "/mark-2/wake-listener/status"])
    preview_only: bool = True
    read_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "supported_states", list(self.supported_states))
        object.__setattr__(self, "timeline", list(self.timeline))
        object.__setattr__(self, "preview_only", True)
        object.__setattr__(self, "read_only", True)

    def validate(self) -> None:
        missing = [state for state in VOICE_SESSION_STATES if state not in self.supported_states]
        if missing:
            raise ValueError(f"voice session read model missing states: {missing}")
        if self.current_state not in self.supported_states:
            raise ValueError(f"unsupported voice session current_state: {self.current_state}")
        if self.wake_listening_state not in {"wake_listening_available", "wake_listening_disabled"}:
            raise ValueError("wake_listening_state must distinguish available vs disabled")
        if self.separation.get("hermes_execution", {}).get("dispatch_allowed") is not False:
            raise ValueError("Hermes dispatch must be false in voice session read model")
        if self.privacy.get("raw_audio_sent_to_backend") is not False:
            raise ValueError("raw audio backend upload must be false")
        if self.privacy.get("transcript_persistence") is not False:
            raise ValueError("transcript persistence must default false")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class VoiceSessionState:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    state: str = "disabled"
    opened_by_wake_phrase: bool = False
    current_transcript: str = ""
    extracted_command: str = ""
    should_answer: bool = False
    response_preview: str = ""
    answer_mode: str = "text"
    local_processing_only: bool = True
    audio_retention_enabled: bool = False
    external_processing_enabled: bool = False
    action_allowed: bool = False
    approval_required: bool = False
    strong_approval_required: bool = False
    execution_enabled: bool = False
    side_effects_enabled: bool = False
    stopped_by_phrase: Optional[str] = None
    audit_events: List[Dict[str, Any]] = field(default_factory=list)
    blocked_reasons: List[str] = field(default_factory=list)
    prepare_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "local_processing_only", True)
        object.__setattr__(self, "audio_retention_enabled", False)
        object.__setattr__(self, "external_processing_enabled", False)
        object.__setattr__(self, "action_allowed", False)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "side_effects_enabled", False)
        object.__setattr__(self, "audit_events", list(self.audit_events))
        object.__setattr__(self, "blocked_reasons", list(self.blocked_reasons))
        object.__setattr__(self, "prepare_only", True)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VoiceCommandDecision:
    command: str
    intent_preview: str
    risk_level: RiskLevel = RiskLevel.MEDIUM
    action_allowed: bool = False
    approval_required: bool = False
    strong_approval_required: bool = False
    controlled_runtime_required: bool = False
    tool_gate_required: bool = False
    would_execute: bool = False
    would_call_tools: bool = False
    would_call_external: bool = False
    would_record_audio: bool = False
    response_preview: str = ""
    blocked_reasons: List[str] = field(default_factory=list)
    execution_enabled: bool = False
    side_effects_enabled: bool = False
    prepare_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_level", RiskLevel(self.risk_level))
        object.__setattr__(self, "action_allowed", False)
        for name in (
            "would_execute",
            "would_call_tools",
            "would_call_external",
            "would_record_audio",
            "execution_enabled",
            "side_effects_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "blocked_reasons", list(self.blocked_reasons))
        object.__setattr__(self, "prepare_only", True)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        return data


class VoiceSessionControl:
    """Prepare-only session and command decisions with policy classification."""

    def __init__(self, *, wake_runtime: Optional[WakeVoiceRuntime] = None, policy_engine: Optional[PolicyEngine] = None) -> None:
        self.wake_runtime = wake_runtime or WakeVoiceRuntime()
        self.policy_engine = policy_engine or PolicyEngine()
        self.strong_policy = StrongApprovalPolicy()

    def status(self, *, wake_listener_status: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        wake_status = dict(wake_listener_status or {})
        dependency_installed = bool(wake_status.get("openwakeword_dependency_installed", False))
        wake_listening_state = "wake_listening_available" if dependency_installed else "wake_listening_disabled"
        supported_phrases = _safe_list(wake_status.get("supported_wake_phrases")) or DEFAULT_SUPPORTED_WAKE_PHRASES
        stop_phrases = _merge_unique(_safe_list(wake_status.get("stop_phrases")), DEFAULT_STOP_PHRASES)
        provider = str(wake_status.get("provider_adapter") or "openWakeWord")
        provider_ready = bool(wake_status.get("provider_adapter_ready", False))

        model = VoiceSessionReadModel(
            current_state="idle",
            wake_listening_state=wake_listening_state,
            state={
                "mode": "safe_read_only_control_plane",
                "current_state": "idle",
                "wake_listening_state": wake_listening_state,
                "conversation_active": False,
                "manual_push_to_talk_active": False,
                "listening": False,
                "transcribing": False,
                "thinking": False,
                "speaking": False,
                "approval_required": False,
                "awaiting_approval": False,
                "awaiting_spoken_challenge": False,
                "cancelled": False,
                "stopped": False,
                "error": False,
                "wake_available": dependency_installed,
                "wake_enabled": False,
                "auto_start": False,
                "activation_endpoint_enabled": False,
            },
            separation={
                "wake_listening": {
                    "available": dependency_installed,
                    "enabled": False,
                    "state_when_available": "wake_listening_available",
                    "state_when_disabled": "wake_listening_disabled",
                    "purpose": "activation_only",
                    "records_audio": False,
                    "transcribes": False,
                    "transcribes_full_conversation": False,
                    "approves": False,
                    "executes": False,
                    "opens_conversation_only_after_valid_activation_future": True,
                },
                "active_conversation": {
                    "enabled": False,
                    "state": "idle",
                    "activation": "manual_push_to_talk_future_or_browser_local_button",
                    "records_audio": False,
                    "transcript_persistence": False,
                    "approves": False,
                    "executes": False,
                    "requires_stop_cancel": True,
                },
                "manual_push_to_talk": {
                    "available_as_frontend_browser_flow": True,
                    "backend_starts_microphone": False,
                    "microphone_auto_start": False,
                    "operator_gesture_required": True,
                },
                "stt": {
                    "backend_enabled": False,
                    "browser_manual_only": True,
                    "always_on_stt": False,
                    "background_transcription": False,
                    "starts_after_valid_activation_only_future": True,
                },
                "tts": {
                    "backend_enabled": False,
                    "browser_speech_synthesis_preview_only": True,
                    "external_provider_called": False,
                    "can_speak_without_approval": False,
                },
                "raw_audio_recording": {
                    "backend_enabled": False,
                    "browser_local_opt_in_surface": True,
                    "auto_record": False,
                    "raw_audio_sent_to_backend": False,
                    "no_audio_persistence_backend": True,
                },
                "voice_approval": {
                    "enabled": False,
                    "disabled_unless_authenticated_gated_audited": True,
                    "requires_readback_when_sensitive": True,
                    "wake_phrase_can_approve": False,
                    "wake_phrase_can_execute": False,
                },
                "hermes_execution": {
                    "enabled": False,
                    "dispatch_allowed": False,
                    "frontend_or_voice_can_call_hermes_directly": False,
                    "future_requires_preview_approval_audit": True,
                },
            },
            privacy={
                "raw_audio_sent_to_backend": False,
                "transcript_persistence": False,
                "background_transcription": False,
                "always_on_stt": False,
                "microphone_auto_start": False,
                "raw_audio_recording": False,
                "audio_persistence": False,
                "audio_buffer_persistence": False,
                "external_stt": False,
                "external_tts": False,
                "memory_autosave": False,
            },
            approval_policy={
                "wake_phrase_cannot_approve": True,
                "wake_phrase_cannot_execute": True,
                "voice_approval_enabled": False,
                "voice_approval_disabled_unless_authenticated_gated_audited": True,
                "sensitive_voice_approval_requires_readback": True,
                "critical_voice_approval_requires_strong_confirmation": True,
                "approval_events_must_be_audited": True,
                "restrictions_are_approval_gates_not_permanent_bans": True,
            },
            safety={
                "read_only": True,
                "no_post_put_delete": True,
                "no_hermes_dispatch": True,
                "no_tool_call": True,
                "no_auto_execute": True,
                "wake_phrase_never_approves": True,
                "wake_phrase_never_executes": True,
                "no_microphone_auto_start": True,
                "no_always_on_stt": True,
                "no_background_transcription": True,
                "no_raw_audio_backend": True,
                "no_transcript_persistence_by_default": True,
                "stop_cancel_required": True,
            },
            wake_architecture={
                "provider_contract": provider,
                "provider_adapter_ready": provider_ready,
                "dependency_detection": {
                    "openwakeword_dependency_installed": dependency_installed,
                    "source": "python_importlib",
                    "honest_status": "available" if dependency_installed else "missing",
                },
                "supported_phrases": supported_phrases,
                "stop_phrases": stop_phrases,
                "auto_start": False,
                "activation_endpoint_enabled": False,
                "ephemeral_buffer_contract": {
                    "in_memory_only": True,
                    "persisted": False,
                    "sent_to_backend": False,
                    "cleared_after_activation_or_timeout": True,
                    "no_audio_retention": True,
                },
                "no_transcription_until_valid_activation": True,
                "no_approval": True,
                "no_execution": True,
                "visible_indicator_required": True,
                "stop_cancel_required": True,
                "implementation_status": wake_status.get("implementation_status", "adapter_contract_only"),
            },
            timeline=[
                {
                    "event": "Voice session manager read model generated",
                    "source": "/voice-runtime/session-status",
                    "status": "idle",
                    "read_only": True,
                },
                {
                    "event": "Wake listening availability separated from active conversation",
                    "source": "/voice-runtime/session-status",
                    "status": wake_listening_state,
                    "read_only": True,
                },
                {
                    "event": "Voice approval disabled unless authenticated gated audited",
                    "source": "/voice-runtime/session-status",
                    "status": "disabled",
                    "read_only": True,
                },
            ],
        )
        return model.to_dict()

    def preview_session(self, text: str, *, confidence: float = 1.0, answer_mode: str = "text") -> VoiceSessionState:
        parsed = self.wake_runtime.parse(text, confidence=confidence)
        decision = self.preview_command(parsed.extracted_command, confidence=confidence) if parsed.extracted_command else None
        return VoiceSessionState(
            state="active_session" if parsed.should_open_session else "disabled",
            opened_by_wake_phrase=parsed.wake_phrase_detected,
            current_transcript=str(text or ""),
            extracted_command=parsed.extracted_command,
            should_answer=parsed.should_answer,
            response_preview=(
                "Estoy escuchando."
                if parsed.should_answer and not parsed.extracted_command
                else "Orden recibida para procesamiento seguro."
                if parsed.should_answer
                else ""
            ),
            answer_mode=answer_mode if answer_mode in {"text", "voice", "both"} else "text",
            approval_required=decision.approval_required if decision else False,
            strong_approval_required=decision.strong_approval_required if decision else False,
            audit_events=[{"event": "wake_phrase_preview", "matched_phrase": parsed.matched_phrase}],
            blocked_reasons=parsed.blocked_reasons + (decision.blocked_reasons if decision else []),
        )

    def preview_command(self, command: str, *, confidence: float = 1.0) -> VoiceCommandDecision:
        command = str(command or "").strip()
        confidence = normalize_confidence(confidence)
        policy = self.policy_engine.classify_action(command)
        context = _command_context(command)
        risk, strong_required, _ = self.strong_policy.classify(context)
        approval_required = policy.decision != PolicyDecision.ALLOWED or strong_required
        low_confidence = confidence < self.wake_runtime.config.confidence_threshold
        blocked = ["voice wake phrase is not permission", "voice execution and tool calls are disabled"]
        if low_confidence:
            blocked.append("low confidence blocks command processing and sensitive actions")
        if approval_required:
            blocked.append("explicit approval is required for this command")
        if strong_required:
            blocked.append("strong approval is required for this command")
        return VoiceCommandDecision(
            command=command,
            intent_preview=policy.decision.value,
            risk_level=risk,
            approval_required=approval_required,
            strong_approval_required=strong_required,
            controlled_runtime_required=approval_required,
            tool_gate_required=approval_required,
            response_preview="Comando recibido para preview; no se ejecutará.",
            blocked_reasons=blocked,
        )

    def preview_stop(self, phrase: str) -> VoiceSessionState:
        normalized = str(phrase or "").strip().casefold()
        matched = next((item for item in self.wake_runtime.config.stop_phrases if normalized == item), None)
        return VoiceSessionState(
            state="stopped" if matched else "paused",
            stopped_by_phrase=matched,
            audit_events=[{"event": "voice_stop_preview", "matched_phrase": matched}],
            blocked_reasons=[] if matched else ["stop phrase was not recognized"],
        )


def _command_context(command: str) -> Dict[str, Any]:
    text = command.casefold()
    context: Dict[str, Any] = {"action_type": command}
    for name, markers in (
        ("production", ("producción", "produccion", "production")),
        ("deploy", ("despliega", "desplegar", "deploy")),
        ("payment", ("paga", "pago", "payment")),
        ("external_call", ("envía", "envia", "send", "mensaje", "email")),
        ("secret_access", (".env", "secreto", "token", "credencial")),
    ):
        if any(marker in text for marker in markers):
            context[name] = True
    return context


def _safe_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _merge_unique(primary: List[str], fallback: List[str]) -> List[str]:
    merged: List[str] = []
    for item in [*primary, *fallback]:
        if item not in merged:
            merged.append(item)
    return merged
