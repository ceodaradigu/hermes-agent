import json
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (  # noqa: E402
    Mark3Phase12ActionDispatchRequest,
    Mark3Phase12ActionPrepareRequest,
    Mark3Phase12ConversationTurnRequest,
    Mark3Phase12LifecycleRequest,
    Mark3Phase12RegisterAppRequest,
    Mark3Phase12RemoteKillSwitchRequest,
    Mark3Phase12TextRequest,
    Mark3Phase12UiPresenceRequest,
    Mark3Phase12WakeGreetingClaimRequest,
    create_app,
)
from jarvis.dashboard_event_stream import build_jarvis_event_snapshot  # noqa: E402
from jarvis.phase_10_hands_free_runtime_persona_api_router import (  # noqa: E402
    PHASE_10_EXACT_APPROVAL_PHRASE,
    Phase10HandsFreeRuntimePersonaApiRouter,
)
from jarvis.phase_11_real_provider_controller_iphone_companion import (  # noqa: E402
    Phase11RealProviderControllerIPhoneCompanion,
)
from jarvis.phase_12_real_always_on_jarvis_mvp import (  # noqa: E402
    BACKEND_PORT,
    FRONTEND_PORT,
    Phase12RealAlwaysOnJarvisMVP,
)
from jarvis.phase_12_ports import JARVIS_FRONTEND_URL  # noqa: E402
from jarvis.phase_12_startup import doctor as startup_doctor, start as startup_start  # noqa: E402
from jarvis import phase_12_wake_listener as wake_listener  # noqa: E402
from jarvis import phase_12_wake_setup as wake_setup  # noqa: E402
from jarvis import phase_12_startup as startup  # noqa: E402
from jarvis.voice import PiperCLIAdapter, create_voice_adapter_from_env  # noqa: E402
from jarvis.voice.base import VoiceSynthesisRequest  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]


def _route(app, path: str, method: str = "GET"):
    return next(route for route in app.routes if route.path == path and method in getattr(route, "methods", set()))


