from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from jarvis.voice.base import VoiceAdapter, VoiceSynthesisRequest, VoiceSynthesisResult


class PiperCLIAdapter(VoiceAdapter):
    """Optional local Piper TTS adapter.

    Piper is intentionally treated as a local binary dependency. This adapter
    never downloads voices, never calls a network API, and never invokes a shell.
    """

    def __init__(
        self,
        *,
        binary_path: str = "piper",
        jarvis_model_path: Optional[str] = None,
        utron_model_path: Optional[str] = None,
        speaker_id: Optional[str] = None,
        runner: Any = None,
    ) -> None:
        self.binary_path = binary_path
        self.jarvis_model_path = jarvis_model_path
        self.utron_model_path = utron_model_path
        self.speaker_id = speaker_id
        self.runner = runner or subprocess.run

    def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        model_path = self._model_path(request)
        if not self.binary_path or not self.binary_path.strip():
            raise ValueError("binary_path must be a non-empty string")
        if not model_path or not str(model_path).strip():
            raise ValueError("Piper model path is required")
        if request.output_format != "wav":
            raise ValueError("Piper CLI output is wav-only in this adapter")

        with tempfile.NamedTemporaryFile(prefix="jarvis-piper-", suffix=".wav", delete=False) as tmp:
            output_path = Path(tmp.name)

        argv = self._argv(model_path, output_path, request)
        try:
            result = self.runner(
                argv,
                input=request.text,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=45,
                check=False,
            )
            returncode = int(getattr(result, "returncode", 0))
            if returncode != 0:
                message = _trim_error(getattr(result, "stderr", "") or getattr(result, "stdout", ""))
                raise RuntimeError(f"Piper synthesis failed: {message or 'non-zero exit'}")
            audio_bytes = output_path.read_bytes()
        finally:
            try:
                output_path.unlink(missing_ok=True)
            except OSError:
                pass

        return VoiceSynthesisResult(
            content_type="audio/wav",
            provider="piper",
            audio_bytes=audio_bytes,
            metadata={
                **request.metadata,
                "local_only": True,
                "network_required": False,
                "voice_profile": self._voice_profile(request),
            },
        )

    def _model_path(self, request: VoiceSynthesisRequest) -> str:
        persona = self._voice_profile(request)
        if persona == "utron" and self.utron_model_path:
            return self.utron_model_path
        return self.jarvis_model_path or str(request.metadata.get("model_path") or "")

    def _voice_profile(self, request: VoiceSynthesisRequest) -> str:
        raw = str(request.voice_id or request.metadata.get("persona") or request.metadata.get("voice_profile") or "jarvis")
        return "utron" if raw.strip().casefold() == "utron" else "jarvis"

    def _argv(self, model_path: str, output_path: Path, request: VoiceSynthesisRequest) -> List[str]:
        argv = [self.binary_path, "--model", model_path, "--output_file", str(output_path)]
        speaker = request.metadata.get("speaker_id", self.speaker_id)
        if speaker not in (None, ""):
            argv.extend(["--speaker", str(speaker)])
        return argv


def _trim_error(value: Any) -> str:
    text = " ".join(str(value or "").split())
    return text[:240]
