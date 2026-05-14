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
    assert result["status"] == "pending"
    assert result["intent"] == "create_asset"
    assert result["transcript"] == "crea una landing"
    assert result["executed"] is False


def test_apply_reviewed_feedback_changes_matching_transcript_without_execution():
    runtime = VoiceRuntime()
    runtime.apply_reviewed_feedback(
        original_text="monta algo para probar este nicho",
        interpreted_intent="create_asset",
        corrected_intent="create_mission",
        correction_note="Primero quiero validación.",
    )

    result = runtime.handle_transcript("monta algo para probar este nicho")

    assert result["status"] == "pending"
    assert result["intent"] == "create_mission"
    assert result["executed"] is False
    assert result["approval_required"] is False
    assert result["user_context_signals"]["reviewed_feedback_applied"] is True
    assert "temporary reviewed feedback rule from David" in result["reason"]


def test_sensitive_terms_keep_requires_approval_with_applied_feedback():
    runtime = VoiceRuntime()
    runtime.apply_reviewed_feedback(
        original_text="monta algo para probar este nicho",
        interpreted_intent="create_asset",
        corrected_intent="create_mission",
    )

    result = runtime.handle_transcript("monta algo para probar este nicho y usa el password del .env")

    assert result["status"] == "requires_approval"
    assert result["intent"] == "requires_approval"
    assert result["approval_required"] is True
    assert result["executed"] is False
    assert "reviewed_feedback_applied" not in result["user_context_signals"]


def test_applied_rules_are_process_local_to_runtime_instance():
    runtime = VoiceRuntime()
    runtime.apply_reviewed_feedback(
        original_text="monta algo para probar este nicho",
        interpreted_intent="create_asset",
        corrected_intent="create_mission",
    )

    fresh_runtime = VoiceRuntime()

    assert runtime.status().applied_feedback_count == 1
    assert fresh_runtime.status().applied_feedback_count == 0
    assert fresh_runtime.handle_transcript("monta algo para probar este nicho")["intent"] == "create_asset"
