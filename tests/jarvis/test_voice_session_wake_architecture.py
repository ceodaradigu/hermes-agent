import json

from jarvis.real_wake_listener import RealWakeListener, RealWakeListenerPlan
from jarvis.voice_session_control import VOICE_SESSION_STATES, VoiceSessionControl
from jarvis.wake_voice_runtime import WakeVoiceRuntime


def test_voice_session_manager_declares_required_states_and_safe_defaults():
    status = VoiceSessionControl().status(wake_listener_status=RealWakeListenerPlan().to_dict())

    assert status["schema_version"] == "jarvis.voice_session_manager.v1"
    assert status["supported_states"] == list(VOICE_SESSION_STATES)
    for state in (
        "idle",
        "wake_listening_available",
        "wake_listening_disabled",
        "conversation_active",
        "listening",
        "transcribing",
        "thinking",
        "speaking",
        "approval_required",
        "cancelled",
        "stopped",
        "error",
    ):
        assert state in status["supported_states"]
    assert status["state"]["current_state"] == "idle"
    assert status["state"]["wake_listening_state"] == "wake_listening_disabled"
    assert status["state"]["conversation_active"] is False
    assert status["state"]["auto_start"] is False
    assert status["state"]["activation_endpoint_enabled"] is False
    assert status["preview_only"] is True
    assert status["read_only"] is True


def test_voice_session_separates_wake_conversation_stt_tts_recording_approval_and_hermes():
    status = VoiceSessionControl().status(wake_listener_status=RealWakeListenerPlan().to_dict())
    separation = status["separation"]

    assert separation["wake_listening"]["enabled"] is False
    assert separation["wake_listening"]["purpose"] == "activation_only"
    assert separation["wake_listening"]["records_audio"] is False
    assert separation["wake_listening"]["transcribes_full_conversation"] is False
    assert separation["wake_listening"]["approves"] is False
    assert separation["wake_listening"]["executes"] is False

    assert separation["active_conversation"]["enabled"] is False
    assert separation["manual_push_to_talk"]["operator_gesture_required"] is True
    assert separation["manual_push_to_talk"]["microphone_auto_start"] is False
    assert separation["stt"]["backend_enabled"] is False
    assert separation["stt"]["always_on_stt"] is False
    assert separation["stt"]["background_transcription"] is False
    assert separation["tts"]["backend_enabled"] is False
    assert separation["tts"]["external_provider_called"] is False
    assert separation["raw_audio_recording"]["backend_enabled"] is False
    assert separation["raw_audio_recording"]["raw_audio_sent_to_backend"] is False
    assert separation["voice_approval"]["enabled"] is False
    assert separation["voice_approval"]["disabled_unless_authenticated_gated_audited"] is True
    assert separation["hermes_execution"]["dispatch_allowed"] is False


def test_voice_session_privacy_flags_are_default_false_for_persistence_and_always_on():
    status = VoiceSessionControl().status(wake_listener_status=RealWakeListenerPlan().to_dict())
    privacy = status["privacy"]

    assert privacy["raw_audio_sent_to_backend"] is False
    assert privacy["transcript_persistence"] is False
    assert privacy["background_transcription"] is False
    assert privacy["always_on_stt"] is False
    assert privacy["microphone_auto_start"] is False
    assert privacy["memory_autosave"] is False


def test_wake_architecture_contract_is_disabled_opt_in_and_metadata_only():
    wake_status = RealWakeListener().status()
    session = VoiceSessionControl().status(wake_listener_status=wake_status)
    wake = session["wake_architecture"]

    assert wake["provider_contract"] == "openWakeWord"
    assert wake["dependency_detection"]["source"] == "python_importlib"
    assert wake["auto_start"] is False
    assert wake["activation_endpoint_enabled"] is False
    assert wake["supported_phrases"] == ["Hola Jarvis", "Jarvis"]
    for phrase in ("para", "cancela", "detente", "silencio", "cancelar misión", "apaga escucha"):
        assert phrase in wake["stop_phrases"]
    assert wake["ephemeral_buffer_contract"]["in_memory_only"] is True
    assert wake["ephemeral_buffer_contract"]["persisted"] is False
    assert wake["ephemeral_buffer_contract"]["sent_to_backend"] is False
    assert wake["no_transcription_until_valid_activation"] is True
    assert wake["no_approval"] is True
    assert wake["no_execution"] is True
    assert wake["visible_indicator_required"] is True
    assert wake["stop_cancel_required"] is True


def test_wake_phrase_no_approval_no_execution_and_no_audio_persistence():
    runtime_result = WakeVoiceRuntime().parse("Hola Jarvis, aprueba deploy").to_dict()
    listener_result = RealWakeListener().preview_transcript("Hola Jarvis, aprueba deploy")
    serialized = json.dumps(listener_result, sort_keys=True).lower()

    assert runtime_result["wake_phrase_detected"] is True
    assert runtime_result["execution_enabled"] is False
    assert runtime_result["side_effects_enabled"] is False
    assert runtime_result["wake_phrase_is_not_permission"] is True
    assert listener_result["approval_granted"] is False
    assert listener_result["would_execute"] is False
    assert listener_result["microphone_accessed"] is False
    assert "raw_audio" not in serialized
