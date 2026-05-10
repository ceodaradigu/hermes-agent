from dataclasses import dataclass
from enum import Enum
from typing import Any

from jarvis.voice.intent_router import VoiceIntentRouter


class VoiceRuntimeMode(str, Enum):
    OFF = "off"
    WAKE_WORD = "wake_word"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class VoiceRuntimeState:
    mode: VoiceRuntimeMode
    enabled: bool
    frontend_required: bool
    input_language: str
    output_language: str
    last_error: str | None
    last_transcript: str | None
    last_intent: dict[str, Any] | None
    wake_words: tuple[str, ...]


class VoiceRuntime:
    """Control-plane state for future local voice runtime work.

    This class intentionally does not access microphones, wake-word engines,
    STT providers, playback devices, threads, or background services.
    """

    _SLEEP_CONTROL_PHRASES = {
        "jarvis no escuches",
        "jarvis silencio",
        "jarvis duerme",
    }
    _WAKE_CONTROL_PHRASES = {
        "hola jarvis",
        "jarvis",
    }

    def __init__(
        self,
        *,
        enabled: bool = False,
        mode: VoiceRuntimeMode | str = VoiceRuntimeMode.OFF,
        frontend_required: bool = False,
        input_language: str = "es",
        output_language: str = "es",
        wake_words: tuple[str, ...] = ("jarvis", "hola jarvis"),
        intent_router: VoiceIntentRouter | None = None,
    ) -> None:
        self._intent_router = intent_router or VoiceIntentRouter()
        self._state = VoiceRuntimeState(
            mode=self._coerce_mode(mode),
            enabled=enabled,
            frontend_required=frontend_required,
            input_language=input_language,
            output_language=output_language,
            last_error=None,
            last_transcript=None,
            last_intent=None,
            wake_words=wake_words,
        )

    def status(self) -> VoiceRuntimeState:
        return self._state

    def start(self) -> VoiceRuntimeState:
        self._state.enabled = True
        self._state.mode = VoiceRuntimeMode.WAKE_WORD
        self._state.last_error = None
        return self.status()

    def stop(self) -> VoiceRuntimeState:
        self._state.enabled = False
        self._state.mode = VoiceRuntimeMode.OFF
        return self.status()

    def set_mode(self, mode: VoiceRuntimeMode | str) -> VoiceRuntimeState:
        self._state.mode = self._coerce_mode(mode)
        self._state.last_error = None
        return self.status()

    def handle_control_phrase(self, text: str) -> dict[str, Any]:
        normalized = self._normalize_text(text)

        if normalized in self._SLEEP_CONTROL_PHRASES:
            self.set_mode(VoiceRuntimeMode.WAKE_WORD)
            return {"handled": True, "mode": self._state.mode.value, "action": "wake_word_only"}

        if normalized in self._WAKE_CONTROL_PHRASES:
            self.set_mode(VoiceRuntimeMode.LISTENING)
            return {"handled": True, "mode": self._state.mode.value, "action": "listen_briefly"}

        return {"handled": False, "mode": self._state.mode.value, "action": "none"}

    def handle_transcript(self, text: str) -> dict[str, Any]:
        self._state.last_transcript = text
        self._state.last_intent = self._intent_router.classify(text).to_dict()
        return self._state.last_intent

    @staticmethod
    def _coerce_mode(mode: VoiceRuntimeMode | str) -> VoiceRuntimeMode:
        if isinstance(mode, VoiceRuntimeMode):
            return mode

        try:
            return VoiceRuntimeMode(mode)
        except ValueError as exc:
            allowed = ", ".join(item.value for item in VoiceRuntimeMode)
            raise ValueError(f"Invalid voice runtime mode '{mode}'. Allowed values: {allowed}") from exc

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.strip().lower().split())
