import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import create_app


class FailingAdapter:
    def run(self, *_args, **_kwargs):
        pytest.fail("legacy Hermes adapter must not be called by dashboard status")


def _app():
    return create_app(
        adapter_factory=lambda: FailingAdapter(),
        hermes_runtime_adapter_factory=lambda _guard: pytest.fail(
            "Hermes runtime adapter factory must not be called by dashboard status"
        ),
    )


def _dashboard_route(app):
    for route in app.routes:
        if route.path == "/mark-3/dashboard/status":
            return route
    raise AssertionError("missing /mark-3/dashboard/status route")


def _payload():
    app = _app()
    route = _dashboard_route(app)
    return route.endpoint(), app


def test_mark_3_dashboard_status_endpoint_responds_200():
    app = _app()
    route = _dashboard_route(app)
    payload = route.endpoint()

    assert route.methods == {"GET"}
    assert isinstance(payload, dict)
    assert payload["system"]["api_status"] == "ok"
    assert payload["system"]["mode"] == "read_only_dashboard"
    assert payload["system"]["free_autonomy_enabled"] is False
    assert payload["system"]["preview_first"] is True
    assert payload["system"]["generated_at"]


def test_mark_3_dashboard_status_declares_jarvis_hermes_contract():
    payload, _ = _payload()

    assert payload["jarvis_hermes_contract"]["jarvis_role"] == "governs/risk/approval/audit/control"
    assert payload["jarvis_hermes_contract"]["hermes_role"] == "execution_engine"
    assert payload["jarvis_hermes_contract"]["frontend_can_execute"] is False
    assert payload["jarvis_hermes_contract"]["no_duplicate_hermes_runtime"] is True
    assert payload["release_candidate"]["not_ready_for_free_autonomy"] is True
    assert payload["release_candidate"]["restrictions_are_approval_gates_not_permanent_bans"] is True


def test_mark_3_dashboard_status_contains_required_modules_and_sources():
    payload, _ = _payload()
    modules = {item["name"]: item for item in payload["modules"]}

    for name in (
        "Mission Loop",
        "Research",
        "Product Revenue",
        "Routine Ops",
        "Moonshot Lab",
        "Voice",
        "Wake Listener",
        "Camera/Vision",
        "Mobile Companion",
        "Memory/Learning",
        "Hermes",
    ):
        assert name in modules
        assert modules[name]["status"] in {
            "ready",
            "preview",
            "prepare-only",
            "gated",
            "disabled",
            "not_connected",
            "unknown",
        }
        assert modules[name]["source"]
        assert modules[name]["risk"]
        assert modules[name]["notes"]


def test_mark_3_dashboard_status_keeps_approvals_sensors_and_execution_disabled():
    payload, _ = _payload()

    assert payload["approvals"]["pending_count"] == 0
    assert payload["approvals"]["action_buttons_enabled"] is False
    assert payload["approvals"]["all_actions_read_only"] is True
    assert payload["approvals"]["wake_phrase_can_approve"] is False
    assert payload["approvals"]["frontend_can_approve"] is False
    assert payload["approvals"]["frontend_can_reject"] is False
    assert payload["approvals"]["frontend_can_modify_scope"] is False
    assert payload["approvals"]["critical_actions_require_strong_approval"] is True
    assert payload["hermes_execution"]["frontend_direct_execution_allowed"] is False
    assert payload["voice_wake"]["wake_phrase_can_approve"] is False
    assert payload["voice_wake"]["audio_recording"] is False
    assert payload["camera_vision"]["recording"] is False
    assert payload["camera_vision"]["storage"] is False
    assert payload["mobile"]["direct_hermes_call_allowed"] is False


