import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (  # noqa: E402
    Mark3ModelRouterDecisionRequest,
    Mark3Phase10AppLaunchRequest,
    Mark3Phase10ApprovalConfirmRequest,
    Mark3Phase10ApprovalStartRequest,
    Mark3Phase10TextRequest,
    create_app,
)
from jarvis.dashboard_event_stream import build_jarvis_event_snapshot  # noqa: E402
from jarvis.dashboard_read_model import build_mark_3_dashboard_status  # noqa: E402
from jarvis.phase_10_hands_free_runtime_persona_api_router import (  # noqa: E402
    PHASE_10_EXACT_APPROVAL_PHRASE,
    Phase10HandsFreeRuntimePersonaApiRouter,
)


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


def _route(app, path: str, method: str = "GET"):
    return next(route for route in app.routes if route.path == path and method in getattr(route, "methods", set()))


def _frontend_source() -> str:
    paths = [
        WEB / "src/pages/JarvisCommandCenterPage.tsx",
        WEB / "src/components/jarvis/JarvisPresenceShell.tsx",
        WEB / "src/components/jarvis/JarvisOrb3D.tsx",
        WEB / "src/components/jarvis/JarvisSmartBar.tsx",
        WEB / "src/components/jarvis/types.ts",
        WEB / "src/components/jarvis/contracts.ts",
        WEB / "src/hooks/jarvis/useLocalVoiceLoop.ts",
        WEB / "src/lib/api.ts",
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_phase_10_wake_and_stop_phrases_are_recognized_without_approval_or_audio_storage():
    runtime = Phase10HandsFreeRuntimePersonaApiRouter()

    for phrase in ("Hola JARVIS", "JARVIS"):
        result = runtime.wake_stop.preview(phrase, confidence=0.99)
        assert result["wake_phrase_detected"] is True
        assert result["should_open_conversation"] is True
        assert result["should_request_local_controller_open_jarvis"] is True
        assert result["approval"]["wake_phrase_can_approve"] is False
        assert result["privacy"]["raw_audio_stored"] is False

    for phrase in ("para", "JARVIS para", "cállate", "JARVIS cállate"):
        result = runtime.wake_stop.preview(phrase, confidence=0.99)
        assert result["stop_phrase_detected"] is True
        assert result["visible_state"] == "stopped"
        assert result["approval"]["wake_phrase_can_execute"] is False


def test_voice_ui_intent_router_accepts_natural_variants_and_gates_sensitive_controls():
    router = Phase10HandsFreeRuntimePersonaApiRouter().voice_ui

    cases = {
        "abre el panel": "ui.panel.open",
        "enséñame el panel": "ui.panel.open",
        "quita el panel": "ui.panel.close",
        "activa la voz": "ui.voice_output.enable",
        "repíteme eso": "ui.voice_output.repeat",
        "corta ya": "ui.voice_output.stop",
        "revisa el estado": "ui.status.review",
        "cancela": "ui.cancel",
    }
    for text, expected in cases.items():
        decision = router.route(text)
        assert decision.intent_name == expected
        assert decision.confidence >= 0.8
        assert decision.requires_approval is False
        assert decision.hermes_dispatch_allowed is False

    for text, action_id in {
        "abre la cámara": "camera.start",
        "graba audio": "audio_recording.start",
        "graba video": "video_recording.start",
    }.items():
        decision = router.route(text)
        assert decision.action_id == action_id
        assert decision.requires_approval is True
        assert decision.requires_exact_phrase is True
        assert decision.required_phrase == PHASE_10_EXACT_APPROVAL_PHRASE

    ambiguous = router.route("haz lo de antes")
    assert ambiguous.intent_name == "ambiguous"
    assert ambiguous.fallback_question


def test_app_launcher_known_unknown_and_browser_intents_are_governed_not_shell():
    runtime = Phase10HandsFreeRuntimePersonaApiRouter()

    chrome = runtime.app_launcher.prepare("Chrome")
    assert chrome["known"] is True
    assert chrome["status"] == "prepared_governed_intent"
    assert chrome["executed"] is False
    assert chrome["freeform_shell_allowed"] is False

    terminal = runtime.app_launcher.prepare("terminal")
    assert terminal["requires_approval"] is True
    assert terminal["requires_exact_phrase"] is True

    unknown = runtime.app_launcher.prepare("MiAppRara")
    assert unknown["known"] is False
    assert "No sé dónde está esa aplicación" in unknown["spanish_response"]
    assert unknown["executed"] is False

    fill = runtime.browser.prepare("rellena este formulario y envíalo")
    assert fill["intent"] == "form.fill_preview"
    assert fill["requires_approval"] is True
    assert fill["safety"]["form_submit_allowed"] is False

    payment = runtime.browser.prepare("compra esto y paga")
    assert payment["requires_strong_approval"] is True
    assert payment["safety"]["purchase_payment_publication_allowed"] is False

    login = runtime.browser.prepare("haz login con mi password")
    assert login["safety"]["login_manual_required"] is True
    assert login["safety"]["credential_storage_allowed"] is False


def test_approval_v2_requires_exact_phrase_active_voice_session_and_rejects_replay():
    approvals = Phase10HandsFreeRuntimePersonaApiRouter().approvals
    started = approvals.start(
        action="abrir terminal y ejecutar una tarea sensible",
        risk_level="high",
        cost_summary="0 EUR estimados",
        change_summary="puede tocar sistema local",
        rollback_or_stop_plan="cerrar antes de ejecutar",
        session_id="voice-session-1",
    )

    approval_id = started["approval_id"]
    assert PHASE_10_EXACT_APPROVAL_PHRASE in started["readback_text"]

    wrong = approvals.confirm(approval_id=approval_id, phrase="confirmo", session_id="voice-session-1")
    assert wrong["approved"] is False
    assert wrong["reason"] == "exact_phrase_required"

    wake = approvals.confirm(approval_id=approval_id, phrase="JARVIS", session_id="voice-session-1")
    assert wake["approved"] is False
    assert wake["reason"] == "wake_phrase_never_approves"

    untrusted_voice = approvals.confirm(
        approval_id=approval_id,
        phrase=PHASE_10_EXACT_APPROVAL_PHRASE,
        session_id="voice-session-1",
        channel="voice",
        active_trusted_session=False,
    )
    assert untrusted_voice["approved"] is False
    assert untrusted_voice["reason"] == "voice_requires_active_trusted_session"

    approved = approvals.confirm(
        approval_id=approval_id,
        phrase=PHASE_10_EXACT_APPROVAL_PHRASE,
        session_id="voice-session-1",
        channel="voice",
        active_trusted_session=True,
    )
    assert approved["approved"] is True
    assert approved["would_execute"] is False

    replay = approvals.confirm(
        approval_id=approval_id,
        phrase=PHASE_10_EXACT_APPROVAL_PHRASE,
        session_id="voice-session-1",
        channel="voice",
        active_trusted_session=True,
    )
    assert replay["approved"] is False
    assert replay["reason"] == "phrase_replay_rejected"

    unrelated = approvals.start(action="otra acción", risk_level="high", session_id="voice-session-1")
    context_mismatch = approvals.confirm(
        approval_id=unrelated["approval_id"],
        phrase=PHASE_10_EXACT_APPROVAL_PHRASE,
        session_id="voice-session-1",
        current_action_fingerprint=started["context_fingerprint"],
    )
    assert context_mismatch["approved"] is False
    assert context_mismatch["reason"] == "context_mismatch"


def test_persona_jarvis_utron_changes_visible_state_but_not_approval_safety():
    runtime = Phase10HandsFreeRuntimePersonaApiRouter()

    activated = runtime.persona.handle_text("JARVIS, activa modo UTRON")
    assert activated["state"]["mode"] == "utron"
    assert activated["state"]["visible_name"] == "UTRON"
    assert activated["state"]["theme"] == "red"
    assert activated["safety"]["approvals_bypassed"] is False
    assert "aprobaciones siguen intactas" in activated["response"]

    formatted = runtime.persona.format_response("Voy a preparar la vista previa.")
    assert formatted.startswith("UTRON:")
    assert "no voy a saltarme aprobaciones" in formatted

    safe_abuse = runtime.persona.format_response("David eres idiota")
    assert "No voy a insultar a David" in safe_abuse

    deactivated = runtime.persona.handle_text("desactiva UTRON")
    assert deactivated["state"]["mode"] == "jarvis"
    assert deactivated["state"]["visible_name"] == "JARVIS"


def test_voice_provider_architecture_and_model_router_do_not_spend_or_leak_keys(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-openrouter-secret-value")
    monkeypatch.setenv("JARVIS_PREMIUM_TTS_API_KEY", "voice-secret-value")
    runtime = Phase10HandsFreeRuntimePersonaApiRouter(monthly_budget_eur=30.0, spent_eur=2.0)

    voice = runtime.voice_providers.status(runtime.persona.state)
    assert voice["state"]["selected_provider"] == "browser_speech_synthesis"
    assert voice["state"]["external_call_performed"] is False
    assert voice["providers"]["premium_api_voice"]["paid_usage_requires_approval"] is True

    status = runtime.model_router.status()
    serialized = json.dumps(status)
    assert status["state"]["monthly_budget_eur"] == 30.0
    assert status["providers"]["openrouter"]["configured"] is True
    assert "sk-openrouter-secret-value" not in serialized
    assert "voice-secret-value" not in json.dumps(voice)

    simple = runtime.model_router.decide(task_type="simple_chat")
    assert simple["selected_provider"] == "local"
    assert simple["estimated_cost_eur"] == 0.0

    expensive = runtime.model_router.decide(
        task_type="code",
        quality_required="high",
        estimated_input_tokens=800_000,
        estimated_output_tokens=400_000,
    )
    assert expensive["selected_provider"] == "openrouter"
    assert expensive["requires_approval"] is True
    assert expensive["budget_remaining_eur"] == 28.0
    assert expensive["external_call_performed"] is False


def test_phase_10_api_dashboard_events_and_frontend_contract(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-do-not-leak")
    app = create_app(
        adapter_factory=lambda: pytest.fail("legacy Hermes adapter must not be called"),
        hermes_runtime_adapter_factory=lambda _authorize: pytest.fail("Hermes runtime bridge must not be called"),
    )
    route_paths = {route.path for route in app.routes}

    for path in (
        "/mark-3/phase-10/status",
        "/mark-3/phase-10/wake/preview",
        "/mark-3/phase-10/voice-ui/intent",
        "/mark-3/phase-10/app-launcher/prepare",
        "/mark-3/phase-10/browser-intent/prepare",
        "/mark-3/phase-10/approval/start",
        "/mark-3/phase-10/approval/confirm",
        "/mark-3/phase-10/persona/status",
        "/mark-3/phase-10/voice-providers/status",
        "/mark-3/model-router/status",
        "/mark-3/model-router/decision",
    ):
        assert path in route_paths

    phase_10 = _route(app, "/mark-3/phase-10/status").endpoint()
    assert phase_10["security_gates"]["jarvis_governs"] is True
    assert phase_10["security_gates"]["frontend_direct_hermes_allowed"] is False
    assert phase_10["security_gates"]["wake_phrase_can_approve"] is False
    assert phase_10["real_vs_readiness"]["app_launch"] == "prepared_governed_intent_no_fake_open"

    wake = _route(app, "/mark-3/phase-10/wake/preview", "POST").endpoint(
        Mark3Phase10TextRequest(text="Hola JARVIS", confidence=0.99)
    )
    assert wake["should_request_local_controller_open_jarvis"] is True

    voice = _route(app, "/mark-3/phase-10/voice-ui/intent", "POST").endpoint(
        Mark3Phase10TextRequest(text="abre la cámara")
    )
    assert voice["requires_exact_phrase"] is True

    app_intent = _route(app, "/mark-3/phase-10/app-launcher/prepare", "POST").endpoint(
        Mark3Phase10AppLaunchRequest(app_name="Spotify")
    )
    assert app_intent["executed"] is False

    approval = _route(app, "/mark-3/phase-10/approval/start", "POST").endpoint(
        Mark3Phase10ApprovalStartRequest(action="abrir terminal", session_id="s1")
    )
    approved = _route(app, "/mark-3/phase-10/approval/confirm", "POST").endpoint(
        Mark3Phase10ApprovalConfirmRequest(
            approval_id=approval["approval_id"],
            phrase=PHASE_10_EXACT_APPROVAL_PHRASE,
            session_id="s1",
        )
    )
    assert approved["approved"] is True
    assert approved["executed"] is False

    decision = _route(app, "/mark-3/model-router/decision", "POST").endpoint(
        Mark3ModelRouterDecisionRequest(task_type="simple_chat")
    )
    assert decision["selected_provider"] == "local"

    dashboard = build_mark_3_dashboard_status(
        app_state=app.state,
        route_paths=(route.path for route in app.routes),
        generated_at="2026-06-20T00:00:00+00:00",
    )
    assert dashboard["phase_10_status"]["schema_version"] == "jarvis.phase_10_hands_free_runtime_persona_api_brain_router.v1"
    assert dashboard["model_router"]["state"]["monthly_budget_eur"] == 30.0
    assert "sk-do-not-leak" not in json.dumps(dashboard)

    snapshot = build_jarvis_event_snapshot(
        dashboard_status=dashboard,
        generated_at="2026-06-20T00:00:00+00:00",
    )
    event_types = {event["event_type"] for event in snapshot["events"]}
    assert {"phase_10_state", "persona_state", "model_router_state", "voice_ui_intent_state", "app_launcher_state", "browser_intent_state"} <= event_types
    assert snapshot["stream"]["no_secrets"] is True

    frontend = _frontend_source()
    for expected in (
        "/mark-3/phase-10/voice-ui/intent",
        "/mark-3/model-router/decision",
        "pendingSensitiveUiAction",
        "confirmo y autorizo",
        "data-persona-mode",
        "data-orb-theme",
        "UTRON",
        "suppressSpeech",
        "isStopVoicePhrase",
        "startCameraPreview",
        "startRecording",
    ):
        assert expected in frontend
    for forbidden in ("HermesRuntimeAdapter", "dispatchHermes", 'fetchJSON("/execute"', 'fetchJSON("/jarvis/execute"'):
        assert forbidden not in frontend
