from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


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
