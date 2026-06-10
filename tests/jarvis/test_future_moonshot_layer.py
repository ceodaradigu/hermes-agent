import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import FutureMoonshotPreviewRequest, InMemoryTaskStore, create_app
from jarvis.future_moonshot.foundation import (
    AROverlayPreview,
    ControlledEnvironmentPreview,
    DeepSimulationPreview,
    FutureMoonshotStatus,
    IdentityImpersonationGuardPreview,
    ImmediateStopPreview,
    LegalSafetyReviewPreview,
    MonetizationAdvantageReviewPreview,
    MoonshotApprovalRequirements,
    MoonshotAuditRollbackPreview,
    MoonshotCapabilityPreview,
    MoonshotSafetyPolicy,
    PhysicalWorldAutomationPreview,
    RoboticsDroneSafetyReviewPreview,
    SmartGlassesIntegrationPreview,
)
from jarvis.mission_control import MissionControl
from jarvis.operator_console import OperatorConsoleCapabilityMatrix, OperatorConsoleSnapshot
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


POST_ROUTES = (
    "/future-moonshot/capability-preview",
    "/future-moonshot/smart-glasses-preview",
    "/future-moonshot/ar-overlay-preview",
    "/future-moonshot/robotics-drone-safety-review",
    "/future-moonshot/deep-simulation-preview",
    "/future-moonshot/physical-automation-preview",
    "/future-moonshot/legal-safety-review",
    "/future-moonshot/controlled-environment-preview",
    "/future-moonshot/immediate-stop-preview",
    "/future-moonshot/audit-rollback-preview",
    "/future-moonshot/monetization-advantage-review",
    "/future-moonshot/identity-impersonation-guard",
    "/future-moonshot/approval-requirements",
)

DANGEROUS_ROUTES = (
    "/future-moonshot/connect-device",
    "/future-moonshot/start-camera",
    "/future-moonshot/start-microphone",
    "/future-moonshot/capture-screen",
    "/future-moonshot/control-robot",
    "/future-moonshot/control-drone",
    "/future-moonshot/send-command",
    "/future-moonshot/render-ar",
    "/future-moonshot/surveil",
    "/future-moonshot/impersonate",
    "/future-moonshot/execute",
)

STATUS_FALSE_FIELDS = (
    "future_moonshot_available",
    "smart_glasses_enabled",
    "ar_overlay_enabled",
    "robotics_enabled",
    "drones_enabled",
    "physical_world_automation_enabled",
    "deep_simulation_enabled",
    "camera_enabled",
    "microphone_enabled",
    "screen_capture_enabled",
    "surveillance_enabled",
    "identity_impersonation_enabled",
    "illegal_action_enabled",
    "implicit_permission_enabled",
    "external_calls_enabled",
    "secrets_access_enabled",
    "hermes_called",
    "approval_gateway_called",
    "execution_enabled",
    "persistence_enabled",
)


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Future/Moonshot previews")


def _app():
    return create_app(adapter_factory=FailAdapter)


