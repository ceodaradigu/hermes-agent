from __future__ import annotations

import inspect
from pathlib import Path
from typing import get_type_hints

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import create_app


MASTER_MAP = Path("docs/JARVIS_MASTER_BUILD_MAP.md")

STATUS_ROUTES = (
    "/voice/companion/status",
    "/mobile/companion/status",
    "/ambient-vision/status",
    "/devices/runtime/status",
    "/sandbox/execution/status",
    "/tools/adoption/status",
    "/asset-factory/status",
    "/deploy-publishing/status",
    "/marketing-distribution/status",
    "/payments-revenue/status",
    "/daily-operator/status",
    "/continuous-learning/status",
    "/personal-os/status",
    "/personalization/status",
    "/future-moonshot/status",
    "/operator/console/status",
)

PREVIEW_ROUTES = (
    "/voice/companion/preview",
    "/mobile/intent/preview",
    "/operator/console/preview",
    "/ambient-vision/session-preview",
    "/devices/sync/preview",
    "/sandbox/command/dry-run",
    "/tools/adoption/decision-preview",
    "/asset-factory/build-package-preview",
    "/deploy-publishing/production-preview",
    "/marketing-distribution/campaign-plan",
    "/payments-revenue/metrics-preview",
    "/daily-operator/daily-plan",
    "/continuous-learning/proposal-preview",
    "/personal-os/awareness-source-preview",
    "/personalization/memory-proposal",
    "/future-moonshot/physical-automation-preview",
)

FORBIDDEN_ENABLED_FIELDS = {
    "execution_enabled",
    "persistence_enabled",
    "external_calls_enabled",
    "secrets_access_enabled",
    "hermes_called",
    "approval_gateway_called",
}

PREVIEW_SIDE_EFFECT_FIELDS = {
    "approval_created",
    "background_sync_started",
    "external_calls_made",
    "hermes_called",
    "mission_created",
    "persisted",
    "state_changed",
    "task_created",
    "would_activate",
    "would_connect",
    "would_create_pr",
    "would_deploy",
    "would_execute",
    "would_install",
    "would_modify_code",
    "would_modify_prompts",
    "would_modify_runtime",
    "would_persist",
    "would_publish",
    "would_send",
    "would_write_memory",
}

DANGEROUS_ROUTE_NAMES = {
    "run",
    "execute",
    "deploy",
    "install",
    "send-email",
    "send-notification",
    "start-camera",
    "start-microphone",
    "capture-screen",
    "control-drone",
    "control-robot",
    "activate-memory",
    "save-memory",
    "create-pr",
    "connect-device",
}


class FailHermesAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes real must not be called by the prepare-only smoke")


class FailApprovalGateway:
    def create_request(self, *args, **kwargs):
        raise AssertionError("ApprovalGateway real must not be called by the prepare-only smoke")


@pytest.fixture
def app():
    return create_app(
        adapter_factory=lambda: FailHermesAdapter(),
        approval_gateway=FailApprovalGateway(),
    )


def _route(app, path: str, method: str):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route
    raise AssertionError(f"route not found: {method} {path}")


def _get(app, path: str):
    route = _route(app, path, "GET")
    assert route.status_code in (None, 200)
    return route.endpoint()


def _post(app, path: str):
    route = _route(app, path, "POST")
    parameter = next(iter(inspect.signature(route.endpoint).parameters.values()))
    request_model = get_type_hints(route.endpoint)[parameter.name]
    payload = {"text": "prepare-only smoke"} if "text" in request_model.model_fields else {}
    return route.endpoint(request_model(**payload))


def _walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _assert_named_flags_false(payload, names):
    found = {}
    for key, value in _walk(payload):
        if key in names:
            found.setdefault(key, []).append(value)
            assert value is False, f"{key} unexpectedly enabled: {value!r}"
    return found


def test_api_loads_and_health_is_http_200(app):
    assert app.title == "JARVIS Gateway API"
    assert _get(app, "/health") == {"status": "ok"}


@pytest.mark.parametrize("path", STATUS_ROUTES)
def test_foundation_status_endpoints_are_http_200_prepare_only_and_disabled(app, path):
    payload = _get(app, path)

    assert payload["prepare_only"] is True
    found = _assert_named_flags_false(payload, FORBIDDEN_ENABLED_FIELDS)
    assert found, f"{path} exposes none of the common safety flags"


