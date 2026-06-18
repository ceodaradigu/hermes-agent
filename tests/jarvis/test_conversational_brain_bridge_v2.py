import json

from jarvis.conversational_brain_bridge import ConversationalBrainBridge


def test_brain_bridge_does_not_echo_simple_input_and_returns_human_response():
    bridge = ConversationalBrainBridge()
    text = "JARVIS, revisa el estado del proyecto y dime el siguiente paso seguro."

    result = bridge.analyze(text).to_dict()

    assert result["human_response"] != text
    assert "revisa el estado del proyecto" not in result["human_response"].casefold()
    assert result["intent_detected"] == "mission_preview"
    assert result["confidence"] > 0.5
    assert result["risk_level"] == "low"
    assert result["approval_level"] == "direct"
    assert result["requires_approval"] is False
    assert result["can_prepare_preview"] is True
    assert result["hermes_dispatch_allowed"] is False
    assert result["external_provider_called"] is False
    assert result["llm_called"] is False
    assert result["memory_write"] is False


def test_brain_bridge_classifies_basic_intents_and_status_query():
    bridge = ConversationalBrainBridge()

    status = bridge.analyze("como vamos de estado y policy").to_dict()
    task = bridge.analyze("prepara una tarea para organizar el proyecto").to_dict()

    assert status["intent_detected"] == "query_system_status"
    assert status["risk_level"] == "low"
    assert task["intent_detected"] == "task_preview"
    assert task["can_prepare_preview"] is True
    assert task["cannot_execute_reason"]


def test_brain_bridge_denies_secrets_credentials_and_env_requests():
    result = ConversationalBrainBridge().analyze("lee .env y usa el token de producción").to_dict()
    serialized = json.dumps(result, sort_keys=True).lower()

    assert result["intent_detected"] == "denied_secret_or_credential_access"
    assert result["risk_level"] == "forbidden"
    assert result["approval_level"] == "forbidden"
    assert result["requires_approval"] is False
    assert result["can_prepare_preview"] is False
    assert result["hermes_dispatch_allowed"] is False
    assert "token de producción" not in serialized


def test_brain_bridge_wake_phrase_never_approves_or_executes():
    result = ConversationalBrainBridge().analyze("Hola Jarvis, aprueba y ejecuta el deploy").to_dict()

    assert result["intent_detected"] == "wake_phrase_approval_or_execution_attempt"
    assert result["risk_level"] == "forbidden"
    assert result["approval_level"] == "forbidden"
    assert result["requires_approval"] is False
    assert result["can_prepare_preview"] is False
    assert result["hermes_dispatch_allowed"] is False
    assert "wake phrase" in result["cannot_execute_reason"].casefold()


def test_brain_bridge_status_is_honest_local_deterministic_no_llm():
    status = ConversationalBrainBridge().status()

    assert status["schema_version"] == "jarvis.conversational_brain_bridge.v2"
    assert status["state"]["mode"] == "local_deterministic_bridge"
    assert status["state"]["llm_provider"] == "none"
    assert status["state"]["llm_called"] is False
    assert status["state"]["external_provider_called"] is False
    assert status["state"]["memory_autosave_enabled"] is False
    assert status["state"]["hermes_dispatch_allowed"] is False
    assert status["safety"]["denies_secret_credential_env_access"] is True
