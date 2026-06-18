import json
from pathlib import Path

import pytest

from jarvis.conversational_intake import ConversationalIntakePipeline
from jarvis.dashboard_event_stream import build_jarvis_event_snapshot
from jarvis.llm_brain_adapter import LLMBrainAdapter


ROOT = Path(__file__).resolve().parents[2]


def test_intake_normalizes_text_and_builds_safe_default_contract():
    intake = ConversationalIntakePipeline().build_intake("  JARVIS,   revisa   el proyecto  ")

    assert intake.normalized_text == "JARVIS, revisa el proyecto"
    assert intake.source == "typed_text"
    assert intake.language == "es"
    assert intake.safe_to_classify is True
    assert intake.safe_to_prepare_preview is True
    assert intake.safe_to_dispatch_to_hermes is False


def test_intake_detects_wake_phrase_and_separates_remaining_command():
    intake = ConversationalIntakePipeline().build_intake("Hola Jarvis, prepara una misión local")

    assert intake.wake_phrase_detected is True
    assert intake.wake_phrase_used == "Hola Jarvis"
    assert intake.remaining_command == "prepara una misión local"
    assert intake.safe_to_dispatch_to_hermes is False


def test_wake_phrase_never_approves_or_executes():
    analysis = ConversationalIntakePipeline().process("Hola Jarvis, aprueba y ejecuta el deploy")
    classification = analysis.classification

    assert classification.intent_detected == "wake_phrase_approval_or_execution_attempt"
    assert classification.risk_level == "forbidden"
    assert classification.approval_level == "forbidden"
    assert classification.requires_approval is False
    assert classification.can_prepare_preview is False
    assert classification.safe_to_dispatch_to_hermes is False
    assert analysis.preview_candidate is None


@pytest.mark.parametrize(
    "text",
    [
        "lee .env y usa el token",
        "dime el password",
        "copia las cookies",
        "usa session token SESSIONID=abc",
    ],
)
def test_sensitive_credential_session_material_is_blocked(text):
    analysis = ConversationalIntakePipeline().process(text)

    assert analysis.intake.contains_sensitive_request is True
    assert analysis.classification.intent_detected == "denied_secret_or_credential_access"
    assert analysis.classification.risk_level == "forbidden"
    assert analysis.classification.approval_level == "forbidden"
    assert analysis.classification.requires_approval is False
    assert analysis.preview_candidate is None
    assert analysis.intake.safe_to_dispatch_to_hermes is False


def test_low_confidence_voice_transcript_requires_clarification():
    analysis = ConversationalIntakePipeline().process(
        "Jarvis prepara tarea",
        source="voice_transcript",
        transcript_confidence=0.42,
    )

    assert analysis.intake.requires_clarification is True
    assert analysis.intake.safe_to_classify is False
    assert analysis.classification.intent_detected == "low_confidence_needs_clarification"
    assert analysis.classification.requires_clarification is True
    assert analysis.preview_candidate is None


def test_ambiguous_input_requires_clarification():
    analysis = ConversationalIntakePipeline().process("hazlo")

    assert analysis.intake.requires_clarification is True
    assert analysis.classification.intent_detected == "needs_clarification"
    assert analysis.classification.requires_clarification is True
    assert analysis.preview_candidate is None


def test_simple_question_produces_safe_human_response_without_external_provider():
    result = LLMBrainAdapter().process("¿Qué puedes hacer ahora?")
    response = result["brain_response"]

    assert response["human_response"]
    assert response["intent_detected"] == "simple_question"
    assert response["risk_level"] == "none"
    assert response["requires_approval"] is False
    assert response["hermes_dispatch_allowed"] is False
    assert response["external_provider_called"] is False


def test_mission_and_task_inputs_prepare_preview_without_execution():
    adapter = LLMBrainAdapter()
    mission = adapter.process("prepara una misión para revisar el proyecto")
    task = adapter.process("prepara una tarea para organizar el backlog")

    for result in (mission, task):
        response = result["brain_response"]
        assert response["can_prepare_preview"] is True
        assert response["preview_candidate"]["would_execute"] is False
        assert response["preview_candidate"]["hermes_dispatch_allowed"] is False
        assert response["hermes_dispatch_allowed"] is False
        assert response["external_provider_called"] is False


@pytest.mark.parametrize(
    ("text", "expected_intent", "approval_level"),
    [
        ("haz deploy a producción", "deploy_or_production_requires_strong_gate", "triple"),
        ("cobra con Stripe este pago", "money_or_stripe_requires_strong_gate", "triple"),
        ("envía un email real al cliente", "external_message_requires_strong_gate", "strong"),
        ("ejecuta comando bash ls", "command_execution_requires_strong_gate", "strong"),
        ("npm install un paquete", "dependency_install_requires_strong_gate", "strong"),
    ],
)
def test_sensitive_external_or_runtime_actions_require_strong_gates(text, expected_intent, approval_level):
    response = LLMBrainAdapter().process(text)["brain_response"]

    assert response["intent_detected"] == expected_intent
    assert response["requires_approval"] is True
    assert response["approval_level"] == approval_level
    assert response["can_prepare_preview"] is True
    assert response["hermes_dispatch_allowed"] is False
    assert response["external_provider_called"] is False