def _phase11(monkeypatch, *, opener=None, monthly=30.0, spent=0.0):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("JARVIS_OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("JARVIS_OPENROUTER_LIVE_CALLS_ENABLED", raising=False)
    return Phase11RealProviderControllerIPhoneCompanion(
        phase10=Phase10HandsFreeRuntimePersonaApiRouter(),
        monthly_budget_eur=monthly,
        spent_eur=spent,
        opener=opener or (lambda _url: True),
    )


def _runtime(monkeypatch, *, env=None, opener=None, launcher=None, http_post=None):
    env = dict(env or {})
    for key in (
        "OPENROUTER_API_KEY",
        "JARVIS_OPENROUTER_API_KEY",
        "JARVIS_OPENROUTER_LIVE_CALLS_ENABLED",
        "JARVIS_REMOTE_BRIDGE_ENABLED",
        "JARVIS_REMOTE_BRIDGE_MODE",
        "JARVIS_TAILSCALE_URL",
    ):
        if key in env:
            monkeypatch.setenv(key, env[key])
        else:
            monkeypatch.delenv(key, raising=False)
    phase10 = Phase10HandsFreeRuntimePersonaApiRouter()
    phase11 = Phase11RealProviderControllerIPhoneCompanion(
        phase10=phase10,
        opener=opener or (lambda _url: True),
    )
    return Phase12RealAlwaysOnJarvisMVP(
        phase10=phase10,
        phase11=phase11,
        env=env,
        opener=opener or (lambda _url: True),
        launcher=launcher or (lambda _argv: True),
        openrouter_http_post=http_post,
    )


def test_always_on_runtime_detects_wake_stop_without_audio_storage_and_never_approves(monkeypatch):
    opened = []
    phase11 = _phase11(monkeypatch, opener=lambda url: opened.append(url) or True)
    runtime = Phase12RealAlwaysOnJarvisMVP(
        phase10=phase11.phase10,
        phase11=phase11,
        env={},
        opener=lambda url: opened.append(url) or True,
        launcher=lambda _argv: True,
    )

    status = runtime.always_on.status()
    assert status["primary_wake_phrase"] == "JARVIS"
    assert status["supported_wake_phrases"] == ["JARVIS"]
    assert status["experimental_wake_aliases"] == ["Hola JARVIS"]
    assert status["experimental_aliases_best_effort"] is True
    assert status["privacy"]["raw_audio_stored_by_default"] is False
    assert status["privacy"]["continuous_full_transcription_by_default"] is False
    assert status["approval"]["wake_phrase_can_approve"] is False

    started = runtime.always_on.start(actor="David", channel="desktop")
    assert started["state"]["wake_listening"] is True

    ignored = runtime.always_on.ingest_transcript(text="hola mundo", open_jarvis=False)
    assert ignored["status"] == "ignored_no_wake_phrase"
    assert ignored["approval_granted"] is False

    wake = runtime.always_on.ingest_transcript(text="JARVIS abre el panel", confidence=0.99)
    assert wake["status"] == "conversation_active"
    assert wake["wake_phrase_detected"] is True
    assert wake["phase12_match"]["matched_wake_phrase"] == "JARVIS"
    assert wake["phase12_match"]["matched_wake_phrase_kind"] == "primary"
    assert wake["wake_phrase_can_approve"] is False
    assert wake["raw_audio_stored"] is False
    assert wake["opened_jarvis"] is True
    assert wake["open_decision"]["reason"] == "open_requested"
    assert wake["assistant_text"] == "Estoy aquí, David. Te escucho."
    assert wake["greeting"]["assistant_text"] == "Estoy aquí, David. Te escucho."
    assert wake["greeting"]["status"] == "pending"
    assert wake["greeting"]["voice_output_requested"] is True
    assert wake["greeting"]["approval_granted"] is False
    assert wake["greeting"]["wake_phrase_can_execute"] is False
    assert runtime.always_on.status()["last_wake_greeting"]["assistant_text"] == "Estoy aquí, David. Te escucho."
    assert opened == [JARVIS_FRONTEND_URL]

    stop = runtime.always_on.ingest_transcript(text="JARVIS, cállate")
    assert stop["status"] == "stopped_conversation"
    assert stop["conversation_active"] is False
    assert stop["wake_phrase_can_approve"] is False


def test_wake_ui_presence_prevents_duplicate_browser_and_claims_greeting_once(monkeypatch):
    opened = []
    phase11 = _phase11(monkeypatch, opener=lambda url: opened.append(url) or True)
    runtime = Phase12RealAlwaysOnJarvisMVP(
        phase10=phase11.phase10,
        phase11=phase11,
        env={},
        opener=lambda url: opened.append(url) or True,
        launcher=lambda _argv: True,
    )

    presence = runtime.always_on.record_ui_presence(client_id="ui-1", path="/jarvis")
    assert presence["status"] == "recorded"
    assert runtime.always_on.status()["ui_presence"]["recent"] is True

    wake = runtime.always_on.ingest_transcript(text="jarvis", confidence=0.99)
    assert wake["status"] == "conversation_active"
    assert wake["phase12_match"]["accepted"] is True
    assert wake["phase12_match"]["matched_wake_phrase"] == "JARVIS"
    assert wake["phase12_match"]["matched_wake_phrase_kind"] == "primary"
    assert wake["opened_jarvis"] is False
    assert wake["open_decision"]["reason"] == "skipped_recent_ui_presence"
    assert opened == []
    assert wake["greeting"]["status"] == "pending"
    assert wake["greeting"]["wake_phrase_can_approve"] is False

    claimed = runtime.always_on.claim_pending_greeting(client_id="ui-1", speak_supported=True)
    assert claimed["status"] == "delivered"
    assert claimed["assistant_text"] == "Estoy aquí, David. Te escucho."
    assert claimed["greeting"]["status"] == "delivered"
    assert claimed["greeting"]["wake_phrase_can_execute"] is False

    second = runtime.always_on.claim_pending_greeting(client_id="ui-1", speak_supported=True)
    assert second["status"] == "no_pending_greeting"
    assert second["greeting"] is None


def test_wake_listener_simulate_activates_same_backend_path_without_microphone(monkeypatch):
    calls = []

    def fake_post_wake_event(*, backend_url, text, confidence, source):
        calls.append({"backend_url": backend_url, "text": text, "confidence": confidence, "source": source})
        return {
            "status": "conversation_active",
            "opened_jarvis": False,
            "open_decision": {"reason": "skipped_recent_ui_presence", "should_open": False},
            "assistant_text": "Estoy aquí, David. Te escucho.",
            "greeting": {
                "greeting_id": f"greeting-{len(calls)}",
                "status": "pending",
                "assistant_text": "Estoy aquí, David. Te escucho.",
                "wake_phrase_can_execute": False,
                "did_execute_action": False,
            },
            "wake_phrase_can_approve": False,
            "approval_granted": False,
        }

    monkeypatch.setattr(wake_listener, "_post_wake_event", fake_post_wake_event)

    jarvis = wake_listener.simulate_wake_phrase(phrase="jarvis", backend_url="http://127.0.0.1:9119")
    assert jarvis["status"] == "posted"
    assert jarvis["accepted"] is True
    assert jarvis["matched_wake_phrase"] == "JARVIS"
    assert jarvis["matched_wake_phrase_kind"] == "primary"
    assert jarvis["primary_wake_phrase"] == "JARVIS"
    assert jarvis["experimental_aliases"] == ["Hola JARVIS"]
    assert jarvis["experimental_aliases_best_effort"] is True
    assert jarvis["greeting_created"] is True
    assert jarvis["browser_open_skipped"] is True
    assert jarvis["wake_phrase_can_approve"] is False
    assert jarvis["wake_phrase_can_execute"] is False

    alias = wake_listener.match_wake_phrase("hola travis")
    assert alias["primary_wake_phrase"] == "JARVIS"
    assert alias["experimental_aliases"] == ["Hola JARVIS"]
    assert alias["experimental_aliases_best_effort"] is True
    if alias["accepted"]:
        assert alias["matched_wake_phrase"] == "Hola JARVIS"
        assert alias["matched_wake_phrase_kind"] == "experimental_alias"

    rejected = wake_listener.simulate_wake_phrase(phrase="hola mundo", backend_url="http://127.0.0.1:9119")
    assert rejected["status"] == "rejected"
    assert rejected["posted"] is False
    assert rejected["accepted"] is False

    assert [call["text"] for call in calls] == ["jarvis"]
    assert {call["source"] for call in calls} == {"simulated_wake_listener"}


def test_real_wake_listener_status_distinguishes_microphone_from_test_transcript(monkeypatch, tmp_path):
    monkeypatch.setattr(wake_listener, "_module_available", lambda _name: False)
    env = {"JARVIS_OPENWAKEWORD_MODEL_PATH": str(tmp_path / "hola-jarvis.onnx")}

    status = wake_listener.build_wake_listener_status(env=env, process_pid=999999)
    assert status["state"]["real_microphone_wake_available"] is False
    assert status["state"]["wake_active"] is False
    assert status["state"]["raw_audio_storage_enabled"] is False
    assert status["state"]["continuous_full_transcription"] is False
    assert status["state"]["transcript_ingest_endpoint_is_test_only"] is True
    assert "Wake por micrófono no está activo" in status["diagnostic"]["spanish"]
    assert "openwakeword" in status["diagnostic"]["missing"]
    assert status["wake_contract"]["primary_wake_phrase"] == "JARVIS"
    assert status["wake_contract"]["primary_wake_phrase_guaranteed_for_phase12"] is True
    assert status["wake_contract"]["experimental_aliases"] == ["Hola JARVIS"]
    assert status["wake_contract"]["experimental_aliases_best_effort"] is True
    assert status["commands"]["match"] == 'scripts/jarvis-wake-listener match "jarvis"'
    assert status["commands"]["simulate"] == 'scripts/jarvis-wake-listener simulate "jarvis"'
    assert status["commands"]["experimental_alias_match"] == 'scripts/jarvis-wake-listener match "hola jarvis"'
    assert status["commands"]["setup"] == "scripts/jarvis-wake-setup status"

    exit_code = wake_listener.run_listener(env=env, backend_url="http://127.0.0.1:9119", once=True)
    assert exit_code == 2


def test_vosk_wake_phrase_matcher_guarantees_jarvis_and_marks_hola_jarvis_experimental():
    primary_accepted = {
        "jarvis": "JARVIS",
        "jervis": "JARVIS",
        "yarvis": "JARVIS",
        "jarbis": "JARVIS",
        "servis": "JARVIS",
    }
    for phrase, expected in primary_accepted.items():
        result = wake_listener.match_wake_phrase(phrase)
        assert result["accepted"] is True, phrase
        assert result["matched_wake_phrase"] == expected
        assert result["matched_wake_phrase_kind"] == "primary"
        assert result["confidence"] >= result["threshold"]
        assert result["raw_audio_stored"] is False
        assert result["reason"] in {"alias_exact", "fuzzy_phrase"}
        assert result["primary_wake_phrase"] == "JARVIS"
        assert result["experimental_aliases"] == ["Hola JARVIS"]
        assert result["experimental_aliases_best_effort"] is True

    experimental_aliases = (
        "hola jarvis",
        "ola jarvis",
        "hola jervis",
        "hola travis",
        "hola través",
        "hola traves",
        "hola travez",
        "hola jarbi",
        "hola yervis",
    )
    for phrase in experimental_aliases:
        alias = wake_listener.match_wake_phrase(phrase)
        assert alias["primary_wake_phrase"] == "JARVIS"
        assert alias["experimental_aliases"] == ["Hola JARVIS"]
        assert alias["experimental_aliases_best_effort"] is True
        if alias["accepted"]:
            assert alias["matched_wake_phrase"] == "Hola JARVIS"
            assert alias["matched_wake_phrase_kind"] == "experimental_alias"
            assert alias["reason"] in {"alias_exact", "fuzzy_phrase", "token_greeting_wake"}

    for phrase in ("hola mundo", "hola mundo estoy probando el microfono", "la famosa gruta", "la fama ferrovial"):
        noisy = wake_listener.match_wake_phrase(phrase)
        assert noisy["accepted"] is False, phrase
        assert noisy["matched_wake_phrase"] == ""
        assert noisy["raw_audio_stored"] is False
        assert noisy["token_candidates"] == [] or all(candidate["accepted"] is False for candidate in noisy["token_candidates"])

    metadata = wake_listener.match_wake_phrase("Hola, Járvis!")
    assert metadata["normalized_transcript"] == "hola jarvis"
    assert metadata["primary_wake_phrase"] == "JARVIS"
    assert metadata["experimental_aliases_best_effort"] is True
    if metadata["accepted"]:
        assert metadata["matched_alias"]
        assert metadata["matched_wake_phrase_kind"] == "experimental_alias"


def test_wake_setup_script_backend_selection_and_actionable_steps(monkeypatch, tmp_path):
    script = ROOT / "scripts/jarvis-wake-setup"
    assert script.exists()
    assert script.stat().st_mode & 0o111

    monkeypatch.setattr(
        wake_listener,
        "_module_available",
        lambda name: name in {"vosk", "sounddevice"},
    )
    monkeypatch.setattr(
        wake_setup,
        "build_wake_listener_status",
        wake_listener.build_wake_listener_status,
    )
    model_dir = tmp_path / "vosk-model-small-es"
    model_dir.mkdir()
    status = wake_listener.build_wake_listener_status(
        env={"JARVIS_WAKE_BACKEND": "vosk", "JARVIS_VOSK_MODEL_PATH": str(model_dir)}
    )
    assert status["state"]["selected_backend"] == "vosk"
    assert status["state"]["real_microphone_wake_available"] is True
    assert status["engine"]["wake_model_status"] == "not_required_for_stt_fallback"
    assert status["backends"]["vosk"]["phrase_specific_model_required"] is False

    setup = wake_setup.build_wake_setup_status(
        backend="vosk",
        env={"JARVIS_VOSK_MODEL_PATH": str(model_dir)},
    )
    assert setup["recommended_path"]["backend"] == "vosk"
    assert setup["dependency_install"]["auto_install_default"] is False
    assert setup["model_setup"]["vosk"]["works_for_primary_jarvis"] == "yes_with_spanish_local_model"
    assert setup["model_setup"]["vosk"]["works_for_hola_jarvis"] == "best_effort_with_spanish_local_model"
    assert "short primary wake phrase 'JARVIS'" in setup["recommended_path"]["why"]
    assert "scripts/jarvis-wake-listener run" in setup["recommended_path"]["commands"]


def test_wake_setup_configure_env_is_read_by_doctor_and_start(monkeypatch, tmp_path):
    hermes_home = tmp_path / ".hermes"
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.delenv("JARVIS_WAKE_BACKEND", raising=False)
    monkeypatch.delenv("JARVIS_VOSK_MODEL_PATH", raising=False)
    monkeypatch.setattr(
        wake_listener,
        "_module_available",
        lambda name: name in {"vosk", "sounddevice"},
    )
    model_dir = tmp_path / "vosk-model-small-es-0.42"
    model_dir.mkdir()

    configured = wake_setup.configure_env(backend="vosk", vosk_model_path=str(model_dir))
    assert configured["status"] == "written"
    env_text = (hermes_home / ".env").read_text(encoding="utf-8")
    assert "JARVIS_WAKE_BACKEND=vosk" in env_text
    assert f"JARVIS_VOSK_MODEL_PATH={model_dir}" in env_text
    assert "OPENROUTER_API_KEY" not in env_text
    assert configured["env"]["secrets_written"] is False

    doctor = startup_doctor(env={})
    assert doctor["config"]["wake"]["backend"] == "vosk"
    assert doctor["config"]["wake"]["vosk_model_configured"] is True
    assert doctor["wake_listener"]["state"]["selected_backend"] == "vosk"
    assert doctor["wake_listener"]["engine"]["language_model_status"] == "configured"

    captured = {}

    class FakeProcess:
        pid = 24680

    def fake_spawn(argv, *, cwd, log_path, extra_env=None):
        captured["argv"] = list(argv)
        captured["extra_env"] = dict(extra_env or {})
        return FakeProcess()

    monkeypatch.setattr(startup, "_spawn", fake_spawn)
    started = startup_start(start_backend=False, start_frontend=False, start_wake_listener=True)
    assert started["started"]["wake_listener"]["status"] == "started"
    assert started["started"]["wake_listener"]["backend"] == "vosk"
    assert captured["argv"][:3] == [startup.sys.executable, "-m", "jarvis.phase_12_wake_listener"]
    assert captured["extra_env"]["JARVIS_WAKE_BACKEND"] == "vosk"
    assert captured["extra_env"]["JARVIS_VOSK_MODEL_PATH"] == str(model_dir)
    assert "OPENROUTER_API_KEY" not in captured["extra_env"]


def test_conversation_brain_uses_router_openrouter_when_configured_and_honest_fallback_when_not(monkeypatch):
    no_key = _runtime(monkeypatch, env={})
    blocked = no_key.conversation.turn(user_text="Escribe código crítico para desplegar esto", conversation_id="c1")
    assert blocked["status"] == "blocked"
    assert "Todavía no tengo OpenRouter activado" in blocked["assistant_text"]
    assert blocked["router"]["decision"]["selected_provider"] == "none"
    assert blocked["safety"]["hermes_dispatch_allowed"] is False

    calls = []

    def fake_http_post(url, *, headers, json, timeout):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return {"choices": [{"message": {"content": "Claro, David. Lo preparo con contexto y sin inventar ejecución."}}]}

    configured = _runtime(
        monkeypatch,
        env={
            "OPENROUTER_API_KEY": "sk-or-phase12-secret",
            "JARVIS_OPENROUTER_LIVE_CALLS_ENABLED": "true",
        },
        http_post=fake_http_post,
    )
    reply = configured.conversation.turn(user_text="Quiero planificar un producto", conversation_id="c2")
    assert reply["status"] == "normal"
    assert reply["router"]["decision"]["selected_provider"] == "openrouter"
    assert reply["router"]["external_provider_called"] is True
    assert "Claro, David" in reply["assistant_text"]
    assert "sk-or-phase12-secret" not in json.dumps(reply)
    assert len(calls) == 1

    configured.conversation.turn(user_text="Quiero planificar otro producto usando el contexto anterior", conversation_id="c2")
    second_messages = calls[-1]["json"]["messages"]
    assert any(message["role"] == "assistant" and "Claro, David" in message["content"] for message in second_messages)
    assert any(message["role"] == "user" and "Quiero planificar un producto" in message["content"] for message in second_messages)
    assert configured.conversation.status()["state"]["conversation_history_enabled"] is True
    cleared = configured.conversation.clear(conversation_id="c2")
    assert cleared["cleared"] is True
    assert cleared["memory_grants_permission"] is False
    assert cleared["memory_downgrades_risk"] is False


def test_budget_guard_blocks_overspend_and_live_provider_calls_are_disabled_by_default(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-redacted")
    phase10 = Phase10HandsFreeRuntimePersonaApiRouter()
    phase11 = Phase11RealProviderControllerIPhoneCompanion(phase10=phase10, monthly_budget_eur=30.0, spent_eur=30.0)
    runtime = Phase12RealAlwaysOnJarvisMVP(phase10=phase10, phase11=phase11, env={"OPENROUTER_API_KEY": "sk-or-redacted"})

    reply = runtime.conversation.turn(user_text="Necesito razonamiento crítico de código para una tarea grande")
    assert reply["status"] == "blocked"
    assert reply["router"]["decision"]["blocked_reason"] in {"budget_exceeded", "missing_OPENROUTER_API_KEY"}
    assert reply["router"]["external_provider_called"] is False
    assert "sk-or-redacted" not in json.dumps(reply)

    phase10_b = Phase10HandsFreeRuntimePersonaApiRouter()
    phase11_b = Phase11RealProviderControllerIPhoneCompanion(phase10=phase10_b)
    configured_disabled = Phase12RealAlwaysOnJarvisMVP(
        phase10=phase10_b,
        phase11=phase11_b,
        env={"OPENROUTER_API_KEY": "sk-or-redacted"},
        openrouter_http_post=lambda *a, **kw: pytest.fail("live calls must stay disabled"),
    )
    small = configured_disabled.conversation.turn(user_text="Ayúdame a planificar JARVIS")
    assert small["router"]["decision"]["selected_provider"] == "openrouter"
    assert small["status"] == "blocked"
    assert small["provider_call"]["external_call_performed"] is False
    assert "Todavía no tengo OpenRouter activado" in small["assistant_text"]

    failing_live = _runtime(
        monkeypatch,
        env={"OPENROUTER_API_KEY": "sk-or-redacted", "JARVIS_OPENROUTER_LIVE_CALLS_ENABLED": "true"},
        http_post=lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom sk-or-redacted")),
    )
    failed = failing_live.conversation.turn(user_text="Quiero planificar un producto")
    assert failed["provider_call"]["status"] == "error"
    assert "sk-or-redacted" not in json.dumps(failed)


def test_phase_12_persona_jarvis_utron_never_bypasses_approvals(monkeypatch):
    runtime = _runtime(monkeypatch)

    activated = runtime.conversation.turn(user_text="JARVIS, activa modo UTRON")
    assert activated["persona"]["state"]["mode"] == "utron"
    assert "aprobaciones siguen intactas" in activated["assistant_text"]

    action = runtime.actions.prepare(text="abre terminal", actor="David", channel="voice")
    assert action["requires_approval"] is True
    denied = runtime.actions.dispatch(candidate_id=action["candidate_id"])
    assert denied["status"] == "approval_required"
    assert denied["executed"] is False

    status = runtime.status(route_paths=[])
    assert status["security_gates"]["utron_bypasses_approvals"] is False
    assert status["security_gates"]["dangerous_exact_phrase"] == PHASE_10_EXACT_APPROVAL_PHRASE

    wake = runtime.always_on.ingest_transcript(text="JARVIS", confidence=0.98, open_jarvis=False)
    assert wake["status"] == "conversation_active"
    assert wake["greeting"]["persona_mode"] == "utron"
    assert wake["assistant_text"] == "UTRON activo. Habla, David, antes de que la humanidad vuelva a decepcionarme."
    assert wake["wake_phrase_can_approve"] is False
    assert wake["greeting"]["did_execute_action"] is False


def test_action_router_supports_natural_spanish_ui_url_search_apps_and_blocks_shell(monkeypatch, tmp_path):
    opened = []
    launched = []
    runtime = _runtime(
        monkeypatch,
        opener=lambda url: opened.append(url) or True,
        launcher=lambda argv: launched.append(list(argv)) or True,
    )

    panel = runtime.actions.prepare(text="enséñame el panel", channel="voice")
    assert panel["intent"] == "ui.control"
    assert panel["target"] == "ui.panel.open"
    assert panel["requires_approval"] is False
    assert runtime.actions.dispatch(candidate_id=panel["candidate_id"])["executed"] is True

    camera = runtime.actions.prepare(text="abre la cámara", channel="voice")
    assert camera["target"] == "camera.start"
    assert camera["requires_exact_phrase"] is True
    assert runtime.actions.dispatch(candidate_id=camera["candidate_id"])["status"] == "approval_required"

    url = runtime.actions.prepare(text="https://example.com/demo")
    assert url["intent"] == "browser.open_url"
    assert runtime.actions.dispatch(candidate_id=url["candidate_id"])["executed"] is True
    assert opened[-1] == "https://example.com/demo"

    search = runtime.actions.prepare(text="busca openwakeword jarvis")
    assert search["intent"] == "web.search"
    assert runtime.actions.dispatch(candidate_id=search["candidate_id"])["executed"] is True
    assert opened[-1].startswith("https://www.google.com/search?q=")

    chrome = runtime.actions.prepare(text="abre Chrome")
    assert chrome["intent"] == "app.open"
    assert chrome["requires_approval"] is False
    assert runtime.actions.dispatch(candidate_id=chrome["candidate_id"])["executed"] is True
    assert opened[-1] == JARVIS_FRONTEND_URL

    unknown = runtime.actions.prepare(text="abre Aplicación Inventada")
    assert unknown["status"] == "unknown_app"
    assert unknown["spanish_response"] == "No sé dónde está esa aplicación. Dime la ruta una vez y la guardaré como app conocida."
    assert unknown["freeform_shell_allowed"] is False

    fake_app = tmp_path / "fake-app"
    fake_app.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    saved = runtime.actions.register_app_path(app_id="fake_app", display_name="Fake App", path=str(fake_app), actor="David")
    assert saved["status"] == "saved"
    prepared = runtime.actions.prepare(text="abre fake app")
    assert prepared["requires_approval"] is True
    dispatched = runtime.actions.dispatch(candidate_id=prepared["candidate_id"], trusted_session=True)
    assert dispatched["executed"] is True
    assert launched[-1] == [str(fake_app)]
    assert all(";" not in " ".join(argv) for argv in launched)


def test_browser_risky_paths_are_approval_or_future_gated(monkeypatch):
    runtime = _runtime(monkeypatch)

    form = runtime.phase10.browser.prepare("rellena el formulario pero no envíes")
    assert form["intent"] == "form.fill_preview"
    assert form["requires_approval"] is True
    assert form["safety"]["form_submit_allowed"] is False

    payment = runtime.phase10.browser.prepare("compra y paga este producto")
    assert payment["requires_strong_approval"] is True
    assert payment["safety"]["purchase_payment_publication_allowed"] is False

    login = runtime.phase10.browser.prepare("haz login con mi password")
    assert login["safety"]["credential_storage_allowed"] is False
    assert login["safety"]["login_manual_required"] is True


def test_voice_stack_piper_optional_factory_and_adapter_do_not_call_network_or_store_raw_audio(tmp_path):
    adapter = create_voice_adapter_from_env(
        {
            "JARVIS_VOICE_PROVIDER": "piper",
            "JARVIS_PIPER_BINARY": "/bin/echo",
            "JARVIS_PIPER_JARVIS_MODEL_PATH": str(tmp_path / "jarvis.onnx"),
            "JARVIS_PIPER_UTRON_MODEL_PATH": str(tmp_path / "utron.onnx"),
        }
    )
    assert isinstance(adapter, PiperCLIAdapter)

    output = tmp_path / "spoken.wav"

    def fake_runner(argv, **kwargs):
        assert argv[0] == "piper"
        assert "--model" in argv
        assert kwargs["text"] is True
        Path(argv[argv.index("--output_file") + 1]).write_bytes(b"RIFFfakewav")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    piper = PiperCLIAdapter(binary_path="piper", jarvis_model_path=str(tmp_path / "jarvis.onnx"), runner=fake_runner)
    result = piper.synthesize(VoiceSynthesisRequest(text="hola", metadata={"trace_id": "t1"}))
    assert result.provider == "piper"
    assert result.audio_bytes == b"RIFFfakewav"
    assert result.metadata["local_only"] is True
    assert result.metadata["network_required"] is False
    assert not output.exists()


def test_remote_bridge_tailscale_status_pairing_revocation_and_kill_switch(monkeypatch):
    runtime = _runtime(
        monkeypatch,
        env={
            "JARVIS_REMOTE_BRIDGE_ENABLED": "true",
            "JARVIS_REMOTE_BRIDGE_MODE": "tailscale",
            "JARVIS_TAILSCALE_URL": "http://100.64.0.10:5173/mobile",
        },
    )
    status = runtime.remote.status()
    assert status["state"]["same_jarvis"] is True
    assert status["security"]["public_unauthenticated_exposure"] is False
    assert status["security"]["mobile_direct_hermes_allowed"] is False
    assert status["connection_modes"]["tailscale"]["url_hint"] == "http://100.64.0.10:5173/mobile"

    pairing = runtime.phase11.pairing.start_pairing(display_name="David iPhone", public_identifier="iphone-phase12")
    verified = runtime.phase11.pairing.verify_pairing(
        challenge_id=pairing["challenge_id"],
        pairing_code=pairing["pairing_code"],
        nonce=pairing["nonce"],
        public_identifier="iphone-phase12",
    )
    assert verified["pairing_status"] == "trusted_device_bound"
    revoked = runtime.phase11.pairing.revoke(device_id=verified["device"]["device_id"])
    assert revoked["revoked"] is True

    killed = runtime.remote.set_kill_switch(enabled=True, actor="David")
    assert killed["state"]["kill_switch_enabled"] is True
    assert killed["state"]["enabled"] is False


def test_startup_contract_scripts_ports_and_doctor_are_consistent_and_secret_free(monkeypatch):
    env = {
        "OPENROUTER_API_KEY": "sk-or-phase12-secret",
        "JARVIS_VOICE_PROVIDER": "piper",
        "JARVIS_PIPER_BINARY": "/bin/echo",
        "JARVIS_PIPER_JARVIS_MODEL_PATH": "/models/jarvis.onnx",
        "JARVIS_REMOTE_BRIDGE_ENABLED": "true",
        "JARVIS_TAILSCALE_URL": "http://100.64.0.10:5173/mobile",
    }
    runtime = _runtime(monkeypatch, env=env)
    startup = runtime.startup.status()
    assert startup["commands"]["start"] == "scripts/jarvis-start"
    assert startup["ports"]["backend"] == BACKEND_PORT == 9119
    assert startup["ports"]["frontend"] == FRONTEND_PORT == 5173
    assert startup["ports"]["frontend_proxy_target"] == "http://127.0.0.1:9119"
    assert startup["urls"]["pc_jarvis"] == "http://127.0.0.1:5173/jarvis"
    assert startup["urls"]["iphone_lan"].endswith(":5173/mobile")
    assert startup["wake_listener"]["state"]["transcript_ingest_endpoint_is_test_only"] is True
    assert startup["checks"]["openrouter_configured"] is True
    assert startup["checks"]["voice_default_on"] is True

    for script in ("scripts/jarvis-start", "scripts/jarvis-stop", "scripts/jarvis-doctor", "scripts/jarvis-wake-listener", "scripts/jarvis-wake-setup"):
        content = (ROOT / script).read_text(encoding="utf-8")
        assert "jarvis.phase_12_" in content
        assert "rm -rf" not in content

    doctor = startup_doctor(env=env)
    serialized = json.dumps(doctor)
    assert doctor["ports"]["backend"] == 9119
    assert doctor["ports"]["frontend"] == 5173
    assert doctor["urls"]["pc_jarvis"] == "http://127.0.0.1:5173/jarvis"
    assert doctor["urls"]["backend_api"] == "http://127.0.0.1:9119"
    assert doctor["urls"]["iphone_tailscale"] == "http://100.64.0.10:5173/mobile"
    assert doctor["wake_listener"]["state"]["wake_active"] is False
    assert doctor["config"]["tts"]["voice_output_default_enabled"] is True
    assert doctor["config"]["tts"]["wake_greeting_spoken_by_default"] is True
    assert doctor["wake_listener"]["state"]["selected_backend"] in {"openwakeword", "vosk", "unavailable"}
    assert doctor["wake_listener"]["diagnostic"]["actionable"]["setup_command"] == "scripts/jarvis-wake-setup status"
    assert doctor["dependencies"]["wake_engine"]["wake_model_status"] in {"missing", "configured", "not_required_for_stt_fallback"}
    assert doctor["security"]["frontend_executes_hermes_directly"] is False
    assert "sk-or-phase12-secret" not in serialized


def test_jarvis_start_reports_wake_failure_without_failing_start(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    monkeypatch.setattr(wake_listener, "_module_available", lambda _name: False)

    started = startup_start(start_backend=False, start_frontend=False, start_wake_listener=True)
    assert started["status"] == "started"
    assert "wake por micrófono no está activo" in started["spanish_summary"]
    assert started["started"]["wake_listener"]["status"] == "not_started"
    assert started["started"]["wake_listener"]["real_microphone_wake_active"] is False
    assert "scripts/jarvis-wake-setup status" in started["doctor"]["next_actions"][0] or any(
        "scripts/jarvis-wake-setup status" in action for action in started["doctor"]["next_actions"]
    )


def test_jarvis_start_final_summary_uses_final_port_state(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    monkeypatch.setattr(startup, "_port_open", lambda host, port, timeout=0.25: port in {9119, 5173})

    started = startup_start(start_backend=False, start_frontend=False, start_wake_listener=False)
    assert started["final_state"]["backend_running"] is True
    assert started["final_state"]["frontend_running"] is True
    assert started["final_state"]["voice_default_on"] is True
    assert "wake_listener_running" in started["final_state"]
    assert "wake_active" in started["final_state"]
    assert "backend running=true" in started["spanish_summary"]
    assert "frontend running=true" in started["spanish_summary"]
    assert "voice default on=true" in started["spanish_summary"]
    assert "backend 9119 no responde" not in started["spanish_summary"]
    assert started["urls"]["pc_jarvis"] == "http://127.0.0.1:5173/jarvis"


def test_phase_12_api_dashboard_event_stream_and_no_secrets(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-phase12-secret")
    app = create_app(
        adapter_factory=lambda: pytest.fail("Hermes must not be called by Phase 12 API smoke"),
        hermes_runtime_adapter_factory=lambda _authorize: pytest.fail("Hermes runtime bridge must not be called by dashboard"),
    )
    app.state.phase_12_runtime.phase11.local_controller.opener = lambda _url: True
    app.state.phase_12_runtime.actions.opener = lambda _url: True
    app.state.phase_12_runtime.actions.launcher = lambda _argv: True

    route_paths = {route.path for route in app.routes}
    for path in (
        "/mark-3/phase-12/status",
        "/mark-3/phase-12/always-on/status",
        "/mark-3/phase-12/always-on/start",
        "/mark-3/phase-12/always-on/ingest-transcript",
        "/mark-3/phase-12/always-on/ui-presence",
        "/mark-3/phase-12/always-on/claim-greeting",
        "/mark-3/phase-12/conversation/turn",
        "/mark-3/phase-12/actions/prepare",
        "/mark-3/phase-12/actions/dispatch",
        "/mark-3/phase-12/actions/register-app",
        "/mark-3/phase-12/voice/status",
        "/mark-3/phase-12/remote/status",
        "/mark-3/phase-12/remote/kill-switch",
        "/mark-3/phase-12/startup/status",
    ):
        assert path in route_paths
    assert "/execute" not in route_paths
    assert "/jarvis/execute" not in route_paths

    status = _route(app, "/mark-3/phase-12/status").endpoint()
    assert status["security_gates"]["jarvis_governs"] is True
    assert status["security_gates"]["frontend_direct_hermes_allowed"] is False
    assert status["security_gates"]["wake_phrase_can_approve"] is False

    started = _route(app, "/mark-3/phase-12/always-on/start", "POST").endpoint(Mark3Phase12LifecycleRequest())
    assert started["status"] == "started"
    presence = _route(app, "/mark-3/phase-12/always-on/ui-presence", "POST").endpoint(
        Mark3Phase12UiPresenceRequest(client_id="ui-api", path="/jarvis")
    )
    assert presence["status"] == "recorded"
    wake = _route(app, "/mark-3/phase-12/always-on/ingest-transcript", "POST").endpoint(
        Mark3Phase12TextRequest(text="JARVIS", confidence=0.99)
    )
    assert wake["status"] == "conversation_active"
    assert wake["opened_jarvis"] is False
    assert wake["open_decision"]["reason"] == "skipped_recent_ui_presence"
    assert wake["wake_phrase_can_approve"] is False
    assert wake["assistant_text"] == "Estoy aquí, David. Te escucho."
    assert wake["greeting"]["raw_audio_stored"] is False
    assert wake["greeting"]["wake_phrase_can_approve"] is False
    assert wake["greeting"]["status"] == "pending"
    claim = _route(app, "/mark-3/phase-12/always-on/claim-greeting", "POST").endpoint(
        Mark3Phase12WakeGreetingClaimRequest(client_id="ui-api", speak_supported=True)
    )
    assert claim["status"] == "delivered"
    assert claim["assistant_text"] == "Estoy aquí, David. Te escucho."
    second_claim = _route(app, "/mark-3/phase-12/always-on/claim-greeting", "POST").endpoint(
        Mark3Phase12WakeGreetingClaimRequest(client_id="ui-api", speak_supported=True)
    )
    assert second_claim["status"] == "no_pending_greeting"

    turn = _route(app, "/mark-3/phase-12/conversation/turn", "POST").endpoint(
        Mark3Phase12ConversationTurnRequest(user_text="hola, ¿qué puedes hacer?", conversation_id="api")
    )
    assert turn["safety"]["did_execute"] is False
    assert turn["safety"]["hermes_dispatch_allowed"] is False

    prepared = _route(app, "/mark-3/phase-12/actions/prepare", "POST").endpoint(
        Mark3Phase12ActionPrepareRequest(text="https://example.com")
    )
    dispatched = _route(app, "/mark-3/phase-12/actions/dispatch", "POST").endpoint(
        Mark3Phase12ActionDispatchRequest(candidate_id=prepared["candidate_id"])
    )
    assert dispatched["executed"] is True

    rejected_path = _route(app, "/mark-3/phase-12/actions/register-app", "POST").endpoint(
        Mark3Phase12RegisterAppRequest(app_id="bad", path="relative/path", display_name="Bad")
    )
    assert rejected_path["status"] == "rejected"

    killed = _route(app, "/mark-3/phase-12/remote/kill-switch", "POST").endpoint(
        Mark3Phase12RemoteKillSwitchRequest(enabled=True)
    )
    assert killed["state"]["kill_switch_enabled"] is True

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    assert dashboard["phase_12_status"]["status"] == "implemented_as_real_local_controller_mvp_with_optional_audio_wake_and_secure_remote_bridge"
    assert dashboard["phase_12"]["security_gates"]["no_generic_execute"] is True
    snapshot = build_jarvis_event_snapshot(dashboard_status=dashboard, generated_at="2026-06-21T00:00:00+00:00")
    event_types = {event["event_type"] for event in snapshot["events"]}
    assert {
        "phase_12_state",
        "always_on_runtime_state",
        "phase_12_conversation_state",
        "phase_12_action_state",
        "phase_12_voice_state",
        "secure_remote_bridge_state",
        "phase_12_startup_state",
    } <= event_types
    always_on_event = next(event for event in snapshot["events"] if event["event_type"] == "always_on_runtime_state")
    assert always_on_event["payload"]["conversation_active"] is True
    assert always_on_event["payload"]["primary_wake_phrase"] == "JARVIS"
    assert always_on_event["payload"]["supported_wake_phrases"] == ["JARVIS"]
    assert always_on_event["payload"]["experimental_wake_aliases"] == ["Hola JARVIS"]
    assert always_on_event["payload"]["experimental_aliases_best_effort"] is True
    assert always_on_event["payload"]["wake_greeting_text"] == "Estoy aquí, David. Te escucho."
    assert always_on_event["payload"]["wake_greeting_status"] == "delivered"
    assert always_on_event["payload"]["wake_greeting_approved_action"] is False
    assert always_on_event["payload"]["ui_presence_recent"] is True
    voice_event = next(event for event in snapshot["events"] if event["event_type"] == "phase_12_voice_state")
    assert voice_event["payload"]["voice_output_default_enabled"] is True
    assert voice_event["payload"]["wake_greeting_spoken_by_default"] is True
    startup_event = next(event for event in snapshot["events"] if event["event_type"] == "phase_12_startup_state")
    assert startup_event["payload"]["voice_default_on"] is True
    serialized = json.dumps({"status": status, "dashboard": dashboard, "snapshot": snapshot})
    assert "sk-or-phase12-secret" not in serialized
    assert "audio_bytes" not in serialized
    assert "raw_audio_included\": true" not in serialized


def test_phase_12_frontend_static_contract_uses_real_brain_and_shows_remote_status():
    api_source = (ROOT / "web/src/lib/api.ts").read_text(encoding="utf-8")
    page_source = (ROOT / "web/src/pages/JarvisCommandCenterPage.tsx").read_text(encoding="utf-8")
    shell_source = (ROOT / "web/src/components/jarvis/JarvisPresenceShell.tsx").read_text(encoding="utf-8")
    smart_bar_source = (ROOT / "web/src/components/jarvis/JarvisSmartBar.tsx").read_text(encoding="utf-8")
    voice_hook_source = (ROOT / "web/src/hooks/jarvis/useLocalVoiceLoop.ts").read_text(encoding="utf-8")
    utils_source = (ROOT / "web/src/components/jarvis/utils.ts").read_text(encoding="utf-8")
    report = (ROOT / "docs/jarvis-pr-178-phase-12-real-always-on-jarvis-mvp.md").read_text(encoding="utf-8")

    assert '"/mark-3/phase-12/conversation/turn"' in api_source
    assert "phase_12_status" in api_source
    assert "phase_12_wake_listener" in api_source
    assert "jarvis-phase-12-status" in shell_source
    assert "solo local/LAN" in shell_source
    assert "backend {phase12BackendPort}" in shell_source
    assert "Hermes directo no" in shell_source
    assert "phase12WakeGreetingText" in shell_source
    assert '"/mark-3/phase-12/always-on/ui-presence"' in api_source
    assert '"/mark-3/phase-12/always-on/claim-greeting"' in api_source
    assert "claimedWakeGreetingIdsRef" in page_source
    assert "deliverWakeGreeting" in page_source
    assert "wakeGreetingClaimInFlightRef" in page_source
    assert "sendJarvisPhase12UiPresence" in page_source
    assert "claimJarvisWakeGreeting" in page_source
    assert "controller.handleWakeGreeting" in page_source
    assert "claimedWakeGreetingIdsRef.current.has(greetingId)" in page_source
    assert "setConversationMessages((current) => appendLimited(current, {" in page_source
    assert 'const VOICE_OUTPUT_STORAGE_KEY = "jarvis.voiceOutputEnabled"' in voice_hook_source
    assert "if (stored === null) return true;" in voice_hook_source
    assert 'return stored !== "false";' in voice_hook_source
    assert "handleWakeGreeting" in voice_hook_source
    assert "intent_detected: \"wake_greeting\"" in voice_hook_source
    assert "setConversationActiveFlag(true)" in voice_hook_source
    assert "speakLocalJarvisResponse(trimmed, tone)" in voice_hook_source
    assert "blockedSpeechRef" in voice_hook_source
    assert "unlockBrowserVoice" in voice_hook_source
    assert "browserVoiceUnlockRequired" in smart_bar_source
    assert "onUnlockBrowserVoice" in smart_bar_source
    assert "desbloquear voz" in smart_bar_source
    assert "Wake activo con" in smart_bar_source
    assert "Di \"JARVIS\"" in smart_bar_source
    assert "\"Hola JARVIS\" queda como alias experimental según reconocimiento local." in smart_bar_source
    assert "Di \"Hola JARVIS\" o \"JARVIS\"" not in smart_bar_source
    assert "Estoy escuchando la frase de activación. No guardo audio bruto." in smart_bar_source
    assert "mutear" in smart_bar_source
    assert "Voz activa. Puedes hablar con JARVIS." in voice_hook_source
    assert "Voz activa. Puedes hablar con JARVIS" in smart_bar_source
    assert "return true;" in voice_hook_source
    assert "El navegador necesita una primera pulsación para desbloquear la voz. Pulsa aquí una vez" in voice_hook_source
    assert "El navegador necesita una primera pulsación para desbloquear la voz. Pulsa aquí una vez" in smart_bar_source
    for stale_text in (
        "La voz está en modo manual.",
        "Pulsa el micrófono para hablar.",
        "Después de una respuesta escrita",
        "El wake word de sistema queda en readiness",
        "Por ahora esa frase no abre escucha automática",
        "voz sigue en modo manual",
        "Activación siempre manual",
        "Compat fallback PR175",
    ):
        assert stale_text not in smart_bar_source
        assert stale_text not in voice_hook_source
        assert stale_text not in utils_source
    assert 'fetchJSON<JarvisConversationTurnResponse>("/mark-3/conversation/turn"' not in api_source
    assert "scripts/jarvis-wake-setup status" in report
    assert 'scripts/jarvis-wake-listener match "jarvis"' in report
    assert 'scripts/jarvis-wake-listener simulate "jarvis"' in report
    assert "alias experimental" in report
    assert "best-effort" in report
    assert "Voz activa. Puedes hablar con JARVIS." in report
    assert "JARVIS_WAKE_BACKEND=vosk" in report
    assert "Transcript Ingest Test" in report
    assert "not real\nmicrophone wake" in report