def test_mark_3_dashboard_status_contains_enriched_approval_summary_and_cards():
    payload, _ = _payload()
    approvals = payload["approvals"]
    cards = approvals["cards"]

    assert approvals["pending_count"] == 0
    assert approvals["critical_count"] >= 1
    assert approvals["blocked_count"] >= 1
    assert approvals["expired_count"] == 0
    assert approvals["preview_count"] == len(cards)
    assert approvals["cards_state"] == "preview/read-only"
    assert approvals["preview_only"] is True

    required_fields = {
        "id",
        "title",
        "action",
        "reason",
        "status",
        "risk_level",
        "approval_level",
        "touches",
        "estimated_cost",
        "measured_cost",
        "rollback_plan",
        "stop_plan",
        "expires_at",
        "scope_summary",
        "evidence_summary",
        "disabled_reason",
        "recommended_operator_action",
    }
    allowed_status = {"preview", "pending", "approved", "rejected", "expired", "blocked", "forbidden", "unknown"}
    allowed_risk = {"low", "medium", "high", "critical", "forbidden", "unknown"}
    allowed_approval = {"direct", "simple", "strong", "double", "triple", "forbidden", "unknown"}

    assert len(cards) >= 5
    for card in cards:
        assert required_fields.issubset(card)
        assert all(card[field] not in ("", None) for field in required_fields - {"touches"})
        assert card["status"] in allowed_status
        assert card["risk_level"] in allowed_risk
        assert card["approval_level"] in allowed_approval
        assert isinstance(card["touches"], list)
        assert card["touches"]
        assert card["estimated_cost"] == "unknown"
        assert card["measured_cost"] == "unknown"
        assert card["preview_only"] is True
        assert card["read_only"] is True
        assert "Preview-only" in card["disabled_reason"] or card["status"] in {"blocked", "forbidden"}


def test_mark_3_dashboard_status_critical_approvals_require_strong_gates_and_plans():
    payload, _ = _payload()
    critical_cards = [card for card in payload["approvals"]["cards"] if card["risk_level"] == "critical"]

    assert critical_cards
    for card in critical_cards:
        assert card["approval_level"] in {"strong", "double", "triple"}
        assert card["requires_readback"] is True
        assert card["strong_confirmation_required"] is True
        assert card["double_confirmation_required"] is True or card["triple_confirmation_required"] is True
        assert card["rollback_required"] is True
        assert card["stop_plan_required"] is True
        assert card["audit_required"] is True
        assert card["rollback_plan"] != "unknown"
        assert card["stop_plan"] != "unknown"


def test_mark_3_dashboard_status_forbidden_credentials_card_is_blocked():
    payload, _ = _payload()
    cards = {card["id"]: card for card in payload["approvals"]["cards"]}
    card = cards["preview-forbidden-credentials-bypass"]

    assert card["status"] in {"forbidden", "blocked"}
    assert card["risk_level"] == "forbidden"
    assert card["approval_level"] == "forbidden"
    assert "credentials" in card["touches"]
    assert card["preview_only"] is True
    assert card["read_only"] is True
    assert card["stop_plan_required"] is True


def test_mark_3_dashboard_status_keeps_finance_unknown_and_no_fake_metrics():
    payload, _ = _payload()
    finance = payload["finance"]

    assert finance["actual_cost"] == "unknown"
    assert finance["estimated_cost"] == "unknown"
    assert finance["confirmed_revenue"] == "unknown"
    assert finance["projected_revenue"] == "unknown"
    assert finance["roi"] == "unknown"
    assert finance["no_fake_metrics"] is True


def test_mark_3_dashboard_status_declares_safety_boundaries():
    payload, _ = _payload()
    safety = payload["safety"]

    assert safety["frontend_can_execute"] is False
    assert safety["frontend_can_approve"] is False
    assert safety["no_duplicate_hermes_runtime"] is True
    assert safety["no_get_user_media"] is True
    assert safety["no_sensor_activation"] is True
    assert safety["no_frontend_tool_runner"] is True
    assert safety["no_frontend_hermes_execution"] is True
    assert safety["no_post_put_delete_from_jarvis_page"] is True
    assert safety["no_money_movement"] is True
    assert safety["no_deploy"] is True
    assert safety["no_credentials"] is True
    assert safety["no_email_send"] is True


