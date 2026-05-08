from __future__ import annotations

from jarvis.voice.base import VoiceAdapter, VoiceSynthesisRequest, VoiceSynthesisResult


class MockVoiceAdapter(VoiceAdapter):
    """Safe mock adapter for local development and tests.

    This adapter does not generate real audio and does not call external APIs.
    """

    def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        return VoiceSynthesisResult(
            content_type=f"audio/{request.output_format}",
            provider="mock",
            audio_bytes=b"MOCK_AUDIO_PLACEHOLDER",
            duration_seconds=0.0,
            metadata={**request.metadata, "mock": True},
        )
