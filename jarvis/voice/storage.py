from __future__ import annotations

from pathlib import Path
from uuid import uuid4

_ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg"}


class VoiceAudioStorage:
    def __init__(self, base_dir: Path | str | None = None):
        self.base_dir = Path(base_dir) if base_dir is not None else Path(".jarvis") / "voice_outputs"

    def save_audio(self, audio_bytes: bytes, output_format: str) -> str:
        fmt = output_format.strip().lower()
        if fmt not in _ALLOWED_EXTENSIONS:
            raise ValueError(f"unsupported output_format: {output_format}")

        if ".." in self.base_dir.parts:
            raise ValueError("invalid output path")

        self.base_dir.mkdir(parents=True, exist_ok=True)
        target = (self.base_dir / f"{uuid4()}.{fmt}").resolve()
        base_resolved = self.base_dir.resolve()
        if base_resolved not in target.parents:
            raise ValueError("invalid output path")

        target.write_bytes(audio_bytes)
        return str(target)