def test_command_center_remains_prepare_only_with_foundation_markers(app):
    payload = _get(app, "/command-center")

    assert payload["prepare_only"] is True
    assert payload["execution_enabled"] is False
    assert payload["approval_enabled"] is False
    assert payload["hermes_connected"] is False
    assert payload["approval_gateway_called"] is False
    for marker in (
        "operator_console",
        "multi_device_runtime",
        "sandbox_execution",
        "tool_adoption_pipeline",
        "asset_factory_web_builder",
        "deploy_publishing_control",
        "marketing_distribution_engine",
        "payments_revenue",
        "daily_operator_scheduler",
        "continuous_learning_tech_radar",
        "advanced_personalization_user_model",
        "future_moonshot_layer",
    ):
        assert payload["metadata"][marker] == "prepare_only"


def test_operator_console_remains_prepare_only_and_read_only(app):
    status = _get(app, "/operator/console/status")
    capabilities = _get(app, "/operator/console/capabilities")
    snapshot = _get(app, "/operator/console/snapshot")

    assert status["prepare_only"] is True
    assert status["safe_read_only_mode"] is True
    assert capabilities["prepare_only"] is True
    for capability in (
        "execute_mission",
        "approve",
        "reject",
        "call_hermes",
        "create_approval",
        "read_secrets",
        "use_microphone",
        "use_camera",
        "send_push",
        "run_background",
        "deploy",
        "spend_money",
    ):
        assert capabilities[capability] is False
    assert snapshot["prepare_only"] is True
    _assert_named_flags_false(snapshot, FORBIDDEN_ENABLED_FIELDS)


def test_daily_learning_personal_os_personalization_and_moonshot_boundaries(app):
    expected_false = {
        "/daily-operator/status": {
            "background_worker_enabled",
            "cron_enabled",
            "system_timer_enabled",
            "task_execution_enabled",
        },
        "/continuous-learning/status": {
            "auto_update_enabled",
            "auto_install_enabled",
            "auto_deploy_enabled",
            "runtime_modification_enabled",
            "prompt_modification_enabled",
        },
        "/personal-os/status": {
            "calendar_reading_enabled",
            "email_reading_enabled",
            "document_reading_enabled",
            "local_file_scanning_enabled",
            "surveillance_enabled",
            "camera_enabled",
            "microphone_enabled",
            "screen_capture_enabled",
        },
        "/personalization/status": {
            "memory_write_enabled",
            "memory_activation_enabled",
            "sensitive_inference_enabled",
            "manipulation_enabled",
            "action_authorization_from_memory_enabled",
        },
        "/future-moonshot/status": {
            "smart_glasses_enabled",
            "camera_enabled",
            "microphone_enabled",
            "screen_capture_enabled",
            "robotics_enabled",
            "drones_enabled",
            "ar_overlay_enabled",
            "physical_world_automation_enabled",
            "surveillance_enabled",
            "identity_impersonation_enabled",
        },
    }

    for path, fields in expected_false.items():
        payload = _get(app, path)
        found = _assert_named_flags_false(payload, fields)
        assert set(found) == fields


def test_selected_cross_foundation_previews_are_prepare_only_without_side_effects(app):
    missions_before = _get(app, "/missions")
    tasks_before = app.state.task_store.list()

    for path in PREVIEW_ROUTES:
        payload = _post(app, path)
        assert payload["prepare_only"] is True, path
        _assert_named_flags_false(payload, FORBIDDEN_ENABLED_FIELDS | PREVIEW_SIDE_EFFECT_FIELDS)

    assert _get(app, "/missions") == missions_before == []
    assert app.state.task_store.list() == tasks_before == []


def test_revenue_metrics_keep_projected_confirmed_gross_expenses_and_net_separate(app):
    pricing = _post(app, "/payments-revenue/pricing-preview")
    metrics = _post(app, "/payments-revenue/metrics-preview")
    master_map = MASTER_MAP.read_text(encoding="utf-8")

    assert pricing["no_confirmed_revenue"] is True
    assert metrics["no_confirmed_revenue"] is True
    for concept in ("projected", "confirmed", "gross", "expenses", "net"):
        assert concept in master_map, concept


def test_global_dangerous_routes_are_absent(app):
    exposed = {
        route.path
        for route in app.routes
        if route.path.rstrip("/").rsplit("/", 1)[-1] in DANGEROUS_ROUTE_NAMES
    }

    assert exposed == set()


def test_master_map_keeps_phase_s_as_last_phase_and_forbids_implicit_phase_t():
    content = MASTER_MAP.read_text(encoding="utf-8")

    assert "Phase S es la última fase maestra implementada" in content
    assert "No existe una siguiente fase maestra aprobada ni una Phase T implícita." in content
    assert "No crear nuevas fases sin actualizar primero este mapa maestro" in content
    assert "### Phase T" not in content
