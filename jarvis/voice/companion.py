from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


_CONTROL_POLICY_REASON = "Voice Companion controls are policy placeholders only."


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
