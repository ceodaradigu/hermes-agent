import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (  # noqa: E402
    IPhoneCommandRequest,
    IPhonePairingStartRequest,
    IPhonePairingVerifyRequest,
    Mark3ModelRouterV2DecisionRequest,
    Mark3Phase11AppLaunchCandidateRequest,
    Mark3Phase11ApprovalConfirmRequest,
    Mark3Phase11ApprovalStartRequest,
    Mark3Phase11BrowserPrepareRequest,
    Mark3Phase11LaunchRequest,
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


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"


def _route(app, path: str, method: str = "GET"):
    return next(route for route in app.routes if route.path == path and method in getattr(route, "methods", set()))


def _runtime(monkeypatch, *, opener=None, monthly=30.0, spent=0.0):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("JARVIS_OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("JARVIS_OPENROUTER_LIVE_CALLS_ENABLED", raising=False)
    return Phase11RealProviderControllerIPhoneCompanion(
        phase10=Phase10HandsFreeRuntimePersonaApiRouter(),
        monthly_budget_eur=monthly,
        spent_eur=spent,
        opener=opener or (lambda _url: True),
    )


def test_openrouter_missing_key_is_disabled_and_secret_free(monkeypatch):
    runtime = _runtime(monkeypatch)

    status = runtime.providers.status()
    serialized = json.dumps(status)

    assert status["providers"]["openrouter"]["configured"] is False
    assert status["providers"]["openrouter"]["enabled"] is False
    assert status["providers"]["openrouter"]["ready"] is False
    assert status["providers"]["openrouter"]["missing"] == ["OPENROUTER_API_KEY"]
    assert status["budget"]["monthly_budget_eur"] == 30.0
    assert "OPENROUTER_API_KEY" in serialized
    assert "sk-" not in serialized
    assert status["summary"]["keys_exposed"] is False


def test_openrouter_key_redacted_router_requires_approval_and_mocked_adapter_never_uses_network(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-phase11-secret-value")
    monkeypatch.setenv("JARVIS_OPENROUTER_LIVE_CALLS_ENABLED", "true")
    calls = []

    def fake_http_post(url, *, headers, json, timeout):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        assert headers["Authorization"] == "Bearer sk-or-phase11-secret-value"
        return {"id": "mocked", "choices": [{"message": {"content": "ok"}}]}

    runtime = Phase11RealProviderControllerIPhoneCompanion(
        phase10=Phase10HandsFreeRuntimePersonaApiRouter(),
        openrouter_http_post=fake_http_post,
    )

    status = runtime.providers.status()
    serialized = json.dumps(status)
    assert status["providers"]["openrouter"]["configured"] is True
    assert status["providers"]["openrouter"]["credential_state"] == "configured_redacted"
    assert status["providers"]["openrouter"]["paid_calls_enabled"] is True
    assert "sk-or-phase11-secret-value" not in serialized

    decision = runtime.model_router.decide(
        task_type="code",
        quality_required="high",
        estimated_input_tokens=220_000,
        estimated_output_tokens=120_000,
    )
    assert decision["selected_provider"] == "openrouter"
    assert decision["requires_approval"] is True
    assert decision["external_call_performed"] is False
    assert "sk-or-phase11-secret-value" not in json.dumps(decision)

    blocked = runtime.openrouter_adapter.chat_completion(
        model=decision["selected_model"],
        messages=[{"role": "user", "content": "hola"}],
        estimated_cost_eur=0.01,
        approval_confirmed=True,
        allow_paid_call=False,
    )
    assert blocked["status"] == "blocked"
    assert blocked["reason"] == "live_paid_calls_disabled_by_default"
    assert calls == []

    ok = runtime.openrouter_adapter.chat_completion(
        model=decision["selected_model"],
        messages=[{"role": "user", "content": "hola"}],
        estimated_cost_eur=0.01,
        approval_confirmed=True,
        allow_paid_call=True,
    )
    assert ok["status"] == "ok"
    assert ok["external_call_performed"] is True
    assert "sk-or-phase11-secret-value" not in json.dumps(ok)
    assert len(calls) == 1


def test_router_v2_budget_guard_local_fallback_and_no_blind_quality_downgrade(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-redacted")
    runtime = Phase11RealProviderControllerIPhoneCompanion(
        phase10=Phase10HandsFreeRuntimePersonaApiRouter(),
        monthly_budget_eur=30.0,
        spent_eur=29.9,
    )

    overspend = runtime.model_router.decide(
        task_type="code",
        quality_required="high",
        estimated_input_tokens=90_000,
        estimated_output_tokens=30_000,
    )
    assert overspend["selected_provider"] == "none"
    assert overspend["blocked_reason"] == "budget_exceeded"
    assert overspend["budget_would_exceed"] is True

    no_key_runtime = _runtime(monkeypatch)
    summary = no_key_runtime.model_router.decide(task_type="summarization", quality_required="standard")
    assert summary["selected_provider"] == "local"
    assert summary["estimated_cost_eur"] == 0.0

    risky = no_key_runtime.model_router.decide(
        task_type="risky_operation_reasoning",
        quality_required="critical",
        user_preference="cheapest",
    )
    assert risky["selected_provider"] == "none"
    assert risky["quality_downgrade_rejected"] is True
    assert "cheap_or_local_downgrade_rejected_because_quality_required" in risky["rejected_downgrades"]
    assert risky["blocked_reason"] == "missing_OPENROUTER_API_KEY"


def test_local_controller_known_unknown_and_bounded_open_jarvis(monkeypatch):
    opened = []
    runtime = _runtime(monkeypatch, opener=lambda url: opened.append(url) or True)

    unknown = runtime.local_controller.prepare_launch(app_name="MiAppRara")
    assert unknown["known"] is False
    assert unknown["spanish_response"] == "No sé dónde está esa aplicación. Dime la ruta una vez y la guardaré como app conocida."
    assert unknown["executed"] is False
    assert unknown["freeform_shell_allowed"] is False

    terminal = runtime.local_controller.prepare_launch(app_name="terminal")
    assert terminal["known"] is True
    assert terminal["requires_approval"] is True
    assert terminal["raw_command_accepted"] is False
    terminal_launch = runtime.local_controller.launch(candidate_id=terminal["candidate_id"])
    assert terminal_launch["status"] == "approval_required"
    assert terminal_launch["executed"] is False

    jarvis = runtime.local_controller.prepare_launch(app_name="Chrome")
    assert jarvis["real_launch_supported_now"] is True
    launched = runtime.local_controller.launch(candidate_id=jarvis["candidate_id"], trusted_session=True)
    assert launched["status"] == "executed"
    assert launched["did_open_browser"] is True
    assert opened == ["http://127.0.0.1:8000/jarvis"]


def test_browser_navigation_pilot_opens_safe_url_and_gates_forms_payments_credentials(monkeypatch):
    opened = []
    runtime = _runtime(monkeypatch, opener=lambda url: opened.append(url) or True)

    url = runtime.browser.prepare(text="https://example.com/path")
    assert url["intent"] == "browser.open_url"
    assert url["real_open_supported_now"] is True
    opened_url = runtime.browser.open_candidate(candidate_id=url["candidate_id"], trusted_session=True)
    assert opened_url["executed"] is True
    assert opened == ["https://example.com/path"]

    search = runtime.browser.prepare(text="busca jarvis hermes")
    assert search["intent"] == "web.search"
    assert search["real_open_supported_now"] is True

    form = runtime.browser.prepare(text="rellena este formulario")
    assert form["intent"] == "form.fill_preview"
    assert form["requires_approval"] is True
    assert form["safety"]["form_submit_allowed"] is False

    payment = runtime.browser.prepare(text="compra esto y paga")
    assert payment["requires_strong_approval"] is True
    assert payment["safety"]["purchase_payment_publication_allowed"] is False

    login = runtime.browser.prepare(text="haz login con mi password")
    assert login["risk_level"] == "high"
    assert login["safety"]["credential_storage_allowed"] is False
    assert login["safety"]["login_manual_required"] is True


def test_iphone_pairing_revocation_command_and_mobile_approval_binding(monkeypatch):
    runtime = _runtime(monkeypatch)

    unauth_command = runtime.shared_state.handle_iphone_command(text="JARVIS, activa modo UTRON", device_id="missing")
    assert unauth_command["status"] == "rejected"
    assert unauth_command["executed"] is False

    start = runtime.pairing.start_pairing(display_name="David iPhone", public_identifier="iphone-1", ttl_seconds=60)
    assert start["pairing_status"] == "pending"
    assert start["expires_at"]
    verified = runtime.pairing.verify_pairing(
        challenge_id=start["challenge_id"],
        pairing_code=start["pairing_code"],
        nonce=start["nonce"],
        public_identifier="iphone-1",
        display_name="David iPhone",
    )
    assert verified["pairing_status"] == "trusted_device_bound"
    device_id = verified["device"]["device_id"]

    command = runtime.shared_state.handle_iphone_command(text="JARVIS, activa modo UTRON", device_id=device_id)
    assert command["status"] == "normal"
    assert command["persona"]["state"]["mode"] == "utron"
    assert command["direct_hermes_allowed"] is False

    approval = runtime.approvals.start(
        action_summary="abrir URL segura",
        risk_level="high",
        action_id="action-open-url",
        scope=["browser.open_url", "https://example.com"],
        channel="iphone_pwa",
        device_id=device_id,
    )
    unpaired = runtime.approvals.confirm(
        approval_id=approval["approval_id"],
        action_id="action-open-url",
        scope=["browser.open_url", "https://example.com"],
        phrase=PHASE_10_EXACT_APPROVAL_PHRASE,
        channel="iphone_pwa",
        device_id="unknown-device",
    )
    assert unpaired["approved"] is False
    assert unpaired["reason"] == "mobile_device_not_paired_or_trusted"

    wrong_scope = runtime.approvals.confirm(
        approval_id=approval["approval_id"],
        action_id="action-open-url",
        scope=["browser.open_url", "https://evil.example"],
        phrase=PHASE_10_EXACT_APPROVAL_PHRASE,
        channel="iphone_pwa",
        device_id=device_id,
    )
    assert wrong_scope["approved"] is False
    assert wrong_scope["reason"] == "scope_mismatch"

    approved = runtime.approvals.confirm(
        approval_id=approval["approval_id"],
        action_id="action-open-url",
        scope=["browser.open_url", "https://example.com"],
        phrase=PHASE_10_EXACT_APPROVAL_PHRASE,
        channel="iphone_pwa",
        device_id=device_id,
    )
    assert approved["approved"] is True
    assert approved["would_execute"] is False

    replay = runtime.approvals.confirm(
        approval_id=approval["approval_id"],
        action_id="action-open-url",
        scope=["browser.open_url", "https://example.com"],
        phrase=PHASE_10_EXACT_APPROVAL_PHRASE,
        channel="iphone_pwa",
        device_id=device_id,
    )
    assert replay["approved"] is False
    assert replay["reason"] == "phrase_replay_rejected"

    revoked = runtime.pairing.revoke(device_id=device_id)
    assert revoked["revoked"] is True
    assert runtime.pairing.is_trusted(device_id) is False


def test_phase_11_api_dashboard_event_stream_and_shared_state_are_secret_free(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-phase11-secret")
    app = create_app(
        adapter_factory=lambda: pytest.fail("Hermes must not be called"),
        hermes_runtime_adapter_factory=lambda _authorize: pytest.fail("Hermes runtime bridge must not be called"),
    )
    app.state.phase_11_runtime.local_controller.opener = lambda url: True

    route_paths = {route.path for route in app.routes}
    for path in (
        "/mark-3/phase-11/status",
        "/mark-3/providers/status",
        "/mark-3/model-router-v2/status",
        "/mark-3/model-router-v2/decision",
        "/mark-3/phase-11/local-controller/launch-candidate",
        "/mark-3/phase-11/browser/prepare",
        "/iphone/companion/status",
        "/iphone/pairing/start",
        "/iphone/pairing/verify",
        "/iphone/approval/decision",
        "/iphone/command",
    ):
        assert path in route_paths

    status = _route(app, "/mark-3/phase-11/status").endpoint()
    assert status["security_gates"]["mobile_direct_hermes_allowed"] is False
    assert status["security_gates"]["dangerous_exact_phrase"] == PHASE_10_EXACT_APPROVAL_PHRASE
    assert status["iphone_companion"]["same_jarvis_brain"] is True
    assert status["iphone_companion"]["separate_mobile_agent"] is False

    decision = _route(app, "/mark-3/model-router-v2/decision", "POST").endpoint(
        Mark3ModelRouterV2DecisionRequest(task_type="code", quality_required="high")
    )
    assert decision["selected_provider"] == "openrouter"
    assert decision["external_call_performed"] is False

    candidate = _route(app, "/mark-3/phase-11/local-controller/launch-candidate", "POST").endpoint(
        Mark3Phase11AppLaunchCandidateRequest(app_name="Chrome")
    )
    assert candidate["freeform_shell_allowed"] is False
    launch = _route(app, "/mark-3/phase-11/local-controller/launch", "POST").endpoint(
        Mark3Phase11LaunchRequest(candidate_id=candidate["candidate_id"], trusted_session=True)
    )
    assert launch["did_open_browser"] is True

    browser = _route(app, "/mark-3/phase-11/browser/prepare", "POST").endpoint(
        Mark3Phase11BrowserPrepareRequest(text="rellena formulario y envia")
    )
    assert browser["requires_approval"] is True
    assert browser["safety"]["form_submit_allowed"] is False

    pairing = _route(app, "/iphone/pairing/start", "POST").endpoint(IPhonePairingStartRequest(public_identifier="iphone-api"))
    verified = _route(app, "/iphone/pairing/verify", "POST").endpoint(
        IPhonePairingVerifyRequest(
            challenge_id=pairing["challenge_id"],
            pairing_code=pairing["pairing_code"],
            nonce=pairing["nonce"],
            public_identifier="iphone-api",
        )
    )
    command = _route(app, "/iphone/command", "POST").endpoint(
        IPhoneCommandRequest(text="desactiva UTRON", device_id=verified["device"]["device_id"])
    )
    assert command["direct_hermes_allowed"] is False

    approval = _route(app, "/mark-3/phase-11/approval/start", "POST").endpoint(
        Mark3Phase11ApprovalStartRequest(action_summary="usar proveedor pago", action_id="provider-call", scope=["openrouter"])
    )
    mobile_approval = _route(app, "/iphone/approval/decision", "POST").endpoint(
        Mark3Phase11ApprovalConfirmRequest(
            approval_id=approval["approval_id"],
            action_id="provider-call",
            scope=["openrouter"],
            phrase=PHASE_10_EXACT_APPROVAL_PHRASE,
            device_id=verified["device"]["device_id"],
        )
    )
    assert mobile_approval["approved"] is True

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    assert dashboard["phase_11_status"]["status"] == "implemented_as_bounded_real_provider_controller_iphone_pilot"
    assert dashboard["iphone"]["same_jarvis_brain"] is True
    snapshot = build_jarvis_event_snapshot(dashboard_status=dashboard, generated_at="2026-06-20T00:00:00+00:00")
    event_types = {event["event_type"] for event in snapshot["events"]}
    assert "phase_11_state" in event_types
    assert "provider_status_state" in event_types
    assert "model_router_v2_state" in event_types
    assert "iphone_companion_state" in event_types

    serialized = json.dumps({"status": status, "dashboard": dashboard, "snapshot": snapshot})
    assert "sk-or-phase11-secret" not in serialized
    assert "audio_bytes" not in serialized
    assert "camera_frames_included\": true" not in serialized


def test_iphone_pwa_static_contract_reuses_same_jarvis_route_and_manifest():
    app_tsx = (WEB / "src/App.tsx").read_text(encoding="utf-8")
    index = (WEB / "index.html").read_text(encoding="utf-8")
    manifest = json.loads((WEB / "public/manifest.webmanifest").read_text(encoding="utf-8"))

    assert '"/mobile": "jarvis"' in app_tsx
    assert '<link rel="manifest" href="/manifest.webmanifest" />' in index
    assert 'apple-mobile-web-app-capable' in index
    assert manifest["start_url"] == "/mobile"
    assert manifest["display"] == "standalone"
    assert manifest["short_name"] == "JARVIS"
