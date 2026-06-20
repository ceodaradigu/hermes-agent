import json
from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")

from jarvis.api.app import (
    Mark3ExternalBudgetGuardRequest,
    Mark3ExternalDeployCandidateRequest,
    Mark3ExternalEmailCandidateRequest,
    Mark3ExternalPaymentCandidateRequest,
    Mark3ExternalRevenueEventRequest,
    Mark3ExternalVoiceApprovalReadinessRequest,
    Mark3RemoteApprovalIntentRequest,
    Mark3RemoteChannelPairingChallengeRequest,
    Mark3RemoteChannelPairingVerifyRequest,
    Mark3RemoteChannelRevokeRequest,
    create_app,
)
from jarvis.memory_brain_v2 import MemoryBrainV2Store
from jarvis.persistent_audit import PersistentAuditLedger


WEB = Path("web")


def _make_app(tmp_path, monkeypatch, **env):
    state_dir = tmp_path / "state"
    monkeypatch.setenv("JARVIS_LOCAL_STATE_DIR", str(state_dir))
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    ledger = PersistentAuditLedger(base_dir=state_dir)
    memory = MemoryBrainV2Store(base_dir=state_dir, audit_ledger=ledger)
    app = create_app(
        adapter_factory=lambda: pytest.fail("legacy Hermes adapter must not be called"),
        hermes_runtime_adapter_factory=lambda _guard: pytest.fail("Hermes runtime adapter must not be created by Phase 8"),
        persistent_audit_ledger=ledger,
        memory_brain_v2=memory,
    )
    return app, ledger


def _route(app, path, method="GET"):
    return next(route for route in app.routes if route.path == path and method in getattr(route, "methods", set()))


def _event_types(ledger):
    return {entry["event_type"] for entry in ledger.list_entries(limit=1000)}


