from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Dict

from jarvis.policy.policy_engine import PolicyDecision, PolicyEngine
from jarvis.voice.intent_router import VoiceIntentRouter


_CONTROL_POLICY_REASON = "Voice Companion controls are policy placeholders only."
_PREVIEW_REASON = "Voice Companion preview is prepare-only; no execution path is enabled."
_REDACTED_TRANSCRIPT = "[redacted sensitive transcript]"
_SENSITIVE_MARKERS = (
    ".env",
    "api key",
    "apikey",
    "authorization",
    "banco",
    "bearer",
    "clave",
    "client secret",
    "contraseña",
    "credencial",
    "credenciales",
    "credential",
    "credentials",
    "dni",
    "password",
    "private key",
    "secreto",
    "secret",
    "tarjeta",
    "token",
)
_SENSITIVE_PATTERN = re.compile(
    r"(\.env|api\s*key|apikey|authorization|banco|bearer|clave|client\s+secret|contrase(?:ñ|n)a|credenciales?|credentials?|dni|password|private\s+key|secret|secreto|tarjeta|token)",
    re.IGNORECASE,
)


class VoiceCompanionPreviewIntent(str, Enum):
    CREATE_MISSION = "create_mission"
    CREATE_ASSET = "create_asset"
    REQUIRES_APPROVAL = "requires_approval"
    DENIED = "denied"
    UNKNOWN = "unknown"


class VoiceCompanionPreviewPolicyDecision(str, Enum):
    ALLOWED = "allowed"
    REQUIRES_APPROVAL = "requires_approval"
    DENIED = "denied"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class VoiceCompanionControlPolicy:
    """Prepare-only policy for future Voice Companion controls.

    This DTO records the desired control posture without activating any
    microphone, wake-word, recording, streaming, execution, Hermes, or approval
    runtime.
    """

    prepare_only: bool = True
    microphone_requested: bool = False
    wake_word_requested: bool = False
    recording_requested: bool = False
    streaming_requested: bool = False
    auto_start_requested: bool = False
    execution_requested: bool = False
    requires_approval_for_activation: bool = True
    activation_enabled: bool = False
    reason: str = _CONTROL_POLICY_REASON

    @classmethod
    def placeholder(cls) -> "VoiceCompanionControlPolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None) -> "VoiceCompanionControlPolicy":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": self.prepare_only,
            "microphone_requested": self.microphone_requested,
            "wake_word_requested": self.wake_word_requested,
            "recording_requested": self.recording_requested,
            "streaming_requested": self.streaming_requested,
            "auto_start_requested": self.auto_start_requested,
            "execution_requested": self.execution_requested,
            "requires_approval_for_activation": self.requires_approval_for_activation,
            "activation_enabled": self.activation_enabled,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class VoiceCompanionStatus:
    """Prepare-only status for the future Voice Companion surface.

    This DTO intentionally has no runtime dependencies and never touches
    microphones, wake-word engines, audio streams, Hermes, or approvals.
    """

    prepare_only: bool = True
    voice_available: bool = False
    microphone_enabled: bool = False
    wake_word_enabled: bool = False
    recording_enabled: bool = False
    streaming_enabled: bool = False
    auto_start_enabled: bool = False
    execution_enabled: bool = False
    approval_required_for_sensitive_actions: bool = True

    @classmethod
    def placeholder(cls) -> "VoiceCompanionStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None) -> "VoiceCompanionStatus":
        return cls(
            prepare_only=True,
            voice_available=False,
            microphone_enabled=False,
            wake_word_enabled=False,
            recording_enabled=False,
            streaming_enabled=False,
            auto_start_enabled=False,
            execution_enabled=False,
            approval_required_for_sensitive_actions=True,
        )

    def to_dict(self) -> Dict[str, bool]:
        return {
            "prepare_only": self.prepare_only,
            "voice_available": self.voice_available,
            "microphone_enabled": self.microphone_enabled,
            "wake_word_enabled": self.wake_word_enabled,
            "recording_enabled": self.recording_enabled,
            "streaming_enabled": self.streaming_enabled,
            "auto_start_enabled": self.auto_start_enabled,
            "execution_enabled": self.execution_enabled,
            "approval_required_for_sensitive_actions": self.approval_required_for_sensitive_actions,
        }


