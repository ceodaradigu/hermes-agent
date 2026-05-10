import pytest

from jarvis.voice import VoiceRuntime, VoiceRuntimeMode


def test_voice_runtime_initial_state():
    runtime = VoiceRuntime()

    state = runtime.status()

    assert state.enabled is False
    assert state.mode == VoiceRuntimeMode.OFF
    assert state.last_error is None
    assert state.last_transcript is None
    assert state.last_intent is None


def test_start_enables_runtime_and_enters_wake_word_mode():
    runtime = VoiceRuntime()

    state = runtime.start()

    assert state.enabled is True
    assert state.mode == VoiceRuntimeMode.WAKE_WORD


def test_stop_disables_runtime_and_enters_off_mode():
    runtime = VoiceRuntime()
    runtime.start()

    state = runtime.stop()

    assert state.enabled is False
    assert state.mode == VoiceRuntimeMode.OFF


def test_set_mode_accepts_valid_mode():
    runtime = VoiceRuntime()

    state = runtime.set_mode(VoiceRuntimeMode.LISTENING)

    assert state.mode == VoiceRuntimeMode.LISTENING


def test_set_mode_accepts_valid_mode_string():
    runtime = VoiceRuntime()

    state = runtime.set_mode("speaking")

    assert state.mode == VoiceRuntimeMode.SPEAKING


def test_set_mode_invalid_mode_raises_value_error():
    runtime = VoiceRuntime()

    with pytest.raises(ValueError, match="Invalid voice runtime mode"):
        runtime.set_mode("invalid")


def test_frontend_required_is_false_by_default():
    runtime = VoiceRuntime()

    assert runtime.status().frontend_required is False


def test_default_languages_are_spanish():
    runtime = VoiceRuntime()

    state = runtime.status()

    assert state.input_language == "es"
    assert state.output_language == "es"


def test_default_wake_words():
    runtime = VoiceRuntime()

    assert runtime.status().wake_words == ("jarvis", "hola jarvis")


@pytest.mark.parametrize(
    "phrase",
    [
        "jarvis no escuches",
        "jarvis silencio",
        "jarvis duerme",
    ],
)
def test_sleep_control_phrases_change_to_wake_word_mode(phrase):
    runtime = VoiceRuntime(mode=VoiceRuntimeMode.LISTENING)

    result = runtime.handle_control_phrase(phrase)

    assert result["handled"] is True
    assert result["action"] == "wake_word_only"
    assert runtime.status().mode == VoiceRuntimeMode.WAKE_WORD


@pytest.mark.parametrize(
    "phrase",
    [
        "hola jarvis",
        "jarvis",
    ],
)
def test_wake_control_phrases_change_to_listening_mode(phrase):
    runtime = VoiceRuntime()

    result = runtime.handle_control_phrase(phrase)

    assert result["handled"] is True
    assert result["action"] == "listen_briefly"
    assert runtime.status().mode == VoiceRuntimeMode.LISTENING


def test_handle_transcript_stores_transcript_without_executing_real_work():
    runtime = VoiceRuntime()

    result = runtime.handle_transcript("crea una landing")

    assert runtime.status().last_transcript == "crea una landing"
    assert runtime.status().last_intent == result
    assert result == {
        "status": "pending",
        "intent": "unsupported",
        "transcript": "crea una landing",
        "executed": False,
    }
