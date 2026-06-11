from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.approval_hardening import RiskLevel, StrongApprovalPolicy
from jarvis.policy.policy_engine import PolicyDecision, PolicyEngine
from jarvis.wake_voice_runtime import WakeVoiceRuntime, normalize_confidence


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