@dataclass(frozen=True)
class VoiceCompanionIntentPreview:
    """Prepare-only intent preview for simulated Voice Companion transcripts.

    This DTO never represents a runnable command. Deserialization is
    intentionally conservative so caller-provided data cannot enable execution,
    mark Hermes as called, or mark a real approval as created.
    """

    prepare_only: bool = True
    input_text: str = ""
    intent: VoiceCompanionPreviewIntent = VoiceCompanionPreviewIntent.UNKNOWN
    policy_decision: VoiceCompanionPreviewPolicyDecision = VoiceCompanionPreviewPolicyDecision.UNKNOWN
    would_execute: bool = False
    execution_enabled: bool = False
    approval_created: bool = False
    approval_gateway_called: bool = False
    hermes_called: bool = False
    sensitive_boundary_triggered: bool = False
    redact_input_text: bool = False
    reason: str = _PREVIEW_REASON
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        redact_input_text = bool(self.redact_input_text or self.sensitive_boundary_triggered)
        object.__setattr__(
            self,
            "input_text",
            _sanitize_preview_text(self.input_text, force_redact=redact_input_text),
        )
        object.__setattr__(self, "intent", _coerce_enum(VoiceCompanionPreviewIntent, self.intent))
        object.__setattr__(
            self,
            "policy_decision",
            _coerce_enum(VoiceCompanionPreviewPolicyDecision, self.policy_decision),
        )
        object.__setattr__(self, "would_execute", False)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "approval_created", False)
        object.__setattr__(self, "approval_gateway_called", False)
        object.__setattr__(self, "hermes_called", False)
        object.__setattr__(self, "sensitive_boundary_triggered", bool(self.sensitive_boundary_triggered))
        object.__setattr__(self, "redact_input_text", redact_input_text)
        object.__setattr__(self, "reason", _safe_reason(self.reason))
        object.__setattr__(self, "warnings", [_safe_reason(item) for item in list(self.warnings or [])])

    @classmethod
    def placeholder(cls) -> "VoiceCompanionIntentPreview":
        return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any] | None) -> "VoiceCompanionIntentPreview":
        source = dict(data or {})
        return cls(
            input_text=str(source.get("input_text", "")),
            intent=source.get("intent", VoiceCompanionPreviewIntent.UNKNOWN),
            policy_decision=source.get("policy_decision", VoiceCompanionPreviewPolicyDecision.UNKNOWN),
            sensitive_boundary_triggered=bool(source.get("sensitive_boundary_triggered", False)),
            redact_input_text=bool(source.get("redact_input_text", False)),
            reason=str(source.get("reason", _PREVIEW_REASON)),
            warnings=[str(item) for item in source.get("warnings", []) or []],
        )

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        policy_engine: PolicyEngine | None = None,
        intent_router: VoiceIntentRouter | None = None,
    ) -> "VoiceCompanionIntentPreview":
        raw_text = str(text or "").strip()
        router = intent_router or VoiceIntentRouter()
        engine = policy_engine or PolicyEngine()

        routed_intent = router.classify(raw_text)
        policy_result = engine.classify_action(raw_text)
        sensitive_boundary = _contains_sensitive_marker(raw_text) or bool(
            (routed_intent.user_context_signals or {}).get("sensitive_boundary", False)
        )

        if policy_result.decision == PolicyDecision.DENIED:
            intent = VoiceCompanionPreviewIntent.DENIED
            decision = VoiceCompanionPreviewPolicyDecision.DENIED
        elif (
            policy_result.decision == PolicyDecision.REQUIRES_APPROVAL
            or routed_intent.approval_required
            or routed_intent.intent == "requires_approval"
            or sensitive_boundary
        ):
            intent = VoiceCompanionPreviewIntent.REQUIRES_APPROVAL
            decision = VoiceCompanionPreviewPolicyDecision.REQUIRES_APPROVAL
        else:
            intent = _preview_intent_from_router(routed_intent.intent)
            decision = VoiceCompanionPreviewPolicyDecision.ALLOWED

        warnings = []
        if sensitive_boundary:
            warnings.append("Sensitive boundary detected; transcript redacted and execution remains disabled.")
        if routed_intent.needs_clarification:
            warnings.append("Intent needs clarification before any future action.")

        return cls(
            input_text=raw_text,
            intent=intent,
            policy_decision=decision,
            sensitive_boundary_triggered=sensitive_boundary,
            redact_input_text=sensitive_boundary,
            reason=_preview_reason(policy_result.decision, routed_intent.reason),
            warnings=warnings,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": self.prepare_only,
            "input_text": self.input_text,
            "intent": self.intent.value,
            "policy_decision": self.policy_decision.value,
            "would_execute": self.would_execute,
            "execution_enabled": self.execution_enabled,
            "approval_created": self.approval_created,
            "approval_gateway_called": self.approval_gateway_called,
            "hermes_called": self.hermes_called,
            "sensitive_boundary_triggered": self.sensitive_boundary_triggered,
            "reason": self.reason,
            "warnings": list(self.warnings or []),
        }


def _preview_intent_from_router(intent: str) -> VoiceCompanionPreviewIntent:
    if intent == "create_mission":
        return VoiceCompanionPreviewIntent.CREATE_MISSION
    if intent == "create_asset":
        return VoiceCompanionPreviewIntent.CREATE_ASSET
    return VoiceCompanionPreviewIntent.UNKNOWN


def _preview_reason(policy_decision: PolicyDecision, routed_reason: str) -> str:
    if policy_decision == PolicyDecision.DENIED:
        return "Policy preview denied this transcript; nothing was executed."
    if policy_decision == PolicyDecision.REQUIRES_APPROVAL:
        return "Policy preview requires human approval before any future execution."
    return _safe_reason(routed_reason or _PREVIEW_REASON)


def _sanitize_preview_text(text: str, *, force_redact: bool = False) -> str:
    value = " ".join(str(text or "").strip().split())
    if not value:
        return ""
    if force_redact or _contains_sensitive_marker(value):
        return _REDACTED_TRANSCRIPT
    return value


def _contains_sensitive_marker(text: str) -> bool:
    value = str(text or "")
    lowered = value.lower()
    return any(marker in lowered for marker in _SENSITIVE_MARKERS) or bool(_SENSITIVE_PATTERN.search(value))


def _safe_reason(text: str) -> str:
    value = " ".join(str(text or "").strip().split())
    if not value:
        return _PREVIEW_REASON
    if _contains_sensitive_marker(value):
        return "Sensitive preview details were redacted; execution remains disabled."
    return value


def _coerce_enum(enum_cls: Any, value: Any) -> Any:
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except ValueError:
        return enum_cls.UNKNOWN
