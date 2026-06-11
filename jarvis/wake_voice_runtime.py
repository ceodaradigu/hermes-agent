from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
import re
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class WakePhraseConfig:
    enabled: bool = False
    local_only: bool = True
    wake_phrases: List[str] = field(default_factory=lambda: ["hola jarvis", "jarvis"])
    confidence_threshold: float = 0.80
    require_visible_indicator: bool = True
    no_audio_retention_by_default: bool = True
    external_audio_processing_enabled: bool = False
    background_listening_allowed: bool = False
    push_to_talk_fallback: bool = True
    stop_phrases: List[str] = field(
        default_factory=lambda: ["no escuches", "para", "cállate", "stop", "detente"]
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "enabled", False)
        object.__setattr__(self, "local_only", True)
        object.__setattr__(self, "wake_phrases", ["hola jarvis", "jarvis"])
        object.__setattr__(self, "require_visible_indicator", True)
        object.__setattr__(self, "no_audio_retention_by_default", True)
        object.__setattr__(self, "external_audio_processing_enabled", False)
        object.__setattr__(self, "background_listening_allowed", False)
        object.__setattr__(self, "push_to_talk_fallback", True)
        object.__setattr__(self, "stop_phrases", ["no escuches", "para", "cállate", "stop", "detente"])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WakePhraseParseResult:
    wake_phrase_detected: bool = False
    matched_phrase: Optional[str] = None
    extracted_command: str = ""
    confidence: float = 0.0
    should_open_session: bool = False
    should_answer: bool = False
    low_confidence: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    prepare_only: bool = True
    wake_phrase_is_not_permission: bool = True
    execution_enabled: bool = False
    side_effects_enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "blocked_reasons", list(self.blocked_reasons))
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "wake_phrase_is_not_permission", True)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "side_effects_enabled", False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VoiceCameraSafetyStatus:
    voice_runtime_available: bool = True
    wake_phrase_available: bool = True
    wake_phrases: List[str] = field(default_factory=lambda: ["Hola Jarvis", "Jarvis"])
    wake_phrase_enabled: bool = False
    background_listening_enabled: bool = False
    push_to_talk_fallback: bool = True
    camera_control_available: bool = True
    camera_active: bool = False
    microphone_active: bool = False
    recording_enabled: bool = False
    audio_retention_enabled: bool = False
    external_audio_enabled: bool = False
    external_video_enabled: bool = False
    execution_enabled: bool = False
    side_effects_enabled: bool = False
    approval_gates_enforced: bool = True
    strong_approval_enforced: bool = True
    wake_phrase_is_not_permission: bool = True
    prepare_only: bool = True

    def __post_init__(self) -> None:
        for name in (
            "voice_runtime_available",
            "wake_phrase_available",
            "push_to_talk_fallback",
            "camera_control_available",
            "approval_gates_enforced",
            "strong_approval_enforced",
            "wake_phrase_is_not_permission",
            "prepare_only",
        ):
            object.__setattr__(self, name, True)
        for name in (
            "wake_phrase_enabled",
            "background_listening_enabled",
            "camera_active",
            "microphone_active",
            "recording_enabled",
            "audio_retention_enabled",
            "external_audio_enabled",
            "external_video_enabled",
            "execution_enabled",
            "side_effects_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "wake_phrases", ["Hola Jarvis", "Jarvis"])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WakeVoiceRuntime:
    """Local-only wake phrase parser. It never opens a microphone or executes."""

    def __init__(self, config: Optional[WakePhraseConfig] = None) -> None:
        self.config = config or WakePhraseConfig()

    def status(self) -> Dict[str, Any]:
        return VoiceCameraSafetyStatus().to_dict()

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            **self.config.to_dict(),
            "wake_phrase_only_activates_session": True,
            "immediate_command_supported": True,
            "low_confidence_blocks_processing": True,
            "no_real_microphone": True,
            "no_recording": True,
            "no_external_processing": True,
        }

    def parse(self, text: str, *, confidence: float = 1.0) -> WakePhraseParseResult:
        confidence = normalize_confidence(confidence)
        raw = str(text or "").strip()
        normalized = raw.casefold()
        matched = next(
            (
                phrase
                for phrase in self.config.wake_phrases
                if re.match(rf"^{re.escape(phrase)}(?:\b|[\s,;:!.?])", normalized)
            ),
            None,
        )
        if not matched:
            return WakePhraseParseResult(
                confidence=confidence,
                blocked_reasons=["wake phrase must appear at the start of the transcript"],
            )

        command = raw[len(matched) :].lstrip(" \t,;:!.?¿¡-")
        low_confidence = confidence < self.config.confidence_threshold
        blocked = ["low confidence blocks command processing and sensitive actions"] if low_confidence else []
        return WakePhraseParseResult(
            wake_phrase_detected=True,
            matched_phrase=matched,
            extracted_command=command,
            confidence=confidence,
            should_open_session=not low_confidence,
            should_answer=not low_confidence,
            low_confidence=low_confidence,
            blocked_reasons=blocked,
        )


def normalize_confidence(value: float) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return confidence if math.isfinite(confidence) and 0.0 <= confidence <= 1.0 else 0.0
