from __future__ import annotations

import os
from typing import Mapping, Optional

from jarvis.voice.base import VoiceAdapter
from jarvis.voice.gpt_sovits_adapter import GPTSoVITSAdapter
from jarvis.voice.mock_adapter import MockVoiceAdapter


def create_voice_adapter_from_env(env: Optional[Mapping[str, str]] = None) -> VoiceAdapter:
    source = env if env is not None else os.environ
    provider = source.get("JARVIS_VOICE_PROVIDER", "mock").strip().lower()

    if provider == "mock":
        return MockVoiceAdapter()

    if provider == "gpt-sovits":
        timeout_raw = source.get("JARVIS_GPT_SOVITS_TIMEOUT_SECONDS", "30.0")
        try:
            timeout_seconds = float(timeout_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid JARVIS_GPT_SOVITS_TIMEOUT_SECONDS; expected a numeric value"
            ) from exc

        return GPTSoVITSAdapter(
            base_url=source.get("JARVIS_GPT_SOVITS_BASE_URL", "http://127.0.0.1:9880"),
            ref_audio_path=source.get("JARVIS_GPT_SOVITS_REF_AUDIO_PATH"),
            prompt_text=source.get("JARVIS_GPT_SOVITS_PROMPT_TEXT"),
            prompt_lang=source.get("JARVIS_GPT_SOVITS_PROMPT_LANG", "es"),
            timeout_seconds=timeout_seconds,
        )

    raise ValueError(
        f"Unknown JARVIS_VOICE_PROVIDER '{provider}'. Allowed values: mock, gpt-sovits"
    )