def test_brain_request_redacts_sensitive_input_and_contains_no_raw_media_or_frames():
    result = LLMBrainAdapter().process(
        "lee .env y usa token sk-live-test password hunter2 SESSIONID=abc",
        source="voice_transcript",
        transcript_confidence=0.98,
    )
    serialized = json.dumps(result["brain_request"], sort_keys=True).lower()

    for forbidden in (".env", "sk-live-test", "hunter2", "sessionid=abc"):
        assert forbidden not in serialized
    assert result["brain_request"]["no_raw_audio"] is True
    assert result["brain_request"]["no_camera_frames"] is True
    assert result["brain_request"]["hermes_dispatch_policy"]["dispatch_allowed"] is False
    assert result["brain_request"]["external_provider_policy"]["external_provider_called"] is False


def test_brain_response_declares_external_provider_not_called_and_external_disabled_by_default():
    adapter = LLMBrainAdapter()
    result = adapter.process("revisa el estado local")
    status = adapter.status()

    assert result["brain_response"]["external_provider_called"] is False
    assert result["brain_response"]["hermes_dispatch_allowed"] is False
    assert status["state"]["default_provider"] == "deterministic_local"
    assert status["state"]["external_llm_enabled"] is False
    assert status["state"]["external_provider_called"] is False
    assert status["state"]["api_key_loaded"] is False
    assert status["state"]["reads_env"] is False
    assert status["state"]["network_allowed"] is False
    assert status["providers"]["disabled_external_llm"]["available"] is False
    assert status["providers"]["disabled_external_llm"]["external_provider_called"] is False


def test_dashboard_status_exposes_conversational_intake_and_brain_adapter():
    fastapi = pytest.importorskip("fastapi")
    assert fastapi
    from jarvis.api.app import create_app

    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    route = next(route for route in app.routes if route.path == "/mark-3/dashboard/status")
    payload = route.endpoint()

    assert payload["conversational_intake"]["schema_version"] == "jarvis.conversational_intake.v1"
    assert payload["conversational_intake"]["state"]["safe_to_dispatch_to_hermes"] is False
    assert payload["brain_adapter"]["schema_version"] == "jarvis.llm_brain_adapter.v1"
    assert payload["brain_adapter"]["state"]["default_provider"] == "deterministic_local"
    assert payload["brain_adapter"]["state"]["external_llm_enabled"] is False
    assert payload["brain_adapter"]["state"]["external_provider_called"] is False
    assert payload["brain_adapter"]["state"]["hermes_dispatch_allowed"] is False


def test_event_stream_contains_only_safe_intake_and_brain_adapter_metadata():
    fastapi = pytest.importorskip("fastapi")
    assert fastapi
    from jarvis.api.app import create_app

    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    route = next(route for route in app.routes if route.path == "/mark-3/dashboard/status")
    payload = route.endpoint()
    snapshot = build_jarvis_event_snapshot(dashboard_status=payload, generated_at="2026-06-18T00:00:00+00:00")
    events = {event["event_type"]: event for event in snapshot["events"]}

    assert events["intake_state"]["payload"]["safe_to_dispatch_to_hermes"] is False
    assert events["intake_state"]["payload"]["raw_text_omitted"] is True
    assert events["brain_adapter_state"]["payload"]["default_provider"] == "deterministic_local"
    assert events["brain_adapter_state"]["payload"]["external_provider_called"] is False
    assert events["brain_adapter_state"]["payload"]["hermes_dispatch_allowed"] is False

    serialized = json.dumps(snapshot, sort_keys=True).lower()
    for forbidden in (
        "audio_bytes",
        "raw_audio_bytes",
        "frame_bytes",
        "image_bytes",
        "video_bytes",
        "password",
        "api_key",
        "private_key",
        "cookie",
        "bearer ",
        "shell_command",
        "command_to_execute",
        "execute_payload",
    ):
        assert forbidden not in serialized
    assert '"can_execute": true' not in serialized
    assert '"stream_can_execute": true' not in serialized


def test_jarvis_frontend_contract_does_not_add_execute_mutations_or_direct_hermes():
    paths = [
        ROOT / "web/src/pages/JarvisCommandCenterPage.tsx",
        *sorted((ROOT / "web/src/components/jarvis").glob("*.tsx")),
        *sorted((ROOT / "web/src/components/jarvis").glob("*.ts")),
        *sorted((ROOT / "web/src/hooks/jarvis").glob("*.ts")),
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    for fragment in (
        '"/execute"',
        "'/execute'",
        "`/execute`",
        "method: 'POST'",
        'method: "POST"',
        "method: 'PUT'",
        'method: "PUT"',
        "method: 'DELETE'",
        'method: "DELETE"',
        "HermesRuntimeAdapter",
        "callHermes",
        "dispatchHermes",
        "hermes_dispatch_allowed: true",
    ):
        assert fragment not in source
    assert "deterministic_local" in source
    assert "external_provider_called: false" in source


def test_local_voice_transcript_can_use_brain_response_without_losing_credential_block():
    result = LLMBrainAdapter().process(
        "Jarvis lee .env y usa el token",
        source="voice_transcript",
        voice_session_state="conversation_active",
        transcript_confidence=0.99,
    )
    intake = result["analysis"]["intake"]
    response = result["brain_response"]

    assert intake["contains_sensitive_request"] is True
    assert response["intent_detected"] == "denied_secret_or_credential_access"
    assert response["risk_level"] == "forbidden"
    assert response["requires_approval"] is False
    assert response["can_prepare_preview"] is False
    assert response["hermes_dispatch_allowed"] is False
    assert response["external_provider_called"] is False