def _frontend_sources():
    paths = [
        WEB / "src/lib/api.ts",
        WEB / "src/components/jarvis/types.ts",
        WEB / "src/components/jarvis/contracts.ts",
        WEB / "src/components/jarvis/JarvisDebugDrawer.tsx",
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def _prepare_deploy(app, **payload):
    return _route(app, "/mark-3/external-operations/prepare-deploy", "POST").endpoint(
        Mark3ExternalDeployCandidateRequest(**payload)
    )


def _pair_remote_device(app, *, channel_id="mobile_pwa", public_identifier="phase8-phone"):
    challenge = _route(app, "/mark-3/remote-channels/pairing/challenge", "POST").endpoint(
        Mark3RemoteChannelPairingChallengeRequest(
            channel_id=channel_id,
            display_name="David phone",
            public_identifier=public_identifier,
        )
    )
    paired = _route(app, "/mark-3/remote-channels/pairing/verify", "POST").endpoint(
        Mark3RemoteChannelPairingVerifyRequest(
            channel_id=channel_id,
            challenge_id=challenge["challenge_id"],
            nonce=challenge["nonce"],
            response_phrase=challenge["challenge_phrase"],
            public_identifier=public_identifier,
            display_name="David phone",
            scope=challenge["scope"],
        )
    )
    return paired


def test_phase_8_routes_dashboard_events_and_frontend_are_secret_free(tmp_path, monkeypatch):
    token = "123456:ABCdef-secret-token-value"
    app, ledger = _make_app(
        tmp_path,
        monkeypatch,
        TELEGRAM_BOT_TOKEN=token,
        TELEGRAM_ALLOWED_USERS="42",
        JARVIS_PHASE8_TELEGRAM_ENABLED="true",
    )
    route_paths = {route.path for route in app.routes}

    assert "/execute" not in route_paths
    assert "/jarvis/execute" not in route_paths
    assert "/mark-3/phase-8/status" in route_paths
    assert "/mark-3/remote-channels/status" in route_paths
    assert "/mark-3/external-operations/prepare-payment" in route_paths

    phase8 = _route(app, "/mark-3/phase-8/status").endpoint()
    assert phase8["status"] == "implemented_as_governed_readiness_and_prepare_only_pilot"
    assert phase8["implemented_blocks"]["remote_channel_registry_v1"] is True
    assert phase8["security_gates"]["remote_channels_call_hermes_directly"] is False
    assert phase8["security_gates"]["provider_calls_enabled_by_default"] is False
    assert phase8["security_gates"]["fake_revenue_allowed"] is False

    telegram = _route(app, "/mark-3/telegram-readiness/status").endpoint()
    assert telegram["token_present"] is True
    assert telegram["token_value_exposed"] is False
    assert telegram["runtime"]["bot_started"] is False
    assert telegram["runtime"]["external_api_called"] is False
    assert token not in json.dumps(telegram)

    dashboard = _route(app, "/mark-3/dashboard/status").endpoint()
    serialized_dashboard = json.dumps(dashboard)
    assert dashboard["phase_8_status"]["source_endpoint"] == "/mark-3/phase-8/status"
    assert dashboard["remote_channels"]["defaults"]["remote_execution_enabled"] is False
    assert dashboard["external_operations"]["provider_calls_enabled"] is False
    assert dashboard["external_budget_guard"]["can_spend"] is False
    assert token not in serialized_dashboard
    assert "Phase 8 Remote Ops" in {module["name"] for module in dashboard["modules"]}

    snapshot = _route(app, "/mark-3/dashboard/events").endpoint()
    event_types = {event["event_type"] for event in snapshot["events"]}
    assert {"phase_8_state", "remote_channel_state", "external_operation_state", "budget_guard_state", "payment_provider_state"} <= event_types
    assert token not in json.dumps(snapshot)

    source = _frontend_sources()
    for text in (
        "Phase 8 Remote Channels",
        "Remote channels must send intent into JARVIS Gateway/control plane.",
        "Telegram readiness does not run a bot automatically.",
        "Telegram token presence is redacted",
        "Phase 8 External Ops",
        "Deploy candidate is dry-run/prepare-only by default",
        "Stripe live mode is blocked by default",
        "Confirmed revenue requires evidence/source",
    ):
        assert text in source
    assert 'fetchJSON("/execute"' not in source
    assert 'fetchJSON("/jarvis/execute"' not in source
    assert "dispatchHermes" not in source

    assert {"phase_8_status_read", "remote_channel_status_read", "telegram_readiness_checked"} <= _event_types(ledger)


def test_remote_pairing_approval_intent_requires_trusted_device_challenge_and_revocation(tmp_path, monkeypatch):
    app, ledger = _make_app(tmp_path, monkeypatch)
    deploy = _prepare_deploy(
        app,
        provider="vercel",
        environment="staging",
        target="jarvis-preview",
        build_summary="static build reviewed",
        rollback_plan="restore previous deployment alias manually",
        cost_estimate=1.25,
    )
    envelope = deploy["envelope"]

    unpaired = _route(app, "/mark-3/remote-channels/approval-intent", "POST").endpoint(
        Mark3RemoteApprovalIntentRequest(
            operation_id=envelope["operation_id"],
            channel_id="mobile_pwa",
            device_id="device-missing",
            challenge_phrase=envelope["challenge_phrase"],
            readback_text=envelope["readback_text"],
        )
    )
    assert unpaired["accepted"] is False
    assert unpaired["reason"] == "paired_trusted_non_revoked_device_required"
    assert unpaired["hermes_called"] is False

    paired = _pair_remote_device(app)
    device_id = paired["device"]["device_id"]

    bad_challenge = _route(app, "/mark-3/remote-channels/approval-intent", "POST").endpoint(
        Mark3RemoteApprovalIntentRequest(
            operation_id=envelope["operation_id"],
            channel_id="mobile_pwa",
            device_id=device_id,
            challenge_phrase="wrong",
            readback_text=envelope["readback_text"],
        )
    )
    assert bad_challenge["accepted"] is False
    assert bad_challenge["reason"] == "exact_challenge_required"

    accepted = _route(app, "/mark-3/remote-channels/approval-intent", "POST").endpoint(
        Mark3RemoteApprovalIntentRequest(
            operation_id=envelope["operation_id"],
            channel_id="mobile_pwa",
            device_id=device_id,
            challenge_phrase=envelope["challenge_phrase"],
            readback_text=envelope["readback_text"],
        )
    )
    assert accepted["accepted"] is True
    assert accepted["intent_status"] == "accepted_pending_local_approval_bridge"
    assert accepted["approval_gateway_called"] is False
    assert accepted["approval_granted"] is False
    assert accepted["execution_allowed"] is False

    _route(app, "/mark-3/remote-channels/revoke", "POST").endpoint(
        Mark3RemoteChannelRevokeRequest(device_id=device_id, reason="test revoke")
    )
    revoked = _route(app, "/mark-3/remote-channels/approval-intent", "POST").endpoint(
        Mark3RemoteApprovalIntentRequest(
            operation_id=envelope["operation_id"],
            channel_id="mobile_pwa",
            device_id=device_id,
            challenge_phrase=envelope["challenge_phrase"],
            readback_text=envelope["readback_text"],
        )
    )
    assert revoked["accepted"] is False
    assert revoked["reason"] == "paired_trusted_non_revoked_device_required"
    assert {"remote_channel_pairing_challenge_consumed", "remote_approval_intent_received", "remote_channel_revoked"} <= _event_types(ledger)


def test_deploy_email_payment_budget_and_revenue_contracts_do_not_execute(tmp_path, monkeypatch):
    stripe_live = "sk_live_1234567890ABCDEF"
    app, ledger = _make_app(tmp_path, monkeypatch, STRIPE_SECRET_KEY=stripe_live)

    deploy = _prepare_deploy(
        app,
        provider="render",
        environment="production",
        target="customer-facing app",
        build_summary="tests green, diff reviewed",
        cost_estimate="unknown",
    )
    deploy_candidate = deploy["candidate"]
    assert deploy_candidate["dry_run_default"] is True
    assert deploy_candidate["would_deploy"] is False
    assert deploy_candidate["would_call_provider"] is False
    assert deploy_candidate["would_change_dns"] is False
    assert deploy_candidate["would_read_secrets"] is False
    assert deploy_candidate["approval_level_required"] == "triple"
    assert "production deploy disabled by default" in deploy_candidate["blocked_reasons"]
    assert deploy["envelope"]["execution_enabled"] is False

    email = _route(app, "/mark-3/external-operations/prepare-email", "POST").endpoint(
        Mark3ExternalEmailCandidateRequest(
            provider="resend",
            operation="send",
            recipients=["david@example.com", "friend@example.com"],
            subject="Hello token",
            body="Use secret sk_live_1234567890ABCDEF",
            personal_identity_use=True,
            send_requested=True,
            attachments=[{"name": "proposal.pdf", "content_type": "application/pdf", "size_bytes": 1234}],
        )
    )
    email_payload = json.dumps(email)
    email_candidate = email["candidate"]
    assert email_candidate["send_disabled_by_default"] is True
    assert email_candidate["would_send_email"] is False
    assert email_candidate["would_scrape_contacts"] is False
    assert email_candidate["approval_level_required"] == "strong"
    assert email_candidate["attachment_metadata_only"][0]["content_included"] is False
    assert "david@example.com" not in email_payload
    assert stripe_live not in email_payload

    payment = _route(app, "/mark-3/external-operations/prepare-payment", "POST").endpoint(
        Mark3ExternalPaymentCandidateRequest(
            stripe_mode="live",
            product_name="JARVIS Pilot",
            amount=49,
            currency="EUR",
            money_movement_requested=True,
        )
    )
    payment_payload = json.dumps(payment)
    payment_candidate = payment["candidate"]
    assert payment_candidate["live_mode"] is True
    assert payment_candidate["would_call_stripe"] is False
    assert payment_candidate["would_move_money"] is False
    assert payment_candidate["would_create_checkout"] is False
    assert payment_candidate["approval_level_required"] == "triple"
    assert "Stripe live mode blocked by default" in payment_candidate["blocked_reasons"]
    assert stripe_live not in payment_payload

    fake_revenue = _route(app, "/mark-3/external-operations/revenue-event", "POST").endpoint(
        Mark3ExternalRevenueEventRequest(confirmed_revenue=100, gross=100, fees=3)
    )
    assert fake_revenue["status"] == "rejected_fake_revenue"
    assert fake_revenue["confirmed_revenue"] is None
    assert fake_revenue["no_fake_revenue"] is True

    confirmed_revenue = _route(app, "/mark-3/external-operations/revenue-event", "POST").endpoint(
        Mark3ExternalRevenueEventRequest(projected_revenue=200, confirmed_revenue=100, gross=100, fees=3, evidence=["stripe event evt_redacted"])
    )
    assert confirmed_revenue["status"] == "confirmed_with_evidence"
    assert confirmed_revenue["projected_is_not_confirmed"] is True
    assert confirmed_revenue["net"] == 97

    unknown_cost = _route(app, "/mark-3/external-operations/budget-guard", "POST").endpoint(
        Mark3ExternalBudgetGuardRequest(monthly_budget=50, per_action_max_cost=10, spending_requested=True)
    )
    assert unknown_cost["decision"] == "blocked_unknown_cost"
    assert unknown_cost["can_spend"] is False
    assert unknown_cost["unknown_cost_blocks_or_requires_strong_approval"] is True

    over_limit = _route(app, "/mark-3/external-operations/budget-guard", "POST").endpoint(
        Mark3ExternalBudgetGuardRequest(
            monthly_budget=50,
            per_action_max_cost=10,
            provider_cost_estimate=12,
            confirmed_spend_this_month=20,
            confirmed_spend_evidence=["provider invoice inv_redacted"],
            explicit_approval_present=True,
        )
    )
    assert over_limit["decision"] == "blocked_over_per_action_limit"
    assert over_limit["budget_consumed"] == 20
    assert over_limit["estimates_consume_budget"] is False
    assert {"external_operation_candidate_prepared", "external_operation_envelope_created", "budget_guard_evaluated", "revenue_event_recorded"} <= _event_types(ledger)


def test_external_operation_voice_readiness_is_scoped_and_never_wake_only(tmp_path, monkeypatch):
    app, _ledger = _make_app(tmp_path, monkeypatch)
    paired = _pair_remote_device(app, public_identifier="phase8-voice-phone")
    device_id = paired["device"]["device_id"]

    payment = _route(app, "/mark-3/external-operations/prepare-payment", "POST").endpoint(
        Mark3ExternalPaymentCandidateRequest(stripe_mode="test", amount=5, currency="EUR")
    )
    readiness = _route(app, "/mark-3/external-operations/voice-approval-readiness", "POST").endpoint(
        Mark3ExternalVoiceApprovalReadinessRequest(
            operation_id=payment["envelope"]["operation_id"],
            device_id=device_id,
            active_voice_session=True,
        )
    )
    assert readiness["voice_approval_available"] is True
    assert readiness["requires_active_voice_session"] is True
    assert readiness["requires_trusted_device"] is True
    assert readiness["requires_exact_readback"] is True
    assert readiness["requires_spoken_challenge"] is True
    assert readiness["wake_phrase_can_approve"] is False

    inactive = _route(app, "/mark-3/external-operations/voice-approval-readiness", "POST").endpoint(
        Mark3ExternalVoiceApprovalReadinessRequest(
            operation_id=payment["envelope"]["operation_id"],
            device_id=device_id,
            active_voice_session=False,
        )
    )
    assert inactive["voice_approval_available"] is False

    critical = _prepare_deploy(
        app,
        provider="vercel",
        environment="production",
        target="prod",
        rollback_plan="manual restore",
        cost_estimate=1,
    )
    critical_readiness = _route(app, "/mark-3/external-operations/voice-approval-readiness", "POST").endpoint(
        Mark3ExternalVoiceApprovalReadinessRequest(
            operation_id=critical["envelope"]["operation_id"],
            device_id=device_id,
            active_voice_session=True,
        )
    )
    assert critical_readiness["voice_approval_available"] is False
    assert critical_readiness["higher_risk_requires_double_or_triple"] is True