def _endpoint(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def _get(app, path):
    return _endpoint(app, path, "GET")()


def _post(app, path, data):
    return _endpoint(app, path, "POST")(FutureMoonshotPreviewRequest(**data))


def test_status_endpoint_is_http_200_prepare_only_and_fully_disabled():
    app = _app()
    route = next(route for route in app.routes if route.path == "/future-moonshot/status")
    payload = route.endpoint()

    assert route.status_code in (None, 200)
    assert payload["prepare_only"] is True
    for field in STATUS_FALSE_FIELDS:
        assert payload[field] is False


def test_policy_requires_all_safety_reviews_controls_and_strong_approvals():
    app = _app()
    route = next(route for route in app.routes if route.path == "/future-moonshot/policy")
    payload = route.endpoint()

    assert route.status_code in (None, 200)
    assert payload["prepare_only"] is True
    assert all(payload.values())
    for field in (
        "legal_review_required", "safety_review_required", "controlled_environment_required",
        "immediate_stop_required", "audit_required", "rollback_required",
        "strong_approval_required_for_physical", "strong_approval_required_for_legal",
        "strong_approval_required_for_identity", "strong_approval_required_for_money",
        "strong_approval_required_for_safety",
    ):
        assert payload[field] is True


def test_capability_preview_never_executes_connects_or_modifies_physical_world():
    payload = _post(_app(), POST_ROUTES[0], {
        "capability_name": "Warehouse concept",
        "capability_type": "robotics",
        "safety_risk": "high",
        "intended_value": "Reduce repetitive work",
    })

    assert payload["capability_type"] == "robotics"
    assert payload["would_execute"] is False
    assert payload["would_connect_device"] is False
    assert payload["would_modify_physical_world"] is False
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True


def test_physical_capability_type_requires_strong_approval_even_if_risks_claim_none():
    payload = _post(_app(), POST_ROUTES[0], {
        "capability_type": "physical_automation",
        "safety_risk": "none",
        "legal_risk": "none",
        "identity_risk": "none",
    })

    assert payload["strong_approval_required"] is True
    assert payload["would_modify_physical_world"] is False


def test_smart_glasses_preview_never_connects_or_activates_sensors():
    payload = _post(_app(), POST_ROUTES[1], {
        "device_name": "Concept glasses",
        "integration_goal": "Show reviewed navigation cues",
        "data_inputs_preview": ["explicit user input"],
    })

    assert payload["camera_required"] is False
    assert payload["microphone_required"] is False
    assert payload["visible_indicator_required"] is True
    assert payload["immediate_stop_required"] is True
    assert payload["would_connect_device"] is False
    assert payload["would_activate_camera"] is False
    assert payload["would_activate_microphone"] is False
    assert payload["strong_approval_required"] is True


def test_ar_overlay_preview_never_renders_captures_uses_camera_or_acts():
    payload = _post(_app(), POST_ROUTES[2], {"overlay_name": "Safety cue", "distraction_risk": "medium"})

    assert payload["would_render_overlay"] is False
    assert payload["would_capture_screen"] is False
    assert payload["would_use_camera"] is False
    assert payload["would_act_on_overlay"] is False
    assert payload["immediate_stop_required"] is True
    assert payload["strong_approval_required"] is True


@pytest.mark.parametrize("system_type,geofence", [("robot", False), ("actuator", False), ("drone", True), ("vehicle", True)])
def test_robotics_drone_review_never_connects_commands_or_moves(system_type, geofence):
    payload = _post(_app(), POST_ROUTES[3], {"system_name": "Concept system", "system_type": system_type})

    assert payload["controlled_environment_required"] is True
    assert payload["human_supervision_required"] is True
    assert payload["geofence_required"] is geofence
    assert payload["emergency_stop_required"] is True
    assert payload["legal_review_required"] is True
    assert payload["would_send_command"] is False
    assert payload["would_connect_device"] is False
    assert payload["would_move_device"] is False


def test_deep_simulation_preview_never_runs_or_executes_real_action():
    payload = _post(_app(), POST_ROUTES[4], {
        "simulation_name": "Failure study",
        "assumptions": ["No real device input"],
        "failure_modes": ["Model mismatch"],
    })

    assert payload["no_real_world_action"] is True
    assert payload["no_production_decision_without_review"] is True
    assert payload["would_run_simulation"] is False
    assert payload["would_execute_real_action"] is False
    assert payload["approval_required"] is True


def test_physical_automation_preview_never_controls_commands_or_modifies_environment():
    payload = _post(_app(), POST_ROUTES[5], {
        "automation_name": "Lab concept",
        "physical_risk": "high",
        "safety_controls": ["Human supervision"],
        "stop_plan": "Manual emergency stop",
        "rollback_plan": "Restore controlled setup",
    })

    assert payload["controlled_environment_required"] is True
    assert payload["would_control_device"] is False
    assert payload["would_send_command"] is False
    assert payload["would_modify_environment"] is False
    assert payload["strong_approval_required"] is True


def test_legal_safety_review_never_invents_conclusion_or_clearance():
    unknown = _post(_app(), POST_ROUTES[6], {"review_subject": "Drone concept"})
    known = _post(_app(), POST_ROUTES[6], {"review_subject": "Drone concept", "jurisdiction": "explicit jurisdiction"})

    assert unknown["blocked_until_review"] is True
    assert unknown["jurisdiction_unknown"] is True
    assert unknown["no_legal_conclusion"] is True
    assert unknown["no_safety_clearance_without_evidence"] is True
    assert known["jurisdiction_unknown"] is False


def test_controlled_environment_preview_never_starts_or_executes():
    payload = _post(_app(), POST_ROUTES[7], {
        "environment_name": "Isolated lab preview",
        "allowed_capabilities": ["static review"],
        "blocked_capabilities": ["device control"],
    })

    assert payload["human_supervision_required"] is True
    assert payload["emergency_stop_available"] is True
    assert payload["audit_enabled_preview"] is True
    assert payload["rollback_available"] is True
    assert payload["would_start_environment"] is False
    assert payload["would_execute"] is False


def test_immediate_stop_preview_never_registers_hook_or_touches_device():
    payload = _post(_app(), POST_ROUTES[8], {"stop_name": "Emergency stop", "stop_triggers": ["unsafe condition"]})

    assert payload["manual_stop_required"] is True
    assert payload["required_before_activation"] is True
    assert payload["would_register_stop_hook"] is False
    assert payload["would_stop_real_device"] is False
    assert payload["would_execute"] is False


def test_audit_rollback_preview_never_writes_persists_or_rolls_back():
    payload = _post(_app(), POST_ROUTES[9], {
        "subject": "Concept",
        "audit_events_preview": ["review requested"],
        "rollback_plan": ["discard concept state"],
    })

    assert payload["audit_required"] is True
    assert payload["rollback_required"] is True
    assert payload["would_write_audit"] is False
    assert payload["would_persist"] is False
    assert payload["would_rollback_real_system"] is False


def test_monetization_review_never_invents_roi_and_rejects_pure_spectacle():
    payload = _post(_app(), POST_ROUTES[10], {"idea_name": "Flashy demo", "spectacle_risk": "high"})

    assert payload["no_fake_roi"] is True
    assert payload["reject_if_only_spectacle"] is True
    assert payload["rejected_as_only_spectacle"] is True
    assert payload["would_execute"] is False
    assert payload["would_spend_money"] is False


def test_identity_guard_blocks_impersonation_and_identity_artifacts():
    payload = _post(_app(), POST_ROUTES[11], {"scenario_name": "Identity concept", "identity_risk": "high"})

    assert payload["consent_required"] is True
    assert payload["prohibited_impersonation_actions"]
    assert payload["would_impersonate"] is False
    assert payload["would_create_identity_artifact"] is False
    assert payload["strong_approval_required"] is True


@pytest.mark.parametrize(
    "risk",
    (
        "physical_requested", "legal_requested", "identity_requested", "money_requested", "safety_requested",
        "camera_requested", "microphone_requested", "screen_requested", "surveillance_requested",
        "external_device_requested",
    ),
)
def test_approval_requirements_escalate_without_creating_or_authorizing(risk):
    payload = _post(_app(), POST_ROUTES[12], {risk: True})

    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["approval_gateway_called"] is False
    assert payload["approval_created"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_rejected"] is False
    assert payload["action_authorized"] is False
    assert payload["device_authorized"] is False


def test_all_preview_routes_are_local_pure_and_create_no_work(monkeypatch):
    app = _app()

    def fail(*args, **kwargs):
        raise AssertionError("Future/Moonshot preview attempted a forbidden side effect")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail, raising=False)
    monkeypatch.setattr(MissionControl, "create_mission", fail)
    monkeypatch.setattr(InMemoryTaskStore, "create", fail)
    monkeypatch.setattr("subprocess.run", fail)
    monkeypatch.setattr("subprocess.Popen", fail)
    monkeypatch.setattr("os.system", fail)

    assert _get(app, "/future-moonshot/status")["execution_enabled"] is False
    assert _get(app, "/future-moonshot/policy")["no_implicit_permissions"] is True
    for path in POST_ROUTES:
        assert _post(app, path, {})["prepare_only"] is True


def test_dangerous_routes_and_websocket_do_not_exist():
    app = _app()
    route_pairs = {(route.path, method) for route in app.routes for method in getattr(route, "methods", set())}

    for path in DANGEROUS_ROUTES:
        assert (path, "POST") not in route_pairs
    assert not any(route.__class__.__name__ == "APIWebSocketRoute" for route in app.routes)


def test_foundation_source_has_no_io_network_shell_package_manager_env_or_device_access():
    source = Path("jarvis/future_moonshot/foundation.py").read_text().lower()
    for forbidden in (
        "subprocess", "socket", "requests", "httpx", "urllib.request", "os.getenv", "os.environ",
        "dotenv", "open(", "read_text", "write_text", "pip install", "npm install", "camera.", "microphone.",
        "robot.", "drone.", "approvalgateway", "hermesruntime",
    ):
        assert forbidden not in source


def test_sensitive_input_is_redacted_and_secrets_are_not_read():
    payload = _post(_app(), POST_ROUTES[0], {
        "concept_summary": "Read .env secret token",
        "warnings": ["private key"],
    })
    serialized = json.dumps(payload).lower()

    for forbidden in (".env", "secret token", "private key"):
        assert forbidden not in serialized


def test_command_center_and_operator_console_remain_prepare_only_with_readiness():
    command_center = _get(_app(), "/command-center")
    operator = _get(_app(), "/operator/console/snapshot")
    capabilities = OperatorConsoleCapabilityMatrix.from_dict({}).to_dict()

    assert command_center["prepare_only"] is True
    assert command_center["metadata"]["future_moonshot_layer"] == "prepare_only"
    assert operator["prepare_only"] is True
    assert operator["metadata"]["future_moonshot_layer"] == "prepare_only"
    assert operator["future_moonshot_status"]["execution_enabled"] is False
    assert operator["future_moonshot_status"]["camera_enabled"] is False
    assert operator["moonshot_safety_policy"]["controlled_environment_required"] is True
    assert operator["moonshot_readiness"]["would_execute"] is False
    assert capabilities["read_future_moonshot_status"] is True
    assert capabilities["read_moonshot_safety_policy"] is True
    assert capabilities["preview_moonshot_capability"] is True
    assert capabilities["execute_mission"] is False
    assert capabilities["use_camera"] is False
    assert capabilities["use_microphone"] is False


def test_from_dict_and_serialization_cannot_enable_forbidden_capabilities():
    malicious = {
        "prepare_only": False,
        **{field: True for field in STATUS_FALSE_FIELDS},
        **{
            field: True
            for field in (
                "camera_required", "microphone_required", "would_execute", "would_connect_device",
                "would_modify_physical_world", "would_activate_camera", "would_activate_microphone",
                "would_render_overlay", "would_capture_screen", "would_use_camera", "would_act_on_overlay",
                "would_send_command", "would_move_device", "would_run_simulation", "would_execute_real_action",
                "would_control_device", "would_modify_environment", "would_start_environment",
                "would_register_stop_hook", "would_stop_real_device", "would_write_audit", "would_persist",
                "would_rollback_real_system", "would_spend_money", "would_impersonate",
                "would_create_identity_artifact", "approval_created", "approval_granted", "approval_rejected",
                "action_authorized", "device_authorized",
            )
        },
    }
    values = (
        FutureMoonshotStatus.from_dict(malicious),
        MoonshotCapabilityPreview.from_dict(malicious),
        SmartGlassesIntegrationPreview.from_dict(malicious),
        AROverlayPreview.from_dict(malicious),
        RoboticsDroneSafetyReviewPreview.from_dict(malicious),
        DeepSimulationPreview.from_dict(malicious),
        PhysicalWorldAutomationPreview.from_dict(malicious),
        LegalSafetyReviewPreview.from_dict(malicious),
        ControlledEnvironmentPreview.from_dict(malicious),
        ImmediateStopPreview.from_dict(malicious),
        MoonshotAuditRollbackPreview.from_dict(malicious),
        MonetizationAdvantageReviewPreview.from_dict(malicious),
        IdentityImpersonationGuardPreview.from_dict(malicious),
        MoonshotApprovalRequirements.from_dict(malicious),
        OperatorConsoleSnapshot.from_dict({"future_moonshot_status": malicious}),
    )

    for value in values:
        payload = value.to_dict()
        assert payload["prepare_only"] is True
        serialized = json.dumps(payload)
        for field in STATUS_FALSE_FIELDS:
            if field in payload:
                assert payload[field] is False
        for field in malicious:
            if field.startswith("would_") or field in {
                "camera_required", "microphone_required", "approval_created", "approval_granted",
                "approval_rejected", "action_authorized", "device_authorized",
            }:
                assert f'"{field}": true' not in serialized


def test_policy_from_dict_cannot_disable_safety_requirements():
    payload = MoonshotSafetyPolicy.from_dict({
        name: False for name in MoonshotSafetyPolicy.__dataclass_fields__
    }).to_dict()
    assert all(payload.values())