def test_mark_3_dashboard_status_adds_no_dangerous_action_routes():
    app = _app()
    routes = {
        (route.path, method)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }

    assert ("/mark-3/dashboard/status", "GET") in routes
    for forbidden in (
        ("/mark-3/dashboard/status", "POST"),
        ("/jarvis/dashboard/status", "POST"),
        ("/jarvis/execute", "POST"),
        ("/jarvis/approve", "POST"),
        ("/jarvis/hermes/execute", "POST"),
        ("/mark-3/dashboard/execute", "POST"),
        ("/mark-3/dashboard/approve", "POST"),
        ("/mark-3/dashboard/reject", "POST"),
    ):
        assert forbidden not in routes


def test_mark_3_dashboard_status_sources_are_declared_get_read_only_routes():
    payload, app = _payload()
    methods_by_path = {
        route.path: set(getattr(route, "methods", set()))
        for route in app.routes
    }
    source_endpoints = set(payload["release_candidate"]["source_endpoints"])
    source_endpoints.update(payload["voice_wake"]["source_endpoints"])
    source_endpoints.update(payload["mobile"]["source_endpoints"])
    source_endpoints.add(payload["approvals"]["source_endpoint"])
    source_endpoints.add(payload["camera_vision"]["source_endpoint"])
    source_endpoints.add(payload["hermes_execution"]["source_endpoint"])
    source_endpoints.add(payload["system"]["source_endpoint"])

    for endpoint in source_endpoints:
        assert endpoint in methods_by_path
        assert methods_by_path[endpoint] == {"GET"}

    assert payload["read_only_contract"]["allowed_http_methods_for_frontend"] == ["GET"]
    assert payload["read_only_contract"]["internal_sources_are_read_only_status_or_audit"] is True


def test_mark_3_dashboard_status_does_not_call_execution_sensors_or_money(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("dashboard status must not call active execution, sensors, or money adapters")

    monkeypatch.setattr("jarvis.runtime.hermes_adapter.HermesRuntimeAdapter.run", fail)
    monkeypatch.setattr("jarvis.mark_3_hermes_runtime_bridge.Mark3HermesRuntimeBridge.execute_read", fail)
    monkeypatch.setattr("jarvis.mark_3_hermes_runtime_bridge.Mark3HermesRuntimeBridge.stop", fail)
    monkeypatch.setattr("jarvis.camera_control_runtime.CameraControlRuntime.preview_session", fail)
    monkeypatch.setattr("jarvis.wake_voice_runtime.WakeVoiceRuntime.parse", fail)
    monkeypatch.setattr("jarvis.mark_2_deploy_adapter.Mark2DeployAdapter.preview", fail)
    monkeypatch.setattr("jarvis.mark_2_stripe_adapter.Mark2StripeAdapter.preview", fail)
    monkeypatch.setattr("jarvis.mark_2_email_adapter.Mark2EmailAdapter.preview", fail)

    payload, _ = _payload()

    assert payload["source_status"]["e2e_smoke"]["would_execute"] is False
    assert payload["source_status"]["dangerous_route_audit"]["dangerous_routes_registered"] == []


def test_mark_3_dashboard_status_timeline_contains_only_read_model_events():
    payload, _ = _payload()
    events = payload["timeline"]

    assert any(item["event"] == "backend status read" for item in events)
    assert any(item["event"] == "release candidate status read" for item in events)
    assert any(item["event"] == "readiness read" for item in events)
    assert any(item["event"] == "dangerous route audit read" for item in events)
    assert any(item["event"] == "dashboard read model generated" for item in events)
    assert all(item["read_only"] is True for item in events)
    assert not any("executed" in item["event"].lower() for item in events)
