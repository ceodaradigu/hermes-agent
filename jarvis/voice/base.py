from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Protocol


_ALLOWED_OUTPUT_FORMATS = {"wav", "mp3", "ogg"}


@dataclass
class VoiceSynthesisRequest:
    text: str
    voice_id: Optional[str] = None
    language: str = "es"
    output_format: str = "wav"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise ValueError("text must be a non-empty string")
        if not self.language or not self.language.strip():
            raise ValueError("language must be a non-empty string")
        if self.output_format not in _ALLOWED_OUTPUT_FORMATS:
            raise ValueError(
                f"output_format must be one of: {', '.join(sorted(_ALLOWED_OUTPUT_FORMATS))}"
            )


@dataclass
class VoiceSynthesisResult:
    content_type: str
    provider: str
    audio_path: Optional[Path] = None
    audio_bytes: Optional[bytes] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class VoiceAdapter(Protocol):
    def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        ...
